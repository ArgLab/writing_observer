// Demo to show the Websocket

'use client';
// @refresh reset

// We need to import this to call init() for now
import { } from '../components.js';

import React, { useState, useEffect } from 'react';
import { LOConnectionLastUpdated, useLOConnectionDataManager, LO_CONNECTION_STATUS, Button } from 'lo_event/lo_event/lo_assess/components/components.jsx';

export default function Home ({ children }) {
  const decoded = {};
  decoded.course_id = '123456';
  const dataScope = {
    wo: {
      execution_dag: 'writing_observer',
      target_exports: ['docs_with_nlp_annotations'],
      kwargs: decoded
    }
  };

  const { data, errors, connection } = useLOConnectionDataManager({ url: 'ws://localhost:8888/wsapi/communication_protocol', dataScope });
  return (
    <div>
      <h1>WebSocket Connection Page</h1>
      <div>
        <LOConnectionLastUpdated message={data} connectionStatus={connection.connectionStatus} showText />
      </div>
      <div>
        <Button onClick={() => connection.sendMessage(JSON.stringify(dataScope))} disabled={connection.connectionStatus !== LO_CONNECTION_STATUS.OPEN}>
          Re-send dataScope to Server
        </Button>
        <Button onClick={connection.openConnection} disabled={connection.connectionStatus === LO_CONNECTION_STATUS.OPEN || connection.connectionStatus === LO_CONNECTION_STATUS.CONNECTING}>
          Open Connection
        </Button>
        <Button onClick={connection.closeConnection} disabled={connection.connectionStatus !== LO_CONNECTION_STATUS.OPEN}>
          Close Connection
        </Button>
      </div>
      <div>
        <h2>User Data</h2>
          {Object.keys(data).length > 0
            ? (<pre>{JSON.stringify(data, null, 2)}</pre>)
            : (<p>No user data available.</p>)
          }
      </div>
      {Object.keys(errors).length > 0 && (
        <div style={{ color: 'red' }}>
          <h2>Errors</h2>
          <pre>{JSON.stringify(errors, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
