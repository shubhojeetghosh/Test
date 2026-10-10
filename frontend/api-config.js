/* Shared API address for every student and admin page. */
(function () {
  // The frontend Vercel project proxies API traffic to FastAPI so auth cookies
  // remain first-party for browsers that block third-party cookies.
  const PRODUCTION_API_URL = "/backend";
  const isLocalDevelopment =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  const localApiHost = window.location.hostname === "localhost"
    ? "localhost"
    : "127.0.0.1";
  const configuredUrl = window.API_BASE_URL ||
    (isLocalDevelopment ? `http://${localApiHost}:8000` : PRODUCTION_API_URL);

  window.API_BASE_URL = configuredUrl.replace(/\/+$/, "");

  // Discard bearer credentials from older releases. The only browser-side
  // marker is a non-secret value; the actual JWT now lives in an HttpOnly cookie.
  for (const key of ["access_token", "admin_access_token"]) {
    const value = window.localStorage.getItem(key);
    if (value && value !== "cookie-session") {
      window.localStorage.removeItem(key);
    }
  }

  // Local development uses different localhost ports, while production uses
  // the same frontend origin. Include cookies for either deployment shape.
  const originalFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : input?.url || "";
    if (url.startsWith(window.API_BASE_URL)) {
      return originalFetch(input, {
        ...(init || {}),
        credentials: init?.credentials || "include"
      });
    }
    return originalFetch(input, init);
  };

}());
