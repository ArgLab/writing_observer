'''
This file creates an All-In-One component for the Learning
Observer server connection. This handles updating data from the
server (based on individual tree updates), storing any errors
that occured, and showing the time since it was last updated.
'''
from dash import html, dcc, clientside_callback, Output, Input, State, MATCH
import dash_bootstrap_components as dbc
import datetime
import uuid

class LODocumentSourceSelectorAIO(dbc.Card):
    class ids:
        source_selector = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'source_selector',
            'aio_id': aio_id
        }
        assignment_wrapper = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'assignment_wrapper',
            'aio_id': aio_id
        }
        assignment_input = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'assignment_input',
            'aio_id': aio_id
        }
        datetime_wrapper = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'datetime_wrapper',
            'aio_id': aio_id
        }
        date_input = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'date_input',
            'aio_id': aio_id
        }
        timestamp_input = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'timestamp_input',
            'aio_id': aio_id
        }
        title_text_wrapper = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'title_text_wrapper',
            'aio_id': aio_id
        }
        title_text_input = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'title_text_input',
            'aio_id': aio_id
        }
        kwargs_store = lambda aio_id: {
            'component': 'LODocumentSourceSelectorAIO',
            'subcomponent': 'kwargs_store',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(self, aio_id=None):
        if aio_id is None:
            aio_id = str(uuid.uuid4())
        

        card_body = dbc.CardBody([
            dbc.Label('Source'),
            dbc.RadioItems(
                id=self.ids.source_selector(aio_id),
                options={'latest': 'Latest Document',
                         'assignment': 'Assignment',
                         'timestamp': 'Specific Time',
                         'title_text': 'Text in Title'},
                inline=True,
                value='latest'),
            html.Div('Additional Arguments'),
            html.Div([
                dbc.RadioItems(id=self.ids.assignment_input(aio_id)),
            ], id=self.ids.assignment_wrapper(aio_id)),
            html.Div([
                dbc.InputGroup([
                    dcc.DatePickerSingle(
                        id=self.ids.date_input(aio_id),
                        date=datetime.date.today()),
                    dbc.Input(
                        type='time',
                        id=self.ids.timestamp_input(aio_id),
                        value=datetime.datetime.now().strftime("%H:%M"))
                ])
            ], id=self.ids.datetime_wrapper(aio_id)),
            html.Div([
                dbc.Input(
                    id=self.ids.title_text_input(aio_id),
                    type='text',
                    placeholder='Enter text to match document titles'
                )
            ], id=self.ids.title_text_wrapper(aio_id)),
            dcc.Store(id=self.ids.kwargs_store(aio_id), data={'src': 'latest'})
        ])
        component = [
            dbc.CardHeader('Document Source'),
            card_body
        ]
        super().__init__(component)

    # Update data
    clientside_callback(
        '''function (src, assignment, date, time, titleText) {
            // if (clicks === 0) { return window.dash_clientside.no_update; }
            let kwargs = {};
            if (src === 'assignment') {
                kwargs.assignment = assignment;
            } else if (src === 'timestamp') {
                kwargs.requested_timestamp = new Date(`${date}T${time}`).getTime().toString()
            } else if (src === 'title_text') {
                kwargs.title_text = titleText;
            }
            return {src, kwargs};
        }
        ''',
        Output(ids.kwargs_store(MATCH), 'data'),
        Input(ids.source_selector(MATCH), 'value'),
        Input(ids.assignment_input(MATCH), 'value'),
        Input(ids.date_input(MATCH), 'date'),
        Input(ids.timestamp_input(MATCH), 'value'),
        Input(ids.title_text_input(MATCH), 'value'),
    )

    clientside_callback(
        '''function (src) {
            if (src === 'assignment') {
                return ['d-none', '', 'd-none'];
            } else if (src === 'timestamp') {
                return ['', 'd-none', 'd-none']
            } else if (src === 'title_text') {
                return ['d-none', 'd-none', '']
            }
            return ['d-none', 'd-none', 'd-none'];
        }
        ''',
        Output(ids.datetime_wrapper(MATCH), 'className'),
        Output(ids.assignment_wrapper(MATCH), 'className'),
        Output(ids.title_text_wrapper(MATCH), 'className'),
        Input(ids.source_selector(MATCH), 'value'),
    )

    clientside_callback(
        '''async function (id, hash, currentSource) {
            const noUpdate = window.dash_clientside.no_update;
            if (!hash || hash.length === 0) { return [noUpdate, noUpdate, noUpdate]; }
            const decoded = decode_string_dict(hash.slice(1));
            if (!decoded.course_id) { return [noUpdate, noUpdate, noUpdate]; }

            const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/webapi/courseassignments/${decoded.course_id}`);
            const data = await response.json();
            const assignmentOptions = data.map(function (item) {
                return { label: item.title, value: item.id };
            });

            const sourceOptions = [
                { label: 'Latest Document', value: 'latest' },
                { label: 'Specific Time', value: 'timestamp' },
                { label: 'Text in Title', value: 'title_text' },
            ];
            if (assignmentOptions.length > 0) {
                sourceOptions.splice(1, 0, { label: 'Assignment', value: 'assignment' });
            }

            let sourceValue = currentSource;
            if (sourceValue === 'assignment' && assignmentOptions.length === 0) {
                sourceValue = 'latest';
            }

            return [assignmentOptions, sourceOptions, sourceValue];
        }
        ''',
        Output(ids.assignment_input(MATCH), 'options'),
        Output(ids.source_selector(MATCH), 'options'),
        Output(ids.source_selector(MATCH), 'value'),
        Input(ids.source_selector(MATCH), 'id'),
        Input('_pages_location', 'hash'),
        State(ids.source_selector(MATCH), 'value'),
    )
