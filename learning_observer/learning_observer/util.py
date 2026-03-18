'''
Random helper functions.

Design invariant:

* This should not rely on anything in the system.

We can relax the design invariant, but we should think carefully
before doing so.
'''
import asyncio
import collections
import dash.development.base_component
import datetime
import enum
import hashlib
import math
import numbers
import re
import uuid
from dateutil import parser

import learning_observer


def paginate(data_list, nrows):
    '''
    Paginate list `data_list` into `nrows`-item rows.

    This should move into the client
    '''
    return [
        data_list[i * nrows:(i + 1) * nrows]
        for i in range(math.ceil(len(data_list) / nrows))
    ]


def to_safe_filename(name):
    '''
    Convert a name to a filename. The filename escapes any non-alphanumeric
    characters, so there are no invalid or control characters.

    Can be converted back with `from_filename`

    For example, { would be encoded as -123- since { is character 123 in UTF-8.
    '''
    return ''.join(
        '-' + str(ord(c)) + '-' if not c.isidentifier() and not c.isalnum() else c
        for c in name
    )


def from_safe_filename(filename):
    '''
    Convert a filename back to a name.

    See `to_filename` for more information.

    Uses `re`, uncompiled, so probably not very fast. Right now, this is used
    for testing / debugging, but might be worth optimizing if we ever use it
    otherwise.
    '''
    return re.sub(r'-(\d+)-', lambda m: chr(int(m.group(1))), filename)


def url_pathname(s):
    """
    Remove URL and domain from a URL. Return the full remainder of the path.

    Input: https://www.googleapis.com/drive/v3/files
    Output: drive/v3/files

    Note that in contrast to the JavaScript version, we don't include the
    initial slash.
    """
    return s.split('/', 3)[-1]


def translate_json_keys(d, translations):
    """
    Replace all of the keys in the dictionary with new keys, including
    sub-dictionaries. This was written for converting CamelCase from
    Google APIs to snake_case.

    Note that this mutates the original data structure
    """
    if isinstance(d, list):
        for item in d:
            translate_json_keys(item, translations)
    elif isinstance(d, dict):
        for k, v in list(d.items()):
            if k in translations:
                d[translations[k]] = d.pop(k)
            else:
                pass  # print("UNTRANSLATED KEY: ", k)

            if isinstance(v, dict) or isinstance(v, list):
                translate_json_keys(v, translations)
    return d


def secure_hash(text):
    '''
    Our standard hash functions. We can either use either

    * A full hash (e.g. SHA3 512) which should be secure against
    intentional attacks (e.g. a well-resourced entity wants to temper
    with our data, or if Moore's Law starts up again, a well-resourced
    teenager).

    * A short hash (e.g. MD5), which is no longer considered
    cryptographically-secure, but is good enough to deter casual
    tempering. Most "tempering" comes from bugs, rather than attackers,
    so this is very helpful still. MD5 hashes are a bit more manageable
    in size.

    For now, we're using full hashes everywhere, but it would probably
    make sense to alternate as makes sense. MD5 is 32 characters, while
    SHA3_512 is 128 characters (104 if we B32 encode).
    '''
    return "SHA512_" + hashlib.sha3_512(text).hexdigest()


def insecure_hash(text):
    '''
    See `secure_hash` above for documentation
    '''
    return "MD5_" + hashlib.md5(text).hexdigest()


class MissingType(enum.Enum):
    Missing = 'Missing'


def get_nested_dict_value(d, key_str=None, default=MissingType.Missing):
    """
    Fetch an item from a nested dictionary using `.` to indicate nested keys

    :param d: Dictionary to be searched
    :type d: dict
    :param key_str: Keys to iterate over
    :type key_str: str
    :return: Value of nested dictionary
    """
    if key_str is None:
        key_str = ''
    keys = key_str.split('.')
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        elif key == '':
            d = d
        else:
            if default == MissingType.Missing:
                raise KeyError(f'Key `{key_str}` not found in {d}')
            return default
    return d


def remove_nested_dict_value(d, key_str):
    """
    Remove an item from a nested dictionary using `.` to indicate nested keys
    """
    keys = key_str.split('.')
    for key in keys[:-1]:
        if d is not None and key in d:
            d = d[key]
        else:
            raise KeyError(f'Key `{key_str}` not found in {d}')
    if keys[-1] in d:
        return d.pop(keys[-1])
    else:
        raise KeyError(f'Key `{key_str}` not found in {d}')


def clean_json(json_object):
    '''
    * Deep copy a JSON object
    * Convert list-like objects to lists
    * Convert dictionary-like objects to dicts
    * Convert functions to string representations
    '''
    if isinstance(json_object, str):
        return str(json_object)
    if isinstance(json_object, numbers.Number):
        return json_object
    if isinstance(json_object, dict):
        return {key: clean_json(value) for key, value in json_object.items()}
    if isinstance(json_object, list) or isinstance(json_object, tuple):
        return [clean_json(i) for i in json_object]
    if isinstance(json_object, learning_observer.stream_analytics.fields.Scope):
        # We could make a nicer representation....
        return str(json_object)
    if callable(json_object):
        return str(json_object)
    if json_object is None:
        return json_object
    if str(type(json_object)) == "<class 'module'>":
        return str(json_object)
    if str(type(json_object)) == "<class 'learning_observer.runtime.Runtime'>":
        return str(json_object)
    if str(type(json_object)) == "<class 'dict_keys'>":
        return list(json_object)
    if isinstance(json_object, dash.development.base_component.Component):
        return f"Dash Component {json_object}"
    if isinstance(json_object, KeyError):
        return str(json_object)
    raise ValueError("We don't yet handle this type in clean_json: {} (object: {})".format(type(json_object), json_object))


def timestamp():
    """
    Return a timestamp string in ISO 8601 format

    Returns:
        str: The timestamp string.

    The timestamp is in UTC.
    """
    return datetime.datetime.utcnow().isoformat()


def timeparse(timestamp):
    """
    Parse an ISO-8601 datetime string into a datetime.datetime

    Returns:
        datetime: datetime object converted from the string timestamp.

    """
    return parser.isoparse(timestamp)


def get_seconds_since_epoch():
    '''
    Return a timestamp in the seconds since epoch format

    Returns:
        int: seconds since last epoch
    '''
    return datetime.datetime.now().timestamp()


count = 0


def generate_unique_token():
    '''Update the system counter and return a new unique token.
    '''
    global count
    count = count + 1
    return f'{count}-{timestamp()}-{str(uuid.uuid4())}'


async def ensure_async_generator(it):
    '''Take an iterable or single dict item and return it
    as an async generator.
    '''
    if isinstance(it, dict):
        yield it
    elif isinstance(it, collections.abc.AsyncIterable):
        # If it is already an async iterable, yield from it
        async for item in it:
            yield item
    elif isinstance(it, collections.abc.Iterable):
        # If it is a synchronous iterable, iterate over it and yield items
        for item in it:
            yield item
    else:
        raise TypeError(f"Object of type {type(it)} is not iterable")


async def async_zip(iterator1, iterator2):
    '''Zip 2 async generators together.
    This functions similar to `zip`
    '''
    gen1 = ensure_async_generator(iterator1)
    gen2 = ensure_async_generator(iterator2)
    try:
        while True:
            # asyncio.gather finishes when both `anext` items are ready
            item1, item2 = await asyncio.gather(
                gen1.__anext__(),
                gen2.__anext__()
            )
            yield item1, item2
    except StopAsyncIteration:
        pass


async def async_generator_to_list(gen):
    '''This is a helper function for converting an async generator
    to a list. This is often used when testing pieces of an async
    generator pipeline.
    '''
    result = []
    async for item in gen:
        result.append(item)
    return result


def get_domain_from_email(email):
    '''Helper function to extract the domain from an email address
    '''
    if email is None:
        return None
    if '@' in email:
        return email.split('@')[1]
    return None


# And a test case
if __name__ == '__main__':
    assert to_safe_filename('{') == '-123-'
    assert from_safe_filename('-123-') == '{'
    test_string = "Hello? How are -- you doing? łłł"
    assert from_safe_filename(to_safe_filename(test_string)) == test_string
    assert url_pathname('https://www.googleapis.com/drive/v3/files') == 'drive/v3/files'
