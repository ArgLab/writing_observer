/**
 * Javascript callbacks to be used with the LO Example dashboard
 */

if (!window.dash_clientside) {
  window.dash_clientside = {};
}

const DASH_HTML_COMPONENTS = 'dash_html_components';
const DASH_CORE_COMPONENTS = 'dash_core_components';
const DASH_BOOTSTRAP_COMPONENTS = 'dash_bootstrap_components';
const LO_DASH_REACT_COMPONENTS = 'lo_dash_react_components';

function createDashComponent (namespace, type, props) {
  return { namespace, type, props };
}

function determineSelectedNLPOptionsList (optionsObj) {
  if (optionsObj === undefined | optionsObj === null) { return []; }
  return Object.keys(optionsObj).filter(id =>
    optionsObj[id].highlight?.value === true ||
    optionsObj[id].metric?.value === true
  );
}

const checkForResponse = function (s, promptHash, options) {
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

function formatStudentData (document, selectedHighlights) {
  const breakpoints = selectedHighlights.reduce((acc, option) => {
    const offsets = document[option.id]?.offsets || [];
    if (offsets) {
      const modifiedOffsets = offsets.map(offset => {
        return {
          id: '',
          tooltip: option.label,
          start: offset[0],
          offset: offset[1],
          style: { backgroundColor: option.highlight.color }
        };
      });
      acc = acc.concat(modifiedOffsets);
    }
    return acc;
  }, []);
  const text = document.text;
  return { text, breakpoints };
}

function styleStudentTile (width, height) {
  return { width: `${(100 - width) / width}%`, height: `${height}px` };
}

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

function studentHasResponded (student, appliedHash) {
  const documents = student.documents || {};
  const docKeys = Object.keys(documents);

  if (docKeys.length === 0) { return false; }

  for (const docKey of docKeys) {
    const doc = documents[docKey];
    if (!doc) { return false; }

    const docHash = doc.option_hash_docs_with_nlp_annotations;
    if (docHash !== appliedHash) {
      return false;
    }
  }
  return true;
}

const ClassroomTextHighlightLoadingQueries = ['docs_with_nlp_annotations', 'time_on_task', 'activity'];

// ── Walkthrough step definitions ──────────────────────────────────────
const WALKTHROUGH_STEPS = [
  {
    title: 'Welcome to the Classroom Text Highlighter!',
    icon: 'fas fa-chalkboard-teacher',
    body: [
      'This dashboard lets you see every student\'s writing at a glance, with ',
      'color-coded highlights that surface things like grammar patterns, ',
      'argument strength, vocabulary usage, and more.',
      '\n\n',
      'Let\'s walk through how to get started — it only takes a minute.'
    ].join('')
  },
  {
    title: 'Step 1 — Choose What to Highlight',
    icon: 'fas fa-highlighter',
    body: [
      'Click the "Choose What to Highlight" button in the toolbar at the top. ',
      'This opens a setup panel where you pick which analyses to run on ',
      'your students\' writing.\n\n',
      'You\'ll see two types of options:\n',
      '• Highlights — color-coded annotations on the text (e.g. grammar types, ',
      'key claims)\n',
      '• Metrics — summary badges shown on each tile (e.g. time on task, ',
      'active/inactive status)'
    ].join('')
  },
  {
    title: 'Step 2 — Click Run to Load Results',
    icon: 'fas fa-play-circle',
    body: [
      'After choosing your highlights and metrics, click the green "Run" button ',
      'at the bottom of the panel.\n\n',
      'The dashboard will fetch analysis for every student in your class. ',
      'A progress bar will appear while results load — this can take a minute ',
      'or two for larger classes.'
    ].join('')
  },
  {
    title: 'Step 3 — Read and Explore Student Work',
    icon: 'fas fa-search-plus',
    body: [
      'Each tile represents one student. Their writing is displayed with your ',
      'chosen highlights applied directly to the text.\n\n',
      '• Click the expand icon (⤢) on any tile to open that student\'s writing ',
      'in a larger, more readable view.\n',
      '• Use the "Highlight Key" button in the toolbar to see what each color means.\n',
      '• Hover over any highlighted word to see which specific annotations apply to it.'
    ].join('')
  },
  {
    title: 'You\'re Ready!',
    icon: 'fas fa-check-circle',
    body: [
      'That\'s everything you need to get started.\n\n',
      'You can change your highlight selections at any time by clicking ',
      '"Choose What to Highlight" again and pressing "Run."\n\n',
      'To revisit this guide later, click the ',
      'help button (?) in the toolbar.'
    ].join('')
  }
];

/**
 * Build the walkthrough modal body for a given step index.
 */
function buildWalkthroughBody (step) {
  const info = WALKTHROUGH_STEPS[step];
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
function buildEmptyState () {
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
            children: '1. Click "Choose What to Highlight" in the toolbar above'
          }),
          createDashComponent(DASH_HTML_COMPONENTS, 'P', {
            className: 'mb-1',
            children: '2. Select the highlights and metrics you\'d like to see'
          }),
          createDashComponent(DASH_HTML_COMPONENTS, 'P', {
            className: 'mb-1',
            children: '3. Click the green "Run" button to load student data'
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

window.dash_clientside.wo_classroom_text_highlighter = {
  // ── Walkthrough callbacks ────────────────────────────────────────────

  /**
   * Navigate walkthrough steps. Triggered by next, back, done, or help button.
   * Returns the new step index (0..N-1) or -1 when dismissed.
   */
  navigateWalkthrough: function (nextClicks, backClicks, doneClicks, skipClicks, helpClicks, currentStep) {
    const triggered = window.dash_clientside.callback_context?.triggered_id;
    if (!triggered) { return window.dash_clientside.no_update; }

    const totalSteps = WALKTHROUGH_STEPS.length;

    switch (triggered) {
      case 'wo-classroom-text-highlighter-walkthrough-next':
        return Math.min(currentStep + 1, totalSteps - 1);
      case 'wo-classroom-text-highlighter-walkthrough-back':
        return Math.max(currentStep - 1, 0);
      case 'wo-classroom-text-highlighter-walkthrough-done':
      case 'wo-classroom-text-highlighter-walkthrough-skip':
        return -1;
      case 'wo-classroom-text-highlighter-help':
        return 0;
      default:
        return window.dash_clientside.no_update;
    }
  },

  /**
   * Render the walkthrough modal based on the current step.
   * Returns [title, body, backDisabled, nextStyle, doneStyle, stepCounter, isOpen].
   */
  renderWalkthroughStep: function (step) {
    const totalSteps = WALKTHROUGH_STEPS.length;
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

    const info = WALKTHROUGH_STEPS[step];
    const body = buildWalkthroughBody(step);
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

  computeAppliedHash: async function (appliedValue) {
    if (!appliedValue) { return ''; }
    const h = await hashObject(appliedValue);
    console.log('[computeAppliedHash] computed hash:', h.substring(0, 12) + '...');
    return h;
  },

  sendToLOConnection: function (wsReadyState, urlHash, docKwargs, appliedHash, nlpValue) {
    if (wsReadyState === undefined) {
      return window.dash_clientside.no_update;
    }
    if (wsReadyState.readyState === 1) {
      if (urlHash.length === 0) { return window.dash_clientside.no_update; }
      const decodedParams = decode_string_dict(urlHash.slice(1));
      if (!decodedParams.course_id) { return window.dash_clientside.no_update; }

      if (!appliedHash) {
        console.log('[sendToLOConnection] No hash yet, skipping');
        return window.dash_clientside.no_update;
      }

      const nlpOptions = determineSelectedNLPOptionsList(nlpValue);
      decodedParams.nlp_options = nlpOptions;
      decodedParams.option_hash = appliedHash;
      decodedParams.doc_source = docKwargs.src;
      decodedParams.doc_source_kwargs = docKwargs.kwargs;
      decodedParams.rerun_dag_delay = 120;
      const outgoingMessage = {
        wo_classroom_text_highlighter_query: {
          execution_dag: 'writing_observer',
          target_exports: ['docs_with_nlp_annotations', 'document_sources', 'document_list', 'time_on_task', 'activity'],
          kwargs: decodedParams
        }
      };
      console.log('[sendToLOConnection] Sending with hash:', appliedHash.substring(0, 12) + '...');
      return JSON.stringify(outgoingMessage);
    }
    return window.dash_clientside.no_update;
  },

  toggleOptionsModal: function (clicks, isOpen) {
    if (!clicks) { return window.dash_clientside.no_update; }
    return !isOpen;
  },

  applyOptionsAndCloseModal: function (clicks, stagedValue, docKwargs) {
    if (!clicks) {
      return [
        window.dash_clientside.no_update,
        window.dash_clientside.no_update,
        window.dash_clientside.no_update
      ];
    }
    console.log('[applyOptionsAndCloseModal] Applying staged options and doc source');
    return [stagedValue, docKwargs, false];
  },

  adjustTileSize: function (width, height, studentIds) {
    const total = studentIds.length;
    return Array(total).fill(styleStudentTile(width, height));
  },

  showHideHeader: function (show, ids) {
    const total = ids.length;
    return Array(total).fill(show ? 'd-none' : '');
  },

  updateCurrentOptionHash: function (appliedHash, ids) {
    if (!appliedHash) {
      return window.dash_clientside.no_update;
    }
    const total = ids.length;
    console.log('[updateCurrentOptionHash] Broadcasting hash to', total, 'tiles:', appliedHash.substring(0, 12) + '...');
    return Array(total).fill(appliedHash);
  },

  populateOutput: function (wsStorageData, value, width, height, showName, options, optionHash) {
    if (!wsStorageData?.students) {
      return buildEmptyState();
    }

    const students = wsStorageData.students;
    if (Object.keys(students).length === 0) {
      return buildEmptyState();
    }

    let output = [];

    const selectedHighlights = fetchSelectedItemsFromOptions(value, options, 'highlight');
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    console.log('[populateOutput] Using hash:', optionHash ? optionHash.substring(0, 12) + '...' : 'NONE');

    for (const student in students) {
      const selectedDocument = students[student].doc_id || Object.keys(students[student].documents || {})[0] || '';
      const documentTitle = students[student]?.availableDocuments?.[selectedDocument]?.title ?? selectedDocument ?? '';
      const studentTileChild = createDashComponent(
        DASH_HTML_COMPONENTS, 'Div',
        {
          children: [
            createProcessTags({ ...students[student].documents[selectedDocument] }, selectedMetrics),
            createDashComponent(
              LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText',
              formatStudentData({ ...students[student].documents[selectedDocument] }, selectedHighlights)
            )
          ]
        }
      );
      const studentTile = createDashComponent(
        LO_DASH_REACT_COMPONENTS, 'WOStudentTextTile',
        {
          showName,
          profile: students[student].documents[selectedDocument]?.profile || {},
          selectedDocument,
          documentTitle,
          childComponent: studentTileChild,
          id: { type: 'WOStudentTextTile', index: student },
          currentStudentHash: students[student].documents[selectedDocument]?.option_hash_docs_with_nlp_annotations,
          currentOptionHash: optionHash,
          className: 'h-100',
          additionalButtons: createDashComponent(
            DASH_BOOTSTRAP_COMPONENTS, 'Button',
            {
              id: { type: 'WOStudentTileExpand', index: student },
              children: createDashComponent(DASH_HTML_COMPONENTS, 'I', { className: 'fas fa-expand' }),
              color: 'transparent'
            }
          )
        }
      );
      const tileWrapper = createDashComponent(
        DASH_HTML_COMPONENTS, 'Div',
        {
          className: 'mb-2',
          children: [
            studentTile,
          ],
          id: { type: 'WOStudentTile', index: student },
          style: styleStudentTile(width, height)
        }
      );
      output = output.concat(tileWrapper);
    }
    return output;
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

  addPreset: function (clicks, name, options, store) {
    if (!clicks) { return store; }
    const copy = { ...store };
    copy[name] = options;
    return copy;
  },

  applyPreset: function (clicks, data) {
    const preset = window.dash_clientside.callback_context?.triggered_id.index ?? null;
    const itemsClicked = clicks.some(item => item !== undefined);
    if (!preset | !itemsClicked) { return window.dash_clientside.no_update; }
    return data[preset];
  },

  updateLoadingInformation: function (wsStorageData, appliedHash) {
    const noLoading = [false, 0, ''];

    if (!wsStorageData?.students || !appliedHash) {
      return noLoading;
    }

    const students = wsStorageData.students;
    const totalStudents = Object.keys(students).length;

    if (totalStudents === 0) {
      return noLoading;
    }

    let returnedResponses = 0;

    for (const studentId of Object.keys(students)) {
      const student = students[studentId];
      if (checkForResponse(student, appliedHash, ClassroomTextHighlightLoadingQueries)) {
        returnedResponses++;
      }
    }

    console.log(`[updateLoadingInformation] ${returnedResponses}/${totalStudents} responded for hash=${appliedHash.substring(0, 12)}...`);

    if (totalStudents === returnedResponses) {
      return noLoading;
    }

    const loadingProgress = returnedResponses / totalStudents + 0.1;
    const outputText = `Fetching responses from server. This will take a few minutes. (${returnedResponses}/${totalStudents} received)`;
    return [true, loadingProgress, outputText];
  },

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
    if (triggeredItem?.type !== 'WOStudentTileExpand') {
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
  renderExpandedStudent: function (wsStorageData, selectedStudentId, isModalOpen, value, options, optionHash) {
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

    const selectedHighlights = fetchSelectedItemsFromOptions(value, options, 'highlight');
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    const childContent = createDashComponent(
      DASH_HTML_COMPONENTS, 'Div',
      {
        children: [
          createProcessTags({ ...doc }, selectedMetrics),
          createDashComponent(
            LO_DASH_REACT_COMPONENTS, 'WOAnnotatedText',
            formatStudentData({ ...doc }, selectedHighlights)
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
    const visible = { };
    const hidden = { display: 'none' };

    const titleStyle = showIdentity ? visible : hidden;
    const docTitleStyle = showIdentity ? visible : hidden;
    const iconClass = showIdentity ? 'fas fa-eye' : 'fas fa-eye-slash';

    return [titleStyle, docTitleStyle, iconClass];
  },

  updateLegend: function (value, options) {
    const selectedHighlights = fetchSelectedItemsFromOptions(value, options, 'highlight');
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');
    const total = selectedHighlights.length + selectedMetrics.length;

    if (selectedHighlights.length === 0) {
      return [
        'No highlights selected yet. Click "Choose What to Highlight" in the toolbar, select your options, then click "Run."',
        total
      ];
    }
    let output = selectedHighlights.map(highlight => {
      const color = highlight.highlight.color;
      const legendItem = createDashComponent(
        DASH_HTML_COMPONENTS, 'Div',
        {
          children: [
            createDashComponent(
              DASH_HTML_COMPONENTS, 'Span',
              { style: { width: '0.875rem', height: '0.875rem', backgroundColor: color, display: 'inline-block', marginRight: '0.5rem' } }
            ),
            highlight.label
          ]
        }
      );
      return legendItem;
    });
    output = output.concat('Note: words in the student text may have multiple highlights. Hover over a word for the full list of which options apply.');
    return [output, total];
  },

  /**
   * Determine the initial walkthrough step based on whether the user
   * has previously completed/skipped it (persisted in localStorage).
   * Also writes back to localStorage when the walkthrough is dismissed.
   *
   * Returns [walkthroughStep, seenFlag].
   */
  initWalkthroughFromStorage: function (step, hasSeenWalkthrough) {
    // On initial load (no trigger), check localStorage flag
    const triggered = window.dash_clientside.callback_context?.triggered_id;

    if (!triggered) {
      // Initial load: if they've seen it before, keep it closed
      if (hasSeenWalkthrough) {
        return [-1, true];
      }
      // First visit: open at step 0
      return [0, false];
    }

    // Step changed (user navigated/dismissed/reopened)
    if (step === -1) {
      // User dismissed or completed — mark as seen
      return [-1, true];
    }

    // User reopened via help button or is navigating
    return [step, hasSeenWalkthrough];
  },
};
