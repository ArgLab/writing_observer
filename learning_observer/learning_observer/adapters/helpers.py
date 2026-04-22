'''
This is a module which can migrate json events from one naming convention to
another.
'''


import json


def rename_json_keys(source, replacements):
    '''
    Rename the keys in a json object using a dictionary of replacements.

    The replacements dictionary maps keys to new keys.

    The source object is transformed in place.

    >>> source = {
    ...     "event-type": "blog",
    ...     "writing-log": "foobar",
    }
    >>> replacements = {
    ...     "event-type": "event_type",
    ...     "writing-log": "writing_log",
    ... }
    >>> rename_json_keys(source, replacements)
    {
        "event_type": "blog",
        "writing_log": "foobar",
    }
    '''
    if isinstance(source, dict):
        for key, value in list(source.items()):
            if key in replacements:
                source[replacements[key]] = source.pop(key)
        rename_json_keys(value, replacements)
    elif isinstance(source, list):
        for item in source:
            rename_json_keys(item, replacements)
    return source


# Write a test case for rename_json_keys.
def dict_compare(d1, d2):
    s1 = json.dumps(d1, sort_keys=True)
    s2 = json.dumps(d2, sort_keys=True)
    if False:  # Turn on for debugging
        print(s1)
        print(s2)
    return s1 == s2


def test_rename_json_keys():
    replacements = {
        "event-type": "event_type",
        "writing-log": "writing_log",
    }

    data = {
        "event-type": "blog",
        "writing-log": "foobar",
        "log-level": "info",
        "text": "The old man and the sea",
        "timestamp": "yesterday",
        "event-data": {
            "event-type": "log",
            "writing-log": "foobar",
            "log-level": "info",
            "text": "The old man and the sea",
            "event-time": "tomorrow"
        }
    }

    desired_output = {
        "event_type": "blog",
        "writing_log": "foobar",
        "log-level": "info",
        "text": "The old man and the sea",
        "timestamp": "yesterday",
        "event-data": {
            "event_type": "log",
            "writing_log": "foobar",
            "log-level": "info",
            "text": "The old man and the sea",
            "event-time": "tomorrow"
        }
    }

    transformed_data = rename_json_keys(data, replacements)

    assert dict_compare(transformed_data, desired_output)


if __name__ == '__main__':
    test_transform_json()
