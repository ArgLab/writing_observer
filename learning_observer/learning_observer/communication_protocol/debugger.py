'''
This provides a web interface for making queries via the
communication protocol and seeing the text of the results.

TODO:

* This isn't really a debugger. Perhaps this should be called
  interactive mode? Or developer mode? Or similar?
* Ideally, this should be moved to the Jupyter notebook
* Make work with the new async generator pipeline
'''

from dash import html, callback, Output, Input, State
from dash.exceptions import PreventUpdate
from dash_renderjson import DashRenderjson
import dash_bootstrap_components as dbc
import json
import lo_dash_react_components as lodrc


# These are IDs for page elements, used in the layout and for callbacks
prefix = 'communication-debugger'
ws = f'{prefix}-websocket'
status = f'{prefix}-connection-status'
message = f'{prefix}-message-input'
submit = f'{prefix}-submit-btn'
response = f'{prefix}-response-markdown'


def layout():
    cont = dbc.Container(
        [
            dbc.Row(
                [
                    html.H1('Communication Protocol Debugger'),
                    lodrc.LOConnection(
                        id=ws,
                        url='ws://localhost:8888/wsapi/communication_protocol'  # HACK/TODO: This might not be 8888. We should use the default port.
                    ),
                    html.Div(id=status)
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2('Query'),
                            dbc.Textarea(
                                id=message,
                                placeholder='Input valid query',
                                value='{"output_name": {"execution_dag": "writing_observer", "target_exports": ["docs_with_roster"], "kwargs": {"course_id": 123}}}',
                            ),
                            dbc.Button(
                                'Submit',
                                id=submit
                            )
                        ],
                        lg=6
                    ),
                    dbc.Col(
                        [
                            html.H2('Response'),
                            DashRenderjson(
                                id=response,
                                invert_theme=True,
                                max_depth=4
                            )
                        ],
                        lg=6
                    )
                ],
            )
        ],
        fluid=True
    )
    return cont


def create_status(title, icon):
    '''
    Are we connected to the server? Connecting? Disconnected? Used by update_status below
    '''
    return html.Div(
        [
            html.I(className=f'{icon} me-1'),
            title
        ]
    )


@callback(
    Output(status, 'children'),
    Input(ws, 'state')
)
def update_status(state):
    '''
    Called when we connect / disconnect / etc.
    '''
    icons = ['fas fa-sync-alt', 'fas fa-check text-success', 'fas fa-sync-alt', 'fas fa-times text-danger']
    titles = ['Connecting to server', 'Connected to server', 'Closing connection', 'Disconnected from server']
    index = state.get('readyState', 3) if state is not None else 3
    return create_status(titles[index], icons[index])


@callback(
    Output(submit, 'disabled'),
    Input(message, 'value')
)
def determine_valid_json(value):
    '''
    Disable or enable to submit button, so we can only submit a
    query if it is valid JSON
    '''
    if value is None:
        return True
    try:
        json.loads(value)
        return False
    except ValueError:
        return True


@callback(
    Output(ws, 'send'),
    Input(submit, 'n_clicks'),
    State(message, 'value')
)
def send_message(clicks, value):
    '''
    Send a message to the communication protocol on the web socket.
    '''
    if clicks is None:
        raise PreventUpdate
    return value


@callback(
    Output(response, 'data'),
    Input(ws, 'message')
)
def receive_message(message):
    '''
    Shows messages from the web socket in the field with ID
    `response` (defined on top)
    '''
    if message is None:
        return {}
    return json.loads(message.get("data", {}))
