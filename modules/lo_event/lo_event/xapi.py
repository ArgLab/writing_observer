"""
This is an interface to the XAPI registry of vocabulary.

This code parses JSON files and creates enum-like objects with mappings from cleaned names to original names and full objects.

For this to work, you should first download the .json files with the download_xapi_json.sh script in the xapi directory.

Example usage:
```python
import xapi

# Access the enum-like objects:
print(dir(xapi.ACTIVITYTYPE))
print(xapi.ACTIVITYTYPE.QUESTION)
print(xapi.ActivitytypeObjects.QUESTION)
```
"""

import json
import sys

sources = ["activityType", "attachmentUsage", "extension", "profile", "verb"]


def clean_name(name):
    """
    Cleans the name of a vocabulary entry so that it is a valid Python identifier by converting to upper case, and removing or replacing special characters

    Args:
    name (str): The original name of the vocabulary entry.

    Returns:
    str: The cleaned name of the vocabulary entry.
    """
    return name.upper().strip().replace(' ', '_').replace('-', '_').replace('.', '_').replace('(', '').replace(')', '')


def get_name(x):
    """
    Retrieves the English language name of a vocabulary entry. This is a work-around since the API sometimes retrieves en-us and sometimes en-US.

    Args:
    x (dict): The JSON object representing the vocabulary entry.

    Returns:
    str: The English language name of the vocabulary entry.
    """
    return x.get('en-us', x.get('en-US', None))


def parse_json(source):
    """
    Parses a JSON file containing vocabulary entries into a tuple of clean names and the source JSON data

    Args:
    source (str): The name of the JSON file.

    Returns:
    tuple: A tuple containing cleaned names, and JSON data of the vocabulary entries.
    """
    json_data = json.load(open(f"xapi/{source}.json"))
    names = []
    names_cleaned = []
    if source == "profile":
        selector = lambda x: x['name']
    else:
        selector = lambda x: get_name(x['metadata']['metadata']['name'])

    for d in json_data:
        names.append(selector(d))
        names_cleaned.append(clean_name(selector(d)))

    return names_cleaned, json_data


def create_enum_map(names):
    """
    Creates an enum-like object with mappings from cleaned names to original names in the module namespace.

    Args:
    names (list): The original names of the vocabulary entries.
    names_cleaned (list): The cleaned names of the vocabulary entries.
    """
    class EnumMap:
        pass
    enum_map = EnumMap()
    setattr(sys.modules[__name__], source.upper(), enum_map)
    for name in names:
        setattr(enum_map, name, name)


def create_object_map(names, json_data):
    """
    Creates an object with mappings from cleaned names to full objects in the module namespace.

    Args:
    names_cleaned (list): The cleaned names of the vocabulary entries.
    json_data (list): The JSON data of the vocabulary entries.
    """
    class ObjectMap:
        pass
    object_map = ObjectMap()
    setattr(sys.modules[__name__], f'{source.capitalize()}Objects', object_map)
    for i, obj in enumerate(json_data):
        setattr(object_map, names[i], obj)


sources = ["activityType", "attachmentUsage", "extension", "profile", "verb"]

for source in sources:
    names_cleaned, json_data = parse_json(source)
    create_enum_map(names_cleaned)
    create_object_map(names_cleaned, json_data)
