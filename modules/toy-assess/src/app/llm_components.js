import React from 'react';

import { useState } from 'react'; // For debugging / dev. Should never be used in final code.
import { useDispatch } from 'react-redux';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';

import * as lo_event from 'lo_event';

import { useComponentSelector, extractChildrenText } from './utils.js';

import { Spinner, Button } from './base_components';

export const UPDATE_LLM_RESPONSE = 'UPDATE_LLM_RESPONSE';

const LLMDialog = ({ children, id, onCloseDialog }) => {
  return (
    <dialog open onClose={onCloseDialog}>
      <div style={styles.dialogHeader}>
        <h2 style={styles.dialogTitle}>Prompt Title</h2>
        <span style={styles.dialogClose} onClick={onCloseDialog}>
          <FontAwesomeIcon icon={faTimes} />
        </span>
      </div>
      <div style={styles.dialogContent}>
        {children}
      </div>
    </dialog>
  );
}


// This will go in a CSS file later. For dev.
const styles = {
  questionMark: {
    fontSize: '0.75rem',
    color: 'blue',
    cursor: 'pointer',
    marginRight: '0.75rem',
  },
  dialog: {
    position: "fixed",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    boxShadow: "0 0 5px rgba(0, 0, 0, 0.2)",
    borderRadius: "5px",
    padding: "20px",
    backgroundColor: "white",
    zIndex: "999",
  },
  dialogHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
  },
  dialogTitle: {
    margin: "0",
  },
  dialogClose: {
    cursor: "pointer",
  },
  dialogContent: {
    marginBottom: "20px",
  },
};

