import learning_observer.constants as constants
import learning_observer.kvs
import learning_observer.settings as settings

from . import util

API = 'schoology'

ENDPOINTS = list(map(lambda x: util.Endpoint(**x, api_name=API), [
    {'name': 'course_list', 'remote_url': 'https://lti-service.svc.schoology.com/lti-service/tool/{clientId}/services/names-roles/v2p0/membership/{courseId}', 'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}},
    {'name': 'course_roster', 'remote_url': 'https://lti-service.svc.schoology.com/lti-service/tool/{clientId}/services/names-roles/v2p0/membership/{courseId}', 'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}},
    {'name': 'course_assignments', 'remote_url': 'https://api.schoology.com/v1/sections/{courseId}/assignments', 'headers': {'Accept': 'application/vnd.ims.lis.v2.lineitemcontainer+json'}},
]))

register_cleaner = util.make_cleaner_registrar(ENDPOINTS)


def register_endpoints(app):
    '''
    '''
    if not settings.feature_flag('schoology_routes'):
        return

    return util.register_endpoints(
        app=app,
        endpoints=ENDPOINTS,
        api_name=API,
        feature_flag_name='schoology_routes'
    )


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


def _process_schoology_user_for_system(member, google_id):
    # Skip if no canvas id
    canvas_id = member.get('user_id')
    if not canvas_id: return None

    # Skip non students
    is_student = 'http://purl.imsglobal.org/vocab/lis/v2/membership#Learner' in member.get('roles', [])
    if not is_student:
        return None

    # Create user for our system
    email = member.get('email')
    local_id = google_id
    if not local_id:
        local_id = f'canvas-{canvas_id}'

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
        # TODO is this needed? Other roster functions in LO include it
        # 'course_id': course_id
    }
    return user


@register_cleaner('course_roster', 'roster')
async def clean_course_roster(schoology_json):
    '''
    Retrieve and clean the roster for a Canvas course, alphabetically sorted

    Conforms to LTI NRPS v2 response format
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
    return users


@register_cleaner('course_assignments', 'assignments') 
def clean_course_assignments(schoology_json):
    '''
    Clean course line items (assignments) from Schoology

    Conforms to LTI AGS response format
    https://www.imsglobal.org/spec/lti-ags/v2p0
    '''
    # print('Schoology assignments TODO', schoology_json)
    return []
