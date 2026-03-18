'''
Handle HTTP basic authentication

Curiously, the Wikipedia article is the best reference on this.

We would like to support two modes of operation:

1) Rely on nginx
2) Rely on our own password file

For now, we only support #1. We do not verify passwords, and let
our web server do it for us.

Well, technically, for now we support neither since this file is IN
DEVELOPMENT, and NOT YET WORKING.
'''
import base64
import json
import yaml
import sys

import bcrypt

import aiohttp.web

import learning_observer.settings
import learning_observer.prestartup

import learning_observer.auth

from learning_observer.log_event import debug_log


def http_basic_extract_username_password(request):
    '''
    Based on an HTTP request, return a username / password tuple

    Return `None` if missing
    '''
    auth_header = request.headers.get('Authorization', None)
    if auth_header is None:
        return None

    if not auth_header.startswith("Basic "):
        raise aiohttp.web.HTTPBadRequest("Malformed header authenticating.")
    split_header = auth_header.split(" ")
    if len(split_header) != 2:
        raise aiohttp.web.HTTPBadRequest("Malformed header authenticating.")
    decoded_header = base64.b64decode(split_header[1]).decode('utf-8')
    (username, password) = decoded_header.split(":")
    return (username, password)


def has_http_auth_headers(request):
    '''
    Check if the request has HTTP basic auth headers
    '''
    auth_header = request.headers.get('Authorization', None)
    if auth_header is not None:
        return True
    return False


def http_auth_middleware_enabled():
    '''
    Check if the authentication middleware should be enabled.

    This should ONLY be set for sites where ALL pages use HTTP
    auth. If we only use http_auth for the auth page, this should be
    disabled.

    We may rely on nginx for http auth. We do NOT want the middleware
    to accidentally receive requests with auth headers on pages which
    nginx has not secured.
    '''
    if 'http_basic' not in learning_observer.settings.settings['auth']:
        return False
    auth_basic_settings = learning_observer.settings.settings['auth']['http_basic']
    return auth_basic_settings.get("full_site_auth", False)


def http_auth_page_enabled():
    '''
    Check if the system has a dedicated HTTP basic authentication login
    page configured in the settings file. This is typically used if we
    want to work with multiple authentication schemes, including both http
    basic and other schemes. If we only use HTTP basic auth, we don't need
    this.
    '''
    # Is http basic auth enabled?
    if 'http_basic' not in learning_observer.settings.settings['auth']:
        return False
    auth_basic_settings = learning_observer.settings.settings['auth']['http_basic']
    # And is it configured with a dedicated login page?
    if not auth_basic_settings.get("login_page_enabled", False):
        return False
    return True


def http_basic_auth_verify_password(request, filename):
    '''
    Checks if a user is authorized, based on the filename of a
    password file, and a request. This is abstracted out since we'd
    like to potentially use http basic auth for authorize:

    1) Accesses to repos (e.g. for serving static content to students)
    2) Event streams
    3) Instructors

    Each of these has their own auth workflow.

    * Return the username if authorized.
    * Return `None` if unauthorized.
    '''
    if not has_http_auth_headers(request):
        return None

    (username, password) = http_basic_extract_username_password(request)
    password_data = yaml.safe_load(open(filename))

    if (data['username'] not in password_data['users']
        or not bcrypt.checkpw(
            password,
            password_data['users'][username]['password']
    )):
        raise aiohttp.web.HTTPUnauthorized(text="Invalid username / password")
    return username


def http_basic_auth(filename=None, response=lambda: None):
    '''
    Takes a password file, or `None` if authorization is handled by nginx. Returns
    a function which authorizes the user.

    This function also works as a handler if you pass a response object. E.g.

    `http_basic_auth(
       filename=None,
       response=lambda: aiohttp.web.json_response({"status": "authorized"})
    )`

    or `response=lambda: aiohttp.web.HTTPFound(location="/")`

    or similar.
    '''
    async def password_auth_handler(request):
        debug_log("Password Auth Handler")
        if filename is not None:
            # We should check this codepath before we run it....
            raise aiohttp.web.HTTPNotImplemented(body="Password file http basic unverified.")
            username = http_basic_auth_verify_password(request, filename)
        else:
            (username, password) = http_basic_extract_username_password(request)

        # TODO: We should sanitize the username.
        # That's a bit of paranoia, but just in case something goes very wrong elsewhere...
        debug_log("Authorizing")
        await learning_observer.auth.utils.update_session_user_info(
            request, {
                'user_id': "httpauth-" + username,
                'email': "",
                'name': "",
                'family_name': "",
                'picture': "",
                'authorized': True,
                # TODO this ought to pull from somewhere else; however, I'm not familiar
                # how to test the http_basic code, so I'm setting this as student for now
                'role': learning_observer.auth.ROLES.STUDENT
            }
        )
        # This is usually ignored, but just in case...
        return response()
    return password_auth_handler


@learning_observer.prestartup.register_startup_check
def http_basic_startup_check():
    if http_auth_page_enabled() and http_auth_middleware_enabled():
        raise learning_observer.prestartup.StartupCheck(
            "Your HTTP Basic authentication is misconfigured.\n"
            + "\n"
            + "You want EITHER auth on every page, OR a login page,\n"
            + "not both. Having both setting may be a security risk.\n"
            + "Please fix this."
        )

    if (
        'http_basic' in learning_observer.settings.settings['auth']
        and learning_observer.settings.settings['auth']['http_basic'].get("delegate_nginx_auth", False)
        and learning_observer.settings.settings['auth']['http_basic'].get("password_file", False)
    ):
        raise learning_observer.prestartup.StartupCheck(
            "Your HTTP Basic authentication is misconfigured.\n"
            + "\n"
            + "You should EITHER rely on nginx for password authentication OR Learning Observer,"
            + "not both."
        )
