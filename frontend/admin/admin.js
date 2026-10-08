document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       API CONFIGURATION
    ===================================================== */

    const API_BASE_URL =
        window.EPS_API?.baseUrl ||
        window.API_BASE_URL;


    /* =====================================================
       PASSWORD SHOW / HIDE
    ===================================================== */

    const passwordToggleButtons =
        document.querySelectorAll(".password-toggle");

    passwordToggleButtons.forEach(button => {

        button.addEventListener("click", () => {

            const targetId =
                button.dataset.target;

            const passwordInput =
                document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }

            if (passwordInput.type === "password") {

                passwordInput.type = "text";

                button.textContent = "Hide";

                button.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            } else {

                passwordInput.type = "password";

                button.textContent = "Show";

                button.setAttribute(
                    "aria-label",
                    "Show password"
                );

            }

        });

    });


    /* =====================================================
       CURRENT USERS
    ===================================================== */

    let currentUsers = [];


    /* =====================================================
       DYNAMIC DATA ELEMENTS
    ===================================================== */

    const totalUsers =
        document.getElementById("totalUsers");

    const usersGrowth =
        document.getElementById("usersGrowth");

    const totalQuizzes =
        document.getElementById("totalQuizzes");

    const quizzesGrowth =
        document.getElementById("quizzesGrowth");

    const totalQuestions =
        document.getElementById("totalQuestions");

    const questionsGrowth =
        document.getElementById("questionsGrowth");

    const totalAttempts =
        document.getElementById("totalAttempts");

    const attemptsGrowth =
        document.getElementById("attemptsGrowth");

    const activityList =
        document.getElementById("activityList");

    const usersTable =
        document.getElementById("usersTable");

    const quizzesTable =
        document.getElementById("quizzesTable");

    const averageScore =
        document.getElementById("averageScore");

    const passRate =
        document.getElementById("passRate");

    const todayAttempts =
        document.getElementById("todayAttempts");


    /* =====================================================
       ADMIN PROFILE ELEMENTS
    ===================================================== */

    const sidebarAdminName =
        document.getElementById("sidebarAdminName");

    const sidebarAdminRole =
        document.getElementById("sidebarAdminRole");

    const sidebarAdminAvatar =
        document.getElementById("sidebarAdminAvatar");

    const topAdminName =
        document.getElementById("topAdminName");

    const topAdminRole =
        document.getElementById("topAdminRole");

    const topAdminAvatar =
        document.getElementById("topAdminAvatar");

    const welcomeAdminName =
        document.getElementById("welcomeAdminName");

    const settingsAdminName =
        document.getElementById("settingsAdminName");

    const settingsAdminEmail =
        document.getElementById("settingsAdminEmail");


    /* =====================================================
       NAVIGATION ELEMENTS
    ===================================================== */

    const navItems =
        document.querySelectorAll(".nav-item");

    const sections =
        document.querySelectorAll(".content-section");

    const pageTitle =
        document.getElementById("pageTitle");

    const pageSubtitle =
        document.getElementById("pageSubtitle");

    const mobileMenu =
        document.getElementById("mobileMenu");

    const sidebar =
        document.querySelector(".sidebar");

    const adminInquiriesList = document.getElementById("adminInquiriesList");
    const inquiriesFeedback = document.getElementById("inquiriesFeedback");
    const newInquiryCount = document.getElementById("newInquiryCount");

    const notificationsButton = document.getElementById("adminNotificationsButton");
    const notificationsPanel = document.getElementById("adminNotificationsPanel");
    const notificationsList = document.getElementById("adminNotificationsList");
    const notificationsDot = document.getElementById("adminNotificationsDot");
    const notificationsCount = document.getElementById("adminNotificationsCount");

    async function loadSetRequestNotifications() {
        if (!notificationsList) return;
        const adminToken = localStorage.getItem("admin_access_token");
        if (!adminToken) {
            notificationsList.innerHTML = '<p class="admin-notifications-empty">Sign in again to view set requests.</p>';
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/admin/student-access/requests`, {
                headers: { Authorization: `Bearer ${adminToken}` }
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data.detail || "Could not load set requests.");
            const requests = Array.isArray(data.requests) ? data.requests : [];

            if (notificationsDot) notificationsDot.hidden = requests.length === 0;
            if (notificationsCount) {
                notificationsCount.hidden = requests.length === 0;
                notificationsCount.textContent = requests.length > 99 ? "99+" : String(requests.length);
            }
            if (!requests.length) {
                notificationsList.innerHTML = '<p class="admin-notifications-empty">No pending set requests.</p>';
                return;
            }

            notificationsList.innerHTML = requests.map(request => `
                <article class="admin-set-request">
                    <strong>${escapeAdminHtml(request.student_name || "Student")}</strong>
                    <p>${escapeAdminHtml(request.student_email || "")}</p>
                    <p>${escapeAdminHtml(request.exam_title || "Exam")} · Set ${escapeAdminHtml(request.set_number ?? "—")}${request.exam_set_title ? ` — ${escapeAdminHtml(request.exam_set_title)}` : ""}</p>
                    <div class="admin-set-request-actions">
                        <button type="button" class="approve-request" data-set-request-action="unlock" data-request-id="${escapeAdminHtml(request.request_id)}">Approve &amp; unlock</button>
                        <button type="button" class="reject-request" data-set-request-action="reject" data-request-id="${escapeAdminHtml(request.request_id)}">Decline</button>
                    </div>
                </article>
            `).join("");
        } catch (error) {
            console.error("Unable to load set request notifications:", error);
            notificationsList.innerHTML = `<p class="admin-notifications-empty">${escapeAdminHtml(error.message || "Could not load set requests.")}</p>`;
        }
    }

    if (notificationsButton && notificationsPanel) {
        notificationsButton.addEventListener("click", () => {
            const opening = notificationsPanel.hidden;
            notificationsPanel.hidden = !opening;
            notificationsButton.setAttribute("aria-expanded", String(opening));
            if (opening) loadSetRequestNotifications();
        });

        document.getElementById("refreshAdminNotifications")?.addEventListener(
            "click", loadSetRequestNotifications
        );

        notificationsList?.addEventListener("click", async event => {
            const button = event.target.closest("[data-set-request-action][data-request-id]");
            if (!button) return;
            const action = button.dataset.setRequestAction;
            const requestId = button.dataset.requestId;
            button.disabled = true;
            try {
                const response = await fetch(
                    `${API_BASE_URL}/admin/student-access/requests/${encodeURIComponent(requestId)}/${action}`,
                    {
                        method: "POST",
                        headers: { Authorization: `Bearer ${localStorage.getItem("admin_access_token")}` }
                    }
                );
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(data.detail || "Could not update this request.");
                await loadSetRequestNotifications();
            } catch (error) {
                console.error("Set request action failed:", error);
                button.disabled = false;
                button.textContent = error.message || "Please try again";
            }
        });

        document.addEventListener("click", event => {
            if (!notificationsPanel.hidden && !event.target.closest(".admin-notification-wrap")) {
                notificationsPanel.hidden = true;
                notificationsButton.setAttribute("aria-expanded", "false");
            }
        });

        loadSetRequestNotifications();
        window.setInterval(loadSetRequestNotifications, 60000);
    }

    function setInquiriesFeedback(message, state = "") {
        if (!inquiriesFeedback) return;
        inquiriesFeedback.textContent = message;
        inquiriesFeedback.dataset.state = state;
    }

    async function loadAdminInquiries() {
        if (!adminInquiriesList) return;
        setInquiriesFeedback("Loading messages…");
        const adminToken = localStorage.getItem("admin_access_token");
        if (!adminToken) {
            setInquiriesFeedback("Your admin session has expired. Please sign in again.", "error");
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/admin/inquiries?limit=100`, {
                headers: { Authorization: `Bearer ${adminToken}` }
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.detail || data.message || "Unable to load the inbox.");
            }

            if (newInquiryCount) newInquiryCount.textContent = String(data.new_count ?? 0);
            adminInquiriesList.replaceChildren();
            const inquiries = Array.isArray(data.inquiries) ? data.inquiries : [];
            if (!inquiries.length) {
                const empty = document.createElement("div");
                empty.className = "inquiries-empty";
                empty.textContent = "No messages yet. Student questions sent from the website will appear here.";
                adminInquiriesList.append(empty);
            } else {
                inquiries.forEach(inquiry => {
                    const card = document.createElement("article");
                    card.className = "inquiry-item";

                    const header = document.createElement("div");
                    header.className = "inquiry-item-header";
                    const sender = document.createElement("div");
                    const name = document.createElement("div");
                    name.className = "inquiry-sender";
                    name.textContent = inquiry.name || "Student";
                    const email = document.createElement("a");
                    email.className = "inquiry-email";
                    email.href = `mailto:${inquiry.email || ""}?subject=${encodeURIComponent(`Re: ${inquiry.subject || "EPS TOPIK enquiry"}`)}`;
                    email.textContent = inquiry.email || "No email provided";
                    sender.append(name, email);
                    const date = document.createElement("time");
                    date.className = "inquiry-date";
                    if (inquiry.created_at) {
                        date.dateTime = inquiry.created_at;
                        const parsedDate = new Date(inquiry.created_at);
                        date.textContent = Number.isNaN(parsedDate.getTime())
                            ? inquiry.created_at
                            : parsedDate.toLocaleString();
                    } else {
                        date.textContent = "Date unavailable";
                    }
                    header.append(sender, date);

                    const subject = document.createElement("h3");
                    subject.className = "inquiry-subject";
                    subject.textContent = inquiry.subject || "No subject";
                    const message = document.createElement("p");
                    message.className = "inquiry-message";
                    message.textContent = inquiry.message || "";

                    const footer = document.createElement("div");
                    footer.className = "inquiry-item-footer";
                    const badge = document.createElement("span");
                    const isResolved = inquiry.status === "resolved";
                    badge.className = `inquiry-status${isResolved ? " resolved" : ""}`;
                    badge.textContent = isResolved ? "Resolved" : "New";
                    const actions = document.createElement("div");
                    actions.className = "inquiry-actions";
                    const reply = document.createElement("button");
                    reply.type = "button";
                    reply.dataset.replyInquiryId = String(inquiry.id);
                    reply.textContent = "Reply to student";
                    reply.setAttribute("aria-label", `Reply to ${inquiry.name || inquiry.email}`);
                    const statusButton = document.createElement("button");
                    statusButton.type = "button";
                    statusButton.dataset.inquiryId = String(inquiry.id);
                    statusButton.dataset.nextStatus = isResolved ? "new" : "resolved";
                    statusButton.textContent = isResolved ? "Reopen" : "Mark resolved";
                    actions.append(reply, statusButton);
                    footer.append(badge, actions);

                    const replyForm = document.createElement("form");
                    replyForm.className = "inquiry-reply-form";
                    replyForm.dataset.inquiryReplyForm = String(inquiry.id);
                    replyForm.hidden = true;
                    const replyLabel = document.createElement("label");
                    replyLabel.textContent = `Email a reply to ${inquiry.email || "the student"}`;
                    const replyInput = document.createElement("textarea");
                    replyInput.name = "message";
                    replyInput.required = true;
                    replyInput.maxLength = 4000;
                    replyInput.rows = 4;
                    replyInput.placeholder = "Write your reply…";
                    replyLabel.append(replyInput);
                    const replyActions = document.createElement("div");
                    replyActions.className = "inquiry-reply-actions";
                    const cancelReply = document.createElement("button");
                    cancelReply.type = "button";
                    cancelReply.dataset.cancelInquiryReply = "true";
                    cancelReply.textContent = "Cancel";
                    const sendReply = document.createElement("button");
                    sendReply.type = "submit";
                    sendReply.textContent = "Send reply";
                    replyActions.append(cancelReply, sendReply);
                    replyForm.append(replyLabel, replyActions);

                    card.append(header, subject, message, footer, replyForm);
                    adminInquiriesList.append(card);
                });
            }
            setInquiriesFeedback(`${data.total ?? inquiries.length} message${(data.total ?? inquiries.length) === 1 ? "" : "s"} in the inbox.`);
        } catch (error) {
            setInquiriesFeedback(error.message || "Unable to load the inbox. Please retry.", "error");
            adminInquiriesList.replaceChildren();
            const empty = document.createElement("div");
            empty.className = "inquiries-empty";
            empty.textContent = "The inbox could not be loaded. Use Refresh inbox to try again.";
            adminInquiriesList.append(empty);
        }
    }

    if (adminInquiriesList) {
        adminInquiriesList.addEventListener("click", async event => {
            const replyButton = event.target.closest("button[data-reply-inquiry-id]");
            if (replyButton) {
                const form = adminInquiriesList.querySelector(
                    `form[data-inquiry-reply-form="${CSS.escape(replyButton.dataset.replyInquiryId)}"]`
                );
                if (form) {
                    form.hidden = !form.hidden;
                    if (!form.hidden) form.querySelector("textarea")?.focus();
                }
                return;
            }

            const cancelButton = event.target.closest("button[data-cancel-inquiry-reply]");
            if (cancelButton) {
                const form = cancelButton.closest("form");
                if (form) {
                    form.reset();
                    form.hidden = true;
                }
                return;
            }

            const button = event.target.closest("button[data-inquiry-id]");
            if (!button) return;
            button.disabled = true;
            setInquiriesFeedback("Updating message…");
            try {
                const adminToken = localStorage.getItem("admin_access_token");
                const response = await fetch(
                    `${API_BASE_URL}/admin/inquiries/${encodeURIComponent(button.dataset.inquiryId)}/status`,
                    {
                        method: "PATCH",
                        headers: {
                            Authorization: `Bearer ${adminToken}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ status: button.dataset.nextStatus })
                    }
                );
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(data.detail || "Unable to update this message.");
                await loadAdminInquiries();
            } catch (error) {
                button.disabled = false;
                setInquiriesFeedback(error.message || "Unable to update this message.", "error");
            }
        });

        adminInquiriesList.addEventListener("submit", async event => {
            const form = event.target.closest("form[data-inquiry-reply-form]");
            if (!form) return;
            event.preventDefault();

            const textarea = form.elements.message;
            const sendButton = form.querySelector('button[type="submit"]');
            const reply = textarea.value.trim();
            if (!reply) {
                textarea.focus();
                setInquiriesFeedback("Write a reply before sending.", "error");
                return;
            }

            sendButton.disabled = true;
            sendButton.textContent = "Sending…";
            setInquiriesFeedback("Sending reply to the student…");
            try {
                const adminToken = localStorage.getItem("admin_access_token");
                const response = await fetch(
                    `${API_BASE_URL}/admin/inquiries/${encodeURIComponent(form.dataset.inquiryReplyForm)}/reply`,
                    {
                        method: "POST",
                        headers: {
                            Authorization: `Bearer ${adminToken}`,
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ message: reply })
                    }
                );
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(data.detail || "The reply could not be sent.");
                await loadAdminInquiries();
                setInquiriesFeedback(data.message || "Reply sent to the student.", "success");
            } catch (error) {
                setInquiriesFeedback(error.message || "The reply could not be sent.", "error");
            } finally {
                sendButton.disabled = false;
                sendButton.textContent = "Send reply";
            }
        });
    }

    const refreshInquiriesButton = document.getElementById("refreshInquiries");
    if (refreshInquiriesButton) refreshInquiriesButton.addEventListener("click", loadAdminInquiries);


    /* =====================================================
       DASHBOARD STATISTICS
       
       IMPORTANT:
       Total Users means ONLY registered students.
       
       Admin accounts are NOT included.
       
       Backend currently returns:
       
       total_students
       total_admins
       total_exams
       total_questions
       total_attempts
    ===================================================== */

    function updateDashboardStats(data) {

        data = data || {};

        console.log(
            "Updating dashboard statistics:",
            data
        );


        /* =================================================
           TOTAL STUDENTS
           
           Only students are counted as users.
           total_admins is intentionally NOT included.
        ================================================= */

        const studentCount =
            Number(
                data.total_students ?? 0
            );


        /* =================================================
           TOTAL USERS
           
           Dashboard Total Users = STUDENTS ONLY
        ================================================= */

        if (totalUsers) {

            totalUsers.textContent =
                studentCount;

        }


        /* =================================================
           USERS GROWTH
           
           Current backend does not provide a growth value,
           so use 0%.
        ================================================= */

        if (usersGrowth) {

            usersGrowth.textContent =
                `↑ ${data.usersGrowth ?? data.users_growth ?? 0}%`;

        }


        /* =================================================
           TOTAL QUIZZES
           
           Backend field:
           total_exams
           
           Frontend card:
           Total Quizzes
        ================================================= */

        if (totalQuizzes) {

            totalQuizzes.textContent =
                Number(
                    data.total_exams ??
                    data.totalQuizzes ??
                    0
                );

        }


        /* =================================================
           QUIZZES GROWTH
        ================================================= */

        if (quizzesGrowth) {

            quizzesGrowth.textContent =
                `↑ ${
                    data.quizzesGrowth ??
                    data.quizzes_growth ??
                    0
                }%`;

        }


        /* =================================================
           TOTAL QUESTIONS
        ================================================= */

        if (totalQuestions) {

            totalQuestions.textContent =
                Number(
                    data.total_questions ??
                    data.totalQuestions ??
                    0
                );

        }


        /* =================================================
           QUESTIONS GROWTH
        ================================================= */

        if (questionsGrowth) {

            questionsGrowth.textContent =
                `↑ ${
                    data.questionsGrowth ??
                    data.questions_growth ??
                    0
                }%`;

        }


        /* =================================================
           TOTAL ATTEMPTS
        ================================================= */

        if (totalAttempts) {

            totalAttempts.textContent =
                Number(
                    data.total_attempts ??
                    data.totalAttempts ??
                    0
                );

        }


        /* =================================================
           ATTEMPTS GROWTH
        ================================================= */

        if (attemptsGrowth) {

            attemptsGrowth.textContent =
                `↑ ${
                    data.attemptsGrowth ??
                    data.attempts_growth ??
                    0
                }%`;

        }


        /* =================================================
           DEBUG
        ================================================= */

        console.log(
            "Dashboard values updated:",
            {
                totalStudents: studentCount,

                totalAdmins:
                    Number(
                        data.total_admins ?? 0
                    ),

                totalExams:
                    Number(
                        data.total_exams ??
                        data.totalQuizzes ??
                        0
                    ),

                totalQuestions:
                    Number(
                        data.total_questions ??
                        data.totalQuestions ??
                        0
                    ),

                totalAttempts:
                    Number(
                        data.total_attempts ??
                        data.totalAttempts ??
                        0
                    )
            }
        );

    }


    /* =====================================================
       LOAD DASHBOARD STATISTICS FROM BACKEND
    ===================================================== */

    async function loadDashboardStats() {

        try {

            const adminToken =
                localStorage.getItem(
                    "admin_access_token"
                );


            if (!adminToken) {

                console.error(
                    "Admin access token not found."
                );

                return;

            }


            const response =
                await fetch(
                    `${API_BASE_URL}/admin/dashboard`,
                    {
                        method: "GET",

                        headers: {
                            "Authorization":
                                `Bearer ${adminToken}`,

                            "Content-Type":
                                "application/json"
                        }
                    }
                );


            if (!response.ok) {

                throw new Error(
                    `Failed to load dashboard statistics: ${response.status}`
                );

            }


            const data =
                await response.json();


            console.log(
                "Dashboard statistics:",
                data
            );


            updateDashboardStats(
                data
            );


        } catch (error) {

            console.error(
                "Error loading dashboard statistics:",
                error
            );

        }

    }


    /* =====================================================
       RESULTS
    ===================================================== */

    function updateResults(data) {

        data = data || {};


        if (averageScore) {

            averageScore.textContent =
                `${data.averageScore ?? 0}%`;

        }


        if (passRate) {

            passRate.textContent =
                `${data.passRate ?? 0}%`;

        }


        if (todayAttempts) {

            todayAttempts.textContent =
                data.todayAttempts ?? 0;

        }


        const totalResultAttempts =
            document.getElementById(
                "totalResultAttempts"
            );


        if (totalResultAttempts) {

            totalResultAttempts.textContent =
                data.totalAttempts ?? 0;

        }

    }


/* =========================================================
   ADMIN RESULTS
   LOAD REAL RESULTS FROM BACKEND
========================================================= */

let currentAdminResults = [];


/* =========================================================
   RESULT TABLE ELEMENTS
========================================================= */

const resultsTableBody =
    document.getElementById(
        "resultsTableBody"
    );

const resultSearch =
    document.getElementById(
        "resultSearch"
    );

const resultQuizFilter =
    document.getElementById(
        "resultQuizFilter"
    );

const resultStatusFilter =
    document.getElementById(
        "resultStatusFilter"
    );


/* =========================================================
   PASS MARK
========================================================= */

/*
 * Your existing student result page uses
 * 40% as the default passing percentage.
 *
 * Change this to another value later if
 * your institute uses a different pass mark.
 */

const ADMIN_PASS_MARK = 40;


/* =========================================================
   LOAD ADMIN RESULTS
========================================================= */

async function loadAdminResults() {

    console.log(
        "================================="
    );

    console.log(
        "LOADING ADMIN RESULTS"
    );

    console.log(
        "================================="
    );


    const accessToken =
        localStorage.getItem(
            "admin_access_token"
        );


    if (!accessToken) {

        console.error(
            "No admin access token found."
        );

        return;
    }


    /*
     * The existing Admin Results backend
     * route is /admin/attempts.
     */

    const url =
        `${API_BASE_URL}/admin/attempts`;


    console.log(
        "Admin Results URL:",
        url
    );


    try {

        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    headers: {

                        "Authorization":
                            `Bearer ${accessToken}`,

                        "Accept":
                            "application/json"
                    }
                }
            );


        console.log(
            "Admin Results Status:",
            response.status
        );


        if (!response.ok) {

            const errorText =
                await response.text();


            console.error(
                "Admin Results API Error:",
                errorText
            );


            throw new Error(
                `Results API returned ${response.status}`
            );
        }

        const data =
    await response.json();

console.log(
    "ADMIN RESULTS DATA:",
    data
);

console.log(
    "ADMIN RESULTS IS ARRAY:",
    Array.isArray(data)
);

console.log(
    "ADMIN RESULTS COUNT:",
    Array.isArray(data)
        ? data.length
        : "NOT AN ARRAY"
);


        /*
         * Backend returns a list of attempts.
         */

        currentAdminResults =
            Array.isArray(data)
                ? data
                : (
                    Array.isArray(data.results)
                        ? data.results
                        : (
                            Array.isArray(data.attempts)
                                ? data.attempts
                                : []
                        )
                );


        console.log(
            "Parsed Admin Results:",
            currentAdminResults
        );


        /*
         * Update statistics.
         */

        updateAdminResultStatistics(
            currentAdminResults
        );


        /*
         * Fill quiz filter.
         */

        populateResultQuizFilter(
            currentAdminResults
        );


        /*
         * Render table.
         */

        renderAdminResultsTable(
            currentAdminResults
        );


    } catch (error) {

        console.error(
            "Failed to load admin results:",
            error
        );


        if (resultsTableBody) {

            resultsTableBody.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="empty-table"
                    >
                        Unable to load results.
                    </td>
                </tr>
            `;

        }

    }

}


/* =========================================================
   GET RESULT OBJECT
========================================================= */

function getResultObject(
    attempt
) {

    return (
        attempt.result ||
        attempt.results ||
        null
    );

}


/* =========================================================
   GET PERCENTAGE
========================================================= */

function getResultPercentage(
    attempt
) {

    const result =
        getResultObject(
            attempt
        );


    if (!result) {

        return null;

    }


    const value =
        result.percentage ??
        result.score_percentage ??
        result.percent;


    if (
        value === undefined ||
        value === null
    ) {

        return null;

    }


    const percentage =
        Number(value);


    return Number.isFinite(
        percentage
    )
        ? percentage
        : null;

}


/* =========================================================
   GET SCORE
========================================================= */

function getResultScore(
    attempt
) {

    const result =
        getResultObject(
            attempt
        );


    if (!result) {

        return null;

    }


    const value =
        result.score ??
        result.total_score;


    if (
        value === undefined ||
        value === null
    ) {

        return null;

    }


    const score =
        Number(value);


    return Number.isFinite(
        score
    )
        ? score
        : null;

}


/* =========================================================
   GET RESULT STATUS
========================================================= */

function getAdminResultStatus(
    attempt
) {

    const percentage =
        getResultPercentage(
            attempt
        );


    /*
     * No result yet.
     */

    if (
        percentage === null
    ) {

        return "pending";

    }


    if (
        percentage >=
        ADMIN_PASS_MARK
    ) {

        return "passed";

    }


    return "failed";

}


/* =========================================================
   GET STUDENT NAME
========================================================= */

function getAttemptStudentName(
    attempt
) {

    const student =
        attempt.student ||
        {};


    return (
        student.name ||
        student.full_name ||
        student.fullName ||
        student.email ||
        `Student ${attempt.user_id ?? ""}`
    );

}


/* =========================================================
   GET QUIZ NAME
========================================================= */

function getAttemptQuizName(
    attempt
) {

    const exam =
        attempt.exam ||
        {};


    return (
        exam.title ||
        exam.name ||
        `Exam ${attempt.exam_id ?? ""}`
    );

}


/* =========================================================
   GET DATE
========================================================= */

function getAttemptDate(
    attempt
) {

    const date =
        attempt.submitted_at ||
        attempt.created_at ||
        attempt.started_at;


    if (!date) {

        return "—";

    }


    const parsed =
        new Date(date);


    if (
        Number.isNaN(
            parsed.getTime()
        )
    ) {

        return "—";

    }


    return parsed.toLocaleDateString();

}


/* =========================================================
   UPDATE RESULT STATISTICS
========================================================= */

function updateAdminResultStatistics(
    attempts
) {

    const totalAttempts =
        attempts.length;


    /*
     * Only attempts with an actual result
     * should be included in score statistics.
     */

    const completedAttempts =
        attempts.filter(
            attempt =>
                getResultPercentage(
                    attempt
                ) !== null
        );


    const percentages =
        completedAttempts
            .map(
                attempt =>
                    getResultPercentage(
                        attempt
                    )
            )
            .filter(
                value =>
                    value !== null
            );


    /*
     * Average percentage.
     */

    let average =
        0;


    if (
        percentages.length > 0
    ) {

        const sum =
            percentages.reduce(
                (
                    total,
                    value
                ) =>
                    total + value,
                0
            );


        average =
            sum /
            percentages.length;

    }


    /*
     * Passed attempts.
     */

    const passedAttempts =
        completedAttempts.filter(
            attempt =>
                getAdminResultStatus(
                    attempt
                ) === "passed"
        ).length;


    /*
     * Pass rate.
     */

    let passRateValue =
        0;


    if (
        completedAttempts.length > 0
    ) {

        passRateValue =
            (
                passedAttempts /
                completedAttempts.length
            ) * 100;

    }


    /*
     * Today's attempts.
     */

    const today =
        new Date();


    const todayYear =
        today.getFullYear();


    const todayMonth =
        today.getMonth();


    const todayDate =
        today.getDate();


    const todayAttemptsCount =
        attempts.filter(
            attempt => {

                const dateValue =
                    attempt.submitted_at ||
                    attempt.created_at ||
                    attempt.started_at;


                if (!dateValue) {

                    return false;

                }


                const date =
                    new Date(
                        dateValue
                    );


                return (
                    date.getFullYear() ===
                        todayYear &&

                    date.getMonth() ===
                        todayMonth &&

                    date.getDate() ===
                        todayDate
                );

            }
        ).length;


    /*
     * Update cards.
     */

    const totalResultAttempts =
        document.getElementById(
            "totalResultAttempts"
        );


    if (
        totalResultAttempts
    ) {

        totalResultAttempts.textContent =
            totalAttempts;

    }


    if (averageScore) {

        averageScore.textContent =
            percentages.length > 0
                ? `${average.toFixed(2)}%`
                : "—";

    }


    if (passRate) {

        passRate.textContent =
            completedAttempts.length > 0
                ? `${passRateValue.toFixed(2)}%`
                : "—";

    }


    if (todayAttempts) {

        todayAttempts.textContent =
            todayAttemptsCount;

    }


    console.log(
        "RESULT STATISTICS:",
        {
            totalAttempts,
            completedAttempts:
                completedAttempts.length,
            averageScore:
                average,
            passRate:
                passRateValue,
            todayAttempts:
                todayAttemptsCount
        }
    );

}


/* =========================================================
   POPULATE QUIZ FILTER
========================================================= */

function populateResultQuizFilter(
    attempts
) {

    if (
        !resultQuizFilter
    ) {

        return;

    }


    /*
     * Keep the first "All Quizzes"
     * option.
     */

    resultQuizFilter.innerHTML = `
        <option value="all">
            All Quizzes
        </option>
    `;


    const quizMap =
        new Map();


    attempts.forEach(
        attempt => {

            const exam =
                attempt.exam ||
                {};


            const examId =
                exam.id ??
                attempt.exam_id;


            const examTitle =
                exam.title ||
                exam.name ||
                `Exam ${examId}`;


            if (
                examId !== undefined &&
                examId !== null
            ) {

                quizMap.set(
                    String(examId),
                    examTitle
                );

            }

        }
    );


    quizMap.forEach(
        (
            title,
            id
        ) => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                id;


            option.textContent =
                title;


            resultQuizFilter.appendChild(
                option
            );

        }
    );

}


/* =========================================================
   FILTER RESULTS
========================================================= */

function getFilteredAdminResults() {

    const search =
        resultSearch
            ? resultSearch.value
                .trim()
                .toLowerCase()
            : "";


    const quizFilter =
        resultQuizFilter
            ? resultQuizFilter.value
            : "all";


    const statusFilter =
        resultStatusFilter
            ? resultStatusFilter.value
            : "all";


    return currentAdminResults.filter(
        attempt => {

            const studentName =
                getAttemptStudentName(
                    attempt
                ).toLowerCase();


            const quizName =
                getAttemptQuizName(
                    attempt
                ).toLowerCase();


            /*
             * Search.
             */

            if (
                search &&
                !studentName.includes(
                    search
                ) &&
                !quizName.includes(
                    search
                )
            ) {

                return false;

            }


            /*
             * Quiz filter.
             */

            if (
                quizFilter !== "all"
            ) {

                const examId =
                    attempt.exam?.id ??
                    attempt.exam_id;


                if (
                    String(examId) !==
                    String(quizFilter)
                ) {

                    return false;

                }

            }


            /*
             * Status filter.
             */

            if (
                statusFilter !== "all"
            ) {

                const status =
                    getAdminResultStatus(
                        attempt
                    );


                if (
                    status !==
                    statusFilter
                ) {

                    return false;

                }

            }


            return true;

        }
    );

}


/* =========================================================
   RENDER RESULTS TABLE
========================================================= */

function renderAdminResultsTable(
    attempts
) {

    if (
        !resultsTableBody
    ) {

        return;

    }


    resultsTableBody.innerHTML =
        "";


    if (
        !attempts ||
        attempts.length === 0
    ) {

        resultsTableBody.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="empty-table"
                >
                    No quiz attempts found.
                </td>
            </tr>
        `;

        return;

    }


    attempts.forEach(
        attempt => {

            const row =
                document.createElement(
                    "tr"
                );


            const studentName =
                getAttemptStudentName(
                    attempt
                );


            const quizName =
                getAttemptQuizName(
                    attempt
                );


            const score =
                getResultScore(
                    attempt
                );


            const percentage =
                getResultPercentage(
                    attempt
                );


            const status =
                getAdminResultStatus(
                    attempt
                );


            let statusText =
                "Pending";


            if (
                status === "passed"
            ) {

                statusText =
                    "Passed";

            }

            else if (
                status === "failed"
            ) {

                statusText =
                    "Failed";

            }


            const scoreText =
                score !== null
                    ? score.toFixed(2)
                    : "—";


            const percentageText =
                percentage !== null
                    ? `${percentage.toFixed(2)}%`
                    : "—";


            const statusClass =
                status === "passed"
                    ? "active-status"
                    : (
                        status === "failed"
                            ? "inactive-status"
                            : ""
                    );


            const dateText =
                getAttemptDate(
                    attempt
                );


            row.innerHTML = `

                <td>

                    <div class="table-user">

                        <div class="table-avatar">
                            ${escapeAdminHtml(
                                studentName
                                    .charAt(0)
                                    .toUpperCase()
                            )}
                        </div>

                        ${escapeAdminHtml(
                            studentName
                        )}

                    </div>

                </td>


                <td>
                    ${escapeAdminHtml(
                        quizName
                    )}
                </td>


                <td>
                    ${scoreText}
                </td>


                <td>
                    ${percentageText}
                </td>


                <td>

                    <span
                        class="status ${statusClass}"
                    >
                        ${statusText}
                    </span>

                </td>


                <td>
                    ${dateText}
                </td>


                <td>

                    <div class="table-actions">

                        <button
                            type="button"
                            class="table-action view-result-btn"
                            data-attempt-id="${escapeAdminHtml(attempt.attempt_id ?? attempt.id)}"
                        >
                            View
                        </button>

                    </div>

                </td>

            `;


            resultsTableBody.appendChild(
                row
            );

        }
    );

}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeAdminHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


/* =========================================================
   RESULT FILTER EVENTS
========================================================= */

if (
    resultSearch
) {

    resultSearch.addEventListener(
        "input",
        function () {

            renderAdminResultsTable(
                getFilteredAdminResults()
            );

        }
    );

}


if (
    resultQuizFilter
) {

    resultQuizFilter.addEventListener(
        "change",
        function () {

            renderAdminResultsTable(
                getFilteredAdminResults()
            );

        }
    );

}


if (
    resultStatusFilter
) {

    resultStatusFilter.addEventListener(
        "change",
        function () {

            renderAdminResultsTable(
                getFilteredAdminResults()
            );

        }
    );

}


/* =========================================================
   VIEW RESULT
========================================================= */

if (
    resultsTableBody
) {

    resultsTableBody.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    ".view-result-btn"
                );


            if (!button) {

                return;

            }


            const attemptId =
                button.dataset.attemptId;


            if (!attemptId) {

                return;

            }


            console.log(
                "Selected attempt:",
                attemptId
            );


            /* =================================================
               FIND THE SELECTED RESULT
            ================================================= */

            const attempt =
                currentAdminResults.find(
                    item =>
                        String(
                            item.attempt_id ??
                            item.id
                        ) ===
                        String(attemptId)
                );


            if (!attempt) {

                console.error(
                    "Result not found for attempt:",
                    attemptId
                );

                return;

            }


            /* =================================================
               GET RESULT DATA
            ================================================= */

            const result =
                attempt.result ||
                attempt.results ||
                null;


            const studentName =
                getAttemptStudentName(
                    attempt
                );


            const quizName =
                getAttemptQuizName(
                    attempt
                );


            const score =
                getResultScore(
                    attempt
                );


            const percentage =
                getResultPercentage(
                    attempt
                );


            const status =
                getAdminResultStatus(
                    attempt
                );


            const submittedDate =
                getAttemptDate(
                    attempt
                );


            /* =================================================
               GET MODAL
            ================================================= */

            const modal =
                document.getElementById(
                    "viewResultModal"
                );


            if (!modal) {

                console.error(
                    "View Result modal not found."
                );

                return;

            }


            /* =================================================
               FILL MODAL
            ================================================= */

            const studentElement =
                document.getElementById(
                    "resultStudent"
                );


            const quizElement =
                document.getElementById(
                    "resultQuiz"
                );


            const scoreElement =
                document.getElementById(
                    "resultScore"
                );


            const percentageElement =
                document.getElementById(
                    "resultPercentage"
                );


            const statusElement =
                document.getElementById(
                    "resultStatus"
                );


            const dateElement =
                document.getElementById(
                    "resultDate"
                );


            if (studentElement) {

                studentElement.textContent =
                    studentName;

            }


            if (quizElement) {

                quizElement.textContent =
                    quizName;

            }


            if (scoreElement) {

                scoreElement.textContent =
                    score !== null
                        ? score.toFixed(2)
                        : "—";

            }


            if (percentageElement) {

                percentageElement.textContent =
                    percentage !== null
                        ? `${percentage.toFixed(2)}%`
                        : "—";

            }


            if (statusElement) {

                if (status === "passed") {

                    statusElement.textContent =
                        "Passed";

                }

                else if (status === "failed") {

                    statusElement.textContent =
                        "Failed";

                }

                else {

                    statusElement.textContent =
                        "Pending";

                }

            }


            if (dateElement) {

                dateElement.textContent =
                    submittedDate;

            }


            /* =================================================
               SHOW MODAL
            ================================================= */

            modal.classList.add(
                "active"
            );

            modal.classList.remove(
                "hidden"
            );


            console.log(
                "View Result modal opened:",
                attempt
            );

        }
    );

}


/* =========================================================
   CLOSE VIEW RESULT MODAL
========================================================= */

const viewResultModal =
    document.getElementById(
        "viewResultModal"
    );


const closeViewResultModal =
    document.getElementById(
        "closeViewResultModal"
    );


const closeViewResult =
    document.getElementById(
        "closeViewResult"
    );


function closeAdminResultModal() {

    if (!viewResultModal) {

        return;

    }


    viewResultModal.classList.remove(
        "active"
    );

    viewResultModal.classList.add(
        "hidden"
    );

}


if (closeViewResultModal) {

    closeViewResultModal.addEventListener(
        "click",
        function () {

            closeAdminResultModal();

        }
    );

}


if (closeViewResult) {

    closeViewResult.addEventListener(
        "click",
        function () {

            closeAdminResultModal();

        }
    );

}


/* =========================================================
   CLOSE MODAL WHEN CLICKING OUTSIDE
========================================================= */

if (viewResultModal) {

    viewResultModal.addEventListener(
        "click",
        function (event) {

            if (
                event.target ===
                viewResultModal
            ) {

                closeAdminResultModal();

            }

        }
    );

}

    /* =====================================================
       ADMIN AVATAR HELPER
    ===================================================== */

    function setAdminAvatar(
        element,
        imageUrl,
        name
    ) {

        if (!element) {
            return;
        }


        /*
         * If profile picture exists,
         * display it.
         */

        if (imageUrl) {

            element.textContent = "";

            element.style.backgroundImage =
                `url("${imageUrl}")`;

            element.style.backgroundSize =
                "cover";

            element.style.backgroundPosition =
                "center";

            element.style.backgroundRepeat =
                "no-repeat";

            return;
        }


        /*
         * No profile picture.
         *
         * Show first letter of the
         * actual admin name.
         */

        element.style.backgroundImage =
            "none";


        const firstLetter =
            name
                ? name.charAt(0).toUpperCase()
                : "";


        element.textContent =
            firstLetter;

    }


    /* =====================================================
       UPDATE ADMIN PROFILE
    ===================================================== */

    function updateAdminProfile(data) {

        data = data || {};


        const name =
            data.name || "";


        const role =
            String(
                data.role || "ADMIN"
            ).toUpperCase();


        const email =
            data.email || "";


        /*
         * Profile picture is stored temporarily
         * in localStorage.
         */

        const savedProfilePicture =
            localStorage.getItem(
                "adminProfilePicture"
            ) || "";


        /* =================================================
           SIDEBAR ADMIN NAME
        ================================================= */

        if (sidebarAdminName) {

            sidebarAdminName.textContent =
                name;

        }


        /* =================================================
           SIDEBAR ADMIN ROLE
        ================================================= */

        if (sidebarAdminRole) {

            sidebarAdminRole.textContent =
                role;

        }


        /* =================================================
           SIDEBAR ADMIN AVATAR
        ================================================= */

        setAdminAvatar(
            sidebarAdminAvatar,
            savedProfilePicture,
            name
        );


        /* =================================================
           TOP ADMIN NAME
        ================================================= */

        if (topAdminName) {

            topAdminName.textContent =
                name;

        }


        /* =================================================
           TOP ADMIN ROLE
        ================================================= */

        if (topAdminRole) {

            topAdminRole.textContent =
                role;

        }


        /* =================================================
           TOP ADMIN AVATAR
        ================================================= */

        setAdminAvatar(
            topAdminAvatar,
            savedProfilePicture,
            name
        );


        /* =================================================
           WELCOME MESSAGE
        ================================================= */

        if (welcomeAdminName) {

            welcomeAdminName.textContent =
                name;

        }


        /* =================================================
           SETTINGS NAME
        ================================================= */

        if (settingsAdminName) {

            settingsAdminName.value =
                name;

        }


        /* =================================================
           SETTINGS EMAIL
        ================================================= */

        if (settingsAdminEmail) {

            settingsAdminEmail.value =
                email;

        }


        console.log(
            "Admin profile displayed:",
            {
                name: name,
                email: email,
                role: role
            }
        );

    }


    /* =====================================================
       LOAD LOGGED-IN ADMIN
       
       IMPORTANT:
       This function uses ONLY admin_user.
       
       It DOES NOT use:
       localStorage.access_token
       
       This prevents the student token from being
       accidentally displayed in the Admin Dashboard.
    ===================================================== */

    function loadLoggedInAdmin() {

    console.log("Loading logged-in admin...");

    const adminToken =
        localStorage.getItem("admin_access_token");

    if (!adminToken) {

        console.error(
            "No admin_access_token found."
        );

        window.location.href =
            "ad-login.html";

        return;

    }


    /*
     * IMPORTANT:
     *
     * Do NOT trust admin_user from localStorage
     * for authentication or authorization.
     *
     * The admin-only endpoint verifies the account
     * and role before populating the dashboard.
     */

    fetch(
        `${API_BASE_URL}/auth/admin/profile`,
        {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${adminToken}`,

                "Content-Type":
                    "application/json"
            }
        }
    )
    .then(async response => {

        let data = {};

        try {
            data = await response.json();
        } catch {
            data = {};
        }


        /*
         * Token is invalid or expired.
         */

        if (response.status === 401) {

            throw new Error(
                "ADMIN_SESSION_EXPIRED"
            );

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Unable to load admin profile."
            );

        }


        return data;

    })
    .then(admin => {

        console.log(
            "Authenticated account from backend:",
            admin
        );


        /*
         * SECURITY CHECK
         *
         * Only ADMIN accounts are allowed
         * to use the admin dashboard.
         */

        const role =
            String(
                admin.role || ""
            ).toUpperCase();


        if (role !== "ADMIN") {

            console.error(
                "Unauthorized account detected:",
                admin
            );


            localStorage.removeItem(
                "admin_access_token"
            );

            localStorage.removeItem(
                "admin_user"
            );


            alert(
                "Unauthorized account. Please login as an administrator."
            );


            window.location.href =
                "ad-login.html";


            return;

        }


        /*
         * Save the verified backend admin data.
         *
         * This keeps admin_user synchronized with
         * the actual authenticated account.
         */

        localStorage.setItem(
            "admin_user",
            JSON.stringify({
                id:
                    admin.id,

                name:
                    admin.name || "",

                email:
                    admin.email || "",

                role:
                    role
            })
        );


        /*
         * Display verified admin information.
         */

        updateAdminProfile({

            id:
                admin.id,

            name:
                admin.name || "",

            email:
                admin.email || "",

            role:
                role

        });

    })
    .catch(error => {

        console.error(
            "Admin authentication error:",
            error
        );


        /*
         * Invalid / expired admin token.
         */

        if (
            error.message ===
            "ADMIN_SESSION_EXPIRED"
        ) {

            localStorage.removeItem(
                "admin_access_token"
            );

            localStorage.removeItem(
                "admin_user"
            );


            alert(
                "Your admin session has expired. Please login again."
            );


            window.location.href =
                "ad-login.html";


            return;

        }


        /*
         * Other authentication/profile errors.
         */

        alert(
            error.message ||
            "Unable to verify admin session."
        );

    });

}


    /* =====================================================
       UPDATE USERS TABLE
    ===================================================== */

    function updateUsersTable(users) {

        currentUsers =
            Array.isArray(users)
                ? users
                : [];


        if (!usersTable) {
            return;
        }


        usersTable.innerHTML = "";


        if (
            !users ||
            users.length === 0
        ) {

            usersTable.innerHTML = `
                <tr>
                    <td colspan="5">
                        <div class="empty-users">

                            <div class="empty-users-icon">
                                👥
                            </div>

                            <h3>
                                No users found
                            </h3>

                            <p>
                                There are currently no registered
                                users on the platform.
                            </p>

                        </div>
                    </td>
                </tr>
            `;

            return;

        }


        users.forEach(user => {

            const row =
                document.createElement("tr");


            const name =
                user.name || "Unknown";


            const email =
                user.email || "-";


            const status =
                user.status || "Active";


            const joined =
                user.created_at
                    ? new Date(
                        user.created_at
                    ).toLocaleDateString()
                    : "-";


            row.innerHTML = `

                <td>

                    <div class="table-user">

                        <div class="table-avatar">

                                ${escapeAdminHtml(name
                                .charAt(0)
                                .toUpperCase())}

                        </div>

                        ${escapeAdminHtml(name)}

                    </div>

                </td>


                <td>
                    ${escapeAdminHtml(email)}
                </td>


                <td>

                    <span
                        class="status ${escapeAdminHtml(status.toLowerCase())}-status"
                    >
                        ${escapeAdminHtml(status)}
                    </span>

                </td>


                <td>
                    ${joined}
                </td>


                <td>

                    <div class="table-actions">

                        <button
                            class="table-action view-user-btn"
                            data-user-id="${escapeAdminHtml(user.id)}">
                            View
                        </button>

                        <button
                            type="button"
                            class="table-action student-results-btn"
                            data-user-id="${escapeAdminHtml(user.id)}">
                            Results
                        </button>

                        <button
                            class="table-action edit-user-btn"
                            data-user-id="${escapeAdminHtml(user.id)}">
                            Edit
                        </button>

                        <button
                        class="table-action access-user-btn"
                        data-user-id="${escapeAdminHtml(user.id)}">
                        Access
                        </button>

                    </div>

                </td>

            `;


            usersTable.appendChild(row);

        });

    }


    updateUsersTable([]);


    /* =====================================================
       LOAD REGISTERED STUDENTS FROM BACKEND
       
       The Users section is intended to display students.
       
       The dashboard count itself is separately calculated
       from total_students.
    ===================================================== */

    async function loadUsers() {

        try {

            const adminToken =
                localStorage.getItem(
                    "admin_access_token"
                );


            if (!adminToken) {

                console.error(
                    "Admin access token not found."
                );

                return;

            }


            const users = [];
            const pageSize = 500;
            let offset = 0;

            while (true) {
                const response = await fetch(
                    `${API_BASE_URL}/admin/users?limit=${pageSize}&offset=${offset}`,
                    {
                        method: "GET",
                        headers: {
                            "Authorization": `Bearer ${adminToken}`,
                            "Content-Type": "application/json"
                        }
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `Failed to load users: ${response.status}`
                    );
                }

                const page = await response.json();
                if (!Array.isArray(page)) {
                    throw new Error("The users API returned an invalid response.");
                }

                users.push(...page);
                if (page.length < pageSize) {
                    break;
                }
                offset += page.length;
            }


            console.log(
                "Registered users loaded:",
                users
            );


            /*
             * Keep only student accounts in the
             * Admin Users table if the backend
             * returns both students and admins.
             */

            const students =
                Array.isArray(users)
                    ? users.filter(user => {

                        const role =
                            String(
                                user.role || "STUDENT"
                            ).toUpperCase();

                        return role === "STUDENT";

                    })
                    : [];


            updateUsersTable(
                students
            );


        } catch (error) {

            console.error(
                "Error loading registered users:",
                error
            );


            updateUsersTable([]);

        }

    }


    /* =====================================================
       LOAD USERS WHEN ADMIN DASHBOARD OPENS
    ===================================================== */

    loadUsers();


    /* =====================================================
       UPDATE QUIZZES TABLE
    ===================================================== */

    function updateQuizzesTable(quizzes) {

        if (!quizzesTable) {
            return;
        }


        quizzesTable.innerHTML = "";


        if (
            !quizzes ||
            quizzes.length === 0
        ) {

            quizzesTable.innerHTML = `

                <tr>

                    <td
                        colspan="5"
                        class="empty-table"
                    >
                        No quizzes found.
                    </td>

                </tr>

            `;

            return;

        }


        quizzes.forEach(quiz => {

            const row =
                document.createElement("tr");


            const title =
                quiz.title ||
                "Untitled Quiz";


            const questionsCount =
                quiz.questions_count ??
                quiz.question_count ??
                quiz.total_questions ??
                quiz.questions?.length ??
                0;

            const setNumber =
                quiz.set_number ??
                quiz.setNumber ??
                quiz.exam_set?.set_number ??
                quiz.set?.set_number ??
                (Array.isArray(quiz.sets) && quiz.sets.length > 0
                    ? quiz.sets[0].set_number
                    : null);

            const matchingSet =
                Array.isArray(quiz.sets)
                    ? quiz.sets.find(set =>
                        String(set.set_number) === String(setNumber)
                    ) || quiz.sets[0]
                    : null;

            const setId =
                quiz.set_id ??
                quiz.exam_set_id ??
                quiz.exam_set?.id ??
                quiz.set?.id ??
                matchingSet?.id ??
                "";


            const status =
                String(
                quiz.status ||
                "Draft"
                );


            const created =
                quiz.created_at
                    ? new Date(
                        quiz.created_at
                    ).toLocaleDateString()
                    : "-";


            row.innerHTML = `

    <td>
        ${escapeAdminHtml(title)}
    </td>

    <td>
        ${
            setNumber !== null &&
            setNumber !== undefined
                ? `Set ${String(setNumber).padStart(2, "0")}`
                : "—"
        }
    </td>

    <td>
        ${questionsCount}
    </td>

    <td>

        <span
            class="status ${escapeAdminHtml(status.toLowerCase())}-status"
        >
            ${escapeAdminHtml(status)}
        </span>

    </td>

    <td>
        ${created}
    </td>

    <td>

        <div class="table-actions">

            <button
                class="table-action view-quiz-btn"
                data-quiz-id="${escapeAdminHtml(quiz.id)}">
                View
            </button>

            <button
                class="table-action edit-quiz-btn"
                data-quiz-id="${escapeAdminHtml(quiz.id)}"
                data-set-id="${escapeAdminHtml(setId)}"
                data-set-number="${escapeAdminHtml(setNumber ?? "")}">
                Edit
            </button>

            <button
                class="table-action delete-quiz-btn"
                data-quiz-id="${escapeAdminHtml(quiz.id)}">
                Delete
            </button>

        </div>

    </td>

`;

            quizzesTable.appendChild(row);

        });

    }


    /* =====================================================
       LOAD PUBLISHED QUIZZES
    ===================================================== */


    async function loadPublishedQuizzes() {

    try {

        const adminToken =
            localStorage.getItem(
                "admin_access_token"
            );


        if (!adminToken) {

            console.error(
                "Admin access token not found."
            );

            updateQuizzesTable([]);

            return;

        }


        const response =
            await fetch(
                `${API_BASE_URL}/admin/exams`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${adminToken}`,

                        "Content-Type":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                `Failed to load quizzes: ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Quizzes loaded from backend:",
            data
        );


        const quizzes =
            Array.isArray(data)
                ? data
                : Array.isArray(data.exams)
                    ? data.exams
                    : [];


        updateQuizzesTable(
            quizzes
        );


    } catch (error) {

        console.error(
            "Error loading quizzes from backend:",
            error
        );


        updateQuizzesTable([]);

    }

}


loadPublishedQuizzes();
loadAdminResults();

    /* =====================================================
   DELETE QUIZ
===================================================== */

document.addEventListener(
    "click",
    async function(event) {

        const deleteButton =
            event.target.closest(
                ".delete-quiz-btn"
            );

        if (!deleteButton) {
            return;
        }

        const quizId =
            deleteButton.dataset.quizId;

        if (!quizId) {
            return;
        }

        const token =
            localStorage.getItem(
                "admin_access_token"
            );

        if (!token) {
            window.location.href =
                "ad-login.html";
            return;
        }

        const confirmed =
            confirm(
                "Are you sure you want to delete this quiz?"
            );

        if (!confirmed) {
            return;
        }

        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/admin/exams/${quizId}`,
                    {
                        method: "DELETE",

                        headers: {
                            "Authorization":
                                `Bearer ${token}`
                        }
                    }
                );

            const data =
                await response.json()
                    .catch(() => ({}));


            if (
                response.status === 401 ||
                response.status === 403
            ) {

                localStorage.removeItem(
                    "admin_access_token"
                );

                localStorage.removeItem(
                    "admin_user"
                );

                window.location.href =
                    "ad-login.html";

                return;
            }


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Unable to delete quiz"
                );

            }


            alert(
                data.message ||
                "Quiz deleted successfully."
            );


            await loadPublishedQuizzes();

            await loadDashboardStats();


        } catch (error) {

            console.error(
                "Delete quiz error:",
                error
            );

            alert(
                error.message ||
                "Failed to delete quiz."
            );

        }

    }
);


    /* =====================================================
       VIEW QUIZ
    ===================================================== */

    document.addEventListener(
        "click",
        function(event) {

            const viewButton =
                event.target.closest(
                    ".view-quiz-btn"
                );


            if (!viewButton) {
                return;
            }


            const quizId =
                viewButton.dataset.quizId;


            if (!quizId) {
                return;
            }


            window.location.href =
                `admin-view-quiz.html?id=${encodeURIComponent(
                    quizId
                )}`;

        }
    );


    /* =====================================================
       EDIT QUIZ
    ===================================================== */

    document.addEventListener(
        "click",
        function(event) {

            const editButton =
                event.target.closest(
                    ".edit-quiz-btn"
                );


            if (!editButton) {
                return;
            }


            const quizId =
                editButton.dataset.quizId;

            const setId =
                editButton.dataset.setId;

            const setNumber =
                editButton.dataset.setNumber;


            if (!quizId) {
                return;
            }


            const editParams = new URLSearchParams({ edit: quizId });
            if (setId) editParams.set("set_id", setId);
            if (setNumber) editParams.set("set_number", setNumber);

            window.location.href =
                `admin-create-quiz.html?${editParams.toString()}`;

        }
    );




    /* =====================================================
       SIDEBAR NAVIGATION
    ===================================================== */

    navItems.forEach(item => {

        item.addEventListener(
            "click",
            event => {

                const sectionName =
                    item.dataset.section;


                /*
                 * Separate HTML pages do not have
                 * data-section.
                 */

                if (!sectionName) {
                    return;
                }


                event.preventDefault();


                navItems.forEach(nav => {

                    nav.classList.remove(
                        "active"
                    );

                });


                item.classList.add(
                    "active"
                );


                sections.forEach(section => {

                    section.classList.remove(
                        "active"
                    );

                });


                const selectedSection =
                    document.getElementById(
                        sectionName
                    );


                if (selectedSection) {

                    selectedSection.classList.add(
                        "active"
                    );

                }


                const pageMeta = {

                    dashboard: {

                        title:
                            "Dashboard",

                        subtitle:
                            "Overview of your EPS TOPIK platform"

                    },

                    users: {

                        title:
                            "Users",

                        subtitle:
                            "Manage platform users"

                    },

                    quizzes: {

                        title:
                            "Quizzes",

                        subtitle:
                            "Create and manage quizzes"

                    },

                    results: {

                        title:
                            "Results",

                        subtitle:
                            "View quiz results and performance"

                    },

                    payments: {

                        title:
                            "Payments",

                        subtitle:
                            "Manage and monitor payment activity"

                    },

                    inquiries: {

                        title:
                            "Student Inquiries",

                        subtitle:
                            "Read and respond to questions from the website"

                    },

                    settings: {

                        title:
                            "Settings",

                        subtitle:
                            "Manage admin panel settings"

                    }

                };


                if (
                    pageMeta[sectionName] &&
                    pageTitle &&
                    pageSubtitle
                ) {

                    pageTitle.textContent =
                        pageMeta[
                            sectionName
                        ].title;


                    pageSubtitle.textContent =
                        pageMeta[
                            sectionName
                        ].subtitle;

                }


                if (sidebar) {

                    sidebar.classList.remove(
                        "open"
                    );

                }

                if (sectionName === "inquiries") {
                    loadAdminInquiries();
                }

            }
        );

    });


    /* =====================================================
       LOAD SECTION FROM URL HASH
    ===================================================== */

    function loadSectionFromHash() {

        const hash =
            window.location.hash.replace(
                "#",
                ""
            );


        if (!hash) {
            return;
        }


        const targetSection =
            document.getElementById(
                hash
            );


        if (!targetSection) {
            return;
        }


        const targetNav =
            document.querySelector(
                `.nav-item[data-section="${hash}"]`
            );


        navItems.forEach(nav => {

            nav.classList.remove(
                "active"
            );

        });


        sections.forEach(section => {

            section.classList.remove(
                "active"
            );

        });


        targetSection.classList.add(
            "active"
        );


        if (targetNav) {

            targetNav.classList.add(
                "active"
            );

        }


        const pageMeta = {

            dashboard: {

                title:
                    "Dashboard",

                subtitle:
                    "Overview of your EPS TOPIK platform"

            },

            users: {

                title:
                    "Users",

                subtitle:
                    "Manage platform users"

            },

            quizzes: {

                title:
                    "Quizzes",

                subtitle:
                    "Create and manage quizzes"

            },

            results: {

                title:
                    "Results",

                subtitle:
                    "View quiz results and performance"

            },

            payments: {

                title:
                    "Payments",

                subtitle:
                    "Manage and monitor payment activity"

            },

            inquiries: {

                title:
                    "Student Inquiries",

                subtitle:
                    "Read and respond to questions from the website"

            },

            settings: {

                title:
                    "Settings",

                subtitle:
                    "Manage admin panel settings"

            }

        };


        if (
            pageMeta[hash] &&
            pageTitle &&
            pageSubtitle
        ) {

            pageTitle.textContent =
                pageMeta[hash].title;


            pageSubtitle.textContent =
                pageMeta[hash].subtitle;

        }

        if (hash === "inquiries") {
            loadAdminInquiries();
        }

    }


    loadSectionFromHash();


    window.addEventListener(
        "hashchange",
        loadSectionFromHash
    );


    /* =====================================================
       MOBILE MENU
    ===================================================== */

    if (mobileMenu) {

        mobileMenu.addEventListener(
            "click",
            () => {

                if (sidebar) {

                    sidebar.classList.toggle(
                        "open"
                    );

                }

            }
        );

    }


    /* =====================================================
       QUICK ACTIONS
    ===================================================== */

    const quickActions =
        document.querySelectorAll(
            ".quick-action"
        );


    quickActions.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const action =
                    button.dataset.action;


                const mapping = {

                    user:
                        "users",

                    results:
                        "results"

                };


                const target =
                    mapping[action];


                if (!target) {
                    return;
                }


                const targetNav =
                    document.querySelector(
                        `.nav-item[data-section="${target}"]`
                    );


                if (targetNav) {

                    targetNav.click();

                }

            }
        );

    });


    /* =====================================================
       USER SEARCH
    ===================================================== */

    const userSearch =
        document.getElementById(
            "userSearch"
        );


    if (userSearch) {

        userSearch.addEventListener(
            "input",
            () => {

                const search =
                    userSearch.value.toLowerCase();


                const rows =
                    document.querySelectorAll(
                        "#usersTable tr"
                    );


                rows.forEach(row => {

                    const text =
                        row.textContent.toLowerCase();


                    row.style.display =
                        text.includes(search)
                            ? ""
                            : "none";

                });

            }
        );

    }


    /* =====================================================
       VIEW USER MODAL
    ===================================================== */

    const viewUserModal =
        document.getElementById(
            "viewUserModal"
        );

    const closeViewUserModal =
        document.getElementById(
            "closeViewUserModal"
        );

    const closeViewUser =
        document.getElementById(
            "closeViewUser"
        );

    const viewUserAvatar =
        document.getElementById(
            "viewUserAvatar"
        );

    const viewUserName =
        document.getElementById(
            "viewUserName"
        );

    const viewUserEmail =
        document.getElementById(
            "viewUserEmail"
        );

    const viewUserStatus =
        document.getElementById(
            "viewUserStatus"
        );

    const viewUserJoined =
        document.getElementById(
            "viewUserJoined"
        );


    function openViewUserModal(user) {

        if (
            !viewUserModal ||
            !user
        ) {
            return;
        }


        const name =
            user.name ||
            "Unknown User";


        if (viewUserAvatar) {

            viewUserAvatar.textContent =
                name
                    .charAt(0)
                    .toUpperCase();

        }


        if (viewUserName) {

            viewUserName.textContent =
                name;

        }


        if (viewUserEmail) {

            viewUserEmail.textContent =
                user.email || "-";

        }


        if (viewUserStatus) {

            viewUserStatus.textContent =
                user.status || "Active";

        }


        if (viewUserJoined) {

            viewUserJoined.textContent =
                user.created_at
                    ? new Date(
                        user.created_at
                    ).toLocaleDateString()
                    : "-";

        }


        viewUserModal.classList.add(
            "active"
        );

    }


    function closeViewUserModalWindow() {

        if (!viewUserModal) {
            return;
        }


        viewUserModal.classList.remove(
            "active"
        );

    }


    if (closeViewUserModal) {

        closeViewUserModal.addEventListener(
            "click",
            closeViewUserModalWindow
        );

    }


    if (closeViewUser) {

        closeViewUser.addEventListener(
            "click",
            closeViewUserModalWindow
        );

    }


    if (viewUserModal) {

        viewUserModal.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    viewUserModal
                ) {

                    closeViewUserModalWindow();

                }

            }
        );

    }


    /* =====================================================
       EDIT USER MODAL
    ===================================================== */

    const editUserModal =
        document.getElementById(
            "editUserModal"
        );

    const closeEditUserModal =
        document.getElementById(
            "closeEditUserModal"
        );

    const cancelEditUser =
        document.getElementById(
            "cancelEditUser"
        );

    const editUserForm =
        document.getElementById(
            "editUserForm"
        );

    const editUserId =
        document.getElementById(
            "editUserId"
        );

    const editUserName =
        document.getElementById(
            "editUserName"
        );

    const editUserEmail =
        document.getElementById(
            "editUserEmail"
        );

    const editUserStatus =
        document.getElementById(
            "editUserStatus"
        );


    function openEditUserModal(user) {

        if (
            !editUserModal ||
            !user
        ) {
            return;
        }


        if (editUserId) {

            editUserId.value =
                user.id || "";

        }


        if (editUserName) {

            editUserName.value =
                user.name || "";

        }


        if (editUserEmail) {

            editUserEmail.value =
                user.email || "";

        }


        if (editUserStatus) {

            editUserStatus.value =
                user.status || "Active";

        }


        editUserModal.classList.add(
            "active"
        );

    }


    function closeEditUserModalWindow() {

        if (!editUserModal) {
            return;
        }


        editUserModal.classList.remove(
            "active"
        );


        if (editUserForm) {

            editUserForm.reset();

        }

    }


    if (closeEditUserModal) {

        closeEditUserModal.addEventListener(
            "click",
            closeEditUserModalWindow
        );

    }


    if (cancelEditUser) {

        cancelEditUser.addEventListener(
            "click",
            closeEditUserModalWindow
        );

    }


    if (editUserModal) {

        editUserModal.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    editUserModal
                ) {

                    closeEditUserModalWindow();

                }

            }
        );

    }

/* =====================================================
   SAVE EDITED USER
===================================================== */

if (editUserForm) {

    editUserForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const token =
                localStorage.getItem(
                    "admin_access_token"
                );


            if (!token) {

                alert(
                    "Admin session expired. Please login again."
                );

                window.location.href =
                    "ad-login.html";

                return;

            }


            const userId =
                editUserId?.value;


            if (!userId) {

                alert(
                    "User ID is missing."
                );

                return;

            }


            const name =
                editUserName?.value.trim() ||
                "";


            const email =
                editUserEmail?.value.trim() ||
                "";


            if (!name) {

                alert(
                    "Please enter the user's name."
                );

                editUserName?.focus();

                return;

            }


            if (!email) {

                alert(
                    "Please enter the user's email."
                );

                editUserEmail?.focus();

                return;

            }


            const submitButton =
                editUserForm.querySelector(
                    'button[type="submit"]'
                );


            try {

                if (submitButton) {

                    submitButton.disabled =
                        true;

                    submitButton.textContent =
                        "Saving...";

                }


                const response =
                    await fetch(
                        `${API_BASE_URL}/admin/users/${encodeURIComponent(userId)}`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Authorization":
                                    `Bearer ${token}`
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email
                            })
                        }
                    );


                const data =
                    await response.json()
                        .catch(() => ({}));


                /* =================================================
                   SESSION EXPIRED
                ================================================= */

                if (
                    response.status === 401 ||
                    response.status === 403
                ) {

                    localStorage.removeItem(
                        "admin_access_token"
                    );

                    localStorage.removeItem(
                        "admin_user"
                    );


                    alert(
                        "Your admin session has expired. Please login again."
                    );


                    window.location.href =
                        "ad-login.html";

                    return;

                }


                /* =================================================
                   BACKEND ERROR
                ================================================= */

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        data.message ||
                        "Failed to update user."
                    );

                }


                /* =================================================
                   SUCCESS
                ================================================= */

                alert(
                    data.message ||
                    "User updated successfully."
                );


                closeEditUserModalWindow();


                /* =================================================
                   REFRESH USERS
                ================================================= */

                await loadUsers();


                /* =================================================
                   REFRESH DASHBOARD
                ================================================= */

                await loadDashboardStats();


            } catch (error) {

                console.error(
                    "Edit user error:",
                    error
                );


                alert(
                    error.message ||
                    "Unable to update user."
                );


            } finally {

                if (submitButton) {

                    submitButton.disabled =
                        false;

                    submitButton.textContent =
                        "Save Changes";

                }

            }

        }
    );

}



    /* =====================================================
       USER TABLE ACTION HANDLER
    ===================================================== */

    if (usersTable) {

        usersTable.addEventListener(
            "click",
            event => {

                const button =
                    event.target.closest(
                        ".table-action"
                    );


                if (!button) {
                    return;
                }


                const userId =
                    button.dataset.userId;


                if (!userId) {
                    return;
                }


                const selectedUser =
                    currentUsers.find(
                        user =>
                            String(user.id) ===
                            String(userId)
                    );


                if (!selectedUser) {

                    console.error(
                        "User not found:",
                        userId
                    );

                    return;

                }


                if (
                    button.classList.contains(
                        "view-user-btn"
                    )
                ) {

                    openViewUserModal(
                        selectedUser
                    );

                }

                if (
                    button.classList.contains(
                        "student-results-btn"
                    )
                ) {
                    window.location.href =
                        `admin-student-results.html?user_id=${encodeURIComponent(userId)}`;
                }


                if (
                    button.classList.contains(
                        "edit-user-btn"
                    )
                ) {

                    openEditUserModal(
                        selectedUser
                    );

                }
            
                if (
                button.classList.contains(
                "access-user-btn"
                )
                ) {

                window.location.href =
                `user-access.html?user_id=${encodeURIComponent(
                userId
                )}`;

}

            }
        );

    }


    /* =====================================================
       TERMS & CONDITIONS
    ===================================================== */

    const termsModal =
        document.getElementById(
            "termsModal"
        );

    const viewTermsBtn =
        document.getElementById(
            "viewTermsBtn"
        );

    const closeTermsModal =
        document.getElementById(
            "closeTermsModal"
        );

    const closeTermsBtn =
        document.getElementById(
            "closeTermsBtn"
        );


    function openTermsModal() {

        if (!termsModal) {
            return;
        }


        termsModal.classList.add(
            "active"
        );

    }


    function closeTermsModalWindow() {

        if (!termsModal) {
            return;
        }


        termsModal.classList.remove(
            "active"
        );

    }


    if (viewTermsBtn) {

        viewTermsBtn.addEventListener(
            "click",
            openTermsModal
        );

    }


    if (closeTermsModal) {

        closeTermsModal.addEventListener(
            "click",
            closeTermsModalWindow
        );

    }


    if (closeTermsBtn) {

        closeTermsBtn.addEventListener(
            "click",
            closeTermsModalWindow
        );

    }


    if (termsModal) {

        termsModal.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    termsModal
                ) {

                    closeTermsModalWindow();

                }

            }
        );

    }


/* =====================================================
   ADMIN SETTINGS
===================================================== */

const saveAdminSettings =
    document.getElementById(
        "saveAdminSettings"
    );


if (saveAdminSettings) {

    saveAdminSettings.addEventListener(
        "click",
        async () => {

            const token =
                localStorage.getItem(
                    "admin_access_token"
                );


            if (!token) {

                alert(
                    "Admin session expired. Please login again."
                );

                window.location.href =
                    "ad-login.html";

                return;

            }


            const name =
                settingsAdminName?.value.trim() ||
                "";


            const email =
                settingsAdminEmail?.value.trim() ||
                "";


            /* =================================================
               VALIDATION
            ================================================= */

            if (!name) {

                alert(
                    "Please enter the admin name."
                );

                settingsAdminName?.focus();

                return;

            }


            if (!email) {

                alert(
                    "Please enter the admin email."
                );

                settingsAdminEmail?.focus();

                return;

            }


            try {

                saveAdminSettings.disabled =
                    true;

                saveAdminSettings.textContent =
                    "Saving...";


                const response =
                    await fetch(
                        `${API_BASE_URL}/auth/admin/profile`,
                        {
                            method: "PUT",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Authorization":
                                    `Bearer ${token}`
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email
                            })
                        }
                    );


                const data =
                    await response.json()
                        .catch(() => ({}));


                /* =================================================
                   SESSION EXPIRED
                ================================================= */

                if (
                    response.status === 401 ||
                    response.status === 403
                ) {

                    localStorage.removeItem(
                        "admin_access_token"
                    );

                    localStorage.removeItem(
                        "admin_user"
                    );


                    alert(
                        "Your admin session has expired. Please login again."
                    );


                    window.location.href =
                        "ad-login.html";

                    return;

                }


                /* =================================================
                   BACKEND ERROR
                ================================================= */

                if (!response.ok) {

                    alert(
                        data.detail ||
                        data.message ||
                        "Failed to update admin profile."
                    );

                    return;

                }


                /* =================================================
                   UPDATE LOCAL ADMIN DATA
                ================================================= */

                const updatedAdmin = {

                    id:
                        data.user_id,

                    name:
                        data.name,

                    email:
                        data.email,

                    role:
                        data.role

                };


                localStorage.setItem(
                    "admin_user",
                    JSON.stringify(
                        updatedAdmin
                    )
                );


                /* =================================================
                   UPDATE PAGE
                ================================================= */

                updateAdminProfile(
                    updatedAdmin
                );


                alert(
                    data.message ||
                    "Admin profile updated successfully."
                );


            } catch (error) {

                console.error(
                    "Admin profile update error:",
                    error
                );


                alert(
                    "Unable to connect to the backend. Make sure FastAPI is running."
                );


            } finally {

                saveAdminSettings.disabled =
                    false;

                saveAdminSettings.textContent =
                    "Save Changes";

            }

        }
    );

}

    /* =====================================================
       LOGOUT
    ===================================================== */

    const logoutBtn =
        document.getElementById(
            "logoutBtn"
        );


    if (logoutBtn) {

        logoutBtn.addEventListener(
            "click",
            () => {

                const confirmed =
                    confirm(
                        "Are you sure you want to logout?"
                    );


                if (!confirmed) {
                    return;
                }


                /*
                 * Remove ONLY admin authentication.
                 *
                 * Student authentication remains separate.
                 */

                localStorage.removeItem(
                    "admin_access_token"
                );


                localStorage.removeItem(
                    "admin_user"
                );


                /*
                 * Do not remove:
                 *
                 * student_access_token
                 * student_user
                 */


                window.location.replace("../index.html");

            }
        );

    }


    /* =====================================================
       ADD USER MODAL
    ===================================================== */

    const addUserBtn =
        document.getElementById(
            "addUserBtn"
        );

    const addUserModal =
        document.getElementById(
            "addUserModal"
        );

    const closeAddUserModal =
        document.getElementById(
            "closeAddUserModal"
        );

    const cancelAddUser =
        document.getElementById(
            "cancelAddUser"
        );

    const addUserForm =
        document.getElementById(
            "addUserForm"
        );


    function openAddUserModal() {

        if (!addUserModal) {
            return;
        }


        addUserModal.classList.add(
            "active"
        );

    }


    function closeAddUserModalWindow() {

        if (!addUserModal) {
            return;
        }


        addUserModal.classList.remove(
            "active"
        );


        if (addUserForm) {

            addUserForm.reset();

        }

    }


    if (addUserBtn) {

        addUserBtn.addEventListener(
            "click",
            openAddUserModal
        );

    }


    if (closeAddUserModal) {

        closeAddUserModal.addEventListener(
            "click",
            closeAddUserModalWindow
        );

    }


    if (cancelAddUser) {

        cancelAddUser.addEventListener(
            "click",
            closeAddUserModalWindow
        );

    }


    if (addUserModal) {

        addUserModal.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    addUserModal
                ) {

                    closeAddUserModalWindow();

                }

            }
        );

    }


if (addUserForm) {

    addUserForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();


            const token =
                localStorage.getItem(
                    "admin_access_token"
                );


            if (!token) {

                alert(
                    "Admin session expired. Please login again."
                );

                window.location.href =
                    "ad-login.html";

                return;

            }


            /*
             * Get Add User form inputs.
             */

            const nameInput =
                document.getElementById(
                    "addUserName"
                );

            const emailInput =
                document.getElementById(
                    "addUserEmail"
                );

            const passwordInput =
                document.getElementById(
                    "addUserPassword"
                );


            if (
                !nameInput ||
                !emailInput ||
                !passwordInput
            ) {

                console.error(
                    "Add User form inputs were not found."
                );

                alert(
                    "Add User form fields could not be found."
                );

                return;

            }


            const name =
                nameInput.value.trim();


            const email =
                emailInput.value.trim();


            const password =
                passwordInput.value;


            /* =================================================
               VALIDATION
            ================================================= */

            if (!name) {

                alert(
                    "Please enter the user's name."
                );

                nameInput.focus();

                return;

            }


            if (!email) {

                alert(
                    "Please enter the user's email."
                );

                emailInput.focus();

                return;

            }


            if (!password) {

                alert(
                    "Please enter a password."
                );

                passwordInput.focus();

                return;

            }


            if (password.length < 6) {

                alert(
                    "Password must contain at least 6 characters."
                );

                passwordInput.focus();

                return;

            }


            /*
             * Find the actual submit button
             * inside the Add User form.
             */

            const submitButton =
                addUserForm.querySelector(
                    'button[type="submit"]'
                );


            try {

                if (submitButton) {

                    submitButton.disabled =
                        true;

                    submitButton.textContent =
                        "Adding...";

                }


                const response =
                    await fetch(
                        `${API_BASE_URL}/admin/users`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json",

                                "Authorization":
                                    `Bearer ${token}`
                            },

                            body: JSON.stringify({
                                name: name,
                                email: email,
                                password: password
                            })
                        }
                    );


                const data =
                    await response.json()
                        .catch(
                            () => ({})
                        );


                /* =================================================
                   SESSION EXPIRED / UNAUTHORIZED
                ================================================= */

                if (
                    response.status === 401 ||
                    response.status === 403
                ) {

                    localStorage.removeItem(
                        "admin_access_token"
                    );

                    localStorage.removeItem(
                        "admin_user"
                    );


                    alert(
                        "Your admin session has expired. " +
                        "Please login again."
                    );


                    window.location.href =
                        "ad-login.html";

                    return;

                }


                /* =================================================
                   BACKEND ERROR
                ================================================= */

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        data.message ||
                        "Failed to create user."
                    );

                }


                /* =================================================
                   SUCCESS
                ================================================= */

                alert(
                    data.message ||
                    "User created successfully."
                );


                /*
                 * Reload users from PostgreSQL.
                 */

                await loadUsers();


                /*
                 * Refresh dashboard student count.
                 */

                await loadDashboardStats();


                /*
                 * Close modal and reset form.
                 */

                closeAddUserModalWindow();


            } catch (error) {

                console.error(
                    "Add user error:",
                    error
                );


                alert(
                    error.message ||
                    "Unable to create user."
                );


            } finally {

                if (submitButton) {

                    submitButton.disabled =
                        false;

                    submitButton.textContent =
                        "Add User";

                }

            }

        }
    );

}

    /* =====================================================
       PROFILE PICTURE MANAGEMENT
    ===================================================== */

    const profilePictureInput =
        document.getElementById(
            "profilePictureInput"
        );

    const profilePicturePreview =
        document.getElementById(
            "profilePicturePreview"
        );

    const removeProfilePicture =
        document.getElementById(
            "removeProfilePicture"
        );


    /* =====================================================
       APPLY PROFILE PICTURE TO AVATARS
    ===================================================== */

    function applyProfilePictureToAvatars(
        imageData
    ) {

        /*
         * Get current admin name.
         */

        let adminName = "";


        const savedAdmin =
            localStorage.getItem(
                "admin_user"
            );


        if (savedAdmin) {

            try {

                const admin =
                    JSON.parse(
                        savedAdmin
                    );


                adminName =
                    admin.name || "";

            } catch {

                adminName = "";

            }

        }


        /* =================================================
           TOP AVATAR
        ================================================= */

        setAdminAvatar(
            topAdminAvatar,
            imageData,
            adminName
        );


        /* =================================================
           SIDEBAR AVATAR
        ================================================= */

        setAdminAvatar(
            sidebarAdminAvatar,
            imageData,
            adminName
        );

    }


    /* =====================================================
       LOAD SAVED PROFILE PICTURE
    ===================================================== */

    function loadProfilePicture() {

        const savedPicture =
            localStorage.getItem(
                "adminProfilePicture"
            ) || "";


        /* =================================================
           PROFILE PAGE PREVIEW
        ================================================= */

        if (profilePicturePreview) {

            if (savedPicture) {

                profilePicturePreview.textContent =
                    "";

                profilePicturePreview.style.backgroundImage =
                    `url("${savedPicture}")`;

                profilePicturePreview.style.backgroundSize =
                    "cover";

                profilePicturePreview.style.backgroundPosition =
                    "center";

                profilePicturePreview.style.backgroundRepeat =
                    "no-repeat";

            } else {

                profilePicturePreview.style.backgroundImage =
                    "none";

                profilePicturePreview.textContent =
                    "";

            }

        }


        /* =================================================
           APPLY TO AVATARS
        ================================================= */

        applyProfilePictureToAvatars(
            savedPicture
        );

    }


    /* =====================================================
       CHANGE PROFILE PICTURE
    ===================================================== */

    if (profilePictureInput) {

        profilePictureInput.addEventListener(
            "change",
            event => {

                const file =
                    event.target.files[0];


                if (!file) {
                    return;
                }


                const allowedTypes = [

                    "image/jpeg",

                    "image/png",

                    "image/webp"

                ];


                if (
                    !allowedTypes.includes(
                        file.type
                    )
                ) {

                    alert(
                        "Please select a JPG, PNG or WebP image."
                    );


                    profilePictureInput.value =
                        "";


                    return;

                }


                const maxSize =
                    2 * 1024 * 1024;


                if (
                    file.size >
                    maxSize
                ) {

                    alert(
                        "Profile picture must be smaller than 2 MB."
                    );


                    profilePictureInput.value =
                        "";


                    return;

                }


                const reader =
                    new FileReader();


                reader.onload =
                    function() {

                        const imageData =
                            reader.result;


                        localStorage.setItem(
                            "adminProfilePicture",
                            imageData
                        );


                        if (
                            profilePicturePreview
                        ) {

                            profilePicturePreview.textContent =
                                "";

                            profilePicturePreview.style.backgroundImage =
                                `url("${imageData}")`;

                            profilePicturePreview.style.backgroundSize =
                                "cover";

                            profilePicturePreview.style.backgroundPosition =
                                "center";

                            profilePicturePreview.style.backgroundRepeat =
                                "no-repeat";

                        }


                        applyProfilePictureToAvatars(
                            imageData
                        );


                        alert(
                            "Profile picture updated successfully."
                        );

                    };


                reader.onerror =
                    function() {

                        alert(
                            "Unable to read the selected image."
                        );


                        profilePictureInput.value =
                            "";

                    };


                reader.readAsDataURL(
                    file
                );

            }
        );

    }


    /* =====================================================
       REMOVE PROFILE PICTURE
    ===================================================== */

    if (removeProfilePicture) {

        removeProfilePicture.addEventListener(
            "click",
            () => {

                const confirmed =
                    confirm(
                        "Are you sure you want to remove your profile picture?"
                    );


                if (!confirmed) {
                    return;
                }


                localStorage.removeItem(
                    "adminProfilePicture"
                );


                if (
                    profilePicturePreview
                ) {

                    profilePicturePreview.style.backgroundImage =
                        "none";

                    profilePicturePreview.textContent =
                        "";

                }


                applyProfilePictureToAvatars(
                    ""
                );


                if (profilePictureInput) {

                    profilePictureInput.value =
                        "";

                }


                alert(
                    "Profile picture removed."
                );

            }
        );

    }


    /* =====================================================
       LOAD PROFILE PICTURE
    ===================================================== */

    loadProfilePicture();


    /* =====================================================
       ACCOUNT SECURITY
    ===================================================== */

    const changePasswordForm =
        document.getElementById(
            "changePasswordForm"
        );

    const changePasswordBtn =
        document.getElementById(
            "changePasswordBtn"
        );

    const currentPasswordInput =
        document.getElementById(
            "currentPassword"
        );

    const newPasswordInput =
        document.getElementById(
            "newPassword"
        );

    const confirmPasswordInput =
        document.getElementById(
            "confirmPassword"
        );


    if (changePasswordForm) {

        changePasswordForm.addEventListener(
            "submit",
            async function(event) {

                event.preventDefault();


                const currentPassword =
                    currentPasswordInput?.value ||
                    "";


                const newPassword =
                    newPasswordInput?.value ||
                    "";


                const confirmPassword =
                    confirmPasswordInput?.value ||
                    "";


                /* =================================================
                   VALIDATION
                ================================================= */

                if (!currentPassword) {

                    alert(
                        "Please enter your current password."
                    );


                    currentPasswordInput?.focus();


                    return;

                }


                if (!newPassword) {

                    alert(
                        "Please enter your new password."
                    );


                    newPasswordInput?.focus();


                    return;

                }


                if (
                    newPassword.length <
                    8
                ) {

                    alert(
                        "New password must contain at least 8 characters."
                    );


                    newPasswordInput?.focus();


                    return;

                }


                if (!confirmPassword) {

                    alert(
                        "Please confirm your new password."
                    );


                    confirmPasswordInput?.focus();


                    return;

                }


                if (
                    newPassword !==
                    confirmPassword
                ) {

                    alert(
                        "New passwords do not match."
                    );


                    confirmPasswordInput?.focus();


                    return;

                }


                if (
                    currentPassword ===
                    newPassword
                ) {

                    alert(
                        "New password must be different from your current password."
                    );


                    newPasswordInput?.focus();


                    return;

                }


                /* =================================================
                   IMPORTANT:
                   USE ADMIN TOKEN ONLY
                ================================================= */

                const accessToken =
                    localStorage.getItem(
                        "admin_access_token"
                    );


                if (!accessToken) {

                    alert(
                        "Your admin session has expired. Please login again."
                    );


                    window.location.href =
                        "ad-login.html";


                    return;

                }


                /* =================================================
                   BUTTON LOADING
                ================================================= */

                if (changePasswordBtn) {

                    changePasswordBtn.disabled =
                        true;


                    changePasswordBtn.textContent =
                        "Changing Password...";

                }


                try {

                    /* =================================================
                       ADMIN CHANGE PASSWORD API
                    ================================================= */

                    const response =
                        await fetch(
                            `${API_BASE_URL}/auth/admin/change-password`,
                            {

                                method:
                                    "POST",

                                headers: {

                                    "Content-Type":
                                        "application/json",

                                    "Authorization":
                                        `Bearer ${accessToken}`

                                },

                                body:
                                    JSON.stringify({

                                        current_password:
                                            currentPassword,

                                        new_password:
                                            newPassword,

                                        confirm_password:
                                            confirmPassword

                                    })

                            }
                        );


                    let data = {};


                    try {

                        data =
                            await response.json();

                    } catch {

                        data = {};

                    }


                    /* =================================================
                       UNAUTHORIZED
                    ================================================= */

                    if (
                        response.status ===
                        401
                    ) {

                        localStorage.removeItem(
                            "admin_access_token"
                        );


                        localStorage.removeItem(
                            "admin_user"
                        );


                        alert(
                            "Your admin session has expired. Please login again."
                        );


                        window.location.href =
                            "ad-login.html";


                        return;

                    }


                    /* =================================================
                       OTHER ERROR
                    ================================================= */

                    if (!response.ok) {

                        throw new Error(

                            data.detail ||

                            data.message ||

                            "Unable to change password."

                        );

                    }


                    /* =================================================
                       SUCCESS
                    ================================================= */

                    alert(
                        data.message ||
                        "Password changed successfully."
                    );


                    changePasswordForm.reset();

                } catch (error) {

                    console.error(
                        "Change password error:",
                        error
                    );


                    alert(
                        error.message ||
                        "Unable to change password. Please try again."
                    );

                } finally {

                    if (changePasswordBtn) {

                        changePasswordBtn.disabled =
                            false;


                        changePasswordBtn.textContent =
                            "Change Password";

                    }

                }

            }
        );

    }


    /* =====================================================
       LOAD ADMIN PROFILE AND DASHBOARD DATA
    ===================================================== */

    loadLoggedInAdmin();

    loadDashboardStats();

});
