import { registerReducer, store } from '../reduxLogger.js';

// Local debug -- for development within this file
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };

export const LOAD_DATA_EVENT = 'LOAD_DATA_EVENT';
export const LOAD_STATE = 'LOAD_STATE';
export const NAVIGATE = 'NAVIGATE';
export const SHOW_SECTION='SHOW_SECTION';
export const STEPTHROUGH_NEXT = 'STEPTHROUGH_NEXT';
export const STEPTHROUGH_PREV = 'STEPTHROUGH_PREV';
export const STORE_VARIABLE = 'STORE_VARIABLE';
export const STORE_SETTING = 'STORE_SETTING';
export const UPDATE_INPUT = 'UPDATE_INPUT';
export const UPDATE_LLM_RESPONSE = 'UPDATE_LLM_RESPONSE';
export const VIDEO_TIME_EVENT = 'VIDEO_TIME_EVENT';

const initialState = {
  component_state: {}
};

/*
  This is our most common reducer. It simply updates the component's
  state with any fields in the event.

  In the future, it would be nice to add some sanity checks.
 */
export const updateResponseReducer = (state = initialState, action) => {
  const { id, ...rest } = action;
  const new_state = {
    ...state,
    component_state: {
      ...state.component_state,
      [id]: {...state.component_state?.[id], ...rest}
    }
  };
  if(DEBUG) {
    console.log("REGISTER REDUCER");
    console.log("Reducer action:", action);
    console.log("Response reducer called");
    console.log("Old state", state);
    console.log("Action", action);
    console.log("New state", new_state);
  }
  return new_state;
}

registerReducer(
  [LOAD_DATA_EVENT,
   LOAD_STATE,
   NAVIGATE,
   SHOW_SECTION,
   STEPTHROUGH_NEXT, STEPTHROUGH_PREV,
   STORE_SETTING,
   STORE_VARIABLE,
   UPDATE_INPUT,
   UPDATE_LLM_RESPONSE, 
   VIDEO_TIME_EVENT],
  updateResponseReducer
);
