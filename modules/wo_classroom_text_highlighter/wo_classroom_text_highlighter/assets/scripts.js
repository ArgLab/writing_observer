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

window.dash_clientside.wo_classroom_text_highlighter = {
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

  applyOptionsAndCloseModal: function (clicks, stagedValue) {
    if (!clicks) {
      return [window.dash_clientside.no_update, window.dash_clientside.no_update];
    }
    console.log('[applyOptionsAndCloseModal] Applying staged options');
    return [stagedValue, false];
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
      return 'No students';
    }
    let output = [];

    const selectedHighlights = fetchSelectedItemsFromOptions(value, options, 'highlight');
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');

    console.log('[populateOutput] Using hash:', optionHash ? optionHash.substring(0, 12) + '...' : 'NONE');

    const students = wsStorageData.students;
    for (const student in students) {
      const selectedDocument = students[student].doc_id || Object.keys(students[student].documents || {})[0] || '';
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
   * Expand a student into the detail modal.
   *
   * Returns [modalTitle, modalBodyChild, isOpen].
   *
   * We extract the student's display name for the modal title
   * and only the inner content (process tags + annotated text)
   * for the body — avoiding the tile chrome (expand button,
   * profile header, etc.).
   */
  expandCurrentStudent: function (clicks, children, ids, isModalOpen, currentChild) {
    const triggeredItem = window.dash_clientside.callback_context?.triggered_id ?? null;
    if (!triggeredItem) { return window.dash_clientside.no_update; }

    let id = null;

    if (triggeredItem?.type === 'WOStudentTile') {
      // Tile content updated while modal is already open — refresh it
      if (!isModalOpen || !currentChild) {
        return window.dash_clientside.no_update;
      }
      id = currentChild?.props?.id?.index;
    } else if (triggeredItem?.type === 'WOStudentTileExpand') {
      id = triggeredItem?.index;
    } else {
      return window.dash_clientside.no_update;
    }

    const index = ids.findIndex(item => item.index === id);
    if (index === -1) { return window.dash_clientside.no_update; }

    // children[index] is the wrapper div's children array.
    // children[index][0] is the WOStudentTextTile component.
    const tile = children[index][0];
    const tileProps = tile?.props || {};

    // Build a readable student name from the profile
    const profile = tileProps.profile || {};
    const studentName = [profile.name_given, profile.name_family]
      .filter(Boolean)
      .join(' ') || 'Student';

    // The actual content lives inside childComponent (metrics + annotated text).
    // This avoids pulling in the expand button, profile header, etc.
    const innerContent = tileProps.childComponent || '';

    return [studentName, innerContent, true];
  },

  updateLegend: function (value, options) {
    const selectedHighlights = fetchSelectedItemsFromOptions(value, options, 'highlight');
    const selectedMetrics = fetchSelectedItemsFromOptions(value, options, 'metric');
    const total = selectedHighlights.length + selectedMetrics.length;

    if (selectedHighlights.length === 0) {
      return ['No options selected. Click on the `Options` to select them.', total];
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
    output = output.concat('Note: words in the student text may have multiple highlights. Hover over a word for the full list of which options apply');
    return [output, total];
  }
};
