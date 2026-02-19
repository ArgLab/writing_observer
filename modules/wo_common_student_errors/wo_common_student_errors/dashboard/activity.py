'''
This file defines the components for the student activity information
'''
import dash_bootstrap_components as dbc


prefix = 'student-activity'
inactive = f'{prefix}-inactive'
active = f'{prefix}-active'


def create_activity_card(id, title):
    '''
    Each activity (inactive/active) should look have the same look
    '''
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader(title),
            dbc.CardBody(dbc.Row(id=id, class_name='g-1 student-activity-status-row'))
        ]),
        sm=6
    )


inactive_card = create_activity_card(inactive, 'Inactive')
active_card = create_activity_card(active, 'Active')
layout = dbc.Row([
    inactive_card,
    active_card
], class_name='g-1')
