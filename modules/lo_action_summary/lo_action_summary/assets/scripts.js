/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

// Initialize the `dash_clientside` object if it doesn't exist
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.lo_action_summary = {
  /**
   * Send updated queries to the communication protocol.
   * @param {object} wsReadyState LOConnection status object
   * @param {string} urlHash query string from hash for determining course id
   * @returns stringified json object that is sent to the communication protocl
   */
  sendToLOConnection: async function (wsReadyState, urlHash) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update;
    }
    if (wsReadyState.readyState === 1) {
      if (urlHash.length === 0) { return window.dash_clientside.no_update; }
      const decodedParams = decode_string_dict(urlHash.slice(1));
      if (!decodedParams.course_id) { return window.dash_clientside.no_update; }

      if ('student_id' in decodedParams) {
        decodedParams.student_id = [{ user_id: decodedParams.student_id }];
      } else {
        decodedParams.student_id = [];
      }

      const outgoingMessage = {
        lo_action_summary_query: {
          execution_dag: 'lo_action_summary',
          target_exports: ['roster', 'action_summary'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  /**
   * Process a message from LOConnection
   * @param {object} incomingMessage object received from LOConnection
   * @returns parsed data to local storage
   */
  receiveWSMessage: async function (incomingMessage) {
    // TODO the naming here is broken serverside. Notice above we
    //  called the target export `student_event_history_export`, i.e. the named
    // export. Below, we need to call `lo_action_summary_join_roster`, i.e. the name
    // of the node. This ought to be cleaned up in the communication protocl.
    const parsedMessage = JSON.parse(incomingMessage.data);
    const messageData = parsedMessage.lo_action_summary_query;
    if (messageData.error !== undefined) {
      console.error('Error received from server', messageData.error);
      return {};
    }
    return messageData;
  },

  /**
   * Build the student UI components based on the stored websocket data
   * @param {*} wsStorageData information stored in the websocket store
   * @returns Dash object to be displayed on page
   */
  populateStudentRadioItems: function (wsStorageData) {
    if (!wsStorageData) {
      return window.dash_clientside.no_update;
    }
    const roster = wsStorageData.roster || [];
    let options = [];
    for (const student of roster) {
      const studentOption = {
        value: student.user_id,
        label: {
          namespace: 'dash_html_components',
          type: 'Div',
          props: {
            children: [{
              namespace: 'lo_dash_react_components',
              props: {
                profile: student.profile,
                className: 'student-name-tag d-inline-block',
                includeName: true,
                id: `${student.user_id}-activity-img`
              },
              type: 'LONameTag'
            }]
          }
        }
      };
      options = options.concat(studentOption);
    }
    return options;
  },

  updateHashWithSelectedStudent: function (selected) {
    if (selected == null) { return window.dash_clientside.no_update; }
    const params = decode_string_dict(window.location.hash.slice(1));
    return `#course_id=${params.course_id};student_id=${selected}`;
  }

};
