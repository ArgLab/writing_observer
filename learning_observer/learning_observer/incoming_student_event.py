'''
This has event handlers for incoming student events.

These should come in over a websocket. We support AJAX too, since it's
nice for debugging. This should never be used in production.

We:
* Authenticate (minimally, for now, see docs)
* Run these through a set of reducers
'''

import asyncio
import datetime
import inspect
import json
import logging
import os
import time
import traceback
import uuid
import weakref

import aiohttp

import learning_observer.log_event as log_event
import learning_observer.paths as paths

import learning_observer.auth.utils as authutils               # Encoded / decode user IDs
import learning_observer.stream_analytics as stream_analytics  # Individual analytics modules

import learning_observer.settings as settings

import learning_observer.stream_analytics.helpers

from learning_observer.log_event import debug_log

import learning_observer.exceptions

import learning_observer.auth.events
import learning_observer.adapters.adapter
import learning_observer.blacklist
import learning_observer.blob_storage
import learning_observer.merkle_store as merkle_store

import learning_observer.constants as constants

logger = logging.getLogger(__name__)


def compile_server_data(request):
    '''
    We extract some basic data. In contrast to client data, this data
    cannot be spoofed, and can be super-useful for debugging, as well
    as attack mitigation.
    '''
    return {
        'time': time.time(),
        'origin': request.headers.get('Origin', ''),
        'agent': request.headers.get('User-Agent', ''),
        'ip': request.headers.get('X-Real-IP', ''),
        'executable': 'aio_webapp'
    }


async def student_event_pipeline(metadata):
    '''
    Create an event pipeline, based on header metadata
    '''
    client_source = None

    if "source" not in metadata:
        analytics_modules = []
        debug_log("Missing client source!")
        print("We are missing a client source. This should never happen. It can mean a few things:")
        print("* Someone is sending us malformed events, either due to a cyberattack or due to a client bug")
        print("* We've got a bug in how we extract metadata")
        print("* Something else?")
        print("This should probably not be ignored.")
        print("We used to raise a SuspiciousOperation exception, but it's surprisingly easy to lose data to a")
        print("bug, so we log the data now instead, but with no reducers. This decision might be re-evaluated")
        print("as the system matures")
        client_source = "org.ets.generic"
    else:
        client_source = metadata["source"]
        debug_log("client_source", client_source)
        debug_log("Module", stream_analytics.reducer_modules(client_source))
        analytics_modules = stream_analytics.reducer_modules(client_source)

    # Create an event processor for this user
    # TODO:
    # * Thing like this (esp. below) should happen in parallel:
    #   https://stackoverflow.com/questions/57263090/async-list-comprehensions-in-python
    # * We should create cached modules for each key, rather than this partial evaluation
    #   kludge
    async def prepare_reducer(analytics_module):
        '''
        Prepare a reducer for the analytics module. Note that this is in-place (the
        field is mutated).
        '''
        f = analytics_module['reducer']
        # We're moving to this always being a co-routine. This is
        # backwards-compatibility code which should be remove,
        # eventually. We started with a function, and had an interrim
        # period where both functions and co-routines worked.
        if not inspect.iscoroutinefunction(f):
            debug_log("Not a coroutine", analytics_module)
            raise AttributeError("The reducer {} should be a co-routine".format(analytics_module))

        analytics_module['reducer_partial'] = await analytics_module['reducer'](metadata)
        return analytics_module

    analytics_modules = await asyncio.gather(*[prepare_reducer(am) for am in analytics_modules])

    async def pipeline(parsed_message):
        '''
        And this is the pipeline itself. It takes messages, processes them,
        and, optionally, will inform consumers when there is new data (disabled
        in the current code, since we use polling).
        '''
        if type(parsed_message) is not dict:
            raise ValueError(f"Expected a dict, got {type(parsed_message)}")
        if 'client' not in parsed_message:
            raise ValueError("Expected a dict with a 'client' field")
        if 'event' not in parsed_message['client']:
            raise ValueError("Expected a dict with a 'client' field with an 'event' field")

        debug_log("Processing message {event} from {source}".format(
            event=parsed_message["client"]["event"], source=client_source
        ))

        # Try to run a message through all event processors.
        #
        # To do: Finer-grained exception handling. Right now, if we break, we
        # don't even run through the remaining processors.
        try:
            processed_analytics = []
            # Go through all the analytics modules
            for am in analytics_modules:
                debug_log("Scope", am['scope'])
                event_fields = {}
                skip = False
                for field in am['scope']:
                    if isinstance(field, learning_observer.stream_analytics.helpers.EventField):
                        debug_log("event", parsed_message)
                        debug_log("field", field)
                        client_event = parsed_message.get('client', {})
                        if field.event not in client_event:
                            debug_log(field.event, "not found")
                            skip = True
                        event_fields[field.event] = client_event.get(field.event)
                if not skip:
                    debug_log("args", event_fields)
                    processed_analytics.append(await am['reducer_partial'](parsed_message, event_fields))
        except Exception as e:
            traceback.print_exc()
            filename = paths.logs("critical-error-{ts}-{rnd}.tb".format(
                ts=datetime.datetime.now().isoformat(),
                rnd=uuid.uuid4().hex
            ))
            fp = open(filename, "w")
            fp.write(json.dumps(parsed_message, sort_keys=True, indent=2))
            fp.write("\nTraceback:\n")
            fp.write(traceback.format_exc())
            fp.close()
            if settings.RUN_MODE == settings.RUN_MODES.DEV:
                raise
        return processed_analytics
    return pipeline

COUNTER = 0


async def handle_incoming_client_event(metadata):
    '''
    Common handler for both Websockets and AJAX events.

    We do a reduce through the event pipeline, and forward on to
    for aggregation on the dashboard side.
    '''
    global COUNTER
    pipeline = await student_event_pipeline(metadata=metadata)

    filename = "{timestamp}-{counter:0>10}-{username}-{pid}.study".format(
        username=metadata.get("auth", {}).get("safe_user_id", "GUEST"),
        timestamp=datetime.datetime.utcnow().isoformat(),
        counter=COUNTER,
        pid=os.getpid()
    )
    COUNTER += 1

    # The adapter allows us to handle old event formats
    adapter = learning_observer.adapters.adapter.EventAdapter()

    handler_log_closed = False

    def close_handler_log():
        nonlocal handler_log_closed
        if not handler_log_closed:
            log_event.close_logfile(filename)
            handler_log_closed = True

    async def handler(request, client_event):
        '''
        This is the handler for incoming client events.
        '''
        client_event = adapter.canonicalize_event(client_event)
        debug_log("Compiling event for reducer: " + client_event["event"])
        event = {
            "client": client_event,
            "server": compile_server_data(request),
            "metadata": metadata
        }

        # Log to the main event log file
        log_event.log_event(event)
        # Log the same thing to our study log file. This isn't a good final format, since we
        # mix data with auth, but we want this for now.
        log_event.log_event(
            json.dumps(event, sort_keys=True),
            filename, preencoded=True, timestamp=True)
        if client_event.get("event") == "terminate":
            debug_log("Terminate event received; closing handler log file")
            close_handler_log()
            return []
        await pipeline(event)

    # when the handler garbage collected (no more events are being passed through),
    # close the log file associated with this connection
    weakref.finalize(handler, close_handler_log)
    handler.close = close_handler_log

    return handler


COUNT = 0


def event_decoder_and_logger(
    request,
    headers=None,
    metadata=None,
):
    '''
    Main event decoder / logger factory.

    Returns an async generator coroutine that:
    1. Immediately begins decoding and yielding events
    2. Buffers decoded events until the Merkle session is initialized
    3. Flushes the buffer once ``initialize_session(student, tool)`` is called
    4. Streams directly into the Merkle chain from that point on
    5. Closes the session cleanly on disconnect / exhaustion

    Also exposes:
    - ``.close``               - force-close the log/session
    - ``.initialize_session``  - provide identity once known

    If the ``merkle`` feature flag is not set, falls back to the legacy
    flat-file logger (which needs no identity).
    '''

    if merkle_config := settings.feature_flag('merkle'):
        # ---- Merkle path ------------------------------------------------
        storage_cls = merkle_store.STORES[merkle_config['store']]
        params = merkle_config.get('params', {})
        if not isinstance(params, dict):
            raise ValueError('Merkle store params must be a dict')

        storage = storage_cls(**params)
        merkle = merkle_store.Merkle(storage, merkle_store.CATEGORIES)
        async_merkle = merkle_store.AsyncMerkle(merkle)

        # --- Deferred session state ---
        session = None
        session_started = False
        session_closed = False
        pre_session_buffer = []

        async def initialize_session(student, tool):
            '''
            Called once downstream stages have resolved identity.
            Opens the Merkle session and flushes every event that
            was buffered before identity was known.

            Idempotent: subsequent calls are no-ops.
            '''
            nonlocal session, session_started
            if session_started:
                logger.debug(
                    'Merkle session already initialized; ignoring duplicate call'
                )
                return

            session = {
                'student': [student],
                'tool': [tool],
            }

            await async_merkle.start(session, metadata=metadata)

            if headers:
                await async_merkle.event_to_session(
                    {'type': 'header', 'headers': headers},
                    session,
                    label='headers',
                )

            # Replay everything we buffered before identity was known
            for buffered_event in pre_session_buffer:
                await async_merkle.event_to_session(buffered_event, session)
            pre_session_buffer.clear()

            session_started = True
            logger.debug(
                'Merkle session initialized for student=%s tool=%s; '
                'flushed %d buffered events',
                student, tool, len(pre_session_buffer),
            )

        async def close_session():
            nonlocal session_closed
            if session_closed:
                return
            session_closed = True

            if session_started:
                try:
                    await async_merkle.close_session(session)
                except Exception:
                    logger.exception('Failed to close merkle session')
            elif pre_session_buffer:
                # Connection died before we ever learned who the student was.
                # The events are not lost (they're in the buffer), but they
                # never made it into a Merkle chain. Log loudly.
                logger.warning(
                    'Merkle session closed before initialization; '
                    '%d event(s) buffered but never persisted to a session.',
                    len(pre_session_buffer),
                )

        async def decode_and_log_event(events):
            '''Async generator: decode every message, persist to Merkle
            (or buffer), yield downstream.'''
            try:
                async for msg in events:
                    json_event = (
                        msg if isinstance(msg, dict)
                        else json.loads(msg.data)
                    )

                    if session_started:
                        await async_merkle.event_to_session(json_event, session)
                    else:
                        # Identity not yet known — buffer for later flush
                        pre_session_buffer.append(json_event)

                    yield json_event
            except Exception:
                logger.exception('Error in merkle event pipeline')
                raise
            finally:
                await close_session()

        decode_and_log_event.close = close_session
        decode_and_log_event.initialize_session = initialize_session
        return decode_and_log_event

    # ---- Legacy flat-file path (unchanged) --------------------------------

    global COUNT
    filename = '{timestamp}-{ip:-<15}-{hip:-<15}-{session_count:0>10}-{pid}'.format(
        ip=request.remote,
        hip=request.headers.get('X-Real-IP', ''),
        timestamp=datetime.datetime.utcnow().isoformat(),
        session_count=COUNT,
        pid=os.getpid(),
    )
    COUNT += 1

    decoder_log_closed = False

    def close_decoder_logfile():
        nonlocal decoder_log_closed
        if not decoder_log_closed:
            log_event.close_logfile(filename)
            decoder_log_closed = True

    async def decode_and_log_event(events):
        try:
            async for msg in events:
                if isinstance(msg, dict):
                    json_event = msg
                else:
                    json_event = json.loads(msg.data)
                log_event.log_event(json_event, filename=filename)
                yield json_event
        finally:
            close_decoder_logfile()

    decode_and_log_event.close = close_decoder_logfile
    # No-op so callers don't need to branch on which path is active
    async def _noop_init(*args, **kwargs):
        pass
    decode_and_log_event.initialize_session = _noop_init
    return decode_and_log_event


async def failing_event_handler(*args, **kwargs):
    '''
    Give a proper AIO HTTP exception if we don't find an
    appropriate event handler or another error condition happens
    '''
    exception_text = "Event handler not set.\n" \
        "This probably means we do not have proper\n" \
        "metadata sent before the event stream"
    raise aiohttp.web.HTTPBadRequest(text=exception_text)


async def incoming_websocket_handler(request):
    '''This handles incoming WebSocket requests. We pass each event
    through minimal processing before it is added to a queue. Once
    we receive enough initial information (e.g. source and auth),
    we start processing each event in our queue through the reducers.
    '''
    debug_log("Incoming web socket connected")
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)
    lock_fields = {}
    authenticated = False
    reducers_last_updated = None
    event_handler = failing_event_handler

    decoder_and_logger = event_decoder_and_logger(request)

    async def process_message_from_ws():
        '''This function makes sure that the ws is an
        async generator for use in the processing pipeline
        '''
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.ERROR:
                debug_log(f"ws connection closed with exception {ws.exception()}")
                return
            if msg.type != aiohttp.WSMsgType.TEXT:
                debug_log("Unknown event type: " + msg.type)
            yield msg

        if ws.closed:
            debug_log(f'ws connection closed for reason {ws.close_code}')

    async def update_event_handler(event):
        '''We need source and auth ready before we can
        set up the `event_handler` and be ready to process
        events.
        '''
        if not authenticated:
            return False

        nonlocal event_handler, reducers_last_updated
        if 'source' in lock_fields:
            debug_log('Updating the event_handler()')
            metadata = lock_fields.copy()
        else:
            metadata = event
        metadata['auth'] = authenticated

        # ---- Initialize the Merkle session now that we know identity ----
        init_session = getattr(decoder_and_logger, 'initialize_session', None)
        if init_session:
            student = authenticated.get(constants.USER_ID, '')
            tool = metadata.get('source', 'unknown')
            await init_session(student, tool)

        event_handler = await handle_incoming_client_event(metadata=metadata)
        reducers_last_updated = learning_observer.stream_analytics.LAST_UPDATED
        return True

    async def handle_auth_events(events):
        '''This method checks a single method for auth and
        updates our `lock_fields`. If we are unauthenticated,
        an error will be thrown and we ignore it.

        HACK The auth method expects a list of events to find
        specific auth events. Since we are yielding event by
        event, we check for auth on an individual event wrapped
        in a list. This workflow feels a little weird. We should
        re-evaluate the auth code.

        TODO We should consider stopping the loop if we receive
        enough events without receiving the authentication info.
        '''
        nonlocal authenticated
        backlog = []

        async for event in events:
            if 'auth' in event:
                '''
                If 'auth' already exists, this means
                    1. Someone is trying to hack the system
                    2. Someone is restreaming logs into the system
                We should record the current auth to history and
                then remove it from the event. The `.authenticate`
                function will take care of re-authorizing the user.

                TODO determine how to store the auth history and append
                current auth object.
                '''
                del event['auth']

            if not authenticated:
                auth_result = await learning_observer.auth.events.authenticate(
                    request=request,
                    event=event,
                    source=''
                )
                if auth_result:
                    authenticated = auth_result
                    await ws.send_json({
                        'status': 'auth',
                        constants.USER_ID: authenticated[constants.USER_ID]
                    })
                    # This specific event was the one that provided auth.
                    # Tag it so we can skip it during backlog flush.
                    event['_consumed_by_auth'] = True

                await update_event_handler(event)
                backlog.append(event)
            else:
                while backlog:
                    prior_event = backlog.pop(0)
                    # Skip events that were consumed by the auth system.
                    # Content events that just happened to arrive before
                    # auth completed are forwarded normally.
                    if prior_event.get('_consumed_by_auth'):
                        continue
                    prior_event.update({'auth': authenticated})
                    yield prior_event
                event.update({'auth': authenticated})
                yield event

    async def decode_lock_fields(events):
        '''This function updates our overall lock_field
        object and sets those fields on other events.
        '''
        async for event in events:
            if event['event'] == 'lock_fields':
                if 'source' not in event['fields'] or event['fields'].get('source', '') != lock_fields.get('source', ''):
                    lock_fields.update(event['fields'])
            else:
                event.update(lock_fields)
                yield event

    async def handle_terminate_events(events):
        '''Stop processing when a terminate event is received.'''
        async for event in events:
            if event.get('event') == 'terminate':
                debug_log(
                    'Terminate event received; shutting down connection '
                    'and cleaning up logs.'
                )
                handler_close = getattr(event_handler, 'close', None)
                if callable(handler_close):
                    # handler_close is a sync function — call directly
                    handler_close()

                decoder_close = getattr(decoder_and_logger, 'close', None)
                if callable(decoder_close):
                    # May be async (Merkle) or sync (legacy) — handle both
                    result = decoder_close()
                    if asyncio.iscoroutine(result):
                        await result

                await ws.close()
                return
            yield event

    async def filter_blacklist_events(events):
        '''This function stops the event pipeline if sources
        should be blocked.
        '''
        async for event in events:
            # TODO implement the following function
            bl_status = learning_observer.blacklist.get_blacklist_status(event)
            if bl_status['action'] == learning_observer.blacklist.ACTIONS.TRANSMIT:
                yield event
            else:
                debug_log('Event is blacklisted.')
                await ws.send_json(bl_status)
                await ws.close()

    async def process_blob_storage_events(events):
        '''HACK This function manages events related to storing and
        retrieving blobs from server-side storage. It is primarily
        used for LO Assess. Ideally, this functionality should reside
        in an independent module, rather than being directly integrated
        into Learning Observer, as it is currently implemented.
        '''
        async for event in events:
            # Extract metadata
            if event['event'] in ['save_blob', 'fetch_blob']:
                # we previously used the `user_id` key for storing blobs
                # we should be using the `safe_user_id` instead
                safe_user_id = event['auth']['safe_user_id']
                legacy_user_id = event['auth']['user_id']
                source = event['source']
                activity = event['activity']

            # Save, fetch, or ignore (continue)
            if event['event'] == 'save_blob':
                await learning_observer.blob_storage.save_blob(
                    safe_user_id, source, activity,
                    event['blob']
                )
            elif event['event'] == 'fetch_blob':
                # Try fetching via our safe user id and fallback to the legacy user id
                blob = await learning_observer.blob_storage.fetch_blob(
                    safe_user_id, source, activity
                )
                if blob is None and legacy_user_id and legacy_user_id != safe_user_id:
                    blob = await learning_observer.blob_storage.fetch_blob(
                        legacy_user_id, source, activity
                    )
                await ws.send_json({
                    'status': 'fetch_blob',
                    'data': blob
                })
            else:
                yield event

    async def check_for_reducer_update(events):
        '''Check to see if the reducers updated
        '''
        async for event in events:
            if reducers_last_updated != learning_observer.stream_analytics.LAST_UPDATED:
                await update_event_handler(event)
            yield event

    async def pass_through_reducers(events):
        '''Pass events through the reducers
        '''
        async for event in events:
            await event_handler(request, event)
            yield event

    async def process_ws_message_through_pipeline():
        '''Prepare each event we receive for processing
        '''
        events = process_message_from_ws()
        events = decoder_and_logger(events)
        events = decode_lock_fields(events)
        events = handle_terminate_events(events)
        events = handle_auth_events(events)
        events = filter_blacklist_events(events)
        events = process_blob_storage_events(events)
        events = check_for_reducer_update(events)
        events = pass_through_reducers(events)
        # empty loop to start the generator pipeline
        async for event in events:
            pass
        debug_log('We are done passing events through the pipeline.')

    # process websocket messages and begin executing events from the queue
    await process_ws_message_through_pipeline()

    return ws
