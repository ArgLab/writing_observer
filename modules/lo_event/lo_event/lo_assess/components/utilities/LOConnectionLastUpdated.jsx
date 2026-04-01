/**
 * LOConnectionLastUpdated is a helper function for displaying
 * connection information and last received message information
 * about a websocket.
 *
 * Usage:
 * ```js
 * const { connectionStatus, message, } = LOConnection({ url, dataScope }); // or some other websocket
 * return ( <LOConnectionLastUpdated message={message} connectionStatus={connectionStatus} /> );
 * ```
 */
import React from 'react';
import { useState, useEffect } from 'react';
import { LO_CONNECTION_STATUS } from '../constants/LO_CONNECTION_STATUS';
import { renderTime } from '../../../util';

function renderReadableTimeSinceUpdate (timeDifference) {
  if (timeDifference < 5) {
    return 'Just now';
  }
  return `${renderTime(timeDifference)} ago`;
}

export const LOConnectionLastUpdated = ({ message, connectionStatus, showText=false }) => {
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastUpdatedMessage, setLastUpdatedMessage] = useState('');

  const icons = {
    [LO_CONNECTION_STATUS.UNINSTANTIATED]: 'fas fa-circle',
    [LO_CONNECTION_STATUS.CONNECTING]: 'fas fa-sync-alt',
    [LO_CONNECTION_STATUS.OPEN]: 'fas fa-check text-success',
    [LO_CONNECTION_STATUS.CLOSING]: 'fas fa-sync-alt',
    [LO_CONNECTION_STATUS.CLOSED]: 'fas fa-times text-danger'
  };
  const titles = {
    [LO_CONNECTION_STATUS.UNINSTANTIATED]: 'Uninstantiated',
    [LO_CONNECTION_STATUS.CONNECTING]: 'Connecting to server',
    [LO_CONNECTION_STATUS.OPEN]: 'Connected to server',
    [LO_CONNECTION_STATUS.CLOSING]: 'Closing connection',
    [LO_CONNECTION_STATUS.CLOSED]: 'Disconnected from server'
  };

  // Set last updated time when new message arrives
  useEffect(() => {
    if (message) {
      setLastUpdated(new Date());
    }
  }, [message]);

  // Every second update last updated message
  useEffect(() => {
    const interval = setInterval(() => {
      if (lastUpdated) {
        const now = new Date();
        const timeDifference = Math.floor((now - lastUpdated) / 1000); // Time difference in seconds
        setLastUpdatedMessage(renderReadableTimeSinceUpdate(timeDifference));
      } else { setLastUpdatedMessage('Never'); }
    }, 1000);
    return () => clearInterval(interval); // Cleanup interval on unmount
  }, [lastUpdated]);

  return (
    <div title={titles[connectionStatus]}>
      <i className={icons[connectionStatus]} />
      {showText ? <span className='mx-1'>{titles[connectionStatus]}</span> : ''}
      <span className='ms-1'>{lastUpdatedMessage}</span>
    </div>
  );
};
