import React from 'react';

import * as util from '../../util.js';
import { createAction } from '../actions.jsx';
import { run_llm } from './llm.jsx';

export const LLMAction = createAction({
  name: "LLMAction",
  f: ({node}) => {
    React.Children.forEach(node, (child) => {
      if (React.isValidElement(child) && child.type === LLMAction) {
        const promptText = util.extractChildrenText(child);
        run_llm(child.props.target, { prompt: promptText });
      }
    });
  }
});
