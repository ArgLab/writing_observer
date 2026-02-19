'''
Password log-in handler
'''
from distutils.log import debug
import bcrypt
import json
import yaml

import aiohttp.web

import learning_observer.auth.handlers
import learning_observer.auth
import learning_observer.auth.utils
import learning_observer.constants
from learning_observer.log_event import debug_log


def password_auth(filename):
    '''
    Authentication handler for logging in with username and password
    based on a password file.

    By placing this in a closure, we eliminate the dependency on
    settings.

    Todo:
    * Flag to load file on startup versus on request
    * Support storing this in a database
    * Log out after time-out from last request

    For convenience, this can be called directly as:

    `curl -X POST \
          -F "username=test_user" \
          -F "password=test_password" \
          http://localhost:8888/23auth/login/password`
    '''
    async def password_auth_handler(request):
        data = await request.post()  # Web form
        body = await request.text()  # AJAX
        if 'username' not in data:
            data = json.loads(body)
        with open(filename) as f:
            password_data = yaml.safe_load(f)

        # If you run into errors on the line below, you *probably*
        # have a dependency issue. Errors:
        # * AttributeError: module 'bcrypt' has no attribute 'checkpw'
        # * AttributeError: module 'bcrypt._bcrypt' has no attribute 'ffi'
        # Try uninstalling bcrypt and reinstalling / upgrading pi-bcrypt
        #
        # If you run into unicode errors, see if you can debug them. There
        # is randomness about whether we do or don't need to .encode('utf-8').
        #
        # It reliably either works or doesn't, but it doesn't change. If your
        # environment has a happy `bcrypt`, it will keep on working.
        if data['username'] not in password_data['users']:
            debug_log("User not found")
            return aiohttp.web.json_response({"status": "unauthorized"})
        user_data = password_data['users'][data['username']]
        try:
            password_check = bcrypt.checkpw(
                data['password'].encode('utf-8'),
                user_data['password'].encode('utf-8')
            )
        except:  # noqa: E722 TODO figure out which errors to catch
            debug_log("Error verifying password hash")
            debug_log("Hint: Try reinstalling / upgrading bcrypt")
            debug_log("For some reason, bcrypt tends to sometimes install incorrectly")
            debug_log("or get into an inconsistent state with ffi.")
            raise
        if not password_check:
            debug_log("Password check failed")
            return aiohttp.web.json_response({"status": "unauthorized"})
        debug_log("Password check authorized")
        await learning_observer.auth.utils.update_session_user_info(
            request, {
                learning_observer.constants.USER_ID: "pwd-" + user_data['username'],  # Perhaps data['username']?
                'email': user_data.get('email', ''),
                'name': user_data.get('name', ''),
                'family_name': user_data.get('family_name', ''),
                'picture': user_data.get('picture', '/auth/default-avatar.svg'),
                'authorized': True,
                'role': user_data.get('role', learning_observer.auth.ROLES.STUDENT)
            }
        )
        return aiohttp.web.json_response({"status": "authorized"})

    return password_auth_handler
