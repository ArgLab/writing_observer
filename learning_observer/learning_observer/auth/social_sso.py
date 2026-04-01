"""
Authentication for Google.

This was based on
[aiohttp-login](https://github.com/imbolc/aiohttp-login/), which at
the time worked with outdated Google APIs and require Jinja2. Oren
modernized this. Piotr integrated this into the system.

Portions of this file, from aiohttp-login, are licensed as:

Copyright (c) 2011 Imbolc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

Eventually, this should be broken out into its own module.
"""

import asyncio
import yarl

import aiohttp
import aiohttp.web
import aiohttp_session

# TODO: We might want to not import this, but pass this info, to make
# this file generic, and not specific to learning_observer.
import learning_observer.settings as settings
import learning_observer.auth.handlers as handlers
import learning_observer.auth.utils
import learning_observer.auth.roles

import learning_observer.constants as constants
import learning_observer.exceptions
import learning_observer.kvs
import learning_observer.rosters
import learning_observer.runtime
import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.util

from learning_observer.log_event import debug_log

import pmss
# TODO the hostname setting currently expect the port
# to specified within the hostname. We ought to
# remove the port and instead use the port setting.
pmss.register_field(
    name="hostname",
    type=pmss.pmsstypes.TYPES.hostname,
    description="The hostname of the LO webapp. Used to redirect OAuth clients.",
    required=True
)
pmss.register_field(
    name="protocol",
    type=pmss.pmsstypes.TYPES.protocol,
    description="The protocol (http / https) of the LO webapp. Used to redirect OAuth clients.",
    required=True
)
pmss.register_field(
    name="client_id",
    type=pmss.pmsstypes.TYPES.string,
    description="The Google OAuth client ID",
    required=True
)
pmss.register_field(
    name="client_secret",
    type=pmss.pmsstypes.TYPES.string,
    description="The Google OAuth client secret",
    required=True
)
pmss.register_field(
    name='fetch_additional_info_from_teacher_on_login',
    type=pmss.pmsstypes.TYPES.boolean,
    description='Whether we should start an additional task that will '\
        'fetch all text from current rosters.',
    default=False
)


DEFAULT_GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.profile.emails',
    'https://www.googleapis.com/auth/classroom.profile.photos',
    'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/classroom.guardianlinks.students.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly'
]

# TODO Type list is not yet supported by PMSS 4/24/24
# pmss.register_field(
#     name='base_scopes',
#     type='list',
#     description='List of Google URLs to look for.',
#     default=DEFAULT_GOOGLE_SCOPES
# )
# pmss.register_field(
#     name='additional_scopes',
#     type='list',
#     description='List of additional URLs to look for.',
#     default=[]
# )


async def social_handler(request):
    """Handles Google sign in.

    Provider is in `request.match_info['provider']` (currently, only Google)
    """
    if request.match_info['provider'] != 'google':
        raise learning_observer.exceptions.SuspiciousOperation(
            "We only handle Google logins. Non-google Provider"
        )

    user = await _google(request)

    if constants.USER_ID in user:
        await learning_observer.auth.utils.update_session_user_info(request, user)

    if user['authorized']:
        url = user['back_to'] or "/"
        if settings.pmss_settings.fetch_additional_info_from_teacher_on_login():
            request[constants.USER] = user
            asyncio.create_task(_store_teacher_info_for_background_process(user['user_id'], request))
    else:
        url = "/"

    return aiohttp.web.HTTPFound(url)


async def _store_teacher_info_for_background_process(id, request):
    '''HACK this code stores 2 pieces of information when
    teacher logs in with a social handlers.

    1. We want to have a background process that fetches Google
    docs and then processes them. This function stores relevant
    teacher information (Google auth token + rosters) so we can
    later fetch and process documents in our separate process.
    The token is removed with the `utils.py:logout()` method.

    2. For each student within a roster, we attempt to fetch all
    of their deocument texts via the Google API. These are
    stored as reducer on the system.

    TODO remove this function and references when new, better
    workflows are established.
    '''
    import learning_observer.google
    debug_log("SocialSSO Storing teacher info: {} {}".format(id, request))
    kvs = learning_observer.kvs.KVS()
    runtime = learning_observer.runtime.Runtime(request)
    courses = await learning_observer.rosters.courselist(request)
    skipped_docs = set()

    # store teacher auth info
    auth_key = sa_helpers.make_key(
        learning_observer.auth.utils.google_stored_auth,
        {sa_helpers.KeyField.TEACHER: id},
        sa_helpers.KeyStateType.INTERNAL)
    await kvs.set(auth_key, request[constants.AUTH_HEADERS])
    current_keys = await kvs.keys()

    async def _fetch_and_store_document(student, doc_id):
        # TODO: Move doc key up here.  Check if doc key in current keys.If it is return.
        debug_log("SocialSSO Fetching Document: {} {}".format(student, doc_id))
        doc_key = sa_helpers.make_key(
            _fetch_and_store_document,
            {sa_helpers.KeyField.STUDENT: student, sa_helpers.EventField('doc_id'): doc_id},
            sa_helpers.KeyStateType.INTERNAL)
        if doc_key in current_keys:
            return
        doc = await learning_observer.google.doctext(runtime, documentId=doc_id)
        if 'text' not in doc:
            skipped_docs.add(doc_id)
            debug_log("** SocialSSO Text not found: {} {}".format(student, doc_id))
            return
        await kvs.set(doc_key, doc)
        debug_log("** SocialSSO Text stored: {} {}".format(student, doc_id))

    async def _process_student_documents(student):
        debug_log("** SocialSSO Processing student: {}".format(student))
        student_docs = (k for k in current_keys if student in k and 'EventField.doc_id' in k)
        specifier = 'EventField.doc_id:'
        student_docs = (k[k.find(specifier) + len(specifier):k.find(',', k.find(specifier))] for k in student_docs)
        student_docs = set(student_docs)
        doc_key = sa_helpers.make_key(
            _process_student_documents,
            {sa_helpers.KeyField.STUDENT: student},
            sa_helpers.KeyStateType.INTERNAL)
        await kvs.set(doc_key, {"student_docs": list(student_docs)})
        for doc_id in student_docs:
            await _fetch_and_store_document(student, doc_id)

    for course in courses:
        # Fetch and store course information
        roster = await learning_observer.rosters.courseroster(request, course_id=course['id'])
        students = [s['user_id'] for s in roster]
        roster_key = sa_helpers.make_key(
            learning_observer.google.roster,
            {sa_helpers.KeyField.TEACHER: id, sa_helpers.KeyField.CLASS: course['id']},
            sa_helpers.KeyStateType.INTERNAL)
        await kvs.set(roster_key, {'teacher_id': id, 'students': students})

        # For each student, fetch their available documents and store them
        for student in students:
            # we ought to fire these off as tasks instead of waiting on
            # them before waiting for the next roster to process
            await _process_student_documents(student)
    # TODO saved skipped doc ids somewhere?


async def _google(request):
    '''
    Handle Google login
    '''
    if 'error' in request.query:
        return {}

    hostname = settings.pmss_settings.hostname()
    protocol = settings.pmss_settings.protocol()
    common_params = {
        'client_id': settings.pmss_settings.client_id(types=['auth', 'google_oauth', 'web']),
        'redirect_uri': f"{protocol}://{hostname}/auth/login/google"
    }

    # Step 1: redirect to get code
    if 'code' not in request.query:
        url = 'https://accounts.google.com/o/oauth2/auth'
        params = common_params.copy()
        # We can override the scopes in the settings file entirely...
        scopes = settings.settings['auth']['google_oauth']['web'].get(
            'base_scopes',
            DEFAULT_GOOGLE_SCOPES
        )
        # Or keep the default scopes and just add a few new ones....
        scopes += settings.settings['auth']['google_oauth'].get(
            'additional_scopes',
            []
        )
        params.update({
            'response_type': 'code',
            'scope': " ".join(scopes),
        })
        if 'back_to' in request.query:
            params['state'] = request.query['back_to']
        url = yarl.URL(url).with_query(params)
        raise aiohttp.web.HTTPFound(url)

    # Step 2: get access token
    url = 'https://accounts.google.com/o/oauth2/token'
    params = common_params.copy()
    params.update({
        'client_secret': settings.pmss_settings.client_secret(types=['auth', 'google_oauth', 'web']),
        'code': request.query['code'],
        'grant_type': 'authorization_code',
    })
    async with aiohttp.ClientSession(loop=request.app.loop) as client:
        async with client.post(url, data=params) as resp:
            data = await resp.json()
        assert 'access_token' in data, data

        # get user profile
        headers = {'Authorization': 'Bearer ' + data['access_token']}
        session = await aiohttp_session.get_session(request)
        session[constants.AUTH_HEADERS] = headers
        request[constants.AUTH_HEADERS] = headers

        # Old G+ URL that's no longer supported.
        url = 'https://www.googleapis.com/oauth2/v1/userinfo'
        async with client.get(url, headers=headers) as resp:
            profile = await resp.json()

    role = await learning_observer.auth.utils.verify_role(profile['id'], profile['email'])
    return {
        constants.USER_ID: profile['id'],
        'email': profile['email'],
        'name': profile['given_name'],
        'family_name': profile['family_name'],
        'back_to': request.query.get('state'),
        'picture': profile['picture'],
        # TODO: Should this be immediate?
        # TODO: Should authorized just take over the role?
        # the old code relis on authorized being set to True
        # to allow users access to various dashboards. Should
        # we modify this behavior to check for a role or True
        # instead of using the role attribute.
        'authorized': role in [learning_observer.auth.ROLES.ADMIN, learning_observer.auth.ROLES.TEACHER],
        'role': role
    }


async def show_me_my_auth_headers(request):
    """
    Show the auth headers that are set in the session. For convenience, we also
    show other headers that were sent to the server and might add other
    information.

    This is handy for debugging and development. I'd often like to use the
    server registered with Google to log in, but then use this information
    in a development environment or a script.

    This is behind a feature flag. On a live server, it should be disabled
    as set right now. In the future, we might want to make this a feature
    that can be enabled for specific users. This is not a huge security
    risk, as the user can only access the information they have access to,
    but a user's patterns might look suspicious to Google's (often broken)
    algorithms, and we don't want to get flagged.

    There is a setting, `allow_override`, which allows setting auth headers
    in a development environment.
    """
    flag = settings.feature_flag('auth_headers_page')

    if not flag:
        # The route should not have been added...
        raise aiohttp.web.HTTPForbidden(
            "This feature is disabled. We should never get here. Please debug this."
        )

    # This is so that we can use the headers from the Google-approved server in
    # my local development environment. Google has all sorts of validation that
    # make it hard to retrieve the headers from the server directly to protect
    # users from phishing, so we can't just implement oauth locally.
    if request.method == 'POST':
        if not (isinstance(flag, dict) or isinstance(flag, list)) or 'allow_override' not in flag:
            raise aiohttp.web.HTTPForbidden("Overriding headers is disabled")
        if not request.can_read_form:
            raise aiohttp.web.HTTPForbidden("Cannot read form")

        auth_headers = request.form.get(constants.AUTH_HEADERS)
        if not auth_headers:
            raise aiohttp.web.HTTPBadRequest(
                text="Missing auth_headers"
            )
        session = await aiohttp_session.get_session(request)
        session[constants.AUTH_HEADERS] = auth_headers
        request[constants.AUTH_HEADERS] = auth_headers
        session.save()

    return aiohttp.web.json_response({
        constants.AUTH_HEADERS: request.get(constants.AUTH_HEADERS, None),
        "headers": dict(request.headers)
    })
