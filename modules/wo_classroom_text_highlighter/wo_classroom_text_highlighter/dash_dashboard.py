'''
This file creates the layout and defines any callbacks
for the classroom highlight dashboard.
'''
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL
import dash_bootstrap_components as dbc
import dash_renderjson
import lo_dash_react_components as lodrc

import learning_observer.settings
import wo_classroom_text_highlighter.options
import wo_classroom_text_highlighter.preset_component

DEBUG_FLAG = learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV

_prefix = 'wo-classroom-text-highlighter'
_namespace = 'wo_classroom_text_highlighter'
_websocket = f'{_prefix}-websocket'
_output = f'{_prefix}-output'

# loading message/bar DOM ids
_loading_prefix = f'{_prefix}-loading'
_loading_collapse = f'{_loading_prefix}-collapse'
_loading_progress = f'{_loading_prefix}-progress-bar'
_loading_information = f'{_loading_prefix}-information-text'

loading_component = dbc.Collapse([
    html.Div(id=_loading_information),
    dbc.Progress(id=_loading_progress, animated=True, striped=True, max=1.1)
], id=_loading_collapse, is_open=False)

# Option components
_options_toggle = f'{_prefix}-options-toggle'
_options_toggle_count = f'{_prefix}-options-toggle-count'
_options_collapse = f'{_prefix}-options-collapse'
_options_close = f'{_prefix}-options-close'
# TODO abstract these into a more generic options component
_options_prefix = f'{_prefix}-options'
_options_doc_src = f'{_options_prefix}-document-source'
_options_width = f'{_options_prefix}-width'
_options_height = f'{_options_prefix}-height'
_options_hide_header = f'{_options_prefix}-hide-names'
_options_text_information = f'{_options_prefix}-text-information'

options_component = html.Div([
    html.Div([
        html.H3('Settings', className='d-inline-block'),
        dbc.Button(
            html.I(className='fas fa-close'),
            className='float-end', id=_options_close,
            color='transparent'),
    ]),
    lodrc.LODocumentSourceSelectorAIO(aio_id=_options_doc_src),
    dbc.Card([
        dbc.CardHeader('View Options'),
        dbc.CardBody([
            dbc.Label('Students per row'),
            dbc.Input(type='number', min=1, max=10, value=2, step=1, id=_options_width),
            dbc.Label('Height of student tile'),
            dcc.Slider(min=100, max=800, marks=None, value=500, id=_options_height),
            dbc.Label('Student profile'),
            dbc.Switch(value=True, id=_options_hide_header, label='Show/Hide'),
        ])
    ]),
    dbc.Card([
        dbc.CardHeader('Information Options'),
        dbc.CardBody([
            wo_classroom_text_highlighter.preset_component.create_layout(),
            lodrc.WOSettings(
                id=_options_text_information,
                options=wo_classroom_text_highlighter.options.OPTIONS,
                value=wo_classroom_text_highlighter.options.DEFAULT_VALUE,
                className='table table-striped align-middle'
            )
        ])
    ])
], className='p-2')

# Legend
_legend = f'{_prefix}-legend'
_legend_button = f'{_legend}-button'
_legend_children = f'{_legend}-children'

# Expanded student
_expanded_student = f'{_prefix}-expanded-student'
_expanded_student_panel = f'{_expanded_student}-panel'
_expanded_student_child = f'{_expanded_student}-child'
_expanded_student_close = f'{_expanded_student}-close'
expanded_student_component = html.Div([
    html.Div([
        html.H3('Individual Student', className='d-inline-block'),
        dbc.Button(
            html.I(className='fas fa-close'),
            className='float-end', id=_expanded_student_close,
            color='transparent'),
    ]),
    html.Div(id=_expanded_student_child)
], className='p-2')

# Alert Component
_alert = f'{_prefix}-alert'
_alert_text = f'{_prefix}-alert-text'
_alert_error_dump = f'{_prefix}-alert-error-dump'

alert_component = dbc.Alert([
    html.Div(id=_alert_text),
    html.Div(dash_renderjson.DashRenderjson(id=_alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
], id=_alert, color='danger', is_open=False)

# Settings buttons
input_group = dbc.InputGroup([
    dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
    dbc.Button([
        html.I(className='fas fa-cog me-1'),
        'Options (',
        html.Span('0', id=_options_toggle_count),
        ')'
    ], id=_options_toggle),
    dbc.Button(
        'Legend',
        id=_legend_button, color='primary'),
    dbc.Popover(
        id=_legend_children, target=_legend_button,
        trigger='focus', body=True, placement='bottom'),
    lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
], class_name='align-items-center')


def layout():
    '''
    Function to define the page's layout.
    '''
    page_layout = html.Div([
        html.H1('Writing Observer - Classroom Text Highlighter'),
        alert_component,
        html.Div([
            html.Div(input_group, className='d-flex me-2'),
            html.Div(loading_component, className='d-flex')
        ], className='d-flex sticky-top pb-1 bg-light'),
        lodrc.LOPanelLayout(
            html.Div(id=_output, className='d-flex justify-content-between flex-wrap'),
            panels=[
                {'children': options_component, 'width': '30%', 'id': _options_prefix, 'side': 'left' },
                {'children': expanded_student_component,
                 'width': '30%', 'id': _expanded_student_panel,
                 'side': 'right'}
            ],
            id=_options_collapse, shown=[]
        ),
    ])
    return page_layout


# Send the initial state based on the url hash to LO.
# If this is not included, nothing will be returned from
# the communication protocol.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(lodrc.LODocumentSourceSelectorAIO.ids.kwargs_store(_options_doc_src), 'data'),
    Input(_options_text_information, 'value')
)

# Build the UI based on what we've received from the
# communicaton protocol
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='populateOutput'),
    Output(_output, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_options_text_information, 'value'),
    Input(_options_width, 'value'),
    Input(_options_height, 'value'),
    Input(_options_hide_header, 'value'),
    State(_options_text_information, 'options'),
)

# Toggle if the options collapse is open or not
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleOptions'),
    Output(_options_collapse, 'shown'),
    Input(_options_toggle, 'n_clicks'),
    State(_options_collapse, 'shown')
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='closeOptions'),
    Output(_options_collapse, 'shown', allow_duplicate=True),
    Input(_options_close, 'n_clicks'),
    State(_options_collapse, 'shown'),
    prevent_initial_call=True
)

# Adjust student tile size
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='adjustTileSize'),
    Output({'type': 'WOStudentTile', 'index': ALL}, 'style'),
    Input(_options_width, 'value'),
    Input(_options_height, 'value'),
    State({'type': 'WOStudentTile', 'index': ALL}, 'id'),
)

# Handle showing or hiding the student tile header
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='showHideHeader'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'showName'),
    Input(_options_hide_header, 'value'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# When options change, update the current option hash for all students.
# When the option hash is different from the students internal option hash
# a loading class is applied to each student tile.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateCurrentOptionHash'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'currentOptionHash'),
    Input(_options_text_information, 'value'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# Expand a single student
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='expandCurrentStudent'),
    Output(_expanded_student_child, 'children'),
    Output(_options_collapse, 'shown', allow_duplicate=True),
    Input({'type': 'WOStudentTileExpand', 'index': ALL}, 'n_clicks'),
    Input({'type': 'WOStudentTile', 'index': ALL}, 'children'),
    State({'type': 'WOStudentTile', 'index': ALL}, 'id'),
    State(_options_collapse, 'shown'),
    State(_expanded_student_child, 'children'),
    prevent_initial_call=True
)

# Close expanded student
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='closeExpandedStudent'),
    Output(_options_collapse, 'shown', allow_duplicate=True),
    Input(_expanded_student_close, 'n_clicks'),
    State(_options_collapse, 'shown'),
    prevent_initial_call=True
)


# Update the alert component with any errors that come through
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateAlertWithError'),
    Output(_alert_text, 'children'),
    Output(_alert, 'is_open'),
    Output(_alert_error_dump, 'data'),
    Input(lodrc.LOConnectionAIO.ids.error_store(_websocket), 'data')
)

# Save options as preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='addPreset'),
    Output(wo_classroom_text_highlighter.preset_component._store, 'data'),
    Input(wo_classroom_text_highlighter.preset_component._add_button, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._add_input, 'value'),
    State(_options_text_information, 'value'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data')
)

# Apply clicked preset
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applyPreset'),
    Output(_options_text_information, 'value'),
    Input({'type': wo_classroom_text_highlighter.preset_component._set_item, 'index': ALL}, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data'),
    prevent_initial_call=True
)

# update loading information
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLoadingInformation'),
    Output(_loading_collapse, 'is_open'),
    Output(_loading_progress, 'value'),
    Output(_loading_information, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_options_text_information, 'value')
)

# Update legend
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLegend'),
    Output(_legend_children, 'children'),
    Output(_options_toggle_count, 'children'),
    Input(_options_text_information, 'value'),
    State(_options_text_information, 'options')
)
