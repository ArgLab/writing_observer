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
_options_modal = f'{_prefix}-options-modal'
_options_run = f'{_prefix}-options-run'
_options_prefix = f'{_prefix}-options'
_options_doc_src = f'{_options_prefix}-document-source'
_options_width = f'{_options_prefix}-width'
_options_height = f'{_options_prefix}-height'
_options_hide_header = f'{_options_prefix}-hide-names'
_options_text_information = f'{_options_prefix}-text-information'
_options_text_information_staged = f'{_options_text_information}-staged'

# Store that holds the hash of the currently applied options.
_applied_option_hash = f'{_options_prefix}-applied-hash'

options_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle('Settings'), close_button=True),
    dbc.ModalBody([
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
        ], className='mb-3'),
        dbc.Card([
            dbc.CardHeader('Information Options'),
            dbc.CardBody([
                wo_classroom_text_highlighter.preset_component.create_layout(),
                lodrc.WOSettings(
                    id=_options_text_information_staged,
                    options=wo_classroom_text_highlighter.options.OPTIONS,
                    value=wo_classroom_text_highlighter.options.DEFAULT_VALUE,
                    className='table table-striped align-middle'
                )
            ])
        ])
    ], style={'overflowY': 'auto'}),
    dbc.ModalFooter(
        dbc.Button(
            [html.I(className='fas fa-play me-2'), 'Run'],
            id=_options_run,
            color='success',
            size='lg',
            className='w-100'
        )
    ),
], id=_options_modal, is_open=False, size='lg', scrollable=True,
    style={'maxHeight': '100vh'})

# Hidden store that holds the "applied" text information value.
applied_options_store = dcc.Store(
    id=_options_text_information,
    data=wo_classroom_text_highlighter.options.DEFAULT_VALUE
)

# Hidden store for the pre-computed hash of the applied options.
applied_option_hash_store = dcc.Store(
    id=_applied_option_hash,
    data=''
)

# Legend
_legend = f'{_prefix}-legend'
_legend_button = f'{_legend}-button'
_legend_children = f'{_legend}-children'

# Expanded student modal
_expanded_student = f'{_prefix}-expanded-student'
_expanded_student_modal = f'{_expanded_student}-modal'
_expanded_student_title = f'{_expanded_student}-title'
_expanded_student_child = f'{_expanded_student}-child'

expanded_student_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle('Student', id=_expanded_student_title),
            close_button=True,
        ),
        dbc.ModalBody(
            html.Div(id=_expanded_student_child),
            style={'overflowY': 'auto'},
        ),
    ],
    id=_expanded_student_modal,
    is_open=False,
    size='xl',
    centered=True,
    scrollable=True,
)

# Alert Component
_alert = f'{_prefix}-alert'
_alert_text = f'{_prefix}-alert-text'
_alert_error_dump = f'{_prefix}-alert-error-dump'

alert_component = dbc.Alert([
    html.Div(id=_alert_text),
    html.Div(dash_renderjson.DashRenderjson(id=_alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
], id=_alert, color='danger', is_open=False)

# Panels layout ID
_panels_layout = f'{_prefix}-panels-layout'

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
    page_layout = html.Div([
        html.H1('Writing Observer - Classroom Text Highlighter'),
        alert_component,
        applied_options_store,
        applied_option_hash_store,
        options_modal,
        expanded_student_modal,
        html.Div([
            html.Div(input_group, className='d-flex me-2'),
            html.Div(loading_component, className='d-flex')
        ], className='d-flex sticky-top pb-1 bg-light'),
        lodrc.LOPanelLayout(
            html.Div(id=_output, className='d-flex justify-content-between flex-wrap'),
            panels=[],
            id=_panels_layout, shown=[]
        ),
    ])
    return page_layout


# Send the initial state based on the url hash to LO.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),
    Input('_pages_location', 'hash'),
    Input(lodrc.LODocumentSourceSelectorAIO.ids.kwargs_store(_options_doc_src), 'data'),
    Input(_applied_option_hash, 'data'),
    State(_options_text_information, 'data')
)

# When the applied options store changes, compute and store the hash.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='computeAppliedHash'),
    Output(_applied_option_hash, 'data'),
    Input(_options_text_information, 'data'),
)

# When Run is clicked, apply staged options and close modal.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applyOptionsAndCloseModal'),
    Output(_options_text_information, 'data'),
    Output(_options_modal, 'is_open', allow_duplicate=True),
    Input(_options_run, 'n_clicks'),
    State(_options_text_information_staged, 'value'),
    prevent_initial_call=True
)

# Build the UI
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='populateOutput'),
    Output(_output, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_options_text_information, 'data'),
    Input(_options_width, 'value'),
    Input(_options_height, 'value'),
    Input(_options_hide_header, 'value'),
    State(_options_text_information_staged, 'options'),
    State(_applied_option_hash, 'data'),
)

# Toggle the options modal open
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleOptionsModal'),
    Output(_options_modal, 'is_open'),
    Input(_options_toggle, 'n_clicks'),
    State(_options_modal, 'is_open'),
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

# When applied hash changes, push to all existing student tiles.
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateCurrentOptionHash'),
    Output({'type': 'WOStudentTextTile', 'index': ALL}, 'currentOptionHash'),
    Input(_applied_option_hash, 'data'),
    State({'type': 'WOStudentTextTile', 'index': ALL}, 'id'),
)

# Expand a single student into the modal
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='expandCurrentStudent'),
    Output(_expanded_student_title, 'children'),
    Output(_expanded_student_child, 'children'),
    Output(_expanded_student_modal, 'is_open'),
    Input({'type': 'WOStudentTileExpand', 'index': ALL}, 'n_clicks'),
    Input({'type': 'WOStudentTile', 'index': ALL}, 'children'),
    State({'type': 'WOStudentTile', 'index': ALL}, 'id'),
    State(_expanded_student_modal, 'is_open'),
    State(_expanded_student_child, 'children'),
    prevent_initial_call=True
)

# Update the alert component with any errors
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
    State(_options_text_information_staged, 'value'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data')
)

# Apply clicked preset to the staged settings
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applyPreset'),
    Output(_options_text_information_staged, 'value'),
    Input({'type': wo_classroom_text_highlighter.preset_component._set_item, 'index': ALL}, 'n_clicks'),
    State(wo_classroom_text_highlighter.preset_component._store, 'data'),
    prevent_initial_call=True
)

# Update loading information
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLoadingInformation'),
    Output(_loading_collapse, 'is_open'),
    Output(_loading_progress, 'value'),
    Output(_loading_information, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_applied_option_hash, 'data')
)

# Update legend
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLegend'),
    Output(_legend_children, 'children'),
    Output(_options_toggle_count, 'children'),
    Input(_options_text_information, 'data'),
    State(_options_text_information_staged, 'options')
)
