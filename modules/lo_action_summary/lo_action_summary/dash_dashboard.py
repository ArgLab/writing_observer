'''
'''
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc


_prefix = 'lo-action-summary'
_namespace = 'lo_action_summary'
_websocket = f'{_prefix}-websocket'
_websocket_storage = f'{_prefix}-websocket-store'
_student_list = f'{_prefix}-student-list'
_student_output = f'{_prefix}-student-output'


def layout():
    '''
    Function to define the page's layout.
    '''
    page_layout = html.Div(children=[
        html.H1(children='Learning Observer Action Summary'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionStatusAIO(aio_id=_websocket)),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ]),
        dcc.Store(id=_websocket_storage),
        html.H2('Students'),
        dbc.RadioItems(id=_student_list, inline=True),
        html.H2('Action Summary'),
        html.Div(id=_student_output)
    ])
    return page_layout

# Send the initial state based on the url hash to LO.
# If this is not included, nothing will be returned from
# the communication protocol.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

# Handle receiving a message from the websocket.
# This step will parse the message and update the
# local storage accordingly.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='receiveWSMessage'),
    Output(_websocket_storage, 'data'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'message'),
    prevent_initial_call=True
)

# Build the UI based on what we've received from the
# communicaton protocol
# This clientside callback and the serverside callback below are
# the same
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='populateStudentRadioItems'),
    Output(_student_list, 'options'),
    Input(_websocket_storage, 'data'),
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateHashWithSelectedStudent'),
    Output('_pages_location', 'hash'),
    Input(_student_list, 'value')
)


def create_markdown_text(events):
    markdown_str = '```\n'
    for e in events:
        markdown_str += f'{e}\n'
    markdown_str += '```'
    return markdown_str


@callback(
    Output(_student_output, 'children'),
    Input(_websocket_storage, 'data'),
)
def populate_output(data):
    if not data:
        return 'No student selected'
    # there should only be 1
    student_summaries = data.get('single_action_summary', [])
    if len(student_summaries) == 0:
        return 'No student selected'
    
    events = student_summaries[0]['events']
    if len(events) > 0:
        return html.Div([
            dcc.Markdown(create_markdown_text(events))
        ])
    return 'No events found.'
