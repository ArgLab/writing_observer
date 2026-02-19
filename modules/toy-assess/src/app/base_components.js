// Basic components. This should depend on no other component files.

import React from 'react';

import { useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEdit, faAngleDown, faAngleRight, faExclamationTriangle, faQuestionCircle, fasQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';
import { faCheckCircle, faTimesCircle, faDotCircle } from '@fortawesome/free-solid-svg-icons';

import * as lo_event from 'lo_event';
import * as reduxLogger from 'lo_event/lo_event/reduxLogger.js';

import { useComponentSelector, useSettingSelector } from './utils.js';
import { library } from '@fortawesome/fontawesome-svg-core';

// Debug log function. This should perhaps go away / change / DRY eventually.
const DEBUG = false;
const dclog = (...args) => {if(DEBUG) {console.log.apply(console, Array.from(args));} };

library.add(faCheckCircle, faDotCircle, faTimesCircle, faQuestionCircle);
