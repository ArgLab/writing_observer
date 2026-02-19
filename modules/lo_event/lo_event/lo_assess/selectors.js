import React from 'react';

import { useSelector } from 'react-redux';

export function useApplicationSelector(selector = s => s) {
  return useSelector(state => selector(state?.application_state));
}

// Get the state for any component, by ID.
export function useComponentSelector(id, selector = s => s) {
  return useApplicationSelector(
    s => selector(s?.component_state?.[id])
  );
}

export function useSettingSelector(setting) {
  return useSelector(state => state?.settings?.[setting]);
}
