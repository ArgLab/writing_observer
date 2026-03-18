'''
This file handles the individual student view on the right side
of the screen when a student is selected.
'''
from dash import html, dcc
import dash_bootstrap_components as dbc
import lo_dash_react_components as lodrc
import plotly.graph_objects as go
import pandas as pd

from . import colors

prefix = 'individual-student-errors'
student = f'{prefix}-student'
text = f'{prefix}-text'
errors = f'{prefix}-errors'

error_sunburst = f'{prefix}-errors-sunburst'
error_sunburst_figure = go.Figure(go.Sunburst(
    ids=[],
    labels=[],
    parents=[],
    values=[],
    marker=dict(
        colors=pd.Series(colors.colors)
    ),
    branchvalues='total'
))
error_sunburst_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0))

layout = html.Div([
    html.Div([
        html.H4(id=student),
        lodrc.WOAnnotatedText(id=text),
        dcc.Graph(id=error_sunburst, figure=error_sunburst_figure),
    ], className='loaded'),
    html.Div(dbc.Spinner(), className='loading')
], id=prefix)
