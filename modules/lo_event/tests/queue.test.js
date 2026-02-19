// Start of a test of the queue.
//
// TODO: Finish, then test both types of queue, and then in node and
// browser, as well as various failure conditions.

import { Queue } from '../lo_event/queue.js';
import { delay } from '../lo_event/util.js';

const DEBUG = false;

function debug_log(...args) {
  if(DEBUG) {
    console.log(...args);
  }
}

const queue = new Queue('queueNew');
await delay(1000);
const max = 5;
debug_log('Queue test: Queueing events');
for (let i = 0; i < max; i++) {
  debug_log('Queue test: Queueing', i);
  queue.enqueue(i);
}

queue.startDequeueLoop({
  onDequeue: debug_log
});
