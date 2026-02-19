/* eslint-disable no-magic-numbers */

const testData = {
  id: "text-highlight-test",
  text: "This is a test of the text highlight component.\nThis is a new line of text data.\n\n\nHow about 3 new lines?",
  highlight_breakpoints: {
    testHighlight: {
      id: "testHighlight",
      value: [
        [5, 7],
        [19, 28],
      ],
      label: "Test Highlight",
    },
  },
  className: "highlight-container",
};

export default testData;
