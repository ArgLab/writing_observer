'''
This file will detail how to build a dashboard using
the Dash framework.

If you are unfamiliar with Dash, it compiles python code
to react and serves it via a Flask server. You can register
callbacks to run when specific states change. Normal callbacks
execute Python code server side, but Clientside callbacks
execute Javascript code client side. Clientside functions are
preferred as it cuts down server and network resources.

This file contains the hard stuff. You'll need to understand
this if you want to build dynamic, interactive dashboards. For
most simple dashboards, we tossed everything you need into
my_layout.
'''
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

from .my_layout import my_layout, my_data_layout

_prefix = '{{ cookiecutter.project_hyphenated }}'
_namespace = '{{ cookiecutter.project_slug }}'
_websocket = f'{_prefix}-websocket'
_output = f'{_prefix}-output'

def layout():
    '''
    Function to define the page's layout.
    '''
    return my_layout(_websocket, _output)

# Send the initial state based on the url hash to LO.
# If this is not included, nothing will be returned from
# the communication protocol.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

# Build the UI based on what we've received from the
# communicaton protocol
# This clientside callback and the serverside callback below are
# the same
# clientside_callback(
#     ClientsideFunction(namespace=_namespace, function_name='populateOutput'),
#     Output(_output, 'children'),
#     Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
# )


@callback(
    Output(_output, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
)
def populate_output(data):
    '''This method creates UI components for each student found
    in the websocket's storage.

    This will use more network traffic and server resources
    than using the equivalent clientside callback, `populateOutput`.
    '''
    return my_data_layout(data)
