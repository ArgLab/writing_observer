import React from 'react';

/*
  This function extracts the text content from the children of a React
  element. If the element itself is a string, it trims and returns the
  string. If the element is a React element, it recursively extracts
  and concatenates the text content from its children.

  This is helpful if we want to e.g. send such text to an LLM or another
  action.
*/
export const extractChildrenText = (element) => {
  if (typeof element === "string") {
    return element.trim();
  }
  const extractElementText = (element) => {
    if (typeof element === "string") {
      return element.trim();
    } else if (React.isValidElement(element)) {
      return element.type.eval(element);
    }
    return "";
  };

  const { children } = element.props;
  const extractedChildren = React.Children.map(children, (element) => extractElementText(element));
  return extractedChildren.join("");
};
