/**
 * The debugLog handles formatting and routing debug statements to
 * different logging outputs.
 */

/**
 * Returns a function that will route debugLog events
 * through the `sendEvent` function. This is typically used
 * for sending events through to the current `lo_event` loggers.
 * Events are transmitted when the count of a specific event
 * type reaches a power of 10.
 *
 * @param {*} sendEvent a `function(event_type, message)` to route events to
 * @returns a function to log events
 */
function sendEventToLogger (sendEvent) {
  const counts = {};
  return function (messageType, message, stackTrace) {
    if (!Object.prototype.hasOwnProperty.call(counts, messageType)) {
      counts[messageType] = 0;
    }
    counts[messageType]++;
    // we confirmed that `Math.log10` does not produce any rounding errors on
    // Firefox and Chrome, but gives exact integer answers for powers of 10
    if (Math.log10(counts[messageType]) % 1 === 0) {
      const payload = { message_type: messageType, message, count: counts[messageType] };
      if (stackTrace) {
        payload.stack = stackTrace;
      }
      sendEvent('debug', payload);
    }
  };
}

/**
 * Send debugLog event to the browser console
 */
function sendToConsole (messageType, message, stackTrace) {
  const stackOutput = stackTrace ? `\n  Stacktrace: ${stackTrace}` : '';
  console.log(`${messageType}, ${message} ${stackOutput}`);
}

/**
 * LOG_OUTPUT refer to where we route debug events
 * `CONSOLE`: routes events to the browser console
 * `LOGGER`: routes events to standard `lo_event` pipeline
 */
export const LOG_OUTPUT = {
  CONSOLE: sendToConsole,
  LOGGER: sendEventToLogger
};

/**
 * LEVEL corresponds to how much information we include when we log something
 * `none`: does not log any information
 * `simple`: logs the data as is
 * `extended`: logs the data in conjuction with timestamp and stack trace
 */
export const LEVEL = {
  NONE: 'none',
  SIMPLE: 'simple',
  EXTENDED: 'extended'
};

let debugLevel = LEVEL.SIMPLE;

let debugLogOutputs = [LOG_OUTPUT.CONSOLE];

export function setLevel (level) {
  if (![LEVEL.NONE, LEVEL.SIMPLE, LEVEL.EXTENDED].includes(level)) {
    throw new Error(`Invalid debug log type ${level}`);
  }
  debugLevel = level;
}

export function setLogOutputs (outputs) {
  debugLogOutputs = outputs;
}

export function info (log, stack) {
  const formattedLog = formatLog(log);
  for (const logDestination of debugLogOutputs) {
    logDestination('info', formattedLog, stack);
  }
}

export function error (log, error) {
  const formattedLog = formatLog(log);
  const errorString = (typeof error === 'string' ? error : (error && error.name ? error.name : "Error"));
  for (const logDestination of debugLogOutputs) {
    logDestination(errorString, formattedLog, error.stack);
  }
}

/**
 * Format text of debugLog event based on our current LEVEL
 */
function formatLog (text) {
  let message;
  if (debugLevel === LEVEL.NONE) {
    return;
  } else if (debugLevel === LEVEL.SIMPLE) {
    message = text;
  } else if (debugLevel === LEVEL.EXTENDED) {
    const stackTrace = getStackTrace();
    const time = new Date().toISOString();
    message = `${time}: ${text}\n${stackTrace.padEnd(60)}`;
  }
  return message;
}

// helper function for generating a stack trace to use with `LEVEL.EXTENDED`
function getStackTrace () {
  const stack = new Error().stack.split('\n');
  const stackTrace = [stack[2], stack[3], stack[4], stack[5], stack[6]].join('\n');
  return stackTrace;
}
