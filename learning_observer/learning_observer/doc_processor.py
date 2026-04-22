'''This file processes documents through a variety of items.
This is an additional script to start after student writing data
has been populated in the database.

Workflow:
- An initial fetch begins to find all documents.
- Check document against rules
    - If processable: add processing job to loop
        - Fetch text
        - Run through NLP and LanguageTool
        - Store in reducers
- Delay the next fetch.
- As documents finish, they are removed from the loop
'''
import aiohttp_session
import pmss

import learning_observer.auth.utils
import learning_observer.constants
import learning_observer.google
import learning_observer.kvs
import learning_observer.offline
import learning_observer.run
import learning_observer.runtime
import learning_observer.settings
import learning_observer.stream_analytics.helpers as sa_helpers
import learning_observer.util

import writing_observer
import writing_observer.awe_nlp
import writing_observer.languagetool
import writing_observer.writing_analysis

from learning_observer.log_event import debug_log

pmss.register_field(
    name='document_processing_delay_seconds',
    type=pmss.pmsstypes.TYPES.integer,
    description="This determines the amount of time to wait (in seconds) between "\
        "processing a document's text within the separate document processor script.",
    default=90
)

pmss.register_field(
    name='document_processing_semaphore_process_count',
    type=pmss.pmsstypes.TYPES.integer,
    description="This determines the number of semaphores to use when processing "\
        "documents. The default, 0, means we will pass all items to the running "\
        "job loop to run. Using a value > 0 will limit the number of jobs we attempt "\
        "to process at once.",
    default=0
)

'''
TODO add in desired rules.
Each rule should be a function that accepts
a document id.
Rules we want
- [x] document modified since last processing AND
      document not processed in last 5 minutes
- [ ] teacher visited dashboard recently
- [ ] events > 2*[events since last processed]
Start with just the first one
'''

async def _fetch_document_process_data(doc_id, student_id):
    '''Fetch processed data from the document.
    '''
    key = sa_helpers.make_key(
        process_document,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    return await KVS[key]


async def _fetch_document_metadata(doc_id, student_id):
    '''This fetch the time on task reducer which contains
    the one piece of metadata we are after, `saved_ts`. This
    item provides the last time we received an event for the
    document.
    '''
    key = sa_helpers.make_key(
        writing_observer.writing_analysis.time_on_task,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    return await KVS[key]


async def check_recent_mod_and_not_recent_process(doc_id):
    '''Determine if the document has been altered since its last
    processing and check whether it is past a specified cutoff
    time (5 minutes).
    '''
    cutoff = learning_observer.settings.pmss_settings.document_processing_delay_seconds(types=['modules', 'writing_observer'])
    student_id = await _determine_student(doc_id)

    doc_info = await _fetch_document_process_data(doc_id, student_id)

    doc_metadata = await _fetch_document_metadata(doc_id, student_id)
    if doc_metadata is None:
        return False

    now = learning_observer.util.get_seconds_since_epoch()
    last_mod = doc_metadata['saved_ts']

    if doc_info is None: return True

    last_processed = doc_info['last_processed']
    recently_modified = last_mod > last_processed
    recently_processed = now - cutoff < last_processed
    if recently_modified and not recently_processed: return True
    return False


async def check_failed_google_api_fetch(doc_id):
    '''Check to see if the current document has previously been
    unsuccessfully fetched from the Google API. We ignore any
    failed documents.

    TODO this ought to be some exponential backoff function,
    so we do not get flagged by some Google bot.
    '''
    if doc_id in failed_fetch:
        return False
    return True


RULES = [
    check_recent_mod_and_not_recent_process,
    check_failed_google_api_fetch
]

KVS = None
app = None
failed_fetch = set()

# TODO move StubApp, StubRequest, and fetch_mock_runtime to offline.py
class StubApp:
    def __init__(self, loop):
        self.loop = loop

    def add_routes(self, *args):
        pass


class StubRequest(dict):
    pass


def fetch_mock_runtime(creds):
    mock_request = StubRequest()
    mock_request[learning_observer.constants.AUTH_HEADERS] = creds
    mock_request[learning_observer.constants.USER] = {}
    mock_request.app = app
    runtime = learning_observer.runtime.Runtime(mock_request)
    return runtime


async def start():
    learning_observer.offline.init('creds.yaml')
    global app, KVS
    app = StubApp(asyncio.get_event_loop())
    learning_observer.google.initialize_and_register_routes(app)
    KVS = learning_observer.kvs.KVS()

    # overwrite aiohttp_session.get_session so the Google API
    # code does not fail when a session is not there.
    async def get_session(request):
        return {learning_observer.constants.USER: {learning_observer.constants.USER_ID: '12345'}}

    aiohttp_session.get_session = get_session
    await process_documents_with_wait()


async def fetch_all_docs():
    '''Return a set of all doc ids currently available
    within the kvs.
    '''
    doc_ids = set()
    keys = await KVS.keys()
    doc_specifier = 'EventField.doc_id:'
    for k in keys:
        if doc_specifier not in k: continue
        end_of_specifier = k.find(doc_specifier) + len(doc_specifier)
        end_of_id = k.find(',', end_of_specifier)
        doc_id = k[end_of_specifier : end_of_id if end_of_id != -1 else len(k)]
        if doc_id == 'None': continue
        doc_ids.add(doc_id)
    return doc_ids


async def delay_fetch_all_docs(delay=20):
    '''We don't want to be fetching all the docs
    constantly when working in the `asycnio.task` workflow.
    This makes us wait before calling it again.
    '''
    await asyncio.sleep(delay)
    return await fetch_all_docs()


async def process_documents_with_wait():
    '''Continually fetch docs and process them as they are
    available.

    Setting the `writing_observer.document_processing_semaphore_process_count`
    setting will set the max number of docs we process at once.
    '''
    max_concurrent_tasks = learning_observer.settings.pmss_settings.document_processing_semaphore_process_count(types=['modules', 'writing_observer'])
    func_wrapper = lambda func: func
    if max_concurrent_tasks > 0:
        semaphore = asyncio.Semaphore(max_concurrent_tasks)
        async def limited_func(func):
            async with semaphore:
                return await func
        func_wrapper = limited_func
    def create_task(func, name):
        return asyncio.create_task(func_wrapper(func), name=name)

    pending = [create_task(fetch_all_docs(), name='fetch')]
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        d = done.pop()
        if d.get_name() == 'fetch':
            doc_ids = d.result()
            for doc_id in doc_ids:
                if doc_id not in failed_fetch:
                    pending.add(create_task(process_document(doc_id), name=doc_id))
            pending.add(create_task(delay_fetch_all_docs(), name='fetch'))


async def process_documents_with_gather():
    '''Fetch ids and gather all processed documents at once.
    New documents will not be processed until all documents
    on the current while loop iteration have finished.
    '''
    while True:
        doc_ids = await fetch_all_docs()
        results = await asyncio.gather(*(process_document(d) for d in doc_ids))


async def check_rules(rules, doc_id):
    '''Determine if a document passes all of the
    provided rules. This is equivalent to running an
    AND over each of the provided rules.

    TODO support AND and OR statements such as
    AND(rule, rule) and similar
    '''
    for rule in rules:
        if not await rule(doc_id):
            return False
    return True


async def process_document(doc_id):
    if not await check_rules(RULES, doc_id):
        return False
    debug_log('* Processing document:', doc_id)
    doc_text = None
    student_id = await _determine_student(doc_id)
    google_auth = await _fetch_teacher_credentials(student_id)
    # TODO this could be cleaned up
    if google_auth is not None:
        doc_text = await _fetch_doc_text_from_google(doc_id, google_auth, student_id)
    if doc_text is None or len(doc_text) == 0:
        doc_text = await _fetch_doc_text_from_reconstruct(doc_id, student_id)
        if doc_text is None or len(doc_text) == 0:
            failed_fetch.add(doc_id)
            return False
    await _pass_doc_through_analysis(doc_id, doc_text, student_id)

    debug_log('**  Done processing document:', doc_id)

    return True


async def _determine_student(doc_id):
    keys = await KVS.keys()
    matching_keys = [k for k in keys if doc_id in k]
    student_specifier = 'STUDENT:'
    students = [k[k.find(student_specifier) + len(student_specifier):] for k in matching_keys]
    # TODO handle more than 1 student per document, but for now just grab the first
    student = students[0]
    return student


async def _fetch_teacher_credentials(student):
    '''Determine which teacher a document belongs to
    and return the teacher's stored Google auth info
    '''
    keys = await KVS.keys()
    roster_specifier = 'learning_observer.google.roster'
    rosters = [k for k in keys if roster_specifier in k]
    matching_teachers = []
    for roster_key in rosters:
        roster = await KVS[roster_key]
        if student in roster['students']:
            matching_teachers.append(roster['teacher_id'])

    # TODO handle more than 1 teacher per student, but for now just grab the first
    if len(matching_teachers) == 0: return None
    teacher = matching_teachers[0]
    auth_key = sa_helpers.make_key(
        learning_observer.auth.utils.google_stored_auth,
        {sa_helpers.KeyField.TEACHER: teacher},
        sa_helpers.KeyStateType.INTERNAL)
    creds = await KVS[auth_key]
    return creds


async def _fetch_doc_text_from_reconstruct(doc_id, student_id):
    '''Fetch the document text from the reconstruct reducer
    '''
    key = sa_helpers.make_key(
        writing_observer.writing_analysis.reconstruct,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    reconstruct = await KVS[key]
    return reconstruct['text']


async def _fetch_doc_text_from_google(doc_id, creds, student_id):
    '''Fetch the document text from the appropriate
    Google endpoint.
    '''
    runtime = fetch_mock_runtime(creds)
    response = await learning_observer.google.doctext(runtime, documentId=doc_id)
    if 'text' not in response:
        return None

    key = sa_helpers.make_key(
        writing_observer.writing_analysis.reconstruct,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    await KVS.set(key, response)

    return response['text']


async def _pass_doc_through_analysis(doc_id, text, student_id):
    '''Pass the document text through a variety of
    analysis items. This includes,
    - Calculating all AWE components
    - Running through Language Tool
    Then store the documents in the default KVS
    '''
    # Can log above and below these lines for primary processing work.
    awe_output = writing_observer.awe_nlp.process_text(text)
    prep_for_lt = [{'text': text, 'provenance': None}]
    lt_output = await writing_observer.languagetool.process_texts(prep_for_lt)

    output = {
        'document_id': doc_id,
        'student_id': student_id,
        'awe_components': awe_output,
        'languagetool': lt_output,
        'text': text,
        'last_processed': learning_observer.util.get_seconds_since_epoch()
    }
    # Set AWE Components info
    awe_output['text'] = text
    awe_key = sa_helpers.make_key(
        writing_observer.writing_analysis.nlp_components,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )
    await KVS.set(awe_key, awe_output)

    # Set LanguageTool info
    for lt_out in lt_output:
        lt_out['text'] = text
        lt_key = sa_helpers.make_key(
            writing_observer.writing_analysis.languagetool_process,
            {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
            sa_helpers.KeyStateType.INTERNAL
        )
        await KVS.set(lt_key, lt_out)

    # TODO choose a different function. since this is a separate
    # script, we get `Internal,__main__.process_document,...`
    key = sa_helpers.make_key(
        process_document,
        {sa_helpers.EventField('doc_id'): doc_id, sa_helpers.KeyField.STUDENT: student_id},
        sa_helpers.KeyStateType.INTERNAL
    )

    await KVS.set(key, output)


if __name__ == '__main__':
    '''We may want to start this as a process when starting Learning Observer rather than
    a separate Python command.

    TODO specify processes to turn on when starting Learning Observer.
    '''
    import asyncio
    asyncio.run(start())
