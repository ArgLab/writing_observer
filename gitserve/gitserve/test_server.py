'''
Minimal test server. Serves up a git repo passed on the command line.

Usage:

>>> python test_server /home/ubuntu/repo/
'''

import sys

import asyncio
import aiohttp.web

import gitserve.aio_gitserve

if len(sys.argv) == 1:
    print("Usage:")
    print("  python test_server.py /home/ubuntu/repo")
    sys.exit(-1)

gitrepo = sys.argv[1]
if len(sys.argv) > 2:
    PREFIX = sys.argv[2]
else:
    PREFIX = ""

if "--working" in sys.argv:
    WORKING = True
else:
    WORKING = False

loop = asyncio.get_event_loop()
app = aiohttp.web.Application(loop=loop)
app.router.add_get(
    '/',
    lambda request: aiohttp.web.Response(text='Test / example server!')
)
app.router.add_get(
    r'/browse/{branch:[^{}/]+}/{filename:[^{}]+}',
    gitserve.aio_gitserve.git_handler_wrapper(
        gitrepo,
        prefix=PREFIX,
        cookie_prefix="content_",
        working_tree_dev=WORKING
    )
)
aiohttp.web.run_app(app, host='127.0.0.1', port=8080)
