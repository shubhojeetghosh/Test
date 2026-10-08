(function () {
  const body = document.getElementById("studentResultsBody");
  const params = new URLSearchParams(window.location.search);
  const userId = params.get("user_id");
  const token = localStorage.getItem("admin_access_token");

  function cellText(value) {
    return String(value ?? "—").replace(/[&<>"']/g, character => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[character]);
  }

  function dateText(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
  }

  async function loadStudentResults() {
    if (!userId || !token) {
      body.innerHTML = '<tr><td colspan="7" class="student-results-message">Student ID is missing or your admin session expired. Return to the admin login and try again.</td></tr>';
      return;
    }

    try {
      const pageSize = 500;
      const attempts = [];
      let offset = 0;
      let student = null;
      while (true) {
        const response = await fetch(
          `${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}/attempts?limit=${pageSize}&offset=${offset}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.detail || "Could not load this student's exam history.");
        }

        student = data.student || student;
        const page = Array.isArray(data.attempts) ? data.attempts : [];
        attempts.push(...page);
        if (page.length < pageSize) break;
        offset += page.length;
      }

      if (student) {
        document.getElementById("studentName").textContent = student.name || "Student";
        document.getElementById("studentEmail").textContent = student.email || "";
      } else {
        document.getElementById("studentName").textContent = `Student #${userId}`;
      }

      if (!attempts.length) {
        body.innerHTML = '<tr><td colspan="7" class="student-results-message">This student has no exam attempts yet.</td></tr>';
        return;
      }

      body.innerHTML = attempts.map(attempt => {
        const result = attempt.result || {};
        const submitted = attempt.submitted_at;
        return `<tr>
          <td>${cellText(attempt.exam?.title || `Exam ${attempt.exam?.id ?? "—"}`)}</td>
          <td>${attempt.set_id == null ? "—" : cellText(attempt.set_id)}</td>
          <td>${result.score == null ? "—" : cellText(result.score)}</td>
          <td>${result.percentage == null ? "—" : `${cellText(result.percentage)}%`}</td>
          <td>${result.correct_answers == null ? "—" : cellText(result.correct_answers)}</td>
          <td>${cellText(String(attempt.status || "Unknown").replaceAll("_", " "))}</td>
          <td>${cellText(dateText(submitted))}</td>
        </tr>`;
      }).join("");
    } catch (error) {
      console.error("Student results loading failed:", error);
      body.innerHTML = `<tr><td colspan="7" class="student-results-message">${cellText(error.message || "Could not load this student's exam history.")}</td></tr>`;
    }
  }

  document.getElementById("logoutBtn")?.addEventListener("click", () => {
    localStorage.removeItem("admin_access_token");
    localStorage.removeItem("admin_user");
    window.location.replace("../index.html");
  });

  loadStudentResults();
})();
