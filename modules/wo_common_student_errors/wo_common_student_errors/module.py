import learning_observer.downloads as d
from learning_observer.dash_integration import thirdparty_url, static_url

import wo_common_student_errors.dashboard.layout


NAME = "Writing Observer - Common Student Errors"

DASH_PAGES = [
    {
        "MODULE": wo_common_student_errors.dashboard.layout,
        "LAYOUT": wo_common_student_errors.dashboard.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Common student errors",
        "DESCRIPTION": "Dashboard for viewing errors across a classroom of students.",
        "SUBPATH": "common-errors",
        "CSS": [
            thirdparty_url("css/bootstrap.min.css"),
            thirdparty_url("css/fontawesome_all.css")
        ],
        "SCRIPTS": [
            static_url("liblo.js")
        ]
    }
]

THIRD_PARTY = {
    "css/bootstrap.min.css": d.BOOTSTRAP_MIN_CSS,
    "css/fontawesome_all.css": d.FONTAWESOME_CSS,
    "webfonts/fa-solid-900.woff2": d.FONTAWESOME_WOFF2,
    "webfonts/fa-solid-900.ttf": d.FONTAWESOME_TTF
}


COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_common_student_errors/dash/common-errors",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]
