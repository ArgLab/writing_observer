import json
import jsonschema
import os

dir = os.path.dirname(os.path.realpath(__file__))
schema_path = os.path.join(dir, 'schema.json')

with open(schema_path, 'r') as f:
    execution_dag_schema = json.load(f)


def prevalidate_schema(query):
    '''This performs a cursory validation to see if we have the basic
    JSON format of an execution DAG.
    Note that this does not do any in-depth checks to see if the DAG
    is functional and safe within the system, e.g. conforms to functions
    available on the server, correct parameters, correct referneces to
    other nodes, security/injection attacks.
    '''
    try:
        jsonschema.validate(query, execution_dag_schema)
        return True
    except jsonschema.ValidationError as e:
        raise e
