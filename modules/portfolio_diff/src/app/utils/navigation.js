/**
 * Force a full page navigation to a route with query params.
 * This intentionally avoids Next.js router to prevent `_rsc` fetches.
 *
 * @param {string} path - Relative path (e.g. "students/compare")
 * @param {Object} queryParams - Key/value pairs for query string
 */
export function navigateTo(path, queryParams = {}) {
  if (typeof window === "undefined") return;

  const query = Object.entries(queryParams)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => {
      return `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`;
    })
    .join("&");

  const url = query ? `${path}?${query}` : path;

  // Force full navigation (prevents Next.js from app-router data fetching)
  window.location.assign("/wo_portfolio_diff/portfolio_diff/" + url);
}
