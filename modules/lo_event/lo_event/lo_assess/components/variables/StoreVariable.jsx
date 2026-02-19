import React from 'react';
import { useEffect } from 'react';
import { extractChildrenText } from '../../util.js';

import * as lo_event from '../../../lo_event.js';
import { STORE_VARIABLE } from '../../reducers.js';

export function StoreVariable({children, id}) {
  useEffect(
    () => {
      const text = extractChildrenText(children);
      lo_event.logEvent(
        STORE_VARIABLE, {
          id,
          value: text,
        });
    }, []);

  return <>{children}</>;
}
