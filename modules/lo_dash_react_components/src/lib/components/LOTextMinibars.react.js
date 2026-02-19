/* Create a mini-bar-graph showing rhythm of text. Each bar represents
 * the length of one sentences, and each group of bars, one paragraph.
 *
 * It's not clear if this is an MVP yet; sentences should be stacked
 * bars (showing words), and sections should be clearly indicated.
 *
 * We'll also want to figure out how to handle multiple student texts
 * on one page, and in particular, axes and scaling.
 */

import * as React from 'react';
import PropTypes from "prop-types";

import { BarChart, Bar, Cell, Tooltip, XAxis, YAxis } from 'recharts';

const DEFAULT_HEIGHT = 60;
const DEFAULT_WIDTH = 200;

// Split the text based on newlines or multiple newlines
function segmentTextIntoParagraphs(text) {
  return text.split(/\n+/).filter(paragraph => paragraph.trim() !== "");
}

// Split the text based on newlines or multiple newlines
function segmentParagraph(paragraph) {
  // Regular expression to match sentence-ending punctuation
  const sentenceEnd = /[.?!]/g;
  return paragraph.split(sentenceEnd).filter(Boolean).map(s => s.trim());
}

function segmentParagraphsIntoSentences(paragraphs) {
  // Map the segmentParagraph function over each paragraph
  return paragraphs.map(segmentParagraph);
}

// Count the number of words in a sentence
function countWords(text) {
  return text.split(/\s+/).length;
}

/**
 * Annotates each sentence in a list of paragraphs with its corresponding word count.
 *
 * @param {Array} list - A list of paragraphs, where each paragraph is a list of sentences.
 *
 * @returns {Array} A list of paragraphs, where each paragraph is a list of objects representing sentences.
 * Each object has two properties: 'text' (the sentence text) and 'count' (the number of words in the sentence).
 *
 * @example
 *
 * const paragraphs = [['This is the first sentence.', 'This is the second sentence.'], ['Another paragraph with one sentence.']];
 * const annotatedParagraphs = annotateWithWordCount(paragraphs);
 * // annotatedParagraphs is now:
 * // [
 * //   [
 * //     { text: 'This is the first sentence.', count: 5 },
 * //     { text: 'This is the second sentence.', count: 5 }
 * //   ],
 * //   [
 * //     { text: 'Another paragraph with one sentence.', count: 5 }
 * //   ]
 * // ]
 */
function annotateWithWordCount(list) {
  return list.map((sentences) => 
    sentences.map((sentence) => ( {
      text: sentence,
      count: countWords(sentence)
    }))
  )
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{`${payload[0].payload.name}`}</p>
      </div>
    );
  }
  return (<div/>)
};

CustomTooltip.propTypes = {
  active: PropTypes.bool.isRequired,
  payload: PropTypes.arrayOf(PropTypes.shape({
    payload: PropTypes.shape({
      name: PropTypes.string.isRequired
    }).isRequired
  })).isRequired
};

/**
 * A component that renders a miniature bar graph representation of text, where each bar represents a sentence, and each
 * set of bars, a paragraph
 */
export default class LOTextMinibars extends React.Component {
  /**
   * Prepares the chart data from the given text and yscale value
   * @param {string} text - The input text
   * @param {number} [ymax] - The scaling factor for the y-axis. This is used if there are multiple graphs on the same page (optional)
   * @returns {object[]} The chart data, an array of objects with properties: name, value, group, fill
   */
  prepareChartData = (text) => {
    const annotatedTextLength = annotateWithWordCount(segmentParagraphsIntoSentences(segmentTextIntoParagraphs(text)));
    const angleGoldenRatio = 137.5;
    const DegreesInACircle = 360
    const ratioColor = index => `hsl(${(index * angleGoldenRatio) % DegreesInACircle}, 75%, 75%)`;
    const chartData = annotatedTextLength.flatMap((array, index) => [
      ...array.map(value => ({ name:value.text, value: value.count, group: index, fill: ratioColor(index) })),
      { value: 0, group: -1, name: '' }
    ]).slice(0, -1);
    return chartData;
  }

  render() {
    const { text, height = DEFAULT_HEIGHT, width = DEFAULT_WIDTH, ymax, xmax, className } = this.props;
    const chartData = this.prepareChartData(text);
    console.log(chartData);
    return (
      <div className={`${className || ''} LOTextMinibars`}>
        <BarChart height={height} width={width} data={chartData}>
          <Tooltip content={<CustomTooltip/>}/>
          <Bar dataKey="value">
            {
              chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} stroke={entry.fill} fill={entry.fill}>
                </Cell>
              ))
            }
          </Bar>
          {
            xmax && <XAxis domain={[0, xmax]} />
          }
          {
            ymax && <YAxis domain={[0, ymax]} />
          }
        </BarChart>
      </div>
    );
  }
}

LOTextMinibars.propTypes = {
  /**
   * The text from which the chart is generated
   */
  text: PropTypes.string.isRequired,
  /**
   * Optional: A class to attach to the main div of the chart
   */
  className: PropTypes.string,
  /**
   * Optional: The height of the chart
   */
  height: PropTypes.number,
  /**
   * Optional: The height of the chart
   */
  width: PropTypes.number,
  /**
   * Optional: The maximum value of x-axis on the chart (e.g. number
   * of sentences + paragraph breaks). Leave blank to autorange
   */
  xmax: PropTypes.number,
  /**
   * Optional: The maximum value of y-axis on the chart (e.g. maximum
   * sentence length). Leave blank to autorange
   */
  ymax: PropTypes.number,
};
