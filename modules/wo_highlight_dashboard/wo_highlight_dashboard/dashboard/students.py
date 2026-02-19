'''
Creates the grid of student cards
'''
# package imports
import learning_observer.constants as constants
from learning_observer.dash_wrapper import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input, State, ALL, MATCH, exceptions as dash_e
import dash_bootstrap_components as dbc
from dash_renderjson import DashRenderjson
import lo_dash_react_components as lodrc
import writing_observer.aggregator

# local imports
from . import settings, settings_defaults, settings_options as so

# TODO pull this flag from settings
DEBUG_FLAG = True

# define ids for the dashboard
# use a prefix to help ensure we don't double up on IDs (guess what happens if you double up? it breaks)
prefix = 'teacher-dashboard'

# individual student items
student_col = f'{prefix}-student-col'  # individual student card wrapper id
student_link = f'{prefix}-student-link'
student_metrics = f'{prefix}-student-metrics'
student_texthighlight = f'{prefix}-student-texthighlight'
student_indicators = f'{prefix}-student-indicators'

student_row = f'{prefix}-student-row'  # overall student row
student_grid = f'{prefix}-student-grid'  # overall student grid wrapper id
websocket = f'{prefix}-websocket'  # websocket to connect to the server (eventually)
student_counter = f'{prefix}-student-counter'  # store item for quick access to the number of students
student_store = f'{prefix}-student-store'  # store item for student information
course_store = f'{prefix}-course-store'  # store item for course id
settings_collapse = f'{prefix}-settings-collapse'  # settings menu wrapper
websocket_status = f'{prefix}-websocket-status'  # websocket status icon
last_updated = f'{prefix}-last-updated'  # data last updated id
last_updated_msg = f'{prefix}-last-updated-text'  # data last updated id
last_updated_interval = f'{prefix}-last-updated-interval'

alert_type = f'{prefix}-alert'
error_alert = f'{prefix}-error-alert'
error_alert_text = f'{prefix}-alert-text'
error_alert_dump = f'{prefix}-alert-error-dump'
initialize_alert = f'{prefix}-initialize-alert'
nlp_running_alert = f'{prefix}-nlp-running-alert'
overall_alert = f'{prefix}-navbar-alert'

msg_counter = f'{prefix}-msg-counter'
nlp_options = f'{prefix}-nlp-options'
assignment_store = f'{prefix}-assignment-info_store'
assignment_name = f'{prefix}-assignment-name'
assignment_desc = f'{prefix}-assignment-description'


def student_dashboard_view(course_id, assignment_id):
    """
    Create a student dashboard view for a given course and assignment.

    Args:
        course_id (str): The ID of the course.
        assignment_id (str): The ID of the assignment.

    Returns:
        html.Div: A Dash component that displays a student dashboard view.

    The student dashboard view consists of a navigation bar at the top and a container
    that contains the main content of the dashboard. The navigation bar displays the
    title of the assignment, a progress bar indicating the status of data fetching, a
    button to open the settings menu, and a button to log out. The container contains
    the description of the assignment, a row of cards that display information about
    each student, and several hidden stores and intervals that store data and update
    the view periodically.

    """
    alert_component = dbc.Alert(
        dcc.Markdown('The analysis features are not enabled on the server. '\
        'The measures provided below are synthetic for testing and debugging. '\
        'Set `modules.writing_observer.use_nlp: true` in the `creds.yaml` '\
        'file to enable analysis tools.'),
        color='danger',
        is_open=(not writing_observer.aggregator.use_nlp)
    )
    navbar = dbc.Navbar(
        [
            # assignment title
            html.H3(
                [
                    # document icon with a right bootstrap margin
                    html.I(className='fas fa-file-lines me-2'),
                    html.Span(id=assignment_name),
                ],
                className='d-inline'
            ),
            html.Div(
                dbc.Progress(
                    value=100, striped=True, animated=True,
                    label='Fetching data...',
                    color='info',
                    id=overall_alert,
                    style={'height': '1.5rem'}
                ),
                className='w-25',
            ),
            # open settings button
            html.Div(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                html.Small(
                                    [
                                        html.I(id=websocket_status),
                                        html.Span('Last Updated: ', className='ms-2'),
                                        html.Span(id=last_updated_msg)
                                    ]
                                ),
                                outline=True,
                                color='dark'
                            ),
                            dbc.DropdownMenu(
                                [
                                    dbc.DropdownMenuItem(
                                        'Settings',
                                        id=settings.open_btn
                                    ),
                                    dbc.DropdownMenuItem(
                                        'Logout',
                                        href='/auth/logout',
                                        external_link=True
                                    ),
                                ],
                                group=True,
                                align_end=True,
                                label='Menu',
                                color='dark',
                                toggle_class_name='dropdown-menu-outline-dark'
                            )
                        ]
                    )
                ],
                className='d-flex align-items-center float-end'
            )
        ],
        sticky='top',
        class_name='justify-content-between align-items-center px-3'
    )
    container = dbc.Container(
        [
            alert_component,
            # assignment description
            html.P(id=assignment_desc),
            dbc.Alert([
                html.Div(id=error_alert_text),
                html.Div(DashRenderjson(id=error_alert_dump), className='' if DEBUG_FLAG else 'd-none')
            ], id=error_alert, color='danger', is_open=False),
            dbc.Alert(
                'Fetching initial data...',
                is_open=False,
                class_name='d-none',
                id={
                    'type': alert_type,
                    'index': initialize_alert
                }
            ),
            dbc.Alert(
                'Running NLP...',
                is_open=False,
                class_name='d-none',
                id={
                    'type': alert_type,
                    'index': nlp_running_alert
                }
            ),
            dbc.Row(
                [
                    # settings panel wrapper
                    dbc.Collapse(
                        dbc.Col(
                            settings.panel,
                            # bootstrap use 100% of (w)idth and (h)eight
                            class_name='w-100 h-100'
                        ),
                        id=settings_collapse,
                        # bootstrap collapse and grid sizing
                        class_name='collapse-horizontal col-xxl-3 col-lg-4 col-md-6',
                        # default open/close
                        is_open=False
                    ),
                    # overall student grid wrapp
                    dbc.Col(
                        dbc.Row(
                            id=student_row,
                            # bootstrap gutters-2 (little bit of space between cards) and w(idth)-100(%)
                            class_name='g-2 w-100'
                        ),
                        id=student_grid,
                        # classname set in callback, default classname should go in the callback
                    )
                ],
                # no spacing between settings and students
                # students already have some space on the sides
                class_name='g-0'
            ),
            lodrc.LOConnection(id=websocket),
            # stores for course and student info + student counter
            dcc.Store(id=course_store),
            dcc.Store(id=assignment_store),
            dcc.Store(
                id=student_store,
                data=[]
            ),
            dcc.Store(
                id=student_counter,
                data=0
            ),
            dcc.Store(
                id=msg_counter,
                data=0
            ),
            dcc.Store(
                id=nlp_options,
                data=[]
            ),
            dcc.Store(
                id=last_updated,
                data=-1
            ),
            dcc.Interval(
                id=last_updated_interval,
                interval=5000
            )
        ],
        fluid=True
    )
    return html.Div([navbar, container], id=prefix)


# set hash parameters
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_course_assignment'),
    Output(course_store, 'data'),
    Output(assignment_store, 'data'),
    Input('_pages_location', 'hash')
)

# fetch the nlp options from the server
# this will only fetch on the first page load since we never update the prefix's className
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='fetch_nlp_options'),
    Output(nlp_options, 'data'),
    Input(prefix, 'className')
)

# set the websocket status icon
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='set_status'),
    Output(websocket_status, 'className'),
    Output(websocket_status, 'title'),
    Input(websocket, 'state')
)

# fetch student info for course
# TODO fix this to pull the roster information better
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_students'),
    Output(student_counter, 'data'),
    Output(student_store, 'data'),
    Input(course_store, 'data')
)

# fetch assignment information from server
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='fetch_assignment_info'),
    Output(assignment_name, 'children'),
    Output(assignment_desc, 'children'),
    Input(course_store, 'data'),
    Input(assignment_store, 'data')
)

# open the settings menu
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='open_settings'),
    Output(settings_collapse, 'is_open'),
    Output({'type': student_col, 'index': ALL}, 'class_name'),
    Output(student_grid, 'class_name'),
    Input(settings.open_btn, 'n_clicks'),
    Input(settings.close_settings, 'n_clicks'),
    State(settings_collapse, 'is_open'),
    State(student_counter, 'data')
)

# Update data from websocket
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='populate_student_data'),
    Output({'type': student_metrics, 'index': ALL}, 'data'),
    Output({'type': student_texthighlight, 'index': ALL}, 'text'),
    Output({'type': student_texthighlight, 'index': ALL}, 'highlight_breakpoints'),
    Output({'type': student_indicators, 'index': ALL}, 'data'),
    Output({'type': student_link, 'index': ALL}, 'href'),
    Output(last_updated, 'data'),
    Output(msg_counter, 'data'),
    Input(websocket, 'message'),
    State(student_store, 'data'),
    State({'type': student_metrics, 'index': ALL}, 'data'),
    State({'type': student_texthighlight, 'index': ALL}, 'text'),
    State({'type': student_texthighlight, 'index': ALL}, 'highlight_breakpoints'),
    State({'type': student_indicators, 'index': ALL}, 'data'),
    State(student_counter, 'data'),
    State(msg_counter, 'data'),
)

clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_error_from_ws'),
    Output(error_alert_text, 'children'),
    Output(error_alert, 'is_open'),
    Output(error_alert_dump, 'data'),
    Input(websocket, 'message'),
)

# update the last updated text
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_last_updated_text'),
    Output(last_updated_msg, 'children'),
    Input(last_updated, 'data'),
    Input(last_updated_interval, 'n_intervals')
)

# send list of wanted nlp options to server
# data will be returned from the server in a separate callback
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='send_options_to_server'),
    Output(websocket, 'send'),
    Input(settings.checklist, 'value'),
    Input(settings.metric_checklist, 'value'),
    Input(settings.highlight_checklist, 'value'),
    Input(settings.indicator_checklist, 'value'),
    Input(settings.sort_by_checklist, 'value'),
    Input(course_store, 'data'),
    Input(settings.doc_src, 'value'),
    Input(settings.doc_src_date, 'date'),
    Input(settings.doc_src_timestamp, 'value')
)

# show or hide the settings checklist for different components
show_hide_module = '''
    function(values, students) {{
        if (values.includes('{id}')) {{
            return Array(students).fill('');
        }}
        return Array(students).fill('d-none');
    }}
    '''
clientside_callback(
    show_hide_module.format(id='metrics'),
    Output({'type': student_metrics, 'index': ALL}, 'class_name'),
    Input(settings.checklist, 'value'),
    State(student_counter, 'data')
)
clientside_callback(
    show_hide_module.format(id='highlight'),
    Output({'type': student_texthighlight, 'index': ALL}, 'class_name'),
    Input(settings.checklist, 'value'),
    State(student_counter, 'data')
)
clientside_callback(
    show_hide_module.format(id='indicators'),
    Output({'type': student_indicators, 'index': ALL}, 'class_name'),
    Input(settings.checklist, 'value'),
    State(student_counter, 'data')
)

clientside_callback(
    # TODO validate that the student link is shown when available
    '''
    function(href) {
        if (typeof href === 'undefined' || href.length === 0) {
            return 'd-none';
        }
        return '';
    }
    ''',
    Output({'type': student_link, 'index': MATCH}, 'class_name'),
    Input({'type': student_link, 'index': MATCH}, 'href')
)

# show or hide the components on all student cards
update_shown_items = '''
    function(values, students) {{
        return Array(students).fill(values.map(x => `${{x}}_{}`));
    }}
'''
clientside_callback(
    update_shown_items.format('metric'),
    Output({'type': student_metrics, 'index': ALL}, 'shown'),
    Input(settings.metric_checklist, 'value'),
    State(student_counter, 'data')
)
clientside_callback(
    update_shown_items.format('highlight'),
    Output({'type': student_texthighlight, 'index': ALL}, 'shown'),
    Input(settings.highlight_checklist, 'value'),
    State(student_counter, 'data')
)
clientside_callback(
    update_shown_items.format('indicator'),
    Output({'type': student_indicators, 'index': ALL}, 'shown'),
    Input(settings.indicator_checklist, 'value'),
    State(student_counter, 'data')
)

# Show/hide the initialization alert
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_hide_initialize_message'),
    Output({'type': alert_type, 'index': initialize_alert}, 'is_open'),
    Input(msg_counter, 'data')
)

# toggle the npl running alert
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='show_nlp_running_alert'),
    Output({'type': alert_type, 'index': nlp_running_alert}, 'is_open'),
    Input(msg_counter, 'data'),
    Input(settings.checklist, 'value'),
    Input(settings.metric_checklist, 'value'),
    Input(settings.highlight_checklist, 'value'),
    Input(settings.indicator_checklist, 'value'),
    Input(settings.sort_by_checklist, 'value'),
)

# update overall page alert based on all alerts
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='update_overall_alert'),
    Output(overall_alert, 'label'),
    Output(overall_alert, 'class_name'),
    Input({'type': alert_type, 'index': ALL}, 'is_open'),
    Input({'type': alert_type, 'index': ALL}, 'children'),
)

# Sort students by indicator values
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='sort_students'),
    Output({'type': student_col, 'index': ALL}, 'style'),
    Input(settings.sort_by_checklist, 'value'),
    Input(settings.sort_toggle, 'value'),
    Input({'type': student_indicators, 'index': ALL}, 'data'),
    State(student_store, 'data'),
    State(settings.sort_by_checklist, 'options'),
    State(student_counter, 'data')
)

# highlight text
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='highlight_text'),
    Output(settings.dummy, 'style'),
    Input(settings.checklist, 'value'),
    Input(settings.highlight_checklist, 'value'),
    Input({'type': student_texthighlight, 'index': ALL}, 'highlight_breakpoints'),
    State(settings.highlight_checklist, 'options')
)


@callback(
    output=dict(
        sort_by_options=Output(settings.sort_by_checklist, 'options'),
        metric_options=Output(settings.metric_checklist, 'options'),
        metric_value=Output(settings.metric_checklist, 'value'),
        # text_options=Output(settings.text_radioitems, 'options'),
        # text_value=Output(settings.text_radioitems, 'value'),
        highlight_options=Output(settings.highlight_checklist, 'options'),
        highlight_value=Output(settings.highlight_checklist, 'value'),
        indicator_options=Output(settings.indicator_checklist, 'options'),
        indicator_value=Output(settings.indicator_checklist, 'value'),
    ),
    inputs=dict(
        course=Input(course_store, 'data'),
        assignment=Input(assignment_store, 'data'),
        options=Input(nlp_options, 'data'),
        essay_type=Input(settings.essay_type, 'value')
    )
)
def fill_in_settings(course, assignment, options, essay_type):
    """
    Fill in the settings for the student performance dashboard based on the selected course and assignment,
    as well as the NLP options. Returns a dictionary of settings that can be used to update the dashboard.

    Args:
        course (dict): A dictionary containing information about the selected course.
        assignment (dict): A dictionary containing information about the selected assignment.
        options (list): A list of NLP options selected by the user.

    Returns:
        dict: A dictionary containing the updated settings for the student performance dashboard. The dictionary has the following keys:
            - sort_by_options: A list of checklist options for sorting the data.
            - metric_options: A list of checklist options for selecting the metrics to display.
            - metric_value: The default metric selected.
            - highlight_options: A list of checklist options for highlighting the data.
            - highlight_value: The default highlight selected.
            - indicator_options: A list of checklist options for selecting the indicators to display.
            - indicator_value: The default indicator selected.
    """
    if len(options) == 0:
        raise dash_e.PreventUpdate
    # populate all settings based on assignment or default

    if essay_type == 'argumentative':
        opt = settings_defaults.general_argumentative
    elif essay_type == 'narrative':
        opt = settings_defaults.general_narrative
    elif essay_type == 'overall':
        opt = settings_defaults.overall
    else:
        opt = settings_defaults.general

    ret = dict(
        sort_by_options=so.create_checklist_options(opt['indicators']['options'], options, 'indicators'),  # same as indicators
        metric_options=so.create_checklist_options(opt['metrics']['options'], options, 'metric'),
        metric_value=opt['metrics']['selected'],
        # text_options=[so.text_options[o] for o in opt['text']['options']],
        # text_value=opt['text']['selected'],
        highlight_options=so.create_checklist_options(opt['highlight']['options'], options, 'highlight'),
        highlight_value=opt['highlight']['selected'],
        indicator_options=so.create_checklist_options(opt['indicators']['options'], options, 'indicators'),
        indicator_value=opt['indicators']['selected'],
    )
    return ret


@callback(
    Output(student_row, 'children'),
    Input(student_store, 'data')
)
def create_cards(students):
    """
    Create a list of Dash Bootstrap Components (dbc) columns, where each column contains
    a dbc Card for a student.

    Args:
        students (list): A list of dictionaries representing the data for each student.

    Returns:
        list: A list of dbc Columns, where each column contains a dbc Card for a student.
    """
    cards = [
        dbc.Col(
            [
                dbc.Card(
                    [
                        html.H4(s['profile']['name']['full_name']),
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    html.I(className='text-body fas fa-up-right-from-square'),
                                    title='Open document in new tab',
                                    target='_blank',
                                    color='white',
                                    id={
                                        'type': student_link,
                                        'index': s[constants.USER_ID]
                                    }
                                )
                            ],
                            className='position-absolute top-0 end-0'
                        ),
                        lodrc.WOMetrics(
                            id={
                                'type': student_metrics,
                                'index': s[constants.USER_ID]
                            }
                        ),
                        html.Div(
                            lodrc.WOTextHighlight(
                                id={
                                    'type': student_texthighlight,
                                    'index': s[constants.USER_ID]
                                }
                            ),
                            className='student-card-text'
                        ),
                        lodrc.WOIndicatorBars(
                            id={
                                'type': student_indicators,
                                'index': s[constants.USER_ID]
                            }
                        )
                    ],
                    body=True,
                    class_name='shadow-card'
                )
            ],
            # pattern matching callback
            id={
                'type': student_col,
                'index': s[constants.USER_ID]
            },
        ) for s in students
    ]
    return cards
