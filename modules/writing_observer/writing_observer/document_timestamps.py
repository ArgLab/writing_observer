import bisect

import learning_observer.communication_protocol.integration


@learning_observer.communication_protocol.integration.publish_function('source_selector')
def select_source(sources, source):
    '''
    Given a variety of sources, pick which source we should use.

    HACK With this as a function, the system will run every node
    available in `sources`. If we created this as a dispatch type
    within the protocol, we could make it so the system only runs
    the requested source node.
    TODO make this a dispatch type within the protocol
    TODO add provenance at this layer. Each source might have a different
    provenance structure. This should create one to use.
    '''
    if source not in sources:
        raise KeyError(f'Source, `{source}`, not found in available sources: {sources.keys()}')
    return sources[source]


@learning_observer.communication_protocol.integration.publish_function('writing_observer.fetch_doc_by_title_text')
async def fetch_doc_by_title_text(document_lists, kwargs=None):
    '''
    Iterate over student document metadata and choose the most recently
    accessed document whose title contains the provided `kwargs.title_text`.
    '''
    if kwargs is None:
        kwargs = {}
    title_text = (kwargs.get('title_text') or '').strip().lower()

    async for student in document_lists:
        docs = student.get('docs', {})
        student['doc_id'] = ''
        if not title_text:
            yield student
            continue

        best_doc_id = ''
        best_last_access = -1
        for doc_id, metadata in docs.items():
            title = str(metadata.get('title', '') or '').lower()
            if title_text not in title:
                continue

            last_access = metadata.get('last_access')
            try:
                last_access = float(last_access)
            except (TypeError, ValueError):
                last_access = -1

            if last_access > best_last_access:
                best_last_access = last_access
                best_doc_id = doc_id

        student['doc_id'] = best_doc_id
        yield student


@learning_observer.communication_protocol.integration.publish_function('writing_observer.fetch_doc_at_timestamp')
async def fetch_doc_at_timestamp(overall_timestamps, kwargs=None):
    '''
    Iterate over a list of students and determine their latest document
    in reference to the `kwargs.requested_timestamp`.

    `requested_timestamp` should be a string of ms since unix epoch
    '''
    if kwargs is None:
        kwargs = {}
    requested_timestamp = kwargs.get('requested_timestamp', None)
    async for student in overall_timestamps:
        timestamps = student.get('timestamps', {})
        student['doc_id'] = ''
        if requested_timestamp is None:
            # perhaps this should fetch the latest doc id instead
            yield student
            continue
        sorted_ts = sorted(timestamps.keys())
        bisect_index = bisect.bisect_right(sorted_ts, requested_timestamp) - 1
        if bisect_index < 0:
            yield student
            continue
        target_ts = sorted_ts[bisect_index]
        student['doc_id'] = timestamps[target_ts]
        yield student
