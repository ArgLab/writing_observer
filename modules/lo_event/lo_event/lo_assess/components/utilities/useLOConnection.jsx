/**
 * useLOConnection is a websocket hook used for connecting to
 * the communication protocl on Learning Observer.
 *
 * The server expects some data before it will start sending messages.
 * When the connection opens, useLOConnection will send the `dataScope`,
 * if available, to initiate receiving messages from the server.
 * Otherwise, users should use the `sendMessage` function to provide
 * data to LO.
 *
 * useLOConnection exposes the following items:
 * - `sendMessage`: function to send messages to the server
 * - `message`: the most recent message received
 * - `error`: any errors that occured
 * - `connectionStatus`: the current status of the websocket connection
 * - `openConnection`: function that opens the connection when called
 * - `closeConnection`: function that closes the connection when called
 */
import React from 'react';
import { useEffect, useRef, useState } from 'react';
import { LO_CONNECTION_STATUS } from '../constants/LO_CONNECTION_STATUS';

export const useLOConnection = ({
  url, dataScope
}) => {
  const [connectionStatus, setConnectionStatus] = useState(LO_CONNECTION_STATUS.CLOSED);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const clientRef = useRef(null);

  // Function to open the WebSocket connection
  const openConnection = () => {
    // Prevent opening a new connection if one is already open or connecting
    if (clientRef.current && (clientRef.current.readyState === LO_CONNECTION_STATUS.OPEN || clientRef.current.readyState === LO_CONNECTION_STATUS.CONNECTING)) {
      console.warn("WebSocket connection is already open or in progress.");
      return;
    }

    const protocol = { 'http:': 'ws:', 'https:': 'wss:' }[window.location.protocol];
    const newUrl = url || `${protocol}//${window.location.hostname}:${window.location.port}/wsapi/communication_protocol`;
    const client = new WebSocket(newUrl);
    clientRef.current = client;

    client.onopen = () => {
      setConnectionStatus(LO_CONNECTION_STATUS.OPEN);
      setError(null);  // Clear any previous errors upon a successful connection
      if (typeof dataScope !== 'undefined') {
        client.send(JSON.stringify(dataScope));
      }
    };

    client.onmessage = (event) => {
      setMessage(event.data);
    };

    client.onerror = (event) => {
      setError(event.message);
    };

    client.onclose = () => {
      setConnectionStatus(LO_CONNECTION_STATUS.CLOSED);
    };
  };

  // Function to close the WebSocket connection manually
  const closeConnection = () => {
    if (clientRef.current && connectionStatus === LO_CONNECTION_STATUS.OPEN) {
      clientRef.current.close();
      clientRef.current = null;
    } else {
      console.warn("WebSocket is not open; no connection to close.");
    }
  };

  // Automatically attempt to open connection on mount
  useEffect(() => {
    openConnection();

    // Cleanup on unmount
    return () => {
      closeConnection();
    };
  }, [url]);  // Include `url` as a dependency in case it changes and requires a reconnection

  const messageQueue = [];

  // Send any messages on the queue
  const processQueue = () => {
    while (messageQueue.length > 0) {
      if (clientRef.current && connectionStatus === LO_CONNECTION_STATUS.OPEN) {
        const message = messageQueue.shift();
        clientRef.current.send(message);
      } else {
        break;
      }
    }
  };

  // Start processing the queue when the connection opens
  useEffect(() => {
    if (connectionStatus === LO_CONNECTION_STATUS.OPEN) {
      processQueue();
    }
  }, [connectionStatus]);

  // Function to send a message via WebSocket
  const sendMessage = (message) => {
    if (clientRef.current && connectionStatus === LO_CONNECTION_STATUS.OPEN) {
      clientRef.current.send(message);
    } else {
      messageQueue.push(message);
    }
  };

  return { sendMessage, message, error, connectionStatus, openConnection, closeConnection };
};
