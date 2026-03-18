/**
 * Returns the WebSocket origin based on the current browser window location.
 *
 * - Uses `wss:` if the page is loaded over HTTPS.
 * - Uses `ws:` if the page is loaded over HTTP.
 * - Returns `null` when executed in a non-browser environment (e.g., SSR or Node.js),
 *   where `window` is undefined.
 */

function trimTrailingSlash(value) {
  return value?.replace(/\/+$/, "");
}

function getRuntimeWsOrigin() {
  if (typeof window === "undefined") return null;

  const runtimeValue = window.__PORTFOLIO_DIFF_CONFIG?.NEXT_PUBLIC_LO_WS_ORIGIN;
  return trimTrailingSlash(runtimeValue) || null;
}

function getWsOriginFromWindow() {
  if (typeof window === "undefined") return null;

  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}`;
}

export function getConfiguredWsOrigin() {
  return (
    getRuntimeWsOrigin() ||
    trimTrailingSlash(process.env.NEXT_PUBLIC_LO_WS_ORIGIN) ||
    getWsOriginFromWindow() ||
    "ws://localhost:8888"
  );
}
