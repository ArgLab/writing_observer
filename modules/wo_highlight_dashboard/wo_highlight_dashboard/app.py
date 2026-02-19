from aiohttp import web
from aiohttp_wsgi import WSGIHandler
import dash_bootstrap_components as dbc

import learning_observer.dash_wrapper as dash
import writing_dashboard.dashboard.layout

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.MINTY,  # bootstrap styling
        dbc.icons.FONT_AWESOME,  # font awesome icons
        'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.6/dbc.min.css',  # styling dcc components as Bootstrap
    ],
    title='Learning Observer',
    suppress_callback_exceptions=True
)

app.layout = writing_dashboard.dashboard.layout.layout

wsgi_handler = WSGIHandler(app.server)
webapp = web.Application()
webapp.router.add_route("*", "/{path_info:.*}", wsgi_handler)
web.run_app(webapp)
