import React from 'react';

import * as lo_event from '../../../lo_event.js';
import { UPDATE_INPUT } from '../../reducers.js';

export function handleInputChange(id) {
  return event => {
    lo_event.logEvent(
      UPDATE_INPUT, {
        id,
        value: event.target.value,
        selectionStart: event.target.selectionStart, //retrieved by the useEffect method below to reset cursor location
        selectionEnd: event.target.selectionEnd,    //stored for completeness, not absolutely neccesary
      });
  };
}

export function fixCursor(id, selectionStart, selectionEnd) {
  return () => {
    //This will fire after the textarea is rendered and value has changed
    //Without this code, the cursor in the textarea will jump to the end of the
    //text, making editing the text in the middle difficult.
    const input = document.getElementsByName(id);
    if (input) {
      input[0].setSelectionRange(selectionStart, selectionEnd);
    }
  };
}
