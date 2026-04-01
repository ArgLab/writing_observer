'''
This file creates an All-In-One component for a sidebar
component that allows users to navigate throughout the platform.
The sidebar shows a Home and Logout button as well as a list
of available dashboards.
'''
from dash import html, clientside_callback, Output, Input, State, MATCH
import dash_bootstrap_components as dbc
import uuid

class ProfileSidebarAIO(html.Div):
    class ids:
        toggle_open = lambda aio_id: {
            'component': 'ProfileSidebarAIO',
            'subcomponent': 'toggle_open',
            'aio_id': aio_id
        }
        offcanvas = lambda aio_id: {
            'component': 'ProfileSidebarAIO',
            'subcomponent': 'offcanvas',
            'aio_id': aio_id
        }
        modules = lambda aio_id: {
            'component': 'ProfileSidebarAIO',
            'subcomponent': 'module_list',
            'aio_id': aio_id
        }

    ids = ids

    def __init__(self, aio_id=None, class_name='', color='primary'):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        component = [
            dbc.Button(html.I(className='fas fa-user'), id=self.ids.toggle_open(aio_id), color=color, class_name=class_name),
            dbc.Offcanvas([
                dbc.Button([html.I(className='fas fa-home me-1'), 'Home'], href='/', external_link=True),
                html.H4('Modules'),
                html.Ul(id=self.ids.modules(aio_id)),
                dbc.Button([html.I(className='fas fa-right-from-bracket me-1'), 'Logout'], color='danger', href='/auth/logout', external_link=True),
            ], title='Profile', id=self.ids.offcanvas(aio_id), placement='end')
        ]
        super().__init__(component)

    # Toggle sidebar
    clientside_callback(
        '''function (clicks, isOpen) {
            if (clicks > 0) { return !isOpen; }
            return isOpen;
        }
        ''',
        Output(ids.offcanvas(MATCH), 'is_open'),
        Input(ids.toggle_open(MATCH), 'n_clicks'),
        State(ids.offcanvas(MATCH), 'is_open')
    )

    # Update available dashboard items
    clientside_callback(
        # TODO include the course_id in these - will need to parse it out of the current string
        '''async function (empty) {
            const response = await fetch(`${window.location.protocol}//${window.location.hostname}:${window.location.port}/webapi/course_dashboards`);

            const modules = await response.json();
            const items = modules.map((x) => {
                const link = {
                    namespace: 'dash_html_components',
                    type: 'A',
                    props: { children: x.name, href: x.url + window.location.hash }
                }
                return {
                    namespace: 'dash_html_components',
                    type: 'Li',
                    props: { children: link }
                }
            })
            return items;
        }
        ''',
        Output(ids.modules(MATCH), 'children'),
        Input(ids.modules(MATCH), 'className'),
    )
