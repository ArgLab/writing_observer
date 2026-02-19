import inspect
import os.path

import js2py

import dash.development
from dash import Dash, html
import dash_bootstrap_components as dbc

import lo_dash_react_components

debug_test_data = {
}


def test_data(component):
    """
    This function is used to retrieve test data for a specific
    component.

    It first checks if the component exists in the test data
    dictionary. This is mostly for use during development. If it does,
    it returns the corresponding test data. If not, it checks if a
    test data file exists for the component. If it does, it reads the
    file and evaluates it using js2py, and returns the 'testData'
    object defined in the file. If neither the component or the test
    data file exists, it returns an empty dictionary..

    :param component: The name of the component to get test data for.
    :type component: str
    :return: The test data for the specified component, or None if it doesn't exist.
    :rtype: dict or None
    """
    if component in debug_test_data:
        return debug_test_data[component]
    path = f"src/lib/components/{component}.testdata.js"

    if os.path.exists(path):
        with open(path) as f:
            text = f.read()
        context = js2py.EvalJs({})
        # js2py is ES5.1, which doesn't support export
        context.execute(text.replace("export default ", ""))
        component_data = context.testData
        return component_data.to_dict()
    return {}


def get_subclasses(module, base_class):
    """Returns a list of all items in a module that are subclasses of `base_class`."""
    return [name for name, obj in inspect.getmembers(module)
            if inspect.isclass(obj) and issubclass(obj, base_class)]


component_list = get_subclasses(lo_dash_react_components, dash.development.base_component.Component)
link_items = [html.Li(html.A(href=f"/components/{component}", children=component)) for component in component_list]
ul = html.Ul(children=link_items)

app = Dash(__name__, use_pages=True, pages_folder="", external_stylesheets=[dbc.themes.BOOTSTRAP])

for component in component_list:
    urlpath = f"/components/{component}"
    component_class = getattr(lo_dash_react_components, component)
    parameters = test_data(component)
    layout = component_class(**parameters)
    dash.register_page(component, path=urlpath, layout=layout)

app.layout = html.Div([
    dash.page_container,
    html.Hr(),
    html.Div(id='output'),
    html.H1("Components"),
    ul
])


if __name__ == '__main__':
    app.run_server(debug=True)
