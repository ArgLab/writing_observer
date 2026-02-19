'''
Define layout for per student list of documents
'''
# TODO this module no longer works properly since switching
# the communication protocol to use an async generator.
error = f'The module WO Document List is not compatible with the communication protocol api.\n'\
        'Please uninstall this module with `pip uninstall wo-document-list`.'
raise RuntimeError(error)
# package imports
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

from dash import clientside_callback, ClientsideFunction, Output, Input, State, html, dcc

prefix = 'document-list'
websocket = f'{prefix}-ws'
ws_store = f'{prefix}-ws-store'
grid = f'{prefix}-student-grid'

# option inputs
assignment_select_id = f'{prefix}-assignment-select'
tag_input_id = f'{prefix}-tag-input'


def layout():
    '''
    Function to define the page layout
    '''
    assignment_select = html.Div([
        dbc.Label('Select an assignment from Google Classroom'),
        dbc.RadioItems(id=assignment_select_id, options=[])
    ])
    tag_input = html.Div([
        dbc.Label('Search on tag'),
        dbc.Input(id=tag_input_id, type='text')
    ])
    cont = dbc.Container([
        html.H2('Prototype: Work in Progress'),
        html.P(
            'This dashboard is a prototype displaying different sources of student documents. '
            'This is currently used as an example to show we can obtain documents from different sources. '
            'The dashboard is subject to change based on ongoing feedback from peers and teachers.'
        ),
        html.H2('Student Document List'),
        dbc.Row([
            dbc.Col(assignment_select, width=6),
            dbc.Col(tag_input, width=6)
        ]),
        dbc.Row(id=grid, class_name='g-2 mt-2'),
        lodrc.LOConnection(id=websocket),
        dcc.Store(id=ws_store, data={})
    ], fluid=True)
    return cont


# send request to websocket
clientside_callback(
    ClientsideFunction(namespace='document_list', function_name='send_to_loconnection'),
    Output(websocket, 'send'),
    Input(websocket, 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(tag_input_id, 'value'),
    Input(assignment_select_id, 'value'),
)

# store message from LOConnection in storage for later use
clientside_callback(
    '''
    function(message) {
        const data = JSON.parse(message.data).wo
        console.log(data)
        return data
    }
    ''',
    Output(ws_store, 'data'),
    Input(websocket, 'message')
)

# fetch assignment list for users to select which assignment they want to see
clientside_callback(
    ClientsideFunction(namespace='document_list', function_name='fetch_assignments'),
    Output(assignment_select_id, 'options'),
    Input('_pages_location', 'hash'),
)

# update the grid of students and their appropriate documents
clientside_callback(
    ClientsideFunction(namespace='document_list', function_name='update_student_grid'),
    Output(grid, 'children'),
    Input(ws_store, 'data')
)
