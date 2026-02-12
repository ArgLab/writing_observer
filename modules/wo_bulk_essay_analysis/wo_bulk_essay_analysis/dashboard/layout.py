'''
Define layout for dashboard that allows teachers to interface
student essays with LLMs.
'''
import dash_bootstrap_components as dbc
from dash_renderjson import DashRenderjson
import lo_dash_react_components as lodrc
import random

from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL

import learning_observer.settings
import wo_classroom_text_highlighter.options

DEBUG_FLAG = learning_observer.settings.RUN_MODE == learning_observer.settings.RUN_MODES.DEV

prefix = 'bulk-essay-analysis'
_websocket = f'{prefix}-websocket'
_namespace = 'bulk_essay_feedback'

# Alert
_alert = f'{prefix}-alert'
_alert_text = f'{prefix}-alert-text'
_alert_error_dump = f'{prefix}-alert-error-dump'

# Query input
query_input = f'{prefix}-query-input'

# Panel layout
panel_layout = f'{prefix}-panel-layout'

# ── Settings modal DOM IDs ─────────────────────────────────────────────
_settings_prefix = f'{prefix}-settings'
_settings_toggle = f'{_settings_prefix}-toggle'
_settings_modal = f'{_settings_prefix}-modal'
_settings_run = f'{_settings_prefix}-run'
_settings_doc_src = f'{_settings_prefix}-document-source'
_settings_width = f'{_settings_prefix}-width'
_settings_height = f'{_settings_prefix}-height'
_settings_hide_header = f'{_settings_prefix}-hide-header'
_settings_text_information = f'{_settings_prefix}-text-information'

# System prompt: staged (in modal) and applied (in store)
_system_input_staged = f'{prefix}-system-prompt-staged'
_system_input_tooltip = f'{_system_input_staged}-tooltip'
_applied_system_prompt = f'{prefix}-applied-system-prompt'
_applied_doc_src = f'{_settings_prefix}-applied-doc-src'

# Placeholder / tag DOM ids
_tags = f'{prefix}-tags'
placeholder_tooltip = f'{_tags}-placeholder-tooltip'
tag = f'{_tags}-tag'
_tag_edit = f'{tag}-edit'
_tag_delete = f'{tag}-delete'
tag_store = f'{_tags}-tags-store'
_tag_add = f'{_tags}-add'
_tag_replacement_id = f'{_tag_add}-replacement-id'
_tag_add_modal = f'{_tag_add}-modal'
_tag_add_open = f'{_tag_add}-open-btn'
_tag_add_label = f'{_tag_add}-label'
_tag_add_text = f'{_tag_add}-text'
_tag_add_upload = f'{_tag_add}-upload'
_tag_add_warning = f'{_tag_add}-warning'
_tag_add_save = f'{_tag_add}-save'

tag_modal = dbc.Modal([
    dbc.ModalHeader('Add Placeholder'),
    dbc.ModalBody([
        dbc.Input(id=_tag_replacement_id, class_name='d-none'),
        dbc.Label('Label'),
        dbc.Input(
            placeholder='Name your placeholder (e.g., "Narrative Grade 8 Rubric")',
            id=_tag_add_label,
            value=''
        ),
        dbc.Label('Contents'),
        dbc.Textarea(
            placeholder='Enter text here... Uploading a file replaces this content',
            id=_tag_add_text,
            style={'height': '300px'},
            value=''
        ),
        dbc.Button(
            dcc.Upload(
                [html.I(className='fas fa-plus me-1'), 'Upload'],
                accept='.txt,.md,.pdf,.docx',
                id=_tag_add_upload
            )
        )
    ]),
    dbc.ModalFooter([
        html.Small(id=_tag_add_warning, className='text-danger'),
        dbc.Button('Save', class_name='ms-auto', id=_tag_add_save),
    ])
], id=_tag_add_modal, is_open=False)

# Prompt history DOM ids
history_body = f'{prefix}-history-body'
history_store = f'{prefix}-history-store'

# Loading message/bar DOM ids
_loading_prefix = f'{prefix}-loading'
_loading_collapse = f'{_loading_prefix}-collapse'
_loading_progress = f'{_loading_prefix}-progress-bar'
_loading_information = f'{_loading_prefix}-information-text'

submit = f'{prefix}-submit-btn'
submit_warning_message = f'{prefix}-submit-warning-msg'
grid = f'{prefix}-essay-grid'

# ── Expanded student modal DOM IDs ─────────────────────────────────────
_expanded_student = f'{prefix}-expanded-student'
_expanded_student_modal = f'{_expanded_student}-modal'
_expanded_student_title = f'{_expanded_student}-title'
_expanded_student_child = f'{_expanded_student}-child'
_expanded_student_show_identity = f'{_expanded_student}-show-identity'
_expanded_student_show_identity_toggle = f'{_expanded_student}-show-identity-toggle'
_expanded_student_doc_title = f'{_expanded_student}-doc-title'
_expanded_student_id = f'{_expanded_student}-id'

expanded_student_id_store = dcc.Store(
    id=_expanded_student_id,
    data=None
)

expanded_student_show_identity_store = dcc.Store(
    id=_expanded_student_show_identity,
    data=True
)

expanded_student_modal = dbc.Modal(
    [
        dbc.ModalHeader([
            dbc.ModalTitle([
                html.Div(id=_expanded_student_title),
                html.Small(
                    id=_expanded_student_doc_title,
                    className='text-muted ms-2',
                    style={'fontSize': '0.75em'}
                ),
            ], className='d-flex align-items-baseline'),
            dbc.Button(
                html.I(className='fas fa-eye', id=f'{_expanded_student_show_identity_toggle}-icon'),
                id=_expanded_student_show_identity_toggle,
                color='link',
                size='sm',
                className='ms-2 text-secondary',
                title='Show/hide student name and document title',
            ),
        ], close_button=True, className='d-flex align-items-center'),
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

# ── Walkthrough DOM IDs ────────────────────────────────────────────────
_walkthrough_prefix = f'{prefix}-walkthrough'
_walkthrough_store = f'{_walkthrough_prefix}-step'
_walkthrough_modal = f'{_walkthrough_prefix}-modal'
_walkthrough_title = f'{_walkthrough_prefix}-title'
_walkthrough_body = f'{_walkthrough_prefix}-body'
_walkthrough_counter = f'{_walkthrough_prefix}-counter'
_walkthrough_back = f'{_walkthrough_prefix}-back'
_walkthrough_next = f'{_walkthrough_prefix}-next'
_walkthrough_done = f'{_walkthrough_prefix}-done'
_walkthrough_skip = f'{_walkthrough_prefix}-skip'
_walkthrough_seen_store = f'{_walkthrough_prefix}-seen'
_help_button = f'{prefix}-help'

walkthrough_seen_store = dcc.Store(
    id=_walkthrough_seen_store,
    storage_type='local',
    data=False
)

walkthrough_store = dcc.Store(id=_walkthrough_store, data=0)

walkthrough_modal = dbc.Modal(
    [
        dbc.ModalHeader(
            dbc.ModalTitle(id=_walkthrough_title),
            close_button=False,
        ),
        dbc.ModalBody(
            html.Div(id=_walkthrough_body),
            style={'minHeight': '200px'},
        ),
        dbc.ModalFooter(
            html.Div([
                html.Small(id=_walkthrough_counter, className='text-muted me-auto'),
                dbc.Button(
                    [html.I(className='fas fa-forward me-1'), 'Skip intro'],
                    id=_walkthrough_skip,
                    color='link',
                    size='sm',
                    className='me-auto text-muted',
                ),
                dbc.Button(
                    [html.I(className='fas fa-arrow-left me-1'), 'Back'],
                    id=_walkthrough_back,
                    color='secondary',
                    outline=True,
                    size='sm',
                    className='me-2',
                ),
                dbc.Button(
                    ['Next', html.I(className='fas fa-arrow-right ms-1')],
                    id=_walkthrough_next,
                    color='primary',
                    size='sm',
                    className='me-2',
                ),
                dbc.Button(
                    [html.I(className='fas fa-check me-1'), 'Get Started!'],
                    id=_walkthrough_done,
                    color='success',
                    size='sm',
                ),
            ], className='d-flex align-items-center w-100'),
        ),
    ],
    id=_walkthrough_modal,
    is_open=False,
    centered=True,
    backdrop='static',
    keyboard=False,
    size='lg',
)

# ── Settings Modal ─────────────────────────────────────────────────────
# Default prompts
system_prompt = (
    'You are a helpful assistant for grade school teachers. Your task is to analyze '
    'student writing and provide clear, constructive, and age-appropriate feedback. '
    'Focus on key writing traits such as clarity, creativity, grammar, and organization. '
    'When summarizing, highlight the main ideas and key details. Always maintain a '
    'positive and encouraging tone to support student growth.'
)

starting_prompt = [
    'Provide 3 bullet points summarizing this text:\n{student_text}',
    'List 3 strengths in this student\'s writing. Use bullet points and focus on creativity or clear ideas:\n{student_text}',
    'Find 2-3 grammar or spelling errors in this text. For each, quote the sentence and suggest a fix:\n{student_text}',
    'Identify 1) Main theme 2) Best sentence 3) One area to improve. Use numbered responses:\n{student_text}',
    'Give one specific compliment and one gentle suggestion to improve this story:\n{student_text}'
]

settings_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle('Dashboard Settings'), close_button=True),
    dbc.ModalBody([
        lodrc.LODocumentSourceSelectorAIO(aio_id=_settings_doc_src),
        dbc.Card([
            dbc.CardHeader('System Prompt'),
            dbc.CardBody([
                html.P(
                    "The system prompt guides the AI's behavior. It sets the context "
                    "for how the AI should analyze or summarize student text.",
                    className='text-muted small mb-2',
                ),
                dbc.Textarea(
                    id=_system_input_staged,
                    value=system_prompt,
                    style={'minHeight': '150px'}
                ),
            ])
        ], className='my-3'),
        dbc.Card([
            dbc.CardHeader('Display Settings'),
            dbc.CardBody([
                dbc.Label('Students per row'),
                dbc.Input(type='number', min=1, max=10, value=2, step=1, id=_settings_width),
                dbc.Label('Height of student tile'),
                dcc.Slider(min=100, max=800, marks=None, value=350, id=_settings_height),
                dbc.Label('Student profile'),
                dbc.Switch(value=True, id=_settings_hide_header, label='Show/Hide'),
            ])
        ], className='mb-3'),
        dbc.Card([
            dbc.CardHeader('Metrics'),
            dbc.CardBody([
                html.P(
                    'Select which metrics to display as badges on each student tile.',
                    className='text-muted small mb-3',
                ),
                lodrc.WOSettings(
                    id=_settings_text_information,
                    options=wo_classroom_text_highlighter.options.PROCESS_OPTIONS,
                    value=wo_classroom_text_highlighter.options.DEFAULT_VALUE,
                    className='table table-striped align-middle'
                )
            ])
        ])
    ], style={'overflowY': 'auto'}),
    dbc.ModalFooter(
        dbc.Button(
            [html.I(className='fas fa-check me-2'), 'Apply'],
            id=_settings_run,
            color='success',
            size='lg',
            className='w-100'
        )
    ),
], id=_settings_modal, is_open=False, size='lg', scrollable=True,
    style={'maxHeight': '100vh'})

# Hidden stores for applied values
applied_system_prompt_store = dcc.Store(
    id=_applied_system_prompt,
    data=system_prompt
)
applied_doc_src_store = dcc.Store(
    id=_applied_doc_src,
    data={}
)

# Alert Component
alert_component = dbc.Alert([
    html.Div(id=_alert_text),
    html.Div(DashRenderjson(id=_alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
], id=_alert, color='danger', is_open=False)

# Loading component
loading_component = dbc.Collapse([
    html.Div(id=_loading_information),
    dbc.Progress(id=_loading_progress, animated=True, striped=True, max=1.1)
], id=_loading_collapse, is_open=False, class_name='mb-1 sticky-top bg-light')

# ── Settings toolbar ───────────────────────────────────────────────────
input_group = dbc.InputGroup([
    dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
    dbc.Button(
        [html.I(className='fas fa-cog me-1'), 'Document Source & Display Settings'],
        id=_settings_toggle,
        color='secondary'
    ),
    dbc.Button(
        [
            html.I(className='fas fa-question-circle me-1'),
            'Help'
        ],
        id=_help_button,
        color='primary',
        title='Reopen the walkthrough guide',
    ),
    lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
], class_name='mb-1 align-items-center')


def layout():
    '''
    Generic layout function to create dashboard
    '''
    # History panel
    history_favorite_panel = dbc.Card([
        dbc.CardHeader('Prompt History'),
        dbc.CardBody([], id=history_body),
        dcc.Store(id=history_store, data=[])
    ], class_name='h-100')

    # Query creator panel
    input_panel = dbc.Card([
        dbc.CardHeader('Prompt Input'),
        dbc.CardBody([
            dbc.Label('Query'),
            dbc.Textarea(
                id=query_input,
                value=random.choice(starting_prompt),
                class_name='h-100',
                style={'minHeight': '150px'}
            ),
            html.Div([
                html.Span([
                    'Placeholders',
                    html.I(className='fas fa-circle-question ms-1', id=placeholder_tooltip)
                ], className='me-1'),
                html.Span([], id=_tags),
                dbc.Button(
                    [html.I(className='fas fa-add me-1'), 'Add'],
                    id=_tag_add_open,
                    class_name='ms-1 mb-1'
                )
            ], className='mt-1'),
            dbc.Tooltip(
                'Click a placeholder to insert it into your query. Upon submission, '
                'it will be replaced with the corresponding value.',
                target=placeholder_tooltip
            ),
            tag_modal,
            dcc.Store(id=tag_store, data={'student_text': ''}),
        ]),
        dbc.CardFooter([
            html.Small(id=submit_warning_message, className='text-secondary'),
            dbc.Button(
                [html.I(className='fas fa-paper-plane me-1'), 'Submit'],
                color='primary',
                id=submit,
                n_clicks=0,
                class_name='float-end'
            )
        ])
    ])

    cont = dbc.Container([
        html.H1('Writing Observer — Classroom AI Feedback Assistant'),
        # Stores
        applied_system_prompt_store,
        applied_doc_src_store,
        walkthrough_store,
        walkthrough_seen_store,
        expanded_student_id_store,
        expanded_student_show_identity_store,
        # Modals
        walkthrough_modal,
        settings_modal,
        expanded_student_modal,
        # Toolbar
        html.Div([
            html.Div(input_group, className='d-flex me-2'),
            html.Div(loading_component, className='d-flex')
        ], className='d-flex sticky-top pb-1 bg-light'),
        alert_component,
        # Prompt input + history
        lodrc.LOPanelLayout(
            input_panel,
            panels=[
                {'children': history_favorite_panel, 'width': '30%', 'id': 'history-favorite'},
            ],
            shown=['history-favorite'],
            id=panel_layout
        ),
        html.H3('Student Text', className='mt-1'),
        html.Div(id=grid, className='d-flex justify-content-between flex-wrap'),
    ], fluid=True)
    return html.Div(cont)


# ══════════════════════════════════════════════════════════════════════
# Walkthrough callbacks
# ══════════════════════════════════════════════════════════════════════

# On load or when step changes, sync with localStorage
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='initWalkthroughFromStorage'),
    Output(_walkthrough_store, 'data', allow_duplicate=True),
    Output(_walkthrough_seen_store, 'data'),
    Input(_walkthrough_store, 'data'),
    State(_walkthrough_seen_store, 'data'),
    prevent_initial_call='initial_duplicate',
)

# Navigate between walkthrough steps
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='navigateWalkthrough'),
    Output(_walkthrough_store, 'data'),
    Input(_walkthrough_next, 'n_clicks'),
    Input(_walkthrough_back, 'n_clicks'),
    Input(_walkthrough_done, 'n_clicks'),
    Input(_walkthrough_skip, 'n_clicks'),
    Input(_help_button, 'n_clicks'),
    State(_walkthrough_store, 'data'),
    prevent_initial_call=True,
)

# Render walkthrough step content
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='renderWalkthroughStep'),
    Output(_walkthrough_title, 'children'),
    Output(_walkthrough_body, 'children'),
    Output(_walkthrough_back, 'disabled'),
    Output(_walkthrough_next, 'style'),
    Output(_walkthrough_done, 'style'),
    Output(_walkthrough_counter, 'children'),
    Output(_walkthrough_modal, 'is_open'),
    Input(_walkthrough_store, 'data'),
)

# ══════════════════════════════════════════════════════════════════════
# Settings modal callbacks
# ══════════════════════════════════════════════════════════════════════

# Toggle settings modal open
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleSettingsModal'),
    Output(_settings_modal, 'is_open'),
    Input(_settings_toggle, 'n_clicks'),
    State(_settings_modal, 'is_open'),
    prevent_initial_call=True
)

# Apply settings and close modal
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='applySettingsAndCloseModal'),
    Output(_applied_system_prompt, 'data'),
    Output(_applied_doc_src, 'data'),
    Output(_settings_modal, 'is_open', allow_duplicate=True),
    Input(_settings_run, 'n_clicks'),
    State(_system_input_staged, 'value'),
    State(lodrc.LODocumentSourceSelectorAIO.ids.kwargs_store(_settings_doc_src), 'data'),
    prevent_initial_call=True
)

# ══════════════════════════════════════════════════════════════════════
# Core dashboard callbacks
# ══════════════════════════════════════════════════════════════════════

# Send request on websocket
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='send_to_loconnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),
    Input('_pages_location', 'hash'),
    Input(submit, 'n_clicks'),
    Input(_applied_doc_src, 'data'),
    State(query_input, 'value'),
    State(_applied_system_prompt, 'data'),
    State(tag_store, 'data'),
)

# Enable/disable submit based on query
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='disableQuerySubmitButton'),
    Output(submit, 'disabled'),
    Output(submit_warning_message, 'children'),
    Input(query_input, 'value'),
    Input(_loading_collapse, 'is_open'),
    Input(tag_store, 'data')
)

# Add submitted query to history
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='update_input_history_on_query_submission'),
    Output(history_store, 'data'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(history_store, 'data')
)

# Update history list display
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='update_history_list'),
    Output(history_body, 'children'),
    Input(history_store, 'data')
)

# Toggle add placeholder modal
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='openTagAddModal'),
    Output(_tag_add_modal, 'is_open'),
    Output(_tag_replacement_id, 'value'),
    Output(_tag_add_label, 'value'),
    Output(_tag_add_text, 'value'),
    Input(_tag_add_open, 'n_clicks'),
    Input({'type': _tag_edit, 'index': ALL}, 'n_clicks'),
    State(tag_store, 'data'),
    State({'type': _tag_edit, 'index': ALL}, 'id'),
)

# Handle file upload to placeholder text field
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='handleFileUploadToTextField'),
    Output(_tag_add_text, 'value', allow_duplicate=True),
    Input(_tag_add_upload, 'contents'),
    Input(_tag_add_upload, 'filename'),
    Input(_tag_add_upload, 'last_modified'),
    prevent_initial_call=True
)

# Update alert with errors
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateAlertWithError'),
    Output(_alert_text, 'children'),
    Output(_alert, 'is_open'),
    Output(_alert_error_dump, 'data'),
    Input(lodrc.LOConnectionAIO.ids.error_store(_websocket), 'data')
)

# Update student grid
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateStudentGridOutput'),
    Output(grid, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(history_store, 'data'),
    Input(_settings_width, 'value'),
    Input(_settings_height, 'value'),
    Input(_settings_hide_header, 'value'),
    Input(_settings_text_information, 'value'),
    State(_settings_text_information, 'options')
)

# Append tag to query input
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='add_tag_to_input'),
    Output(query_input, 'value', allow_duplicate=True),
    Input({'type': tag, 'index': ALL}, 'n_clicks'),
    State(query_input, 'value'),
    State(tag_store, 'data'),
    prevent_initial_call=True
)

# Enable/disable save attachment button
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='disableAttachmentSaveButton'),
    Output(_tag_add_save, 'disabled'),
    Output(_tag_add_warning, 'children'),
    Input(_tag_add_label, 'value'),
    Input(_tag_add_text, 'value'),
    State(tag_store, 'data'),
    State(_tag_replacement_id, 'value')
)

# Populate tag word bank
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='update_tag_buttons'),
    Output(_tags, 'children'),
    Input(tag_store, 'data')
)

# Save placeholder to storage
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='savePlaceholder'),
    Output(tag_store, 'data'),
    Output(_tag_add_modal, 'is_open', allow_duplicate=True),
    Input(_tag_add_save, 'n_clicks'),
    State(_tag_add_label, 'value'),
    State(_tag_add_text, 'value'),
    State(_tag_replacement_id, 'value'),
    State(tag_store, 'data'),
    prevent_initial_call=True
)

# Remove placeholder from storage
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='removePlaceholder'),
    Output(tag_store, 'data', allow_duplicate=True),
    Input({'type': _tag_delete, 'index': ALL}, 'submit_n_clicks'),
    State(tag_store, 'data'),
    State({'type': _tag_delete, 'index': ALL}, 'id'),
    prevent_initial_call=True
)

# Update loading information
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateLoadingInformation'),
    Output(_loading_collapse, 'is_open'),
    Output(_loading_progress, 'value'),
    Output(_loading_information, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(history_store, 'data')
)

# Adjust student tile size
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='adjustTileSize'),
    Output({'type': 'WOAIAssistStudentTile', 'index': ALL}, 'style', allow_duplicate=True),
    Output({'type': 'WOAIAssistStudentTileText', 'index': ALL}, 'style', allow_duplicate=True),
    Input(_settings_width, 'value'),
    Input(_settings_height, 'value'),
    State({'type': 'WOAIAssistStudentTile', 'index': ALL}, 'id'),
    prevent_initial_call=True
)

# Expand a single student into modal
# ── Expand: record which student was clicked, open modal ──────────────
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='expandCurrentStudent'),
    Output(_expanded_student_id, 'data'),
    Output(_expanded_student_modal, 'is_open'),
    Output(_expanded_student_show_identity, 'data'),
    Input({'type': 'WOAIAssistStudentTileExpand', 'index': ALL}, 'n_clicks'),
    State({'type': 'WOAIAssistStudentTile', 'index': ALL}, 'id'),
    State(_expanded_student_modal, 'is_open'),
    State(_expanded_student_id, 'data'),
    State(_settings_hide_header, 'value'),
    prevent_initial_call=True
)

# ── Expand: reactively render content from live websocket data ────────
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='renderExpandedStudent'),
    Output(_expanded_student_title, 'children'),
    Output(_expanded_student_doc_title, 'children'),
    Output(_expanded_student_child, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_expanded_student_id, 'data'),
    State(_expanded_student_modal, 'is_open'),
    State(history_store, 'data'),
    State(_settings_text_information, 'value'),
    State(_settings_text_information, 'options'),
)

# Toggle identity visibility within the expanded modal
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleExpandedStudentIdentity'),
    Output(_expanded_student_show_identity, 'data', allow_duplicate=True),
    Input(_expanded_student_show_identity_toggle, 'n_clicks'),
    State(_expanded_student_show_identity, 'data'),
    prevent_initial_call=True
)

# Render identity visibility in the expanded modal (hide/show name, doc title, icon)
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='renderExpandedStudentIdentity'),
    Output(_expanded_student_title, 'style'),
    Output(_expanded_student_doc_title, 'style'),
    Output(f'{_expanded_student_show_identity_toggle}-icon', 'className'),
    Input(_expanded_student_show_identity, 'data'),
)

# Show/hide student tile headers
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='showHideHeader'),
    Output({'type': 'WOAIAssistStudentTileText', 'index': ALL}, 'showName'),
    Input(_settings_hide_header, 'value'),
    State({'type': 'WOAIAssistStudentTileText', 'index': ALL}, 'id'),
)
