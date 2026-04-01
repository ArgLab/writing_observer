'''
Helpful extra handlers
'''

import os
import os.path

import aiohttp
import aiohttp.web

import pathvalidate


# This should be cleaned up. Imports generally. We're mid-refactor...
from learning_observer.log_event import debug_log


def static_file_handler(filename):
    '''
    Serve a single static file
    '''
    async def handler(request):
        debug_log(request.headers)
        return aiohttp.web.FileResponse(filename)
    return handler


def json_response_handler(data):
    '''Serve data (dict-like) as a json response
    '''
    async def handler(request):
        return aiohttp.web.json_response(data)
    return handler


def redirect(new_path):
    '''
    Static, fixed redirect to a new location
    '''
    async def handler(request):
        raise aiohttp.web.HTTPFound(location=new_path)
    return handler


def static_directory_handler(basepath):
    '''
    Serve static files from a directory.

    This could be done directly by nginx on deployment.

    This is very minimal for now: No subdirectories, no gizmos,
    nothing fancy. I avoid fancy when we have user input and
    filenames. Before adding fancy, I'll want test cases of
    aggressive user input.
    '''

    def handler(request):
        '''
        We're in a closure, since we want to configure the directory
        when we set up the path.
        '''
        # Extract the filename from the request
        filename = request.match_info['filename']
        # Raise an exception if we get anything nasty
        pathvalidate.validate_filename(filename)
        # Check that the file exists
        full_pathname = os.path.join(basepath, filename)
        if not os.path.exists(full_pathname):
            raise aiohttp.web.HTTPNotFound()
        # And serve pack the file
        return aiohttp.web.FileResponse(full_pathname)
    return handler


def ajax_handler_wrapper(handler_func):
    '''
    Wrap a function which returns a JSON object to handle requests
    '''
    def handler(request):
        return aiohttp.web.json_response(handler_func())
    return handler
