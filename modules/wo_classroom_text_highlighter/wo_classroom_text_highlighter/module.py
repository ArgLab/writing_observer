'''
Writing Observer Classroom Text Highlighter

Writing Observer dashboard for highlighting different attributes of text at the classroom level.
'''
import learning_observer.downloads as d
from learning_observer.dash_integration import thirdparty_url, static_url

import wo_classroom_text_highlighter.dash_dashboard

# Name for the module
NAME = 'Writing Observer - Classroom Text Highlighter'

'''
Define pages created with Dash.
'''
DASH_PAGES = [
    {
        'MODULE': wo_classroom_text_highlighter.dash_dashboard,
        'LAYOUT': wo_classroom_text_highlighter.dash_dashboard.layout,
        'ASSETS': 'assets',
        'TITLE': 'Writing Observer Classroom Text Highlighter',
        'DESCRIPTION': 'Writing Observer dashboard for highlighting different attributes of text at the classroom level.',
        'SUBPATH': 'wo-classroom-text-highlighter',
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
    'url': "/wo_classroom_text_highlighter/dash/wo-classroom-text-highlighter",
    "icon": {
        "type": "fas",
        "icon": "fa-highlighter"
    }
}]
