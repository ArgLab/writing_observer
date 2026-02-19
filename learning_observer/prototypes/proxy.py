'''
This is a PROTOTYPE proxy request handler. It is designed to be used with
aiohttp. The goal is to be able to connnect to Jupyter Notebook servers, and
relay the requests to them.

This currently works 90% with Jupyter Notebook servers running on localhost,
but runs into issues with API requests. That's probably some CSRF issue, or
similar.

We could also try to monitor at the ZMQ level, and relay the requests to
the notebook server.
'''

from ast import Not
import asyncio
from datetime import datetime
import re
import multidict

from aiohttp import web
import aiohttp

BASE_URL = "http://localhost:8889"


async def proxy(
    base_url=BASE_URL,
    source_port=8080,
    target_port=8889,
):
    async def proxy_handler(request):
        '''
        Relay HTTP requests from 8080 to 8889

        This is the main handler for the proxy.
        '''
        print(request)
        target_url = base_url + request.path

        cookies = request.cookies
        headers = multidict.CIMultiDict(request.headers)
        if "referer" in headers:
            old_referer = headers['referer']
            headers.popall("referer")
            headers['referer'] = old_referer.replace(
                str(source_port), str(target_port)
            )
        async with aiohttp.ClientSession() as client:
            if request.method == "POST":
                post_data = await request.post()
                print("PD", post_data)
                resp = await client.post(
                    target_url,
                    data=post_data,
                    cookies=cookies,
                    headers=headers
                )
            elif request.method == "GET":
                resp = await client.get(
                    target_url,
                    cookies=cookies,
                    headers=headers
                )
            elif request.method == "PUT":
                put_data = await request.post()
                resp = await client.put(
                    target_url,
                    data=put_data,
                    cookies=cookies,
                    headers=headers
                )
            else:
                raise NotImplementedError(
                    "Unsupported method: " + request.method
                )
            data = await resp.read()

            if resp.status == 200:
                data = await resp.read()
                return web.Response(
                    body=data,
                    status=resp.status,
                    headers=resp.headers
                )
            elif resp.status == 301:
                return web.HTTPFound(resp.headers['Location'])
            elif resp.status == 302:
                return web.HTTPFound(resp.headers['Location'])
            elif resp.status == 304:
                return web.Response(status=resp.status)
            elif resp.status == 401:
                return web.HTTPUnauthorized()
            elif resp.status == 404:
                return web.HTTPNotFound()
            elif resp.status == 403:
                print(resp)
                print(data)
                return web.HTTPForbidden()
            else:
                print("Error:", resp.status)
                return web.HTTPInternalServerError()
    return proxy_handler


async def init_app():
    '''
    This is the main entry point for testing the proxy.

    It creates a proxy server and runs it in a loop. This is useful for
    testing the proxy without the full system.
    '''
    app = web.Application()
    p = await proxy()
    app.router.add_get('/{path:.*}', p)
    app.router.add_post('/{path:.*}', p)
    app.router.add_put('/{path:.*}', p)
    return app


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app)
