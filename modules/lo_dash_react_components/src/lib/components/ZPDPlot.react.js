/*
 * Traditional, per-student Vygotskian display of which concepts are in the zone of
 * proximal development, actual development, and which a student cannot do
 */

import React from 'react';
import PropTypes from 'prop-types';
import { Arrow, LEFT, updateArrowPositions, initArrows } from './helperlib';
import StudentSelectHeader from "./StudentSelectHeader.react";

/* Gives information about one card for one student. */
function ZPDItemCard({id, cardIndex, cardCount, itemName, visited, attempts, supports, zone}) {
  const halfCircle = 180;
  const cardAngle = halfCircle * (cardIndex+1) / (cardCount+1);
  const cardOffsetRadius = 0.8;
  return (
    <div className="item-card" id={id}>
      <div className="card-header">{itemName}</div>
      <div className="card-table">
        <div className="card-row">
          <div className="card-cell" title="Visited">Visited</div>
          <div className="card-cell" title="Attempts">Attempts</div>
          <div className="card-cell" title="Supports">Supports</div>
        </div>
        <div className="card-row">
          <div className="card-cell" title="Visited">{visited ? "✓" : "X"}</div>
          <div className="card-cell" title="Attempts">{attempts}</div>
          <div className="card-cell" title="Supports">{supports}</div>
        </div>
      </div>
      {(zone !== "None") && (<Arrow
      	                       source={id}
      	                       sourceOffset={LEFT}
      	                       target={`${zone.toLowerCase()}-circle`}
      	                       targetOffset={[cardOffsetRadius, cardAngle]}
                             />)}
    </div>
  );
}

ZPDItemCard.propTypes = {
  cardIndex: PropTypes.number.isRequired,
  cardCount: PropTypes.number.isRequired,
  id: PropTypes.string.isRequired,
  itemName: PropTypes.string.isRequired,
  visited: PropTypes.bool.isRequired,
  attempts: PropTypes.string.isRequired,
  supports: PropTypes.string.isRequired,
  zone: PropTypes.string,
};

/* Static display of the three zones */
const ZPDRing = (_props) => {
  return (
    <div className="left-column">
      <div className="znd-circle" id="znd-circle">
	      <div className="label znd-circle-label">Can't do</div>
        <div className="zpd-circle" id="zpd-circle">
	        <div className="zpd-label zpd-circle-label">Zone of Proximal Development</div>
	        <div className="zad-circle" id="zad-circle">
	          <div className="label">Mastery</div>
	        </div>
        </div>
      </div>
    </div>
  );
}

/**
 * This is a component which shows which zones different problems fall into for a given student.
 */
export default class ZPDPlot extends React.Component {
  componentDidMount() {
    updateArrowPositions();
  }

  render() {
    const { ZPDItemCards, setProps, students, selectedStudent } = this.props;

    return (
      <div id="zpd-wrapper" className="zpd-wrapper arrow-wrapper">
        <StudentSelectHeader
          selectedStudent={selectedStudent}
          students={students}
          setProps={setProps}
        />
        <ZPDRing id="ring" />
        <div id="zpd-wrapper">
          <div className="right-column">
            {ZPDItemCards.map((card, index) => (
              <ZPDItemCard
                key={card.id}
                cardIndex={index}
                cardCount={ZPDItemCards.length}
                {...card}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }
}

ZPDPlot.defaultProps = {};

ZPDPlot.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,
  /**
   * A list of all available students. This is so we can select a student.
   * This should be moved out of this, one level up, so the logic is common
   * to any per-student view.
   */
  students: PropTypes.arrayOf(PropTypes.string),
  /**
   * Data for cards for the items students worked through.
   */
  ZPDItemCards: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string,
    itemName: PropTypes.string,
    zone: PropTypes.string,
    attempts: PropTypes.string,
    supports: PropTypes.string,
    visited: PropTypes.bool
  })).isRequired,
  /**
   * The current student for whom we're showing data
   */
  selectedStudent: PropTypes.string,
  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func
};

initArrows();
