'''
Google-specific API module for Learning Observer.

This module provides access to various Google APIs (Classroom, Drive, Docs, etc.)
using the generic API infrastructure.

The module provides:
- Raw data access to Google APIs
- Cleaned data from Google APIs in standardized formats
- Both web API routes and in-process function calls
'''

import itertools
import json
import re

import learning_observer.constants as constants
import learning_observer.auth
import learning_observer.kvs
import learning_observer.prestartup
import learning_observer.settings as settings
import learning_observer.util

from . import util


# Cache for Google API responses
cache = None

# Google field name mapping
GOOGLE_FIELDS = [
    'alternateLink', 'calculationType', 'calendarId', 'courseGroupEmail',
    'courseId', 'courseState', 'creationTime', 'descriptionHeading',
    'displaySetting', 'emailAddress', 'enrollmentCode', 'familyName',
    'fullName', 'givenName', 'gradebookSettings', 'guardiansEnabled',
    'ownerId', 'photoUrl', 'teacherFolder', 'teacherGroupEmail', 'updateTime',
    'userId'
]

# Convert Google's CamelCase to LO's snake_case
camel_to_snake = re.compile(r'(?<!^)(?=[A-Z])')
GOOGLE_TO_SNAKE = {field: camel_to_snake.sub('_', field).lower() for field in GOOGLE_FIELDS}

# API endpoint definitions
ENDPOINTS = list(map(lambda x: util.Endpoint(*x, api_name='google'), [
    ("document", "https://docs.googleapis.com/v1/documents/{documentId}"),
    ("course_list", "https://classroom.googleapis.com/v1/courses"),
    ("course_roster", "https://classroom.googleapis.com/v1/courses/{courseId}/students"),
    ("course_work", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork"),
    ("coursework_submissions", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWork/{courseWorkId}/studentSubmissions"),
    ("coursework_materials", "https://classroom.googleapis.com/v1/courses/{courseId}/courseWorkMaterials"),
    ("course_topics", "https://classroom.googleapis.com/v1/courses/{courseId}/topics"),
    ("drive_files", "https://www.googleapis.com/drive/v3/files"),    # This paginates. We only return page 1.
    ("drive_about", "https://www.googleapis.com/drive/v3/about?fields=%2A"),  # Fields=* probably gives us more than we need
    ("drive_comments", "https://www.googleapis.com/drive/v3/files/{documentId}/comments?fields=%2A&includeDeleted=true"),
    ("drive_revisions", "https://www.googleapis.com/drive/v3/files/{documentId}/revisions")
]))

# Create a register_cleaner function specific to Google ENDPOINTS
register_cleaner = util.make_cleaner_registrar(ENDPOINTS)


@learning_observer.prestartup.register_startup_check
def connect_to_google_cache():
    '''Setup cache for requests to the Google API.
    The cache is currently only used with the `use_google_ajax`
    feature flag.
    '''
    if not settings.feature_flag('google_routes'):
        return

    for key in ['save_google_ajax', 'use_google_ajax', 'save_clean_ajax', 'use_clean_ajax']:
        if settings.feature_flag(key):
            global cache
            try:
                cache = learning_observer.kvs.KVS.google_cache()
            except AttributeError:
                error_text = 'The google_cache KVS is not configured.\n'\
                    'Please add a `google_cache` kvs item to the `kvs` '\
                    'key in `creds.yaml`.\n'\
                    '```\ngoogle_cache:\n  type: filesystem\n  path: ./learning_observer/static_data/google\n'\
                    '  subdirs: true\n```\nOR\n'\
                    '```\ngoogle_cache:\n  type: redis_ephemeral\n  expiry: 600\n```'
                raise learning_observer.prestartup.StartupCheck("Google KVS: " + error_text)


def register_endpoints(app):
    '''
    Initialize Google API routes and register them with the app.
    This function sets up all the raw and cleaner functions for Google APIs.
    '''
    if not settings.feature_flag('google_routes'):
        return

    # Create the API routes and get back the functions
    return util.register_endpoints(
        app=app,
        endpoints=ENDPOINTS,
        api_name='google',
        key_translator=GOOGLE_TO_SNAKE,
        cache=cache,
        cache_key_prefix='raw_google',
        feature_flag_name='google_routes'
    )


# ===== CLEANERS =====

# Rosters
@register_cleaner("course_roster", "roster")
def clean_course_roster(google_json):
    '''
    Retrieve the roster for a course, alphabetically
    '''
    students = google_json.get('students', [])
    students.sort(
        key=lambda x: x.get('name', {}).get('fullName', 'ZZ'),
    )
    # Convert Google IDs to internal ideas (which are the same, but with a gc- prefix)
    for student_json in students:
        google_id = student_json['profile']['id']
        local_id = learning_observer.auth.google_id_to_user_id(google_id)
        student_json[constants.USER_ID] = local_id
        del student_json['profile']['id']

        # For the present there is only one external id so we will add that directly.
        if 'external_ids' not in student_json['profile']:
            student_json['profile']['external_ids'] = []
        student_json['profile']['external_ids'].append({"source": "google", "id": google_id})
    return students


@register_cleaner("course_list", "courses")
def clean_course_list(google_json):
    '''
    Google's course list is one object deeper than we'd like, and alphabetic
    sort order is nicer. This will clean it up a bit
    '''
    courses = google_json.get('courses', [])
    courses.sort(
        key=lambda x: x.get('name', 'ZZ'),
    )
    return courses


@register_cleaner('course_work', 'assignments')
def clean_course_work(google_json):
    '''
    Google's course work is one object deeper than we'd like, and update_time
    sort order is nicer. This will clean it up a bit
    '''
    assignments = google_json.get('courseWork', [])
    assignments.sort(
        key=lambda x: x.get('update_time', 0)
    )
    return assignments


# Google Docs
def _force_text_length(text, length):
    '''
    Force text to a given length, either concatenating or padding

    >>> force_text_length("Hello", 3)
    >>> 'Hel'

    >>> force_text_length("Hello", 13)
    >>> 'Hello        '
    '''
    return text[:length] + " " * (length - len(text))


def get_error_details(error):
    messages = {
        403: 'Student working on private document.',
        404: 'Unable to fetch document.'
    }
    code = error['code']
    message = messages.get(code, 'Unknown error.')
    return {'error': {'code': code, 'message': message}}


@register_cleaner("document", "doctext")
def extract_text_from_google_doc_json(
        j, align=True,
        EXTRACT_DEBUG_CHECKS=False):
    '''
    Extract text from a Google Docs JSON object, ignoring formatting.

    There is an alignment issue between Google's and Python's handling
    of Unicode. We can either:
    * extract text faithfully (align=False)
    * extract text with aligned indexes by cutting text / adding
      spaces (align=True)

    This issue came up in text with a Russian flag unicode symbol
    (referencing the current conflict). I tried various encodings,
    and none quite matched Google 100%.

    Note that align=True doesn't necessarily give perfect local alignment
    within text chunks, since we do have different lengths for something like
    this flag. It does work okay globally.
    '''
    # return error message for text
    if 'error' in j:
        return get_error_details(j['error'])
    length = j['body']['content'][-1]['endIndex']
    elements = [a.get('paragraph', {}).get('elements', []) for a in j['body']['content']]
    flat = sum(elements, [])
    text_chunks = [f.get('textRun', {}).get('content', '') for f in flat]
    if align:
        lengths = [f.get('endIndex', 0) - f.get('startIndex', 0) for f in flat]
        text_chunks = [_force_text_length(chunk, length) for chunk, length in zip(text_chunks, lengths)]
    text = ''.join(text_chunks)

    if EXTRACT_DEBUG_CHECKS:
        print("Text length versus Google length:")
        print(len(text), length)
        print("We expect these to be off by one, since Google seems to starts at 1 (and Python at 0)")
        if align:
            print
            print("Offsets (these should match):")
            print(list(zip(itertools.accumulate(map(len, text_chunks)), itertools.accumulate(lengths))))

    return {'text': text}


@register_cleaner("coursework_submissions", "assigned_docs")
def clean_assignment_docs(google_json):
    '''
    Retrieve set of documents per student associated with an assignment
    '''
    student_submissions = google_json.get('studentSubmissions', [])
    cleaned_submissions = []
    for student_json in student_submissions:
        google_id = student_json[constants.USER_ID]
        local_id = learning_observer.auth.google_id_to_user_id(google_id)
        docs = [d['driveFile'] for d in learning_observer.util.get_nested_dict_value(student_json, 'assignmentSubmission.attachments', []) if 'driveFile' in d]
        cleaned_submissions.append({
            constants.USER_ID: local_id,
            'documents': docs
        })
    return cleaned_submissions


if __name__ == '__main__':
    import json
    import sys
    j = json.load(open(sys.argv[1]))
    # extract_text_from_google_doc_json(j, align=False, EXTRACT_DEBUG_CHECKS=True)
    # extract_text_from_google_doc_json(j, align=True, EXTRACT_DEBUG_CHECKS=True)
    output = clean_assignment_docs(j)
    print(json.dumps(output, indent=2))
