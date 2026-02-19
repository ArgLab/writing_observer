'''
This is an interface to AWE_Workbench.
'''

import asyncio
import enum
import functools
import multiprocessing
import os
import pmss
import time

from concurrent.futures import ProcessPoolExecutor
from learning_observer.log_event import debug_log
from learning_observer.util import timestamp, timeparse

import spacy
import coreferee
import spacytextblob.spacytextblob
import awe_components.components.lexicalFeatures
import awe_components.components.syntaxDiscourseFeats
import awe_components.components.viewpointFeatures
import awe_components.components.lexicalClusters
import awe_components.components.contentSegmentation
import json
import warnings

import writing_observer.nlp_indicators
import learning_observer.kvs
import learning_observer.paths
import learning_observer.settings
import learning_observer.util


SPACY_PREFERENCE = {
    'require': spacy.require_gpu,
    'prefer': spacy.prefer_gpu,
    'none': lambda: None
}

pmss.parser('spacy_gpu_preference', parent='string', choices=['require', 'prefer', 'none'], transform=None)
pmss.register_field(
    name='spacy_gpu_preference',
    type='spacy_gpu_preference',
    description='Determine if we should use the GPU for Spacy or not.\n'\
                '`require`: use GPU for spacy operations, raises error if GPU is not preset.\n'\
                '`prefer`: uses GPU, if available, for spacy operations, otherwise use CPU.\n'\
                '`none`: use CPU for spacy operations.',
    default='none'
)

RUN_MODES = enum.Enum('RUN_MODES', 'MULTIPROCESSING SERIAL')


def init_nlp():
    '''
    Initialize the spacy pipeline with the AWE components. This takes a while
    to run.
    '''
    gpu_preference = learning_observer.settings.pmss_settings.spacy_gpu_preference()
    debug_log(f'Spacy GPU preference set to {gpu_preference}.')
    SPACY_PREFERENCE[gpu_preference]()

    warnings.filterwarnings('ignore', category=UserWarning, module='nltk')
    try:
        nlp = spacy.load("en_core_web_lg")
    except OSError as e:
        error_text = 'There was an issue loading `en_core_web_lg` from spacy. '\
                     '`awe_components` requires various models to operate properly. '\
                     f'Run `{learning_observer.paths.PYTHON_EXECUTABLE} -m awe_components.setup.data` to install all '\
                     'of the necessary models.'

        a = input('Spacy model `en_core_web_lg` not available. Would you like to download? (y/n)')
        if a.strip().lower() not in ['y', 'yes']:
            raise OSError(error_text) from e
        import awe_components.setup.data
        awe_components.setup.data.download_models()
        nlp = spacy.load('en_core_web_lg')

    # Adding all of the components, since
    # each of them turns out to be implicated in
    # the demo list. I note below which ones can
    # be loaded separately to support specific indicators.
    nlp.add_pipe('coreferee')
    nlp.add_pipe('spacytextblob')
    nlp.add_pipe('lexicalfeatures')
    nlp.add_pipe('syntaxdiscoursefeatures')
    nlp.add_pipe('viewpointfeatures')
    nlp.add_pipe('lexicalclusters')
    nlp.add_pipe('contentsegmentation')
    return nlp


nlp = init_nlp()


def outputIndicator(doc, indicatorName, itype, stype=None, text=None, added_filter=None):
    '''
    A function to output three types of information: summary metrics,
    lists of textual information selected by the indicator, and
    the offset information for each word or span selected by the indicator
    '''

    indicator = {}

    if added_filter is None:
        theFilter = [(indicatorName, [True]), ('is_alpha', [True])]
    else:
        theFilter = added_filter
        theFilter.append(('is_alpha', [True]))

    indicator['metric'] =\
        doc._.AWE_Info(infoType=itype,
                       indicator=indicatorName,
                       filters=theFilter,
                       summaryType=stype)

    data = json.loads(
        doc._.AWE_Info(infoType=itype,
                       indicator=indicatorName,
                       filters=theFilter)).values()

    indicator['offsets'] = \
        [[entry['offset'], entry['length']] for entry in data]

    if itype == 'Token':
        indicator['text'] = \
            json.loads(doc._.AWE_Info(infoType=itype,
                                      indicator=indicatorName,
                                      filters=theFilter,
                                      transformations=['lemma'],
                                      summaryType='uniq'))
    else:
        indicator['text'] = []

        for span in indicator['offsets']:
            indicator['text'].append(text[int(span[0]):int(span[0]) + int(span[1])])

    return indicator


def process_text(text, options=None):
    '''
    This will extract a dictionary of metadata using Paul's AWE Workbench code.
    '''
    doc = nlp(text)
    results = {}

    if options is None:
        # Do we want options to be everything initially or nothing?
        options = writing_observer.nlp_indicators.INDICATORS.keys()

    for item in options:
        if item not in writing_observer.nlp_indicators.INDICATORS:
            continue
        indicator = writing_observer.nlp_indicators.INDICATORS[item]
        (id, label, infoType, select, filterInfo, summaryType, category) = indicator
        results[id] = outputIndicator(doc, select, infoType, stype=summaryType, text=text, added_filter=filterInfo)
        results[id].update({
            "label": label,
            "type": infoType,
            "name": id,
            "summary_type": summaryType
        })
    return results


async def process_texts_serial(texts, options=None):
    '''
    Process a list of texts, in serial.

    For testing / debugging, this will process a single essay. Note that while
    labeled async, it's not. If run on the server, it will lock up the main
    Python process.
    '''
    annotated = []
    for text in texts:
        print(text)
        annotations = process_text(text, options)
        annotations['text'] = text
        annotated.append(annotations)

    return annotated


executor = None


def run_in_fork(func):
    '''
    This will run a function in a forked subproces, for isolation.

    I wanted to check if this would solve a bug. It didn't.
    '''
    q = multiprocessing.Queue()
    thread = os.fork()
    if thread != 0:
        print("Awaiting queue")
        return q.get(block=True)
        print("Awaited")
    else:
        print("Queuing")
        q.put(func())
        print("Queued")
        os._exit(0)


async def process_texts_parallel(texts, options=None):
    '''
    This will spin up as many processes as we have cores, and process texts
    in parallel. Note that we should confirm issues of thread safety. If
    Python does this right, this should run in forked environments, and we
    won't run into issues. Otherwise, we'd want to either fork ourselves, or
    understand how well spacy, etc. do with parallelism.
    '''
    global executor
    if executor is None:
        executor = ProcessPoolExecutor()

    loop = asyncio.get_running_loop()
    result_futures = []
    for text in texts:
        processor = functools.partial(process_text, text, options)
        # forked_processor = functools.partial(run_in_fork, processor)
        result_futures.append(loop.run_in_executor(executor, processor))

    annotated = []
    for text, result_future in zip(texts, result_futures):
        try:
            annotations = await result_future
            annotations['text'] = text
        except Exception:
            raise
            annotations = "Error"
        annotated.append(annotations)

    return annotated


async def get_latest_cache_data_for_text(cache, text_hash):
    """
    Cache Helper Function: Returns latest cache for the text hash or initializes key-value pair for that hash if it does not already exist in the cache.
    :param cache: The cache object.
    :param text_hash: The hash of the text.
    :return: The latest cache data for the text hash.
    """
    text_cache_data = await cache[text_hash]
    if text_cache_data is None:
        text_cache_data = {}
    return text_cache_data


async def check_available_features_in_cache(cache, text_hash, requested_features, writing):
    """
    Cache Helper Function : Check if some options are a subset of features_available
    :param cache: The cache object.
    :param text_hash: The hash of the text.
    :param requested_features: The set of requested features.
    :param writing: The writing data.
    :return: A tuple containing the found features and the updated writing data.
    """
    features_available = 'features_available'
    text_cache_data = await get_latest_cache_data_for_text(cache, text_hash)  # Get latest cache
    found_features = set()
    text_cache_data.setdefault(features_available, dict())
    if len(text_cache_data[features_available]) > 0:
        found_features = requested_features.intersection(text_cache_data[features_available].keys())
        writing.update(text_cache_data[features_available])
    return found_features, writing


async def check_and_wait_for_running_features(writing, requested_features, found_features, cache, sleep_interval, wait_time_for_running_features, text_hash):
    """
    Check if some options are a subset of running_features: features that are needed but are already running
    :param writing: The writing data.
    :param requested_features: The set of requested features.
    :param found_features: The found features.
    :param cache: The cache object.
    :param sleep_interval: The time interval in seconds to wait between recurring calls to cache.
    :param wait_time_for_running_features: The time in seconds to wait for features already running.
    :param text_hash: The hash of the text.
    :return: A tuple containing the unfound features, found features, and the updated writing data.
    """
    text_cache_data = await get_latest_cache_data_for_text(cache, text_hash)  # Get latest cache
    running_features = set(json.loads(text_cache_data['running_features'])) if 'running_features' in text_cache_data else set()
    run_successful = False
    unfound_features = requested_features - found_features
    needed_running_features = set()  # Features that are needed but are already processing
    if running_features:
        needed_running_features = unfound_features.intersection(running_features)
    # Recursively check if features have finished processing at a regular interval of sleep_interval
    if len(needed_running_features) > 0:
        while True:
            new_cache = await cache[text_hash]
            if new_cache['stop_time'] != "running":
                run_successful = True
                break
            if (timeparse(timestamp()) - timeparse(new_cache['start_time'])).total_seconds() > wait_time_for_running_features:
                break
            await asyncio.sleep(sleep_interval)
        if run_successful:
            # running_features will be available in features_available after they finish running.
            writing.update(text_cache_data['features_available'])
            found_features = found_features.union(needed_running_features)
    return unfound_features, found_features, writing


async def process_and_cache_missing_features(unfound_features, found_features, requested_features, cache, text_hash, writing):
    """
    Cache Helper: Add not found options to running_features and update cache.
    :param unfound_features: The unfound features.
    :param found_features: The found features.
    :param requested_features: The set of requested features.
    :param cache: The cache object.
    :param text_hash: The hash of the text.
    :param writing: The writing data.
    :return: The updated writing data.
    """
    unfound_features = requested_features - found_features
    running_features = unfound_features
    temp_cache_dict = {'running_features': json.dumps(list(running_features)),
                       'start_time': timestamp(),
                       'stop_time': "running"}
    
    text_cache_data = await get_latest_cache_data_for_text(cache, text_hash)  # Get latest cache
    text_cache_data.update(temp_cache_dict)
    text_cache_data.setdefault('features_available', dict())
    await cache.set(text_hash, text_cache_data)
    
    annotated_text = process_text(writing.get("text", ""), list(unfound_features))
    text_cache_data['running_features'] = json.dumps([])
    text_cache_data['stop_time'] = timestamp()
    text_cache_data['features_available'].update(annotated_text)
    writing.update(annotated_text)
    await cache.set(text_hash, text_cache_data)
    return writing


async def process_writings_with_caching(writing_data, options=None, mode=RUN_MODES.MULTIPROCESSING, sleep_interval=1, wait_time_for_running_features=60):
    '''
    Caching:

    1. Create text hash.
    2. Check if hash exist in cache.
    3. Check if some options are a subset of features_available
        * Yes: add the intersection of features_available and options to results
    4. Check if some options are a subset of running_features.
        * Yes:
        a. Wait for running_features to finish.
        b. Update the cache
        c. Add intersection of running_features and Options to results
    5. Check if additional features are required.
        * Yes:
        a. Collect options not covered till now and add to running_features.
        b. Once finished, update cache and return results.

    param writing_data: The writing data.
    :param options: The list of additional features (optional).
    :param mode: The run mode (default: RUN_MODES.MULTIPROCESSING).
    :param sleep_interval: Time in seconds to wait between recurring calls to cache to check if features have finished running, defaults to 1.
    :param wait_time_for_running_features: The time in seconds to wait for features already running (default: 60).
    :return: The results list.
    '''
    results = []
    cache = learning_observer.kvs.KVS()
    requested_features = set(options if options else [])
    processor = {
        RUN_MODES.MULTIPROCESSING: process_texts_parallel,
        RUN_MODES.SERIAL: process_texts_serial
    }

    async for writing in writing_data:
        text = writing.get('text', '')
        if len(text) == 0:
            yield writing
            continue

        # Creating text hash and setting defaults
        text_hash = 'NLP_CACHE_' + learning_observer.util.secure_hash(text.encode('utf-8'))

        # Check if some options are a subset of features_available
        found_features, writing = await check_available_features_in_cache(cache, text_hash, requested_features, writing)
        # If all options were found
        if found_features == requested_features:
            yield writing
            continue

        # Check if some options are a subset of running_features: features that are needed but are already running
        unfound_features, found_features, writing = await check_and_wait_for_running_features(writing, requested_features, found_features, cache, sleep_interval, wait_time_for_running_features, text_hash)
        # If all options are found
        if found_features == requested_features:
            yield writing
            continue

        # Add not found options to running_features and update cache
        yield await process_and_cache_missing_features(unfound_features, found_features, requested_features, cache, text_hash, writing)


if __name__ == '__main__':
    import time
    import writing_observer.sample_essays
    # Run over a sample text
    example_texts = writing_observer.sample_essays.SHORT_STORIES
    t1 = time.time()
    results = process_text(example_texts[0])
    t2 = time.time()
    print(json.dumps(results, indent=2))

    # If we want to save some test data, flip this to True
    if False:
        with open("results.json", "w") as fp:
            json.dump(results, fp, indent=2)
    print("==============")
    results2 = asyncio.run(process_texts_parallel(example_texts[0:8]))
    t3 = time.time()
    results3 = asyncio.run(process_texts_serial(example_texts[0:8]))
    t4 = time.time()
    print(results2)
    print("Single time", t2 - t1)
    print("Parallel time", t3 - t2)
    print("Serial time", t4 - t3)
    print("Note that these results are imperfect -- ")
    print("Errors", len([r for r in results2 if r == "Error"]))
    print("Errors", [r if r == "Error" else "--" for r in results2])