import React from 'react';

import './Button.css';

/*
 * Parent of all buttons!
 */
export function Button( {...props} ) {
  const className = props.className ?? "blue-button";
  return <button className={className} {...props}/>;
}
