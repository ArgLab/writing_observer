import React, { Component } from 'react';
import PropTypes from 'prop-types';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover';

import 'react-tooltip/dist/react-tooltip.css';

/**
 * WOAnnotatedText
 */
export default class WOAnnotatedText extends Component {
  constructor (props) {
    super(props);
    this.state = {
      selectedItem: null
    };
  }

  replaceNewLines = (str) => {
    const split = str.split('\n');
    if (split.length > 1) {
      return split.map((line, index) => (
        <React.Fragment key={index}>
          {line}
          {split.length - 1 === index ? <span/> : <br/>}
        </React.Fragment>
      ));
    }
    return str;
  };

  render () {
    const { breakpoints, text, className } = this.props;

    const breaks = new Set();
    breakpoints.forEach(obj => {
      breaks.add(obj.start);
      breaks.add(obj.start + obj.offset);
    });
    breaks.add(0);
    breaks.add(text.length);

    const ids = {};
    breaks.forEach(item => {
      ids[item] = [];
    });

    const breaksList = [...breaks].sort((a, b) => a - b);
    let matchingBreaks = [];

    breakpoints.forEach(obj => {
      matchingBreaks = breaksList.filter(v => (v >= obj.start & v < (obj.start + obj.offset)));
      matchingBreaks.forEach(b => {
        ids[b] = ids[b].concat({ tooltip: obj.tooltip, style: obj.style });
      });
    });

    const chunks = Array(breaksList.length - 1);
    let curr, textChunk;
    for (let i = 0; i < chunks.length; i++) {
      curr = ids[breaksList[i]];
      textChunk = text.substring(breaksList[i], breaksList[i + 1]);
      if (curr.length === 0) {
        chunks[i] = {
          text: textChunk,
          annotated: false
        };
      } else {
        chunks[i] = {
          text: textChunk,
          annotated: true,
          id: i,
          tooltip: curr.map(o => o.tooltip),
          style: curr[0].style
        };
      }
    }

    if (chunks.length === 0) {
      return <div className={className}>
        {this.replaceNewLines(text)}
      </div>;
    }

    // TODO figure out how empty breakpoints
    if (chunks[chunks.length - 1].end < text.length) {
      chunks.push({
        text: text.substring(chunks[chunks.length - 1].end),
        annotated: false
      });
    }
    return (
      <div className={className}>
        {chunks.map((chunk, index) => (
          chunk.annotated
            ? <OverlayTrigger
              key={index}
              placement='bottom'
              overlay={
                <Popover>
                  <Popover.Header as="h3">Annotations</Popover.Header>
                  <Popover.Body>
                  <ul>
                    {[...new Set(chunk.tooltip)].map((item, index) => (
                      <li key={index}>
                        {item}
                      </li>
                    ))}
                  </ul>
                  </Popover.Body>
                </Popover>
              }
            >
              <span style={chunk.style}>
                {this.replaceNewLines(chunk.text)}
              </span>
            </OverlayTrigger>
            : <span key={index}>
              {this.replaceNewLines(chunk.text)}
            </span>
        ))}
      </div>
    );
  }
}

WOAnnotatedText.defaultProps = {
  id: '',
  className: '',
  text: '',
  breakpoints: []
};

WOAnnotatedText.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * The breakpoints of our text
   */
  breakpoints: PropTypes.arrayOf(PropTypes.exact({
    id: PropTypes.string,
    start: PropTypes.number,
    offset: PropTypes.number,
    tooltip: PropTypes.string,
    style: PropTypes.object
  })),

  /**
   * Text of essay
   */
  text: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func
};
