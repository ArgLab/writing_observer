"""
Basic LTI grade submission demo module.

This module exposes a minimal HTML dashboard (served via the `EXTRA_VIEWS`
mechanism) that reads the active LTI session and posts an AGS score using the
existing Canvas proxy wiring. It is intended as a copy/paste example for new
integrations rather than a production UI.
"""

from . import views

NAME = "LTI Grade Demo"

EXTRA_VIEWS = [
    {
        "name": "LTI Grade Demo Dashboard",
        "suburl": "lti-grade-demo",
        "method": "GET",
        "handler": views.render_dashboard,
    },
    {
        "name": "LTI session summary",
        "suburl": "session-summary",
        "method": "GET",
        "handler": views.session_summary,
    },
    {
        "name": "Course line items",
        "suburl": "line-items",
        "method": "GET",
        "handler": views.course_line_items,
    },
    {
        "name": "Submit LTI grade",
        "suburl": "submit-score",
        "method": "POST",
        "handler": views.submit_score,
    },
]

COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/views/lo_lti_grade_demo/lti-grade-demo/",
    "icon": {
        "type": "fas",
        "icon": "fa-star"
    }
}]
