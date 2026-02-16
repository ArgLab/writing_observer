'''
This file is designed to take an execution DAG (as a JSON object),
a set of parameters, and execute those queries.

The executor processes the `execution_dag` portion of our request.
'''
import asyncio
import collections
import concurrent.futures
import functools
import inspect
import weakref

import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.util
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.settings
import learning_observer.stream_analytics.fields
import learning_observer.stream_analytics.helpers
from learning_observer.log_event import debug_log
from learning_observer.util import get_nested_dict_value, clean_json, ensure_async_generator, async_zip
from learning_observer.communication_protocol.exception import DAGExecutionException


class _SharedAsyncIterable:
    """Fan out one async iterable to multiple consumers without runaway memory use.

    The execution DAG can reuse a single async iterable in multiple downstream nodes.
    We do not want to eagerly drain the source in a background task, because that
    defeats backpressure and retains every item indefinitely. This wrapper only
    pulls items when a consumer needs them and discards items once every consumer
    has advanced past them.
    """
    def __init__(self, source):
        self._source = source
        self._source_iter = source.__aiter__()
        self._buffer = []
        self._start_index = 0
        self._done = False
        self._exception = None
        self._condition = asyncio.Condition()
        self._fetch_lock = asyncio.Lock()
        self._iterators = weakref.WeakSet()

    async def _fetch_next(self, target_index):
        async with self._fetch_lock:
            async with self._condition:
                if self._exception is not None or self._done:
                    return
                if target_index < self._start_index + len(self._buffer):
                    return
            # Only fetch when a consumer needs a new item to avoid eager draining.
            try:
                item = await self._source_iter.__anext__()
            except StopAsyncIteration:
                async with self._condition:
                    self._done = True
                    self._condition.notify_all()
                return
            except Exception as e:
                async with self._condition:
                    self._exception = e
                    self._done = True
                    self._condition.notify_all()
                raise
            async with self._condition:
                self._buffer.append(item)
                self._condition.notify_all()

    async def _trim_buffer(self):
        async with self._condition:
            if not self._iterators:
                # No active consumers, so we can drop everything immediately.
                self._start_index += len(self._buffer)
                self._buffer.clear()
                return
            # Drop any buffered items that all active consumers have passed.
            min_index = min(iterator._index for iterator in self._iterators)
            trim_count = min_index - self._start_index
            if trim_count > 0:
                del self._buffer[:trim_count]
                self._start_index = min_index

    def _discard_iterator(self, iterator):
        if iterator not in self._iterators:
            return
        self._iterators.discard(iterator)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        # Schedule trimming outside of __del__ to avoid blocking finalization.
        loop.create_task(self._trim_buffer())

    def __aiter__(self):
        iterator = _SharedAsyncIterator(self)
        self._iterators.add(iterator)
        return iterator


class _SharedAsyncIterator:
    """Advance through the shared buffer and coordinate with other consumers."""
    def __init__(self, shared):
        self._shared = shared
        self._index = shared._start_index

    async def __anext__(self):
        while True:
            async with self._shared._condition:
                buffer_offset = self._index - self._shared._start_index
                if buffer_offset < len(self._shared._buffer):
                    item = self._shared._buffer[buffer_offset]
                    self._index += 1
                    break
                if self._shared._exception is not None:
                    raise self._shared._exception
                if self._shared._done:
                    raise StopAsyncIteration
            # Trigger a fetch if we are caught up with the shared buffer.
            await self._shared._fetch_next(self._index)
        await self._shared._trim_buffer()
        return item

    def __del__(self):
        self._shared._discard_iterator(self)


dispatch = learning_observer.communication_protocol.query.dispatch


def unimplemented_handler(*args, **kwargs):
    """
    We use a handler for mapping different types of nodes to their appropriate
    functions in an execution DAG.
    This function is used as a default when the function for a given node is not found.
    """
    raise DAGExecutionException(
        'Unimplemented function',
        inspect.currentframe().f_code.co_name,
        {'args': args, 'kwargs': kwargs}
    )


DISPATCH = collections.defaultdict(lambda: unimplemented_handler)


def handler(name):
    """
    Add mapping for nodes of type `name` in an execution DAG
    to their appropriate server-side functions.
    Raises an exception when duplicate names are found
    """
    def decorator(f):
        if name in DISPATCH:
            raise DAGExecutionException(
                f'Duplicate entry for {name} found.',
                inspect.currentframe().f_code.co_name,
                {'handler': name, 'new_function': f, 'prior_function': DISPATCH[name]}
            )
        DISPATCH[name] = f
        return f
    return decorator


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.CALL)
async def call_dispatch(functions, function_name, args, kwargs):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.CALL node.
    This is used when users want to call functions on the server and use their
    output within an execution DAG. Some of these functions include:
    * `courseroster(request, course_id)`
    * `process_document_data(text)`

    We run the function, `function_name`, in `functions` with any `args` or
    `kwargs` and return the result.

    Generic double function for testing
    >>> def double(x):
    ...     if x is None:
    ...         raise ValueError("Input cannot be None")
    ...     return x * 2

    Simple call to double with args [1]
    >>> asyncio.run(call_dispatch({'double': double}, 'double', [1], {}))
    2

    Raises an exception when function `nonexistent` is not found.
    >>> asyncio.run(call_dispatch({'double': double}, 'nonexistent', [1], {}))
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Function nonexistent did not execute properly during call.', 'call_dispatch', {'function_name': 'nonexistent', 'args': [1], 'kwargs': {}, 'error': "'nonexistent'"}, ...)


    Raises an exception when the called function raises an exception.
    >>> asyncio.run(call_dispatch({'double': double}, 'double', [None], {}))
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Function double did not execute properly during call.', 'call_dispatch', {'function_name': 'double', 'args': [None], 'kwargs': {}, 'error': 'Input cannot be None'}, ...)
    """
    # TODO add in provenance to the call
    # this probably requires switching to an async generator instead of regular return
    provenance = {'function_name': function_name, 'args': args, 'kwargs': kwargs}
    try:
        function = functions[function_name]
        result = function(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
    except Exception as e:
        raise DAGExecutionException(
            f'Function {function_name} did not execute properly during call.',
            inspect.currentframe().f_code.co_name,
            {'function_name': function_name, 'args': args, 'kwargs': kwargs, 'error': str(e)},
            e.__traceback__
        )
    return result


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER)
def substitute_parameter(parameter_name, parameters, required, default):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.PARAMETER node.
    This function is used to substitute parameters provided by the user into future
    nodes. When defining the node, a default may be provided.

    Standard scenario fetching a required parameter
    >>> substitute_parameter('param1key', {'param1key': 'param1val'}, True, None)
    'param1val'

    Standard scenario fetching a nonexistent optional parameter and using the default
    >>> substitute_parameter('param2key', {'param1key': 'param1val'}, False, 'defaultvalue')
    'defaultvalue'

    Raise an exception when a required parameter is missing
    >>> substitute_parameter('param2key', {'param1key': 'param1val'}, True, None)
    Traceback (most recent call last):
      ...
    learning_observer.communication_protocol.exception.DAGExecutionException: ('Required parameter `param2key` was not found in parameters.', 'substitute_parameter', {'parameter_name': 'param2key', 'parameters': {'param1key': 'param1val'}})
    """
    if parameter_name not in parameters:
        if required:
            raise DAGExecutionException(
                f'Required parameter `{parameter_name}` was not found in parameters.',
                inspect.currentframe().f_code.co_name,
                {'parameter_name': parameter_name, 'parameters': parameters}
            )
        else:
            return default
    return parameters[parameter_name]


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.JOIN)
async def handle_join(left, right, left_on, right_on):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.JOIN node.
    Users will use this when they want to combine the output of multiple nodes.

    Both `left_on` and `right_on` support nested dot notation. That is,
    ```python
    some_dict = {'some': {'nested': {'key': 'value'}}}
    normal_access = some_dict['some']['nested']['key']
    dot_access = get_nested_dict_value(some_dict, 'some.nested.key')
    assert(normal_access == dot_access)
    ```

    Generic join where left.lid == right.rid
    >>> asyncio.run(async_generator_to_list(handle_join(
    ...     left=[{'lid': 1, 'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'rid': 2, 'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )))
    [{'lid': 1, 'left': True, 'rid': 1, 'right': True}, {'lid': 2, 'left': True, 'rid': 2, 'right': True}]

    We return every item in `left` even if they do not have a matching item
    in `right`. This also demonstrates the behavior for `RIGHT_ON` not being found in
    one of the elements of `right`.
    >>> asyncio.run(async_generator_to_list(handle_join(
    ...     left=[{'lid': 1, 'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )))
    [{'lid': 1, 'left': True, 'rid': 1, 'right': True}, {'lid': 2, 'left': True}]

    When `LEFT_ON` is not found, we return an whatever is in `left`.
    >>> asyncio.run(async_generator_to_list(handle_join(
    ...     left=[{'left': True}, {'lid': 2, 'left': True}],
    ...     right=[{'rid': 2, 'right': True}, {'rid': 1, 'right': True}],
    ...     left_on='lid', right_on='rid'
    ... )))
    [{'left': True}, {'lid': 2, 'left': True, 'rid': 2, 'right': True}]
    """
    right_dict = {}
    async for d in ensure_async_generator(right):
        try:
            nested_value = get_nested_dict_value(d, right_on)
            right_dict[nested_value] = d
        except KeyError as e:
            pass
    async for left_dict in ensure_async_generator(left):
        try:
            lookup_key = get_nested_dict_value(left_dict, left_on)
            right_dict_match = right_dict.get(lookup_key)
            if right_dict_match:
                merged_dict = {**left_dict, **right_dict_match}
            else:
                # defaults to left_dict if not match isn't found
                merged_dict = left_dict
            yield merged_dict
        except KeyError as e:
            # TODO should we throw an error if we can't find a match in
            # right or should we just yield left as is?
            yield left_dict
            # result.append(DAGExecutionException(
            #     f'KeyError: key `{left_on}` not found in `{left_dict.keys()}`',
            #     inspect.currentframe().f_code.co_name,
            #     {'target': left_dict, 'key': left_on, 'exception': e}
            # ).to_dict())


async def map_coroutine_serial(func, values, value_path):
    """
    We call map for coroutine functions operating in serial.
    See the `handle_map` function for more details regarding parameters.
    """
    async for v in ensure_async_generator(values):
        try:
            yield await func(get_nested_dict_value(v, value_path)), v
        except Exception as e:
            yield e, v


async def map_coroutine_parallel(func, values, value_path):
    """
    We call map for coroutine functions operating in parallel.
    See the `handle_map` function for more details regarding parameters.
    """
    async def _return_result_and_value(v):
        '''Wrapper for the function to return both the result and
        the value passed in. The value is yielded to annotate the
        results metadata.
        '''
        try:
            result = await func(get_nested_dict_value(v, value_path))
        except Exception as e:
            result = e
        return result, v

    tasks = []
    async for v in ensure_async_generator(values):
        tasks.append(_return_result_and_value(v))
    for task in asyncio.as_completed(tasks):
        task_result, task_value = await task
        yield task_result, task_value


async def map_parallel(func, values, value_path):
    """
    We call map for synchronous functions operating in parallel.
    See the `handle_map` function for more details regarding parameters.
    """
    def _return_result_and_value(v):
        '''Wrapper for the function to return both the result and
        the value passed in. The value is yielded to annotate the
        results metadata.
        '''
        try:
            result = func(get_nested_dict_value(v, value_path))
        except Exception as e:
            result = e
        return result, v

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        async for v in ensure_async_generator(values):
            futures.append(loop.run_in_executor(executor, _return_result_and_value, v))
        for future in asyncio.as_completed(futures):
            future_result, future_value = await future
            yield future_result, future_value


async def map_serial(func, values, value_path):
    """
    We call map for synchronous functions operating in serial.
    See the `handle_map` function for more details regarding parameters.
    """
    async for v in ensure_async_generator(values):
        try:
            yield func(get_nested_dict_value(v, value_path)), v
        except Exception as e:
            yield e, v


async def _annotate_map_results_with_metadata(function, results, value_path, func_kwargs):
    """
    Each of the map functions yields the result (or errors) along with the value.
    This function processes the output and the provenance to be further used in
    the communicaton protocol.
    If the result from the map is a dictionary, we use that as our base output.
    If the result from the map is just a value, we wrap it in a dictionary.
    If the result is an Exception, we wrap it in a DAGExecutionException and
    use that as our result. This allows for some items to fail while others
    were processed just fine.
    Lastly, the provenance is added to our result.
    """
    async for map_result, item in results:
        provenance = {
            'function': function,
            'func_kwargs': func_kwargs,
            'value': {k: v for k, v in item.items() if k != 'provenance'},
            'value_path': value_path,
            'provenance': item['provenance'] if 'provenance' in item else {}
        }
        if isinstance(map_result, dict):
            out = map_result
        elif isinstance(map_result, Exception):
            error_provenance = provenance.copy()
            error_provenance['error'] = str(map_result)
            out = DAGExecutionException(
                f'Function {function} did not execute properly during map.',
                inspect.currentframe().f_code.co_name,
                error_provenance,
                map_result.__traceback__
            ).to_dict()
        else:
            out = {'output': map_result}
        out['provenance'] = provenance
        yield out


MAPS = {
    'map_parallel': map_parallel,
    'map_serial': map_serial,
    'map_coroutine_parallel': map_coroutine_parallel,
    'map_coroutine_serial': map_coroutine_serial
}


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.MAP)
async def handle_map(functions, function_name, values, value_path, func_kwargs=None, parallel=False):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.MAP node.
    Users can run a single function across a set of values.

    We fetch the function found under `function_name` in the `functions` dictionary and
    apply any `func_kwargs` to it before calling the map function. The function is ran
    over the value found at `value_path` under each value in `values`. The `value_path`
    parameter supports dot notation.

    Generic double function for testing
    >>> def double(x):
    ...     if not isinstance(x, int):
    ...         raise ValueError("Input must be an int")
    ...     return x * 2

    >>> async def process_map_test_result(func):
    ...     '''The map functions return an async generator.
    ...     This function awaits the creation of the generator and drives it.
    ...     '''
    ...     result = await func
    ...     return await async_generator_to_list(result)

    Generic example of mapping a double function over [0, 1].
    >>> asyncio.run(process_map_test_result(handle_map({'double': double}, 'double', [{'path': i} for i in range(2)], 'path')))
    [{'output': 0, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 0}, 'value_path': 'path', 'provenance': {}}}, {'output': 2, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 1}, 'value_path': 'path', 'provenance': {}}}]

    Exceptions in each function with in the map are returned with normal results
    and handled later by the DAG executor. In our text, we return both a normal result
    and the result of an exception being caught.
    >>> asyncio.run(process_map_test_result(handle_map({'double': double}, 'double', [{'path': i} for i in [1, 'fail']], 'path')))
    [{'output': 2, 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 1}, 'value_path': 'path', 'provenance': {}}}, {'error': 'Function double did not execute properly during map.', 'function': '_annotate_map_results_with_metadata', 'error_provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 'fail'}, 'value_path': 'path', 'provenance': {}, 'error': 'Input must be an int'}, 'timestamp': ..., 'traceback': ..., 'provenance': {'function': 'double', 'func_kwargs': {}, 'value': {'path': 'fail'}, 'value_path': 'path', 'provenance': {}}}]

    Example of trying to call nonexistent function, `triple`
    >>> asyncio.run(process_map_test_result(handle_map({'double': double}, 'triple', [{'path': i} for i in range(2)], 'path')))
    [{'error': 'Could not find function `triple` in available functions.', 'function': 'handle_map', 'error_provenance': {'function_name': 'triple', 'available_functions': dict_keys(['double']), 'error': "'triple'"}, 'timestamp': ..., 'traceback': ...}]
    """
    if func_kwargs is None:
        func_kwargs = {}
    try:
        func = functions[function_name]
    except KeyError as e:
        exception = DAGExecutionException(
            f'Could not find function `{function_name}` in available functions.',
            inspect.currentframe().f_code.co_name,
            {'function_name': function_name, 'available_functions': functions.keys(), 'error': str(e)},
            e.__traceback__
        ).to_dict()
        return ensure_async_generator(exception)
    func_with_kwargs = functools.partial(func, **func_kwargs)
    is_coroutine = inspect.iscoroutinefunction(func)
    map_function = MAPS[f'map{"_coroutine" if is_coroutine else ""}_{"parallel" if parallel else "serial"}']

    results = map_function(func_with_kwargs, values, value_path)
    if inspect.isawaitable(results):
        results = await results

    output = _annotate_map_results_with_metadata(function_name, results, value_path, func_kwargs)
    return output


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.SELECT)
async def handle_select(keys, fields=learning_observer.communication_protocol.query.SelectFields.Missing):
    """
    We dispatch this function whenever we process a DISPATCH_MODES.SELECT node.
    This function is used to select data from a kvs. The data being selected
    is usually the output or the default from a reducer.

    Currently, we only select data from the default learning_observer kvs.
    TODO pass kvs as a parameter

    This function expects a list of dicts that contain a 'key' attribute as well
    as which fields to include. The fields should be specified as a dictionary
    where the keys are the dot notation you are looking for and the values are
    the key they are returned under.

    TODO add in test cases once we pass kvs as a parameter
    """
    fields_to_keep = fields
    if fields is None or fields == learning_observer.communication_protocol.query.SelectFields.Missing:
        fields_to_keep = {}

    # Collect all keys from the async generator
    keys_list = []
    async for k in ensure_async_generator(keys):
        if isinstance(k, dict) and 'key' in k:
            keys_list.append(k)
        else:
            raise DAGExecutionException(
                f'Key not formatted correctly for select: {k}',
                inspect.currentframe().f_code.co_name,
                {'keys': keys, 'fields': fields}
            )

    # Batch fetch all values from KVS
    kvs = learning_observer.kvs.KVS()
    kvs_keys = [k['key'] for k in keys_list]
    resulting_values = await kvs.multiget(kvs_keys)

    # Process each key and its corresponding value
    for k, resulting_value in zip(keys_list, resulting_values):
        query_response_element = {
            'provenance': {
                'key': k['key'],
                'provenance': k['provenance']
            }
        }

        # Use default value if KVS returned None
        if resulting_value is None:
            resulting_value = k.get('default', None)

        # Determine fields to keep based on the current resulting_value if fields is All
        if fields == learning_observer.communication_protocol.query.SelectFields.All:
            current_fields_to_keep = {key: key for key in resulting_value.keys() if key != 'provenance'} if resulting_value else {}
        else:
            current_fields_to_keep = fields_to_keep

        # Populate the query response element with the specified fields
        for f in current_fields_to_keep:
            try:
                value = get_nested_dict_value(resulting_value, f)
            except KeyError as e:
                value = DAGExecutionException(
                    f'KeyError: key `{f}` not found in `{resulting_value.keys()}`',
                    inspect.currentframe().f_code.co_name,
                    {'target': resulting_value, 'key': f, 'exception': e}
                ).to_dict()
            query_response_element[current_fields_to_keep[f]] = value

        yield query_response_element


def _normalize_scope_field_key(key):
    return str(key).strip().lower()


def _scope_field_candidates(field):
    if isinstance(field, learning_observer.stream_analytics.fields.KeyField):
        base = field.name
        plural = f'{base.lower()}s'
        if base == 'CLASS':
            plural = 'classes'
        return [
            base,
            f'KeyField.{base}',
            base.lower(),
            plural
        ]

    if isinstance(field, learning_observer.stream_analytics.helpers.EventField):
        base = field.event
        candidates = [
            base,
            f'EventField.{base}',
            base.lower(),
            base.upper()
        ]
        if base == 'doc_id':
            candidates.extend(['RESOURCE', 'RESOURCES', 'resource', 'resources'])
        return candidates

    return []


# ==============================================================================
# Scope Value Handling
# ==============================================================================
#
# Scope fields can be specified as:
# 1. A single value (string, None, etc.) - broadcast across all items
# 2. An iterable of values - one per scope entry
# 3. An async iterable - same as above, but async
#
# SingleValue wraps case 1 to distinguish it from iterables.


class SingleValue:
    """Wrapper indicating a single value to broadcast across all scope items.

    When building keys across multiple scope dimensions, single values are
    repeated infinitely so they can be zipped with finite iterables from
    other dimensions.

    Example: student="bob_id" with documents=[doc1, doc2, doc3] produces
    keys for (bob_id, doc1), (bob_id, doc2), (bob_id, doc3).
    """
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'SingleValue({self.value!r})'


def _is_single_value(value):
    """Check if value is a SingleValue wrapper."""
    return isinstance(value, SingleValue)


def _normalize_scope_value(value):
    """Normalize a scope field value for consistent handling.

    - None, strings, and other scalars become SingleValue (broadcast)
    - Lists and iterables pass through (one item per scope entry)
    - Async iterables pass through unchanged
    - Dicts pass through (will be iterated or accessed via path)
    """
    if value is None:
        return SingleValue(None)
    if _is_single_value(value):
        return value
    if isinstance(value, collections.abc.AsyncIterable):
        return value
    if isinstance(value, (str, bytes)):
        return SingleValue(value)
    if isinstance(value, dict):
        # Dicts represent structured data, not a collection to iterate
        return value
    if isinstance(value, collections.abc.Iterable):
        return value
    return SingleValue(value)


async def _repeat_forever(value):
    """Async generator that yields the same value indefinitely."""
    while True:
        yield value


def _expand_scope_value(value, *, broadcast=False):
    """Convert a normalized scope value to an iterable.

    Args:
        value: A normalized scope value (SingleValue or iterable).
        broadcast: If True, single values repeat infinitely for zipping
                   with other dimensions. If False, yield once.

    Returns:
        An iterable (sync or async) suitable for iteration.
    """
    if _is_single_value(value):
        return _repeat_forever(value.value) if broadcast else [value.value]
    return value


def _parse_scope_spec(spec):
    """Parse a scope specification into (values, path).

    Supports formats:
        roster                                    -> (roster, None)
        {"values": roster, "path": "user_id"}    -> (roster, "user_id")
        {"value": roster}                        -> (roster, None)

    Returns:
        Tuple of (values, path) where path may be None.
    """
    if not isinstance(spec, dict):
        return spec, None

    # Check for known value keys in priority order
    for key in ('values', 'value', 'items', 'data'):
        if key in spec:
            values = spec[key]
            path = spec.get('path') or spec.get('value_path')
            return values, path

    # No recognized keys - treat entire dict as the value
    return spec, None


def _normalize_scope_field_specs(raw_specs):
    """Normalize scope field specifications to a consistent format.

    Returns:
        Dict mapping normalized field names to {"values": ..., "path": ...}
    """
    normalized = {}
    for key, spec in raw_specs.items():
        normalized_key = _normalize_scope_field_key(key)
        values, path = _parse_scope_spec(spec)
        normalized[normalized_key] = {
            'values': _normalize_scope_value(values),
            'path': path
        }
    return normalized


def _provenance_key_for_field(field):
    if isinstance(field, learning_observer.stream_analytics.fields.KeyField):
        return field.name
    if isinstance(field, learning_observer.stream_analytics.helpers.EventField):
        if field.event == 'doc_id':
            return 'RESOURCE'
        return f'EventField.{field.event}'
    return str(field)


async def _async_zip_many(iterables):
    generators = [ensure_async_generator(it) for it in iterables]
    try:
        while True:
            values = await asyncio.gather(*[gen.__anext__() for gen in generators])
            yield values
    except StopAsyncIteration:
        return


async def _extract_fields_with_provenance(scope_specs):
    """Prepare the key field dictionary and provenance for each scope tuple."""
    if not scope_specs:
        return

    if len(scope_specs) == 1:
        # Single dimension: simple iteration
        field, values, path = scope_specs[0]
        async for item in ensure_async_generator(_expand_scope_value(values, broadcast=False)):
            field_value = get_nested_dict_value(item, path or '', '')
            fields = {field: field_value}
            item_provenance = item.get('provenance', {'value': item}) if isinstance(item, dict) else {'value': item}
            if path:
                item_provenance[path] = field_value
            provenance = {_provenance_key_for_field(field): item_provenance}
            yield fields, provenance
        return

    # Multiple dimensions: zip with broadcasting for single values
    # Avoid infinite iteration when all dimensions are single values.
    broadcast = not all(_is_single_value(values) for _, values, _ in scope_specs)
    iterables = [_expand_scope_value(values, broadcast=broadcast) for _, values, _ in scope_specs]

    async for items in _async_zip_many(iterables):
        fields = {}
        provenance = {}
        for (field, _, path), item in zip(scope_specs, items):
            field_value = get_nested_dict_value(item, path or '', '')
            fields[field] = field_value
            item_provenance = item.get('provenance', {'value': item}) if isinstance(item, dict) else {'value': item}
            if path:
                item_provenance[path] = field_value
            provenance[_provenance_key_for_field(field)] = item_provenance
        yield fields, provenance


def _resolve_scope_specs(scope, kwargs):
    scope_specs = {}
    raw_scope_specs = kwargs.get('scope_fields', {})
    if isinstance(raw_scope_specs, dict):
        scope_specs.update(_normalize_scope_field_specs(raw_scope_specs))

    allowed_scope_keys = set()
    for field in scope:
        allowed_scope_keys.update(
            _normalize_scope_field_key(candidate)
            for candidate in _scope_field_candidates(field)
        )

    for key, value in kwargs.items():
        if key in {'scope_fields', 'STUDENTS', 'STUDENTS_path', 'RESOURCES', 'RESOURCES_path'}:
            continue
        if key.endswith('_path'):
            continue
        path_key = f"{key}_path"
        if path_key in kwargs:
            scope_specs.setdefault(
                _normalize_scope_field_key(key),
                {'values': _normalize_scope_value(value), 'path': kwargs[path_key]}
            )

    if 'STUDENTS' in kwargs:
        scope_specs.setdefault(
            'student',
            {'values': _normalize_scope_value(kwargs['STUDENTS']), 'path': kwargs.get('STUDENTS_path')}
        )
    if 'RESOURCES' in kwargs:
        scope_specs.setdefault(
            'doc_id',
            {'values': _normalize_scope_value(kwargs['RESOURCES']), 'path': kwargs.get('RESOURCES_path')}
        )

    unexpected_scope_keys = set(scope_specs.keys()) - allowed_scope_keys
    if unexpected_scope_keys:
        raise DAGExecutionException(
            'Provided scope fields do not match reducer scope.',
            inspect.currentframe().f_code.co_name,
            {
                'scope': [str(field) for field in scope],
                'unexpected_fields': sorted(unexpected_scope_keys)
            }
        )

    specs = []
    for field in sorted(scope, key=str):
        field_specs = None
        for candidate in _scope_field_candidates(field):
            candidate_key = _normalize_scope_field_key(candidate)
            if candidate_key in scope_specs:
                field_specs = scope_specs[candidate_key]
                break
        if field_specs is None:
            return None
        specs.append((field, field_specs['values'], field_specs.get('path')))

    return specs


def _find_reducer_by_key(function):
    for reducer in learning_observer.module_loader.reducers():
        if reducer.get('id') == function or reducer.get('string_id') == function:
            return reducer
    return None


@handler(learning_observer.communication_protocol.query.DISPATCH_MODES.KEYS)
async def handle_keys(function, **kwargs):
    """
    This function is a HACK that is being used instead of `handle_keys` for any
    `DISPATCH_MODE.KEYS` nodes.

    Whenever a user wants to perform a select operation, they first must make sure their
    keys are formatted properly. This method builds the keys to access the appropriate
    reducers output.

    This function supports creation of keys based on the reducer scope.
    We create a list of fields needed for the `make_key()` function as well as the provenance
    associated with each. These are zipped together and returned to the user.
    """
    # TODO do something if `func` is not found
    func = _find_reducer_by_key(function)
    if func is None:
        return
    scope_specs = _resolve_scope_specs(func.get('scope', []), kwargs)
    if scope_specs is None:
        return
    fields_and_provenances = _extract_fields_with_provenance(scope_specs)

    if fields_and_provenances is None:
        return
    async for f, p in fields_and_provenances:
        key = learning_observer.stream_analytics.helpers.make_key(
            func['function'],
            f,
            learning_observer.stream_analytics.fields.KeyStateType.INTERNAL
        )
        key_wrapper = {
            'key': key,
            'provenance': p,
            'default': func['default']
        }
        yield key_wrapper


def _has_error(node):
    '''
    When executing a DAG, we may return an error. This function returns the first
    error found, so that it can be further bubbled up the execution tree.

    FIXME Possible bottleneck in this code. The following uses DFS when checking
    for errors. Since a DAG can split off and rejoin, we may get iterate over the
    same nodes multiple times. We have simple DAGs, so for now it should not be a
    problem. However, we ought to change this to a BFS or add a visited node tracker.
    '''
    queue = [(node, [])]  # start with the node and an empty path
    while queue:
        current, path = queue.pop(0)
        if 'error' in current:
            return current, path
        for c in current:
            if isinstance(current[c], dict):
                queue.append((current[c], path + [c]))
            elif isinstance(current[c], list):
                for idx, i in enumerate(current[c]):
                    if isinstance(i, dict):
                        queue.append((i, path + [c, idx]))
    return None, []


def _find_error_messages(d):
    '''
    We want to collect all the error messages that occured within the
    communication protocol and return them so they user can clearly
    see what went wrong.
    '''
    errors = []

    def collect_errors(item):
        '''Iterate over each item in the object and return any error
        messages we find
        '''
        if isinstance(item, dict):
            for key, value in item.items():
                if key == 'error' and type(value) == str:
                    errors.append(value)
                else:
                    collect_errors(value)
        elif isinstance(item, list):
            for element in item:
                collect_errors(element)

    collect_errors(d)
    return errors


def strip_provenance(variable):
    '''
    Context is included for debugging purposes, but should not be included
    in deployed settings. This function removes all instances of 'provenance'
    from a variable.

    Generic removal of `provenance` key from dict.
    >>> strip_provenance({'provenance': 123, 'other': 123})
    {'other': 123}

    Removal of `provenance` from list of dicts.
    >>> strip_provenance([{'provenance': 123, 'other': 123}, {'provenance': 123, 'other': 123}, {'provenance': 123, 'other': 123}])
    [{'other': 123}, {'other': 123}, {'other': 123}]

    If we don't have a dict, we do not change or remove anything.
    >>> strip_provenance(1)
    1
    >>> strip_provenance([1, 2, 3])
    [1, 2, 3]

    Each provenance item should appear at the top-level of a dictionary, so
    nested provenance key/value pairs are still included.
    >>> strip_provenance({'nested_dict': {'provenance': 123, 'other': 123}})
    {'nested_dict': {'provenance': 123, 'other': 123}}
    '''
    if isinstance(variable, dict):
        return {key: value for key, value in variable.items() if key != 'provenance'}
    elif isinstance(variable, list):
        return [strip_provenance(item) if isinstance(item, dict) else item for item in variable]
    else:
        return variable


async def _clean_json_via_generator(iterator):
    async for item in ensure_async_generator(iterator):
        yield clean_json(item)


async def execute_dag(endpoint, parameters, functions, target_exports):
    """
    This is the primary way to execute a DAG.
    Users should pass the overall execution dag dict, a dictionary parameters,
    a dictionary of available functions, and a list of exports they wish to
    receive data back for.

    See `learning_observer/communication_protocol/test_cases.py` for usage examples.
    """
    exports = endpoint.get('exports', {})
    nodes = endpoint.get('execution_dag', {})
    visited = set()

    # --- Resolve targets and collect any obvious errors early ---
    target_nodes = []
    target_errors = {}  # maps target node name -> error dict

    for key in target_exports:
        if key not in exports:
            # Unknown export requested
            target_name = f'__missing_export__:{key}'
            target_nodes.append(target_name)
            target_errors[target_name] = DAGExecutionException(
                f'Export `{key}` not found in endpoint.exports.',
                inspect.currentframe().f_code.co_name,
                {'requested_export': key, 'available_exports': list(exports.keys())}
            ).to_dict()
            continue

        target_node = exports[key].get('returns')
        if target_node not in nodes:
            # Export exists, but its `returns` node is missing from the DAG
            target_name = f'__missing_export__:{key}'
            target_nodes.append(target_name)
            target_errors[target_name] = DAGExecutionException(
                f'Target DAG node `{target_node}` not found in execution_dag.',
                inspect.currentframe().f_code.co_name,
                {'target_node': target_node, 'available_nodes': list(nodes.keys())}
            ).to_dict()
            continue

        target_nodes.append(target_node)

    async def dispatch_node(node):
        """
        Dispatch the appropriate server-side function for a given node.
        """
        try:
            if not isinstance(node, dict):
                return node
            if dispatch not in node:
                return node
            node_dispatch = node[dispatch]
            function = DISPATCH[node_dispatch]
            del node[dispatch]
            # make dispatch specific function call
            if node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER:
                result = function(parameters=parameters, **node)
            elif (node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.CALL
                  or node_dispatch == learning_observer.communication_protocol.query.DISPATCH_MODES.MAP):
                result = function(functions=functions, **node)
            else:
                result = function(**node)
            if inspect.isawaitable(result):
                result = await result
            return result
        except DAGExecutionException as e:
            return e.to_dict()

    async def walk_dict(node_dict):
        """
        We walk through the execution DAG backwards. We visit any variable nodes
        we find and cache their stored value.
        """
        for child_key, child_value in list(node_dict.items()):
            if isinstance(child_value, dict) and dispatch in child_value and child_value[dispatch] == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
                node_dict[child_key] = await visit(child_value['variable_name'])
            elif isinstance(child_value, dict):
                await walk_dict(child_value)

    async def visit(node_name):
        """
        When executing the DAG, we `visit()` nodes that we want output from.
        These will either be specified as target_nodes or be any descendents
        of the target_nodes.

        If we've already visited a node, we return the result.
        If any of the child nodes return errors, we return them.
        """
        # We've already done this one.
        if node_name in visited:
            return nodes[node_name]
        # Execute all the child nodes
        await walk_dict(nodes[node_name])

        # Check for any errors, then dispatch the node
        # if errors are present, we bubble them up the DAG
        error, error_path = _has_error(nodes[node_name])
        if error is not None:
            nodes[node_name] = {
                'error': error,
                'dispatch': nodes[node_name]['dispatch'],
                'error_path': error_path
            }
            error_texts = '\n'.join((f'  {e}' for e in _find_error_messages(error)))
            tb = nodes[node_name]["error"].get("traceback", 'No traceback available')
            debug_log('ERROR:: Error occured within execution dag at '\
                      f'{node_name}\n{tb}\n'\
                      f'{error_texts}')
        else:
            nodes[node_name] = await dispatch_node(nodes[node_name])
            if isinstance(nodes[node_name], collections.abc.AsyncIterable) and not isinstance(nodes[node_name], _SharedAsyncIterable):
                nodes[node_name] = _SharedAsyncIterable(nodes[node_name])


        visited.add(node_name)
        return nodes[node_name]

    out = {}
    async_iterable_cache = {}
    for e in target_nodes:
        if e in target_errors:
            out[e] = _clean_json_via_generator(target_errors[e])
            continue

        node_result = await visit(e)
        if isinstance(node_result, collections.abc.AsyncIterable):
            shared_iterable = async_iterable_cache.get(id(node_result))
            if shared_iterable is None:
                shared_iterable = node_result
                async_iterable_cache[id(node_result)] = shared_iterable
            out[e] = _clean_json_via_generator(shared_iterable)
            continue

        out[e] = _clean_json_via_generator(node_result)


    return out

    # Include execution history in output if operating in development settings
    if learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV:
        return {e: _clean_json_via_generator(await visit(e)) for e in target_nodes}
    # HACK currently `dashboard.py` relies on the provenance to tell users which
    # items need updating, such as John Doe's history essay. This ought to be
    # handled by the communication protocol during execution. Once that occurs,
    # we can go back to stripping the provenance out.
    return {e: _clean_json_via_generator(await visit(e)) for e in target_nodes}
    # TODO test this code to make sure it works with async generators
    # Remove execution history if in deployed settings, with data flowing back to teacher dashboards
    return {e: _clean_json_via_generator(strip_provenance(await visit(e))) for e in target_nodes}


if __name__ == "__main__":
    import doctest
    # This function is used by doctests
    from learning_observer.util import async_generator_to_list

    doctest.testmod(optionflags=doctest.ELLIPSIS)