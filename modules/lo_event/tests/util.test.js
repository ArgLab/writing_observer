// TODO:
// * Document
// * More test cases
// * Much better description strings

import * as util from '../lo_event/util.js';

let someAsyncCondition;
global.document = {};

const DEBUG = false;

function debug_log(...args) {
  if(DEBUG) {
    console.log(...args);
  }
}

async function checkCondition () {
  // Example of a condition check
  // Replace this with your actual condition check logic
  debug_log('Util test: checking', someAsyncCondition);
  return someAsyncCondition;
}

xdescribe('Testing Backoff functionality', () => {
  beforeEach(() => {
    console.log('util.js:backoff Setting condition to false');
    someAsyncCondition = false;
  });

  it('Check for generic backoff functionality', async () => {
    console.log('TESTING THIS FUNCTION');
    // Set the condition to true after some time for demonstration
    setTimeout(() => {
      console.log('Util test: setting someAsyncCondition');
      someAsyncCondition = true;
    }, 1000);

    try {
      await util.backoff(checkCondition, 'This should not be seen in the console');
      expect(someAsyncCondition).toBe(true);
    } catch (error) {
      console.error(error.message);
    }
  }, 10000);

  it('Test max retry on backoff', async () => {
    try {
      await util.backoff(
        checkCondition,
        'Condition not met after max retries.',
        [1000, 1000, 1000],
        util.TERMINATION_POLICY.RETRY,
        5
      );
    } catch (error) {
      console.error(error.message);
    }
    expect(someAsyncCondition).toBe(false);
  }, 10000);
});

describe('util.js testing', () => {
  console.log("Testing rest of util.js");
  it('Test fullyQualifiedWebsocketURL', () => {
    // We need a function wrapper to check for thrown errors
    expect(function () {
      util.fullyQualifiedWebsocketURL();
    }).toThrow(new Error('Base server is not provided.'));

    global.document.location = 'http://www.example.com';
    expect(util.fullyQualifiedWebsocketURL()).toBe('ws://www.example.com/wsapi/in');
    expect(util.fullyQualifiedWebsocketURL('/ws')).toBe('ws://www.example.com/ws');
    expect(util.fullyQualifiedWebsocketURL('/ws', 'https://learning-observer.org')).toBe('wss://learning-observer.org/ws');
    expect(function () {
      util.fullyQualifiedWebsocketURL('/ws', 'fake://learning-observer.org');
    }).toThrow(new Error('Protocol mapping not found.'));
  });

  it('test deeply merging metadata', async () => {
    const obj1 = { a: 1, b: { c: 3 } };
    const func1 = function () {
      return { b: { d: 4 }, e: 5 };
    };
    expect(await util.mergeMetadata([obj1, func1])).toEqual({ a: 1, b: { c: 3, d: 4 }, e: 5 });
  });

  it('it should copy specified fields from the source object', () => {
    console.log("Testing copy fields");
    const source = { foo: 'bar', baz: 'qux' };
    const fields = ['foo', 'baz'];
    expect(util.copyFields(source, fields)).toEqual({ foo: 'bar', baz: 'qux' });
  });

  it('it should return an empty object if source is null', () => {
    expect(util.copyFields(null, ['foo', 'baz'])).toEqual({});
  });

  it('it should only copy fields that exist in the source object', () => {
    const source = { foo: 'bar' };
    const fields = ['foo', 'baz'];
    expect(util.copyFields(source, fields)).toEqual({ foo: 'bar' });
  });
});

