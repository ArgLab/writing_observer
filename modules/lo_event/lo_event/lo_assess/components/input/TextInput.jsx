import React from 'react';
import { useEffect } from 'react';

import { fixCursor, handleInputChange } from './inputHelpers.js';
import { useComponentSelector, useSettingSelector } from '../../selectors.js';

export function TextInput({id, className, children}) {
  let value = useComponentSelector(id, s => s?.value ?? '');
  let selectionStart = useComponentSelector(id, s => s?.selectionStart ?? 1);
  let selectionEnd = useComponentSelector(id, s => s?.selectionEnd ?? 1);

  useEffect(fixCursor(id, selectionStart, selectionEnd), [value]);

  return (
    <>
      { children }
      <textarea
        name={id}
        className={className || "large-input"}
        required=""
        value={value}
        onChange={ handleInputChange(id) }
      ></textarea>
    </>
  );
}
