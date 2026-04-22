// background.js
/*
Background script. This works across all of Google Chrome.
*/

import { CONFIG } from "./service_worker_config.js";
import { googledocs_id_from_url, googledocs_tab_id_from_url } from './writing_common';
import * as loEvent from 'lo_event/lo_event/lo_event.js';
import * as loEventDebug from 'lo_event/lo_event/debugLog.js';
import { websocketLogger } from 'lo_event/lo_event/websocketLogger.js';
import { consoleLogger } from 'lo_event/lo_event/consoleLogger.js';
import { browserInfo } from 'lo_event/lo_event/metadata/browserinfo.js';
import { chromeAuth } from 'lo_event/lo_event/metadata/chromeauth.js';
import { localStorageInfo, sessionStorageInfo } from 'lo_event/lo_event/metadata/storage.js';

const { RAW_DEBUG, WEBSOCKET_SERVER_URL } = CONFIG;

// Track which tabs currently have an active content script.
// Used to send a clean 'all_docs_closed' event when all Google Docs tabs close,
// giving the server a session boundary without tearing down the WebSocket.
const activeContentTabs = new Set();

// lo_event is initialized at most once per service worker lifetime.
// Chrome will kill the worker when idle, which naturally tears down
// the WebSocket. When the worker wakes back up, the module re-executes
// from scratch so a fresh init() is safe.
let loggerStarted = false;

const manifestVersion = chrome.runtime.getManifest().version;

/**
 * Initialize lo_event exactly once per service worker lifetime.
 * Subsequent calls are no-ops. Chrome's worker lifecycle handles
 * cleanup — when the worker is terminated, all in-memory state
 * (including the WebSocket) is destroyed. On wake-up the module
 * re-evaluates, `loggerStarted` resets to false, and we get a
 * clean init().
 */
function ensureLoggerStarted() {
    if (loggerStarted) return;
    loggerStarted = true;

    const wsLogger = websocketLogger(WEBSOCKET_SERVER_URL);
    loEvent.init(
        'org.mitros.writing_analytics',
        manifestVersion,
        [consoleLogger(), wsLogger],
        {
            debugLevel: loEventDebug.LEVEL.SIMPLE,
            metadata: [
                browserInfo(),
                chromeAuth(),
                localStorageInfo(),
                sessionStorageInfo()
            ]
        }
    );
    loEvent.go();
    loEvent.logEvent('extension_loaded', {});
    logFromServiceWorker('Extension loaded');
}

/**
 * Notify the server that the user has closed all Google Docs tabs.
 * This provides a clean session boundary for analytics without
 * triggering the server-side terminate handler (which would close
 * the WebSocket). The WebSocket stays alive so that if the user
 * opens a new doc before the worker dies, events flow immediately.
 *
 * We intentionally do NOT reset `loggerStarted` or tear down
 * lo_event. The worker will die naturally when Chrome decides
 * it's idle, which destroys the WebSocket from the client side.
 */
function maybeSendSessionEnd() {
    if (loggerStarted && activeContentTabs.size === 0) {
        loEvent.logEvent('all_docs_closed', {});
        logFromServiceWorker('All Google Docs tabs closed');
    }
}

/**
 * Check for existing Google Docs tabs when the service worker starts.
 * This covers the case where Chrome wakes the worker (e.g. due to a
 * webRequest or message) but the content scripts already sent their
 * 'content_script_ready' message during a previous worker lifetime.
 */
async function reconcileActiveGoogleDocsTabs() {
    try {
        const tabs = await chrome.tabs.query({ url: ['*://docs.google.com/document/*'] });
        for (const tab of tabs) {
            if (tab.id !== undefined && isGoogleDocsDocumentUrl(tab.url)) {
                activeContentTabs.add(tab.id);
            }
        }
        if (activeContentTabs.size > 0) {
            logFromServiceWorker(
                `Reconciled ${activeContentTabs.size} Google Docs tab(s) on worker start`
            );
            ensureLoggerStarted();
        }
    } catch (error) {
        logFromServiceWorker(`Failed to reconcile Google Docs tabs: ${error}`);
    }
}

/**
 * Replacement for chrome.extension.getBackgroundPage().console.log()
 * which is not available in Manifest V3 service workers.
 */
function logFromServiceWorker(event) {
    console.log(event);
}

/**
 * Returns true if `url` points to a Google Docs document.
 */
function isGoogleDocsDocumentUrl(url) {
    return typeof url === 'string' && /^https?:\/\/docs\.google\.com\/document\//i.test(url);
}

/**
 * Check if this is a Google Docs save request. Return true for something like:
 * https://docs.google.com/document/d/1lt_lSfEM.../save?id=...
 * And false otherwise.
 *
 * Note that while `save` is often early in the URL, on the first
 * few requests of a web page load, it can be towards the end. We
 * went from a conservative regexp to a liberal one. We should
 * confirm this never catches extra requests, though.
 */
function this_a_google_docs_save(request) {
    return /.*:\/\/docs\.google\.com\/document\/(.*)\/save/i.test(request.url);
}

/**
 * These requests correspond to some server-push features, such as
 * collaborative editing. We still need to reverse-engineer these.
 *
 * Note that we cannot monitor request responses without more
 * complex JavaScript. See:
 * https://stackoverflow.com/questions/6831916
 */
function this_a_google_docs_bind(request) {
    return /.*:\/\/docs\.google\.com\/document\/(.*)\/bind/i.test(request.url);
}

// Listen for the keystroke messages from the page script and forward to the server.
chrome.runtime.onMessage.addListener(
    function (request, sender, _sendResponse) {
        // Guard against null / malformed messages from other extensions or
        // internal Chrome plumbing.
        if (!request || typeof request !== 'object') {
            return false;
        }

        // Lifecycle messages from content scripts manage tab tracking
        if (request.type === 'content_script_ready') {
            if (sender.tab?.id !== undefined) {
                activeContentTabs.add(sender.tab.id);
            }
            ensureLoggerStarted();
            return false;
        }

        if (request.type === 'content_script_unloading') {
            if (sender.tab?.id !== undefined) {
                activeContentTabs.delete(sender.tab.id);
                maybeSendSessionEnd();
            }
            return false;
        }

        // Ignore messages that don't carry an event type — we can't route them.
        if (!request.event) {
            logFromServiceWorker('Ignoring message with no event type');
            return false;
        }

        // Any analytics message from a content script means the tab is active.
        // Trust the sender rather than gating on activeContentTabs membership,
        // which avoids a race with reconcileActiveGoogleDocsTabs().
        if (sender.tab?.id !== undefined) {
            activeContentTabs.add(sender.tab.id);
        }
        ensureLoggerStarted();

        request['wa_source'] = 'client_page';
        loEvent.logEvent(request['event'], request);

        // Explicitly return false — we will not call sendResponse asynchronously.
        return false;
    }
);

// Listen for web loads, and forward relevant ones (e.g. saves) to the server.
chrome.webRequest.onBeforeRequest.addListener(
    /*
      This allows us to log web requests. There are two types of web requests:
      * Ones we understand (SEMANTIC)
      * Ones we don't (RAW/DEBUG)
  
      There is an open question as to how we ought to handle RAW/DEBUG
      events. We will reduce potential issues around collecting data
      we don't want (privacy, storage, bandwidth) if we silently drop
      these. On the other hand, we significantly increase risk of
      losing user data should Google ever change their web API. If we
      log everything, we have good odds of being able to
      reverse-engineer the new API, and reconstruct what happened.
  
      Our current strategy is to:
      * Log the former requests in a clean way, extracting the data we
        want
      * Have a flag to log the debug requests (which includes the
        unparsed version of events we want).
      We should step through and see how this code manages failures.
  
      For development purposes, both modes of operation are
      helpful. Having these is nice for reverse-engineering,
      especially new pages. They do inject a lot of noise, though, and
      from there, being able to easily ignore these is nice.
    */
    function (request) {
        // A webRequest for docs.google.com means a Google Docs tab is active.
        // Make sure the logger is running.
        ensureLoggerStarted();

        let formdata = {};
        let event;
        if (request.requestBody) {
            formdata = request.requestBody.formData;
        }
        if (!formdata) {
            formdata = {};
        }
        if (RAW_DEBUG) {
            loEvent.logEvent('raw_http_request', {
                'url': request.url,
                'form_data': formdata
            });
        }

        if (this_a_google_docs_save(request)) {
            try {
                /* We should think through which time stamps we should log. These are all subtly
                   different: browser event versus request timestamp, as well as user time zone
                   versus GMT. */
                event = {
                    'doc_id': googledocs_id_from_url(request.url),
                    'tab_id': googledocs_tab_id_from_url(request.url),
                    'url': request.url,
                    'bundles': JSON.parse(formdata.bundles),
                    'rev': formdata.rev,
                    'timestamp': parseInt(request.timeStamp, 10)
                };
                logFromServiceWorker(event);
                loEvent.logEvent('google_docs_save', event);
            } catch (err) {
                /*
                  Oddball events, like text selections.
                */
                event = {
                    'doc_id': googledocs_id_from_url(request.url),
                    'tab_id': googledocs_tab_id_from_url(request.url),
                    'url': request.url,
                    'formdata': formdata,
                    'rev': formdata.rev,
                    'timestamp': parseInt(request.timeStamp, 10)
                };
                loEvent.logEvent('google_docs_save_extra', event);
            }
        } else if (this_a_google_docs_bind(request)) {
            logFromServiceWorker(request);
        } else {
            logFromServiceWorker('Not a save or bind: ' + request.url);
        }
    },
    { urls: ['*://docs.google.com/*'] },
    ['requestBody']
);

// Clean up tab tracking when a tab is closed.
chrome.tabs.onRemoved.addListener(function (tabId) {
    activeContentTabs.delete(tabId);
    maybeSendSessionEnd();
});

// Track navigation: add tabs that navigate to Google Docs,
// remove tabs that navigate away. Only react when the URL
// actually changes to avoid noise from status/favicon/title updates.
chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, _tab) {
    if (!changeInfo.url) return;

    if (isGoogleDocsDocumentUrl(changeInfo.url)) {
        activeContentTabs.add(tabId);
        ensureLoggerStarted();
    } else if (activeContentTabs.has(tabId)) {
        activeContentTabs.delete(tabId);
        maybeSendSessionEnd();
    }
});

// Reconcile on worker start — fire and forget since all event paths
// independently call ensureLoggerStarted() when needed.
reconcileActiveGoogleDocsTabs();

// Re-inject content scripts when the extension is reloaded, upgraded, or re-installed.
// https://stackoverflow.com/questions/10994324/chrome-extension-content-script-re-injection-after-upgrade-or-install
chrome.runtime.onInstalled.addListener(reinjectContentScripts);
async function reinjectContentScripts() {
    for (const contentScript of chrome.runtime.getManifest().content_scripts) {
        for (const tab of await chrome.tabs.query({ url: contentScript.matches })) {
            try {
                await chrome.scripting.executeScript({
                    target: { tabId: tab.id, allFrames: true },
                    files: contentScript.js
                });
                console.log(`Content script re-injected into tab ${tab.id}`);
            } catch (err) {
                console.warn(`Failed to inject into tab ${tab.id}: ${err.message}`);
            }
        }
    }
}
