/**
 * This files functions as a Queue using an indexeddb backend.
 *
 * If we are operating in a browser environment, we will use
 * the built-in indexeddb. In node environments, we will use
 * packages that mirror the functionality of indexeddb.
 *
 * Each item can be added to the end of the queue with `enqueue(item)`.
 * Items can be retrieved from the queue with `item = await dequeue()`.
 *
 * TODO
 * This code works in the browser, but breaks in a node environment.
 * autoIncrement is NOT supported when working in the node
 * environment. We will likely need to make some form of wrapper
 * to achieve this behavior for node.
 * See https://github.com/metagriffin/indexeddb-js/blob/master/src/indexeddb-js.js#L418C1-L418C53
 * NOTE: When we had our own counter for the id, we did notice that the node
 * environment (indexeddb-js or sqlite3) handled keys differently, thus
 * returning items out of order.
 *
 * TODO: This needs a very good code review. We weren't able to do
 * this before merge.
 */
import * as debug from './debugLog.js';
import * as util from './util.js';

const ENQUEUE = 'enqueue';
const DEQUEUE = 'dequeue';

export class Queue {
  constructor (queueName) {
    this.db = null;
    this.dbOperationQueue = [];
    this.nextDBOperationPromise = null;
    this.nextItemPromise = null;
    this.queueName = queueName;

    this.initialize = this.initialize.bind(this);
    this.addItemToDB = this.addItemToDB.bind(this);
    this.nextItemFromDB = this.nextItemFromDB.bind(this);
    this.nextDBOperation = util.once(this.nextDBOperation.bind(this));
    this.startProcessing = this.startProcessing.bind(this);
    this.addItemToDBOperationQueue = this.addItemToDBOperationQueue.bind(this);
    this.enqueue = this.enqueue.bind(this);
    this.dequeue = this.dequeue.bind(this);

    this.dbOperationDispatch = {
      [ENQUEUE]: this.addItemToDB,
      [DEQUEUE]: this.nextItemFromDB
    };
    this.initialize();
  }

  /**
   * Determine which environment we are in to set
   * the appropriate indexeddb information.
   */
  async initialize () {
    let request;
    if (typeof indexedDB === 'undefined') {
      debug.info('idbQueue: Importing indexedDB compatibility');

      const sqlite3 = await import('sqlite3');
      const indexeddbjs = await import('indexeddb-js');

      const engine = new sqlite3.default.Database('queue.sqlite');
      const scope = indexeddbjs.makeScope('sqlite3', engine);
      request = scope.indexedDB.open(this.queueName);
    } else {
      debug.info('idbQueue: Using browser consoleDB');
      request = indexedDB.open(this.queueName, 1);
    }

    request.onerror = (event) => {
      debug.error('QUEUE ERROR: could not open database', event.target.error);
    };

    request.onupgradeneeded = async (event) => {
      this.db = event.target.result;
      const objectStore = this.db.createObjectStore(this.queueName, { keyPath: 'id', autoIncrement: true });
      objectStore.createIndex('id', 'id');
    };

    request.onsuccess = (event) => {
      this.db = event.target.result;
      this.startProcessing();
    };
  }

  /**
   * Perform transaction to add item into indexeddb
   * If we are waiting for an item to available to dequeue,
   * we resolve the item immediately and don't add it to
   * the indexeddb.
   */
  async addItemToDB ({ payload }) {
    if (this.nextItemPromise) {
      this.nextItemPromise(payload.payload);
      this.nextItemPromise = null;
      return;
    }
    debug.info(`idbQueue: adding item to database, ${payload}`);
    const transaction = this.db.transaction([this.queueName], 'readwrite');
    const objectStore = transaction.objectStore(this.queueName);

    const request = objectStore.add(payload);

    request.onsuccess = (event) => {
      // successful request added
    };

    request.onerror = (event) => {
      if (event.target.error.name === 'ConstraintError') {
        debug.error('IDBQUEUE ERROR: Item already exists', event.target.error);
      } else {
        debug.error('IDBQUEUE ERROR: Error adding item to the queue:', event.target.error);
      }
    };
  }

  /**
   * Perform transaction to fetch next item in indexeddb
   */
  async nextItemFromDB ({ resolve, reject }) {
    debug.info('idbQueue: Fetching next item from database');
    const transaction = this.db.transaction([this.queueName], 'readwrite');
    const objectStore = transaction.objectStore(this.queueName);
    const request = objectStore.openCursor();

    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        const item = cursor.value;
        const deleteRequest = objectStore.delete(cursor.key);

        deleteRequest.onsuccess = () => {
          resolve(item.payload);
        };

        deleteRequest.onerror = (event) => {
          debug.error('IDBQUEUE ERROR: Error removing item from the queue:', event.target.error);
          reject(event.target.error);
        };
      } else {
        // No more items in the IndexedDB.
        resolve(new Promise((resolve) => {
          this.nextItemPromise = resolve;
        }));
      }
    };

    request.onerror = (event) => {
      debug.error('IDBQUEUE ERROR: Error reading queue cursor:', event.target.error);
      reject(event.target.error);
    };
  }

  /**
   * The processing loop continually waits for the next
   * dbOperation to come using the following generator.
   */
  async * nextDBOperation () {
    while (true) {
      let operation;
      if (this.dbOperationQueue.length > 0) {
        operation = this.dbOperationQueue.shift();
      } else {
        operation = await new Promise(resolve => {
          this.nextDBOperationPromise = resolve;
        });
      }
      debug.info(`idbQueue: Yielding next operation, ${operation}`);
      yield operation;
    }
  }

  /**
   * This method processes incoming dbOperations
   */
  async startProcessing () {
    const dbOperationStream = this.nextDBOperation();

    for await (const operation of dbOperationStream) {
      debug.info(`idbQueue: processing operation ${operation}`);
      try {
        await this.dbOperationDispatch[operation.operation](operation);
      } catch (error) {
        debug.error('Unable to perform operation on DB', error);
      }
    }
  }

  // helper function for enqueue/dequeue
  addItemToDBOperationQueue (payload) {
    if (this.nextDBOperationPromise) {
      this.nextDBOperationPromise(payload);
      this.nextDBOperationPromise = null;
    } else {
      this.dbOperationQueue.push(payload);
    }
  }

  /**
   * This functions will append an enqueue message to the
   * current operation stream.
   */
  enqueue (item) {
    debug.info(`idbQueue: Enqueuing item ${item}`);
    const payload = {
      operation: ENQUEUE,
      payload: { payload: item }
    };
    this.addItemToDBOperationQueue(payload);
  }

  /**
   * This function appends a dequeue message to the operation
   * stream and returns the result.
   */
  dequeue () {
    debug.info('idbQueue: dequeueing item');
    return new Promise((resolve, reject) => {
      const payload = { operation: DEQUEUE, resolve, reject };
      this.addItemToDBOperationQueue(payload);
    });
  }
}
