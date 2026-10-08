// Prevent protected admin pages from being shown from browser history after logout.
(function enforceAdminSession() {
  const publicPages = new Set([
    "ad-login.html", "ad-forgot-pass.html", "ad-verify-otp.html", "ad-reset-pass.html"
  ]);
  const page = window.location.pathname.split("/").pop().toLowerCase();
  if (publicPages.has(page)) return;

  const requireSession = () => {
    if (!localStorage.getItem("admin_access_token")) {
      window.location.replace("../index.html");
    }
  };

  requireSession();
  window.addEventListener("pageshow", requireSession);
  window.addEventListener("storage", event => {
    if (event.key === "admin_access_token" && !event.newValue) requireSession();
  });
})();
