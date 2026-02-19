'''
This file creates an All-In-One component for the Learning
Observer server connection. This handles updating data from the
server (based on individual tree updates), storing any errors
that occured, and showing the time since it was last updated.
'''
from dash import html, dcc, clientside_callback, Output, Input, State, MATCH
import uuid

from .LOConnection import LOConnection

class LOConnectionAIO(html.Div):
    class ids:
        websocket = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'websocket',
            'aio_id': aio_id
        }
        connection_status = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'connection_status',
            'aio_id': aio_id
        }
        last_updated_store = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'last_updated_store',
            'aio_id': aio_id
        }
        last_updated_time = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'last_updated_time',
            'aio_id': aio_id
        }
        last_updated_interval = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'last_updated_interval',
            'aio_id': aio_id
        }
        ws_store = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'ws_store',
            'aio_id': aio_id
        }
        error_store = lambda aio_id: {
            'component': 'LOConnectionAIO',
            'subcomponent': 'error_store',
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
            dcc.Store(id=self.ids.last_updated_store(aio_id), data=-1),
            dcc.Store(id=self.ids.ws_store(aio_id), data={}),
            dcc.Store(id=self.ids.error_store(aio_id), data={})
        ]
        super().__init__(component)

    # Update connection status information
    clientside_callback(
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

    # Update connection last modified text
    clientside_callback(
        '''function (lastTime, intervals) {
            if (lastTime === -1) {
                return 'Never';
            }
            const currTime = new Date();
            const secondDiff = (currTime.getTime() - lastTime.getTime())/1000
            if (secondDiff < 1) {
                return 'just now'
            }
            const ms_since_last_message = rendertime2(secondDiff);
            return `${ms_since_last_message} ago`;
        }
        ''',
        Output(ids.last_updated_time(MATCH), 'children'),
        Input(ids.last_updated_store(MATCH), 'data'),
        Input(ids.last_updated_interval(MATCH), 'n_intervals')
    )

    # Update when the data was last modified
    clientside_callback(
        '''function (data) {
            if (data !== undefined) {
                return new Date();
            }
            return window.dash_clientside.no_update;
        }''',
        Output(ids.last_updated_store(MATCH), 'data'),
        Input(ids.websocket(MATCH), 'message')
    )

    # Handle incoming message from server
    clientside_callback(
        '''function (incomingMessage, currentData, errorStore) {
            // console.log('LOConnection', incomingMessage, currentData, errorStore);
            if (incomingMessage !== undefined) {
                const messages = JSON.parse(incomingMessage.data);
                messages.forEach(message => {
                    const pathKeys = message.path.split('.');
                    let current = currentData;

                    // Traverse the path to get to the right location
                    for (let i = 0; i < pathKeys.length - 1; i++) {
                        const key = pathKeys[i];
                        if (!(key in current)) {
                        current[key] = {}; // Create path if it doesn't exist
                        }
                        current = current[key];
                    }

                    if ('error' in message.value) {
                        errorStore[message.path] = message.value;
                    } else {
                        delete errorStore[message.path];
                    }
                    const finalKey = pathKeys[pathKeys.length - 1];
                    if (message.op === 'update') {
                        if (current[finalKey] === undefined) {
                            current[finalKey] = {};
                        }
                        if ('error' in message.value) {
                            current[finalKey]['error'] = message.value;
                            current[finalKey]['option_hash'] = message.value['option_hash'];
                        } else {
                            delete current[finalKey]['error'];
                            // Shallow merge using spread syntax
                            current[finalKey] = {
                            ...current[finalKey], // Existing data
                            ...message.value // New data (overwrites where necessary)
                            };
                        }
                    }
                });
                return [currentData, errorStore]; // Return updated data
            }
            return window.dash_clientside.no_update;
        }''',
        Output(ids.ws_store(MATCH), 'data'),
        Output(ids.error_store(MATCH), 'data'),
        Input(ids.websocket(MATCH), 'message'),
        State(ids.ws_store(MATCH), 'data'),
        State(ids.error_store(MATCH), 'data')
    )
