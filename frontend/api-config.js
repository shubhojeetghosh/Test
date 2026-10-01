/* Shared API address for every student and admin page. */
(function () {
  // Set this to the deployed FastAPI URL after the backend is deployed.
  // Leave it empty when frontend and backend share the same origin.
  const PRODUCTION_API_URL = "";
  const isLocalDevelopment =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  const configuredUrl = window.API_BASE_URL ||
    (isLocalDevelopment ? "http://127.0.0.1:8000" : PRODUCTION_API_URL);

  window.API_BASE_URL = configuredUrl.replace(/\/+$/, "");
}());
