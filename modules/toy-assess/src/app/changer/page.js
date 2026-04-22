// This is a little demo that retypes text as different characters.

'use client';
// @refresh reset

// We need to import this to call init() for now
import {  } from '../components.js';

import { ActionButton, Element, LLMAction, SideBarPanel, MainPane, TextInput, LLMFeedback } from 'lo_event/lo_event/lo_assess/components/components.jsx';

export default function Home( { children } ) {
  return (
    <SideBarPanel>
      <MainPane>
        <h1>Write a text</h1>
        <p>
          Put it in the box provided. After you get feedback and look at examples,
          feel free to revise your answer.
        </p>
        <TextInput id="student_essay" />
        <br />
        <LLMFeedback id="essay_rewrite"/>
      </MainPane>
      <div>
        <p> Rewrite / audience / style </p>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this in simple English for a first grader: <Element>student_essay</Element></LLMAction>
          First Grader Text
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this in contorted social sciences academic English: <Element>student_essay</Element></LLMAction>
          SSR
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this in business English, with a marketing focus: <Element>student_essay</Element></LLMAction>
          Business
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this in first person: <Element>student_essay</Element></LLMAction>
          First person
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">You're a world-class comedian. Please rewrite this to be hillarious, and with an edge. You can make stuff up (hey, it's comedy), but there should be real jokes (not just flippancy): <Element>student_essay</Element></LLMAction>
        Comedian
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this using a Chinese communication style, organization, and argumentation structure (e.g. as described by Hofstede or Meyer), but in English: <Element>student_essay</Element></LLMAction>
          Chinese American
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this text in legal English for a legal filing <Element>student_essay</Element></LLMAction>
          Lawyer
        </ActionButton>
        <br/>
        <ActionButton>
          <LLMAction target="essay_rewrite">Please rewrite this text as a lower-to-mid-level middle schooler. Please include middle-school level spelling errors, grammar errors, and style issues; we'll want middle-school students to find and correct issues: <Element>student_essay</Element></LLMAction>
          Middle Schooler
        </ActionButton>
      </div>
    </SideBarPanel>
  );
};
