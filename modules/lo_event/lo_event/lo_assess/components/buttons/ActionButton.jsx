import React from 'react';
import * as reduxLogger from '../../../reduxLogger.js';
import { Button } from './Button.jsx';

export function executeChildActions(children) {
  console.log("Running child actions");
  console.log(children);
  React.Children.forEach(children, (child) => {
    console.log("eca:", child);
    if (React.isValidElement(child)) {
      console.log("eca.type:", child.type);
      console.log("eca.type.isaction:", child.type.isAction);
      console.log("ive:", React.isValidElement(child));
    }
    if (React.isValidElement(child) && child.type.isAction) {
      console.log("Running executor");
      child.type.action( { node: child } );
    }
  });
}

export const ActionButton = ({ children, target, systemPrompt, showPrompt = true, ...props }) => {
  const onClick = () => executeChildActions(children);
  return (
      <Button onClick={onClick} {...props} > { children } </Button>
  );
}
