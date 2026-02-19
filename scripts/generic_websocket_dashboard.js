/*
  Simple Node.js websocket client for exercising the communication protocol.

  Update the REQUEST payload to point at the execution DAG and exports you want
  to test.
*/

// Remove this line when running within a browser terminal (i.e. non-Node.js environment)
const WebSocket = require('ws');

const SERVER = 'ws://localhost:8888/wsapi/communication_protocol';

const REQUEST = {
  docs_request: {
    execution_dag: 'writing_observer',
    target_exports: ['docs_with_roster'],
    kwargs: {
      course_id: 'COURSE-123',
    }
  }
};
const socket = new WebSocket(SERVER);

socket.on('open', () => {
  console.log('Open');
  socket.send(JSON.stringify(REQUEST));
});

socket.on('message', (msg) => {
  try {
    const parsed = JSON.parse(msg.toString());
    console.log(parsed);
  } catch (error) {
    console.log(msg.toString());
  }
});

socket.on('error', (err) => {
  console.log('Error');
  console.log(err);
});

socket.on('close', (event) => {
  console.log('Close');
  if (event) {
    console.log(event);
  }
});
