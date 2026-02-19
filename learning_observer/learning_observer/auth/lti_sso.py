'''
Generic LTI 1.3 Single Sign-On handler for multiple providers.

Implements LTI 1.3's OpenID Connect (OIDC) authentication handshake.
OIDC establishes a secure SSO channel between Learning Management
Systems (LMS) and our tool. This allows the LMS to install our
application under specific contexts (courses).

The workflow is split across 2 functions

`handle_oidc_authorize`
1. The LMS sends request for OIDC parameters to this endpoint
2. We create parameters with metadata and send back

`handle_oidc_launch`
3. If authorized, the LMS sends back encrypted data to this endpoint
4. We decrypt, to get information about the user
5. We verify ourselves against the LMS to generate an auth token
6. User and auth information is stored in the session
'''

import aiohttp
import aiohttp_session
import jwt
import pmss
import re
import time
import uuid
from aiohttp import web
from urllib.parse import urlencode

import learning_observer.auth.utils
import learning_observer.constants as constants
import learning_observer.settings

from learning_observer.log_event import debug_log

'''
Items in settings should look like
{
    'auth_uri': 'https://canvas.instructure.com/api/lti/authorize_redirect',
    'jwks_uri': 'https://canvas.instructure.com/api/lti/security/jwks',
    'token_uri': 'https://canvas.instructure.com/login/oauth2/token',
    'client_id': 'YOUR_CLIENT_ID',
    'redirect_uri': 'https://yourdomain.com/lti/canvas/launch',
    'private_key_path': './keys/canvas/private.pem'
}
'''
pmss.register_field(
    name='auth_uri',
    type=pmss.pmsstypes.TYPES.string,
    description="Where to redirect the user's OIDC parameters",
    required=True
)
pmss.register_field(
    name='jwks_uri',
    type=pmss.pmsstypes.TYPES.string,
    description="The server's jwks endpoint",
    required=True
)
pmss.register_field(
    name='token_uri',
    type=pmss.pmsstypes.TYPES.string,
    description="Where to trade verified users for oauth tokens",
    required=True
)
pmss.register_field(
    name='redirect_uri',
    type=pmss.pmsstypes.TYPES.string,
    description='Where to redirect a user after successful OAuth login',
    required=True
)
pmss.register_field(
    name='private_key_path',
    type=pmss.pmsstypes.TYPES.string,
    description='Path to where private key is stored',
    required=True
)


# TODO this code is copied from lo/lo/integrations/canvas.py
# it should abstracted properly
def _extract_course_id_from_url(url):
    if match := re.search(r'/courses/(\d+)/names_and_role', url):
        return match.group(1)
    return None


# TODO: Implement persistent configuration storage
# TODO: Add rate limiting for JWKS requests
# TODO: Implement CSRF protection for state parameter

# ===============================
# JWKS/JWT Validation Utilities
# ===============================

JWKS_CACHE = {}


async def _decode_and_validate_lti_token(provider: str, token: str) -> dict:
    '''
    This uses the provider's public key to decode the token
    provided by the LMS to our launch endpoint.

    The JSON Web Key Sets (JWKS) are used for verifying
    JSON Web Tokens (JWT) that were issued and signed.
    '''
    async def get_public_key(kid: str):
        '''Get RSA public key from our JWKS to verify token signature
        '''
        async def fetch_jwks() -> dict:
            '''This fetches and caches JWKS from an external service.
            '''
            jwks_uri = learning_observer.settings.pmss_settings.jwks_uri(types=['auth', 'lti', provider])

            if provider not in JWKS_CACHE:
                async with aiohttp.ClientSession() as session:
                    async with session.get(jwks_uri) as response:
                        JWKS_CACHE[provider] = await response.json()
            return JWKS_CACHE[provider]

        def find_jwk(jwks: dict) -> dict:
            return next((k for k in jwks.get('keys', []) if k.get('kid') == kid), None)

        if jwk := find_jwk(await fetch_jwks()):
            return jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
        return None

    # Extract unverified headers and claims from JWT
    # We need to extract some information from the token so
    # we can know the `kid`, `aud`, and `iss`.
    headers = jwt.get_unverified_header(token)
    claims = jwt.decode(token, options={'verify_signature': False})

    if not (public_key := await get_public_key(headers.get('kid'))):
        raise jwt.exceptions.InvalidTokenError('Invalid key ID')

    return jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        audience=claims.get('aud'),
        issuer=claims.get('iss')
    )


# ======================
# OIDC Authorization Flow
# ======================
# Implements LTI 1.3's OpenID Connect (OIDC) authentication handshake.
# OIDC establishes a secure SSO channel between Learning Management
# Systems (LMS) and our tool.

# ======================
# OIDC Login Handler
# ======================


async def handle_oidc_authorize(request: web.Request) -> web.Response:
    '''Initiate OIDC authorization flow.
    Create OIDC request parameters and send them to the
    LMS to verify.

    This function is registered to route `/lti/{provider}/login`
    '''
    def create_oidc_params(provider, data: dict) -> dict:
        return {
            'scope': 'openid',
            'response_type': 'id_token',
            'response_mode': 'form_post',
            'prompt': 'none',
            'client_id': learning_observer.settings.pmss_settings.client_id(types=['auth', 'lti', provider]),
            # TODO this could easily be built from server/lti/{provider}/launch
            'redirect_uri': learning_observer.settings.pmss_settings.redirect_uri(types=['auth', 'lti', provider]),
            # help confirm state with future responses
            'nonce': str(uuid.uuid4()),
            'state': str(uuid.uuid4()),
            # hints provided by LMS
            'login_hint': data.get('login_hint', ''),
            'lti_message_hint': data.get('lti_message_hint', '')
        }

    provider = request.match_info['provider']
    data = await request.post() if request.method == 'POST' else request.query

    params = create_oidc_params(provider, data)
    session = await aiohttp_session.get_session(request)
    session['lti_state'] = params['state']
    session['lti_nonce'] = params['nonce']
    redirect_base_url = learning_observer.settings.pmss_settings.auth_uri(types=['auth', 'lti', provider])
    return web.HTTPFound(
        location=f"{redirect_base_url}?{urlencode(params)}"
    )


# ======================
# OIDC Launch Handler
# ======================


async def handle_oidc_launch(request: web.Request) -> web.Response:
    '''Process OIDC launch response
    After the LMS server confirms our identity, it sends information
    about the user to this endpoint. We exchange that information for
    an API token and store it in the user's session. This token is
    used later for getting the roster/assignments/etc.

    This function is registered to route `/lti/{provider}/launch`
    '''
    def validate_oidc_state(session: dict, state: str) -> None:
        '''Validate OIDC state parameter matches session'''
        if session.get('lti_state') != state:
            debug_log('LTI Launch invalid state')
            raise web.HTTPBadRequest(text='Something went wrong.')

    def create_user_from_claims(claims: dict, provider: str) -> dict:
        '''The created user is consistent with the rest of LO.
        '''
        roles = claims.get('https://purl.imsglobal.org/spec/lti/claim/roles', [])
        instructor_roles = [
            'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator',
            'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor',
            'http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor',
            'http://purl.imsglobal.org/vocab/lis/v2/system/person#SysAdmin'
        ]
        learner_roles = [
            'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner',
            'http://purl.imsglobal.org/vocab/lis/v2/membership#Learner'
        ]
        is_instructor = any(r in roles for r in instructor_roles)
        is_learner = any(r in roles for r in learner_roles)

        # Include the LTI Launch Context
        # HACK in Canvas, each course has 2 IDs:
        # 1. LTI compliant ID - `lti_context_id`
        # 2. ID used to make API calls - `api_id`
        context = claims.get('https://purl.imsglobal.org/spec/lti/claim/context', {})
        api_with_id = claims.get('https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice', {}).get('context_memberships_url')
        extracted_course_id = _extract_course_id_from_url(api_with_id)
        id = context['id']
        lti_context = {
            'lti_context_id': id,
            'api_id': extracted_course_id if extracted_course_id else id,
            'provider': provider
        }

        return {
            constants.USER_ID: claims['sub'],
            'email': claims.get('email'),
            'name': claims.get('given_name'),
            'family_name': claims.get('family_name', ''),
            'picture': claims.get('picture', ''),
            'role': learning_observer.auth.ROLES.TEACHER if is_instructor else learning_observer.auth.ROLES.STUDENT,
            'authorized': is_instructor or is_learner,
            'lti_context': lti_context
            # TODO figure out backto. With google sso, we had a state we could store things in
            # 'back_to': request.query.get('state')
        }

    def generate_signed_client_authentication_jwt(provider) -> str:
        '''
        Generates cryptographically signed JWTs for verifying identity.
        Uses RSA-SHA256 to sign claims containing client identity (iss/sub),
        token endpoint (aud), timestamp controls (iat/exp), and unique JTI.

        The token generated is used to obtain an OAuth token
        '''
        def read_private_pem_key_from_file(path: str) -> str:
            return open(path, 'r').read()

        private_key_path = learning_observer.settings.pmss_settings.private_key_path(types=['auth', 'lti', provider])
        private_key = read_private_pem_key_from_file(private_key_path)

        now = time.time()
        client_id = learning_observer.settings.pmss_settings.client_id(types=['auth', 'lti', provider])
        token_uri = learning_observer.settings.pmss_settings.token_uri(types=['auth', 'lti', provider])

        # Note the client is both the issuer and subject since
        # it is proving its own identity
        payload = {
            'iss': client_id,   # issuer
            'sub': client_id,   # subject
            'aud': token_uri,   # audience
            'iat': now,         # JWT issued at
            'exp': now + 300,   # JWT expiration (5 minutes)
            'jti': str(uuid.uuid4()) # JWT ID
        }
        return jwt.encode(payload, private_key, algorithm='RS256')

    async def exchange_assertion_for_token(provider, assertion: str) -> str:
        '''Exchange client assertion for access token'''
        token_uri = learning_observer.settings.pmss_settings.token_uri(types=['auth', 'lti', provider])
        token_data = {
            'grant_type': 'client_credentials',
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'client_assertion': assertion,
            'scope': ' '.join([
                # Can retrieve user data associated with the context the tool is installed in
                'https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly',
                # Can view assignment data in the gradebook associated with the tool
                'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly',
                # Can create and update submission results for assignments associated with the tool
                'https://purl.imsglobal.org/spec/lti-ags/scope/score',
            ])
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=token_uri, data=token_data) as response:
                if response.status != 200:
                    debug_log(f'LTI Launch Error during token exchange:\n{await response.text()}')
                    raise web.HTTPBadRequest(text='Something went wrong.')
                return (await response.json())['access_token']

    provider = request.match_info['provider']
    data = await request.post()

    try:
        # Validate OIDC response
        session = await aiohttp_session.get_session(request)
        validate_oidc_state(session, data.get('state'))

        # Verify and decode JWT
        claims = await _decode_and_validate_lti_token(provider, data.get('id_token'))
        if claims['nonce'] != session.get('lti_nonce'):
            debug_log('LTI Launch invalid nonce')
            raise web.HTTPBadRequest(text='Something went wrong.')

        # Create user session
        user_info = create_user_from_claims(claims, provider)
        await learning_observer.auth.utils.update_session_user_info(request, user_info)

        # Exchange for access token
        assertion = generate_signed_client_authentication_jwt(provider)
        access_token = await exchange_assertion_for_token(provider, assertion)

        # Store auth headers
        headers = {'Authorization': f'Bearer {access_token}'}
        session[constants.AUTH_HEADERS] = headers
        request[constants.AUTH_HEADERS] = headers

        return web.HTTPFound(location='/')

    except (jwt.PyJWTError, KeyError) as e:
        debug_log(f'LTI Launch Authentication failed: {e}')
        raise web.HTTPUnauthorized(text='Something went wrong.')


async def check_oidc_login(request):
    return web.HTTPFound('/')
