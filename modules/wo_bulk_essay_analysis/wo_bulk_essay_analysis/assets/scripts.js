/**
 * General scripts used for the bulk essay analysis dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {};
}

pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/3rd_party/pdf.worker.min.js';

function fetchSelectedItemsFromOptions (value, options, type) {
  return options.reduce(function (filtered, option) {
    if (value?.[option.id]?.[type]?.value) {
      const selected = { ...option, ...value[option.id] };
      filtered.push(selected);
    }
    return filtered;
  }, []);
}

function createProcessTags (document, metrics) {
  const children = metrics.map(metric => {
    switch (metric.id) {
      case 'time_on_task':
        return createDashComponent(
          DASH_BOOTSTRAP_COMPONENTS, 'Badge',
          { children: `${rendertime2(document[metric.id])} on task`, className: 'me-1' }
        );
      case 'status':
        const color = document[metric.id] === 'active' ? 'success' : 'warning';
        return createDashComponent(
          DASH_BOOTSTRAP_COMPONENTS, 'Badge',
          { children: document[metric.id], color }
        );
      default:
        break;
    }
  });
  return createDashComponent(DASH_HTML_COMPONENTS, 'Div', { children, className: 'sticky-top' });
}

async function hashObject (obj) {
  const jsonString = JSON.stringify(obj);
  const encoder = new TextEncoder();
  const data = encoder.encode(jsonString);

  if (crypto && crypto.subtle) {
    try {
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
      return hashHex;
    } catch (error) {
      console.warn('crypto.subtle.digest failed; falling back to simple hash.');
    }
  }

  return simpleHash(jsonString);
}

function simpleHash (str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return hash.toString(16);
}

const createStudentCard = function (s, promptHash, width, height, showName, selectedMetrics) {
  const selectedDocument = s.doc_id || Object.keys(s.documents || {})[0] || '';
  const documentTitle = s?.availableDocuments?.[selectedDocument]?.title ?? selectedDocument ?? '';
  const student = s.documents?.[selectedDocument] ?? {};

  const studentText = createDashComponent(
    LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText',
    { text: student.text, breakpoints: [] }
  );
  const studentTileChild = createDashComponent(
    DASH_HTML_COMPONENTS, 'Div',
    {
      children: [
        createProcessTags({ ...student }, selectedMetrics),
        studentText
      ]
    }
  );
  const errorMessage = createDashComponent(
    DASH_HTML_COMPONENTS, 'Div',
    { children: 'An error occurred while processing the text.' }
  );
  const feedbackMessage = createDashComponent(
    DASH_CORE_COMPONENTS, 'Markdown',
    {
      children: student?.feedback ? student.feedback : '',
      className: student?.feedback ? 'p-1 overflow-auto' : '',
      style: { whiteSpace: 'pre-line' }
    }
  );
  const feedbackLoading = createDashComponent(
    DASH_HTML_COMPONENTS, 'Div',
    {
      children: [
        createDashComponent(DASH_BOOTSTRAP_COMPONENTS, 'Spinner', {}),
        createDashComponent(DASH_HTML_COMPONENTS, 'Div', { children: 'Waiting for a response.' })
      ],
      className: 'text-center'
    }
  );
  const feedback = promptHash === student.option_hash_gpt_bulk ? feedbackMessage : feedbackLoading;
  const feedbackOrError = 'error' in student ? errorMessage : feedback;
  const userId = student?.user_id;
  if (!userId) { return null; }

  const studentTile = createDashComponent(
    LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
    {
      showName,
      profile: student?.profile || {},
      selectedDocument,
      documentTitle,
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

const checkForBulkResponse = function (s, promptHash, options) {
  if (!('documents' in s)) { return false; }
  const selectedDocument = s.doc_id || Object.keys(s.documents || {})[0] || '';
  const student = s.documents[selectedDocument];
  if (!student) { return false; }
  return options.every(option => {
    const hashKey = `option_hash_${option}`;
    if (hashKey in student) {
      return promptHash === student[hashKey];
    }
    return option in student;
  });
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
  return allTexts.join('\n');
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
  return result.value;
};

const fileTextExtractors = {
  pdf: extractPDF,
  txt: extractTXT,
  md: extractMD,
  docx: extractDOCX
};

const AIAssistantLoadingQueries = ['gpt_bulk', 'time_on_task', 'activity'];

// ── Walkthrough step definitions ──────────────────────────────────────
const BULK_WALKTHROUGH_STEPS = [
  {
    title: 'Welcome to the Classroom AI Feedback Assistant!',
    icon: 'fas fa-robot',
    body: [
      'This dashboard lets you send every student\'s writing to an AI assistant ',
      'and view the feedback side-by-side with their original text.',
      '\n\n',
      'Let\'s walk through how to get started — it only takes a minute.'
    ].join('')
  },
  {
    title: 'Step 1 — Write Your Prompt',
    icon: 'fas fa-pen-fancy',
    body: [
      'In the Prompt Input panel you\'ll see a text area for your query. ',
      'This is what the AI will do with each student\'s writing.\n\n',
      'Use placeholders like {student_text} to reference student essays. ',
      'You can also add custom placeholders (e.g. a rubric) via the ',
      '"Add" button next to the placeholder word bank.\n\n',
      'There\'s also a system prompt that guides the AI\'s overall behavior — ',
      'you can edit it in Settings (⚙).'
    ].join('')
  },
  {
    title: 'Step 2 — Click Submit',
    icon: 'fas fa-paper-plane',
    body: [
      'Once your prompt is ready, click the "Submit" button.\n\n',
      'The dashboard will send your prompt (with each student\'s text filled in) ',
      'to the AI. A progress bar will appear while results load — this can take ',
      'a few minutes for larger classes.'
    ].join('')
  },
  {
    title: 'Step 3 — Review AI Feedback',
    icon: 'fas fa-comments',
    body: [
      'Each student tile shows their original writing on top and the AI\'s ',
      'feedback below.\n\n',
      '• Click the expand icon (⤢) on any tile to open a larger view.\n',
      '• Use the Settings (⚙) button to adjust tile sizes, change the document ',
      'source, or edit the system prompt.\n',
      '• Your prompt history is saved so you can see what you\'ve already tried.'
    ].join('')
  },
  {
    title: 'You\'re Ready!',
    icon: 'fas fa-check-circle',
    body: [
      'That\'s everything you need to get started.\n\n',
      'You can change your prompt at any time and click "Submit" again ',
      'to get new feedback.\n\n',
      'To revisit this guide later, click the ',
      'help button (?) in the toolbar.'
    ].join('')
  }
];

/**
 * Build the walkthrough modal body for a given step index.
 */
function buildBulkWalkthroughBody (step) {
  const info = BULK_WALKTHROUGH_STEPS[step];
  const paragraphs = info.body.split('\n').filter(Boolean).map(line =>
    createDashComponent(DASH_HTML_COMPONENTS, 'P', {
      children: line,
      className: 'mb-2',
      style: { whiteSpace: 'pre-wrap' }
    })
  );
  return createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
    children: [
      createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
        children: createDashComponent(DASH_HTML_COMPONENTS, 'I', {
          className: `${info.icon} fa-3x text-primary mb-3`
        }),
        className: 'text-center'
      }),
      ...paragraphs
    ]
  });
}

/**
 * Build an empty-state placeholder when no student data is loaded yet.
 */
function buildBulkEmptyState () {
  return createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
    className: 'd-flex flex-column align-items-center justify-content-center text-center py-5 w-100',
    style: { minHeight: '300px', color: '#6c757d' },
    children: [
      createDashComponent(DASH_HTML_COMPONENTS, 'I', {
        className: 'fas fa-users fa-4x mb-3',
        style: { opacity: 0.3 }
      }),
      createDashComponent(DASH_HTML_COMPONENTS, 'H4', {
        children: 'No student data loaded yet',
        className: 'mb-3'
      }),
      createDashComponent(DASH_HTML_COMPONENTS, 'P', {
        children: 'To get started:',
        className: 'mb-2 fw-bold'
      }),
      createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
        className: 'text-start',
        style: { maxWidth: '400px' },
        children: [
          createDashComponent(DASH_HTML_COMPONENTS, 'P', {
            className: 'mb-1',
            children: '1. Write your prompt in the Prompt Input panel above'
          }),
          createDashComponent(DASH_HTML_COMPONENTS, 'P', {
            className: 'mb-1',
            children: '2. Make sure {student_text} is included in your query'
          }),
          createDashComponent(DASH_HTML_COMPONENTS, 'P', {
            className: 'mb-1',
            children: '3. Click "Submit" to send the prompt to the AI for each student'
          })
        ]
      }),
      createDashComponent(DASH_HTML_COMPONENTS, 'P', {
        className: 'mt-3 text-muted small',
        children: 'Click the ? button for a full walkthrough.'
      })
    ]
  });
}

window.dash_clientside.bulk_essay_feedback = {
  // ── Walkthrough callbacks ────────────────────────────────────────────

  navigateWalkthrough: function (nextClicks, backClicks, doneClicks, skipClicks, helpClicks, currentStep) {
    const triggered = window.dash_clientside.callback_context?.triggered_id;
    if (!triggered) { return window.dash_clientside.no_update; }

    const totalSteps = BULK_WALKTHROUGH_STEPS.length;

    switch (triggered) {
      case 'bulk-essay-analysis-walkthrough-next':
        return Math.min(currentStep + 1, totalSteps - 1);
      case 'bulk-essay-analysis-walkthrough-back':
        return Math.max(currentStep - 1, 0);
      case 'bulk-essay-analysis-walkthrough-done':
      case 'bulk-essay-analysis-walkthrough-skip':
        return -1;
      case 'bulk-essay-analysis-help':
        return 0;
      default:
        return window.dash_clientside.no_update;
    }
  },

  renderWalkthroughStep: function (step) {
    const totalSteps = BULK_WALKTHROUGH_STEPS.length;
    const isOpen = step >= 0 && step < totalSteps;

    if (!isOpen) {
      return [
        '', '', true,
        { display: 'inline-block' },
        { display: 'none' },
        '',
        false
      ];
    }

    const info = BULK_WALKTHROUGH_STEPS[step];
    const body = buildBulkWalkthroughBody(step);
    const isFirst = step === 0;
    const isLast = step === totalSteps - 1;
    const counter = `${step + 1} of ${totalSteps}`;

    return [
      info.title,
      body,
      isFirst,
      { display: isLast ? 'none' : 'inline-block' },
      { display: isLast ? 'inline-block' : 'none' },
      counter,
      true
    ];
  },

  initWalkthroughFromStorage: function (step, hasSeenWalkthrough) {
    const triggered = window.dash_clientside.callback_context?.triggered_id;

    if (!triggered) {
      if (hasSeenWalkthrough) {
        return [-1, true];
      }
      return [0, false];
    }

    if (step === -1) {
      return [-1, true];
    }

    return [step, hasSeenWalkthrough];
  },

  // ── Settings modal callbacks ─────────────────────────────────────────

  toggleSettingsModal: function (clicks, isOpen) {
    if (!clicks) { return window.dash_clientside.no_update; }
    return !isOpen;
  },

  applySettingsAndCloseModal: function (clicks, stagedSystemPrompt, docKwargs) {
    if (!clicks) {
      return [
        window.dash_clientside.no_update,
        window.dash_clientside.no_update,
        window.dash_clientside.no_update
      ];
    }
    return [stagedSystemPrompt, docKwargs, false];
  },

  // ── Expanded student modal ───────────────────────────────────────────

  /**
   * When a student tile expand button is clicked, record which student
   * was selected and open the modal.
   *
   * Returns [selectedStudentId, isModalOpen, showIdentity].
   */
  expandCurrentStudent: function (clicks, ids, isModalOpen, currentStudentId, globalShowName) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }

    // Only act on actual expand button clicks
    if (triggeredItem?.type !== 'WOAIAssistStudentTileExpand') {
      return window.dash_clientside.no_update;
    }

    // Make sure something was actually clicked (not just initial callback fire)
    const hasActualClick = clicks && clicks.some(c => c !== undefined && c !== null && c > 0);
    if (!hasActualClick) { return window.dash_clientside.no_update; }

    const id = triggeredItem?.index;
    const index = ids.findIndex(item => item.index === id);
    if (index === -1) { return window.dash_clientside.no_update; }

    const showIdentity = globalShowName !== undefined ? globalShowName : true;

    return [id, true, showIdentity];
  },

  /**
   * Reactively render the expanded student modal content from live
   * websocket data. Only builds content when the modal is actually open
   * and a student is selected.
   *
   * Returns [studentName, docTitle, childContent].
   */
  renderExpandedStudent: async function (wsStorageData, selectedStudentId, isModalOpen, history, value, options) {
    // Don't do anything if the modal isn't open
    if (!isModalOpen) {
      return window.dash_clientside.no_update;
    }

    if (!selectedStudentId || !wsStorageData?.students) {
      return [
        '',
        '',
        createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
          children: 'No student selected.',
          className: 'text-muted text-center py-5'
        })
      ];
    }

    const student = wsStorageData.students[selectedStudentId];
    if (!student) {
      return [
        'Student',
        '',
        createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
          children: 'Student data not available.',
          className: 'text-muted text-center py-5'
        })
      ];
    }

    const selectedDocument = student.doc_id || Object.keys(student.documents || {})[0] || '';
    const documentName = student?.availableDocuments?.[selectedDocument]?.title ?? selectedDocument ?? '';
    const doc = student.documents?.[selectedDocument];

    if (!doc) {
      return [
        'Student',
        documentName,
        createDashComponent(DASH_HTML_COMPONENTS, 'Div', {
          children: 'Document data not available yet.',
          className: 'text-muted text-center py-5'
        })
      ];
    }

    const names = doc.profile?.name || {};
    const studentName = [names.given_name, names.family_name]
      .filter(Boolean)
      .join(' ') || 'Student';

    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    // Compute prompt hash for feedback status
    const currPrompt = history.length > 0 ? history[history.length - 1] : '';
    const promptHash = await hashObject({ prompt: currPrompt });

    // Build student text
    const studentText = createDashComponent(
      LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText',
      { text: doc.text, breakpoints: [] }
    );

    const studentTileChild = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        children: [
          createProcessTags({ ...doc }, selectedMetrics),
          studentText
        ]
      }
    );

    // Build feedback
    const errorMessage = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      { children: 'An error occurred while processing the text.' }
    );
    const feedbackMessage = createDashComponent(
      DASH_CORE_COMPONENTS, 'Markdown',
      {
        children: doc?.feedback ? doc.feedback : '',
        className: doc?.feedback ? 'p-1 overflow-auto' : '',
        style: { whiteSpace: 'pre-line' }
      }
    );
    const feedbackLoading = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        children: [
          createDashComponent(DASH_BOOTSTRAP_COMPONENTS, 'Spinner', {}),
          createDashComponent(DASH_HTML_COMPONENTS, 'Div', { children: 'Waiting for a response.' })
        ],
        className: 'text-center'
      }
    );
    const feedback = promptHash === doc.option_hash_gpt_bulk ? feedbackMessage : feedbackLoading;
    const feedbackOrError = 'error' in doc ? errorMessage : feedback;

    const childContent = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        children: [
          studentTileChild,
          createDashComponent(
            DASH_BOOTSTRAP_COMPONENTS, 'Card',
            { children: feedbackOrError, body: true }
          )
        ]
      }
    );

    return [studentName, documentName, childContent];
  },

  toggleExpandedStudentIdentity: function (clicks, currentValue) {
    if (!clicks) { return window.dash_clientside.no_update; }
    return !currentValue;
  },

  renderExpandedStudentIdentity: function (showIdentity) {
    const visible = {};
    const hidden = { display: 'none' };

    const titleStyle = showIdentity ? visible : hidden;
    const docTitleStyle = showIdentity ? visible : hidden;
    const iconClass = showIdentity ? 'fas fa-eye' : 'fas fa-eye-slash';

    return [titleStyle, docTitleStyle, iconClass];
  },

  // ── Core dashboard callbacks ─────────────────────────────────────────

  send_to_loconnection: async function (state, hash, clicks, docKwargs, query, appliedSystemPrompt, tags) {
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
      decoded.rerun_dag_delay = 120;

      const trig = window.dash_clientside.callback_context.triggered[0];
      if (trig.prop_id.includes('bulk-essay-analysis-submit-btn')) {
        decoded.gpt_prompt = query;
        decoded.system_prompt = appliedSystemPrompt;
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

  update_input_history_on_query_submission: async function (clicks, query, history) {
    if (clicks > 0) {
      return history.concat(query);
    }
    return window.dash_clientside.no_update;
  },

  update_history_list: function (history) {
    const items = history.map((x) => {
      return createDashComponent(DASH_HTML_COMPONENTS, 'Li', { children: x });
    });
    return createDashComponent(DASH_HTML_COMPONENTS, 'Ol', { children: items });
  },

  updateStudentGridOutput: async function (wsStorageData, history, width, height, showName, value, options) {
    if (!wsStorageData?.students) {
      return buildBulkEmptyState();
    }

    const students = wsStorageData.students;
    if (Object.keys(students).length === 0) {
      return buildBulkEmptyState();
    }

    const currPrompt = history.length > 0 ? history[history.length - 1] : '';
    const promptHash = await hashObject({ prompt: currPrompt });
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    let output = [];
    for (const student in students) {
      const card = createStudentCard(students[student], promptHash, width, height, showName, selectedMetrics);
      if (card) {
        output = output.concat(card);
      }
    }
    return output;
  },

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

  add_tag_to_input: function (clicks, curr, store) {
    const trig = window.dash_clientside.callback_context.triggered[0];
    const trigProp = trig.prop_id;
    const trigJSON = JSON.parse(trigProp.slice(0, trigProp.lastIndexOf('.')));
    if (trig.value > 0) {
      return curr.concat(` {${trigJSON.index}}`);
    }
    return window.dash_clientside.no_update;
  },

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

  savePlaceholder: function (clicks, label, text, replacementId, tagStore) {
    if (clicks > 0) {
      const newStore = { ...tagStore };
      if (!!replacementId && replacementId !== label) {
        delete newStore[replacementId];
      }
      newStore[label] = text;
      return [newStore, false];
    }
    return window.dash_clientside.no_update;
  },

  removePlaceholder: function (clicks, tagStore, ids) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }
    const id = triggeredItem.index;
    const index = ids.findIndex(item => item.index === id);
    if (clicks[index]) {
      const newStore = { ...tagStore };
      delete newStore[id];
      return newStore;
    }
    return window.dash_clientside.no_update;
  },

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

  updateLoadingInformation: async function (wsStorageData, history) {
    const noLoading = [false, 0, ''];
    if (!wsStorageData?.students) {
      return noLoading;
    }
    const students = wsStorageData.students;
    const totalStudents = Object.keys(students).length;
    if (totalStudents === 0) {
      return noLoading;
    }
    const currentPrompt = history.length > 0 ? history[history.length - 1] : '';
    const promptHash = await hashObject({ prompt: currentPrompt });
    const returnedResponses = Object.values(students).filter(student => checkForBulkResponse(student, promptHash, AIAssistantLoadingQueries)).length;
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

  showHideHeader: function (show, ids) {
    const total = ids.length;
    return Array(total).fill(show ? 'd-none' : '');
  }
};
