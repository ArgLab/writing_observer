'''
Define layout for dashboard that allows teachers to interface
student essays with LLMs.
'''
import dash_bootstrap_components as dbc
from dash_renderjson import DashRenderjson
import lo_dash_react_components as lodrc
import random

from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input, State, ALL

import wo_classroom_text_highlighter.options

# TODO pull this flag from settings
DEBUG_FLAG = True

prefix = 'bulk-essay-analysis'
_websocket = f'{prefix}-websocket'
_namespace = 'bulk_essay_feedback'

alert = f'{prefix}-alert'
alert_text = f'{prefix}-alert-text'
alert_error_dump = f'{prefix}-alert-error-dump'

query_input = f'{prefix}-query-input'

panel_layout = f'{prefix}-panel-layout'

_advanced = f'{prefix}-advanced'
_advanced_doc_src = f'{_advanced}-document-source'
_advanced_toggle = f'{_advanced}-toggle'
_advanced_collapse = f'{_advanced}-collapse'
_advanced_close = f'{_advanced}-close'
_advanced_width = f'{_advanced}-width'
_advanced_height = f'{_advanced}-height'
_advanced_hide_header = f'{_advanced}-hide-header'
_advanced_text_information = f'{_advanced}-text-information'

_system_input = f'{prefix}-system-prompt-input'
_system_input_tooltip = f'{_system_input}-tooltip'

# placeholder DOM ids
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

# prompt history DOM ids
history_body = f'{prefix}-history-body'
history_store = f'{prefix}-history-store'
favorite_store = f'{prefix}-favorite-store'

# loading message/bar DOM ids
_loading_prefix = f'{prefix}-loading'
_loading_collapse = f'{_loading_prefix}-collapse'
_loading_progress = f'{_loading_prefix}-progress-bar'
_loading_information = f'{_loading_prefix}-information-text'

submit = f'{prefix}-submit-btn'
submit_warning_message = f'{prefix}-submit-warning-msg'
_student_data_wrapper = f'{prefix}-student-data'
grid = f'{prefix}-essay-grid'

# Expanded student
_expanded_student = f'{prefix}-expanded-student'
_expanded_student_selected = f'{_expanded_student}-selected'
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
    dbc.Input(id=_expanded_student_selected, class_name='d-none'),
    html.Div(id=_expanded_student_child)
], className='p-2')

# default prompts
system_prompt = 'You are a helpful assistant for grade school teachers. Your task is to analyze '\
    'student writing and provide clear, constructive, and age-appropriate feedback. '\
    'Focus on key writing traits such as clarity, creativity, grammar, and organization. '\
    'When summarizing, highlight the main ideas and key details. Always maintain a '\
    'positive and encouraging tone to support student growth.'

starting_prompt = [
    'Provide 3 bullet points summarizing this text:\n{student_text}',
    'List 3 strengths in this student\'s writing. Use bullet points and focus on creativity or clear ideas:\n{student_text}',
    'Find 2-3 grammar or spelling errors in this text. For each, quote the sentence and suggest a fix:\n{student_text}',
    'Identify 1) Main theme 2) Best sentence 3) One area to improve. Use numbered responses:\n{student_text}',
    'Give one specific compliment and one gentle suggestion to improve this story:\n{student_text}'
]


def layout():
    '''
    Generic layout function to create dashboard
    '''
    # advanced menu for system prompt
    advanced = html.Div([
        html.Div([
            html.H3('Settings', className='d-inline-block'),
            dbc.Button(
                html.I(className='fas fa-close'),
                className='float-end', id=_advanced_close,
                color='transparent'),
        ]),
        lodrc.LODocumentSourceSelectorAIO(aio_id=_advanced_doc_src),
        dbc.Card([
            dbc.CardHeader('View Options'),
            dbc.CardBody([
                dbc.Label('Students per row'),
                dbc.Input(type='number', min=1, max=10, value=2, step=1, id=_advanced_width),
                dbc.Label('Height of student tile'),
                dcc.Slider(min=100, max=800, marks=None, value=350, id=_advanced_height),
                dbc.Label('Student profile'),
                dbc.Switch(value=True, id=_advanced_hide_header, label='Show/Hide'),
            ])
        ]),
        dbc.Card([
            dbc.CardHeader('Information Options'),
            dbc.CardBody(lodrc.WOSettings(
                id=_advanced_text_information,
                options=wo_classroom_text_highlighter.options.PROCESS_OPTIONS,
                value=wo_classroom_text_highlighter.options.DEFAULT_VALUE,
                className='table table-striped align-middle'
            ))
        ])
    ])

    # history panel
    history_favorite_panel = dbc.Card([
        dbc.CardHeader('Prompt History'),
        dbc.CardBody([], id=history_body),
        dcc.Store(id=history_store, data=[])
    ], class_name='h-100')

    # query creator panel
    input_panel = dbc.Card([
        dbc.CardHeader('Prompt Input'),
        dbc.CardBody([
            dbc.Label([
                'System prompt',
                html.I(className='fas fa-circle-question ms-1', id=_system_input_tooltip)
            ]),
            dbc.Tooltip(
                "A system prompt guides the AI's responses. It sets the context for how the AI should analyze or summarize student text.",
                target=_system_input_tooltip
            ),
            dbc.Textarea(id=_system_input, value=system_prompt, style={'minHeight': '120px'}),
            dbc.Label('Query'),
            dbc.Textarea(id=query_input, value=random.choice(starting_prompt), class_name='h-100', style={'minHeight': '150px'}),
            html.Div([
                html.Span([
                    'Placeholders',
                    html.I(className='fas fa-circle-question ms-1', id=placeholder_tooltip)
                ], className='me-1'),
                html.Span([], id=_tags),
                dbc.Button([html.I(className='fas fa-add me-1'), 'Add'], id=_tag_add_open, class_name='ms-1 mb-1')
            ], className='mt-1'),
            dbc.Tooltip(
                'Click a placeholder to insert it into your query. Upon submission, it will be replaced with the corresponding value.',
                target=placeholder_tooltip
            ),
            tag_modal,
            dcc.Store(id=tag_store, data={'student_text': ''}),
        ]),
        dbc.CardFooter([
            html.Small(id=submit_warning_message, className='text-secondary'),
            dbc.Button('Submit', color='primary', id=submit, n_clicks=0, class_name='float-end')
        ])
    ])

    alert_component = dbc.Alert([
        html.Div(id=alert_text),
        html.Div(DashRenderjson(id=alert_error_dump), className='' if DEBUG_FLAG else 'd-none')
    ], id=alert, color='danger', is_open=False)

    loading_component = dbc.Collapse([
        html.Div(id=_loading_information),
        dbc.Progress(id=_loading_progress, animated=True, striped=True, max=1.1)
    ], id=_loading_collapse, is_open=False, class_name='mb-1 sticky-top bg-light')

    # overall container
    cont = dbc.Container([
        html.H1('Writing Observer - Classroom AI Feedback Assistant'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
            dbc.Button([html.I(className='fas fa-cog me-1'), 'Advanced'], id=_advanced_toggle),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ], class_name='mb-1'),
        lodrc.LOPanelLayout(
            input_panel,
            panels=[
                {'children': history_favorite_panel, 'width': '30%', 'id': 'history-favorite'},
            ],
            shown=['history-favorite'],
            id=panel_layout
        ),
        alert_component,
        html.H3('Student Text', className='mt-1'),
        loading_component,
        lodrc.LOPanelLayout(
            html.Div(id=grid, className='d-flex justify-content-between flex-wrap'),
            panels=[
                {'children': advanced, 'width': '30%', 'id': _advanced_collapse, 'side': 'left' },
                {'children': expanded_student_component,
                 'width': '30%', 'id': _expanded_student_panel,
                 'side': 'right'}
            ],
            id=_student_data_wrapper, shown=[]
        ),
    ], fluid=True)
    return html.Div(cont)


# Toggle if the advanced menu collapse is open or not
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='toggleAdvanced'),
    Output(_student_data_wrapper, 'shown', allow_duplicate=True),
    Input(_advanced_toggle, 'n_clicks'),
    State(_student_data_wrapper, 'shown'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='closeAdvanced'),
    Output(_student_data_wrapper, 'shown', allow_duplicate=True),
    Input(_advanced_close, 'n_clicks'),
    State(_student_data_wrapper, 'shown'),
    prevent_initial_call=True
)

# send request on websocket
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='send_to_loconnection'),
    Output(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash'),
    Input(submit, 'n_clicks'),
    Input(lodrc.LODocumentSourceSelectorAIO.ids.kwargs_store(_advanced_doc_src), 'data'),
    State(query_input, 'value'),
    State(_system_input, 'value'),
    State(tag_store, 'data'),
)

# enable/disabled submit based on query
# makes sure there is a query and the tags are properly formatted
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disableQuerySubmitButton'),
    Output(submit, 'disabled'),
    Output(submit_warning_message, 'children'),
    Input(query_input, 'value'),
    Input(_loading_collapse, 'is_open'),
    Input(tag_store, 'data')
)

# add submitted query to history and clear input
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_input_history_on_query_submission'),
    Output(history_store, 'data'),
    Input(submit, 'n_clicks'),
    State(query_input, 'value'),
    State(history_store, 'data')
)

# update history based on history browser storage
# TODO create a history component that can handle favorites
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_history_list'),
    Output(history_body, 'children'),
    Input(history_store, 'data')
)

# Toggle if the add placeholder is open or not
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

# show attachment panel upon uploading document and populate fields
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='handleFileUploadToTextField'),
    Output(_tag_add_text, 'value', allow_duplicate=True),
    Input(_tag_add_upload, 'contents'),
    Input(_tag_add_upload, 'filename'),
    Input(_tag_add_upload, 'last_modified'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateAlertWithError'),
    Output(alert_text, 'children'),
    Output(alert, 'is_open'),
    Output(alert_error_dump, 'data'),
    Input(lodrc.LOConnectionAIO.ids.error_store(_websocket), 'data')
)

# update student cards based on new data in storage
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='updateStudentGridOutput'),
    Output(grid, 'children'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(history_store, 'data'),
    Input(_advanced_width, 'value'),
    Input(_advanced_height, 'value'),
    Input(_advanced_hide_header, 'value'),
    Input(_advanced_text_information, 'value'),
    State(_advanced_text_information, 'options')
)

# append tag in curly braces to input
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='add_tag_to_input'),
    Output(query_input, 'value', allow_duplicate=True),
    Input({'type': tag, 'index': ALL}, 'n_clicks'),
    State(query_input, 'value'),
    State(tag_store, 'data'),
    prevent_initial_call=True
)

# enable/disable the save attachment button if tag is already in use/blank
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='disableAttachmentSaveButton'),
    Output(_tag_add_save, 'disabled'),
    Output(_tag_add_warning, 'children'),
    Input(_tag_add_label, 'value'),
    Input(_tag_add_text, 'value'),
    State(tag_store, 'data'),
    State(_tag_replacement_id, 'value')
)

# populate word bank of tags
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='update_tag_buttons'),
    Output(_tags, 'children'),
    Input(tag_store, 'data')
)

# save placeholder to storage
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='savePlaceholder'),
    Output(tag_store, 'data'),
    Output(_tag_add_modal, 'is_open', allow_duplicate=True),
    Input(_tag_add_save, 'n_clicks'),
    State(_tag_add_label, 'value'),
    State(_tag_add_text, 'value'),
    State(_tag_replacement_id, 'value'),
    State(tag_store, 'data'),
    prevent_initial_call=True
)

# remove placeholder from storage
clientside_callback(
    ClientsideFunction(namespace='bulk_essay_feedback', function_name='removePlaceholder'),
    Output(tag_store, 'data', allow_duplicate=True),
    Input({'type': _tag_delete, 'index': ALL}, 'submit_n_clicks'),
    State(tag_store, 'data'),
    State({'type': _tag_delete, 'index': ALL}, 'id'),
    prevent_initial_call=True
)

# update loading information
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
    Input(_advanced_width, 'value'),
    Input(_advanced_height, 'value'),
    State({'type': 'WOAIAssistStudentTile', 'index': ALL}, 'id'),
    prevent_initial_call=True
)

# Expand a single student
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='selectStudentForExpansion'),
    Output(_expanded_student_selected, 'value'),
    Output(_student_data_wrapper, 'shown', allow_duplicate=True),
    Input({'type': 'WOAIAssistStudentTileExpand', 'index': ALL}, 'n_clicks'),
    State(_student_data_wrapper, 'shown'),
    State({'type': 'WOAIAssistStudentTile', 'index': ALL}, 'id'),
    prevent_initial_call=True
)

# Update expanded children based on selected student
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='expandSelectedStudent'),
    Output(_expanded_student_child, 'children'),
    Input(_expanded_student_selected, 'value'),
    Input(lodrc.LOConnectionAIO.ids.ws_store(_websocket), 'data'),
    Input(_advanced_hide_header, 'value'),
    Input(history_store, 'data'),
    Input(_advanced_text_information, 'value'),
    State(_advanced_text_information, 'options')
)

# Close expanded student
clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='closeExpandedStudent'),
    Output(_student_data_wrapper, 'shown', allow_duplicate=True),
    Input(_expanded_student_close, 'n_clicks'),
    State(_student_data_wrapper, 'shown'),
    prevent_initial_call=True
)
