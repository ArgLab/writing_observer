'''
{{ cookiecutter.project_name }}

{{ cookiecutter.project_short_description }}
'''
import learning_observer.downloads as d
import learning_observer.communication_protocol.util
from learning_observer.dash_integration import thirdparty_url, static_url
from learning_observer.stream_analytics.helpers import KeyField, Scope

import {{ cookiecutter.project_slug }}.reducers
import {{ cookiecutter.project_slug }}.dash_dashboard

# Name for the module
NAME = '{{ cookiecutter.project_name }}'

'''
Define execution DAGs for this module. We provide a default DAG
for fetching information from the provided reducer. The internal
structure looks like:

`execution_dag`: defined directed acyclic graph (DAG) for querying data
    <node name>: q.select() # or some other communication protocol query
`exports`: fetchable nodes from the execution dag
    <name for export>: {
        "returns": <node name>,
        "parameters": ["list", "of", "parameters", "needed"]
    }

NOTE interfacing with the communication protocol may change,
the current flow is the first iteration. We will mark where things
ought to be improved.
'''
EXECUTION_DAG = learning_observer.communication_protocol.util.generate_base_dag_for_student_reducer('{{ cookiecutter.reducer }}', '{{ cookiecutter.project_slug }}')

'''
Add reducers to the module.

`context`: TODO
`scope`: the granularity of event (by student, by student + document, etc)
`function`: the reducer function to run
`default` (optional): initial value to start with
'''
REDUCERS = [
    {
        'context': 'org.mitros.writing_analytics',
        # TODO scope is defined as a decorator on the function, why is
        # is also defined here?
        'scope': Scope([KeyField.STUDENT]),
        'function': {{ cookiecutter.project_slug }}.reducers.{{ cookiecutter.reducer }},
        'default': {'count': 0}
    }
]

'''
Define pages created with Dash.
'''
DASH_PAGES = [
    {
        'MODULE': {{ cookiecutter.project_slug }}.dash_dashboard,
        'LAYOUT': {{ cookiecutter.project_slug }}.dash_dashboard.layout,
        'ASSETS': 'assets',
        'TITLE': '{{ cookiecutter.project_name }}',
        'DESCRIPTION': '{{ cookiecutter.project_short_description }}',
        'SUBPATH': '{{ cookiecutter.project_hyphenated }}',
        'CSS': [
            thirdparty_url("css/fontawesome_all.css")
        ],
        'SCRIPTS': [
            static_url("liblo.js")
        ]
    }
]

'''
Additional files we want included that come from a third part.
'''
THIRD_PARTY = {
    "css/fontawesome_all.css": d.FONTAWESOME_CSS,
    "webfonts/fa-solid-900.woff2": d.FONTAWESOME_WOFF2,
    "webfonts/fa-solid-900.ttf": d.FONTAWESOME_TTF
}

'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/{{ cookiecutter.project_slug }}/dash/{{ cookiecutter.project_hyphenated }}",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]
