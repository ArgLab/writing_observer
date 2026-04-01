import React from 'react';

import { useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { MathJax, MathJaxContext } from 'better-react-mathjax';
import { parse, format } from "mathjs";

import * as lo_event from 'lo_event';
import { useComponentSelector, useSettingSelector } from './utils.js';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };


export const UPDATE_INPUT = 'UPDATE_INPUT';

function handleInputChange(id) {
  return event => {
    if(DEBUG) {
      console.log("Dispatching", id, event.target.value);
    }

    lo_event.logEvent(
      UPDATE_INPUT, {
        id,
        value: event.target.value,
        selectionStart: event.target.selectionStart, //retrieved by the useEffect method below to reset cursor location
        selectionEnd: event.target.selectionEnd,    //stored for completeness, not absolutely neccesary
      });
  };
}

function fixCursor(id, selectionStart, selectionEnd) {
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

export function RenderEquation( { id }) {
  let value = useComponentSelector(id, s => s?.value)  ?? '';
  let equation='', raw_equation='';
  try {
    console.log("v>>>", value);
    let p = parse(value);
    console.log("p>>>", p);
    raw_equation = p.toTex();
    console.log("e>>>", raw_equation);
    equation = "\\("+raw_equation+"\\)";
    console.log("f>>>", equation);
  } catch {
    equation = value;
  }
  //equation = "\\(\\frac{10}{4x} \\approx 2^{12}\\)";
  console.log("mj>>>", equation);
  return <><MathJax
           dynamic
           hideUntilTypeset={"first"}
           inline
           > { equation } </MathJax>
           { raw_equation }
         </>;
}

export function LineInput( { defaultvalue, prompt, id, children } ) {
  prompt = prompt || "Answer: ";

  let value = useComponentSelector(id, s => s?.value) ?? defaultvalue ?? '';

  return (
    <div>
      { prompt }
      <input
        className="item-input"
        value={ value }
        onChange={ handleInputChange(id) }
      />
      {children}
    </div>
  );
}


export function NumericInput( { defaultvalue, prompt, id, children } ) {
  prompt = prompt || "Answer: ";

  let value = useComponentSelector(id, s => s?.value) ?? defaultvalue ?? '';

  return (
    <div>
      { prompt }
      <input
        className="item-input"
        type="number"
        value={ value }
        onChange={ handleInputChange(id) }
      />
      {children}
    </div>
  );
}

export function UnitInput( { id, children, prompt, units=["cm", "cm²"] } ) {
  const number_id = id+".number";
  const units_id = id+".units";

  let value = useComponentSelector(number_id, s => s?.value ?? '');
  let unit = useComponentSelector(units_id, s => s?.value ?? units[0]);

  prompt = prompt || "Answer: ";
  const handleNumberChange = handleInputChange(number_id);
  const handleUnitChange = handleInputChange(units_id);

  return (
    <div className="item-grader">
      { prompt } <input type="number" value={value} onChange={ handleNumberChange }/>
      <select onChange={ handleUnitChange } value={unit}>
        {units.map((u, i) => (
          <option key={ i } value={ u }>
            { u }
          </option>
        ))}
      </select>
      {children}
    </div>
  );
}

