import { treeget, copyFields } from './util.js';

function selectionData(event) {
  return window.getSelection().toString();
}

function windowSize(event){
  return { h: window.innerHeight, w: window.innerWidth };
}

function mediaInfo(event){
  if(event.video) {
    return copyFields(event.video, ["src", "width", "height", "duration", "currentRime", "muted", "paused", "controls"]);
  } else {
    return null;
  }
}

let parent_events = {
  generic: {properties: ["timeStamp", "type"]},
  animation: {parent: ["generic"], properties: ["animationName", "elapsedTime", "pseudoElement"]},
  clipboard: {parent: ["generic"]},
  composition: {parent: ["generic"], properties: ["data", "locale"]},
  key: {parent: ["generic"], properties: ["altKey", "charCode", "code", "ctrlKey", "iscomposing", "key", "keyCode", "metaKey", "repeat", "shiftKey", "timeStamp", "type", "which"], functions: {}},
  mouse: {parent: ["generic"], properties: ["x", "y", "layerX", "layerY", "movementX", "movementY", "offsetY", "offsetY", "pageX", "pageY", "screenX", "screenY", "altKey", "metaKey", "shiftKey"]},
  pointer: {parent: ["mouse"], properties: ["altitudeAngle", "azimuthAngle", "pointerId", "width", "height", "pressure", "tangentialPressure", "tiltX", "tiltY", "twist", "pointerType", "isPrimary"]},
  scroll: {parent: ["generic"], properties: ["detail", "layerX", "layerY", "which", "rangeOffset", "SCROLL_PAGE_UP", "SCROLL_PAGE_DOWN"]},
  touch: {parent: ["mouse"], properties: ["changedTouches", "targetTouches", "touches", "rotation", "scale"]}, // Rotation / scale are nonstandard, but helpful where they work.
  transition: {parent: ["generic"], properties: ["propertyName", "elapsedTime", "pseudoElement"]},
  media: {parent: ["generic"], functions: { mediaInfo }},
};

// TODO: Find some way to either aggregate or debounce dense events like mouseMove, seeks, etc.
// These can occur many times in each second, and naively treated, they will overwhelm the server.
let events = {
  // Key events (done)
  keydown: {parent: ["key"]},
  keypress: {parent: ["key"]},
  keyup: {parent: ["key"]},

  // Composition events are used in entry of e.g. Chinese characters (probably done, but untested)
  compositionupdate: {parent: ["composition"]},
  compositionstart: {parent: ["composition"]},
  compositionend: {parent: ["composition"]},

  // Clipboard events (done, but we don't log data for cut)
  cut: {parent: ["clipboard"]},
  copy: {parent: ["clipboard"], functions: {selectionData}},
  paste: {parent: ["clipboard"], functions: {clipboardData : (event) => event.clipboardData.getData('text')}},

  // Drag-and-drop events (probably done, but we may want to extract dataTransfer, and untested)
//  drag: {parent: "mouse", properties: [], functions: {}}, <-- Large number of events
  dragend: {parent: "mouse", properties: [], functions: {}},
  dragenter: {parent: "mouse", properties: [], functions: {}},
  dragleave: {parent: "mouse", properties: [], functions: {}},
//  dragover: {parent: "mouse", properties: [], functions: {}},
  dragstart: {parent: "mouse", properties: [], functions: {}},
  drop: {parent: "mouse", properties: [], functions: {}},

  // Animations, videos, media, etc.
  // Animation (done)
  animationend: {parent: ["animation"]},
  animationiteration: {parent: ["animation"]},
  animationstart: {parent: ["animation"]},
  // CSS transitions
  transitionstart: {parent: ["transition"]},
  transitionrun: {parent: ["transition"]},
  transitionend: {parent: ["transition"]},
  // Resources
  loadstart: {parent: ["media"], properties: ["lengthComputable", "loaded", "total"]},
  abort: {parent: ["generic"]}, // User aborts loading an element
  error: {parent: ["generic"]}, // Could not load image
  // Videos
  durationchange: {parent: ["media"]}, // Video duration changes. Don't know why.
  play: {parent: ["media"]}, // These two happen when a video is played / unpaused, with nuanced differences.
  playing: {parent: ["media"]},
  stalled: {parent: ["media"]},
  seeked: {parent: ["media"]}, //
  //  seeking: {parent: ["media"]}, <-- Many events
  // timeupdate <-- Many events
  canplay: {parent: ["media"]},
  canplaythrough: {parent: ["media"]},
  ended: {parent: ["media"]},
  loadeddata: {parent: ["media"]}, // First video frame available
  loadedmetadata: {parent: ["media"]}, // Audio / video metadata available
  pause: {parent: ["media"]},
  progress: {parent: ["media"]},
  ratechange: {parent: ["media"]},
  volumechange: {parent: ["media"]},
  waiting: {parent: ["media"]},
  suspend: {parent: ["media"]},

  // Mouse / pointer (probably done)
  // There is a transition from mouse events to pointer events, which also handle touch, pen, etc. events
  //pointermove: {parent: ["pointer"]},
  //pointerrawupdate: {parent: ["pointer"]},
  pointerup: {parent: ["pointer"]},
  pointercancel: {parent: ["pointer"]},
  //  pointerout: {parent: ["pointer"]},
  pointerleave: {parent: ["pointer"]},
  gotpointercapture: {parent: ["pointer"]},
  lostpointercapture: {parent: ["pointer"]},
  // Mouse events
  // wheel: {parent: ["mouse"], properties: ["deltaX", "deltaY", "deltaZ", "deltaMode", "wheelDelta"]}, // To do: debounce
  mousedown: {parent: ["mouse"]},
  mouseenter: {parent: ["mouse"]},
  mouseleave: {parent: ["mouse"]},
  //  mousemove: {properties: [], functions: {}}, <-- Massive number of events
  //  mouseover: {properties: [], functions: {}}, <-- Moderate number of events
  //  mouseout: {properties: [], functions: {}}, <-- Moderate number of events
  mouseup: {parent: ["mouse"]},
  // Touch events
  touchcancel: {parent: ["touch"]},
  touchend: {parent: ["touch"]},
  // touchmove: {parent: ["touch"]},
  touchstart: {parent: ["touch"]},
  // Pointer actions
  click: {parent: ["mouse"]},
  dblclick: {parent: ["mouse"]},
  contextmenu: {parent: ["pointer"]},
  show: {parent: ["generic"]}, // context menu
  // Scroll
  //  scroll: {parent: ["generic"]}, // Massive number of events. These sorts of events should be debounced, perhaps.
  scrollend: {parent: ["generic"], properties: [], functions: {}},  

  // Form / input-style elements
  change: {parent: ["generic"]}, // <input> changed. Typically when unfocused
  input: {parent: ["generic"], properties: ["data", "inputType"]}, // Similar, typically, keystoke-by-keystroke (web search for nuanced difference)
  invalid: {parent: ["generic"], properties: [], functions: {}},
  toggle: {parent: ["generic"], properties: [], functions: {}}, // Details opened or closed
  reset: {parent: ["generic"]}, // Form is reset
  submit: {parent: ["generic"]},

  // General
  DOMContentLoaded: {parent: ["generic"]},
  readystatechange: {parent: ["generic"]},
  prereadychange: {parent: ["generic"]},
  load: {parent: ["generic"]},
  unload: {parent: ["generic"]}, // Deprecated, but keeping around just in case it works. Page closed.
  beforeunload: {parent: ["generic"]}, // Should do the same thing, but work. May have spurious events if cancelled.
  pagehide: {parent: ["generic"], properties: ["persisted"]},
  pageshow: {parent: ["generic"], properties: ["persisted"]},
  hashchange: {parent: ["generic"], properties: ["newURL", "oldURL"]},
  fullscreenchange: {parent: ["generic"]},
  fullscreenerror: {parent: ["generic"]},
  offline: {parent: ["generic"]},
  online: {parent: ["generic"]},
  visibilitychange: {parent: ["generic"], functions: {visibility: (event) => document.visibilityState}},
  deviceorientation:  {parent: ["generic"]},

  // Element focus (probably done)
  blur: {parent: ["generic"]},
  focus: {parent: ["generic"]},
  focusin: {parent: ["generic"]},
  focusout: {parent: ["generic"]},
  // Printing
  afterprint: {parent: ["generic"]},
  beforeprint: {parent: ["generic"]},
  // PWA install
  appinstalled: {parent: ["generic"]},
  beforeinstallprompt: {parent: ["generic"]},
  // Selection
  select: {parent: ["generic"], functions: { selectionStart: (event) => event.target.selectionStart, selectionEnd: (event) => event.target.selectionEnd, selectionData }},
  selectionchange: {parent: ["generic"], functions: { selectionData }},

  // Uncategorized
//  message: {parent: ["generic"], properties: [], functions: {}}, <-- We want to avoid the possibility of infinite loops
//  open: {parent: ["generic"], properties: [], functions: {}}, <-- We want to avoid the possibility of infinite loops
//  resize: {parent: ["generic"], functions: { windowSize }},  <-- This would be helpful with a debounce, so we have the final resize

}


/*
  These functions navigated the structures above and integrate fields from parents
 */

// Helper for building event property list
function compileEventProperties(event) {
  let properties = [];
  if (event.parent) {
    event.parent.forEach((parentEvent) => {
      properties = properties.concat(compileEventProperties(parent_events[parentEvent]));
    });
  }
  if(event.properties) {
    properties = properties.concat(event.properties);
  }
  return properties;
}

// Helper for building event function dictionary
function compileEventFunctions(event) {
  let functions = {};
  if (event.parent) {
    event.parent.forEach((parentEvent) => {
      functions = { ...functions, ...compileEventFunctions(parent_events[parentEvent]) };
     });
  }
  functions = { ...functions, ...event.functions };
  return functions;
}

// Helper for building event function list
function compileEvent(event) {
  const properties = compileEventProperties(event);
  const functions = compileEventFunctions(event);
  
  return { properties, functions };
}

/*
  These functions extract relevant data from a given event
 */

// This grabs information about an element on a page, typically an event target.
function targetInfo(target) {
  let fields = copyFields(target, ["className", "nodeType", "localName", "tagName", "nodeName", "id", "value"]);
  if(target.classList) {
    fields.classlist = Array.from(target.classList);
  }

  return fields;
}

// This copies information about the targets and elements related to
// an event into a dictionary.
function copyTargets(event) {
  // These are the potential elements associated with an event
  // This is very redundant, but most of the redundancy disappears with compression.
  // We should consider scaling this back if these are identical, however, just for readability
  const targets = [
    "target",
    "currentTarget",
    "srcElement",
    "view",
    "relatedTarget"
  ];

  let compiledTargets = {};   // The information we return
  let uncompiledTargets = {}; // The actual target object themselves

  // For each candidate target which exists....
  targets.forEach((targetKey) => {
    if (event[targetKey]) {
      // Check if we've already processed it
      let duplicateKeys = Object.keys(uncompiledTargets).filter(key => {
        return uncompiledTargets[key] === event[targetKey];
      });
      // If so, we just add it to our list of duplicates
      if (duplicateKeys.length > 0) {
        if(!compiledTargets[duplicateKeys[0]].dupes) {
          compiledTargets[duplicateKeys[0]].dupes = [];
        }
        compiledTargets[duplicateKeys[0]].dupes.push(targetKey);
      // Otherwise, we include it in the main dictionary.
      } else {
        uncompiledTargets[targetKey] = event[targetKey];
        compiledTargets[targetKey] = targetInfo(event[targetKey]);
      }
    }
  });

  return compiledTargets;
}

export function lo_event_name(event) {
  return `browser.${events[event.type].parent[0]}.${event.type}`;
}

export function lo_event_props(event) {
  const { properties, functions } = compileEvent(events[event.type]);
  const copiedProperties = copyFields(event, properties);
  let props = {...copiedProperties, ...copyTargets(event)};
  for (const f in functions) {
    const d = functions[f](event);
    if(d) {
      props[f] = d;
    }
  }
  return props;
}

function debounce(func, wait) {
  // TODO
}

function eventListener(dispatch) {
  return function(event) {
    const eventType = lo_event_name(event);
    const browser_props = lo_event_props(event);

    const lodict = {
      browser_props
    };
    if (events[event.type].debounce) {
      lodict.debounced = true;
      debounce(
        eventType,
        () => dispatch(eventType, lodict)
      );
    } else {
      dispatch(eventType, lodict);
    }
  };
}

export function subscribeToEvents({ target = document, eventList = events, dispatch=console.log } = {}) {
  for (let key in eventList) {
    target.addEventListener(key, eventListener(dispatch));
  }
}
