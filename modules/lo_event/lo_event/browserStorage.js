// We often need a KVS to store things like settings.

// This code is not fully tested. Much of it works, but there are
// pathways and fallbacks which might not.

// TODO: Add test cases for all pathways and fallbacks. This kind of code
// is very tough to debug otherwise.

// This code is a little bit rough since it needs to work across many
// environments (different browsers, browser permissions, in node, in
// extensions, etc.). It's hard to know how it will behave everywhere.

// The idea here is we need a key-value store for many purposes, but
// especially, opt-out / opt-in. This allows us to use:
// * Extension-specific storage APIs (chrome.storage)
// * Normal browser storage APIs
// * As a final fall-back (and debugging aid), in-memory storage
//
// We copy the chrome.storage API since it is the most annoying,
// being asynchronous. It's not possible to implement the other APIs
// on top of it, but the reverse is simple.
//
// At the end, we export one storage object, with a consistent API,
// using our most reliable storage.
import * as debug from './debugLog.js';

// thunkStorage mirrors the capability of `chrome.storage.sync`
// this is used for testing purposes, as well as a fallback if
// chrome.storage.sync is unavailable.
const thunkStorage = {
  data: {},
  set: function (items, callback) {
    this.data = { ...this.data, ...items };
    if (callback) callback();
  },
  get: function (keys, callback) {
    let result = {};
    if (Array.isArray(keys)) {
      keys.forEach(key => {
        if (Object.prototype.hasOwnProperty.call(this.data, key)) {
          result[key] = this.data[key];
        }
      });
    } else if (typeof keys === 'string') {
      if (Object.prototype.hasOwnProperty.call(this.data, keys)) {
        result[keys] = this.data[keys];
      }
    } else {
      result = { ...this.data };
    }
    if (callback) callback(result);
  }
};

/**
 * Returns a `get` function that wraps a provided `getItem`
 * function to mirror the workflow and capabilities of the
 * `storage.sync.get`/`chrome.sync.get` API.
 */
function getWithCallback (getItem) {
  function get (items, callback = () => {}) {
    if (typeof items === 'string') {
      items = [items];
    }
    const results = {};
    for (const item of items) {
      results[item] = getItem(item);
    }
    callback(results);
  }
  return get;
}

/**
 * Returns a `set` function that wraps a provided `setItem`
 * function to mirror the capabilities of the
 * `storage.sync.set`/`chrome.sync.set` API.
 */
function setWithCallback (setItem) {
  function set (items, callback = () => {}) {
    for (const item in items) {
      setItem(item, items[item]);
    }
    if (callback) callback();
  }
  return set;
}

export let storage;

let b;

if (typeof browser !== 'undefined') {
  b = browser;
} else if (typeof chrome !== 'undefined') {
  b = chrome;
}

/**
 * Determine which backend storage API to use and (sometimes)
 * add compatibility wrappers around them.
 *
 * Backend API priority:
 * - Browser's storage.sync (extension only)
 * - Browser's storage.local (extension only)
 * - localStorage
 * - window.localStorage
 * - thunkStorage
 */
if (typeof b !== 'undefined') {
  if (b.storage && b.storage.sync) {
    debug.info('Setting storage to storage.sync');
    storage = b.storage.sync;
  } else if (b.storage && b.storage.local) {
    debug.info('Setting storage to storage.local');
    storage = b.storage.local;
  } else {
    debug.info('Setting storage to default, thunkStorage');
    storage = thunkStorage;
  }
} else if (typeof localStorage !== 'undefined') {
  // Add compatibility modifications for localStorage
  debug.info('Setting storage to localStorage');
  storage = {
    get: getWithCallback(localStorage.getItem.bind(localStorage)),
    set: setWithCallback(localStorage.setItem.bind(localStorage))
  };
} else if (typeof window !== 'undefined' && typeof window.localStorage !== 'undefined') {
  // Add compatibility modifications for window.localStorage
  debug.info('Setting storage to window.localStorage');
  storage = {
    get: getWithCallback(window.localStorage.getItem.bind(window.localStorage)),
    set: setWithCallback(window.localStorage.setItem.bind(window.localStorage))
  };
} else {
  // If none of the above options exist, fall back to thunkStorage or exit gracefully
  debug.info('Setting storage to default, thunkStorage');
  storage = thunkStorage;
}
