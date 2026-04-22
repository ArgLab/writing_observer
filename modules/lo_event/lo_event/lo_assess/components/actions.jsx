import React from 'react';

import * as util from '../util.js';

export function createAction({f, name}) {
  let Action = ({props}) => (<></>);
  Action.isAction = true;
  Action.action = f;
  Object.defineProperty(Action, 'name', {value: name, writable: false});
  return Action;
}

/*
export function LLMPrompt({children}) {
  return <></>;
}

export const reset=() => reduxLogger.setState({});
*/
