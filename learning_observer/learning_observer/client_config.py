'''
Client Configuration
====================

This module creates a client-side configuration. This might include
things such as:

- Relative URL paths
- Per-server UX tweaks
- Etc.
'''

import aiohttp

import learning_observer.settings
import learning_observer.auth.http_basic


async def client_config_handler(request):
    '''
    Return a configuration JSON response to the client. This:
    - Tells the client this is running from a live server
    - Includes any system-specific configuration

    For debugging / devel, it's helpful to be able to mock the API
    with static files. Those won't do things like web sockets. In that
    case, we can host this client-side configuration on a local
    server as a static file, with `mode` set to `static`.
    '''
    client_config = {
        "mode": "server",
        "modules": {  # Per-module config
            'wobserver': {
                'hide_labels': False  # TODO: Should be loaded from config file
            }
        },
        "google_oauth": "google_oauth" in learning_observer.settings.settings['auth'],
        "password_auth": "password_file" in learning_observer.settings.settings['auth'],
        "http_basic_auth": learning_observer.auth.http_basic.http_auth_page_enabled(),
        "lti_auth": "lti" in learning_observer.settings.settings['auth'],
        "theme": learning_observer.settings.settings['theme']
    }

    return aiohttp.web.json_response(client_config)
