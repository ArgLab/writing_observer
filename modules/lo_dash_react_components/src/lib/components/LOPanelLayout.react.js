import React, { Component } from "react";
import PropTypes from "prop-types";

/**
 * LOPanelLayout provides the image and name pair for a given profile
 */
export default class LOPanelLayout extends Component {
  render() {
    const { id, className, children, panels, shown } = this.props

    const shownPanels = panels.filter(panel => shown.includes(panel.id));
    const totalPanelWidth = shownPanels.reduce((total, panel) => total + parseFloat(panel.width), 0);

    let leftPanels = panels.filter(panel => panel.side === 'left');
    let rightPanels = panels.filter(panel => panel.side !== 'left');

    leftPanels = leftPanels.sort((a, b) => a.offset - b.offset);
    rightPanels = rightPanels.sort((a, b) => a.offset - b.offset);

    const mainContentWidth = `${100 - totalPanelWidth}%`;

    return (
      <div id={id} className={`LOPanelLayout ${className}`}>
        {leftPanels.map(panel =>
          <div
            key={panel.id}
            className={`${panel.className} ${shown.includes(panel.id) ? 'side-panel open' : 'side-panel closed'}`}
            style={{ width: shown.includes(panel.id) ? panel.width : 0 }}
          >
            {panel.children}
          </div>
        )}
        <div className="main-content" style={{ width: mainContentWidth }}>
          {children}
        </div>
        {rightPanels.map(panel =>
          <div
            key={panel.id}
            className={`${panel.className} ${shown.includes(panel.id) ? 'side-panel open' : 'side-panel closed'}`}
            style={{ width: shown.includes(panel.id) ? panel.width : 0 }}
          >
            {panel.children}
          </div>
        )}
      </div>
    )
  }
}
LOPanelLayout.defaultProps = {
  id: "",
  className: "",
  panels: [],
  shown: []
};

LOPanelLayout.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * The children of the main window
   */
  children: PropTypes.node,

  /**
   * The panels to be included in the display
     */
  panels: PropTypes.arrayOf(PropTypes.exact({
    children: PropTypes.node,
    width: PropTypes.string,
    offset: PropTypes.number,
    side: PropTypes.string,
    className: PropTypes.string,
    id: PropTypes.string.isRequired
  })),

  /**
   * Which panels (by id) are currently being shown
   */
  shown: PropTypes.arrayOf(PropTypes.string),

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};
