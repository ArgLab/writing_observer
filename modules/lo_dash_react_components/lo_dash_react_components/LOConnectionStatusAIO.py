'''
This file creates an All-In-One component for the Learning
Observer server connection. This handles updating data from the
server and showing the time since it was last updated.

TODO this file is still being used by the cookiecutter module.
This was replaced by LOConnectionAIO to utilize the new method
of updating data.
'''
from dash import html, dcc, clientside_callback, Output, Input, MATCH
import uuid

from .LOConnection import LOConnection

class LOConnectionStatusAIO(html.Div):
    class ids:
        websocket = lambda aio_id: {
            'component': 'LOConnectionStatus',
            'subcomponent': 'websocket',
            'aio_id': aio_id
        }
        connection_status = lambda aio_id: {
            'component': 'LOConnectionStatus',
            'subcomponent': 'connection_status',
            'aio_id': aio_id
        }
        last_updated_store = lambda aio_id: {
            'component': 'LOConnectionStatus',
            'subcomponent': 'last_updated_store',
            'aio_id': aio_id
        }
        last_updated_time = lambda aio_id: {
            'component': 'LOConnectionStatus',
            'subcomponent': 'last_updated_time',
            'aio_id': aio_id
        }
        last_updated_interval = lambda aio_id: {
            'component': 'LOConnectionStatus',
            'subcomponent': 'last_updated_interval',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(self, aio_id=None, data_scope=None):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        # Determine which state we are in
        component = [
            html.I(id=self.ids.connection_status(aio_id)),
            html.Span('Last Updated:', className='mx-1'),
            html.Span(id=self.ids.last_updated_time(aio_id)),
            dcc.Interval(id=self.ids.last_updated_interval(aio_id), interval=5000),
            LOConnection(id=self.ids.websocket(aio_id), data_scope=data_scope),
            dcc.Store(id=self.ids.last_updated_store(aio_id), data=-1)
        ]
        super().__init__(component)

    clientside_callback(
        # ClientsideFunction(namespace='lo_dash_react_components', function_name='update_connection_status_icon'),
        '''function (status) {
            const icons = ['fas fa-sync-alt', 'fas fa-check text-success', 'fas fa-sync-alt', 'fas fa-times text-danger'];
            const titles = ['Connecting to server', 'Connected to server', 'Closing connection', 'Disconnected from server'];
            if (status === undefined) {
                return [icons[3], titles[3]];
            }
            return [icons[status.readyState], titles[status.readyState]];
        }
        ''',
        Output(ids.connection_status(MATCH), 'className'),
        Output(ids.connection_status(MATCH), 'title'),
        Input(ids.websocket(MATCH), 'state'),
    )

    clientside_callback(
        # ClientsideFunction(namespace='lo_dash_react_components', function_name='update_connection_last_modified_text'),
        '''function (lastTime, intervals) {
            if (lastTime === -1) {
                return 'Never';
            }
            const currTime = new Date();
            const secDiff = (currTime.getTime() - lastTime.getTime())/1000
            if (secDiff < 1) {
                return 'just now'
            }
            const ms_since_last_message = rendertime2(secDiff);
            return `${ms_since_last_message} ago`;
        }
        ''',
        Output(ids.last_updated_time(MATCH), 'children'),
        Input(ids.last_updated_store(MATCH), 'data'),
        Input(ids.last_updated_interval(MATCH), 'n_intervals')
    )

    clientside_callback(
        # ClientsideFunction(namespace='lo_dash_react_components', function_name='update_connection_last_modified_store'),
        '''function (data) {
            if (data !== undefined) {
                return new Date();
            }
            return window.dash_clientside.no_update;
        }''',
        Output(ids.last_updated_store(MATCH), 'data'),
        Input(ids.websocket(MATCH), 'message')
    )
