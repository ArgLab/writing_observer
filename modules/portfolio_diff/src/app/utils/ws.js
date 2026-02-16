/**
 * Returns the WebSocket origin based on the current browser window location.
 *
 * - Uses `wss:` if the page is loaded over HTTPS.
 * - Uses `ws:` if the page is loaded over HTTP.
 * - Returns `null` when executed in a non-browser environment (e.g., SSR or Node.js),
 *   where `window` is undefined.
 */

export function getWsOriginFromWindow() {
  if (typeof window === "undefined") return null;

  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}`;
}