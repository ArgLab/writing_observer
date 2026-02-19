'use client';
import React from 'react';

import { Provider } from 'react-redux';
import * as reduxLogger from 'lo_event/lo_event/reduxLogger.js';

const StoreWrapper = ({ children }) => (
  <Provider store={reduxLogger.store}>
    {children}
  </Provider>
);

export default StoreWrapper;
