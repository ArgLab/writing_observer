import React, { Component } from "react";
import PropTypes from "prop-types";
import ProgressBar from "react-bootstrap/ProgressBar";

/**
 * WOIndicatorBars provide progress bars.
 * It takes a property, `data`, and
 * outputs each item as a label/progress bar pair.
 * If the id of the item is not in the property `shown`,
 * it will not appear.
 */
export default class WOIndicatorBars extends Component {
  renderIndicatorBar = ([key, indicator], shown) => {
    const indicator_colors = ["danger", "warning", "success"];
    const INDICATOR_STEP = 34;
    if (!shown.includes(key)) {
      return null;
    }
    return (
      <div key={key} className="d-table-row">
        <div className="small d-table-cell text-nowrap">{indicator.label}:</div>
        <div className="d-table-cell w-100 align-middle">
          <ProgressBar
            key="indicator-bar"
            now={indicator.value}
            title={`${indicator.value}% ${indicator.help}`}
            variant={
              indicator_colors[Math.floor(indicator.value) / INDICATOR_STEP]
            }
          />
        </div>
      </div>
    );
  };

  render() {
    const { id, data, shown, className = "" } = this.props;

    const indicatorBars = Object.entries(data).map((entry) =>
      this.renderIndicatorBar(entry, shown)
    );

    return (
      <div
        key="indicator-bars"
        className={`WOIndicatorBars ${className} d-table`}
        id={id}
      >
        {indicatorBars}
      </div>
    );
  }
}

WOIndicatorBars.defaultProps = {
  shown: [],
  data: {},
};

WOIndicatorBars.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
     * Data for the metrics should be in form:
     * `{
            "transitions": {
                "id": "transitions",
                "value": 81,
                "label": "Transitions",
                "help": "Percentile based on total number of transitions used"
            },
        }`
     */
  data: PropTypes.object,

  /**
   * Which ids to show.
   */
  shown: PropTypes.array,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};
