import { copyFields } from '../util.js';

// These should be `export`ed, once helpful, since clients might wish
// to use these as a starting point. We'll do that when the first
// use-case comes up, though (so if you'd like access, just ask or
// make a PR).

const defaultNavigatorFields = [
  'appCodeName',
  'appName',
  'buildID',
  'cookieEnabled',
  'deviceMemory',
  'language',
  'languages',
  'onLine',
  'oscpu',
  'platform',
  'product',
  'productSub',
  'userAgent',
  'webdriver'
];

const defaultConnectionFields = [
  'effectiveType',
  'rtt',
  'downlink',
  'type',
  'downlinkMax'
];

const defaultDocumentFields = [
  'URL',
  'baseURI',
  'characterSet',
  'charset',
  'compatMode',
  'cookie',
  'currentScript',
  'designMode',
  'dir',
  'doctype',
  'documentURI',
  'domain',
  'fullscreen',
  'fullscreenEnabled',
  'hidden',
  'inputEncoding',
  'isConnected',
  'lastModified',
  'location',
  'mozSyntheticDocument',
  'pictureInPictureEnabled',
  'plugins',
  'readyState',
  'referrer',
  'title',
  'visibilityState'
];

const defaultWindowFields = [
  'closed',
  'defaultStatus',
  'innerHeight',
  'innerWidth',
  'name',
  'outerHeight',
  'outerWidth',
  'pageXOffset',
  'pageYOffset',
  'screenX',
  'screenY',
  'status'
];

/*
  Browser information object, primarily for debugging. Note that not
  all fields will be available in all browsers and contexts. If not
  available, it will return null (this is even usable in node.js,
  but it will simply return that there is no navigator, window, or
  document object).

  @returns {Object} An object containing the browser's navigator, window, and document information.

  Example usage:
    const browserInfo = getBrowserInfo();
    console.log(browserInfo);
*/

export function getBrowserInfo({
  navigatorFields = defaultNavigatorFields, 
  connectionFields = defaultConnectionFields, 
  documentFields = defaultDocumentFields, 
  windowFields = defaultWindowFields
} = {}) {
  const browserInfo = {
    navigator: typeof navigator !== 'undefined' ? copyFields(navigator, navigatorFields) : null,
    connection: typeof navigator !== 'undefined' && navigator.connection ? copyFields(navigator.connection, connectionFields) : null,
    document: typeof document !== 'undefined' ? copyFields(document, documentFields) : null,
    window: typeof window !== 'undefined' ? copyFields(window, windowFields) : null
  };

  return { browser_info: browserInfo };
}

export const browserInfo = () =>  ({
  name: 'browserInfo',
  func: getBrowserInfo,
  async: false,
  static: false // Mostly static, but window size might change.
});
