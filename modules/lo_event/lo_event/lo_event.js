/*
  Logging library for Learning Observer clients
*/

import { timestampEvent, mergeMetadata } from './util.js';
import { getBrowserInfo } from './metadata/browserinfo.js';
import * as Queue from './queue.js';
import * as disabler from './disabler.js';
import * as debug from './debugLog.js';
import * as util from './util.js';

export const QueueType = Queue.QueueType;

// We implement this as something like an FSM.
const INIT_STATES = {
  NOT_STARTED: 'NOT_STARTED', // init() has not been called
  IN_PROGRESS: 'IN_PROGRESS', // init() called, but waiting on loggers or metadata
  LOGGERS_READY: 'LOGGERS_READY', // loggers initialized, but queuing initial events / auth
  READY: 'READY', // Events streaming to loggers (which might have their own queues)
  ERROR: 'ERROR' // Something went very, very wrong
};

let initialized = INIT_STATES.NOT_STARTED; // Current FSM state
let currentState = new Promise((resolve, reject) => { resolve(); }); // promise pipeline to ensure we handle all initialization


let loggersEnabled = []; // A list of all loggers which should receive events.
let queue;

function isInitialized () {
  return initialized === INIT_STATES.READY;
}

/**
 * Collect all enabled loggers with an init function, call it,
 * and wait for all of them to finish initializing. We add this
 * function to our `currentState` pipeline to ensure loggers
 * are ready to go before we send events.
 */
async function initializeLoggers () {
  debug.info('initializing loggers');
  const initializedLoggers = loggersEnabled
    .filter(logger => typeof logger.init === 'function') // Filter out loggers without .init property
    .map(logger => logger.init()); // Call .init() on each logger, which may return a promise

  try {
    await Promise.all(initializedLoggers);
    debug.info('Loggers initialized!');
    initialized = INIT_STATES.LOGGERS_READY;
  } catch (error) {
    initialized = INIT_STATES.ERROR;
    debug.error('Error resolving logger initializers:', error);
  }
}

/**
 * Executes and compiles metadata tasks into a single metadata object.
 *
 * When initializing `lo_event`, clients can set which metadata items
 * they wish to include.
 */
export async function compileMetadata(metadataTasks) {
  const taskPromises = metadataTasks.map(async task => {
    try {
      const result = await Promise.resolve(task.func());
      return { [task.name]: result };
    } catch (error) {
      debug.error(`Error in initialization task ${task.name}:`, error);
      return null;
    }
  });

  const results = await Promise.all(taskPromises);
  setFieldSet(results);
  return results.filter(Boolean);
}


/**
 * Set specific key/value pairs using the `lock_fields`
 * event. We use this to set specific fields that we want
 * included overall for subsequent events to prevent
 * sending the same information in each event.
 *
 * This is useful for items such as `source` and `version`
 * which should be the same for every event.
 *
 * This function works even after we are initialized and
 * processing items from the queue (INIT_STATES.READY).
 *
 * Each individual logger should keep track of state and
 * handle their respecitive reconnects properly.
 */
export function setFieldSet (data) {
  currentState = currentState.then(
    () => setFieldSetAsync(data)
  );
}

/**
 * Runs and awaits for all loggers to run their `setField` command
 */
async function setFieldSetAsync (data) {
  const payload = { fields: await mergeMetadata(data), event: 'lock_fields' };
  timestampEvent(payload);
  const authpromises = loggersEnabled
    .filter(logger => typeof logger.setField === 'function')
    .map(logger => logger.setField(JSON.stringify(payload)));

  await Promise.all(authpromises);
}

// TODO: We should consider specifying a set of verbs, nouns, etc. we
// might use, and outlining what can be expected in the protocol
// TODO: We should consider structing / destructing here
export function init (
  source,
  version,
  loggers, // e.g. [console_logger(), websocket_logger("/foo/bar")]
  {
    debugLevel = debug.LEVEL.NONE,
    debugDest = [debug.LOG_OUTPUT.CONSOLE],
    useDisabler = true,
    queueType = Queue.QueueType.AUTODETECT,
    sendBrowserInfo = false,
    verboseEvents = false,
    metadata = [],
  } = {}
) {
  if (!source || typeof source !== 'string') throw new Error('source must be a non-null string');
  if (!version || typeof version !== 'string') throw new Error('version must be a non-null string');

  util.setVerboseEvents(verboseEvents);
  queue = new Queue.Queue('LOEvent', { queueType });

  debug.setLevel(debugLevel);
  debug.setLogOutputs(debugDest);
  if (useDisabler) {
    currentState = currentState.then(() => disabler.init(useDisabler));
  }

  loggersEnabled = loggers;
  initialized = INIT_STATES.IN_PROGRESS;
  currentState = currentState
    .then(initializeLoggers)
    .then(() => setFieldSet([{ source, version }]))
    .then(() => compileMetadata(metadata));
  if(sendBrowserInfo) {
    // In the future, some or all of this might be sent on every
    // reconnect
    logEvent("BROWSER_INFO", getBrowserInfo());
  }
}

export function go () {
  currentState.then(() => {
    initialized = INIT_STATES.READY;
    queue.startDequeueLoop({
      initialize: isInitialized,
      shouldDequeue: disabler.retry,
      onDequeue: sendEvent
    });
  });
}

function sendEvent (event) {
  const jsonEncodedEvent = JSON.stringify(event);
  for (const logger of loggersEnabled) {
    try {
      logger(jsonEncodedEvent);
    } catch (error) {
      if (error instanceof disabler.BlockError) {
        // Handle BlockError exception here
        disabler.handleBlockError(error);
      } else {
        // Other types of exceptions will propagate up
        throw error;
      }
    }
  }
}

export function logEvent (eventType, event) {
  // opt out / dead
  if (!disabler.storeEvents()) {
    return;
  }
  event.event = eventType;
  timestampEvent(event);

  queue.enqueue(event);
}

/**
 * We would like to be able to log events roughly following the xAPI
 * conventions (and possibly Caliper conventions). This allows us to
 * explicitly structure events with the same fields as xAPI, and
 * might have validation logic in the future. However, we have not
 * figured out the best way to do this, so please treath this as
 * stub / in-progress code.
 *
 * In the long term, we'd like to be as close to standards as possible.
 */
export function logXAPILite (
  {
    verb,
    object,
    result,
    context,
    attachments
  }
) {
  logEvent(verb,
    { object, result, context, attachments }
  );
}
