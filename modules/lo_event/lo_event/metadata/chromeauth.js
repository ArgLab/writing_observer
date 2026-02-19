/*
  This function is a wrapper for retrieving profile information using
  the Chrome browser's identity API. It addresses a bug in the Chrome
  function and converts it into a modern async function. The bug it
  works around can be found at
  https://bugs.chromium.org/p/chromium/issues/detail?id=907425#c6.

  To do: Add chrome.identity.getAuthToken() to retrieve an
  authentication token, so we can do real authentication.

  Returns:
    A Promise that resolves with the user's profile information.

  Example usage:
    const profileInfo = await chromeProfileInfoWrapper();
    console.log(profileInfo);

  Users should switch to chromeIdentityHeader(), below. This function name should also
  mention `chrome`, but I don't want to do that without updating the extension at the
  same time.
*/
function chromeProfileInfoWrapper() {
  if (typeof chrome !== 'undefined' && chrome.identity) {
    try {
      return new Promise((resolve, reject) => {
        chrome.identity.getProfileUserInfo({ accountStatus: 'ANY' }, function (data) {
          resolve(data);
        });
      });
    } catch (e) {
      return new Promise((resolve, reject) => {
        chrome.identity.getProfileUserInfo(function (data) {
          resolve(data);
        });
      });
    }
  }
  // Default to an empty object
  return new Promise((resolve, reject) => {
    resolve({});
  });
}

export const chromeAuth = () => ({
  name: 'chrome_identity',
  func: chromeProfileInfoWrapper,
  async: true,
  static: false
});
