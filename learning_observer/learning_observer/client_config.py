'''
Client Configuration
====================

This module creates a client-side configuration. This might include
things such as:

- Relative URL paths
- Per-server UX tweaks
- Etc.

For now, this is managed in static files. We might move into a
database eventually. It will always be visible at a standard URL,
probably `/config.json`
'''

import aiohttp


client_config = {
    # Tell the client there's a live server
    #
    # For debugging / devel, it's helpful to be able to mock the API
    # with static files. Those won't do things like web sockets.
    "mode": "server",
    "modules": {}     # Per-module config
}


async def client_config_handler(request):
    '''
    Return a configuration JSON response to the client. This:
    - Tells the client this is running from a live server
    - Includes any system-specific configuration
    '''
    return aiohttp.web.json_response(client_config)
