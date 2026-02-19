/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

// Initialize the `dash_clientside` object if it doesn't exist
if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.{{ cookiecutter.project_slug }} = {
  /**
   * Send updated queries to the communication protocol.
   * @param {object} wsReadyState LOConnection status object
   * @param {string} urlHash query string from hash for determining course id
   * @returns stringified json object that is sent to the communication protocl
   */
  sendToLOConnection: async function (wsReadyState, urlHash) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update
    }
    if (wsReadyState.readyState === 1) {
      if (urlHash.length === 0) { return window.dash_clientside.no_update }
      const decodedParams = decode_string_dict(urlHash.slice(1))
      if (!decodedParams.course_id) { return window.dash_clientside.no_update }
      const outgoingMessage = {
        {{ cookiecutter.project_slug }}_query: {
          execution_dag: '{{ cookiecutter.project_slug }}',
          target_exports: ['{{ cookiecutter.reducer }}_export'],
          kwargs: decodedParams
        }
      };
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  /**
   * Build the student UI components based on the stored websocket data
   * @param {*} wsStorageData information stored in the websocket store
   * @returns Dash object to be displayed on page
   */
  populateOutput: function (wsStorageData) {
    if (!wsStorageData?.students) {
      return 'No students';
    }
    let output = []
    // Iterate over students and create UI items for each
    for (const [student, value] of Object.entries(wsStorageData.students)) {
      // We define Dash components in JS via a dictionary
      // of where the component lives, what it is, and any
      // parameters we want to pass along to it.
      // - `namespace`: the module the component is in
      // - `type`: the component to use
      // - `props`: any parameters the component expects
      // The following produces a LONameTag and Span wrapped in a Div
      const studentBadge = {
        namespace: 'dash_html_components',
        type: 'Div',
        props: {
          children: [{
            namespace: 'dash_html_components',
            props: {
              children: student
            },
            type: 'Span'
          }, {
            namespace: 'dash_html_components',
            props: {
              children: ` - ${value.count} events`
            },
            type: 'Span'
          }]
        }
      }
      output = output.concat(studentBadge);
    }
    return output;
  }
};
