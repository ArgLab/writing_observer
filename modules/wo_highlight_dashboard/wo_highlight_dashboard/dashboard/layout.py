'''
Define layout for student dashboard view
'''
# TODO this module no longer works properly since switching
# the communication protocol to use an async generator.
# Additionally, this module has been re-written as `wo_classroom_text_highlighter`
error = f'The module WO Highlight Dashboard is not compatible with the communication protocol api.\n'\
        'Please uninstall this module with `pip uninstall wo-highlight-dashboard`.'
raise RuntimeError(error)
# package imports
import learning_observer.dash_wrapper as dash
import dash_bootstrap_components as dbc

# local imports
from .students import student_dashboard_view


# passing empty parameters will automatigically be used as query strings
# see: https://dash.plotly.com/urls#query-strings
def layout(course_id=None, assignment_id=None):
    """
    Returns the layout of the student dashboard view wrapped in a Spinner component.

    Args:
    - course_id (str or None): The ID of the course to display in the dashboard. Defaults to None.
    - assignment_id (str or None): The ID of the assignment to display in the dashboard. Defaults to None.

    Returns:
    - A Dash layout containing the student dashboard view wrapped in a Spinner component.
    """
    layout = dbc.Spinner([
        dash.html.H2('Prototype: Work in Progress'),
        dash.html.P(
            'This dashboard is a prototype displaying various natural language processing (NLP) features. '
            'The NLP features include metrics and the ability to highlight specific attributes of the text. '
            'The dashboard is subject to change based on ongoing feedback from teachers.'
        ),
        student_dashboard_view(course_id, assignment_id),
    ], color='primary')
    return layout
