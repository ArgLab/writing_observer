'''
This file handles integrating exports from DAGs into the
Learning Observer platform and publishing functions from
the Learning Observer platform into the communications
protocol.
'''
import copy

import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.util

FUNCTIONS = {}
DUPLICATE_FUNCTION_FOUND = """Duplicate function name found: {name}.
Please ensure that all callable functions used in the
communication protocol have different names.
Search the codebase for `publish_function({name})` to view
any duplicates.
"""


def publish_function(name):
    """
    To expose functions to the communications protocol, we have to
    pass in a dictionary of functions to the DAG executor. The Learning
    Observer system will pass the `FUNCTIONS` dictionary to the executor.
    This decorator adds a function to FUNCTIONS.
    """
    def decorator(f):
        if name in FUNCTIONS:
            # NOTE perhaps we should include some form of priority
            # use case: we may want to overwrite the roster function for a specific system
            raise KeyError(DUPLICATE_FUNCTION_FOUND.format(name=name))
        FUNCTIONS[name] = f
        return f
    return decorator


def add_exports_to_module(execution_dag, module):
    '''
    We may want to access each endpoint as a function call in code.
    This function iterates over exposed endpoints and adds each as a callable
    function to the provided `module`.

    The `set_query_with_name` inner closure is necessary to appropriately
    set the `name` parameter within the `query_func` inner-most function.

    Example Usage:
        dag = {
            "exports": {
                "query1": ...,
                "query2": ...,
            }
        }
        add_exports_to_module(exports, my_module)
        result = await my_module.query1(parameter1=123)

    Raises:
        AttributeError: If the attribute name already exists in the module.
    '''
    for query_name in execution_dag['exports']:
        def set_query_with_name(name):
            async def query_func(**kwargs):  # create new function
                flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(execution_dag))
                output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS, target_exports=[query_name])
                return output
            if hasattr(module, name):
                raise AttributeError(f'Attibute, {name}, already exists under {module}')
            else:
                setattr(module, name, query_func)
        set_query_with_name(query_name)


def prepare_dag_execution(query, targets):
    '''
    This functions wraps an execution DAG in the necessary steps to
    execute specific `targets`.

    Example Usage:
        query_obj = ...  # create the query object
        query_function = prepare_dag_execution(query_obj)
        result = await query_function(param1=value1, param2=value2)
    '''
    async def query_func(**kwargs):
        flat = learning_observer.communication_protocol.util.flatten(copy.deepcopy(query))
        output = await learning_observer.communication_protocol.executor.execute_dag(flat, parameters=kwargs, functions=FUNCTIONS, target_exports=targets)
        return output
    return query_func
