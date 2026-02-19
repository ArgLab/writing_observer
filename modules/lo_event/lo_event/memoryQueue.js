/*
 * This is a small in-memory queue class. It is designed to:
 * - Allow us to experiment with interfaces, as we try to abstract the queue out of lo_event, websocket, etc., without moving all the indexeddb code
 * - Works everywhere / act as a fallback where indexeddb is unavailable
 * - Nice for dev, where we don't want to persist events from buggy code
 * - Nice for simple use-cases
 */

export class Queue {
  constructor (queueName) {
    this.queue = [];
    this.queueName = queueName;
    this.promise = null;
    this.resolve = null;

    this.enqueue = this.enqueue.bind(this);
    this.dequeue = this.dequeue.bind(this);
  }

  async initialize () {
  }

  enqueue (item) {
    if (this.promise) {
      this.resolve(item);
      this.promise = null;
    } else {
      this.queue.push(item);
    }
  }

  dequeue () {
    if (this.queue.length > 0) {
      return this.queue.shift();
    } else {
      this.promise = new Promise((resolve) => {
        this.resolve = resolve;
      });
      return this.promise;
    }
  }
}
