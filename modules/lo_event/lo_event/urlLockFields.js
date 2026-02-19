let urlListenerInitialized = false;
let lastUrl = null;

function parseUrlFields (url, baseUrl) {
  if (!url) {
    return null;
  }

  try {
    const parsed = new URL(url, baseUrl);
    return {
      url: parsed.href,
      url_path: parsed.pathname
    };
  } catch (error) {
    return null;
  }
}

function updateUrlLockFields (setFieldSet, url) {
  const baseUrl = (typeof window !== 'undefined' && window.location) ? window.location.href : undefined;
  const fields = parseUrlFields(url, baseUrl);
  if (!fields) {
    return;
  }

  if (fields.url === lastUrl) {
    return;
  }

  lastUrl = fields.url;
  setFieldSet([fields]);
}

function initializeWindowListeners (setFieldSet) {
  if (typeof window === 'undefined' || !window.location) {
    return;
  }

  updateUrlLockFields(setFieldSet, window.location.href);

  if (!window.addEventListener) {
    return;
  }

  const handleLocationChange = () => updateUrlLockFields(setFieldSet, window.location.href);
  window.addEventListener('popstate', handleLocationChange);
  window.addEventListener('hashchange', handleLocationChange);

  if (window.history) {
    const originalPushState = window.history.pushState;
    const originalReplaceState = window.history.replaceState;

    window.history.pushState = function (...args) {
      const result = originalPushState.apply(this, args);
      handleLocationChange();
      return result;
    };

    window.history.replaceState = function (...args) {
      const result = originalReplaceState.apply(this, args);
      handleLocationChange();
      return result;
    };
  }
}

function initializeChromeListeners (setFieldSet) {
  if (typeof chrome === 'undefined' || !chrome.tabs) {
    return;
  }

  const handleTab = (tab) => {
    if (tab && tab.url) {
      updateUrlLockFields(setFieldSet, tab.url);
    }
  };

  if (chrome.tabs.onUpdated && chrome.tabs.onUpdated.addListener) {
    chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
      if (changeInfo && changeInfo.url) {
        updateUrlLockFields(setFieldSet, changeInfo.url);
        return;
      }
      handleTab(tab);
    });
  }

  if (chrome.tabs.onActivated && chrome.tabs.onActivated.addListener) {
    chrome.tabs.onActivated.addListener((activeInfo) => {
      if (!chrome.tabs.query) {
        return;
      }
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        handleTab(tabs && tabs[0]);
      });
    });
  }

  if (chrome.tabs.query) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      handleTab(tabs && tabs[0]);
    });
  }
}

export function initializeUrlLockFields (setFieldSet) {
  if (urlListenerInitialized) {
    return;
  }
  urlListenerInitialized = true;

  initializeWindowListeners(setFieldSet);
  initializeChromeListeners(setFieldSet);
}
