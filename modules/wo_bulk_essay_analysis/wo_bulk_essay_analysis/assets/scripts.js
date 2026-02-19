/**
 * General scripts used for the bulk essay analysis dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {};
}

pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/3rd_party/pdf.worker.min.js';

const createStudentCard = async function (s, prompt, width, height, showName, selectedMetrics) {
  const selectedDocument = s.doc_id || Object.keys(s.documents || {})[0] || '';
  const student = s.documents?.[selectedDocument] ?? {};
  const promptHash = await hashObject({ prompt });

  const studentText = {
    namespace: 'lo_dash_react_components',
    type: 'WOAnnotatedText',
    props: { text: student.text, breakpoints: [] }
  };
  const studentTileChild = createDashComponent(
    DASH_HTML_COMPONENTS, 'Div',
    {
      children: [
        createProcessTags({ ...student }, selectedMetrics),
        studentText
      ]
    }
  );
  const errorMessage = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: 'An error occurred while processing the text.'
    }
  };
  const feedbackMessage = {
    namespace: DASH_CORE_COMPONENTS,
    type: 'Markdown',
    props: {
      children: student?.feedback ? student.feedback : '',
      className: student?.feedback ? 'p-1 overflow-auto' : '',
      style: { whiteSpace: 'pre-line' }
    }
  };
  const feedbackLoading = {
    namespace: 'dash_html_components',
    type: 'Div',
    props: {
      children: [{
        namespace: 'dash_bootstrap_components',
        type: 'Spinner',
        props: {}
      }, {
        namespace: 'dash_html_components',
        type: 'Div',
        props: { children: 'Waiting for a response.' }
      }],
      className: 'text-center'
    }
  };
  const feedback = promptHash === student.option_hash_gpt_bulk ? feedbackMessage : feedbackLoading;
  const feedbackOrError = 'error' in student ? errorMessage : feedback;
  const userId = student?.user_id;
  if (!userId) { return {}; }
  const studentTile = createDashComponent(
    LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
    {
      showName,
      profile: student?.profile || {},
      selectedDocument,
      childComponent: studentTileChild,
      id: { type: 'WOAIAssistStudentTileText', index: userId },
      currentOptionHash: promptHash,
      currentStudentHash: student.option_hash_gpt_bulk,
      style: { height: `${height}px` },
      additionalButtons: createDashComponent(
        DASH_BOOTSTRAP_COMPONENTS, 'Button',
        {
          id: { type: 'WOAIAssistStudentTileExpand', index: userId },
          children: createDashComponent(DASH_HTML_COMPONENTS, 'I', { className: 'fas fa-expand' }),
          color: 'transparent'
        }
      )
    }
  );
  const tileWrapper = createDashComponent(
    DASH_HTML_COMPONENTS, 'Div',
    {
      className: 'position-relative mb-2',
      children: [
        studentTile,
        createDashComponent(
          DASH_BOOTSTRAP_COMPONENTS, 'Card',
          { children: feedbackOrError, body: true }
        ),
      ],
      id: { type: 'WOAIAssistStudentTile', index: userId },
      style: { width: `${(100 - width) / width}%` }
    }
  );
  return tileWrapper;
};

/**
 * Check for if we should trigger loading on a student or not.
 * @param {*} s student
 * @param {*} promptHash current hash of prompts
 * @returns true if student's selected document's hash is the same as promptHash
 */
const checkForResponse = function (s, promptHash, options) {
  if (!('documents' in s)) { return false; }
  const selectedDocument = s.doc_id || Object.keys(s.documents || {})[0] || '';
  const student = s.documents[selectedDocument];
  return options.every(option => promptHash === student[`option_hash_${option}`]);
};

const charactersAfterChar = function (str, char) {
  const commaIndex = str.indexOf(char);
  if (commaIndex === -1) {
    return '';
  }
  return str.slice(commaIndex + 1).trim();
};

// Helper functions for extracting text from files
const extractPDF = async function (base64String) {
  const pdfData = atob(charactersAfterChar(base64String, ','));

  // Use PDF.js to load and parse the PDF
  const pdf = await pdfjsLib.getDocument({ data: pdfData }).promise;

  const totalPages = pdf.numPages;
  const allTextPromises = [];

  for (let pageNumber = 1; pageNumber <= totalPages; pageNumber++) {
    const pageTextPromise = pdf.getPage(pageNumber).then(function (page) {
      return page.getTextContent();
    }).then(function (textContent) {
      return textContent.items.map(item => item.str).join(' ');
    });

    allTextPromises.push(pageTextPromise);
  }

  const allTexts = await Promise.all(allTextPromises);
  const allText = allTexts.join('\n');

  return allText;
};

const extractTXT = async function (base64String) {
  return atob(charactersAfterChar(base64String, ','));
};

const extractMD = async function (base64String) {
  return atob(charactersAfterChar(base64String, ','));
};

const extractDOCX = async function (base64String) {
  const arrayBuffer = Uint8Array.from(atob(charactersAfterChar(base64String, ',')), c => c.charCodeAt(0)).buffer;
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value; // The raw text
};

const fileTextExtractors = {
  pdf: extractPDF,
  txt: extractTXT,
  md: extractMD,
  docx: extractDOCX
};

const AIAssistantLoadingQueries = ['gpt_bulk', 'time_on_task', 'activity'];

window.dash_clientside.bulk_essay_feedback = {
  /**
   * Sends data to server via websocket
   */
  send_to_loconnection: async function (state, hash, clicks, docKwargs, query, systemPrompt, tags) {
    if (state === undefined) {
      return window.dash_clientside.no_update;
    }
    if (state.readyState === 1) {
      if (hash.length === 0) { return window.dash_clientside.no_update; }
      const decoded = decode_string_dict(hash.slice(1));
      if (!decoded.course_id) { return window.dash_clientside.no_update; }

      decoded.gpt_prompt = '';
      decoded.message_id = '';
      decoded.doc_source = docKwargs.src;
      decoded.doc_source_kwargs = docKwargs.kwargs;
      // TODO what is a reasonable time to wait inbetween subsequent calls for
      // the same arguments
      decoded.rerun_dag_delay = 120;

      const trig = window.dash_clientside.callback_context.triggered[0];
      if (trig.prop_id.includes('bulk-essay-analysis-submit-btn')) {
        decoded.gpt_prompt = query;
        decoded.system_prompt = systemPrompt;
        decoded.tags = tags;
      }

      const optionsHash = await hashObject({ prompt: decoded.gpt_prompt });
      decoded.option_hash = optionsHash;

      const message = {
        wo: {
          execution_dag: 'writing_observer',
          target_exports: ['gpt_bulk', 'document_list', 'document_sources', 'time_on_task', 'activity'],
          kwargs: decoded
        }
      };
      return JSON.stringify(message);
    }
    return window.dash_clientside.no_update;
  },

  toggleAdvanced: function (clicks, shown) {
    if (!clicks) {
      return window.dash_clientside.no_update;
    }
    const optionPrefix = 'bulk-essay-analysis-advanced-collapse';
    if (shown.includes(optionPrefix)) {
      shown = shown.filter(item => item !== optionPrefix);
    } else {
      shown = shown.concat(optionPrefix);
    }
    return shown;
  },

  closeAdvanced: function (clicks, shown) {
    if (!clicks) { return window.dash_clientside.no_update; }
    shown = shown.filter(item => item !== 'bulk-essay-analysis-advanced-collapse');
    return shown;
  },

  /**
   * adds submitted query to history and clear input
   */
  update_input_history_on_query_submission: async function (clicks, query, history) {
    if (clicks > 0) {
      return history.concat(query);
    }
    return window.dash_clientside.no_update;
  },

  /**
   * update history based on history browser storage
  */
  update_history_list: function (history) {
    const items = history.map((x) => {
      return {
        namespace: 'dash_html_components',
        type: 'Li',
        props: { children: x }
      };
    });
    return {
      namespace: 'dash_html_components',
      type: 'Ol',
      props: { children: items }
    };
  },

  /**
   * update student cards based on new data in storage
   */
  updateStudentGridOutput: async function (wsStorageData, history, width, height, showName, value, options) {
    if (!wsStorageData) {
      return 'No students';
    }
    const currPrompt = history.length > 0 ? history[history.length - 1] : '';
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    let output = [];
    for (const student in wsStorageData.students) {
      output = output.concat(await createStudentCard(wsStorageData.students[student], currPrompt, width, height, showName, selectedMetrics));
    }
    return output;
  },

  /**
   * Uploads file content as str
  */
  handleFileUploadToTextField: async function (contents, filename, timestamp) {
    if (filename === undefined) {
      return '';
    }
    let data = '';
    try {
      const filetype = charactersAfterChar(filename, '.');
      if (filetype in fileTextExtractors) {
        data = await fileTextExtractors[filetype](contents);
      } else {
        console.error('Unsupported file type');
      }
    } catch (error) {
      console.error('Error extracting text from file:', error);
    }
    return data;
  },

  /**
   * append tag in curly braces to input
  */
  add_tag_to_input: function (clicks, curr, store) {
    const trig = window.dash_clientside.callback_context.triggered[0];
    const trigProp = trig.prop_id;
    const trigJSON = JSON.parse(trigProp.slice(0, trigProp.lastIndexOf('.')));
    if (trig.value > 0) {
      return curr.concat(` {${trigJSON.index}}`);
    }
    return window.dash_clientside.no_update;
  },

  /**
   * enable/disabled submit based on query
   * makes sure there is a query and the tags are properly formatted
   *
   * updates the following components
   * - submit query button disbaled status
   * - helper text for why we disabled the submit query button
  */
  disableQuerySubmitButton: function (query, loading, store) {
    if (query.length === 0) {
      return [true, 'Please create a request before submitting.'];
    }
    if (loading) {
      return [true, 'Please wait until current query has finished before resubmitting.'];
    }
    const tags = Object.keys(store);
    const queryTags = query.match(/[^{}]+(?=})/g) || [];
    const diffs = queryTags.filter(x => !tags.includes(x));
    if (diffs.length > 0) {
      return [true, `Unable to find [${diffs.join(',')}] within the tags. Please check that the spelling is correct or remove the extra tags.`];
    } else if (!queryTags.includes('student_text')) {
      return [true, 'Submission requires the inclusion of {student_text} to run the request over the student essays.'];
    }
    return [false, ''];
  },

  /**
   * enable/disable the save attachment button if tag is already in use/blank
   *
   * updates the following components
   * - save button disbaled status
   * - helper text for why we are disabled
   */
  disableAttachmentSaveButton: function (label, content, currentTagStore, replacementId) {
    const tags = Object.keys(currentTagStore);
    if (label.length === 0 & content.length === 0) {
      return [true, ''];
    } else if (label.length === 0) {
      return [true, 'Add a label for your content'];
    } else if (content.length === 0) {
      return [true, 'Add content for your label'];
    } else if ((!replacementId | replacementId !== label) & tags.includes(label)) {
      return [true, `Label ${label} is already in use.`];
    }
    return [false, ''];
  },

  /**
   * Opens the tag modal when users want to add a new one or edit an
   * existing tag.
   */
  openTagAddModal: function (clicks, editClicks, currentTagStore, ids) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }
    if (triggeredItem === 'bulk-essay-analysis-tags-add-open-btn') {
      return [true, null, '', ''];
    }
    const id = triggeredItem.index;
    const index = ids.findIndex(item => item.index === id);
    if (editClicks[index]) {
      return [true, id, id, currentTagStore[id]];
    }
    return window.dash_clientside.no_update;
  },

  /**
   * populate word bank of tags
   */
  update_tag_buttons: function (tagStore) {
    const tagLabels = Object.keys(tagStore);
    const tags = tagLabels.map((val) => {
      const isStudentText = val === 'student_text';
      const button = createDashComponent(
        DASH_BOOTSTRAP_COMPONENTS, 'Button',
        {
          children: val,
          id: { type: 'bulk-essay-analysis-tags-tag', index: val },
          n_clicks: 0,
          color: isStudentText ? 'warning' : 'info'
        }
      );
      const editButton = createDashComponent(
        DASH_BOOTSTRAP_COMPONENTS, 'Button',
        {
          children: createDashComponent(DASH_HTML_COMPONENTS, 'I', { className: 'fas fa-edit' }),
          id: { type: 'bulk-essay-analysis-tags-tag-edit', index: val },
          n_clicks: 0,
          color: 'info'
        }
      );
      const deleteButton = createDashComponent(
        DASH_CORE_COMPONENTS, 'ConfirmDialogProvider',
        {
          children: createDashComponent(
            DASH_BOOTSTRAP_COMPONENTS, 'Button',
            {
              children: createDashComponent(DASH_HTML_COMPONENTS, 'I', { className: 'fas fa-trash' }),
              color: 'info'
            }
          ),
          id: { type: 'bulk-essay-analysis-tags-tag-delete', index: val },
          message: `Are you sure you want to delete the \`${val}\` placeholder?`
        }
      );
      const buttons = isStudentText ? [button] : [button, editButton, deleteButton];
      const buttonGroup = createDashComponent(
        DASH_BOOTSTRAP_COMPONENTS, 'ButtonGroup',
        {
          children: buttons,
          class_name: `${isStudentText ? '' : 'prompt-variable-tag'} ms-1 mb-1`
        }
      );
      return buttonGroup;
    });
    return tags;
  },

  /**
   * Save placeholder to browser storage and close edit placeholder modal
   */
  savePlaceholder: function (clicks, label, text, replacementId, tagStore) {
    if (clicks > 0) {
      const newStore = tagStore;
      if (!!replacementId & replacementId !== label) {
        delete newStore[replacementId];
      }
      newStore[label] = text;
      return [newStore, false];
    }
    return window.dash_clientside.no_update;
  },

  /**
   * Remove placeholder from store on confirm dialogue yes
   */
  removePlaceholder: function (clicks, tagStore, ids) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }
    const id = triggeredItem.index;
    const index = ids.findIndex(item => item.index === id);
    if (clicks[index]) {
      const newStore = tagStore;
      delete newStore[id];
      return newStore;
    }
    return window.dash_clientside.no_update;
  },

  /**
   * Check if we've received any errors and update
   * the alert with the appropriate information
   *
   * returns an array which updates dash components
   * - text to display on alert
   * - show alert
   * - JSON error data on the alert (only in debug)
   */
  updateAlertWithError: function (error) {
    if (Object.keys(error).length === 0) {
      return ['', false, ''];
    }
    const text = 'Oops! Something went wrong ' +
                 "on our end. We've noted the " +
                 'issue. Please try again later, or consider ' +
                 'exploring a different dashboard for now. ' +
                 'Thanks for your patience!';
    return [text, true, error];
  },

  /**
   * Iterate over students and figure out if any of them have not loaded
   * yet. We hash the last history item to compare to.
   */
  updateLoadingInformation: async function (wsStorageData, history) {
    const noLoading = [false, 0, ''];
    if (!wsStorageData) {
      return noLoading;
    }
    const currentPrompt = history.length > 0 ? history[history.length - 1] : '';
    const promptHash = await hashObject({ prompt: currentPrompt });
    const returnedResponses = Object.values(wsStorageData.students).filter(student => checkForResponse(student, promptHash, AIAssistantLoadingQueries)).length;
    const totalStudents = Object.keys(wsStorageData.students).length;
    if (totalStudents === returnedResponses) { return noLoading; }
    const loadingProgress = returnedResponses / totalStudents + 0.1;
    const outputText = `Fetching responses from server. This will take a few minutes. (${returnedResponses}/${totalStudents} received)`;
    return [true, loadingProgress, outputText];
  },

  adjustTileSize: function (width, height, studentIds) {
    const total = studentIds.length;
    return [
      Array(total).fill({ width: `${(100 - width) / width}%` }),
      Array(total).fill({ height: `${height}px` })
    ];
  },

  selectStudentForExpansion: function (clicks, shownPanels, ids) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }
    let id = null;
    if (triggeredItem?.type === 'WOAIAssistStudentTileExpand') {
      id = triggeredItem?.index;
      const index = ids.findIndex(item => item.index === id);
      if (clicks[index]) {
        shownPanels = shownPanels.concat('bulk-essay-analysis-expanded-student-panel');
      } else {
        // No clicks occurred so we should keep the ID as it was
        id = window.dash_clientside.no_update;
      }
    } else {
      return window.dash_clientside.no_update;
    }
    return [id, shownPanels];
  },

  expandSelectedStudent: async function (selectedStudent, wsData, showName, history, value, options) {
    if (!selectedStudent | !(selectedStudent in (wsData.students || {}))) {
      return window.dash_clientside.no_update;
    }
    const prompt = history.length > 0 ? history[history.length - 1] : '';
    const s = wsData.students[selectedStudent];
    const selectedDocument = s.doc_id || Object.keys(s.documents || {})[0] || '';
    const document = Object.keys(s.documents)[0];
    const student = s.documents[document];
    const promptHash = await hashObject({ prompt });
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    // TODO some of this can easily be abstracted
    const studentText = {
      namespace: 'lo_dash_react_components',
      type: 'WOAnnotatedText',
      props: { text: student.text, breakpoints: [] }
    };
    const studentTileChild = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        children: [
          createProcessTags({ ...student }, selectedMetrics),
          studentText
        ]
      }
    );
    const errorMessage = {
      namespace: 'dash_html_components',
      type: 'Div',
      props: {
        children: 'An error occurred while processing the text.'
      }
    };
    const feedbackMessage = {
      namespace: DASH_CORE_COMPONENTS,
      type: 'Markdown',
      props: {
        children: student?.feedback ? student.feedback : '',
        className: student?.feedback ? 'p-1' : '',
        style: { whiteSpace: 'pre-line' }
      }
    };
    const feedbackLoading = {
      namespace: 'dash_html_components',
      type: 'Div',
      props: {
        children: [{
          namespace: 'dash_bootstrap_components',
          type: 'Spinner',
          props: {}
        }, {
          namespace: 'dash_html_components',
          type: 'Div',
          props: { children: 'Waiting for a response.' }
        }],
        className: 'text-center'
      }
    };
    const feedback = promptHash === student.option_hash_gpt_bulk ? feedbackMessage : feedbackLoading;
    const feedbackOrError = 'error' in student ? errorMessage : feedback;
    const studentTile = createDashComponent(
      LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
      {
        showName,
        profile: student?.profile || {},
        selectedDocument,
        childComponent: studentTileChild,
        id: { type: 'WOAIAssistStudentTileText', index: student.user_id },
        currentOptionHash: promptHash,
        currentStudentHash: student.option_hash_gpt_bulk
      }
    );
    const individualWrapper = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        className: '',
        children: [
          studentTile,
          createDashComponent(
            DASH_BOOTSTRAP_COMPONENTS, 'Card',
            { children: feedbackOrError, body: true }
          )
        ]
      }
    );
    return individualWrapper;
  },

  closeExpandedStudent: function (clicks, shown) {
    if (!clicks) { return window.dash_clientside.no_update; }
    shown = shown.filter(item => item !== 'bulk-essay-analysis-expanded-student-panel');
    return shown;
  }
};
