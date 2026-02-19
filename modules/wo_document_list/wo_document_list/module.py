import learning_observer.downloads as d
from learning_observer.dash_integration import thirdparty_url, static_url

import wo_document_list.dashboard.layout


NAME = "Writing Observer - Document List"

DASH_PAGES = [
    {
        "MODULE": wo_document_list.dashboard.layout,
        "LAYOUT": wo_document_list.dashboard.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Student Document List",
        "DESCRIPTION": "Dashboard for viewing documents from various sources for each student.",
        "SUBPATH": "document-list",
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
    'url': "/wo_document_list/dash/document-list",
    "icon": {
        "type": "fas",
        "icon": "fa-pen-nib"
    }
}]
