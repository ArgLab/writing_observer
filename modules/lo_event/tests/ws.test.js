/*
 * This is a cursory test of the web socket logger.
 *
 * It takes some time to run, so it is not part of the main test suite.
 */

import { WebSocketServer } from 'ws';
import * as debug from '../lo_event/debugLog.js';
import { getBrowserInfo } from '../lo_event/metadata/browserinfo.js';

import * as loEvent from '../lo_event/lo_event.js';
import * as websocketLogger from '../lo_event/websocketLogger.js';

const DEBUG = false;

function debug_log(...args) {
  if(DEBUG) {
    console.log(...args);
  }
}

debug_log('WS test: Launching server');

const host = 'localhost';
const port = 8087;

const wss = new WebSocketServer({ host, port });

debug_log('WS test: Setting up connection');

const dispatch = {
  terminate: function (event, ws) {
    debug_log('WS test: Terminating');

    // It takes a little bit of voodoo to convince the server to
    // terminate.

    // We need to close all open socket connections (of which we have
    // just one), close the listening socket, and terminate the
    // process.
    ws.close();
    wss.close(() => {
      debug_log('WS test: Server closed');
      process.exit(0);
    });
  },
  test: function (event) {
    debug_log('WS test: Test event: ', event.event_number);
  },
  lock_fields: function (event) {
    debug_log('WS test: Metadata: ', event);
  },
  blocklist: function (event, ws) {
    debug_log('WS test: Sending blocklist');
    ws.send(JSON.stringify({
      status: 'blocklist',
      time_limit: 'MINUTES',
      action: 'DROP'
    }));
  },
  debug: function (event) {
    debug_log('WS test: DEBUG', event);
  }
};

wss.on('connection', (ws) => {
  debug_log('WS test: New connection');
  ws.on('message', (data) => {
    // Verify received data
    const j = JSON.parse(data.toString());
    debug_log('WS test: Dispatching: ', j);
    dispatch[j.event](j, ws);
  });
});

const wsl = websocketLogger.websocketLogger(`ws://${host}:${port}`);

loEvent.init(
  'org.ets.lo_event.test',
  '1',
  [wsl],
  debug.LEVEL.SIMPLE,
  [debug.LOG_OUTPUT.LOGGER(loEvent.logEvent), debug.LOG_OUTPUT.CONSOLE]
);
loEvent.setFieldSet([{ preauth_type: 'test' }]);
loEvent.setFieldSet([{ postauth_type: 'test' }, getBrowserInfo()]);
loEvent.go();

loEvent.logEvent('test', { event_number: 1 });
loEvent.logEvent('test', { event_number: 2 });
loEvent.logEvent('test', { event_number: 3 });

// Check the blocklist.
// In this test, we might receive one more event or so.
//
// This takes a second, and the terminate event never comes in, so
// after that the server hangs, so this is behind a flag.
const TEST_BLOCKLIST = false;
if (TEST_BLOCKLIST) {
  loEvent.logEvent('blocklist', { action: 'Send us back a block event!' });
  await new Promise(resolve => setTimeout(resolve, 1000));
}

loEvent.logEvent('test', { event_number: 4 });
loEvent.logEvent('test', { event_number: 5 });
loEvent.logEvent('terminate', {});

debug_log('WS test: Done');
