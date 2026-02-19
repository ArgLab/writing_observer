import React from 'react';
import * as reduxLogger from '../../../reduxLogger.js';
import { Button } from './Button.jsx';

/*
 * Reset the system state
 *
 * This should be folded into action button?
 */
export function ResetButton({children, ...props}) {
  return (
    <Button onClick={() => reduxLogger.setState({})} {...props} >
      { children }
    </Button>
  );
}
