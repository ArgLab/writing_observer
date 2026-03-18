'''
This file creates the aggregate items for the category/subcategory graph.
Clicking on either of these continues to filter the aggregated data.
'''
from dash import clientside_callback, ClientsideFunction, Output, Input, State, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from . import colors

prefix = 'common-error-aggregate'
category_bar_chart = f'{prefix}-category-barchart'
subcategory_bar_chart = f'{prefix}-subcategory-barchart'
feedback_list = f'{prefix}-feedback-list'
student_list = f'{prefix}-student-list'
data_store = f'{prefix}-store'

category_figure = go.Figure(go.Bar(x=[], y=[], marker_color=[]))
category_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0), clickmode='event+select')
category_figure.update_yaxes(type='linear', rangemode='tozero')

subcategory_figure = go.Figure(go.Bar(x=[], y=[], marker_color=[]))
subcategory_figure.update_layout(margin=dict(t=0, l=0, r=0, b=0), clickmode='event+select')
subcategory_figure.update_yaxes(type='linear', rangemode='tozero')

feedback = dbc.Card([
    dbc.CardHeader('Feedback Items'),
    dbc.CardBody(html.Ol([], id=feedback_list))
])

students = dbc.Card([
    dbc.CardHeader('Students'),
    dbc.CardBody(html.Ol([], id=student_list))
])

layout = html.Div([
    html.H4('Aggregate Information'),
    dbc.Row([
        dbc.Col(dcc.Graph(id=category_bar_chart, figure=category_figure), sm=6),
        dbc.Col(dcc.Graph(id=subcategory_bar_chart, figure=subcategory_figure), sm=6),
        dbc.Col(feedback, sm=6),
        dbc.Col(students, sm=6)
    ], class_name='g-0'),
    dcc.Store(id=data_store, data=[])
], id=prefix)

clientside_callback(
    ClientsideFunction(namespace='aggregate_common_errors', function_name='update_category_graph'),
    Output(category_bar_chart, 'extendData'),
    Output(subcategory_bar_chart, 'extendData'),
    Output(feedback_list, 'children'),
    Output(student_list, 'children'),
    Input(data_store, 'data'),
    Input(category_bar_chart, 'selectedData'),
    Input(subcategory_bar_chart, 'selectedData')
)
