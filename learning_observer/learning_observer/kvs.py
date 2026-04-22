'''Key-value store

Manages JSON objects

kvs.KVS() will return a key-value store. Note that the back-end is
shared, but each

Keys are strings. Values are JSON objects.

To read objects:

'''

import asyncio
import copy
import enum
import functools
import json
import os
import os.path

import learning_observer.paths
import learning_observer.prestartup
import learning_observer.redis_connection
import learning_observer.settings
import learning_observer.util

OBJECT_STORE = dict()


class _KVS:
    async def dump(self, filename=None):
        '''
        Dumps the entire contents of the KVS to a JSON object.

        It is intended to be used in development and for debugging. It is not
        intended to be used in production, as it is not very performant. It can
        be helpful for offline analytics too, at least at a small scale.

        If `filename` is not `None`, the contents of the KVS are written to the
        file. In either case, the contents are returned as a JSON object.

        In the future, we might want to add filters, so that this is scalable
        for extracting specific data from production systems (e.g. dump data
        for one user).

        args:
            filename: The filename to write to. If `None`, don't write to a file.

        returns:
            A JSON object containing the contents of the KVS.
        '''
        data = {}
        for key in await self.keys():
            data[key] = await self[key]
        if filename:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        return data

    async def multiget(self, keys):
        '''
        Multiget. It's not fast, but it means we can use appropriate
        abstractions and make it fast later.
        '''
        return [await self[key] for key in keys]

    async def load(self, filename):
        '''
        Loads the contents of a JSON object into the KVS.

        It is intended to be used in development and for debugging. It is not
        intended to be used in production, as it is not very performant. It can
        be helpful for offline analytics too, at least at a small scale.
        '''
        with open(filename) as f:
            data = json.load(f)
        for key, value in data.items():
            await self.set(key, value)


class InMemoryKVS(_KVS):
    '''
    Stores items in-memory. Items expire on system restart.
    '''
    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        return copy.deepcopy(OBJECT_STORE.get(key, None))

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        OBJECT_STORE[key] = value

    async def keys(self):
        '''
        Returns all keys.

        Eventually, this might support wildcards.
        '''
        return list(OBJECT_STORE.keys())

    async def clear(self):
        '''
        Clear the KVS.

        This is helpful for debugging and testing. We did not want to
        implement this for the production KVS, since it would be
        too easy to accidentally lose data.
        '''
        global OBJECT_STORE
        OBJECT_STORE = dict()


class _RedisKVS(_KVS):
    '''
    Stores items in redis.
    '''
    def __init__(self, expire):
        self.expire = expire

    async def connect(self):
        '''
        asyncio_redis auto-reconnects. We can't do async in __init__. So
        we connect on the first get / set.
        '''
        await learning_observer.redis_connection.connect()

    async def __getitem__(self, key):
        '''
        Syntax:

        >> await kvs['item']
        '''
        await self.connect()
        item = await learning_observer.redis_connection.get(key)
        if item is not None:
            return json.loads(item)
        return None

    async def set(self, key, value):
        '''
        Syntax:
        >> await set('key', value)

        `key` is a string, and `value` is a json object.

        We can't use a setter with async, as far as I can tell. There is no

        `await kvs['item'] = foo

        So we use an explict set function.
        '''
        await self.connect()
        value = json.dumps(value)  # Fail early if we're not JSON
        assert isinstance(key, str), "KVS keys must be strings"
        return await learning_observer.redis_connection.set(key, value, expiry=self.expire)

    async def keys(self):
        '''
        Return all the keys in the KVS.

        This is obviously not very performant for large-scale dpeloys.
        '''
        await self.connect()
        return await learning_observer.redis_connection.keys()

    async def clear(self):
        '''
        Remove all keys from the redis-backed KVS.

        This uses ``FLUSHDB`` on the configured Redis connection, which clears
        the entire database. Use cautiously in shared environments.
        '''
        await self.connect()
        return await (await learning_observer.redis_connection.connection()).flushdb()

    async def remove(self, key):
        '''
        Remove item from the KVS.

        HACK python didn't like `await del kvs[key]`, so I created this
        method to use in the meantime. More thought should be put into this
        '''
        await self.connect()
        return await learning_observer.redis_connection.delete(key)

    async def multiget(self, keys):
        '''
        Fetch multiple items from the KVS via `mget`
        '''
        await self.connect()
        items = await learning_observer.redis_connection.mget(keys)
        return [json.loads(item) if item is not None else None for item in items]


class EphemeralRedisKVS(_RedisKVS):
    '''
    For testing: redis drops data quickly.
    '''
    def __init__(self, expire=30):
        '''
        We're just a `_RedisKVS` with expiration set
        '''
        super().__init__(expire=expire)


class PersistentRedisKVS(_RedisKVS):
    '''

    For deployment: Data lives forever.
    '''
    def __init__(self):
        '''
        We're just a `_RedisKVS` with expiration unset
        '''
        super().__init__(expire=None)


class FilesystemKVS(_KVS):
    '''
    This is a very non-scalable, non-performant KVS, where each item is a file
    on the filesystem. It can be helpful for debugging. Note that any sort
    of real-world use as the main KVS is not only non-performant, but could
    result in SSD wear.

    It's not a bad solution for caching some files in small-scale deploys.
    '''
    def __init__(self, path=None, subdirs=False):
        '''
        path: Where to store the kvs. Default: kvs
        subdirs: If set, keys with slashes will result in the creation of
        subdirs. For example, self.set("foo/bar", "hello") would create the
        directory foo (if it doesn't exist) and store "hello" in the file "bar"
        '''
        self.path = path or learning_observer.paths.data('kvs')
        self.subdirs = subdirs
        if not os.path.exists(path):
            os.mkdir(path)

    def key_to_safe_filename(self, key):
        '''
        Convert a key to a safe filename
        '''
        if self.subdirs:
            paths = key.split('/')
            # Add underscores to directories so they don't conflict with files
            for i in range(len(paths) - 1):
                paths[i] = '_' + paths[i]
            safename = (os.sep).join(map(learning_observer.util.to_safe_filename, paths))
        else:
            safename = learning_observer.util.to_safe_filename(key)
        return os.path.join(self.path, safename)

    def safe_filename_to_key(self, filename):
        # raise NotImplementedError("Code this up, please. Or for debugging, comment out the exception")
        return learning_observer.util.from_safe_filename(filename)

    async def __getitem__(self, key):
        path = self.key_to_safe_filename(key)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    async def set(self, key, value):
        path = self.key_to_safe_filename(key)
        if self.subdirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(value, f, indent=4)

    async def __delitem__(self, key):
        path = self.key_to_safe_filename(key)
        os.remove(path)

    async def keys(self):
        '''
        This one is a little bit tricky, since if subdirs, we need to do a full
        walk
        '''
        keys = []
        if self.subdirs:
            for root, dirs, files in os.walk(self.path):
                for f in files:
                    keys.append(self.safe_filename_to_key(os.path.join(root, f).replace(os.sep, '/')))
        else:
            for f in os.listdir(self.path):
                keys.append(self.safe_filename_to_key(f))
        return keys

    async def clear(self):
        '''
        Remove all entries stored in the filesystem-backed KVS.

        The base directory is preserved, but all contained files (and
        directories when ``subdirs`` is enabled) are removed.
        '''
        if self.subdirs:
            for root, dirs, files in os.walk(self.path, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
        else:
            for f in os.listdir(self.path):
                os.remove(os.path.join(self.path, f))


# TODO change the keys to variables
KVS_MAP = {
    'stub': InMemoryKVS,
    'redis_ephemeral': EphemeralRedisKVS,
    'redis': PersistentRedisKVS,
    'filesystem': FilesystemKVS
}


class MissingKVSParameters(AttributeError):
    '''Raise this when required parameters are not present
    in the KVS item trying to be created.

    You will see this error if you forget to include
    1. `expiry` in type `redis_ephemeral` OR
    2. `path` in type `filesystem`
    '''
    def __init__(self, key, type, param):
        msg = f'KVS, {key}, is set to type `{type}` but `{param}` is not specified. '\
              'This can be fixed in `creds.yaml`.'
        super().__init__(msg)


class KVSRouter:
    """Routes KVS calls to the appropriate backend."""

    def __init__(self, default=None, items=None):
        """
        Initialize the router with a default KVS and optional additional items.

        :param default: the default KVS callable
        :param items: a dictionary or list of tuples containing KVS items
        """
        self._items = {'default': default}

        if items is not None:
            for key, kvs_item in items:
                kvs_type = kvs_item['type']
                if kvs_type not in KVS_MAP:
                    raise KeyError(f"Invalid KVS type '{kvs_type}'")
                kvs_class = KVS_MAP[kvs_type]
                if kvs_type == 'redis_ephemeral':
                    if 'expiry' not in kvs_item:
                        raise MissingKVSParameters(key, kvs_type, 'expiry')
                    kvs_class = functools.partial(kvs_class, kvs_item['expiry'])
                elif kvs_type == 'filesystem':
                    if 'path' not in kvs_item:
                        raise MissingKVSParameters(key, kvs_type, 'path')
                    kvs_class = functools.partial(kvs_class, kvs_item['path'], kvs_item.get('subdirs', False))
                self.add_item(key, kvs_class)

    def __call__(self):
        """Call the default KVS callable."""
        return self._items['default']()

    def add_item(self, key, value):
        """Add a new KVS item."""
        self._items[key] = value

    def remove_item(self, key):
        """Remove a KVS item."""
        del self._items[key]

    def __getattr__(self, key):
        """Get a KVS item by key."""
        if key in self._items:
            return self._items[key]
        else:
            raise AttributeError(f"KVS has no object '{key}'")


KVS = None


@learning_observer.prestartup.register_startup_check
def kvs_startup_check():
    '''
    This is a startup check. If confirms that the KVS is properly configured
    in settings.py. It should happen after we've loaded settings.py, so we
    register this to run in prestartup.

    Checks like this one allow us to fail on startup, rather than later
    '''
    global KVS
    try:
        KVS = KVSRouter(items=learning_observer.settings.settings['kvs'].items())

    except KeyError:
        if 'kvs' not in learning_observer.settings.settings:
            raise learning_observer.prestartup.StartupCheck(
                "No KVS configured. Please set kvs.type in settings.py\n"
                "Look at example settings file to see what's available."
            )
        elif any([kvs['type'] not in KVS_MAP for _, kvs in learning_observer.settings.settings['kvs'].items()]):
            raise learning_observer.prestartup.StartupCheck(
                "Unknown KVS type: {}\n"
                "Look at example settings file to see what's available. \n"
                "Suppported types: {}".format(
                    ', '.join([kvs['type'] for _, kvs in learning_observer.settings.settings['kvs'].items() if kvs['type'] not in KVS_MAP]),
                    list(KVS_MAP.keys())
                )
            )
        elif 'default' not in learning_observer.settings.settings['kvs']:
            raise learning_observer.prestartup.StartupCheck(
                "No default KVS configured. Please set default kvs.\n"
                "See example settings file for usage."
            )
        else:
            raise learning_observer.prestartup.StartupCheck(
                "KVS incorrectly configured. Please fix the error, and\n"
                "then replace this with a more meaningful error message"
            )
    return True


async def test():
    '''
    Simple test case: Spin up a few KVSes, write data to them, make
    sure it's persisted globally.
    '''
    learning_observer.settings.load_settings('creds.yaml')
    mk1 = InMemoryKVS()
    mk2 = InMemoryKVS()
    ek1 = EphemeralRedisKVS()
    ek2 = EphemeralRedisKVS()
    fs1 = FilesystemKVS(path="/tmp/flatkvs")
    fs2 = FilesystemKVS(path="/tmp/dirkvs", subdirs=True)
    assert (await mk1["hi"]) is None
    print(await ek1["hi"])
    assert (await ek1["hi"]) is None
    await mk1.set("hi", 5)
    await mk2.set("hi", 7)
    await ek1.set("hi", 8)
    await ek2.set("hi", 9)
    if True:
        os.makedirs("/tmp/flatkvs", exist_ok=True)
        os.makedirs("/tmp/dirkvs", exist_ok=True)
        await fs1.set("fooo", "poof")
        await fs1.set("foo/barła", "zoo")
        await fs2.set("foob", "loo")
        await fs2.set("fob/perła", "koo")
        assert (await fs1["fooo"]) == "poof"
    if False:  # We don't do this correctly yet
        async for k in fs2.keys():
            print(k)
        async for k in fs1.keys():
            print(k)

    assert (await mk1["hi"]) == 7
    print(await ek1["hi"])
    print(type(await ek1["hi"]))
    print((await ek1["hi"]) == 9)
    assert (await ek1["hi"]) == 9
    print(await mk1.keys())
    print(await ek1.keys())
    print("Test successful")
    print("Please wait before running test again")
    print("redis needs to flush expiring objects")
    print("This delay is set in the config file.")
    print("It is typically 1s - 24h, depending on")
    print("the work.")

if __name__ == '__main__':
    asyncio.run(test())
