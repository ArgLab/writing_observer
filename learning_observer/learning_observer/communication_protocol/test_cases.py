"""
Run all test cases. Print output from the ones specified.

Usage:
    test_cases.py [--quiet | --verbose] [<test_case>...]

Options:
    -h --help     Show this screen.
    --quiet       Do not include execution DAG output
    --verbose     Include execution DAG output (overrides --quiet)

Test Cases:
    docs_with_roster    Prints the dummy Google Docs text DAG.
    map_example         Prints the map example test cases.
    map_async_example   Prints the map async example test cases.
    parameter_error     Prints the parameter test case.
    field_error         Prints the missing fields test case.
    malformed_key       Prints the malformed key test case.
    call_exception      Prints the func_except test case.
    join_error_key      Prints the nonexistent key in join test case.
    circular_error      Prints the circular error test case
    all                 Prints all available test cases.
    none                Prints no output, except on unexpected errors
"""

import asyncio
import copy
import docopt
import json
import random
import sys
import time

import learning_observer.communication_protocol.executor
import learning_observer.communication_protocol.integration
import learning_observer.communication_protocol.query as q
import learning_observer.communication_protocol.util
import learning_observer.communication_protocol.exception
import learning_observer.constants as constants
import learning_observer.offline


# dummy functions for testing
def dummy_roster(course):
    """
    Dummy function for course roster.

    Args:
        course: The course identifier

    Returns:
        list: A list of student identifiers
    """
    return [{
        constants.USER_ID: f'student-{i}'
    } for i in range(10)]


def dummy_exception():
    raise Exception('This is an exception that was raised in a published function.')


async def dummy_async_map(value, example):
    await asyncio.sleep(1)
    if value.endswith('2'):
        raise ValueError('Item ends with a 2')
    return {'value': value, 'example': example}

def dummy_sync_map(value, example):
    time.sleep(1)
    if value.endswith('2'):
        raise ValueError('Item ends with a 2')
    return {'value': value, 'example': example}


DUMMY_FUNCTIONS = {
    "learning_observer.dummyroster": dummy_roster,
    "learning_observer.dummycall": dummy_exception,
    "learning_observer.dummyasyncmap": dummy_async_map,
    "learning_observer.dummymap": dummy_sync_map
}

course_roster = q.call('learning_observer.dummyroster')
exception_func = q.call('learning_observer.dummycall')
map_func = q.call('learning_observer.dummymap')
async_map_func = q.call('learning_observer.dummyasyncmap')

TEST_DAG = {
    'execution_dag': {
        "roster": course_roster(course=q.parameter("course_id", required=True)),
        "doc_ids": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'document_id': 'doc_id'}),
        "docs": q.select(q.keys('writing_observer.reconstruct', STUDENTS=q.variable("roster"), STUDENTS_path='user_id', RESOURCES=q.variable("doc_ids"), RESOURCES_path='doc_id'), fields={'text': 'text'}),
        "docs_join_roster": q.join(LEFT=q.variable("docs"), RIGHT=q.variable("roster"), LEFT_ON='provenance.provenance.STUDENT.value.user_id', RIGHT_ON='user_id'),
        "map_students": q.map(map_func, q.variable('roster'), 'user_id', {'example': 123}, parallel=True),
        "map_async_students": q.map(async_map_func, q.variable('roster'), 'user_id', {'example': 123}, parallel=True),
        "field_error": q.select(q.keys('writing_observer.last_document', STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'nonexistent_key': 'doc_id'}),
        "malformed_key_error": q.select([{'item': 1}, {'item': 2}], fields={'nonexistent_key': 'doc_id'}),
        "call_exception": exception_func(),
        "join_key_error": q.join(LEFT=q.variable('docs'), LEFT_ON='nonexistent.value.path', RIGHT=q.variable('roster'), RIGHT_ON='user_id'),
        "circular_2": q.keys('writing_observer.last_document', STUDENTS=q.variable("circular_1"), STUDENTS_PATH='user_id'),
        "circular_1": q.variable("circular_2")
    },
    'exports': {
        'docs_with_roster': {
            'returns': 'docs_join_roster',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": "Example of fetching students text information based on their last document.",
            'expected': lambda x: isinstance(x, list) and 'text' in x[0]
        },
        'map_example': {
            'returns': 'map_students',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": 'Show example of mapping students',
            'expected': lambda x: isinstance(x, list) and 'value' in x[0]
        },
        'map_async_example': {
            'returns': 'map_async_students',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": 'Show example of mapping students',
            'expected': lambda x: isinstance(x, list) and 'value' in x[0]
        },
        'parameter_error': {
            'returns': 'docs_join_roster',
            'parameters': ['course_id'],
            'test_parameters': {},
            "description": "Fetches student doc text; however, this errors since we do not provide the necessary parameters.",
            'expected': lambda x: isinstance(x, list) and 'error' in x[0]
        },
        'field_error': {
            'returns': 'field_error',
            'parameters': ['course_id'],
            'test_parameters': {'course_id': 123},
            "description": "The desired field does not exist within our key. We output an error, but do no fail.",
            'expected': lambda x: isinstance(x, list) and 'error' in x[0]['doc_id']
        },
        'malformed_key': {
            'returns': 'malformed_key_error',
            'parameters': [],
            'test_parameters': {},
            "description": "Malformed key when trying to select",
            'expected': lambda x: isinstance(x, dict) and 'error' in x
        },
        'call_exception': {
            'returns': 'call_exception',
            'parameters': [],
            'test_parameters': {},
            'description': "Throw an exception within a published function",
            'expected': lambda x: isinstance(x, list) and 'error' in x[0]
        },
        # TODO this test case fails and was failing before switching to an async generator
        # Should we be erroring if the `left_on` path doesn't exist or just yielding `left`
        # as is? Currently, `executor.py` yields `left`.
        'join_key_error': {
            'returns': 'join_key_error',
            'parameters': [],
            'test_parameters': {'course_id': 123},
            'description': 'The left_on path does not exist, so we return an error on the join.',
            'expected': lambda x: isinstance(x, list) and 'error' in x[0]
        },
        'circular_error': {
            'returns': 'circular_2',
            'parameters': [],
            'test_parameters': {},
            'description': 'Test out circular node errors',
            'expected': lambda x: isinstance(x, list) and 'error' in x[0]
        }
    }
}


async def run_test_cases(test_cases, verbose=False):
    """
    Run all test cases. Print output from the ones specified.

    Args:
        test_cases (list): The test cases to be run

    Returns:
        None
    """
    # List of available test cases
    available_test_cases = list(TEST_DAG['exports'].keys()) + ['all', 'none']

    if not all(case in available_test_cases for case in test_cases):
        print(f"Invalid test case. Available test cases are: {available_test_cases}")
        sys.exit()

    learning_observer.offline.init('creds.yaml')

    for key in TEST_DAG['exports']:
        FLAT = learning_observer.communication_protocol.util.flatten(copy.deepcopy(TEST_DAG))
        EXECUTE = await learning_observer.communication_protocol.executor.execute_dag(
            copy.deepcopy(FLAT), parameters=TEST_DAG['exports'][key]['test_parameters'],
            functions=DUMMY_FUNCTIONS, target_exports=[key]
        )
        if (key in test_cases or 'all' in test_cases) and 'none' not in test_cases:
            print(f"Executing {key}")
            if verbose:
                print(json.dumps(EXECUTE, indent=2))

            try:
                driven_gen = [i async for i in EXECUTE[TEST_DAG['exports'][key]['returns']]]
            except learning_observer.communication_protocol.exception.DAGExecutionException as e:
                driven_gen = e.to_dict()
            assert (TEST_DAG['exports'][key]['expected'](driven_gen))
            print('  Received expected output.')


if __name__ == "__main__":
    """
    Program entry point
    """
    args = docopt.docopt(__doc__)
    if args['<test_case>'] == []:
        print(__doc__)
        sys.exit()
    asyncio.run(run_test_cases(args['<test_case>'], args['--verbose']))
