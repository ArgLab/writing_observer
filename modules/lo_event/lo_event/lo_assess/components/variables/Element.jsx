import React from 'react';
import { useComponentSelector } from '../../selectors.js';
import { store } from '../../../reduxLogger.js';

export function Element({children}) {
  const id=children.trim();
  const value = useComponentSelector(id, s => s?.value);

  return <>{value}</>;
}

Element.eval = function(element) {
  const value=store.getState()?.application_state?.component_state?.[element.props.children.trim()]?.value;
  return value;
}
