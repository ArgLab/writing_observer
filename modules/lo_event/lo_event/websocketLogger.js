import { Queue } from './queue.js';
import * as disabler from './disabler.js';
import * as util from './util.js';
import * as debug from './debugLog.js';
import { storage } from './browserStorage.js';

function wsHost(overrides = {}, loc=window.location) {
  const { hostname, port, path, url } = overrides;
  const loServer = storage.get('lo_server');
  if (loServer) {
    console.log("Overriding server from storage");
    return loServer;
  }
  const protocol = loc.protocol === 'https:' ? 'wss://' : 'ws://';
  const host = hostname || loc.hostname;
  const portNumber = port || loc.port || (loc.protocol === 'https:' ? 443 : 80);
  const pathname = path || '/wsapi/in/';
  const fullUrl = url || `${host}:${portNumber}${pathname}`;

  return `${protocol}${fullUrl}`;
}


export function websocketLogger (server = {}) {
  /*
    This is a pretty complex logger, which sends events over a web
    socket.

    `server` can be a URL (usually, ws:// or wss://) or an object
    containing one or more of hostname, port, path, and url.

    Note that if the server is an object, it can be overwritten in
    storage (key loServer).

    Most of the complexity comes from reconnections, retries,
    etc. and the need to keep robust queues, as well as the need be
    robust about queuing events before we have a socket open or during
    a network failure.
  */
  let socket; // Our actual socket used to send and receive data.
  let WSLibrary; // For compatibility between node and browser, this either points to the browser WebSocket or to a compatibility library.
  const queue = new Queue('websocketLogger');
  // This holds an exception, if we're blacklisted, between the web
  // socket and the API. We generate this when we receive a message,
  // which is not a helpful place to raise the exception from, so we
  // keep this around until we're called from the client, and then we
  // raise it there.
  let blockerror;
  let metadata = {};

  // This logic might be moved into wsHost, so it's a little bit more
  // consistent.
  if(!server) {
    server = wsHost();
  } else if(typeof server === 'object') {
    server = wsHost(server);
  }
  // else the server is likely already a url string

  function calculateExponentialBackoff (n) {
    return Math.min(1000 * Math.pow(2, n), 1000 * 60 * 15);
  }

  let failures = 0;
  let READY = false;
  let wsFailureResolve = null;
  let wsFailurePromise = null;
  let wsConnectedResolve = null;

  async function startWebsocketConnectionLoop () {
    while (true) {
      const connected = await newWebsocket();
      if (!connected) {
        failures++;
        await util.delay(calculateExponentialBackoff(failures));
      } else {
        READY = true;
        failures = 0;
        await socketClosed();
        READY = false;
      }
    }
  }

  function socketClosed () { return wsFailurePromise; }

  function newWebsocket () {
    socket = new WSLibrary(server);
    wsFailurePromise = new Promise((resolve, reject) => {
      wsFailureResolve = resolve;
    });
    const wsConnectedPromise = new Promise((resolve, reject) => {
      wsConnectedResolve = resolve;
    });
    socket.onopen = () => { prepareSocket(); wsConnectedResolve(true); };
    socket.onerror = function (e) {
      debug.error('Could not connect to websocket', e);
      wsConnectedResolve(false);
      wsFailureResolve();
    };
    socket.onclose = () => { wsConnectedResolve(false); wsFailureResolve(); };
    socket.onmessage = receiveMessage;
    return wsConnectedPromise;
  }

  function prepareSocket () {
    if(Object.keys(metadata).length > 0) {
      queue.enqueue(JSON.stringify(metadata));
    }

    queue.startDequeueLoop({
      initialize: waitForWSReady,
      shouldDequeue: waitForWSReady,
      onDequeue: socketSend
    });
  }

  async function socketSend (item) {
    socket.send(item);
  }

  async function waitForWSReady () {
    return await util.backoff(() => (READY));
  }

  function receiveMessage (event) {
    const response = JSON.parse(event.data);
    switch (response.status) {
      case 'blocklist':
        debug.info('Received block error from server');
        blockerror = new disabler.BlockError(
          response.message,
          response.time_limit,
          response.action
        );
        break;
      case 'auth':
        storage.set({ user_id: response.user_id });
        util.dispatchCustomEvent('auth', { detail: { user_id: response.user } });
        break;
      // These should probably be behind a feature flag, as they assume
      // we trust the server.
      case 'local_storage':
        storage.set({ [response.key]: response.value });
        break;
      case 'browser_event':
        util.dispatchCustomEvent(response.event_type, { detail: response.detail });
        break;
      case 'fetch_blob':
        util.dispatchCustomEvent('fetch_blob', { detail: response.data });
        break;
      default:
        debug.info(`Received response we do not yet handle: ${response}`);
        break;
    }
  }

  function checkForBlockError () {
    if (blockerror) {
      console.log('Throwing block error');
      const b = blockerror;
      blockerror = null;
      socket.close();
      throw b;
    }
  }

  function wsLogData (data) {
    checkForBlockError();
    queue.enqueue(data);
  }

  wsLogData.init = async function () {
    if (typeof WebSocket === 'undefined') {
      debug.info('Importing ws');
      WSLibrary = (await import('ws')).WebSocket;
    } else {
      debug.info('Using built-in websocket');
      WSLibrary = WebSocket;
    }
    startWebsocketConnectionLoop();
  };

  wsLogData.setField = function (data) {
    util.mergeDictionary(metadata, JSON.parse(data));
    queue.enqueue(data);
  };

  function handleSaveBlob (blob) {
    queue.enqueue(JSON.stringify({ event: 'save_blob', blob }));
  }

  util.consumeCustomEvent('save_blob', handleSaveBlob)

  return wsLogData;
}
