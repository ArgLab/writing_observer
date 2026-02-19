/*
 * This file contains generic components and most of the machinery
 * behind the system. The goal is to gradually make the main page file
 * simple enough for a relatively non-technical person to edit, and then
 * to abstract much of it into data files.
 *
 * To do that, we are happy to have extra complexity here.
 */

import React from 'react';

import * as lo_event from 'lo_event';
import { reduxLogger } from 'lo_event/lo_event/reduxLogger.js';
import { consoleLogger } from 'lo_event/lo_event/consoleLogger.js';
import * as reducers from 'lo_event/lo_event/lo_assess/reducers.js';
import * as debug from 'lo_event/lo_event/debugLog.js';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faQuestionCircle, faTimes } from '@fortawesome/free-solid-svg-icons';

import './base-style.css';
import './sidebar-panel.css';
import './globals.css';

lo_event.init(
  "org.ets.sba",
  "0.0.1",
  [consoleLogger(), reduxLogger([], {})],
  {
	  debugLevel: debug.LEVEL.EXTENDED,
	  debugDest: [debug.LOG_OUTPUT.CONSOLE],
	  useDisabler: false,
	  queueType: lo_event.QueueType.IN_MEMORY
  }
);

lo_event.go();
