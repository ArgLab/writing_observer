'''
This file defines the hierarchical graphs
'''
from dash import html, dcc, clientside_callback, ClientsideFunction, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from . import colors

prefix = 'common-error-hierarchical'
order_toggle = f'{prefix}-hierarchy-order-toggle'
data_store = f'{prefix}-store'

sunburst = f'{prefix}-sunburst'
sunburst_figure = go.Figure(go.Sunburst(
    ids=[],
    labels=[],
    parents=[],
    values=[],
    marker_colors=[],
    branchvalues='total'
))
sunburst_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0))

treemap = f'{prefix}-treemap'
treemap_figure = go.Figure(go.Treemap(
    ids=[],
    labels=[],
    parents=[],
    values=[],
    marker_colors=[],
    branchvalues='total'
))
treemap_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0))

icicle = f'{prefix}-icicle'
icicle_figure = go.Figure(go.Icicle(
    ids=[],
    labels=[],
    parents=[],
    values=[],
    marker_colors=[],
    branchvalues='total'
))
icicle_figure.update_layout(margin=dict(t=5, l=0, r=0, b=5))

layout = html.Div([
    html.H4('Hierarchical Information'),
    dbc.RadioItems(
        options=[
            {'label': 'Category - Student - Subcategory', 'value': 'stud-sub'},
            {'label': 'Category - Subcategory - Student', 'value': 'sub-stud'}
        ],
        value='stud-sub',
        id=order_toggle
    ),
    dbc.Tabs([
        dbc.Tab(dcc.Graph(id=sunburst, figure=sunburst_figure), label='Sunburst'),
        dbc.Tab(dcc.Graph(id=treemap, figure=treemap_figure), label='Treemap'),
        dbc.Tab(dcc.Graph(id=icicle, figure=icicle_figure), label='Icicle')
    ]),
    dcc.Store(id=data_store, data=[])
], id=prefix)

clientside_callback(
    ClientsideFunction(namespace='hierarchical_common_errors', function_name='populate_hierarchical_charts'),
    Output(sunburst, 'extendData'),
    Output(treemap, 'extendData'),
    Output(icicle, 'extendData'),
    Input(data_store, 'data'),
    Input(order_toggle, 'value')
)
