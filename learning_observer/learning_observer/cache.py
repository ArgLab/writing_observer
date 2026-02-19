import functools
import json

import learning_observer.kvs
import learning_observer.prestartup
from learning_observer.log_event import debug_log

cache_backend = None


def create_key_from_args(func, *args, **kwargs):
    key_dict = {'func': str(func.__name__), 'args': args, 'kwargs': kwargs}
    key_str = json.dumps(key_dict, sort_keys=True)
    return key_str

@learning_observer.prestartup.register_startup_check
def connect_to_memoization_kvs():
    global cache_backend
    try:
        cache_backend = learning_observer.kvs.KVS.memoization()
    except AttributeError:
        error_text = 'The memoization KVS is not configured.\n'\
            'Please add a `memoization` kvs item to the `kvs` '\
            'key in `creds.yaml`.\n'\
            '```\nmemoization:\n  type: stub\n```\nOR\n'\
            '```\nmemoization:\n  type: redis_ephemeral\n  expiry: 60\n```'
        debug_log(f'WARNING:: {error_text}')
        # raise learning_observer.prestartup.StartupCheck("KVS: "+error_text)


def async_memoization():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # if the memoization cache is absent, just run the function
            if cache_backend is None:
                return await func(*args, **kwargs)

            # process item if the cache is present
            key = create_key_from_args(func, args, kwargs)
            if key in await cache_backend.keys():
                return await cache_backend[key]
            result = await func(*args, **kwargs)
            await cache_backend.set(key, result)
            return result
        return wrapper
    return decorator
