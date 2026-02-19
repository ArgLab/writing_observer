import React from 'react';

import * as util from '../../util.js';
import { createAction } from '../actions.jsx';

export const PopupAction = createAction({
  name: "PopupAction",
  f: ({node}) => alert(util.extractChildrenText(node))
});
