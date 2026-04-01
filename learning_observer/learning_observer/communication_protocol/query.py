'''
This file includes commands to create a request within the
communication protocol. It provides a set of Python calls, designed to
(roughly) mirror a relational database, and returns a JSON object
corresponding to that query.

See the examples in the `test_cases.py` for the format.

This JSON object can then be executed by `executor.py`.

This file should be kept thin and minimal, since we will want versions
translated into JavaScript for the front end (and, perhaps eventually,
Julia, R, Stata, and other languages researchers might want to use to
query our system).

This file is intended to be imported in diverse contexts, including ones
where we don't want all of the machinery of the Learning Observer, so also
note the lack of dependencies.
'''
import enum

dispatch = "dispatch"


class DISPATCH_MODES:
    pass


dispatch_modes = ['parameter', 'variable', 'call', 'select', 'join', 'map', 'keys']
[setattr(DISPATCH_MODES, d.upper(), d) for d in dispatch_modes]


def parameter(parameter_name, required=False, default=None):
    """
    Parameters are used to allow users to make specifications for the execution DAG.
    """
    return {
        dispatch: DISPATCH_MODES.PARAMETER,
        "parameter_name": parameter_name,
        "required": required,
        "default": default
    }


def variable(variable_name):
    """
    Variables are used to reference the output of other nodes in the execution DAG.
    """
    return {
        dispatch: DISPATCH_MODES.VARIABLE,
        "variable_name": variable_name
    }


def call(function_name):
    """
    Call is used to call functions on the server-side with appropriate args and kwargs.
    """
    def caller(*args, **kwargs):
        return {
            dispatch: DISPATCH_MODES.CALL,
            "function_name": function_name,
            "args": args,
            "kwargs": kwargs
        }
    setattr(caller, "__lo_name__", function_name)
    return caller


class SelectFields(str, enum.Enum):
    Missing = 'Missing'
    All = 'All'


def select(keys, fields=None):
    """
    Select is used to collect data from the KVS
    """
    return {
        dispatch: DISPATCH_MODES.SELECT,
        "keys": keys,
        "fields": fields
    }


def join(LEFT, RIGHT, LEFT_ON=None, RIGHT_ON=None):
    """
    Join is used to combine two lists of dictionaries.
    """
    return {
        dispatch: DISPATCH_MODES.JOIN,
        "left": LEFT,
        "right": RIGHT,
        "left_on": LEFT_ON,
        "right_on": RIGHT_ON
    }


def map(function, values, value_path=None, func_kwargs=None, parallel=False):
    """
    Map is used to run a function on the server, similar to `call`, over
    a list of values.
    """
    return {
        dispatch: DISPATCH_MODES.MAP,
        "function_name": function.__lo_name__,
        "values": values,
        "value_path": value_path,
        "func_kwargs": func_kwargs,
        "parallel": parallel
    }


def keys(func, **kwargs):
    """
    Keys is used to convert our data into the appropriate format for
    the `select` operation to pull data from the KVS.
    """
    return {
        "dispatch": DISPATCH_MODES.KEYS,
        "function": func,
        **kwargs
    }
