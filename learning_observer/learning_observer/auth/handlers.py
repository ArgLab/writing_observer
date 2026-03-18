'''
This file should contain handlers and all the other aio_http stuff for auth/auth.

We should give it a better name, since it also contains middlewares
'''

import base64
import json
import random

import aiohttp
import aiohttp.web
import aiohttp_session

import learning_observer.auth.utils
import learning_observer.auth.http_basic
import learning_observer.constants as constants
import learning_observer.settings

import learning_observer.graphics_helpers

import names


async def logout_handler(request):
    """
    Handles sign out. This is generic - does not depend on which
    log-in method is used (password, social, etc.)
    """
    session = await learning_observer.auth.utils.logout(request)
    return aiohttp.web.HTTPFound("/")  # TODO: Make a proper logout page


async def user_info_handler(request):
    '''
    This is a handler which currently shows:
    * Google user ID
    * E-mail
    * First and family name
    * Google avatar
    * And whether the user is authorized

    This is helpful for things like the little avatar when rendering the
    page.

    TODO: Think through what info we want to give as we add authentication
    methods. We don't want to leak data accidentally.
    '''
    return aiohttp.web.json_response(request[constants.USER])


async def user_from_session(request):
    '''
    Get the user object from the session.
    '''
    session = await aiohttp_session.get_session(request)
    session_user = session.get(constants.USER, None)
    if constants.AUTH_HEADERS in session:
        request[constants.AUTH_HEADERS] = session[constants.AUTH_HEADERS]
    return session_user


async def test_case_user(request):
    '''
    Return a test user, if we are in test mode

    This is a short circuit for test cases without logging in.
    THIS SHOULD NEVER BE ENABLED ON A LIVE SERVER
    '''
    tci = learning_observer.settings.settings['auth'].get("test_case_insecure", False)
    if not tci:
        return None
    if not isinstance(tci, dict):
        tci = {}

    user_info = {
        "name": tci.get("name", "Test Case"),
        "picture": "testcase.jpg",
        "authorized": True,
        "google_id": 12345,
        "email": "testcase@localhost"
    }
    await learning_observer.auth.utils.update_session_user_info(request, user_info)
    return user_info


async def demo_user(request):
    '''
    Return a demo user, if we are in demo mode

    This short circuits authentication for demos, cog-labs, development, etc.

    This should not be enabled on long-running live server, beyond spinning one up
    for a demo or something.

    In contrast to the test case user, this assigns a dummy name and similar. That's
    bad for testing, where we want determinism, but it's good for demos.
    '''
    if not learning_observer.settings.settings['auth'].get("demo_insecure", False):
        return None

    def name_to_email(name):
        '''
        Convert a name to an email address.

        Args:
            name (str): The name to convert.

        Returns:
            str: The email address.

        Example: "John Doe" -> "jdoe@localhost"
        '''

        name = name.split()
        return name[0][0].lower() + name[-1].lower() + "@localhost"

    demo_auth_setting = learning_observer.settings.settings['auth']["demo_insecure"]
    if isinstance(demo_auth_setting, dict) and 'name' in demo_auth_setting:
        name = demo_auth_setting['name']
    else:
        name = names.get_full_name()

    user_info = {
        "name": name,
        "picture": "/auth/default-avatar.svg",
        "authorized": True,
        "google_id": random.randint(10000, 99999),
        "email": name_to_email(name)
    }
    await learning_observer.auth.utils.update_session_user_info(request, user_info)
    return user_info


async def set_user_info_cookie(request, response):
    '''
    Set a cookie with the user's info.

    This is a helper function for the login handlers.

    This is *obsolete*, We now pass this through an AJAX call
    from the client to get the user info. This is because we
    found cookies were not working consistently on all browsers.
    They're probable fine for deployment, but we ran into
    heisenbugs on `localhost`.

    Args:
        request (aiohttp.web.Request): The request object.

    Returns:
        None
    '''
    # This is a dumb way to sanitize data and pass it to the front-end.
    #
    # Cookies tend to get encoded and decoded in ad-hoc strings a lot, often
    # in non-compliant ways (to see why, try to find the spec for cookies!)
    #
    # This avoids bugs (and, should the issue come up, security issues
    # like injections)
    #
    # This should really be abstracted away into a library which passes state
    # back-and-forth, but for now, this works.
    session = await aiohttp_session.get_session(request)
    session_user = session.get(constants.USER, None)

    response.set_cookie(
        "userinfo",
        base64.b64encode(json.dumps(session_user).encode('utf-8')).decode('utf-8')
    )


async def http_auth_user(request):
    '''
    Authenticate a user by HTTP Basic Auth.
    '''
    if not learning_observer.auth.http_basic.http_auth_middleware_enabled():
        return None
    if not learning_observer.auth.http_basic.has_http_auth_headers(request):
        return None
    raise NotImplementedError(
        "HTTP Basic Auth is not tested yet. Most of the code is there, but it\n"
        "should be tested. Since this is a security issue, it should be\n"
        "tested before we remove this exception."
    )
    request[constants.AUTH_HEADERS] = session.get(constants.AUTH_HEADERS, None)


@aiohttp.web.middleware
async def auth_middleware(request, handler):
    '''
    This is a middleware which:

    * Moves the user information into the request.
    * Sets the user's info cookie.
    * Handles authentication modes which don't require an explicit login. (e.g.
      demo mode, test case mode, http basic auth)

    Save user into a cookie
    '''
    user = None

    # This sets the order in which we check for user info
    user_sources = [
        user_from_session,
        http_auth_user,
        test_case_user,
        demo_user
    ]

    for user_source in user_sources:
        user = await user_source(request)
        if user is not None:
            break

    # If we didn't find a user, we're not authorized. We don't raise an error,
    # because we want to allow the user to log in from the main page. We just
    # don't want to allow them to access sensitive pages.

    request[constants.USER] = user
    resp = await handler(request)

    # We want to be able to e.g. show the user's name in the header on the
    # page from the front-end, so we need to pass the user's info to the
    # front-end. We do this by setting a cookie.
    #
    # This retrieves the user info from the session, since the user info
    # might have changed in the request (in particular, if the user logged
    # out)
    await set_user_info_cookie(request, resp)
    return resp


def serve_user_icon(request):
    '''
    Serve a user's default icon:
    * A user's icon if available.
    * An SVG of initials if no other icon is available.
    * A default icon if no other icon is available.

    Args:
        request (aiohttp.web.Request): The request object.

    Returns:
        aiohttp.web.Response: The response object.
    '''

    # Good idea once we have a good icon
    # if request[constants.USER] is None:
    #    return aiohttp.web.FileResponse(
    #        learning_observer.settings.settings['auth']['default_icon']
    #    )

    # In the future, we might want something along the lines of:
    # if 'picture' in request[constants.USER]:
    #    return aiohttp.web.FileResponse(
    #        request[constants.USER]['picture']
    #    )
    # We don't do this now -- we encode the URL and don't call this function
    # if we have a picture -- since we often serve avatars from Google.

    user = request.get(constants.USER, {})
    if user is None:
        user = {}
    name = user.get('name', None)

    return aiohttp.web.Response(
        body=learning_observer.graphics_helpers.default_user_icon(name),
        content_type="image/svg+xml"
    )
