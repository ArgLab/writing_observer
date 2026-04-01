import * as lo_event from '../lo_event';
import * as reduxLogger from '../reduxLogger.js';
import { consoleLogger } from '../consoleLogger.js';
import * as debug from '../debugLog.js';

/*
 * Default convenience init function
 */
export function init() {
  lo_event.init(
    "org.ets.activity",
    "0.0.1",
    [consoleLogger(), reduxLogger.reduxLogger([], {})],
    {
      debugLevel: debug.LEVEL.EXTENDED,
      debugDest: [debug.LOG_OUTPUT.CONSOLE],
      useDisabler: false,
      queueType: lo_event.QueueType.IN_MEMORY
    }
  );

  lo_event.go();
}
