import React, { useState } from 'react';
import PropTypes from "prop-types";

const LOTableView = ({ children }) => {
  const [leftPanel, rightPanel] = children;

  return (
    <div style={{ display: "flex", height: "100vh" }} className="LOTableView">
      {/* Left Panel */}
      <div style={{ flex: 1, backgroundColor: "gray" }}>
        {leftPanel}
      </div>

      {/* Right Panel */}
      <div style={{ width: 200, backgroundColor: "lightgray" }}>
        {rightPanel}
      </div>
    </div>
  );
};

LOTableView.propTypes = {
  children: PropTypes.arrayOf(PropTypes.element).isRequired,
}

const LOControls = ({ title, options, selectedOption, onOptionChange }) => {
  return (
    <div className="LOControls">
      <h2>{title}</h2>
      {options.map((option) => (
        <label key={option}>
          <input
            type="radio"
            value={option}
            name={title}
            checked={selectedOption === option}
            onChange={onOptionChange}
          />
          {option}
        </label>
      ))}
    </div>
  );
};

LOControls.propTypes = {
  title: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  selectedOption: PropTypes.string.isRequired,
  onOptionChange: PropTypes.func.isRequired,
};

const LOOptions = ({ children }) => {
  return <div className="LOOptions">{children}</div>;
};

LOOptions.propTypes = {
  children: PropTypes.arrayOf(PropTypes.element).isRequired,
};

const CardList = ({ cards }) => {

  const [isGridLayout, setIsGridLayout] = useState(false);

  // Debug code, so we can see both layouts easily.
  const handleClick = () => {
    setIsGridLayout(!isGridLayout);
  };

  return (
    <div className={`card-list${isGridLayout ? ' card-grid-layout' : ''}`} onClick={handleClick}>
      {cards.map((item, index) => (
        <div className="card" key={index} style={{ backgroundColor: item.color }}>
          <div className="column" key={index}>
            <img className="avatar" src={item.avatar} />
            <div className="name">{item.name}</div>
          </div>
          <div className="columns">
            {item.columns.map((column, index) => (
              <div className="column" key={index}  title={item.tooltip}>
                <div className="label">{column.label}</div>
                <div className="value">{column.value}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * PropTypes for the columns of the table
 */
const columnPropTypes = PropTypes.shape({
  /** Column header label */
  label: PropTypes.string.isRequired,
  /** Data type of column values can be string, number, or boolean */
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
  ]).isRequired,
});

/**
 * PropTypes for a single card
 */
const cardPropTypes = PropTypes.shape({
  /** Unique identifier for the card */
  id: PropTypes.string.isRequired,
  /** Name of the user displayed on the card */
  name: PropTypes.string.isRequired,
  /** URL for the user's profile picture */
  picture: PropTypes.string.isRequired,
  /** Array of columns to display on the card */
  columns: PropTypes.arrayOf(columnPropTypes).isRequired,
  /** Optional color for the card background */
  color: PropTypes.string,
});

/**
 * PropTypes for the CardList component
 */
CardList.propTypes = {
  /** Array of cards to display in the list */
  cards: PropTypes.arrayOf(cardPropTypes).isRequired,
};

const LOStudentTable = ({ cards, controlGroups }) => {
  // Use the useState hook to keep track of which option is selected
  const [selectedOptions, setSelectedOptions] = useState({});

  const handleOptionChange = (event) => {
    const { name, value } = event.target;
    console.log(name, value);
    setSelectedOptions((prevSelectedOptions) => ({
      ...prevSelectedOptions,
      [name]: value,
    }));
  };

  return (
    <div className="LOStudentTable">
      <LOTableView>
        <CardList cards={cards}/>
        <LOOptions>
          {/* Use the map function to render multiple control groups */}
          {controlGroups.map(({ title, options }) => (
            <LOControls
              key={title}
              title={title}
              options={options}
              selectedOption={selectedOptions[title]}
              onOptionChange={handleOptionChange}
            />
          ))}
        </LOOptions>
      </LOTableView>
    </div>
  );
}

LOStudentTable.propTypes = {
  /** Array of cards to display in the list */
  cards: PropTypes.arrayOf(cardPropTypes).isRequired,
  /** Array of control groups to display */
  controlGroups: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      options: PropTypes.arrayOf(PropTypes.string).isRequired,
    })
  ).isRequired,
};

export default LOStudentTable;
