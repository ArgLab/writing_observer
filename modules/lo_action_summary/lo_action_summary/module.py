'''
Learning Observer Action Summary

This module allows users to view a student's history of events for a specific reducer context.
'''
import learning_observer.downloads as d
import learning_observer.communication_protocol.query as q
from learning_observer.dash_integration import thirdparty_url, static_url
from learning_observer.stream_analytics.helpers import KeyField, Scope

import lo_action_summary.reducers
import lo_action_summary.dash_dashboard

# Name for the module
NAME = 'Learning Observer Action Summary'

course_roster = q.call('learning_observer.courseroster')

EXECUTION_DAG = {
    'execution_dag': {
        'roster': course_roster(runtime=q.parameter('runtime'), course_id=q.parameter('course_id', required=True)),
        'single_action_summary': q.select(q.keys('lo_action_summary.student_event_history', STUDENTS=q.parameter('student_id', required=True), STUDENTS_path='user_id'), fields=q.SelectFields.All),
    },
    'exports': {
        'roster': {
            'returns': 'roster',
            'parameters': ['course_id'],
        },
        'action_summary': {
            'returns': 'single_action_summary',
            'parameters': ['course_id', 'student_id'],
        }
    }
}

# TODO we want the event history for both SBA and DA
# reducer_context = 'org.ets.sba'
reducer_context = 'org.ets.da'
REDUCERS = [
    {
        'context': reducer_context,
        'scope': Scope([KeyField.STUDENT]),
        'function': lo_action_summary.reducers.student_event_history,
        'default': {'events': []}
    }
]

'''
Define pages created with Dash.
'''
DASH_PAGES = [
    {
        'MODULE': lo_action_summary.dash_dashboard,
        'LAYOUT': lo_action_summary.dash_dashboard.layout,
        'ASSETS': 'assets',
        'TITLE': 'Learning Observer Action Summary',
        'DESCRIPTION': "This module allows users to view a student's history of events for a specific reducer context.",
        'SUBPATH': 'lo-action-summary',
        'CSS': [
            thirdparty_url('css/fontawesome_all.css')
        ],
        'SCRIPTS': [
            static_url('liblo.js')
        ]
    }
]

'''
Additional files we want included that come from a third part.
'''
THIRD_PARTY = {
    'css/fontawesome_all.css': d.FONTAWESOME_CSS,
    'webfonts/fa-solid-900.woff2': d.FONTAWESOME_WOFF2,
    'webfonts/fa-solid-900.ttf': d.FONTAWESOME_TTF
}

'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': '/lo_action_summary/dash/lo-action-summary',
    'icon': {
        'type': 'fas',
        'icon': 'fa-play-circle'
    }
}]
