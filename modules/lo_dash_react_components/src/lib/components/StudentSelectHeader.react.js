import React, { Component } from "react";
import PropTypes from "prop-types";
import classnames from "classnames";

/**
 * Displays a header menu for selecting students
 */
export default class StudentSelectHeader extends Component {
  /**
   * Constructor for the StudentSelectHeader component.
   *
   * @param {object} props - The props for the component.
   */
  constructor(props) {
    super(props);
    this.state = {
      showDropdown: false,
    };
    this.handleClick = this.handleClick.bind(this);
    this.iterateName = this.iterateName.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
  }

  /**
   * Toggles the visibility of the dropdown menu when the user clicks on the student name.
   */
  handleClick() {
    this.setState((prevState) => ({ showDropdown: !prevState.showDropdown }));
  }

  /**
   * Iterates through the list of students and updates the selected student accordingly.
   *
   * @param {number} offset - The offset to apply to the current student index.
   */
  iterateName(offset) {
    const { students, selectedStudent, setProps } = this.props;
    const curr_index = students.indexOf(selectedStudent);
    const new_name =
      students[
        curr_index + offset >= 0
          ? (curr_index + offset) % students.length
          : students.length - 1
      ];
    setProps({ selectedStudent: new_name });
  }

  /**
   * Handles the user selecting a new student from the dropdown menu.
   *
   * @param {string} name - The name of the selected student.
   */
  handleSelect(name) {
    const { setProps } = this.props;
    setProps({ selectedStudent: name });
    this.setState({ showDropdown: false });
  }

  /**
   * Renders the StudentSelectHeader component.
   *
   * @returns {JSX.Element} - The rendered component.
   */
  render() {
    const { id, className, students, selectedStudent } = this.props;
    const { showDropdown } = this.state;
    const classNames = classnames("student-select-header", className);

    return (
      <div id={id} className={classNames}>
        <header id="student-select-header" className="nav-header">
          <div className="button-left">
            <button className="button" onClick={() => this.iterateName(-1)}>
              &lt;
            </button>
          </div>
          <div className="header-student" onClick={this.handleClick}>
            {selectedStudent}
          </div>
          {showDropdown && (
            <ul className="dropdown">
              {students.map((name) => (
                <li
                  key={name}
                  onClick={() => this.handleSelect(name)}
                  className={
                    name === selectedStudent
                      ? "dropdown-item dropdown-item-selected"
                      : "dropdown-item"
                  }
                >
                  {name}
                </li>
              ))}
            </ul>
          )}
          <div className="button-right">
            <button className="button" onClick={() => this.iterateName(1)}>
              &gt;
            </button>
          </div>
        </header>
      </div>
    );
  }
}

StudentSelectHeader.propTypes = {
  /** A unique identifier for the component, used to identify it in Dash callbacks */
  id: PropTypes.string,

  /** A string of class names to be added to the outermost div */
  className: PropTypes.string,

  /** An array of student names to be displayed in the dropdown */
  students: PropTypes.arrayOf(PropTypes.string),

  /** The currently selected student name */
  selectedStudent: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,
};

StudentSelectHeader.defaultProps = {
  students: [],
  selectedStudent: "",
};
