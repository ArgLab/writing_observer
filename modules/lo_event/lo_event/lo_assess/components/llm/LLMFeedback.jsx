import React from 'react';

import { useDispatch } from 'react-redux';
import { useComponentSelector } from '../../selectors.js';
import { extractChildrenText } from '../../util.js';
import { LLM_RUNNING, LLM_INIT } from './llm.jsx';
import { Spinner } from '../components.jsx';

export const LLMFeedback = ({children, id}) => {
  const dispatch = useDispatch();
  let feedback = useComponentSelector(id, s => s?.value ?? '');
  let state = useComponentSelector(id, s => s?.state ?? LLM_INIT);

  return (
    <div>
      <center> 🤖 </center>
      {state === LLM_RUNNING ? (<Spinner/>) : feedback}
    </div>
  );
};
