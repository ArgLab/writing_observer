# learning_observer/integrations/schoology.py
import learning_observer.constants as constants
import learning_observer.settings as settings

from . import util

API = 'schoology'

# All endpoints use LTI service URLs, not direct Schoology REST API.
# These are accessed using the LTI access token negotiated at launch.
#
# LTI AGS spec: https://www.imsglobal.org/spec/lti-ags/v2p0
# LTI NRPS spec: https://www.imsglobal.org/spec/lti-nrps/v2p0
LTI_SERVICE_BASE = 'https://lti-service.svc.schoology.com/lti-service/tool/{clientId}'

ENDPOINTS = list(map(lambda x: util.Endpoint(**x, api_name=API), [
    {
        'name': 'course_list',
        'remote_url': f'{LTI_SERVICE_BASE}/services/names-roles/v2p0/membership/{{courseId}}',
        'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}  # required Schoology header for LTI membership requests
    },
    {
        'name': 'course_roster',
        'remote_url': f'{LTI_SERVICE_BASE}/services/names-roles/v2p0/membership/{{courseId}}',
        'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}  # required Schoology header for LTI membership requests
    },
    {
        # AGS line item container — lists all assignments for the course
        'name': 'course_assignments',
        'remote_url': f'{LTI_SERVICE_BASE}/services/ags/v2p0/lineitems/{{courseId}}',
        'headers': {'Accept': 'application/vnd.ims.lis.v2.lineitemcontainer+json'}
    },
    {
        # AGS results for a specific line item — lists per-student results/submissions
        # The lineItemId is typically the full line item URL or the trailing segment.
        'name': 'assignment_results',
        'remote_url': f'{LTI_SERVICE_BASE}/services/ags/v2p0/lineitems/{{courseId}}/{{courseWorkId}}/results',
        'headers': {'Accept': 'application/vnd.ims.lis.v2.resultcontainer+json'}
    },
]))

register_cleaner = util.make_cleaner_registrar(ENDPOINTS)


def register_endpoints(app):
    '''Register Schoology LTI endpoints with the application.'''
    if not settings.feature_flag('schoology_routes'):
        return

    return util.register_endpoints(
        app=app,
        endpoints=ENDPOINTS,
        api_name=API,
        feature_flag_name='schoology_routes'
    )


# ---------------------------------------------------------------------------
# Course list
# ---------------------------------------------------------------------------

@register_cleaner('course_list', 'courses')
def clean_course_list(schoology_json):
    '''
    The LTI integration Schoology uses for auth occurs on a
    course by course level. This cleaner wraps the current
    course in a list.
    '''
    context = schoology_json.get('context', {})
    course = {
        'id': context.get('id'),
        'name': context.get('label'),
        'title': context.get('title'),
    }
    return [course]


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

def _process_schoology_user_for_system(member, google_id):
    '''Convert an LTI NRPS member record into an internal user dict.'''
    lti_user_id = member.get('user_id')
    if not lti_user_id:
        return None

    is_student = (
        'http://purl.imsglobal.org/vocab/lis/v2/membership#Learner'
        in member.get('roles', [])
    )
    if not is_student:
        return None

    email = member.get('email')
    local_id = google_id
    if not local_id:
        local_id = f'schoology-{lti_user_id}'

    member[constants.USER_ID] = local_id
    user = {
        'profile': {
            'name': {
                'given_name': member.get('given_name'),
                'family_name': member.get('family_name'),
                'full_name': member.get('name')
            },
            'email_address': email,
            'photo_url': member.get('picture')
        },
        constants.USER_ID: local_id,
    }
    return user


@register_cleaner('course_roster', 'roster')
async def clean_course_roster(schoology_json):
    '''
    Retrieve and clean the roster for a Schoology course, alphabetically sorted.

    Conforms to LTI NRPS v2 response format.
    https://www.imsglobal.org/spec/lti-nrps/v2p0
    '''
    members = schoology_json.get('members', [])
    users = []

    emails = [m.get('email') for m in members]
    google_ids = await util.lookup_gids_by_emails(emails)

    for member, google_id in zip(members, google_ids):
        user = _process_schoology_user_for_system(member, google_id)
        if user is not None:
            users.append(user)

    users.sort(
        key=lambda user: user.get('profile', {}).get('name', {}).get('family_name', '')
    )
    return users


# ---------------------------------------------------------------------------
# Assignments (AGS line items)
# ---------------------------------------------------------------------------
@register_cleaner('course_assignments', 'assignments')
def clean_course_assignments(schoology_json):
    '''
    TODO implemement this function
    When launching via LTI, Schoology only allows us to see assignments
    created by our tool. To see all assignments we require an Oauth workflow.
    Clean course line items (assignments) from Schoology via LTI AGS.
    '''
    raise NotImplemented('Schoology assignments have not yet been implemented.')


# ---------------------------------------------------------------------------
# Assignment results / assigned docs (AGS results)
# ---------------------------------------------------------------------------
@register_cleaner('assignment_results', 'assigned_docs')
async def clean_assigned_docs(schoology_json):
    '''
    TODO implemement this function
    When launching via LTI, Schoology only allows us to see assignments
    created by our tool. To see all assignments we require an Oauth workflow.
    Extract per-student Google Doc attachments from LTI AGS results
    for a single assignment.
    '''
    raise NotImplemented('Schoology documents from assignments have not yet been implemented.')
