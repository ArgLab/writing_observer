import re

import learning_observer.constants as constants
import learning_observer.kvs
import learning_observer.settings as settings
import learning_observer.auth
import learning_observer.util

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
        'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}
    },
    {
        'name': 'course_roster',
        'remote_url': f'{LTI_SERVICE_BASE}/services/names-roles/v2p0/membership/{{courseId}}',
        'headers': {'Accept': 'application/vnd.ims.lti-nrps.v2.membershipcontainer+json'}
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
        key=lambda u: u.get('profile', {}).get('name', {}).get('family_name', '')
    )
    return users


# ---------------------------------------------------------------------------
# Assignments (AGS line items)
# ---------------------------------------------------------------------------

def _extract_id_from_lti_url(url):
    '''
    Extract the trailing ID segment from a full LTI AGS URL.

    e.g. "https://lti-service.svc.schoology.com/.../lineitems/12345/67890"
         → "67890"
    '''
    if not isinstance(url, str):
        return url
    url = url.rstrip('/')
    return url.rsplit('/', 1)[-1]


@register_cleaner('course_assignments', 'assignments')
def clean_course_assignments(schoology_json):
    '''
    TODO we need to test this function with schoology
    Clean course line items (assignments) from Schoology via LTI AGS.

    LTI AGS line item container spec:
    https://www.imsglobal.org/spec/lti-ags/v2p0#line-item-container

    The response is typically a JSON array of line item objects. Each
    line item has at minimum:
        - id:           Full LTI URL of the line item
        - scoreMaximum: Maximum score
        - label:        Human-readable title
        - endDateTime:  (optional) Due date

    Output is normalized to match the Canvas cleaner so downstream
    consumers can treat them identically:
        - id:       Short identifier (trailing URL segment)
        - lti_id:   Original full LTI URL
        - title:    Human-readable name (copied from label)
    '''
    line_items = schoology_json
    if not isinstance(line_items, list):
        # The AGS spec says the response is a JSON array, but some
        # platforms wrap it. Try common wrapper keys.
        for key in ('lineItems', 'line_items', 'body'):
            candidate = schoology_json.get(key)
            if isinstance(candidate, list):
                line_items = candidate
                break
        else:
            line_items = []

    normalized = []
    for item in line_items:
        if not isinstance(item, dict):
            continue

        raw_id = item.get('id')
        short_id = _extract_id_from_lti_url(raw_id)

        entry = dict(item)
        entry['lti_id'] = raw_id
        entry['id'] = short_id

        # Normalize label → title for cross-provider consistency
        if 'label' in entry and 'title' not in entry:
            entry['title'] = entry['label']

        normalized.append(entry)

    # Sort by due date when available, fall back to label/title
    normalized.sort(
        key=lambda x: x.get('endDateTime', x.get('label', x.get('title', 'ZZ')))
    )
    return normalized


# ---------------------------------------------------------------------------
# Assignment results / assigned docs (AGS results)
# ---------------------------------------------------------------------------

def _extract_google_doc_id(url):
    '''
    Extract a Google Doc/Drive file ID from a URL.

    Supports:
        - https://docs.google.com/document/d/DOCID/...
        - https://drive.google.com/file/d/FILEID/...
        - https://docs.google.com/spreadsheets/d/DOCID/...
        - https://docs.google.com/presentation/d/DOCID/...

    Returns the ID string or None.
    '''
    if not isinstance(url, str):
        return None
    match = re.search(
        r'(?:docs|drive)\.google\.com/'
        r'(?:document|file|spreadsheets|presentation)/d/'
        r'([a-zA-Z0-9_-]+)',
        url
    )
    return match.group(1) if match else None


def _extract_google_doc_attachments(result):
    '''
    Pull Google Doc references out of an LTI AGS result object.

    LTI AGS results don't have a standardized attachments field, but
    Schoology (and other LMS platforms) may include submission data in
    various shapes:

    1. ``submission.attachments[].driveFile`` — same as Google Classroom
    2. ``attachments[]`` with a ``url`` pointing to docs.google.com
    3. Schoology-specific fields like ``download_path``
    4. ``comment`` field that may contain Google Doc URLs

    Returns a list of dicts: ``{id, title, alternateLink}``
    '''
    docs = []
    seen_ids = set()

    # Collect all possible attachment lists
    attachment_sources = []

    # Top-level attachments
    top_attachments = result.get('attachments', [])
    if isinstance(top_attachments, list):
        attachment_sources.append(top_attachments)

    # Nested under submission (Google Classroom style)
    submission = result.get('submission', result.get('assignmentSubmission', {}))
    if isinstance(submission, dict):
        sub_attachments = submission.get('attachments', [])
        if isinstance(sub_attachments, list):
            attachment_sources.append(sub_attachments)

    for attachments in attachment_sources:
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            # Google Classroom / LTI driveFile style
            if 'driveFile' in attachment:
                drive_file = attachment['driveFile']
                doc_id = drive_file.get('id')
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    docs.append(drive_file)
                continue

            # URL-based: check all URL-like fields
            url_fields = ['url', 'download_path', 'converted_download_path', 'alternateLink']
            for field in url_fields:
                url = attachment.get(field, '')
                doc_id = _extract_google_doc_id(url)
                if doc_id and doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    docs.append({
                        'id': doc_id,
                        'title': attachment.get('title', attachment.get('filename', '')),
                        'alternateLink': url,
                    })
                    break  # Found a doc in this attachment, move on

    # Also scan the comment field for Google Doc URLs
    comment = result.get('comment', '')
    if isinstance(comment, str):
        for match in re.finditer(
            r'(https?://(?:docs|drive)\.google\.com/'
            r'(?:document|file|spreadsheets|presentation)/d/'
            r'[a-zA-Z0-9_-]+[^\s]*)',
            comment
        ):
            url = match.group(1)
            doc_id = _extract_google_doc_id(url)
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                docs.append({
                    'id': doc_id,
                    'title': '',
                    'alternateLink': url,
                })

    return docs


@register_cleaner('assignment_results', 'assigned_docs')
async def clean_assigned_docs(schoology_json):
    '''
    TODO we need to test this function with schoology

    Extract per-student Google Doc attachments from LTI AGS results
    for a single assignment.

    LTI AGS results spec:
    https://www.imsglobal.org/spec/lti-ags/v2p0#result-service

    Output matches Google Classroom's ``assigned_docs`` cleaner::

        [
            {
                "user_id": "...",
                "documents": [
                    {"id": "...", "title": "...", "alternateLink": "..."}
                ]
            },
            ...
        ]
    '''
    results = schoology_json
    if not isinstance(results, list):
        for key in ('results', 'body'):
            candidate = schoology_json.get(key)
            if isinstance(candidate, list):
                results = candidate
                break
        else:
            results = []

    # Each AGS result identifies the user via ``userId`` — this is the
    # same LTI user ID we see in NRPS membership records.  We need to
    # map these back to internal Learning Observer IDs.
    #
    # Strategy: look up by email when available (consistent with roster
    # cleaner), fall back to schoology-{lti_user_id}.

    # Build list of emails for batch lookup
    emails = []
    lti_user_ids = []
    for result in results:
        if not isinstance(result, dict):
            emails.append('')
            lti_user_ids.append(None)
            continue
        emails.append(result.get('email', result.get('userEmail', '')))
        lti_user_ids.append(result.get('userId', result.get('user_id')))

    google_ids = await util.lookup_gids_by_emails(emails)

    cleaned = []
    for result, google_id, lti_user_id in zip(results, google_ids, lti_user_ids):
        if not isinstance(result, dict):
            continue

        local_id = google_id
        if not local_id and lti_user_id:
            local_id = f'schoology-{lti_user_id}'
        if not local_id:
            continue

        docs = _extract_google_doc_attachments(result)

        cleaned.append({
            constants.USER_ID: local_id,
            'documents': docs,
        })

    return cleaned
