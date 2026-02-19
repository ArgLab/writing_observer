/*
 * Test of basic functionality. This uses the redux logger, primarily.
 */

import * as loEvent from '../lo_event/lo_event.js';
import * as reduxLogger from '../lo_event/reduxLogger.js';
import { consoleLogger } from '../lo_event/consoleLogger.js';
import * as debug from '../lo_event/debugLog.js';
import { getBrowserInfo } from '../lo_event/metadata/browserinfo.js';

const rl = reduxLogger.reduxLogger();

console.log('lo_event test: Initializing loEvent');
loEvent.init(
  'org.ets.lo_event.test',
  '1',
  [consoleLogger(), rl],
  debug.LEVEL.SIMPLE,
  [debug.LOG_OUTPUT.LOGGER(loEvent.logEvent)]
);
loEvent.setFieldSet([{ preauth_type: 'test' }]);
loEvent.setFieldSet([{ postauth_type: 'test' }, getBrowserInfo()]);
loEvent.go();

console.log('lo_event test: Initialized');
loEvent.logEvent('test', { event_number: 1 });
loEvent.logEvent('test', { event_number: 2 });
loEvent.logEvent('test', { event_number: 3 });

console.log('lo_event test: Preparing to run test cases');

describe('loEvent testing', () => {
  it('Check basic event handling', async () => {
    console.log('lo_event test: Running test cases');
    // TODO revisit why we need this additional awaitEvent call.
    // Spent some time poking, but didn't fully understand the
    // why so I'm leaving it as is now.
    // Are events coming in in the right order?
    expect((await reduxLogger.awaitEvent()).event_number).toBe(1);
    expect((await reduxLogger.awaitEvent()).event_number).toBe(2);
    console.log('lo_event test: Test Event 3: ', reduxLogger.awaitEvent()); // <- event number 3
    // Are metadata being sent?
    console.log('lo_event test: redux lock fields', rl.getLockFields());
  });
});
