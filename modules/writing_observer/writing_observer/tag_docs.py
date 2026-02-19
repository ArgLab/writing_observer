'''
These functions are used to get the appropriate behavior for
grouping tagged documents together. Lots of this code could
be transferred to a query commands in the execution protocol.
I tried to keep it generic enough so we could easily move
them later on, I just didn't want to do the added work of
creating new query commands.
'''
import copy

import learning_observer.util
import learning_observer.communication_protocol.integration


@learning_observer.communication_protocol.integration.publish_function('unwind')
def unwind(objects, value_path, new_name, keys_to_keep=None):
    '''
    Takes an array field, denoted by `value_path`, from the provided `objects` and
    produces a new object for each value in the array. The outputted object is the same
    as one of the inputted objects with `new_name` equal to a value in the array.
    Objects can be a single object or a list of objects.

    This behavior is the same to that of the $unwind feature in MongoDB.

    :param value_path: Dot notation path to item we wind unwound
    :type value_path: str

    :param new_name: Name of key in new objects to store unwound array value
    :type new_name: str

    :param keys_to_keep: List of keys to return. If `None`, all keys are returned except the head of `value_path`
    :default keys_to_keep: None
    :type keys_to_keep: list

    Generic example of unwinding single object
    >>> unwind(objects={'user': 1, 'items': ['i1', 'i2']}, value_path='items', new_name='item')
    [{'user': 1, 'item': 'i1'}, {'user': 1, 'item': 'i2'}]

    Example unwinding multiple objects
    >>> unwind(
    ...     objects=[{'user': 1, 'items': ['i1', 'i2']}, {'user': 2, 'items': ['i3']}],
    ...     value_path='items', new_name='item'
    ... )
    [{'user': 1, 'item': 'i1'}, {'user': 1, 'item': 'i2'}, {'user': 2, 'item': 'i3'}]

    Example where we only keep specific keys
    >>> unwind(
    ...     objects={'user': 1, 'items': ['i1', 'i2'], 'extra_key': 123},
    ...     value_path='items', new_name='item', keys_to_keep=['user']
    ... )
    [{'user': 1, 'item': 'i1'}, {'user': 1, 'item': 'i2'}]

    TODO this ought to be query command, I'm just writing it as a function for now
    but I'll try to keep it generic to be slid in later.
    '''
    items = objects if isinstance(objects, list) else [objects]
    unpacked = []
    for item in items:
        # should we default or should we error? Probably error, maybe later
        values = learning_observer.util.get_nested_dict_value(item, value_path, [])
        for value in values:
            new = copy.deepcopy(item)
            learning_observer.util.remove_nested_dict_value(new, value_path)
            if isinstance(values, dict):
                values[value]['id'] = value
                new[new_name] = values[value]
            else:
                new[new_name] = value
            if keys_to_keep is None:
                unpacked.append(new)
            else:
                unpacked.append({k: v for k, v in new.items() if k in keys_to_keep or k == new_name})
    return unpacked


@learning_observer.communication_protocol.integration.publish_function('writing_observer.group_docs_by')
def group_docs_by(items, value_path):
    '''
    After fetching all the text from each pair of student/doc id, we want
    to regroup them by student. Appending each document to a list in the
    process.

    Currently this function is hardcoded for the tagging documents workflow.
    Ideally we can determine which values we wish to keep as well as which
    functions to run on them.
    TODO abstract out of specific use case and implement as a query command

    Example grouping items by user (this gets renamed to user_id)
    >>> group_docs_by(
    ...     items=[{'user': 1, 'doc': 'i1'}, {'user': 1, 'doc': 'i2'}, {'user': 2, 'doc': 'i3'}],
    ...     value_path='user'
    ... )
    [{'user_id': 1, 'documents': ['i1', 'i2']}, {'user_id': 2, 'documents': ['i3']}]
    '''
    overall = {}
    for item in items:
        try:
            value = learning_observer.util.get_nested_dict_value(item, value_path)
        except KeyError:
            # TODO handle key not found
            continue
        if value in overall:
            overall[value]['documents'].append(item['doc'])
        else:
            overall[value] = {}
            overall[value]['user_id'] = value
            overall[value]['documents'] = [item['doc']]
    return [v for _, v in overall.items()]


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
