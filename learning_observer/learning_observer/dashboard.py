'''
This generates dashboards from student data.

TODO much of this file is no longer being used and the
unused code ought to be removed. We have iterated on how
we do this a few times and have landed in a much better
place than we started.
'''

import asyncio
import copy
import datetime
import inspect
import json
import aiohttp.client_exceptions
import jsonschema
import numbers
import os
import pmss
import queue
import time

import aiohttp

import learning_observer.util as util

import learning_observer.synthetic_student_data as synthetic_student_data

import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.kvs as kvs
import learning_observer.runtime

import learning_observer.paths as paths

import learning_observer.auth
import learning_observer.constants as constants
import learning_observer.rosters as rosters
import learning_observer.util

from learning_observer.log_event import debug_log, log_event, close_logfile

import learning_observer.module_loader
import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.schema
import learning_observer.settings

pmss.register_field(
    name='dangerously_allow_insecure_dags',
    type=pmss.pmsstypes.TYPES.boolean,
    description='Data can be queried either by system defined execution DAGs '\
                '(directed acyclic graphs) or user created execution DAGs. '\
                'This is useful for developing new system queries, but should not '\
                'be used in production.',
    default=False
)

pmss.register_field(
    name='logging_enabled',
    type=pmss.pmsstypes.TYPES.boolean,
    description='Allow data to be logged or not. Used in within namespaces '\
                'such as `dashboard_settings` or `lms_integration`.',
    default=False
)


def timelist_to_seconds(timelist):
    '''
    [5, "seconds"] ==> 5
    [5, "minutes"] ==> 300
    etc.
    '''
    if timelist is None:
        return None
    if len(timelist) != 2:
        raise Exception("Time lists should have number and units")
    if not isinstance(timelist[0], numbers.Number):
        raise Exception("First element should be a number")
    if not isinstance(timelist[1], str):
        raise Exception("Second element should be a string")
    units = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600
    }
    if timelist[1] not in units:
        raise Exception("Second element should be a time unit")
    return timelist[0] * units[timelist[1]]


@learning_observer.auth.teacher
async def generic_dashboard(request):
    '''
    We would like to be able to support pretty arbitrary dashboards,
    where the client asks for a subset of data and we send it.

    This is probably the wrong abstraction, but our goal is to allows
    arbitrary dashboards client-side.

    We're figuring out what we're doing. This view is behind a feature
    flag, since we have no clear idea.

    Our goal is to be able to set up appropriate queries to deliver
    pretty generic aggregations.

    The current model has the client ask for specific data, and for us
    to send it back. However, the concept of doing this more server-side
    makes a lot of sense too.

    GraphQL looks super-relevant. Implementing it is a big lift, and
    it might need to be slightly adapted to the context.

    The test case for this is in `scripts/generic_websocket_dashboard.py`
    '''
    # We never send data more than twice per second, because performance.
    MIN_REFRESH = 0.5

    teacherkvs = kvs.KVS()
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    subscriptions = queue.PriorityQueue()

    def timeout():
        '''
        Calculate the time until we need to send the next message.
        '''
        if subscriptions.empty():
            return None
        else:
            Δt = subscriptions.queue[0][0] - time.time()
            return Δt

    count = [0]

    def counter():
        count[0] += 1
        return count[0]

    running = False           # Are we streaming data?
    next_subscription = None  # What is the next item to send?

    while True:
        # Wait for the next message, with an upper bound of when we
        # need to get back to the client.
        try:
            if subscriptions.empty() or not running:
                msg = await ws.receive()
            else:
                msg = await ws.receive(timeout=timeout())
            debug_log("msg", msg)
            if msg.type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                # By this point, the client is long gone, but we want to
                # return something to avoid confusing middlewares.
                return aiohttp.web.Response(text="This never makes it back....")
            elif msg.type == aiohttp.WSMsgType.TEXT:
                message = json.loads(msg.data)
                debug_log(message)
                if message['action'] == 'subscribe':
                    subscriptions.put([
                        time.time(),
                        {
                            'keys': message['keys'],
                            'ids': [sa_helpers.make_key_from_json(key) for key in message['keys']],
                            'refresh': timelist_to_seconds(message['refresh']),
                            'subscription_id': message.get('subscription_id', counter())
                        }
                    ])
                elif message['action'] == 'start':
                    await ws.send_json(
                        {'subscribed': [i[1] for i in subscriptions.queue]}
                    )
                    running = True
                elif message['action'] == 'hangup':
                    break
        # If we didn't get a message before we need to send one,
        # just keep going.
        except asyncio.exceptions.TimeoutError:
            pass
        if ws.closed:
            debug_log("Socket closed")
            return aiohttp.web.Response(text="This never makes it back to the client....")
        # Now, we send any messages we need to
        while timeout() is not None and timeout() < 0:
            response = {}
            t, s = subscriptions.get()
            for key, json_key in zip(s['ids'], s['keys']):
                response[key] = await teacherkvs[key]
                if isinstance(response[key], dict):
                    response[key]['key'] = json_key
            response['subscription_id'] = s['subscription_id']
            if 'refresh' in s and s['refresh'] is not None:
                subscriptions.put([time.time() + max(s['refresh'], MIN_REFRESH), s])
            await ws.send_json(response)

    return aiohttp.web.Response(text="This should never happen....")


def fetch_student_state(
        course_id, module_id,
        agg_module, roster,
        default_data={}
):
    '''
    This closure will compile student data from a roster of students.

    Closure remembers course roster, and redis KVS.

    Reopening connections to redis every few seconds otherwise would
    run us out of file pointers.
    '''
    teacherkvs = kvs.KVS()

    async def student_state_fetcher():
        '''
        Poll redis for student state. This should be abstracted out into a
        generic aggregator API, much like we have a reducer on the
        incoming end.
        '''
        students = []
        for student in roster:
            student_state = {
                # We're copying Google's roster format here.
                #
                # It's imperfect, and we may want to change it later, but it seems
                # better than reinventing our own standard.
                #
                # We don't copy verbatim, since we do want to filter down any
                # extra stuff.
                'profile': {
                    'name': {
                        'full_name': student['profile']['name']['full_name']
                    },
                    'photo_url': student['profile'].get('photo_url', ''),
                    'email_address': student['profile'].get('email_address', ''),
                    'external_ids': student['profile'].get('external_ids', []),
                },
                "course_id": course_id,
                constants.USER_ID: student[constants.USER_ID],  # TODO: Encode?
            }

            student_state.update(default_data)

            # TODO/HACK: Only do this for Google data. Make this do the right thing
            # for synthetic data.
            google_id = student[constants.USER_ID]
            if google_id.isnumeric():
                student_id = learning_observer.auth.google_id_to_user_id(google_id)
            else:
                student_id = google_id
            # TODO: Evaluate whether this is a bottleneck.
            #
            # mget is faster than ~50 gets. But some online benchmarks show both taking
            # microseconds, to where it might not matter.
            #
            # For most services (e.g. a SQL database), this would be a huge bottleneck. redis might
            # be fast enough that it doesn't matter? Dunno.
            for sa_module in agg_module['sources']:
                key = sa_helpers.make_key(
                    sa_module,
                    {sa_helpers.KeyField.STUDENT: student_id},
                    sa_helpers.KeyStateType.EXTERNAL)
                data = await teacherkvs[key]
                # debug_log(key, data)  # <-- Useful, but a lot of stuff is spit out.
                if data is not None:
                    student_state[sa_helpers.fully_qualified_function_name(sa_module)] = data
            cleaner = agg_module.get("cleaner", lambda x: x)
            students.append(cleaner(student_state))

        return students
    return student_state_fetcher


def find_course_aggregator(module_id):
    '''
    Find a course aggregator based on a `module_id`

    * This should move to the modules package.
    * We should support having a list of these
    '''
    course_aggregator_module = None
    default_data = {}
    course_aggregator_candidates = learning_observer.module_loader.course_aggregators()
    for candidate_module in course_aggregator_candidates:
        if course_aggregator_candidates[candidate_module]['short_id'] == module_id:
            # TODO: We should support multiple modules here.
            if course_aggregator_module is not None:
                raise aiohttp.web.HTTPNotImplemented(text="Duplicate module: " + candidate_module)
            course_aggregator_module = course_aggregator_candidates[candidate_module]
            default_data = course_aggregator_module.get('default-data', {})
    return (course_aggregator_module, default_data)


@learning_observer.auth.teacher
async def websocket_dashboard_view(request):
    '''
    Handler to aggregate student data, and serve it back to the client
    every half-second to second or so.

    TODO remove this method. This is the old way of passing data from
    the server to the client (pre communication protocol).
    '''
    # Extract parameters from the URL
    #
    # Note that we need to do auth/auth. At present, we always want a
    # course ID, even for a single student. If a teacher requests a
    # students' data, we want to make sure that sutdnet is in that
    # teacher's course.
    course_id = request.rel_url.query.get("course")
    # module_id should support a list, perhaps?
    module_id = request.rel_url.query.get("module")
    # For student dashboards
    student_id = request.rel_url.query.get("student", None)
    # For individual resources
    resource_id = request.rel_url.query.get("resource", None)
    # How often do we refresh? Default is 0.5 seconds
    refresh = 0.5  # request.match_info.get('refresh', 0.5)

    # Find the right module
    course_aggregator_module, default_data = find_course_aggregator(module_id)

    if course_aggregator_module is None:
        debug_log("Bad module: ", module_id)
        available = learning_observer.module_loader.course_aggregators()
        debug_log("Available modules: ", [available[key]['short_id'] for key in available])
        raise aiohttp.web.HTTPBadRequest(text="Invalid module: {}".format(module_id))

    # We need to receive to detect web socket closures.
    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.1)
    await ws.prepare(request)

    roster = await rosters.courseroster(request, course_id)

    # If we're grabbing data for just one student, we filter the
    # roster down.  This pathway ensures we only serve data for
    # students on a class roster.  I'm not sure this API is
    # right. Should we have a different URL? A set of filters? A lot
    # of that is TBD. Once nice property about this is that we have
    # the same data format for 1 student as for a classroom of
    # students.
    if student_id is not None:
        roster = [r for r in roster if r[constants.USER_ID] == student_id]
    # Grab student list, and deliver to the client
    student_state_fetcher = fetch_student_state(
        course_id,
        module_id,
        course_aggregator_module,
        roster,
        default_data
    )
    aggregator = course_aggregator_module.get('aggregator', lambda x: {})
    async_aggregator = inspect.iscoroutinefunction(aggregator)
    args_aggregrator = inspect.getfullargspec(aggregator)[0]
    client_data = None
    runtime = learning_observer.runtime.Runtime(request)

    while True:
        sd = await student_state_fetcher()
        data = {
            "student_data": sd   # Per-student list
        }
        # Prep the aggregator function to be called.
        # Determine if we should pass the client_data in or not/async capability
        # Currently options is a list of strings (what we want returned)
        # In the futuer this should be some form of communication protocol
        if 'options' in args_aggregrator:
            agg = aggregator(runtime, sd, client_data)
        else:
            agg = aggregator(runtime, sd)
        if async_aggregator:
            agg = await agg
        data.update(agg)
        await ws.send_json(data)
        # First try to receive a json, if you receive something that can't be json'd
        # check for closing, otherwise timeout will fire
        # This is kind of an awkward block, but aiohttp doesn't detect
        # when sockets close unless they receive data. We try to receive,
        # and wait for an exception or a CLOSE message.
        try:
            client_data = await ws.receive_json()
        except (TypeError, ValueError):
            if (await ws.receive()).type == aiohttp.WSMsgType.CLOSE:
                debug_log("Socket closed!")
                # By this point, the client is long gone, but we want to
                # return something to avoid confusing middlewares.
                return aiohttp.web.Response(text="This never makes it back....")
        except asyncio.exceptions.TimeoutError:
            # This is the normal code path
            pass
        await asyncio.sleep(0.5)
        # This never gets called, since we return above
        if ws.closed:
            debug_log("Socket closed. This should never appear, however.")
            return aiohttp.web.Response(text="This never makes it back....")


# We use following functions to return an error message about the requested
# DAG back to the user.
async def dag_not_found(dags):
    if type(dags) == set:
        return f'Execution DAG{"s" if len(dags) > 1 else ""}, {", ".join(dags)}, not found on system.'
    return f'Execution DAG, {dags}, not found on system.'


async def dag_incorrect_format(e):
    return f'Submitted Execution DAG not in valid format: {e}'


async def dag_unsupported_type(t):
    return f'Unsupported type, {t}, for execution_dag parameter.'


async def dag_submission_not_allowed():
    return 'Submitting fully formed DAGs is not supported.'


def extract_namespaced_dags(dag, deps=None):
    '''This will return any dependencies on other dags
    (in other words, variables of the form namespace.variable which are not local).
    If it finds something like writing_observer.docs, it will add that to a set,
    and return that set of dependencies.

    This is so we can have a complete list of DAG nodes we might need to reference.
    We can take the keys from the execution_dag dictionary, but we also add all of
    the references to DAGs in other modules.
    '''
    # TODO move this function to the communication protocol directory
    if deps is None:
        deps = set()

    if isinstance(dag, dict):
        if dag.get('dispatch') == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
            variable_name = dag['variable_name']
            if '.' in variable_name:
                deps.add(variable_name.split('.')[0])
        for key in dag:
            extract_namespaced_dags(dag[key], deps)
    return deps


def fully_qualify_names_with_default_namespace(dag, namespace_prefix):
    '''In order to avoid naming conflicts, and to have consistency, this will append
    the default namespace to all variables without a namespace prefix.

    For example, if the prefix is writing_observer, and we run into a node `docs`,
    this node will be renamed to `writing_observer.docs`.

    TODO If a node already has a prefix (e.g. dynamic_assessment.foo), it will remain unchanged.
    '''
    # TODO move this function to the communication protocol directory
    if isinstance(dag, dict):
        if dag.get('dispatch') == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
            dag['variable_name'] = f'{namespace_prefix}.{dag["variable_name"]}'
        for key in dag:
            fully_qualify_names_with_default_namespace(dag[key], namespace_prefix)
    return dag


async def dispatch_named_execution_dag(dag_name):
    '''This method takes a Named Query and fetches it from the
    available DAGs on the system.
    '''
    available_dags = learning_observer.module_loader.execution_dags()
    query = None
    try:
        query = available_dags[dag_name]
    except KeyError:
        debug_log(await dag_not_found(dag_name))
    finally:
        pass
    return query


async def dispatch_defined_execution_dag(dag):
    '''This method confirms that an Open Queries provided by the user
    are 1) allowed to be submitted and 2) adhere to the appropriate
    JSON structure.
    '''
    query = None
    if not learning_observer.settings.pmss_settings.dangerously_allow_insecure_dags():
        debug_log(await dag_submission_not_allowed())
        return query
    try:
        learning_observer.communication_protocol.schema.prevalidate_schema(dag)
        query = dag
    except jsonschema.ValidationError as e:
        debug_log(await dag_incorrect_format(e))
        return query
    finally:
        pass
    return query


DAG_DISPATCH = {dict: dispatch_defined_execution_dag, str: dispatch_named_execution_dag}


async def _handle_dependent_dags(query):
    '''
    Handles dependent DAGs and ensures all dependencies are present.
    NOTE dependent dags only work for on a single level dependency
    TODO allow multiple layers of dependency among dags
    '''
    execution_dags = learning_observer.module_loader.execution_dags()
    dependent_dags = extract_namespaced_dags(query['execution_dag'])
    missing_dags = dependent_dags - execution_dags.keys()

    if missing_dags:
        # TODO we ought to handle this as an error
        debug_log(await dag_not_found(missing_dags))
        return

    for dep in dependent_dags:
        # Copy and qualify names for dependent DAG
        dep_dag = copy.deepcopy(execution_dags[dep]['execution_dag'])
        prefixed_dag = fully_qualify_names_with_default_namespace(dep_dag, dep)

        # Merge dependent DAG with current query
        query['execution_dag'] = {**query['execution_dag'], **{f'{dep}.{k}': v for k, v in prefixed_dag.items()}}

    return query


async def _prepare_dag_as_generators(client_query, query, targets, request):
    '''
    Prepares the query for execution, sets up client parameters and runtime.
    '''
    target_exports = list(targets)

    # Prepare the DAG execution function
    query_func = learning_observer.communication_protocol.integration.prepare_dag_execution(query, target_exports)

    # Handle client parameters and runtime setup
    client_parameters = client_query.get('kwargs', {}).copy()
    runtime = learning_observer.runtime.Runtime(request)
    client_parameters['runtime'] = runtime

    # Execute the query and return generators keyed by export targets.
    generator_dictionary = await query_func(**client_parameters)
    target_nodes_to_targets = {}
    exports = query.get('exports', {})
    execution_nodes = query.get('execution_dag', {})
    for target in target_exports:
        if target in exports:
            node = exports[target].get('returns')
            if node not in execution_nodes:
                node = f'__missing_export__:{target}'
        else:
            node = f'__missing_export__:{target}'
        target_nodes_to_targets.setdefault(node, []).append(target)

    generators_by_id = {}
    for node, node_targets in target_nodes_to_targets.items():
        generator = generator_dictionary.get(node)
        if generator is None:
            debug_log(f'Missing generator for DAG node {node}')
            continue
        generator_id = id(generator)
        if generator_id not in generators_by_id:
            generators_by_id[generator_id] = {
                'generator': generator,
                'targets': []
            }
        generators_by_id[generator_id]['targets'].extend(node_targets)
    return [
        (entry['targets'], entry['generator'])
        for entry in generators_by_id.values()
    ]



async def _create_dag_generators(client_query, targets, request):
    dag = client_query['execution_dag']
    if type(dag) not in DAG_DISPATCH:
        debug_log(await dag_unsupported_type(type(dag)))
        return

    query = await DAG_DISPATCH[type(dag)](dag)
    if query is None:
        # the DAG_DISPATCH prints a more detailed message about why
        debug_log('The submitted query failed.')
        return
    query = await _handle_dependent_dags(query)
    return await _prepare_dag_as_generators(client_query, query, targets, request)


def _scope_segment_for_provenance_key(key):
    if key == 'RESOURCE':
        return 'documents'
    if key.startswith('EventField.'):
        field_name = key.split('EventField.', 1)[1]
        if field_name == 'doc_id':
            return 'documents'
        if field_name.endswith('_id'):
            return f"{field_name}s"
        return f"{field_name}s"
    if key == 'CLASS':
        return 'classes'
    return f"{key.lower()}s"


def _provenance_key_for_scope_field(field):
    if isinstance(field, sa_helpers.KeyField):
        return field.name
    if isinstance(field, sa_helpers.EventField):
        if field.event == 'doc_id':
            return 'RESOURCE'
        return f'EventField.{field.event}'
    return str(field)


def _scope_key_order_for_reducer(reducer):
    if not reducer:
        return []
    scope = reducer.get('scope', [])
    ordered_scope = sorted(
        scope,
        key=lambda field: (0 if isinstance(field, sa_helpers.KeyField) else 1, getattr(field, 'name', str(field)))
    )
    return [_provenance_key_for_scope_field(field) for field in ordered_scope]


def _find_reducer_from_provenance_key(key):
    if not key:
        return None
    parts = key.split(',')
    if len(parts) < 2:
        return None
    reducer_name = parts[1]
    for reducer in learning_observer.module_loader.reducers():
        function_name = sa_helpers.fully_qualified_function_name(reducer['function'])
        if function_name == reducer_name:
            return reducer
    return None


def _value_from_provenance_entry(key, entry):
    if not isinstance(entry, dict):
        return entry
    if key == 'STUDENT':
        for candidate in ('user_id', 'student_id', 'id'):
            if candidate in entry:
                return entry[candidate]
    if key in ('RESOURCE', 'EventField.doc_id'):
        for candidate in ('doc_id', 'resource_id', 'id'):
            if candidate in entry:
                return entry[candidate]
    if key == 'CLASS':
        for candidate in ('class_id', 'id'):
            if candidate in entry:
                return entry[candidate]
    if key == 'TEACHER':
        for candidate in ('user_id', 'teacher_id', 'id'):
            if candidate in entry:
                return entry[candidate]
    if key.startswith('EventField.'):
        field_name = key.split('EventField.', 1)[1]
        if field_name in entry:
            return entry[field_name]
    return entry.get('value')


def _find_student_or_resource(d):
    '''HACK the communication protocol does not provide an easy way to
    determine which student or student/document pair is being updated.
    The protocol does include a provenance key with each item that includes
    the history of what occured within the protocol.
    In production settings, the provenance should be removed from the
    user output. However, this method assumes that the provenance is still
    around.
    This method digs into the provenance and extracts the corresponding
    scope ids. This information is used to tell the client which items in
    their data-tree to update (i.e. update Billy's History Essay with this
    new information).
    '''
    if not isinstance(d, dict):
        return []
    if 'provenance' in d:
        provenance = d['provenance']
        provenance_data = provenance
        provenance_key = None
        if isinstance(provenance, dict):
            provenance_data = provenance.get('provenance', provenance)
            provenance_key = provenance.get('key')
        while isinstance(provenance_data, dict) and 'provenance' in provenance_data:
            provenance_key = provenance_data.get('key', provenance_key)
            next_provenance = provenance_data.get('provenance')
            if next_provenance is None or next_provenance is provenance_data:
                break
            provenance_data = next_provenance
        output = []
        if isinstance(provenance_data, dict):
            reducer = _find_reducer_from_provenance_key(provenance_key)
            scope_order = _scope_key_order_for_reducer(reducer)
            scope_order_index = {key: idx for idx, key in enumerate(scope_order)} if scope_order else {}
            if scope_order_index:
                ordered_entries = sorted(
                    ((key, entry) for key, entry in provenance_data.items() if key in scope_order_index),
                    key=lambda item: scope_order_index[item[0]]
                )
            else:
                ordered_entries = provenance_data.items()
            for key, entry in ordered_entries:
                if scope_order_index and key not in scope_order_index:
                    continue
                segment = _scope_segment_for_provenance_key(key)
                if segment is None:
                    continue
                value = _value_from_provenance_entry(key, entry)
                if value is None:
                    continue
                output.append(segment)
                output.append(str(value))

        if output:
            return output
        return _find_student_or_resource(provenance_data)
    return []


# We track protocol log creation per-process so that concurrent websocket
# connections produce unique filenames even when they open at the same time.
DASHBOARD_PROTOCOL_LOG_COUNTER = 0
DASHBOARD_PROTOCOL_LOG_LOCK = asyncio.Lock()


@learning_observer.auth.teacher
async def websocket_dashboard_handler(request):
    '''
    Handles client requests through a WebSocket, executes requested queries,
    and sends back the results.

    Args:
        request: aiohttp request object.

    Returns:
        aiohttp web response.
    '''
    active_user = await learning_observer.auth.get_active_user(request)
    user_context = {
        'user_id': (active_user or {}).get('user_id'),
        'user_email': (active_user or {}).get('email'),
        'user_role': (active_user or {}).get('role'),
    }
    # Fetch PMSS setting flag for dashboard logging, scoped by user's email domain
    user_domain = learning_observer.util.get_domain_from_email(user_context['user_email'])
    dashboard_protocol_logging_enabled = learning_observer.settings.pmss_settings.logging_enabled(types=['dashboard_settings'], attributes={'domain': user_domain})

    global DASHBOARD_PROTOCOL_LOG_COUNTER
    async with DASHBOARD_PROTOCOL_LOG_LOCK:
        current_counter = DASHBOARD_PROTOCOL_LOG_COUNTER
        DASHBOARD_PROTOCOL_LOG_COUNTER += 1

    # TODO this is similar to our incoming student event log file names
    # this ought to be abstracted to a helper function
    # The combination of timestamp / user / process / counter creates
    # unique filenames for each dashboard session
    protocol_log_filename = "{timestamp}-{user:-<15}-{remote:-<15}-{counter:0>10}-{pid}.dashboard".format(
        timestamp=datetime.datetime.utcnow().isoformat(),
        user=(user_context.get('user_id') or 'UNKNOWN')[:15],
        remote=(request.remote or '')[:15],
        counter=current_counter,
        pid=os.getpid(),
    )

    is_protocol_log_closed = False

    def close_protocol_log():
        '''Close the structured protocol log if logging is enabled.'''
        if not dashboard_protocol_logging_enabled:
            return
        nonlocal is_protocol_log_closed
        if not is_protocol_log_closed:
            try:
                close_logfile(protocol_log_filename)
            finally:
                is_protocol_log_closed = True

    has_logged_connection_closure = False
    lock_field_event = {
        'event': 'lock_fields',
        'fields': {
            'user_id': user_context.get('user_id'),
            'user_email': user_context.get('user_email'),
            'user_role': user_context.get('user_role'),
            'remote': request.remote,
            'request_path': str(request.rel_url)
        }
    }
    if dashboard_protocol_logging_enabled:
        log_event(lock_field_event, filename=protocol_log_filename)

    def _log_protocol_event(event, **extra):
        '''
        Emit structured logs describing websocket activity.
        '''
        if not dashboard_protocol_logging_enabled:
            return
        nonlocal has_logged_connection_closure  # ensure we mutate the outer flag
        payload = {
            'event': event,
            'timestamp': str(datetime.datetime.now()),
        }
        payload.update(extra)
        try:
            log_event(payload, filename=protocol_log_filename)
        except TypeError:
            # Fall back to logging the raw payload if serialization fails.
            log_event({
                'event_type': 'communication_protocol_event',
                'event': event,
                'serialization_failed': True,
                'payload_repr': repr(payload),
            }, filename=protocol_log_filename)
        if event == 'connection_closed':
            has_logged_connection_closure = True

    def _close_connection_and_cleanup(reason: str):
        """
        Idempotently log connection closure and close the protocol log file.
        """
        if not has_logged_connection_closure:
            _log_protocol_event('connection_closed', reason=reason)
        close_protocol_log()

    def _create_query_summary_for_logging(query):
        '''
        Provide a compact description of the query for log aggregation.
        '''
        summary = {}
        for key, value in (query or {}).items():
            if not isinstance(value, dict):
                summary[key] = {'non_dict_value': repr(value)}
                continue
            execution_dag = value.get('execution_dag')
            summary[key] = {
                'target_exports': value.get('target_exports', []),
                'execution_dag_type': type(execution_dag).__name__,
                'execution_dag_name': execution_dag if isinstance(execution_dag, str) else None,
                'kwargs': value.get('kwargs', {}),
            }
        return summary

    _log_protocol_event('connection_opened')

    ws = aiohttp.web.WebSocketResponse(receive_timeout=0.3)
    await ws.prepare(request)
    client_query = None
    previous_client_query = None
    pending_updates = []
    pending_updates_lock = asyncio.Lock()
    background_tasks = set()

    async def _queue_update(update):
        '''Send an update to our batch
        '''
        async with pending_updates_lock:
            pending_updates.append(update)

    async def _send_pending_updates_to_client():
        '''If our queue has any items, send them to the client, clear
        the queue, then wait before checking again.
        '''
        while True:
            async with pending_updates_lock:
                if pending_updates:
                    try:
                        await ws.send_json(pending_updates)
                        pending_updates.clear()
                    except aiohttp.web_ws.WebSocketError:
                        break
                    except aiohttp.client_exceptions.ClientConnectionResetError:
                        break
            if ws.closed:
                break
            # TODO this ought to be pulled from somewhere
            await asyncio.sleep(1)

    async def _execute_dag(dag_query, targets, params):
        '''This method creates the DAG generator and drives it.
        Once finished, we wait until rescheduling it. If the parameters
        change, we exit before creating and driving the generator.
        '''
        if params != client_query:
            # the params are different and we should stop this generator
            return

        # Create DAG generator and drive
        generators = await _create_dag_generators(dag_query, targets, request)
        if generators is None:
            return
        drive_tasks = []
        for target_group, generator in generators:
            drive_tasks.append(asyncio.create_task(
                _drive_generator(generator, dag_query['kwargs'], targets=target_group)
            ))
        if drive_tasks:
            await asyncio.gather(*drive_tasks)

        # Handle rescheduling the execution of the DAG for fresh data
        # TODO add some way to specify specific endpoint delays
        dag_delay = dag_query['kwargs'].get('rerun_dag_delay', 10)
        if dag_delay < 0:
            # if dag_delay is negative, we skip repeated execution
            return
        await asyncio.sleep(dag_delay)
        await _execute_dag(dag_query, targets, params)

    async def _drive_generator(generator, dag_kwargs, targets=None):
        '''For each item in the generator, this method creates
        an update to send to the client.
        '''
        target_exports = targets or [None]
        async for item in generator:
            scope = _find_student_or_resource(item)
            update_path = ".".join(scope)
            for target in target_exports:
                item_payload = item
                if 'option_hash' in dag_kwargs and target is not None and isinstance(item, dict):
                    item_payload = dict(item)
                    item_payload[f'option_hash_{target}'] = dag_kwargs['option_hash']
                # TODO this ought to be flag - we might want to see the provenance in some settings
                item_without_provenance = learning_observer.communication_protocol.executor.strip_provenance(item_payload)
                update_payload = {'op': 'update', 'path': update_path, 'value': item_without_provenance}
                _log_protocol_event(
                    'update_enqueued',
                    payload=update_payload,
                    target_export=target
                )
                await _queue_update(update_payload)

    send_batches_task = asyncio.create_task(_send_pending_updates_to_client())
    background_tasks.add(send_batches_task)
    send_batches_task.add_done_callback(background_tasks.discard)

    try:
        while True:
            try:
                received_params = await ws.receive_json()
                client_query = received_params
                _log_protocol_event(
                    'query_received',
                    query_summary=_create_query_summary_for_logging(client_query),
                )
                # TODO we should validate the client_query structure
            except aiohttp.client_exceptions.WSMessageTypeError as e:
                # Check if this was a close message
                if ws.closed:
                    _close_connection_and_cleanup('websocket_closed_with_message_error')
                    break
                # Log the unexpected message type and continue
                _log_protocol_event('unexpected_message_type', error=str(e))
                continue
            except (TypeError, ValueError) as e:
                _log_protocol_event(
                    'json_parse_error', 
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                if ws.closed:
                    _close_connection_and_cleanup('websocket_closed_during_json_parse')
                    break
                continue
            except asyncio.exceptions.TimeoutError:
                # this is the normal path of the code
                # if the client_query hasn't been set, keep waiting for it
                if client_query is None:
                     continue

            if ws.closed:
                _close_connection_and_cleanup('websocket_closed_flag')
                break

            if client_query != previous_client_query:
                previous_client_query = copy.deepcopy(client_query)
                for k, v in client_query.items():
                    targets = v.get('target_exports', [])
                    execute_dag_task = asyncio.create_task(_execute_dag(v, targets, client_query))
                    background_tasks.add(execute_dag_task)
                    execute_dag_task.add_done_callback(background_tasks.discard)

    # Various ways we might encounter an exception
    except asyncio.CancelledError:
        _close_connection_and_cleanup('server_cancelled')
    except (aiohttp.web_ws.WebSocketError, 
            aiohttp.client_exceptions.ClientConnectionResetError,
            ConnectionResetError) as e:
        _log_protocol_event(
            'connection_closed_gracefully', 
            exception_type=type(e).__name__, 
            detail=str(e))
        _close_connection_and_cleanup('client_disconnected')
    except Exception as e:
        _log_protocol_event(
            'handler_exception', 
            exception_type=type(e).__name__, 
            detail=repr(e))
        _close_connection_and_cleanup('server_exception')
    finally:
        # Ensure all background tasks are stopped cleanly
        for t in list(background_tasks):
            t.cancel()
        if background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)
        
        # Close WebSocket gracefully if not already closed
        if not ws.closed:
            try:
                await ws.close()
            except Exception:
                pass
    return aiohttp.web.Response()


# Obsolete code -- we should put this back in after our refactor. Allows us to use
# dummy data
# @learning_observer.auth.teacher
# async def static_student_data_handler(request):
#     '''
#     Populate static / mock-up dashboard with static fake data
#     '''
#     # module_id = request.match_info['module_id']
#     # course_id = int(request.match_info['course_id'])

#     return aiohttp.web.json_response({
#         "new_student_data": json.load(open(paths.static("student_data.js")))
#     })


# @learning_observer.auth.teacher
# async def generated_student_data_handler(request):
#     '''
#     Populate static / mock-up dashboard with static fake data dynamically
#     '''
#     # module_id = request.match_info['module_id']
#     # course_id = int(request.match_info['course_id'])

#     return aiohttp.web.json_response({
#         "new_student_data": synthetic_student_data.synthetic_data()
#     })
