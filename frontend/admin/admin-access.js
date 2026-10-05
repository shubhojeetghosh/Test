(function () {
    "use strict";

    const form = document.getElementById("adminAccessForm");
    if (!form) return;

    const token = localStorage.getItem("admin_access_token");
    if (!token) {
        window.location.replace("ad-login.html");
        return;
    }

    const emailInput = document.getElementById("newAdminEmail");
    const otpInput = document.getElementById("adminOtp");
    const otpSection = document.getElementById("adminOtpSection");
    const detailsSection = document.getElementById("adminDetailsSection");
    const sendButton = document.getElementById("sendAdminOtpBtn");
    const verifyButton = document.getElementById("verifyAdminOtpBtn");
    const createButton = document.getElementById("createAdminBtn");
    const feedback = document.getElementById("adminAccessFeedback");
    const adminList = document.getElementById("adminAccountList");
    const nameInput = document.getElementById("newAdminName");
    const passwordInput = document.getElementById("newAdminPassword");
    const confirmInput = document.getElementById("confirmAdminPassword");
    let verifiedEmail = "";

    function setFeedback(message, state = "") {
        feedback.textContent = message;
        feedback.dataset.state = state;
    }

    async function request(path, options = {}) {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("admin_access_token");
                window.location.replace("ad-login.html");
            }
            throw new Error(data.detail || data.message || "Request failed. Please try again.");
        }
        return data;
    }

    function resetVerification() {
        verifiedEmail = "";
        otpSection.hidden = true;
        otpInput.required = false;
        detailsSection.hidden = true;
        emailInput.readOnly = false;
        otpInput.value = "";
        for (const input of [nameInput, passwordInput, confirmInput]) input.disabled = true;
        createButton.disabled = true;
    }

    emailInput.addEventListener("input", () => {
        if (verifiedEmail && emailInput.value.trim().toLowerCase() !== verifiedEmail) {
            resetVerification();
            setFeedback("The email changed. Send a new OTP to verify this address.");
        }
    });

    sendButton.addEventListener("click", async () => {
        const email = emailInput.value.trim().toLowerCase();
        if (!emailInput.checkValidity()) {
            emailInput.reportValidity();
            return;
        }
        resetVerification();
        sendButton.disabled = true;
        sendButton.textContent = "Sending…";
        setFeedback("");
        try {
            const data = await request("/auth/admin/create", {
                method: "POST",
                body: JSON.stringify({ email })
            });
            emailInput.value = email;
            otpSection.hidden = false;
            otpInput.required = true;
            otpInput.focus();
            setFeedback(data.message || "A 6-digit verification code was sent to that email.", "success");
        } catch (error) {
            setFeedback(error.message, "error");
        } finally {
            sendButton.disabled = false;
            sendButton.textContent = "Send OTP";
        }
    });

    verifyButton.addEventListener("click", async () => {
        const email = emailInput.value.trim().toLowerCase();
        const otp = otpInput.value.trim();
        if (!/^\d{6}$/.test(otp)) {
            otpInput.setCustomValidity("Enter the 6-digit code from the email.");
            otpInput.reportValidity();
            otpInput.addEventListener("input", () => otpInput.setCustomValidity(""), { once: true });
            return;
        }
        verifyButton.disabled = true;
        verifyButton.textContent = "Verifying…";
        try {
            const data = await request("/auth/admin/create/verify-otp", {
                method: "POST",
                body: JSON.stringify({ email, otp })
            });
            verifiedEmail = email;
            emailInput.readOnly = true;
            otpInput.required = false;
            detailsSection.hidden = false;
            for (const input of [nameInput, passwordInput, confirmInput]) input.disabled = false;
            createButton.disabled = false;
            setFeedback(data.message || "Email verified. Enter the new admin’s name and password.", "success");
            nameInput.focus();
        } catch (error) {
            setFeedback(error.message, "error");
        } finally {
            verifyButton.disabled = false;
            verifyButton.textContent = "Verify OTP";
        }
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();
        const email = emailInput.value.trim().toLowerCase();
        if (!verifiedEmail || email !== verifiedEmail) {
            setFeedback("Verify this email with the OTP before creating the admin account.", "error");
            return;
        }
        if (passwordInput.value !== confirmInput.value) {
            confirmInput.setCustomValidity("The passwords do not match.");
            confirmInput.reportValidity();
            confirmInput.addEventListener("input", () => confirmInput.setCustomValidity(""), { once: true });
            return;
        }

        createButton.disabled = true;
        createButton.textContent = "Creating…";
        try {
            const data = await request("/auth/admin/create/set-password", {
                method: "POST",
                body: JSON.stringify({
                    name: nameInput.value.trim(),
                    email,
                    password: passwordInput.value,
                    confirm_password: confirmInput.value
                })
            });
            form.reset();
            resetVerification();
            setFeedback(`${data.name || "The new administrator"} can now sign in from the Admin Login page using this email and password.`, "success");
            await loadAdminAccounts();
        } catch (error) {
            setFeedback(error.message, "error");
        } finally {
            createButton.disabled = true;
            createButton.textContent = "Create Administrator";
        }
    });

    function showEmpty(message, isError = false) {
        const empty = document.createElement("div");
        empty.className = "admin-list-empty";
        const icon = document.createElement("div");
        icon.className = "admin-list-empty-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = isError ? "!" : "👤";
        const text = document.createElement("strong");
        text.textContent = message;
        empty.append(icon, text);
        adminList.replaceChildren(empty);
    }

    async function loadAdminAccounts() {
        showEmpty("Loading administrator accounts…");
        try {
            const data = await request("/auth/admin/accounts");
            const admins = Array.isArray(data.admins) ? data.admins : [];
            if (!admins.length) {
                showEmpty("No administrator accounts were found.");
                return;
            }
            const fragment = document.createDocumentFragment();
            admins.forEach(admin => {
                const row = document.createElement("article");
                row.className = "admin-account-row";
                const avatar = document.createElement("span");
                avatar.className = "admin-account-avatar";
                avatar.textContent = (admin.name || "A").trim().charAt(0).toUpperCase();
                const identity = document.createElement("div");
                identity.className = "admin-account-identity";
                const name = document.createElement("strong");
                name.textContent = admin.name || "Administrator";
                const email = document.createElement("span");
                email.textContent = admin.email || "";
                identity.append(name, email);
                const badge = document.createElement("span");
                badge.className = "admin-account-badge";
                badge.textContent = Number(admin.id) === Number(data.current_admin_id) ? "You · Admin" : "Admin";
                row.append(avatar, identity, badge);
                fragment.append(row);
            });
            adminList.replaceChildren(fragment);
        } catch (error) {
            showEmpty(error.message || "Could not load administrator accounts.", true);
        }
    }

    for (const input of [nameInput, passwordInput, confirmInput]) input.disabled = true;
    createButton.disabled = true;
    loadAdminAccounts();
})();
