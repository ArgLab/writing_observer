/*
 * This is a logger which uses redux in order to route events to one
 * or more subscribers. It is currently used for working with the test
 * framework.
 *
 * In the future, our goal is to make this into a 'batteries included'
 * framework for developing `react`/`redux`/`lo_event` applications
 * which embodies good design practices for this domain.
 *
 * Our goal is NOT to be universal. Integrating `lo_event` into an
 * exiting `redux` workflow is ≈25 lines of code. This framework is
 * opinionated, and if there's a clash of opinions, you're better
 * off writing those 25 lines.
 *
 * Beyond test cases, the major use case is to make the development of
 * a broad class of simple educational activites, well, simple. For
 * larger applications, it probably makes more sense to start with
 * vanilla `react`/`redux`/`lo_event` without using this file, to just
 * use bits and pieces, or to treat this code as an examplar.
 */
import * as redux from 'redux';
import { thunk } from 'redux-thunk';
import { createStateSyncMiddleware, initMessageListener } from 'redux-state-sync';
import debounce from 'lodash/debounce';

import * as util from './util.js';

const EMIT_EVENT = 'EMIT_EVENT';
const EMIT_LOCKFIELDS = 'EMIT_LOCKFIELDS';
const EMIT_SET_STATE = 'SET_STATE';

let IS_LOADED = false;

// TODO: Import debugLog and use those functions.
const DEBUG = false;

function debug_log (...args) {
  if (DEBUG) {
    console.log(...args);
  }
}

/**
 * Update the redux logger's state with `data`.
 * This is fired when consuming a custom `fetch_blob`
 * event.
 */
export function handleLoadState (data) {
  IS_LOADED = true;
  const state = store.getState();
  if (data) {
    setState(
      {
        ...state,
        ...data,
        settings: {
          ...state.settings,
          reduxStoreStatus: IS_LOADED
        }
      });
  } else {
    debug_log('No data provided while handling state from server, continuing.');
    setState(
      {
        ...state,
        settings: {
          ...state.settings,
          reduxStoreStatus: IS_LOADED
        }
      });
  }
}

async function saveStateToLocalStorage (state) {
  if (!IS_LOADED) {
    debug_log('Not saving store locally because IS_LOADED is set to false.');
    return;
  }

  try {
    const KEY = state?.settings?.reduxID || 'redux';
    const serializedState = JSON.stringify(state);
    localStorage.setItem(KEY, serializedState);
  } catch (e) {
    // Ignore
  }
}

/**
 * Dispatch a `save_blob` event on the redux
 * logger.
 */
async function saveStateToServer (state) {
  if (!IS_LOADED) {
    debug_log('Not saving store on the server because IS_LOADED is set to false.');
    return;
  }

  try {
    // console.log("dispatching save_blob")
    util.dispatchCustomEvent('save_blob', { detail: state });
    // store.dispatch('save_blob', { detail: state });
  } catch (e) {
    // Ignore
    debug_log('Error in dispatch', { e });
  }
}

// Action creator function This is a little bit messy, since we
// duplicate type from the payload. It's not clear if this is a good
// idea. We used to have `type` be set to the current contents of
// `redux_type`. However, for debugging / logging tools
// (e.g. redux-dev-tools), it was convenient to have this match up to
// the internal event type.
const emitEvent = (event) => {
  return {
    redux_type: EMIT_EVENT,
    type: JSON.parse(event).event,
    payload: event
  };
};

// Action creator function
const emitSetField = (setField) => {
  return {
    redux_type: EMIT_LOCKFIELDS,
    type: EMIT_LOCKFIELDS,
    payload: setField
  };
};

const emitSetState = (state) => {
  return {
    redux_type: EMIT_SET_STATE,
    type: EMIT_SET_STATE,
    payload: state
  };
};

function store_last_event_reducer (state = {}, action) {
  return { ...state, event: action.payload };
};

function lock_fields_reducer (state = {}, action) {
  const payload = JSON.parse(action.payload);
  return {
    ...state,
    lock_fields: {
      ...payload,
      fields: {
        ...(state.lock_fields ? state.lock_fields.fields : {}),
        ...payload.fields
      }
    }
  };
}

/*
 * This is our most common reducer. It simply updates a component's
 * state with the dictionary of an action.
 *
 * In the future, we plan to add various sorts of event validation and
 * potentially preprocessing. We would like things like:
 *
 *    updateComponentStateReducer({valid_fields: ['response'})
 *
 * Ergo, the two-level call with the destruct.
 */
export const updateComponentStateReducer = ({}) => (state = initialState, action) => {
  const { id, ...rest } = action;
  const new_state = {
    ...state,
    component_state: {
      ...state.component_state,
      [id]: {...state.component_state?.[id], ...rest}
    }
  };

  debug_log(
    "==REGISTER REDUCER==\n",
    "Reducer action:", action, "\n",
    "Response reducer called\n",
    "Old state", state, "\n",
    "Action", action, "\n",
    "New state", new_state
  );

  return new_state;
}

function set_state_reducer (state = {}, action) {
  return action.payload;
}

const BASE_REDUCERS = {
  [EMIT_EVENT]: [store_last_event_reducer],
  [EMIT_LOCKFIELDS]: [lock_fields_reducer],
  [EMIT_SET_STATE]: [set_state_reducer]
}

const APPLICATION_REDUCERS = {};

export const registerReducer = (keys, reducer) => {
  const reducerKeys = Array.isArray(keys) ? keys : [keys];

  reducerKeys.forEach(key => {
    debug_log('registering key: ' + key);
    if (!APPLICATION_REDUCERS[key]) {
      APPLICATION_REDUCERS[key] = [];
    }
    APPLICATION_REDUCERS[key].push(reducer);
  });
  return reducer;
};

// Reducer function
const reducer = (state = {}, action) => {
  let payload;

  debug_log('Reducing ', action, ' on ', state);
  state = BASE_REDUCERS[action.redux_type] ? composeReducers(...BASE_REDUCERS[action.redux_type])(state, action) : state;

  if (action.redux_type === EMIT_EVENT) {
    payload = JSON.parse(action.payload);
    if (action.type === 'save_setting') {
      return {
        ...state,
        settings: {
          ...state.settings,
          payload
        }
      };
    }
    debug_log(Object.keys(payload));

    if (APPLICATION_REDUCERS[payload.event]) {
      state = { ...state, application_state: composeReducers(...APPLICATION_REDUCERS[payload.event])(state.application_state || {}, payload) };
    }
  }

  return state;
};

const eventQueue = [];
const composeEnhancers = (typeof window !== 'undefined' && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) || redux.compose;

// This should just be redux.applyMiddleware(thunk))
// There is a bug in our version of redux-thunk where, in node, this must be thunk.default.
//
// This shows up as an error in the test case. If the error goes away, we should switch this
// back to thunk.
// const presistedState = loadState();

export let store = redux.createStore(
  reducer,
  { event: null }, // Base state
  composeEnhancers(redux.applyMiddleware((thunk.default || thunk), createStateSyncMiddleware()))
);

initMessageListener(store);

let promise = null;
let previousEvent = null;
let lockFields = null;
let eventSubscribers = [];

/*
  Compose reducers takes a dynamic number of reducers as arguments and
  returns a new reducer function. This applies each reducer to the
  state in the order they are provided, ultimately returning the
  final state after all reducers have been applied.

  Example usage:
  ```
  const rootReducer = composeReducers(reducer1, reducer2, reducer3);
  const finalState = rootReducer(initialState, { redux_type: 'SOME_ACTION' });
  ```
*/
function composeReducers(...reducers) {
  return (state, action) => reducers.reduce(
    (currentState, reducer) => reducer(currentState, action),
    state
  );
}

export function setState(state) {
  debug_log('Set state called');
  if (Object.keys(state).length === 0) {
    const storeState = store.getState();
    state = {
      settings: {
        ...storeState.settings,
        reduxStoreStatus: IS_LOADED
      }
    };
  }
  store.dispatch(emitSetState(state));
}

const debouncedSaveStateToLocalStorage = debounce((state) => {
  saveStateToLocalStorage(state);
}, 1000);

const debouncedSaveStateToServer = debounce((state) => {
  saveStateToServer(state);
}, 1000);

function initializeStore () {
  store.subscribe(() => {
    const state = store.getState();
    // we use debounce to save the state once every second
    // for better performances in case multiple changes occur in a short time
    debouncedSaveStateToLocalStorage(state);
    debouncedSaveStateToServer(state);

    if (state.lock_fields) {
      lockFields = state.lock_fields.fields;
    }
    if (!state.event) return;
    debug_log('Received event:', state.event);
    const event = JSON.parse(state.event);
    if (event === previousEvent) {
      return;
    }
    previousEvent = event;

    if (promise) {
      promise.resolve(event);
      promise = null;
    } else {
      // This is only useful for awaitEvent below. Otherwise, events build up. Having
      // this event queue may be good or a memory leak. We should figure out whether
      // to have this behind a flag later.
      eventQueue.push(event);
    }
    for (const i in eventSubscribers) {
      eventSubscribers[i](event);
    }
  });
}

export function reduxLogger (subscribers, initialState = null) {
  if (subscribers != null) {
    eventSubscribers = subscribers;
  }

  function logEvent (event) {
    store.dispatch(emitEvent(event));
  }
  logEvent.lo_name = 'Redux Logger'; // A human-friendly name for the logger
  logEvent.lo_id = 'redux_logger';   // A machine-frienly name for the logger

  logEvent.init = async function () {
    initializeStore();
  };

  logEvent.setField = function (event) {
    store.dispatch(emitSetField(event));
  };

  logEvent.getLockFields = function () { return lockFields; };

  // do we want to initialize the store here? We set it to the stored state in create store
  // if (initialState) {
  // }

  return logEvent;
}

// This is a convenience function which lets us simply await events.
//
// Note that this should not be used in threaded code or in multiple
// places at the same time in async code. It's a convenience function
// for _simple_ code.
export const awaitEvent = () => {
  if (eventQueue.length > 0) {
    return eventQueue.shift(); // Return the first event in the queue
  }
  if (promise) {
    throw new Error('Only one call to awaitEvent is allowed at a time');
  }

  // Create a new promise
  let resolvePromise;

  promise = new Promise((resolve) => {
    resolvePromise = resolve;
  });

  promise.resolve = resolvePromise;
  return promise;
};

// Start listening for fetch
util.consumeCustomEvent('fetch_blob', handleLoadState);
