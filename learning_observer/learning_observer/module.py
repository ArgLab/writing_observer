'''
Module definition file

This may be an examplar for building new modules too.
'''
import os.path

import dash_bootstrap_components as dbc

import learning_observer.dash_integration
import learning_observer.communication_protocol.explorer
import learning_observer.communication_protocol.debugger


NAME = "Learning Observer Base"

# Outgoing APIs
#
# Generically, these would usually serve JSON to dashboards written as JavaScript and
# HTML. These used to be called 'dashboards,' but we're now hosting those as static
# files.

COURSE_AGGREGATORS = {
    # "writing-observer": {
    #     "sources": [  # These are the reducers whose outputs we aggregate
    #         learning_observer.stream_analytics.writing_analysis.time_on_task,
    #         learning_observer.stream_analytics.writing_analysis.reconstruct
    #         # TODO: "roster"
    #     ],
    #     #  Then, we pass the per-student data through the cleaner, if provided.
    #     "cleaner": learning_observer.writing_observer.aggregator.sanitize_and_shrink_per_student_data,
    #     #  And we pass an array of the output of that through the aggregator
    #     "aggregator": learning_observer.writing_observer.aggregator.aggregate_course_summary_stats,
    #     "name": "This is the main Writing Observer dashboard."
    # }
}

STUDENT_AGGREGATORS = {
}

# Incoming event APIs
REDUCERS = [
]


# Required client-side JavaScript downloads
THIRD_PARTY = {
    "require.js": {       # Our recommended library loader
        "url": "https://requirejs.org/docs/release/2.3.6/comments/require.js",
        "hash": "d1e7687c1b2990966131bc25a761f03d6de83115512c9ce85d72e4b9819fb"
        "8733463fa0d93ca31e2e42ebee6e425d811e3420a788a0fc95f745aa349e3b01901"
    },
    "text.js": {          # Add-on for require to load text files
        "url": "https://raw.githubusercontent.com/requirejs/text/"
        "3f9d4c19b3a1a3c6f35650c5788cbea1db93197a/text.js",
        "hash": "fb8974f1633f261f77220329c7070ff214241ebd33a1434f2738572608efc"
        "8eb6699961734285e9500bbbd60990794883981fb113319503208822e6706bca0b8"
    },
    "r.js": {             # We should check if this is still used
        "url": "https://requirejs.org/docs/release/2.3.6/r.js",
        "hash": "52300a8371df306f45e981fd224b10cc586365d5637a19a24e710a2fa566f"
        "88450b8a3920e7af47ba7197ffefa707a179bc82a407f05c08508248e6b5084f457"
    },
    "bulma.min.css": {    # Our default stylesheet
        "url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.0/css/"
        "bulma.min.css",
        "hash": "ec7342883fdb6fbd4db80d7b44938951c3903d2132fc3e4bf7363c6e6dc52"
        "95a478c930856177ac6257c32e1d1e10a4132c6c51d194b3174dc670ab8d116b362"
    },
    "bulma-tooltip-min.css": {  # Add-on for above
        "url": "https://cdn.jsdelivr.net/npm/@creativebulma/bulma-tooltip@1.2.0/"
        "dist/bulma-tooltip.min.css",
        "hash": "fc37b25fa75664a6aa91627a7b1298a09025c136085f99ba31b1861f073a0"
        "696c4756cb156531ccf5c630154d66f3059b6b589617bd6bd711ef665079f879405"
    },
    "fontawesome.js": {   # Icons for the above
        "url": "https://use.fontawesome.com/releases/v5.3.1/js/all.js",
        "hash": "83e7b36f1545d5abe63bea9cd3505596998aea272dd05dee624b9a2c72f96"
        "62618d4bff6e51fafa25d41cb59bd97f3ebd72fd94ebd09a52c17c4c23fdca3962b"
    },
    "showdown.js": {      # Default markup library
        "url": "https://cdn.jsdelivr.net/gh/showdownjs/showdown@1.9.1/dist/showdown.js",
        "hash": "4fe14f17c2a1d0275d44e06d7e68d2b177779196c6d0c562d082eb5435eec"
        "4e710a625be524767aef3d9a1f6a5b88f912ddd71821f4a9df12ff7dd66d6fbb3c9"
    },
    "showdown.js.map": {  # Part of above
        "url": "https://cdn.jsdelivr.net/gh/showdownjs/showdown@1.9.1/dist/showdown.js.map",
        "hash": "74690aa3cea07fd075942ba9e98cf7297752994b93930acb3a1baa2d3042a"
        "62b5523d3da83177f63e6c02fe2a09c8414af9e1774dad892a303e15a86dbeb29ba"
    },
    "mustache.min.js": {  # Default templating engine
        "url": "http://cdnjs.cloudflare.com/ajax/libs/mustache.js/3.1.0/"
        "mustache.min.js",
        "hash": "e7c446dc9ac2da9396cf401774efd9bd063d25920343eaed7bee9ad878840"
        "e846d48204d62755aede6f51ae6f169dcc9455f45c1b86ba1b42980ccf8f241af25"
    },
    "d3.v5.min.js": {     # Client-side data flow
        "url": "https://d3js.org/d3.v5.min.js",
        "hash": "466fe57816d719048885357cccc91a082d8e5d3796f227f88a988bf36a5c2"
        "ceb7a4d25842f5f3c327a0151d682e648cd9623bfdcc7a18a70ac05cfd0ec434463"
    },
    "p5.js.min": {        # Mostly, for rapid prototyping of visualizations
        "url": "https://github.com/processing/p5.js/releases/download/v1.4.0/p5.min.js",
        "hash": "6e2559786ad5e22f01f112289ddd32fb7675703501306ff9f71c203146047"
        "e20bb552850b8c89e913e43e1027f292a3f13aa63ace0bdf8af24a8654f9200346c"
    }
}


# We're still figuring this out, but we'd like to support hosting static files
# from the git repo of the module.
#
# This allows us to have a Merkle-tree style record of which version is deployed
# in our log files.
STATIC_FILE_GIT_REPOS = {
    # 'writing_observer': {
    #     # Where we can grab a copy of the repo, if not already on the system
    #     'url': 'https://github.com/ArgLab/writing_observer.git',
    #     # Where the static files in the repo lie
    #     'prefix': 'learning_observer/learning_observer/static',
    #     # Branches we serve. This can either be a whitelist (e.g. which ones
    #     # are available) or a blacklist (e.g. which ones are blocked)
    #     'whitelist': ['master']
    # }
}


# We're kinda refactoring the stuff above to below
#
# The stuff above will become APIs to dashboards. The stuff below
# will register the actual dashboards.
COURSE_DASHBOARDS = [
    # {
    #     'name': "Writing Observer",
    #     'url': "/static/repos/lo_core/writing_observer/master/wobserver.html",
    #     "icon": {
    #         "type": "fas",
    #         "icon": "fa-pen-nib"
    #     }
    # }
]

STUDENT_DASHBOARDS = {
}

WSGI = [
    {
        "APP": learning_observer.dash_integration.get_app,
        "URL_PATTERNS": [
            "/{path_info:dash/test}",  # <-- Test case (to be removed)
            "/{path_info:_dash.*}",    # <-- All the infrastructure dash wants
            "/{path_info:.*/dash/.*}",   # <-- All the other modules. We can be more specific later
            "/{path_info:dash/assets/.*}"   # <-- Again, we should be more specific later
        ]
    }
]

DASH_PAGES = [
    {
        "MODULE": learning_observer.dash_integration,
        "LAYOUT": learning_observer.dash_integration.test_layout,
        "TITLE": "Test Page for Dash.",
        "DESCRIPTION": "We're just testing. Nothing to see here.",
        "SUBPATH": "test"
    },
    {
        "MODULE": learning_observer.communication_protocol.explorer,
        "LAYOUT": learning_observer.communication_protocol.explorer.layout,
        "TITLE": "Queries",
        "DESCRIPTION": "Named queries and what they do",
        "SUBPATH": "queries"
    },
    {
        "MODULE": learning_observer.communication_protocol.debugger,
        "LAYOUT": learning_observer.communication_protocol.debugger.layout,
        "TITLE": "Debugger",
        "DESCRIPTION": "Interactive debugger",
        "SUBPATH": "debugger"
    }
]
