'''
This file initially intended to handle any aggregators on the system.
We've kind of strayed from that purpose and jammed a bunch of other
code in. 
TODO refractor the code to be more organized
'''
import pmss
import sys
import time

import learning_observer.cache
import learning_observer.communication_protocol.integration
import learning_observer.constants as constants
import learning_observer.kvs
import learning_observer.settings
from learning_observer.stream_analytics.fields import KeyField, KeyStateType, EventField
import learning_observer.stream_analytics.helpers
# import traceback
import learning_observer.util

pmss.register_field(
    name='use_nlp',
    description='Flag for loading in and using AWE Components. These are '\
                'used to extract NLP metrics from text. When enabled, the '\
                'server start-up time takes longer.',
    type=pmss.pmsstypes.TYPES.boolean,
    default=False
)
pmss.register_field(
    name='use_google_documents',
    description="Flag for whether we should fetch the ground truth of a "\
                "document's text from the Google API to fix any errors "\
                "in the reconstruction reducer.",
    type=pmss.pmsstypes.TYPES.boolean,
    default=False
)

def excerpt_active_text(
    text, cursor_position,
    desired_length=103, cursor_target=2 / 3, max_overflow=10,
    cursor_character="❙"
):
    '''
    This function returns a short segment of student text, cutting in a
    sensible way around word boundaries. This can be used for real-time
    typing views.

    `desired_length` is how much text we want.
    `cursor_target` is what fraction of the text should be before the cursor.
    `max_overflow` is how much longer we're willing to go in order to land on
       a word boundary.
    `cursor_character` is what we insert at the boundary. Can be an empty
       string, a nice bit of markup, etc.
    '''
    character_count = len(text)
    before = int(desired_length * 2 / 3)
    # We step backwards and forwards from the cursor by the desired number of characters
    start = max(0, int(cursor_position - before))
    end = min(character_count - 1, start + desired_length)
    # And, if we don't have much text after the cursor, we adjust the beginning
    # print(start, cursor_position, end)
    start = max(0, end - desired_length)
    # Split on a word boundary, if there's one close by
    # print(start, cursor_position, end)
    while end < character_count and end - start < desired_length + 10 and not text[end].isspace():
        end += 1

    # print(start, cursor_position, end)
    while start > 0 and end - start < desired_length + 10 and not text[start].isspace():
        start -= 1

    clipped_text = text[start:max(cursor_position - 1, 0)] + cursor_character + text[max(cursor_position - 1, 0):end]
    return clipped_text


def sanitize_and_shrink_per_student_data(student_data):
    '''
    This function is run over the data for **each student**, one-by-one.

    We:
    * Compute text length
    * Cut down the text to just what the client needs to receive (we
      don't want to send 30 full essays)
    '''
    text = student_data.get('writing_observer.writing_analysis.reconstruct', {}).get('text', None)
    if text is None:
        student_data['writing_observer_compiled'] = {
            "text": "[None]",
            "character_count": 0
        }
        return student_data

    character_count = len(text)
    cursor_position = student_data['writing_observer.writing_analysis.reconstruct']['position']

    # Yes, this does mutate the input. No, we should. No, it doesn't matter, since the
    # code needs to move out of here. Shoo, shoo.
    student_data['writing_observer_compiled'] = {
        "text": excerpt_active_text(text, cursor_position),
        "character_count": character_count
    }
    # Remove things which are too big to send back. Note: Not benchmarked, so perhaps not too big
    del student_data['writing_observer.writing_analysis.reconstruct']['text']
    # We should downsample, rather than removing
    del student_data['writing_observer.writing_analysis.reconstruct']['edit_metadata']
    return student_data


def aggregate_course_summary_stats(student_data):
    '''
    Here, we compute summary stats across the entire course. This is
    helpful so that the front end can know, for example, how to render
    axes.

    Right now, this API is **evolving**. Ideally, we'd like to support:

    - Transforming summarized per-student data based on data from
      other students
    - Extract aggregates

    This API lets us do that, but it's a little too generic. We'd like
    to be a little bit more semantic.
    '''
    max_idle_time = 0
    max_time_on_task = 0
    max_character_count = 0
    for student in student_data:
        max_character_count = max(
            max_character_count,
            student.get('writing_observer_compiled', {}).get('character_count', 0)
        )
        max_time_on_task = max(
            max_time_on_task,
            student.get('writing_observer.writing_analysis.time_on_task', {}).get("total_time_on_task", 0)
        )
    return {
        "summary_stats": {
            'max_character_count': max_character_count,
            'max_time_on_task': max_time_on_task,
            # TODO: Should we aggregate this in some way? If we run on multiple servers,
            # this is susceptible to drift. That could be jarring; even a few seconds
            # error could be an issue in some contexts.
            'current_time': time.time()
        }
    }


######
#
#  Everything from here on is a hack.
#  We need to figure out proper abstractions.
#
######


async def get_latest_student_documents(student_data):
    '''
    This will retrieve the latest student documents from the database. It breaks
    abstractions.

    It also involves some excess loops that are annoying but briefly we need to
    determine which students actually *have* last writing data. Then we need to
    go through and build keys for that data.  Then we fetch the data itself.
    Later on in this file we need to marry the information again.  This builds
    up a series of lists which are successively merged into a single dict with
    the resulting data.

    Some of what is copied along is clearly duplicative and probably unneeded.
    '''
    import learning_observer.kvs

    import writing_observer.writing_analysis
    from learning_observer.stream_analytics.fields import KeyField, KeyStateType, EventField

    kvs = learning_observer.kvs.KVS()

    # Compile a list of the active students.
    active_students = [s for s in student_data if 'writing_observer.writing_analysis.last_document' in s]

    # Now collect documents for all of the active students.
    document_keys = ([
        learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.reconstruct,
            {
                KeyField.STUDENT: s[constants.USER_ID],
                EventField('doc_id'): get_last_document_id(s)
            },
            KeyStateType.INTERNAL
        ) for s in active_students])

    kvs_data = await kvs.multiget(keys=document_keys)

    # Return blank entries if no data, rather than None. This makes it possible
    # to use item.get with defaults sanely.  For the sake of later alignment
    # we also zip up the items with the keys and users that they come from
    # this hack allows us to align them after cleaning occurrs later.
    # writing_data = [{} if item is None else item for item in writing_data]
    writing_data = []
    for idx in range(len(document_keys)):
        student = active_students[idx]
        doc = kvs_data[idx]

        # If we have an empty item we simply return an empty dict with the
        # student but an empty doc value.
        if (doc is None):
            doc = {}

        # Now insert the student data and pass it along.
        doc['student'] = student
        writing_data.append(doc)

    return writing_data


async def remove_extra_data(writing_data):
    '''
    We don't want Deane graph data going to the client. We just do a bit of
    a cleanup. This is in-place.
    '''
    for item in writing_data:
        if 'edit_metadata' in item:
            del item['edit_metadata']
    return writing_data


async def merge_with_student_data(writing_data, student_data):
    '''
    Add the student metadata to each text
    '''

    for item, student in zip(writing_data, student_data):
        if 'edit_metadata' in item:
            del item['edit_metadata']
        item['student'] = student
    return writing_data


# TODO the use_nlp initialization code ought to live in a
# registered startup function
use_nlp = learning_observer.settings.module_setting('writing_observer', 'use_nlp')
if use_nlp:
    try:
        import writing_observer.awe_nlp
        processor = writing_observer.awe_nlp.process_writings_with_caching
    except ImportError as e:
        print(e)
        print('AWE Components is not installed. To install, please see https://github.com/ETS-Next-Gen/AWE_Components')
        sys.exit(-1)
else:
    import writing_observer.stub_nlp
    processor = writing_observer.stub_nlp.process_texts

processor = learning_observer.communication_protocol.integration.publish_function('writing_observer.process_texts')(processor)


@learning_observer.communication_protocol.integration.publish_function('writing_observer.update_reconstruct_with_google_api')
async def update_reconstruct_reducer_with_google_api(runtime, doc_ids):
    """
    This method updates the reconstruct reducer every so often with the ground
    truth directly from the Google API. This allows us to automatically fix
    errors introduced by the reconstruction. If the current user does not have
    access to the ground truth (e.g. permission), then we do not update the
    reconstruct reducer.

    This method is intended for use within the communication protocol.
    Since we already select reconstruct data from the KVS, this method just
    updates the KVS and returns the data we input, `doc_ids`, without modification.

    We use a closure here to make use of memoization so we do not update the KVS
    every time we call this method.
    """

    @learning_observer.cache.async_memoization()
    async def fetch_doc_from_google(student, doc_id):
        """
        This method performs the fetching of current document text and the
        updating of the KVS.
        """
        if student is None or doc_id is None or len(doc_id) == 0:
            return None
        import learning_observer.google

        kvs = learning_observer.kvs.KVS()

        text = await learning_observer.google.doctext(runtime, documentId=doc_id)
        # Only update Redis is we have text available. If `text` is missing, then
        # we likely encountered an error, usually related to document permissions.
        if 'text' not in text:
            return None
        key = learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.reconstruct,
            {
                KeyField.STUDENT: student,
                EventField('doc_id'): doc_id
            },
            KeyStateType.INTERNAL
        )
        await kvs.set(key, text)
        return text

    fetch_from_google_documents = learning_observer.settings.module_setting('writing_observer', 'use_google_documents')
    async for d in doc_ids:
        if fetch_from_google_documents:
            await fetch_doc_from_google(
                learning_observer.util.get_nested_dict_value(d, 'provenance.provenance.STUDENT.value.user_id'),
                learning_observer.util.get_nested_dict_value(d, 'doc_id')
            )
        yield d


def get_last_document_id(s):
    """
    Retrieves the ID of the latest document for a given student.
    :param s: The student data.
    :return: The ID of the latest document.
    """
    return s.get('writing_observer.writing_analysis.last_document', {}).get('document_id', None)


async def update_reconstruct_data_with_google_api(runtime, student_data):
    """
    This function updates the text reconstruction writing data from the extension with the
    ground truth data from the Google Docs API.
    :param runtime: The runtime for the application
    :param student_data: A list of students
    :return: A list of writing data, one for each student
    """
    @learning_observer.cache.async_memoization()
    async def fetch_doc_from_google(student):
        """
        This function retrieves a single document text from Google based on the document ID.
        :param student: A student object
        :return: The text of the latest document
        """
        import learning_observer.google

        kvs = learning_observer.kvs.KVS()

        docId = get_last_document_id(student)
        # fetch text
        text = await learning_observer.google.doctext(runtime, documentId=docId)
        # set reconstruction data to ground truth
        key = learning_observer.stream_analytics.helpers.make_key(
            writing_observer.writing_analysis.reconstruct,
            {
                KeyField.STUDENT: student[constants.USER_ID],
                EventField('doc_id'): docId
            },
            KeyStateType.INTERNAL
        )
        await kvs.set(key, text)
        return text

    # For each student, retrieve the document text from Google and store it in a list
    writing_data = [
        await fetch_doc_from_google(s)
        if get_last_document_id(s) is not None else {}
        for s in student_data
    ]
    return writing_data


# TODO This is old way of querying data from the system.
# The code should all still function, but the proper way to
# do this is using the Communication Protocol.
# This function and any references should be removed.
async def latest_data(runtime, student_data, options=None):
    '''
    Retrieves the latest writing data for a set of students.


    :param runtime: The runtime object from the server
    # for annotated_text, single_doc in zip(annotated_texts, writing_data):
    :param student_data: The student data.
    #     if annotated_text != "Error":
    :param options: Additional options to pass to the text processing pipeline.
    #         single_doc.update(annotated_text)
    :return: The latest writing data.
    '''

    # HACK we have a cache downstream that relies on redis_ephemeral being setup
    # when that is resolved, we can remove the feature flag
    # Update reconstruct data from KVS with ground truth from Google API
    if learning_observer.settings.module_setting('writing_observer', 'use_google_documents'):
        await update_reconstruct_data_with_google_api(runtime, student_data)

    # Get the latest documents with the students appended.
    writing_data = await get_latest_student_documents(student_data)

    # Strip out the unnecessary extra data.
    writing_data = await remove_extra_data(writing_data)

    # print(">>> WRITE DATA-premerge: {}".format(writing_data))

    # This is the error.  Skipping now.
    writing_data_merge = await merge_with_student_data(writing_data, student_data)
    # print(">>> WRITE DATA-postmerge: {}".format(writing_data_merge))

    # #print(">>>> PRINT WRITE DATA: Merge")
    # #print(writing_data)

    # just_the_text = [w.get("text", "") for w in writing_data]

    # annotated_texts = await writing_observer.awe_nlp.process_texts_parallel(just_the_text)

    # for annotated_text, single_doc in zip(annotated_texts, writing_data):
    #     if annotated_text != "Error":
    #         single_doc.update(annotated_text)

    writing_data = await merge_with_student_data(writing_data, student_data)
    writing_data = await processor(writing_data, options)

    return {'latest_writing_data': writing_data}


@learning_observer.communication_protocol.integration.publish_function('google.fetch_assignment_docs')
async def fetch_assignment_docs(runtime, course_id, kwargs=None):
    '''
    Invoke the Google API to retrieve a list of students, where each student possesses a
    collection of documents associated with the specified assignment.

    I wasn't sure where to put this code, so I just tossed it here for now.
    This entire file needs a bit of reworking, what's a little more?
    '''
    if kwargs is None:
        kwargs = {}
    assignment_id = kwargs.get('assignment')
    output = []
    if assignment_id:
        output = await learning_observer.google.assigned_docs(runtime, courseId=course_id, courseWorkId=assignment_id)
    async for student in learning_observer.util.ensure_async_generator(output):
        s = {}
        s['doc_id'] = student['documents'][0]['id']
        # HACK a piece above the source selector in the communication protocol
        # expects all items returned to have the same provenance. This mirrors
        # the provenance that will be returned by the other sources.
        # TODO modify the source selector to handle the provenance
        provenance = {
            'provenance': {'STUDENT': {
                'value': {'user_id': student['user_id']},
                'user_id': student['user_id']
            }}
        }
        s['provenance'] = provenance
        yield s
