import React, { Component } from "react";
import PropTypes from "prop-types";

/**
 * LOCollapse provides a simple collapsible component with a title
 */
export default class LOCollapse extends Component {

  handleClick = () => {
    this.props.setProps({is_open: !this.props.is_open})
  }

  render() {
    const { is_open, children, label, className, id } = this.props

    return (
      <div id={id} className={`LOCollapse ${className}`}>
        <div onClick={this.handleClick}>
          <span className='me-1'>{label}</span>
          <i className={is_open ? 'fas fa-caret-up' : 'fas fa-caret-down'} />
        </div>
        <div className={`contents ${is_open ? 'expanded' : ''}`}>
          {children}
        </div>
      </div>
    )
  }
}
LOCollapse.defaultProps = {
  id: "",
  className: "",
  label: '',
  is_open: false,
};

LOCollapse.propTypes = {
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
   * The children of the main window
   */
  label: PropTypes.node,

  /**
   * Which panels (by id) are currently being is_open
   */
  is_open: PropTypes.bool,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};
