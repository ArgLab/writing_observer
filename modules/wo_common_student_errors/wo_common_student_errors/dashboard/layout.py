'''
Define layout for common student errors
This layout is pretty messy as we are constantly prototyping
new ways of displaying information
'''
# TODO this module no longer works properly since switching
# the communication protocol to use an async generator.
error = f'The module WO Common student errors is not compatible with the communication protocol api.\n'\
        'Please uninstall this module with `pip uninstall wo-common-student-errors`.'
raise RuntimeError(error)
# package imports
import dash_bootstrap_components as dbc
from dash_renderjson import DashRenderjson
import datetime
import lo_dash_react_components as lodrc
import plotly.express as px
import writing_observer.languagetool

from dash import clientside_callback, ClientsideFunction, Output, Input, State, html, dcc

# local imports
from . import activity, individual, aggregate_information, colors, hierarchical_information

# TODO pull this flag from settings
DEBUG_FLAG = True

prefix = 'common-student-errors'
websocket = f'{prefix}-websocket'
ws_store = f'{prefix}-ws-store'
error_store = f'{prefix}-error-store'

alert = f'{prefix}-alert'
alert_text = f'{prefix}-alert-text'
alert_error_dump = f'{prefix}-alert-error-dump'

# document source
doc_src = f'{prefix}-doc-src'
doc_src_date = f'{prefix}-doc-src-date'
doc_src_timestamp = f'{prefix}-doc-src-timestamp'

# error per text length items
error_per_length = f'{prefix}-errors-per-length-graph'
error_per_length_tooltip = f'{prefix}-errors-per-length-tooltip'
error_per_length_figure = px.scatter(
    x=[0], y=[0], text=[''], title='Number of errors compared to text length',
    labels=dict(x='Text length (words)', y='Total Errors')
)
error_per_length_figure.update_layout(clickmode='event+select')
error_per_length_figure.update_traces(hoverinfo='none', hovertemplate=None, marker_size=24, textfont=dict(color='white'), textposition='middle center')

categorical_errors = f'{prefix}-categorical-errors'


def layout():
    '''
    Generic layout function for the common errors dashboard
    '''
    headers = ['Student']
    [headers.append(category) for category in colors.colors.keys()]

    tooltip = dcc.Tooltip(id=error_per_length_tooltip, direction='bottom')
    overall_view = html.Div([
        html.Div([
            dbc.Label('Document Source'),
            dbc.RadioItems(options=[
                {'label': 'Latest Document', 'value': 'latest' },
                {'label': 'Specific Time', 'value': 'ts'},
            ], value='latest', id=doc_src),
            dbc.InputGroup([
                dcc.DatePickerSingle(id=doc_src_date, date=datetime.date.today()),
                dbc.Input(type='time', id=doc_src_timestamp, value=datetime.datetime.now().strftime("%H:%M"))
            ])
        ]),
        activity.layout,
        dcc.Graph(
            id=error_per_length,
            figure=error_per_length_figure,
            clear_on_unhover=True
        ),
        tooltip,
        hierarchical_information.layout,
        aggregate_information.layout,
        html.Div([
            html.H4('Table counts'),
            dbc.Table([
                html.Thead((html.Tr([html.Th(h, className='categorical-table-headers') for h in headers]))),
                html.Tbody(id=categorical_errors)
            ], hover=True),
        ])
    ], className='vh-100 overflow-auto')

    individal_view = html.Div([
        individual.layout
    ], className='vh-100 overflow-auto')

    alert_component = dbc.Alert([
        html.Div(id=alert_text),
        html.Div(DashRenderjson(id=alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
    ], id=alert, color='danger', is_open=False)

    cont = dbc.Container([
        html.H2('Prototype: Work in Progress'),
        html.P(
            'This dashboard is a prototype displaying various features returned from LanguageTool. '
            'LanguageTool is used to determine grammatical and syntax errors in text. '
            'The dashboard is subject to change based on ongoing feedback from teachers.'
        ),
        alert_component,
        lodrc.LOPanelLayout(
            children=overall_view,
            panels=[
                {'children': individal_view, 'width': '40%', 'id': 'individual'},
            ],
            shown=['individual'],
            id='panel'
        ),
        dcc.Store(ws_store, data={'wo': {}}),
        dcc.Store(error_store, data=False if writing_observer.languagetool.lt_started else {'error': 'Language Tool is not running.'}),
        lodrc.LOConnection(id=websocket),
    ], fluid=True)
    return dcc.Loading(cont)



# disbale document date/time options
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disable_doc_src_datetime'),
    Output(doc_src_date, 'disabled'),
    Output(doc_src_timestamp, 'disabled'),
    Input(doc_src, 'value')
)

# send request to LOConnection
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='send_to_loconnection'),
    Output(websocket, 'send'),
    Output(individual.prefix, 'className'),
    Input(websocket, 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(doc_src, 'value'),
    Input(doc_src_date, 'date'),
    Input(doc_src_timestamp, 'value'),
)

# Update the url's hash based on errors per text length graph's selectedData
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_hash_via_graph'),
    Output('_pages_location', 'hash'),
    Input(error_per_length, 'selectedData'),
    State(ws_store, 'data')
)

# store message from LOConnection in storage for later use
clientside_callback(
    '''
    function(message) {
        const data = JSON.parse(message.data)
        return data
    }
    ''',
    Output(ws_store, 'data'),
    Input(websocket, 'message'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_error_storage'),
    Output(error_store, 'data'),
    Input(ws_store, 'data')
)

clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_alert_with_error'),
    Output(alert_text, 'children'),
    Output(alert, 'is_open'),
    Output(alert_error_dump, 'data'),
    Input(error_store, 'data')
)

# populate the activity/inactivity cards
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_activity'),
    Output(activity.inactive, 'children'),
    Output(activity.active, 'children'),
    Input(ws_store, 'data')
)

# update individual student panel based on LOConnection message
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_student_error'),
    Output(individual.student, 'children'),
    Output(individual.text, 'text'),
    Output(individual.text, 'breakpoints'),
    Output(individual.error_sunburst, 'extendData'),
    Output(individual.prefix, 'className', allow_duplicate=True),
    Input(ws_store, 'data'),
    Input('_pages_location', 'hash'),
    prevent_initial_call=True
)

# handle errors per text length graph hover information
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='update_graph_hover'),
    Output(error_per_length_tooltip, 'show'),
    Output(error_per_length_tooltip, 'bbox'),
    Output(error_per_length_tooltip, 'children'),
    Input(error_per_length, 'hoverData'),
    Input(ws_store, 'data')
)

# populate errors per text length graph data
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_error_graph'),
    Output(error_per_length, 'extendData'),
    Input(ws_store, 'data'),
)

# update categorical student aggregation table
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_categorical_errors'),
    Output(categorical_errors, 'children'),
    Input(ws_store, 'data')
)

# parse the data from the LOConnection message for the aggregation information
# note this is different from the aggregation table
clientside_callback(
    ClientsideFunction(namespace='common_student_errors', function_name='receive_populate_agg_info'),
    Output(aggregate_information.data_store, 'data'),
    Input(ws_store, 'data')
)

# provide data to the hierarchical information layout
clientside_callback(
    '''
    function(message) {
        const data = message.wo.lt_combined
        if (!data) {
        return window.dash_clientside.no_update
        }
        return data
    }
    ''',
    Output(hierarchical_information.data_store, 'data'),
    Input(ws_store, 'data')
)
