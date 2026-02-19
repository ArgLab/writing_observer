'''
Although the target is writing analytics, we would like analytics
to eventually have pluggable modules. To validate that we're
maintaining with the right abstractions in place, we are developing
around several streaming systems:

* Dynamic assessment
* Writing process analytics
* Mirror

This should move into a config file.
'''

import collections
import copy
import functools
import learning_observer.exceptions
import learning_observer.module_loader
import learning_observer.util

from learning_observer.log_event import debug_log

import learning_observer.stream_analytics.time_on_task

REDUCER_MODULES = None
LAST_UPDATED = None


def reducer_modules(source):
    '''
    Helper.

    TODO: Somewhat obsolete, since a lot of this code will migrate into module_loader.
    '''
    global REDUCER_MODULES
    modules = copy.deepcopy(REDUCER_MODULES.get(source, None))
    if modules is None:
        debug_log("Unknown event source: " + str(source))
        debug_log("Known sources: " + repr(REDUCER_MODULES.keys()))
        raise learning_observer.exceptions.SuspiciousOperation("Unknown event source")

    return modules


def async_lambda(function):
    '''Work-around for Python 3 issues with handling async
    functions. This turns a function into an asynchronous one. It
    allows us to make async lambda expressions.
    '''
    @functools.wraps(function)
    async def async_lambda_helper(*args, **kwargs):
        '''
        The async version of our lambda
        '''
        return function(*args, **kwargs)
    return async_lambda_helper


def init():
    '''
    Initialize the stream analytics module. For now, this just populates
    `REDUCER_MODULES`, transformed into an appopriate dictionary format
    for retrieving what we need.

    We also add a loop-back module for testing.

    Probably, we'd rather remove this redundancy, and do this in the
    module loader.
    '''
    import learning_observer.stream_analytics.helpers as helpers
    srm = collections.defaultdict(lambda: list())

    # For debugging; this can go away at some point
    srm['org.mitros.mirror'].append({'reducer': async_lambda(
        lambda metadata: async_lambda(lambda event: event)
    )})

    reducers = learning_observer.module_loader.reducers()
    for reducer in reducers:
        context = reducer['context']
        function = reducer['function']
        scope = reducer.get('scope', helpers.Scope([helpers.KeyField.STUDENT]))
        srm[context].append({
            'reducer': function,
            'scope': scope
        })

    global REDUCER_MODULES, LAST_UPDATED
    REDUCER_MODULES = dict(srm)
    LAST_UPDATED = learning_observer.util.generate_unique_token()
