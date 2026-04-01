'''
This is a web interface which provides information about:

* The available queries
* The DAG execution graphs associated with those
* Parameters to said queries

TODO at some point during development this broke and no longer
displays the DAGs correctly. This was a hacked together prototype
so efforts to fix have been pushed to wayside.
'''

from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import json

import learning_observer.module_loader
import learning_observer.communication_protocol.query
import learning_observer.communication_protocol.util

main_panel = 'queries-view'
module_store = 'queries-module-store'


def layout():
    dags = learning_observer.module_loader.execution_dags()

    ret = dbc.Container(
        [
            dcc.Store(id=module_store, data=json.loads(json.dumps(list(dags.keys()), default=str))),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.ListGroup(
                                [
                                    dbc.CardLink(dag, href=f'#{dag}')
                                    for dag in dags
                                ]
                            )
                        ),
                        md=4,
                        lg=3
                    ),
                    dbc.Col(
                        dbc.Card(
                            id=main_panel,
                            body=True
                        ),
                        md=8,
                        lg=9
                    )
                ]
            )
        ],
        fluid=True
    )
    return ret


def create_modules(modules):
    row = dbc.Row(
        [
            dbc.Col(
                dbc.Card(
                    dbc.CardLink(m, href=f'#{m}'),
                    body=True
                ),
                xs=10,
                sm=8,
                md=6,
                lg=4,
                xxl=3
            ) for m in list(modules)
        ],
        justify='around',
        class_name='text-center'
    )
    return row


def iteratively_build_flowchart(data, path='', subgraphs=None, arrows=None):
    '''
    Iterate over the execution dag and add pieces of the flowchart as we go.

    :param data: The data dictionary to parse
    :type data: dict
    :param path: The current path in the data structure
    :type path: str
    :param subgraphs: The list of subgraphs
    :type subgraphs: list, optional
    :param arrows: The list of arrows
    :type arrows: list, optional
    :return: A tuple containing the subgraphs and arrows
    :rtype: tuple
    '''
    if subgraphs is None:
        subgraphs = []
    if arrows is None:
        arrows = []
    if isinstance(data, dict):
        if path != '':
            subgraphs.append(f'subgraph {path}')
        for k, v in data.items():
            new_path = f'{path}.{k}' if path else k
            dispatch = k == 'dispatch'
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.VARIABLE:
                variable_name = data.get('variable_name', None)
                arrows.append(f'{variable_name} --> {path}')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.PARAMETER:
                parameter_name = data.get('parameter_name', None)
                subgraphs.append(f'{parameter_name}[/Parameter: {parameter_name}/]')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.CALL:
                parameter_name = data.get('function_name', None)
                subgraphs.append(f'{parameter_name}([Call: {parameter_name}])')
            if dispatch and v == learning_observer.communication_protocol.query.DISPATCH_MODES.MAP:
                parameter_name = data.get('function', None)
                subgraphs.append(f'{parameter_name}[[Map: {parameter_name}]]')
            else:
                iteratively_build_flowchart(v, new_path, subgraphs, arrows)
        if path != '':
            subgraphs.append('end')
    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_path = f'{path}[{i}]'
            iteratively_build_flowchart(v, new_path, subgraphs, arrows)
    return subgraphs, arrows


def create_mermaid_flowchart(endpoint):
    """
    Create a mermaid flowchart from an endpoint.

    :param endpoint: The endpoint dictionary
    :type endpoint: dict
    :return: A string representing the mermaid flowchart
    :rtype: str
    """
    subgraphs, arrows = iteratively_build_flowchart(learning_observer.communication_protocol.util.flatten(endpoint)['execution_dag'])
    return 'flowchart TD\n' + '\n'.join(subgraphs) + '\n' + '\n'.join(arrows)


def create_parameter(param):
    return html.Div(
        [
            html.H5(
                dcc.Markdown(f'`{param["id"]}`'),
                className='d-inline-block'
            ),
            html.P(
                [
                    html.Strong('Type: '),
                    ' or '.join([str(t.__name__) for t in param['type']]),
                    html.Br(),
                    html.P(param['description'])
                ]
            ),
        ]
    )


def create_query(item):
    copy = item.copy()
    div = html.Div(
        [
            html.H3(copy['module']),
            html.H4('Exports'),
            # TODO create exports piece
            html.H4('Flow chart'),
            # TODO this used to use Dash Extensions to show a Mermaid chart
            # Dash Extensions was causing dependency issues and since this
            # code was already broken, we opted to remove it.
        ]
    )
    return div


@callback(
    Output(main_panel, 'children'),
    Input('_pages_location', 'hash'),
    State(module_store, 'data')
)
def update_page(hash, modules):
    if hash is None:
        return create_modules(modules)

    dags = learning_observer.module_loader.execution_dags()

    cleaned_hash = hash[1:]
    if cleaned_hash in dags:
        return create_query(dags[cleaned_hash])
    else:
        return create_modules(modules)
