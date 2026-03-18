/*
 * Helper functions, mostly for extracting things from our store.
 */
import React from 'react';

import { useSelector } from 'react-redux';
import { registerReducer } from 'lo_event/lo_event/reduxLogger.js';

import * as lo_event from 'lo_event';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };

// The store contains a mixture of lo_event state and our own
// state. This abstracts out just our own state. This should likely
// be polished and merged into lo_event.
export function useApplicationSelector(selector = s => s) {
  return useSelector(state => selector(state?.application_state));
}

// Get the state for any component, by ID.
export function useComponentSelector(id, selector = s => s) {
  return useApplicationSelector(
    s => selector(s?.component_state?.[id])
  );
}

export function useSettingSelector(setting) {
  return useSelector(state => state?.settings?.[setting]);
}

export const extractChildrenText = (element) => {
  if (typeof element === "string") {
    return element.trim();
  }
  const extractElementText = (element) => {
    if (typeof element === "string") {
      return element.trim();
    } else if (React.isValidElement(element)) {
      return element.type.eval(element);
    }
    return "";
  };

  const { children } = element.props;
  const extractedChildren = React.Children.map(children, (element) => extractElementText(element));
  return extractedChildren.join("");
};

const initialState = {
  component_state: {}
};

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

/*
  Let's say we have:
     <Foo> <Bar>Parameter 1</Bar> <Bif>Parameter 2</Bif> </Foo>
  The goal is to be able to extract Parameter 1 by passing Foo's children and "Bar."

  This is helpful for longer parameters than fit in <Foo Bar="...">

  Untested
 */
function extractChildComponent(componentName, children) {
  let component = null;

  React.Children.forEach(children, child => {
    if (child && child.type && child.type.displayName === componentName) {
      component = child;
    }
  });

  return component ? React.cloneElement(component) : null;
}

export const LOAD_DATA_EVENT = 'LOAD_DATA_EVENT';
export const JSONTYPE = 'JSONTYPE'; // Better names? JSON conflicts with JSON.parse, etc.
export const TEXTTYPE = 'TEXTTYPE';

registerReducer(
  [LOAD_DATA_EVENT],
  updateResponseReducer
);

/*
 * Return data from a given URL, or false if not loaded yet.
 *
 * id: component ID
 * key: Where to store data in component's redux store
 * override: if available, do not do AJAX and return the
 *   override. This is commonly used if we want to be able have
 *   e.g. both subtitles and subtitles_src as available parameters
 * type: JSONTYPE or TEXTTYPE
 * modifier: allows us to tweak the data (e.g. grab a single field from an AJAX request)
 *
 * We might consider allowing this to also automate extractChildComponent in the future.
 *
 * Note that key and id are optional. For simple data loads, this will simply be stored using the URL as an ID. This should probably be namespaced somehow later.
 */
export function useData({id, key, url, override = false, type=JSONTYPE, modifier=(d) => d}) {
  id = id ?? url;
  key = key ?? url;
  const data = useComponentSelector(id, s => s?.[key] ?? override);

  async function fetchData() {
    const response = await fetch(url);

    const lookup = {
      JSONTYPE: async () => await response.json(),
      TEXTTYPE: async () => await response.text(),
    };

    const data = await lookup[type]();

    lo_event.logEvent(LOAD_DATA_EVENT, {
      id,
      [key]: modifier(data),
    });
  }

  React.useEffect(() => {
    if(!data) {
      fetchData();
    }
  }, [url]);

  return data;
}
