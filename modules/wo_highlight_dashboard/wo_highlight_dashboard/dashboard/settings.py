'''
Defines the settings panel used on the student overview dashbaord view
'''
# package imports
from learning_observer.dash_wrapper import html, dcc, clientside_callback, ClientsideFunction, Output, Input
import dash_bootstrap_components as dbc
import datetime

prefix = 'teacher-dashboard-settings'
# ids related to opening/closing panel
open_btn = f'{prefix}-show-hide-open-button'  # settings button
offcanvas = f'{prefix}-show-hide-offcanvcas'  # setting wrapper
close_settings = f'{prefix}-close'  # X on settings panel

# document source
doc_src = f'{prefix}-doc-src'
doc_src_date = f'{prefix}-doc-src-date'
doc_src_timestamp = f'{prefix}-doc-src-timestamp'

# essay type
essay_type = f'{prefix}-essay-type'

# ids related to sorting
sort_by_checklist = f'{prefix}-sort-by-checklist'  # options that can be included for sorting
sort_toggle = f'{prefix}-sort-by-toggle'  # checkbox for determining sort direction
sort_icon = f'{prefix}-sort-by-icon'  # icon for sort direction
sort_label = f'{prefix}-sort-by-label'  # text for sort direction
sort_reset = f'{prefix}-sort-by-reset'  # sort reset button
# ids relating to showing or hiding elements
checklist = f'{prefix}-show-hide-checklist'  # parent checklist - determines which type of stuff to show
metric_collapse = f'{prefix}-show-hide-metric-collapse'  # metric options wrapper
metric_checklist = f'{prefix}-show-hide-metric-checklist'  # metric options
text_collapse = f'{prefix}-show-hide-text-collapse'  # text options wrapper
text_radioitems = f'{prefix}-show-hide-text-radioitems'  # text options
highlight_collapse = f'{prefix}-show-hide-highlight-collapse'  # highlight options wrapper
highlight_checklist = f'{prefix}-show-hide-highlight-radioitems'  # highlight options
indicator_collapse = f'{prefix}-show-hide-indicator-collapse'  # indicator options wrapper
indicator_checklist = f'{prefix}-show-hide-indicator-checklist'  # indicator wrapper
dummy = f'{prefix}-dummy'

# settings panel itself
panel = dbc.Card(
    [
        html.Div(id=dummy),
        html.Div(
            [
                # panel title
                html.H4(
                    [
                        html.I(className='fas fa-gear me-2'),  # gear icon
                        'Settings'
                    ],
                    # bootstrap styling to allow for the floating X button and remove lower margin
                    className='d-inline mb-0'
                ),
                # close settings X
                dbc.Button(
                    # font awesome X icon
                    html.I(className='fas fa-xmark'),
                    color='white',
                    # bootstrap text styling
                    class_name='text-body',
                    id=close_settings
                )
            ],
            # create flex container so children can be positioned properly
            className='m-2 d-flex align-items-center justify-content-between'
        ),
        # Each settings option is an accordion item
        dbc.Accordion(
            [
                # essay type
                dbc.AccordionItem(
                    html.Div([
                        dbc.RadioItems(options=[
                            {'label': 'Latest Document', 'value': 'latest' },
                            {'label': 'Specific Time', 'value': 'ts'},
                        ], value='latest', id=doc_src),
                        dbc.InputGroup([
                            dcc.DatePickerSingle(id=doc_src_date, date=datetime.date.today()),
                            dbc.Input(type='time', id=doc_src_timestamp, value=datetime.datetime.now().strftime("%H:%M"))
                        ])
                    ]), title='Document Source'
                ),
                dbc.AccordionItem(
                    html.Div([
                        dbc.RadioItems(options=[
                            {'label': 'All', 'value': 'overall' },
                            {'label': 'Argumentative', 'value': 'argumentative'},
                            {'label': 'Narrative', 'value': 'narrative'}
                        ], value='overall', id=essay_type)
                    ]), title='Essay Type'
                ),
                # sort by
                dbc.AccordionItem(
                    dbc.Card(
                        [
                            dcc.Checklist(
                                options=[],
                                value=[],
                                id=sort_by_checklist,
                                labelClassName='form-check nested-form',  # style dcc as bootstrap
                                inputClassName='form-check-input'  # style dcc as bootstrap
                            ),
                            html.Div(
                                # button group for sort buttons
                                dbc.ButtonGroup(
                                    [
                                        # change sort direction
                                        dbc.Button(
                                            dcc.Checklist(
                                                options=[
                                                    {
                                                        'value': 'checked',
                                                        'label': html.Span(  # define Dash component as checklist option
                                                            [
                                                                html.I(id=sort_icon),
                                                                html.Span(
                                                                    'None',
                                                                    id=sort_label,
                                                                    className='ms-1'
                                                                )
                                                            ]
                                                        )
                                                    }
                                                ],
                                                value=[],
                                                id=sort_toggle,
                                                inputClassName='d-none',  # hide the checkbox, icon/text are clickable
                                                className='d-inline',  # needed to style for components as options
                                            ),
                                            outline=True,
                                            color='primary',
                                            title='Arrange students by attributes',
                                        ),
                                        # reset sort button
                                        dbc.Button(
                                            [
                                                html.I(className='fas fa-rotate me-1'),  # font awesome rotate icon
                                                'Reset Sort'
                                            ],
                                            id=sort_reset,
                                            outline=True,
                                            color='primary'
                                        )
                                    ],
                                    size='sm',
                                    class_name='float-end d-inline'  # bootstrap keep button group to the right
                                ),
                                className='mt-1'  # bootstrap top margin
                            )
                        ],
                        class_name='border-0'  # bootstrap remove borders
                    ),
                    title='Sort by'  # hover text
                ),
                # show/hide elements
                dbc.AccordionItem(
                    [
                        dcc.Checklist(
                            options=[
                                # metrics
                                {
                                    'label': html.Span(
                                        [
                                            html.Span(
                                                [
                                                    html.I(className='fas fa-hashtag me-1'),
                                                    'Metrics overview'
                                                ],
                                                className='font-size-lg'  # make labels a little bigger
                                            ),
                                            dbc.Collapse(
                                                dcc.Checklist(
                                                    # option for each possible metric
                                                    options=[],
                                                    value=[],  # defaults
                                                    id=metric_checklist,
                                                    labelClassName='form-check nested-form',  # style dcc as Bootstrap and add nested hover
                                                    inputClassName='form-check-input'  # style dcc as Bootstrap
                                                ),
                                                id=metric_collapse,
                                            )
                                        ],
                                    ),
                                    'value': 'metrics'
                                },
                                # text
                                # {
                                #     'label': html.Span(
                                #         [
                                #             html.Span(
                                #                 [
                                #                     html.I(className='fas fa-file me-1'),
                                #                     'Text',
                                #                 ],
                                #                 className='font-size-lg'
                                #             ),
                                #             dbc.Collapse(
                                #                 dcc.RadioItems(
                                #                     # option for each possible text item
                                #                     # TODO pull this information from somewhere
                                #                     options=[],
                                #                     value=None,  # default option
                                #                     id=text_radioitems,
                                #                     labelClassName='form-check nested-form',  # style dcc as Bootstrap and add nested hover
                                #                     inputClassName='form-check-input'  # style dcc as Bootstrap
                                #                 ),
                                #                 id=text_collapse,
                                #             )
                                #         ],
                                #     ),
                                #     'value': 'text'
                                # },
                                # highlight
                                {
                                    'label': html.Span(
                                        [
                                            html.Span(
                                                [
                                                    html.I(className='fas fa-highlighter fa-flip-horizontal me-1'),
                                                    'Highlight',
                                                ],
                                                className='font-size-lg'
                                            ),
                                            dbc.Collapse(
                                                dcc.Checklist(
                                                    # option for each possible highlightable item
                                                    # TODO pull this information from somewhere
                                                    options=[],
                                                    value=[],  # default options
                                                    id=highlight_checklist,
                                                    labelClassName='form-check nested-form',  # style dcc as Bootstrap and add nested hover
                                                    inputClassName='form-check-input'  # style dcc as Bootstrap
                                                ),
                                                id=highlight_collapse,
                                            )
                                        ],
                                    ),
                                    'value': 'highlight'
                                },
                                # indicators
                                {
                                    'label': html.Span(
                                        [
                                            html.Span(
                                                [
                                                    html.I(className='fas fa-chart-bar me-1'),
                                                    'Indicators overview',
                                                ],
                                                className='font-size-lg'
                                            ),
                                            dbc.Collapse(
                                                # option for each possible indicator
                                                # TODO pull this information from somewhere
                                                dcc.Checklist(
                                                    options=[],
                                                    value=[],  # default options
                                                    id=indicator_checklist,
                                                    labelClassName='form-check nested-form',  # style dcc as Bootstrap and add nested hover
                                                    inputClassName='form-check-input'  # style dcc as Bootstrap
                                                ),
                                                id=indicator_collapse,
                                            )
                                        ]
                                    ),
                                    'value': 'indicators'
                                }
                            ],
                            value=['text', 'highlight', 'indicators', 'metrics'],
                            id=checklist,
                            labelClassName='form-check',  # style dcc as Bootstrap
                            inputClassName='form-check-input'  # style dcc as Bootstrap
                        ),
                    ],
                    title='Student Card Options',
                    class_name='rounded-bottom'  # bootstrap round bottom corners
                ),
            ],
            # make both items visible from the start
            active_item=['item-1', 'item-3'],
            always_open=True,  # keep accordionitems open when click on others
            flush=True,  # styles to take up width
            class_name='border-top'  # bootstrap border on top
        ),
    ],
    id=offcanvas,
    # TODO eventually we want sticky-top in the classname however
    # if the screen height is short enough we won't be able to
    # see all options available.
    # need to add overflow to the last accordian item

    # bootstrap add right (e)nd and (b)ottom margins
    class_name='me-2 mb-2'
)

# disbale document date/time options
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='disable_doc_src_datetime'),
    Output(doc_src_date, 'disabled'),
    Output(doc_src_timestamp, 'disabled'),
    Input(doc_src, 'value')
)

# change the icon and label of the sort button
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='change_sort_direction_icon'),
    Output(sort_icon, 'className'),
    Output(sort_label, 'children'),
    Input(sort_toggle, 'value'),
    Input(sort_by_checklist, 'value')
)

# reset the sort
clientside_callback(
    ClientsideFunction(namespace='clientside', function_name='reset_sort_options'),
    Output(sort_by_checklist, 'value'),
    Input(sort_reset, 'n_clicks')
)

# settings checklist toggle
# if the option is selected, show its sub-options
#
# e.g. if metrics is chosen, show the options for time_on_task, adjectives, adverbs, etc.
#       otherwise, don't shown those items

toggle_checklist_visibility = '''
    function(values, students) {{
        if (values.includes('{id}')) {{
            return true;
        }}
        return false;
    }}
    '''
clientside_callback(
    toggle_checklist_visibility.format(id='indicators'),
    Output(indicator_collapse, 'is_open'),
    Input(checklist, 'value')
)
clientside_callback(
    toggle_checklist_visibility.format(id='metrics'),
    Output(metric_collapse, 'is_open'),
    Input(checklist, 'value')
)
# clientside_callback(
#     toggle_checklist_visibility.format(id='text'),
#     Output(text_collapse, 'is_open'),
#     Input(checklist, 'value')
# )
clientside_callback(
    toggle_checklist_visibility.format(id='highlight'),
    Output(highlight_collapse, 'is_open'),
    Input(checklist, 'value')
)
