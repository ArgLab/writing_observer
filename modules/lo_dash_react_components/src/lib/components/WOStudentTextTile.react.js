import React, { Component } from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Card from 'react-bootstrap/Card';

import LONameTag from './LONameTag.react';

/**
 * WOStudentTextTile
 */
export default class WOStudentTextTile extends Component {
  render () {
    const { id, className, style, showName, profile, currentStudentHash, currentOptionHash, childComponent, additionalButtons } = this.props;
    const isLoading = currentOptionHash !== currentStudentHash;
    let bodyClassName = isLoading ? 'loading' : '';
    bodyClassName = `${bodyClassName} overflow-auto position-relative`;

    return (
      <Card key={`WOStudentTextTile-${id}`} className={`WOStudentTextTile ${className}`} style={style} id={id}>
        <Card.Header>
          <LONameTag
            id='lo-name-tag'
            profile={profile || {}}
            includeName={true}
            className={showName ? 'd-inline-flex align-items-center' : 'd-none'}
          />
          <ButtonGroup className='float-end'>
            {isLoading && (
              <Button variant='transparent'>
                <div className='loading-circle'/>
              </Button>
            )}
            {additionalButtons && additionalButtons}
          </ButtonGroup>
        </Card.Header>
        <Card.Body className={bodyClassName}>
          {childComponent}
        </Card.Body>
      </Card>
    );
  }
}

WOStudentTextTile.defaultProps = {
  className: '',
  showName: true,
  style: {},
  profile: {}
};

WOStudentTextTile.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * Style to apply to the outer most item. This
   * is usually used to set the size of the tile.
   */
  style: PropTypes.object,

  /**
   * Determine whether the header with the student
   * name should be visible or not
   */
  showName: PropTypes.bool,

  /**
   * Hash of the current options, used to determine if we
   * should be in a loading state or not.
   */
  currentOptionHash: PropTypes.string,

  /**
   * Hash of the current student, used to determine if we
   * should be in a loading state or not.
   */
  currentStudentHash: PropTypes.string,

  /**
   * Component to use for within the card body
   */
  childComponent: PropTypes.node,

  /**
   * Buttons to add to the button group
   */
  additionalButtons: PropTypes.node,

  /**
   * The profile of the student
   */
  profile: PropTypes.object,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func
};
