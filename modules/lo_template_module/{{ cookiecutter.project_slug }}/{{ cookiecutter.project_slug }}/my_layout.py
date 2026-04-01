from dash import html, dcc
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc

def my_layout(_websocket, _output):
    '''
    This is the layout for the static part of your dashboard which
    is loaded when the page first loads.

    * The data would be populated in a div with id _output.
    * We pass the _websocket so we can render a component letting us know when things updated
    '''
    page_layout = html.Div(children=[
        html.H1(children='{{ cookiecutter.project_name }}'),
        dbc.InputGroup([
            dbc.InputGroupText(lodrc.LOConnectionAIO(aio_id=_websocket)),
            lodrc.ProfileSidebarAIO(class_name='rounded-0 rounded-end', color='secondary'),
        ]),
        html.H2('Output from reducers'),
        html.Div(id=_output)
    ])
    return page_layout


def my_data_layout(data):
    '''
    This is the layout for the changing part of your dashboard
    populated from the data.
    '''
    if not data or len(data.get('students', {})) == 0:
        return 'No students'
    output = [html.Div([
        k,
        html.Span(f' - {v["count"]} events')
    ]) for k, v in data.get('students', {}).items()]
    return output
