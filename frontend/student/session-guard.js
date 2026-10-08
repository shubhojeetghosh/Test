// Redirect protected student pages when their session has ended, including
// pages restored from the browser's back-forward cache after logout.
(function enforceStudentSession() {
  const page = window.location.pathname.split("/").pop().toLowerCase();
  const publicPages = new Set([
    "login.html", "register.html", "forgot-pass.html", "reset-pass.html",
    "verify-otp.html", "verify-registration.html"
  ]);
  if (publicPages.has(page)) return;

  const requireSession = () => {
    if (!localStorage.getItem("access_token")) {
      window.location.replace("../index.html");
    }
  };

  requireSession();
  window.addEventListener("pageshow", requireSession);
  window.addEventListener("storage", event => {
    if (event.key === "access_token" && !event.newValue) requireSession();
  });
})();
