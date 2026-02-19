# Dashboards

We can create custom dashboards for the system.

## Dash

Dash is a package for writing and serving web applications directly in Python. In Dash, there are 2 primary items, 1) page components such as headers, divs, spans, etc. and 2) callbacks.

### Getting Started with Dash

Page components can be set up similar to other `html` layouts, like so

```python
from dash import html

layout = html.Div([
    html.H1(children='This is a header'),
    html.Div(id='A'),
    html.Div(id='B'),
    html.Input(id='input')
])
# html version
# <div>
#     <h1>This is a header</h1>
#     <div id="A"/>
#     <input id="input"/>
# </div>
```

Adding callbacks can introduce interactivity to the dashboard. Dash listens for the value of any `Input` item to change, then runs code and updates the value of the `Output` components. The updated `Output` components could be the `Input` trigger for other callbacks.

```python
from dash import callback, Output, Input

@callback(
    Output('A', 'children'),
    Input('input', 'value')
)
def update_output_children(value):
    '''This callback will trigger whenever the contents of `input`'s `value`
    property changes. It will update the `children` property of `A`.
    '''
    return f'The callback value is: {value}'
```

Callbacks are handled on the server, since we are running Python code. This creates an increase in the network and server resources. Instead, we can use `clientside_callbacks` to run Javascript code on the client's browser.

```python
from dash import clientside_callback, ClientsideFunction, Output, Input

# note this is no longer a decorator, Dash handles adding this code
# to the pages it serves
clientside_callback(
    ClientsideFunction(namespace='my_module', function_name='updateOutputChildren')
    Output('B', 'children'),
    Input('input', 'value')
)
```

```javascript
// `my_module/assets/scripts.js`

// make sure `dash_clientside` is defined first
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

// create a dictionary of functions
window.dash_clientside.my_module = {
    updateOutputChildren: function(value) {
        return `The callback value is: ${value}`
    }
}
```

### Dash in the Learning Observer

The `lo_dash_react_components` offers a variety of components (written in React, ported to Python). This includes a handy websocket component for connecting directly to the communication protocol. We can build components based on the information we receive from the communcation protocol. The protocol may eventually offer partial updates in the future, we so any time we get a new message, we should update a stored object. This stored object should be used to build the components.

```python
from dash import html, dcc, callback, clientside_callback, ClientsideFunction, Output, Input
import lo_dash_react_components as lodrc

layout = html.Div([
    lodrc.LOConnectionStatusAIO(aio_id=_websocket),
    dcc.Store(id=_websocket_storage),
    html.H2('Output from reducers'),
    html.Div(id=_output)
])

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='sendToLOConnection'),
    Output(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'send'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'state'),  # used for initial setup
    Input('_pages_location', 'hash')
)

clientside_callback(
    ClientsideFunction(namespace=_namespace, function_name='receiveWSMessage'),
    Output(_websocket_storage, 'data'),
    Input(lodrc.LOConnectionStatusAIO.ids.websocket(_websocket), 'message'),
    prevent_initial_call=True
)

@callback(
    Output(_output, 'children'),
    Input(_websocket_storage, 'data'),
)
def populate_output(data):
    if not data:
        return 'No students'
    output = [html.Div([
        lodrc.LONameTag(
            profile=s['profile'], className='d-inline-block student-name-tag',
            includeName=True, id=f'{s["user_id"]}-name-tag'
        ),
        html.Span(f' - {s["count"]} events')
    ]) for s in data]
    return output
```

And here are the relevant Javascript functions:

```javascript
window.dash_clientside.learning_observer_template = {
  sendToLOConnection: async function (wsReadyState, urlHash) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update
    }
    if (wsReadyState.readyState === 1) {
      // decode url parameters from hash
      if (urlHash.length === 0) { return window.dash_clientside.no_update }
      const decodedParams = decode_string_dict(urlHash.slice(1))
      if (!decodedParams.course_id) { return window.dash_clientside.no_update }
      // send our request to LO
      const outgoingMessage = {
        learning_observer_template_query: {
          execution_dag: 'learning_observer_template',
          target_exports: ['student_event_counter_export'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  receiveWSMessage: async function (incomingMessage) {
    // parse incoming message
    const messageData = JSON.parse(incomingMessage.data).learning_observer_template_query.student_event_counter_join_roster || [];
    if (messageData.error !== undefined) {
      console.error('Error received from server', messageData.error);
      return [];
    }
    return messageData;
  }
}
```

The websocket helper always reads its connection details from the page
hash. Without a hash (or without a `course_id` entry in the decoded
parameters) the client returns `no_update`, meaning the dashboard never
sends a query to the communication protocol. When you add links to a
dashboard, ensure they preserve whatever hash parameters the module
expects—typically at least `course_id` and sometimes other filter values.

To add a dashboard to a module, add the following to the module's `module.py` file

```python
# module.py
# ...other definitions
DASH_PAGES = [
    {
        'MODULE': module.path.dash_dashboard,
        'LAYOUT': module.path.dash_dashboard.layout,
        'ASSETS': 'assets',     # define where to find addtional js, css files are
        'TITLE': 'My dashboard title',
        'DESCRIPTION': 'My dashboard description.',
        'SUBPATH': 'my-dashboard-subpath',
        # additional js, css files we want to included
        'CSS': [
            thirdparty_url("css/fontawesome_all.css")
        ],
        'SCRIPTS': [
            static_url("liblo.js")
        ]
    }
]
```

## NextJS

NextJS is web framework for building React-based web applications along with additional server-side functionality.

### Getting Started with NextJS

Follow the [Getting Started Guide](https://nextjs.org/docs/app/getting-started) in the official NextJS documentation.

### Serving NextJS in the Learning Observer

Before NextJS application can be built and added to the system, a few configuration changes need to be made. The built application will not access the server-side code. Any server-side API endpoints need to be implemented in Python. The code that calls these endpoints will need to be updated to point to the correct path.

Additionally, we need to add a `basePath` to our `next.config.js` file. When building the application, this prefixes all paths with the defined base path. This allows links to function appropriately while being served from Learning Observer. Using a base path is especially important when multiple modules serve NextJS dashboards, because it prevents routing conflicts by ensuring that each module's assets are namespaced by the module name.

```js
const nextConfig = {
  // ... the rest of your config
  basePath: '/_next/<module-name>/<built-app-name>',
  output: 'export',
}
```

With this configuration:

* Without a base path, multiple modules exporting dashboards to `/` will conflict with one another and with Learning Observer's own root path.
* With a base path, each module is served from `/_next/<module-name>/<built-app-name>/`, which avoids those conflicts by including the module name in the URL path.
* Avoid absolute paths inside the application (for example, `href="/students"`). Absolute paths ignore the configured `basePath`, which breaks routing when the dashboard is served from Learning Observer. Prefer relative links or the [`next/link`](https://nextjs.org/docs/pages/api-reference/components/link) component's `basePath`-aware helpers.

Use query parameters instead of dynamic path segments for any routing that needs to work after static export. For example, prefer `students/compare?id=123` instead of `/students/[id]/compare` so that the static export can generate the page.

During development it can be helpful to mock the data that will normally arrive via the Learning Observer websocket. A simple placeholder object keeps the dashboard usable before the websocket connection is wired up:

```js
const data = {
  students: {
    martha: {
      documents: {
        history_essay: {
          text: 'this is my history essay'
        }
      }
    }
  }
};
```

To add a NextJS project to a module:

1. Build the project with `npm run build`. The static export requires the `output: 'export'` setting shown above. A directory named `out` will be created and the built application will be placed there.
2. Copy the contents of `out` to `modules/<module_name>/<built-app-name>/`.
3. Add the path to the built application to the module's `module.py` file

    ```python
    # module.py
    # ...other definitions
    '''
    Next js dashboards
    '''
    NEXTJS_PAGES = [
        {'path': '<built-app-name>/'}
    ]
    ```

4. Install the module in editable mode with `pip install -e modules/<module_name>`.
5. Start Learning Observer with `make run` to serve the dashboard.

### Connecting to the Communication Protocol

When you are ready to connect to Learning Observer's Communication Protocol, install the `lo_event` module to gain access to the shared websocket utilities.

Installing `lo_event` makes the `LOConnectionDataManager` React hook available to your NextJS project. The hook manages websocket connection state and incoming messages so that your components can focus on rendering data.

Adding `lo_event` may surface build-time errors if your environment lacks Node polyfills. For example, some systems report `fs` being unavailable. You can instruct Webpack to ignore the `fs` module when bundling the client by extending `next.config.js`:

```js
const nextConfig = {
  // ...existing config
  webpack: (
    config,
    { buildId, dev, isServer, defaultLoaders, nextRuntime, webpack }
  ) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false, // tells Webpack to ignore fs in client bundle
    };
    return config;
  },
};

module.exports = nextConfig;
```
