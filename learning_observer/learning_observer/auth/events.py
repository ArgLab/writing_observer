'''
We would like to have multiple means of assigning identity to incoming student events:

- Assigned per-connection
- Header in the events, unverified (e.g. for use during a coglab,
  during quasi-anonymous browser sessions)
- Header in the events, verified from a password file
- HTTP basic auth
- Google oauth
- Etc.

One piece of nuance:

- Some schemes will have a header sent once per connection, with no
  student data (view header, then discard)
- Some schemes will include identity with each event.

We're still figuring out the best ways to do this.

Some of these code paths are untested. Please test and debug before using.
'''

import asyncio
import urllib.parse
import secrets
import sys

import aiohttp_session
import aiohttp.web

import learning_observer.constants as constants
import learning_observer.paths
import learning_observer.prestartup
import learning_observer.settings

import learning_observer.auth.http_basic

from learning_observer.log_event import debug_log

AUTH_METHODS = {}


def register_event_auth(name):
    '''
    Decorator to register a method to authenticate events
    '''
    def wrapper(f):
        '''
        The decorator does not change the function
        '''
        AUTH_METHODS[name] = f
        return f
    return wrapper


def encode_id(source, unsafe_id):
    '''
    This is a bit of encoding logic to generically encode IDs from
    unknown sources. We want to avoid the problem of Little Bobby
    Tables (https://xkcd.com/327/).

    It's not clear this is needed long-term (we put this in when we
    were using Google emails rather than numeric IDs), but we're
    keeping it here for now for the test data sources. This just
    generically sanitizes everything in case we either missed
    something above, or just want to have a sane default before
    implementing something fancy.

    We also want to avoid overlapping UIDs between sources. For
    example, we don't want an attack where e.g. a user carefully
    creates an account on one auth provide to collide with a
    pre-existing account on another auth provider. So we append
    providence. Note that we don't want to do this twice (so
    `authutils` does this already for Google)

    >>> encode_id("gcu", "1234; DROP TABLE *")
    'gcu-1234%3B+DROP+TABLE+%2A'
    '''
    return "{source}-{uid}".format(
        source=source,
        uid=urllib.parse.quote_plus(
            unsafe_id,
            safe='@'  # Keep emails more readable
        )
    )


def token_authorize_user(auth_method, user_id_token):
    '''
    Authorize a user based on a list of allowed user ID tokens
    '''
    am_settings = learning_observer.settings.settings['event_auth'][auth_method]
    if 'userfile' in am_settings:
        userfile = am_settings['userfile']
        users = [u.strip() for u in open(learning_observer.paths.data(userfile)).readlines()]
        if user_id_token in users:
            return "authenticated"
    if am_settings.get("allow_guest", False):
        return "unauthenticated"
    raise aiohttp.web.HTTPUnauthorized()


@register_event_auth("http_basic")
async def basic_auth(request, event, source):
    '''
    Authenticate with HTTP Basic through nginx.
    '''
    (username, password) = learning_observer.auth.http_basic.http_basic_extract_username_password(request)
    print(f"Authenticated as {username}")
    if username is None:
        # nginx shouldn't pass requests without
        # auth headers. We are logging, but
        # with red flags; we don't want to lose
        # data. In more secure settings, we
        # might want to raise an exception
        # instead
        print("Event auth missing: This should never happen")
        return {
            'sec': 'unauthorized',
            constants.USER_ID: 'guest',
            'providence': 'error'
        }
    return {
        'sec': 'authenticated',
        constants.USER_ID: username,
        'providence': 'nginx'
    }


@register_event_auth("guest")
async def guest_auth(request, event, source):
    '''
    Guest users.

    We assign a cookie on first visit, but we have no guarantee
    the browser will keep cookies around.

    >>> a = asyncio.run(guest_auth(TestRequest(), [], {}, 'org.mitros.test'))
    >>> a['user_id'] = len(a['user_id'])  # Different user_id each time, and we want doctest to match exact string.
    >>> a
    {'sec': 'none', 'user_id': 32, 'providence': 'guest'}
    '''
    session = await aiohttp_session.get_session(request)
    guest_id = session.get('guest_id', None)
    if guest_id is None:
        guest_id = secrets.token_hex(16)
        session['guest_id'] = guest_id
    return {
        'sec': 'none',
        constants.USER_ID: guest_id,
        'providence': 'guest'
    }


@register_event_auth("local_storage")
async def local_storage_auth(request, event, source):
    '''
    This authentication method is used by the browser extension, based
    on configuration options. Each Chromebook is given a unique ID
    token, which is stored in local_storage.

    This can be authenticated (if we have a list of such tokens),
    unauthenticated (if we don't), or allow for both, with a tag for
    guest versus non-guest accounts.

    >>> auth_event = {'event': 'local_storage', 'user_tag': 'bob'}
    >>> a = asyncio.run(local_storage_auth(TestRequest(), [], auth_event, 'org.mitros.test'))
    >>> a
    {'sec': 'authenticated', 'user_id': 'ls-bob', 'providence': 'ls'}
    >>> auth_event['user_tag'] = 'jim'
    >>> a = asyncio.run(local_storage_auth(TestRequest(), [auth_event], {}, 'org.mitros.test'))
    >>> a
    {'sec': 'unauthenticated', 'user_id': 'ls-jim', 'providence': 'ls'}
    '''
    if 'user_tag' not in event:
        return False

    user_id = "ls-" + event['user_tag']
    authenticated = token_authorize_user('local_storage', user_id)

    return {
        'sec': authenticated,
        constants.USER_ID: user_id,
        'providence': 'ls'  # local storage
    }


@register_event_auth("chromebook")
async def chromebook_auth(request, event, source):
    '''
    Authenticate student Chromebooks.

    TODO: We should have some way to do this securely -- to connect
          the identity token to the Google ID.
    TODO: See about client-side oauth on Chromebooks
    '''
    if 'chrome_identity' not in event:
        return False

    # If we have an auth key, we are authenticated!
    lsa = await local_storage_auth(request, event, source)

    if lsa and lsa['sec'] == 'authenticated':
        auth = 'authenticated'
    else:
        auth = 'unauthenticated'

    untrusted_google_id = event.get('chrome_identity', {}).get('id', None)
    debug_log("untrusted_google_id", untrusted_google_id)

    if untrusted_google_id is None:
        return False

    gc_uid = learning_observer.auth.utils.google_id_to_user_id(untrusted_google_id)
    return {
        'sec': auth,
        constants.USER_ID: gc_uid,
        'safe_user_id': gc_uid,
        'providence': 'gcu'  # Google Chrome, unauthenticated
    }


@register_event_auth('lti_session')
async def lti_session_auth(request, event, source):
    """Authenticate websocket events using the existing LTI session.

    When a dashboard is launched through LTI, the launch flow stores the
    verified user information (including the subject identifier and course
    context) in the aiohttp session via :func:`update_session_user_info`. If a
    websocket request reuses that session, we can surface the same metadata for
    incoming events so reducers can attribute them correctly.
    """

    session = await aiohttp_session.get_session(request)
    user = session.get(constants.USER)
    if not user:
        return False

    return {
        'sec': 'authenticated',
        constants.USER_ID: user[constants.USER_ID],
        'providence': 'lti',
        'lti_context': user.get('lti_context')
    }


@register_event_auth("hash_identify")
async def hash_identify(request, event, source):
    '''
    It's sometimes convenient to point folks to pages where the
    user ID is encoded in the URL e.g. by hash:

       `http://myserver.ets.org/user-study-5/#user=zihan`

    This fails for even modest-scale use; even in an afterschool
    club, experience shows that at least one child WILL mistype
    a URL, either unintentionally or as a joke.

    But it is nice for one-offs where you're working directly
    with a subject.

    This could be made better by providing an authenticated user
    list. Then, it'd be okay for the math team example
    '''
    if 'hash' not in event:
        return False

    return {
        'sec': 'unauthenticated',
        constants.USER_ID: "hi-" + event['hash'],
        'providence': 'mch'  # Math contest hash -- toying with plug-in archicture
    }


@register_event_auth("testcase_auth")
async def test_case_identify(request, event, source):
    '''
    This is for test cases. It's quick, easy, insecure, and shouldn't
    be used in production.
    '''
    if constants.USER_ID not in event:
        return False

    return {
        'sec': "unauthenticated",
        constants.USER_ID: "testcase-" + event[constants.USER_ID],
        'providence': 'tc'
    }


async def authenticate(request, event, source):
    '''
    Authenticate an event stream.

        Parameters:
            request: aio_http request object
            headers: list of headers from event stream
            first_event: first non-header event
            source: where the events are coming from (e.g. `org.mitros.writing`)

    TODO: Allow configuring authentication methods based on event
    type (e.g. require auth for writing, but not for dynamic assessment)

    Our thoughts are that the auth metadata ought to contain:

    1. Whether the user was authenticated (`sec` field):
        * `authenticated` -- we trust who they are
        * `unauthenticated` -- we think we know who they are, without security
        * `guest` -- we don't know who they are
    2. Providence: How they were authenticated (if at all), or how we believe they are who they are.
    3. `user_id` -- a unique user identifier
    '''
    for auth_method in learning_observer.settings.settings['event_auth']:
        auth_metadata = await AUTH_METHODS[auth_method](request, event, source)
        if auth_metadata:
            if "safe_user_id" not in auth_metadata:
                auth_metadata['safe_user_id'] = encode_id(
                    source=auth_metadata["providence"],
                    unsafe_id=auth_metadata[constants.USER_ID]
                )
            return auth_metadata

    return False


@learning_observer.prestartup.register_startup_check
def check_event_auth_config():
    '''
    Check that all event auth methods are correctly configured,
    before events come in.
    '''
    if 'event_auth' not in learning_observer.settings.settings:
        raise learning_observer.prestartup.StartupCheck("Please configure event authentication")
    for auth_method in learning_observer.settings.settings['event_auth']:
        if auth_method not in AUTH_METHODS:
            raise learning_observer.prestartup.StartupCheck(
                "Please configure event authentication for {}\n(Methods: {})".format(
                    auth_method,
                    list(AUTH_METHODS.keys())
                ))


if __name__ == "__main__":
    import doctest
    print("Running tests")

    class TestRequest:
        pass

    session = {}

    async def get_session(request):
        return session

    aiohttp_session.get_session = get_session
    doctest.testmod()
