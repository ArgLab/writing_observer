'''
This was designed as a helper for per-thread connection pooling (we want
just one redis connection). This was necessary with asyncio_redis. We ported
to redis.asyncio, and right now, a lot of this design and code is obsolete.
Right now, it's easy to switch around, but this should be modernized once we're
confident using redis.asyncio. It handles a lot of what we do manually inside
the library.
'''

import pmss
import redis.asyncio

import learning_observer.settings
from learning_observer.log_event import debug_log


pmss.register_field(
    name='redis_host',
    type=pmss.pmsstypes.TYPES.hostname,
    description='Determine the host for the redis_connection. Defaults to localhost.',
    default='localhost'
)
pmss.register_field(
    name='redis_port',
    type=pmss.pmsstypes.TYPES.port,
    description='Determine the port for the redis_connection. Defaults to 6379.',
    default=6379
)
pmss.register_field(
    name='redis_password',
    type=pmss.pmsstypes.TYPES.string,
    description='Password token for connectioning to redis_connection',
    default=None
)


REDIS_CONNECTION = None


async def connect():
    '''
    Connect to redis
    '''
    global REDIS_CONNECTION
    if REDIS_CONNECTION is None:
        REDIS_CONNECTION = redis.asyncio.Redis(
            host=learning_observer.settings.pmss_settings.redis_host(types=['redis_connection']),
            port=learning_observer.settings.pmss_settings.redis_port(types=['redis_connection']),
            # TODO figure out how to properly use None from pmss
            # password=learning_observer.settings.pmss_settings.redis_password(types=['redis_connection'])
        )
        await REDIS_CONNECTION.ping()


async def connection():
    '''
    Returns our connection. Connects if needed.

    This is shorthand. It's not clear if this is the right abstraction,
    since it makes for a mess of awaits.
    '''
    await connect()
    return REDIS_CONNECTION


async def keys():
    '''
    Return all the keys in the database. This might take a while on production
    installs, but is super-helpful in debugging.
    '''
    return [key.decode('utf-8') for key in await (await connection()).keys()]


async def get(key):
    '''
    Get a key. Returns a future.
    '''
    return await (await connection()).get(key)


async def mget(keys):
    '''
    Get mutliple keys. Returns a future.
    '''
    return await (await connection()).mget(keys)


async def set(key, value, expiry=None):
    '''
    Set a key. We should eventually do multi-sets. Returns a future.
    '''
    return await (await connection()).set(key, value, expiry)


async def delete(key):
    '''
    Delete a key. Returns a future.
    '''
    return await (await connection()).delete(key)
