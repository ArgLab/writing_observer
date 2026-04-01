import React, { Component } from "react";
import PropTypes from "prop-types";

/**
 * WOTextHighlight provides breakpoints and classes to allow for later highlighting.
 * It takes a property, `text`, and
 * and breaks it up based on all possible breakpoints in property `highlight_breakpoints`.
 * The text is output as a variety of spans with classnames corresponding to ids.
 */
export default class WOTextHighlight extends Component {
  // Define the render method for the component
  render() {
    // Destructure the props object and assign default values where necessary
    const {
      id,
      text = "",
      highlight_breakpoints = {},
      className = "",
    } = this.props;

    // Define arrays to hold the highlight information and breakpoints
    const highlights = [];
    const breakpoints = [0];

    // Iterate over the highlight_breakpoints object to extract highlight information
    Object.entries(highlight_breakpoints).forEach(([key, value]) => {
      value.value.forEach(([start, length]) => {
        // Add breakpoints for the start and end of the highlighted section
        breakpoints.push(start);
        breakpoints.push(start + length);
        // Add the highlight information to the highlights array
        highlights.push([start, start + length, key]);
      });
    });

    // Sort the highlight and breakpoint arrays in ascending order
    highlights.sort((a, b) => a[0] - b[0]);
    breakpoints.sort((a, b) => a - b);

    // Initialize the child variable with the original text, and update it if there are highlights
    let child = text;
    if (highlights.length > 0) {
      child = new Array();
      let start = 0;
      let end = 0;
      let classes = [];
      // Iterate over the breakpoints to split the text into highlighted and non-highlighted sections
      child = breakpoints.map((bp, i) => {
        start = bp;
        end = i === breakpoints.length - 1 ? text.length : breakpoints[i + 1];
        // Extract the current section of text
        const text_slice = text.slice(start, end);
        // Get the classes to apply to the current section of text based on the highlights
        classes = highlights
          .filter(([s, e]) => s <= start && e >= end)
          .map(([_, __, c]) => c)
          .join(" ");
        // Split the text by newline characters to handle multi-line highlights
        const text_newline_split = text_slice.split("\n");
        // Return a span element for the current section of text, with appropriate classes and line breaks
        return (
          <span key={`text-${start}-${end}`} className={classes}>
            {text_newline_split.length === 1
              ? text_slice
              : text_newline_split.map((line, i) => (
                <span key={i}>
                  {line}
                  {i === text_newline_split.length - 1 ? "" : <br />}
                </span>
              ))}
          </span>
        );
      });
    } else {
      const text_split = text.split("\n");
      child = text_split.length === 1
        ? child
        : text_split.map((line, i) => (
          <span key={i}>
            {line}
            {i === text_split.length - 1 ? "" : <br />}
          </span>
        ))
    }
    // Return a div element with the child elements and appropriate attributes
    return (
      <div
        key="text-highlight"
        className={`${className} WOTextHighlight`}
        id={id}
      >
        {child}
      </div>
    );
  }
}

WOTextHighlight.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * The text to be highlighted.
   */
  text: PropTypes.string,

  /**
     * highlight breakpoints in the form of:
     * `{
            "coresentences": {
                "id": "coresentences",
                "value": [
                    [
                        0,
                        13
                    ],
                    [
                        20,
                        25
                    ]
                ],
                "label": "Main ideas"
            },
        }`
     * 
     */
  highlight_breakpoints: PropTypes.object,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};
