const API_BASE_URL = window.API_BASE_URL || "";
function escapeStudentHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

const API_ENDPOINTS = {

  login:
    `${API_BASE_URL}/auth/login`,

  verifyOtp:
    `${API_BASE_URL}/auth/verify-otp`,

  register:
    `${API_BASE_URL}/auth/register`,

  verifyRegistrationOtp:
    `${API_BASE_URL}/auth/verify-registration-otp`,

  resendRegistrationOtp:
    `${API_BASE_URL}/auth/resend-registration-otp`,

  forgotPassword:
    `${API_BASE_URL}/auth/forgot-password`,

  resetPassword:
    `${API_BASE_URL}/auth/reset-password`,

  profile:
    `${API_BASE_URL}/auth/profile`,

  dashboard:
  `${API_BASE_URL}/api/student/dashboard`

};

function editProfile() {

  window.location.href = "profile.html";
}


function logout() {

  const confirmLogout =
    confirm("Are you sure you want to logout?");


  if (!confirmLogout) {
    return;
  }


  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");

  window.location.href = "login.html";
}
//////profile
/* =========================================================
   PROFILE PAGE
   ========================================================= */

const profileForm =
  document.getElementById("profileForm");


const profilePhotoInput =
  document.getElementById("profilePhotoInput");


/* ================= LOAD PROFILE ================= */

function loadProfilePage() {

  if (!profileForm) {
    return;
  }


 const savedUser =
  JSON.parse(localStorage.getItem("user") || "{}");

const name =
  savedUser.name || "";

const email =
  savedUser.email ||
  localStorage.getItem("user_email") ||
  "";

  const studentId =
    savedUser.student_id ||
    savedUser.studentId ||
    savedUser.roll_no ||
    savedUser.rollNo ||
    localStorage.getItem("student_id") ||
    "";
  

  const photo =
    localStorage.getItem("profile_photo");


  /* Form */

  document.getElementById(
    "profileName"
  ).value = name;


  document.getElementById(
    "profileEmail"
  ).value = email;


  /* Left card */

  document.getElementById(
    "profileDisplayName"
  ).textContent = name;


  document.getElementById(
    "profileDisplayId"
  ).textContent = studentId;


  updateProfileInitials(name);


  if (photo) {/* =========================================================
   EXAM RESULT PAGE
   ========================================================= */


/* ================= REVIEW ANSWERS ================= */

function reviewAnswers() {

  window.location.href =
    "review-answers.html";
}


/* ================= RETAKE TEST ================= */

function retakeTest() {

  const confirmRetake =
    confirm(
      "Do you want to retake this test?"
    );


  if (!confirmRetake) {
    return;
  }


  /*
     Change exam.html if your exam page
     uses another filename.
  */

  window.location.href =
    "exam.html";
}


/* ================= DASHBOARD ================= */

function goToDashboard() {

  window.location.href =
    "dashboard.html";
}


/* ================= DOWNLOAD RESULT ================= */

function downloadResult() {

  const testName =
    document.getElementById(
      "resultTestName"
    )?.textContent || "EPS TOPIK Test";


  const percentage =
    document.getElementById(
      "resultPercentage"
    )?.textContent || "-";


  const score =
    document.getElementById(
      "resultScore"
    )?.textContent || "-";


  const correct =
    document.getElementById(
      "correctAnswers"
    )?.textContent || "-";


  const wrong =
    document.getElementById(
      "wrongAnswers"
    )?.textContent || "-";


  const unanswered =
    document.getElementById(
      "unansweredAnswers"
    )?.textContent || "-";


  const resultText = `
EPS TOPIK EXAM RESULT

Test: ${testName}

Score: ${score}
Percentage: ${percentage}

Correct Answers: ${correct}
Incorrect Answers: ${wrong}
Unanswered: ${unanswered}

EPS TOPIK Exam Platform
`;


  const file =
    new Blob(
      [resultText],
      {
        type: "text/plain"
      }
    );


  const url =
    URL.createObjectURL(file);


  const link =
    document.createElement("a");


  link.href = url;

  link.download =
    "EPS-TOPIK-Result.txt";


  document.body.appendChild(link);

  link.click();


  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

    showProfilePhoto(photo);

  }

}



/* ================= INITIALS ================= */

function updateProfileInitials(name) {

  const fallback =
    document.getElementById(
      "profilePhotoFallback"
    );


  if (!fallback) {
    return;
  }


  const parts =
    name
      .trim()
      .split(/\s+/);


  let initials = "ST";


  if (parts.length === 1) {

    initials =
      parts[0]
        .substring(0, 2)
        .toUpperCase();

  }

  else if (parts.length > 1) {

    initials =
      (
        parts[0][0] +
        parts[parts.length - 1][0]
      ).toUpperCase();

  }


  fallback.textContent =
    initials;

}



/* ================= PHOTO PREVIEW ================= */

if (profilePhotoInput) {

  profilePhotoInput.addEventListener(
    "change",
    function () {

      const file =
        this.files[0];


      if (!file) {
        return;
      }


      /* 2 MB */

      const maxSize =
        2 * 1024 * 1024;


      if (file.size > maxSize) {

        showMessage(
          "Profile photo must be smaller than 2 MB.",
          "error"
        );

        this.value = "";

        return;

      }


      if (
        ![
          "image/jpeg",
          "image/png",
          "image/webp"
        ].includes(file.type)
      ) {

        showMessage(
          "Please select a JPG, PNG or WEBP image.",
          "error"
        );

        this.value = "";

        return;

      }


      const reader =
        new FileReader();


      reader.onload =
        function (event) {

          const imageData =
            event.target.result;


          showProfilePhoto(
            imageData
          );


          /*
             Temporary frontend storage.

             Later this should be uploaded
             to the backend/server.
          */

          localStorage.setItem(
            "profile_photo",
            imageData
          );

        };


      reader.readAsDataURL(
        file
      );

    }
  );

}



/* ================= SHOW PHOTO ================= */

function showProfilePhoto(imageData) {

  const preview =
    document.getElementById(
      "profilePhotoPreview"
    );


  const fallback =
    document.getElementById(
      "profilePhotoFallback"
    );


  if (!preview || !fallback) {
    return;
  }


  preview.src =
    imageData;


  preview.style.display =
    "block";


  fallback.style.display =
    "none";

}



/* ================= REMOVE PHOTO ================= */

function removeProfilePhoto() {

  localStorage.removeItem(
    "profile_photo"
  );


  const preview =
    document.getElementById(
      "profilePhotoPreview"
    );


  const fallback =
    document.getElementById(
      "profilePhotoFallback"
    );


  if (preview) {

    preview.src = "";

    preview.style.display =
      "none";

  }


  if (fallback) {

    fallback.style.display =
      "grid";

  }


  if (profilePhotoInput) {

    profilePhotoInput.value =
      "";

  }

}



/* ================= SAVE PROFILE ================= */

if (profileForm) {

  profileForm.addEventListener(
    "submit",
    handleProfileUpdate
  );

}


async function handleProfileUpdate(event) {

  event.preventDefault();


  const name =
    document
      .getElementById("profileName")
      .value
      .trim();


  const email =
    document
      .getElementById("profileEmail")
      .value
      .trim();


  const savedUser =
    JSON.parse(localStorage.getItem("user") || "{}");

  const studentId =
    savedUser.student_id ||
    savedUser.studentId ||
    savedUser.roll_no ||
    savedUser.rollNo ||
    localStorage.getItem("student_id") ||
    "";


  const currentPassword =
    document
      .getElementById("currentPassword")
      .value;


  const newPassword =
    document
      .getElementById("newPassword")
      .value;


  const confirmPassword =
    document
      .getElementById("confirmNewPassword")
      .value;


  /* ================= VALIDATION ================= */


  if (!name) {

    showMessage(
      "Please enter your full name.",
      "error"
    );

    return;

  }


  if (!email) {

    showMessage(
      "Please enter your email.",
      "error"
    );

    return;

  }


  /*
     Password fields are optional.

     But if the user enters a new password,
     all required password fields must exist.
  */

  if (
    currentPassword ||
    newPassword ||
    confirmPassword
  ) {


    if (!currentPassword) {

      showMessage(
        "Enter your current password before changing it.",
        "error"
      );

      return;

    }


    if (!newPassword) {

      showMessage(
        "Enter your new password.",
        "error"
      );

      return;

    }


    if (newPassword.length < 6) {

      showMessage(
        "New password must contain at least 6 characters.",
        "error"
      );

      return;

    }


    if (
      newPassword !==
      confirmPassword
    ) {

      showMessage(
        "New passwords do not match.",
        "error"
      );

      return;

    }

  }



  /*
     FRONTEND STORAGE FOR NOW

     Once backend gives the profile endpoint,
     replace this part with authenticatedFetch().
  */


  localStorage.setItem(
    "user_name",
    name
  );


  localStorage.setItem(
    "user_email",
    email
  );


  // Keep the registered student ID read-only; profile edits do not change it.


  document.getElementById(
    "profileDisplayName"
  ).textContent = name;


  document.getElementById(
    "profileDisplayId"
  ).textContent = studentId;


  updateProfileInitials(
    name
  );


  showMessage(
    "Profile updated successfully.",
    "success"
  );


  /*
     IMPORTANT:

     This does NOT really change the backend
     password yet.

     When backend provides something like:

     PUT /auth/profile
     POST /auth/change-password

     we will send currentPassword/newPassword
     to those APIs.
  */

}



/* ================= START PROFILE PAGE ================= */

document.addEventListener(
  "DOMContentLoaded",
  function () {

    loadProfilePage();

  }
);
/* =========================================================
   PASSWORD SHOW / HIDE
   ========================================================= */

function togglePassword(inputId, button) {

  const input = document.getElementById(inputId);

  if (!input) {
    return;
  }

  if (input.type === "password") {

    input.type = "text";
    button.textContent = "Hide";

  } else {

    input.type = "password";
    button.textContent = "Show";

  }
}

/* =========================================================
   REGISTER
   Connect register.html to POST /auth/register
   ========================================================= */

const registerForm = document.getElementById("registerForm");

if (registerForm) {

  registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    // Get values from register.html
    const name =
      document.getElementById("registerName").value.trim();

    const email =
      document.getElementById("registerEmail").value.trim();

    const password =
      document.getElementById("registerPassword").value;

    const confirmPassword =
      document.getElementById("confirmPassword").value;

    const messageBox =
      document.getElementById("messageBox");

    const registerButton =
      document.getElementById("registerButton");


    // ==========================================
    // CHECK PASSWORDS
    // ==========================================

    if (password !== confirmPassword) {

      if (messageBox) {
        messageBox.textContent =
          "Passwords do not match.";
      }

      return;
    }


    try {

      // Disable button while registering
      if (registerButton) {

        registerButton.disabled = true;

        registerButton.textContent =
          "Creating Account...";

      }


    // ==========================================
    // CALL BACKEND REGISTER API
    // ==========================================

      const response = await fetch(
        API_ENDPOINTS.register,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({

            name: name,

            email: email,

            password: password

          })
        }
      );


      // Get backend response
      const data = await response.json();

      console.log(
        "Register API response:",
        data
      );


      // ==========================================
      // BACKEND ERROR
      // ==========================================

      if (!response.ok) {

        let errorMessage =
          "Registration failed.";


        if (data.detail) {

          if (Array.isArray(data.detail)) {

            errorMessage =
              data.detail
                .map(error =>
                  error.msg || "Invalid input"
                )
                .join(", ");

          } else {

            errorMessage =
              data.detail;

          }

        } else if (data.message) {

          errorMessage =
            data.message;

        }


        if (messageBox) {

          messageBox.textContent =
            errorMessage;

        } else {

          alert(errorMessage);

        }

        return;
      }


      if (messageBox) {
        messageBox.textContent =
          "Verification code sent. Check your email to finish creating your account.";
      }
      // Keep only the email temporarily; passwords and OTPs never enter storage or URLs.
      sessionStorage.setItem("pending_registration_email", email.toLowerCase());
      window.location.href = "verify-registration.html";

    } catch (error) {

      console.error(
        "Register error:",
        error
      );


      if (messageBox) {

        messageBox.textContent =
          "Could not connect to backend. Check whether the backend server is running.";

      } else {

        alert(
          "Could not connect to backend. Check whether the backend server is running."
        );

      }


    } finally {

      if (registerButton) {

        registerButton.disabled = false;

        registerButton.textContent =
          "Create Account";

      }

    }

  });

}

/* =========================================================
   STUDENT REGISTRATION EMAIL VERIFICATION
   ========================================================= */

const registrationOtpForm = document.getElementById("registrationOtpForm");
if (registrationOtpForm) {
  const email = sessionStorage.getItem("pending_registration_email") || "";
  const emailLabel = document.getElementById("registrationEmailLabel");
  const otpInput = document.getElementById("registrationOtp");
  const verifyButton = document.getElementById("verifyRegistrationOtpButton");
  const resendButton = document.getElementById("resendRegistrationOtpButton");
  const messageBox = document.getElementById("messageBox");
  const resendTimer = document.getElementById("resendTimer");
  let resendCountdown = 30;

  const maskEmail = (value) => {
    const [name, domain] = value.split("@");
    if (!name || !domain) return "your email";
    return `${name.slice(0, 1)}${"•".repeat(Math.min(Math.max(name.length - 1, 2), 6))}@${domain}`;
  };

  if (!email) {
    window.location.replace("register.html");
  } else {
    if (emailLabel) emailLabel.textContent = maskEmail(email);
    otpInput?.focus();

    const updateResendCountdown = () => {
      if (!resendButton || !resendTimer) return;
      resendButton.disabled = resendCountdown > 0;
      resendTimer.textContent = resendCountdown > 0
        ? `Resend available in ${resendCountdown}s`
        : "You can request a new code.";
      if (resendCountdown > 0) {
        resendCountdown -= 1;
        window.setTimeout(updateResendCountdown, 1000);
      }
    };
    updateResendCountdown();

    otpInput?.addEventListener("input", () => {
      otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
      if (messageBox) messageBox.textContent = "";
    });

    otpInput?.addEventListener("paste", (event) => {
      const pasted = (event.clipboardData || window.clipboardData).getData("text");
      if (/^\s*\d{6}\s*$/.test(pasted)) {
        event.preventDefault();
        otpInput.value = pasted.trim();
      }
    });

    registrationOtpForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const otp = (otpInput?.value || "").trim();
      if (!/^\d{6}$/.test(otp)) {
        if (messageBox) messageBox.textContent = "Enter the 6-digit code from your email.";
        return;
      }
      verifyButton.disabled = true;
      verifyButton.textContent = "Verifying...";
      try {
        const response = await fetch(API_ENDPOINTS.verifyRegistrationOtp, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, otp }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "That code is invalid or expired.");
        if (!data.access_token) throw new Error("Verification succeeded but sign-in could not be completed. Please log in.");

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type || "bearer");
        localStorage.setItem("user_email", data.email || email);
        localStorage.setItem("user", JSON.stringify({
          name: data.name,
          email: data.email || email,
          id: data.user_id,
          role: data.role,
        }));
        localStorage.setItem("login_type", "student");
        sessionStorage.removeItem("pending_registration_email");
        window.location.replace("dashboard.html");
      } catch (error) {
        if (messageBox) messageBox.textContent = error.message || "Could not verify your email. Try again.";
      } finally {
        verifyButton.disabled = false;
        verifyButton.textContent = "Verify email";
      }
    });

    resendButton?.addEventListener("click", async () => {
      resendButton.disabled = true;
      if (messageBox) messageBox.textContent = "Sending a new code...";
      try {
        const response = await fetch(API_ENDPOINTS.resendRegistrationOtp, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          if (response.status === 429) {
            const retryAfter = Number(response.headers.get("Retry-After")) || 30;
            if (messageBox) messageBox.textContent = `Please wait ${retryAfter} seconds before requesting another code.`;
          } else {
            throw new Error(data.detail || "Could not resend the verification code.");
          }
          resendButton.disabled = false;
          return;
        }
        if (messageBox) messageBox.textContent = data.message || "A new code has been sent.";
        resendCountdown = 30;
        updateResendCountdown();
      } catch (error) {
        if (messageBox) messageBox.textContent = error.message || "Could not resend the verification code.";
        resendButton.disabled = false;
      }
    });
  }
}

/* =========================================================
   STUDENT / ADMIN LOGIN
   ========================================================= */

let selectedLoginType = "student";


/* =========================================================
   SWITCH LOGIN TYPE
   ========================================================= */

function switchLoginType(type) {

  selectedLoginType = type;

  const studentButton =
    document.getElementById("studentLoginBtn");

  const adminButton =
    document.getElementById("adminLoginBtn");

  const loginEyebrow =
    document.getElementById("loginEyebrow");

  const loginTitle =
    document.getElementById("loginTitle");

  const loginDescription =
    document.getElementById("loginDescription");

  const forgotPasswordLink =
    document.getElementById("forgotPasswordLink");

  const studentDivider =
    document.getElementById("studentDivider");

  const studentRegister =
    document.getElementById("studentRegister");

  const loginButton =
    document.getElementById("loginButton");

  const authCard =
    document.querySelector(".auth-card");


  /* ================= STUDENT ================= */

  if (type === "student") {

    if (studentButton) {
      studentButton.classList.add("active");
    }

    if (adminButton) {
      adminButton.classList.remove("active");
    }

    if (authCard) {
      authCard.classList.remove("admin-mode");
    }

    if (loginEyebrow) {
      loginEyebrow.textContent =
        "EPS TOPIK EXAM";
    }

    if (loginTitle) {
      loginTitle.textContent =
        "Welcome back";
    }

    if (loginDescription) {
      loginDescription.textContent =
        "Log in to continue your Korean language test preparation.";
    }

    if (forgotPasswordLink) {
      forgotPasswordLink.style.display =
        "inline";
    }

    if (studentDivider) {
      studentDivider.style.display =
        "flex";
    }

    if (studentRegister) {
      studentRegister.style.display =
        "block";
    }

    if (loginButton) {
      loginButton.textContent =
        "Log in";
    }

  }


  /* ================= ADMIN ================= */

  else if (type === "admin") {

    if (adminButton) {
      adminButton.classList.add("active");
    }

    if (studentButton) {
      studentButton.classList.remove("active");
    }

    if (authCard) {
      authCard.classList.add("admin-mode");
    }

    if (loginEyebrow) {
      loginEyebrow.textContent =
        "EPS TOPIK ADMIN";
    }

    if (loginTitle) {
      loginTitle.textContent =
        "Admin Portal";
    }

    if (loginDescription) {
      loginDescription.textContent =
        "Sign in to manage the EPS TOPIK examination platform.";
    }

    /*
       Keep forgot password available for admin
       for now. We can create a separate admin
       recovery flow later if required.
    */
    if (forgotPasswordLink) {
      forgotPasswordLink.style.display =
        "inline";
    }

    /*
       Admin does not need student registration.
    */
    if (studentDivider) {
      studentDivider.style.display =
        "none";
    }

    if (studentRegister) {
      studentRegister.style.display =
        "none";
    }

    if (loginButton) {
      loginButton.textContent =
        "Admin Login";
    }

  }

}
/* =========================================================
   LOGIN RETURN URL
   ========================================================= */

function getLoginReturnUrl() {
  const params = new URLSearchParams(
    window.location.search
  );

  const next = params.get("next");

  // Default destination after normal login
  if (!next) {
    return "dashboard.html";
  }

  // Prevent redirects to external websites
  if (
    next.startsWith("http://") ||
    next.startsWith("https://") ||
    next.startsWith("//") ||
    !next.startsWith("../")
  ) {
    return "dashboard.html";
  }

  return next;
}

/* =========================================================
   LOGIN FORM
   ========================================================= */

const loginForm =
  document.getElementById("loginForm");


if (loginForm) {

  loginForm.addEventListener(
    "submit",
    async function (event) {

      event.preventDefault();


      const email =
        document
          .getElementById("loginEmail")
          .value
          .trim();


      const password =
        document
          .getElementById("loginPassword")
          .value;


      const loginButton =
        document.getElementById("loginButton");


      const messageBox =
        document.getElementById("messageBox");


      if (!email || !password) {

        alert(
          "Please enter email and password."
        );

        return;
      }


      try {

        if (loginButton) {

          loginButton.disabled =
            true;

          loginButton.textContent =
            selectedLoginType === "admin"
              ? "Logging in..."
              : "Logging in...";
        }


        /* =========================================
           LOGIN REQUEST
           ========================================= */

        const response =
          await fetch(
            `${API_BASE_URL}/auth/login`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body: JSON.stringify({
                email: email,
                password: password
              })
            }
          );


        const data =
          await response.json();


        /* =========================================
           BACKEND ERROR
           ========================================= */

        if (!response.ok) {

          const errorMessage =
            data.detail ||
            data.message ||
            "Invalid email or password.";

          if (messageBox) {
            messageBox.textContent =
              errorMessage;
          }

          alert(errorMessage);

          return;
        }


        /* =========================================
           ACCESS TOKEN CHECK
           ========================================= */

        if (!data.access_token) {

          alert(
            "No access token received from backend."
          );

          return;
        }


        /* =========================================
           IMPORTANT:
           CHECK THE REAL BACKEND ROLE
           ========================================= */

        const backendRole =
          String(data.role || "")
            .toLowerCase()
            .trim();


        /*
           ADMIN LOGIN SELECTED
           BUT ACCOUNT IS NOT ADMIN
        */

        if (
          selectedLoginType === "admin" &&
          backendRole !== "admin"
        ) {

          alert(
            "Access denied. This account is not an admin account."
          );

          return;
        }


        /*
           STUDENT LOGIN SELECTED
           BUT ACCOUNT IS ADMIN
        */

        if (
          selectedLoginType === "student" &&
          backendRole === "admin"
        ) {

          alert(
            "Please use the Admin login option for this account."
          );

          return;
        }


        /* =========================================
           SAVE LOGIN INFORMATION
           ========================================= */

        localStorage.setItem(
          "access_token",
          data.access_token
        );


        localStorage.setItem(
          "token_type",
          data.token_type || "bearer"
        );


        localStorage.setItem(
          "user_email",
          email
        );


        localStorage.setItem(
          "user",
          JSON.stringify({

            name:
              data.name,

            email:
              data.email || email,

            id:
              data.user_id,

            role:
              data.role

          })
        );


        /* =========================================
           SAVE LOGIN TYPE
           ========================================= */

        localStorage.setItem(
          "login_type",
          selectedLoginType
        );


        /* =========================================
           REDIRECT
           ========================================= */

        if (backendRole === "admin") {

          alert(
            "Admin login successful!"
          );

          /*
             CHANGE THIS PATH IF YOUR ADMIN
             DASHBOARD HAS A DIFFERENT LOCATION.
          */

          window.location.href =
            "admin/admin.html";

        }
else {
  window.location.href =
    getLoginReturnUrl();
}

      }


      catch (error) {

        console.error(
          "Login error:",
          error
        );


        alert(
          "Could not connect to backend. Check whether the backend server is running."
        );

      }


      finally {

        if (loginButton) {

          loginButton.disabled =
            false;

          loginButton.textContent =
            selectedLoginType === "admin"
              ? "Admin Login"
              : "Log in";

        }

      }

    }
  );

}

/* =========================================================
   PASSWORD RECOVERY
   ========================================================= */

const sendOtpButton = document.getElementById("sendOtpButton");

if (sendOtpButton) {
  sendOtpButton.addEventListener("click", async function () {
    const email = document.getElementById("forgotEmail").value.trim();
    const messageBox = document.getElementById("messageBox");
    if (!email) {
      messageBox.textContent = "Enter your registered email address.";
      return;
    }
    sendOtpButton.disabled = true;
    try {
      await window.EPS_API.auth.forgotPassword({ email });
      localStorage.setItem("password_reset_email", email);
      window.location.href = "verify-otp.html";
    } catch (error) {
      messageBox.textContent = error.message || "Unable to send an OTP.";
    } finally {
      sendOtpButton.disabled = false;
    }
  });
}

const verifyOtpForm = document.getElementById("verifyOtpForm");

if (verifyOtpForm) {
  verifyOtpForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const email = localStorage.getItem("password_reset_email");
    const otp = document.getElementById("otp").value.trim();
    const messageBox = document.getElementById("messageBox");
    if (!email) {
      messageBox.textContent = "Restart password recovery and enter your email address.";
      return;
    }
    try {
      await window.EPS_API.auth.verifyOtp({ email, otp });
      localStorage.setItem("password_reset_otp", otp);
      window.location.href = "reset-pass.html";
    } catch (error) {
      messageBox.textContent = error.message || "Unable to verify the OTP.";
    }
  });
}


/* =========================================================
   SET SELECTION BACK BUTTON
   ========================================================= */

const backBtn =
  document.getElementById("backBtn");

if (backBtn) {

  backBtn.addEventListener("click", function () {

    window.location.href =
      "set.html";

  });

}


/* =========================================================
   DASHBOARD TEST BUTTON
   ========================================================= */

function startTest(setId, examId) {

    console.log("START TEST");
    console.log("Exam ID:", examId);
    console.log("Set ID:", setId);

    if (!setId || !examId) {

        console.error(
            "Missing exam ID or set ID:",
            {
                examId: examId,
                setId: setId
            }
        );

        alert(
            "Unable to start test. Exam ID or Set ID is missing."
        );

        return;
    }

    window.location.href =
        `exam.html?exam=${encodeURIComponent(examId)}&set=${encodeURIComponent(setId)}`;
}

/* =========================================================
   PROFILE BUTTON
   ========================================================= */

function editProfile() {

  window.location.href =
    "profile.html";
}


/* =========================================================
   SUBSCRIPTION BUTTON
   ========================================================= */

function startSubscription() {

  alert(
    "Payment gateway will be connected here."
  );

}


/* =========================================================
   LOGOUT
   ========================================================= */

function logout() {

  const confirmLogout =
    confirm("Are you sure you want to logout?");


  if (!confirmLogout) {
    return;
  }


  localStorage.removeItem(
    "access_token"
  );

  localStorage.removeItem(
    "token_type"
  );

  localStorage.removeItem(
    "user_email"
  );


  window.location.href =
    "login.html";
}
/* =========================================================
   EXAM RESULT PAGE
   ========================================================= */


/* ================= REVIEW ANSWERS ================= */

function reviewAnswers() {

  window.location.href =
    "review-answers.html";
}


/* ================= RETAKE TEST ================= */

function retakeTest() {

  const confirmRetake =
    confirm(
      "Do you want to retake this test?"
    );


  if (!confirmRetake) {
    return;
  }


  /*
     Change exam.html if your exam page
     uses another filename.
  */

  window.location.href =
    "exam.html";
}


/* ================= DASHBOARD ================= */

function goToDashboard() {

  window.location.href =
    "dashboard.html";
}


/* ================= DOWNLOAD RESULT ================= */

function downloadResult() {

  const testName =
    document.getElementById(
      "resultTestName"
    )?.textContent || "EPS TOPIK Test";


  const percentage =
    document.getElementById(
      "resultPercentage"
    )?.textContent || "-";


  const score =
    document.getElementById(
      "resultScore"
    )?.textContent || "-";


  const correct =
    document.getElementById(
      "correctAnswers"
    )?.textContent || "-";


  const wrong =
    document.getElementById(
      "wrongAnswers"
    )?.textContent || "-";


  const unanswered =
    document.getElementById(
      "unansweredAnswers"
    )?.textContent || "-";


  const resultText = `
EPS TOPIK EXAM RESULT

Test: ${testName}

Score: ${score}
Percentage: ${percentage}

Correct Answers: ${correct}
Incorrect Answers: ${wrong}
Unanswered: ${unanswered}

EPS TOPIK Exam Platform
`;


  const file =
    new Blob(
      [resultText],
      {
        type: "text/plain"
      }
    );


  const url =
    URL.createObjectURL(file);


  const link =
    document.createElement("a");


  link.href = url;

  link.download =
    "EPS-TOPIK-Result.txt";


  document.body.appendChild(link);

  link.click();


  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}
/* =========================================================
   LOAD DASHBOARD USER PROFILE FROM BACKEND
   ========================================================= */

async function loadDashboardUserProfile() {

    // Only run on dashboard
    const profileName =
        document.getElementById("sidebarUserName");

    const profileId =
        document.getElementById("sidebarStudentId");

    const profileAvatar =
        document.getElementById("profileAvatar");

    // If these elements don't exist,
    // this is not the dashboard page.
    if (
        !profileName &&
        !profileId &&
        !profileAvatar
    ) {
        return;
    }

    const token =
        localStorage.getItem("access_token");

    if (!token) {
        console.warn(
            "No access token found."
        );
        return;
    }

    try {

        const response =
            await fetch(
                API_ENDPOINTS.profile,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`,

                        "Content-Type":
                            "application/json"
                    }
                }
            );

        if (!response.ok) {

            throw new Error(
                `Profile request failed: ${response.status}`
            );

        }

        const user =
            await response.json();

        console.log(
            "Logged-in user profile:",
            user
        );


        /* =================================================
           NAME
        ================================================= */

        const name =
            user.name ||
            user.full_name ||
            user.fullName ||
            "Student";

        if (profileName) {

            profileName.textContent =
                name;

        }


        /* =================================================
           STUDENT ID
        ================================================= */

        const studentId =
            user.student_id ||
            user.studentId ||
            user.roll_no ||
            user.rollNo ||
            "";

        if (profileId) {

            profileId.textContent =
                studentId;

        }


        /* =================================================
           INITIALS
        ================================================= */

        if (profileAvatar) {

            const parts =
                name
                    .trim()
                    .split(/\s+/);

            let initials = "";

            if (parts.length === 1) {

                initials =
                    parts[0]
                        .substring(0, 2)
                        .toUpperCase();

            } else {

                initials =
                    (
                        parts[0][0] +
                        parts[parts.length - 1][0]
                    ).toUpperCase();

            }

            profileAvatar.textContent =
                initials;

        }


        /* =================================================
           NAVBAR
        ================================================= */

        const navName =
            document.getElementById(
                "navUserName"
            );

        const navStudentId =
            document.getElementById(
                "navStudentId"
            );

        const navAvatar =
            document.getElementById(
                "navUserAvatar"
            );


        if (navName) {

            navName.textContent =
                name;

        }

        if (navStudentId) {

            navStudentId.textContent =
                studentId;

        }

        if (navAvatar) {

            const parts =
                name
                    .trim()
                    .split(/\s+/);

            let initials = "";

            if (parts.length === 1) {

                initials =
                    parts[0]
                        .substring(0, 2)
                        .toUpperCase();

            } else {

                initials =
                    (
                        parts[0][0] +
                        parts[parts.length - 1][0]
                    ).toUpperCase();

            }

            navAvatar.textContent =
                initials;

        }

    } catch (error) {

        console.error(
            "Could not load dashboard profile:",
            error
        );

    }
}


/* =========================================================
   START DASHBOARD PROFILE
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const dashboardElement =
        document.getElementById("sidebarUserName");

    // Run only on the dashboard page
    if (dashboardElement) {
        loadDashboardProfile();
    }

});
/* =========================================================
   LOAD LOGGED-IN STUDENT PROFILE
   ========================================================= */

async function loadDashboardProfile() {

    const nameElement =
        document.getElementById("sidebarUserName");

    const studentIdElement =
        document.getElementById("sidebarStudentId");

    const avatarElement =
        document.getElementById("profileAvatar");

    const navNameElement =
        document.getElementById("navUserName");

    const navStudentIdElement =
        document.getElementById("navStudentId");

    const navAvatarElement =
        document.getElementById("navUserAvatar");

    const welcomeNameElement =
        document.getElementById("dashboardUserName");


    // Make sure this code only runs on the dashboard
    if (
        !nameElement &&
        !studentIdElement &&
        !avatarElement
    ) {
        return;
    }


    // Get JWT token created during login
    const token =
        localStorage.getItem("access_token");

    if (!token) {

        console.error(
            "No access token found."
        );

        return;
    }


    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/profile`,
            {
                method: "GET",

                headers: {
                    "Authorization":
                        `Bearer ${token}`,

                    "Content-Type":
                        "application/json"
                }
            }
        );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Profile API error:",
                response.status,
                errorText
            );

            return;
        }


        const user =
            await response.json();


        console.log(
            "PROFILE FROM BACKEND:",
            user
        );


        /* =================================================
           GET NAME
        ================================================= */

        const name =
            user.name ||
            user.full_name ||
            user.fullName ||
            "Student";


        /* =================================================
           GET STUDENT ID
        ================================================= */

        const studentId =
            user.student_id ||
            user.studentId ||
            user.roll_no ||
            user.rollNo ||
            "";


        /* =================================================
           DASHBOARD PROFILE CARD
        ================================================= */

        if (nameElement) {

            nameElement.textContent =
                name;

        }


        if (studentIdElement) {

            studentIdElement.textContent =
                studentId;

        }


        if (avatarElement) {

            avatarElement.textContent =
                getUserInitials(name);

        }

        /* =================================================
           NAVBAR
        ================================================= */

        if (navNameElement) {

            navNameElement.textContent =
                name;

        }


        if (navStudentIdElement) {

            navStudentIdElement.textContent =
                studentId;

        }


        if (navAvatarElement) {

            navAvatarElement.textContent =
                getUserInitials(name);

        }


        /* =================================================
           WELCOME MESSAGE
        ================================================= */

        if (welcomeNameElement) {

            welcomeNameElement.textContent =
                name;

        }

    } catch (error) {

        console.error(
            "Failed to load student profile:",
            error
        );

    }
}


/* =========================================================
   DASHBOARD PROGRESS
   ========================================================= */

function renderDashboardProgress(progress) {

    if (!progress) {
        return;
    }

    /* Progress percentage */

    const percentage =
        document.getElementById(
            "progressPercentage"
        );

    if (percentage) {

        percentage.textContent =
            `${Number(
                progress.percentage || 0
            ).toFixed(0)}%`;

    }


    /* Tests completed */

    const completed =
        document.getElementById(
            "progressTestsCompleted"
        );

    if (completed) {

        completed.textContent =
            `${progress.completed || 0} / ${progress.total || 0}`;

    }


    /* Average score */

    const average =
        document.getElementById(
            "progressAverageScore"
        );

    if (average) {

        average.textContent =
            `${Number(
                progress.average_score || 0
            ).toFixed(1)}%`;

    }

}

/* =========================================================
   STUDENT DASHBOARD DATA
   ========================================================= */

async function loadStudentDashboard() {

    // Make sure we are on dashboard page
    const dashboard =
        document.getElementById("tests");

    if (!dashboard) {
        return;
    }

    const token =
        localStorage.getItem("access_token");

    if (!token) {
        console.error(
            "No access token found."
        );
        return;
    }

    try {

        /*
         * The old dashboard endpoint:
         *
         * /student/dashboard
         *
         * does not exist.
         *
         * Use the working quiz endpoint instead.
         */

        const response =
            await fetch(
                `${API_BASE_URL}/api/quizzes`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`,

                        "Content-Type":
                            "application/json"
                    }
                }
            );

        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Quiz API error:",
                response.status,
                errorText
            );

            return;
        }

        const quizzes =
            await response.json();

        console.log(
            "QUIZZES FROM BACKEND:",
            quizzes
        );


        /*
         * Convert:
         *
         * quiz -> sets
         *
         * into the format expected by
         * renderAvailableTests().
         */

        const tests = [];

        quizzes.forEach(function (quiz) {

            if (!quiz.sets) {
                return;
            }

            quiz.sets.forEach(function (set) {

                tests.push({

                    id: set.id,

                    exam_id: quiz.id,

                    title: quiz.title,

                    set_number:
                        set.set_number,

                    set_name:
                        set.set_name,

                    is_free:
                        true,

                    total_questions:
                        quiz.total_questions || 0,

                    reading_questions:
                        0,

                    listening_questions:
                        0

                });

            });

        });


        console.log(
            "TESTS FOR STUDENT DASHBOARD:",
            tests
        );


        /*
         * Display available tests.
         */

        renderAvailableTests(
            tests
        );


        /*
         * Keep the existing dashboard
         * functions safe.
         *
         * These values are not provided by
         * /api/quizzes, so do not send
         * undefined data into them.
         */
       const dashboardResponse = await fetch(
    `${API_BASE_URL}/api/student/dashboard`,
    {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    }
);

if (!dashboardResponse.ok) {
    const errorText = await dashboardResponse.text();

    console.error(
        "Student dashboard API error:",
        dashboardResponse.status,
        errorText
    );

    return;
}

const dashboardData = await dashboardResponse.json();

console.log(
    "STUDENT DASHBOARD DATA:",
    dashboardData
);

renderDashboardStats(
    dashboardData.stats
);

renderDashboardProgress(
    dashboardData.progress
);

renderRecentResults(
    dashboardData.recent_results
);

    } catch (error) {

        console.error(
            "Failed to load student dashboard:",
            error
        );

    }

}


/* =========================================================
   RECENT RESULTS
   ========================================================= */

function renderRecentResults(results) {

    const container =
        document.getElementById(
            "recentResultsBody"
        );

    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!results || results.length === 0) {

        container.innerHTML = `
            <div class="result-row">

                <span>
                    No tests completed yet.
                </span>

                <span>-</span>

                <strong>-</strong>

                <span>-</span>

            </div>
        `;

        return;
    }


    results.forEach(function (result) {

        const row =
            document.createElement("div");

        row.className =
            "result-row";


        const score =
            Number(
                result.percentage || 0
            ).toFixed(1);


        row.innerHTML = `

            <span>
                ${escapeStudentHtml(result.test_name || "-")}
            </span>

            <span>
                ${formatDashboardDate(
                    result.date
                )}
            </span>

            <strong>
                ${score}%
            </strong>

            <span class="${
                result.result === "Passed"
                    ? "passed"
                    : ""
            }">
                ${escapeStudentHtml(result.result || "-")}
            </span>

        `;


        container.appendChild(row);

    });

}
function formatDashboardDate(dateString) {

    if (!dateString) {
        return "-";
    }


    const date =
        new Date(dateString);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return dateString;
    }


    return date.toLocaleDateString(
        "en-GB",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );

}
        /* =========================================================
   AVAILABLE TESTS
   ========================================================= */
function renderAvailableTests(tests) {

    const container =
        document.getElementById(
            "availableTestsList"
        );

    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!tests || tests.length === 0) {

        container.innerHTML = `
            <p style="
                text-align: center;
                padding: 30px;
            ">
                No tests available.
            </p>
        `;

        return;
    }


    tests.forEach(function (test) {

        const card =
            document.createElement("article");

        card.className =
            "test-card";


        const setNumber =
            String(
                test.set_number
            ).padStart(2, "0");


        card.innerHTML = `

            <div class="test-number">
                ${setNumber}
            </div>


            <div class="test-details">

                <div class="test-title-row">

                    <h4>
                        Set No. ${setNumber}
                    </h4>

                    ${
                        test.is_free
                            ? `
                                <span class="free-badge">
                                    FREE
                                </span>
                              `
                            : `
                                <span class="locked-badge">
                                    AVAILABLE
                                </span>
                              `
                    }

                </div>


                <p>
                ${escapeStudentHtml(test.set_name || "")}
                </p>


                <div class="test-meta">

                    <span>
                        ${test.total_questions || 0}
                        Questions
                    </span>

                    <span>
                        ${test.reading_questions || 0}
                        Reading
                    </span>

                    <span>
                        ${test.listening_questions || 0}
                        Listening
                    </span>

                </div>

            </div>


            <button
                type="button"
                class="test-button"
            >
                Start Test
            </button>

        `;


        const button =
            card.querySelector(
                ".test-button"
            );


        button.addEventListener(
            "click",
            function () {

                startTest(
                    test.id,
                    test.exam_id
                );

            }
        );


        container.appendChild(card);

    });

}

        /* =========================================================
   DASHBOARD STATISTICS
   ========================================================= */

function renderDashboardStats(stats) {

    /* Tests Completed */

    const testsCompleted =
        document.getElementById(
            "testsCompleted"
        );

    if (testsCompleted) {

        testsCompleted.textContent =
            stats.tests_completed ?? 0;

    }


    /* Average Score */

    const averageScore =
        document.getElementById(
            "averageScore"
        );

    if (averageScore) {

        averageScore.textContent =
            `${Number(
                stats.average_score || 0
            ).toFixed(1)}%`;

    }


    /* Best Score */

    const bestScore =
        document.getElementById(
            "bestScore"
        );

    if (bestScore) {

        bestScore.textContent =
            `${Number(
                stats.best_score || 0
            ).toFixed(1)}%`;

    }


    /* Tests Available */

    const testsAvailable =
        document.getElementById(
            "testsAvailable"
        );

    if (testsAvailable) {

        testsAvailable.textContent =
            stats.tests_available ?? 0;

    }

}


/* =========================================================
   CREATE INITIALS
   ========================================================= */

function getUserInitials(name) {

    const parts =
        name
            .trim()
            .split(/\s+/);


    if (parts.length === 1) {

        return parts[0]
            .substring(0, 2)
            .toUpperCase();

    }


    return (
        parts[0][0] +
        parts[parts.length - 1][0]
    ).toUpperCase();

}

/* =========================================================
   START PROFILE LOADING
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadDashboardProfile();

    }
);
/* =========================================================
   LOAD LOGGED-IN USER ON DASHBOARD
========================================================= */

function loadDashboardUser() {

    const savedUser =
        localStorage.getItem("user");

    console.log("Saved login user:", savedUser);

    if (!savedUser) {

        console.warn(
            "No logged-in user found in localStorage."
        );

        return;
    }

    try {

        const user =
            JSON.parse(savedUser);

        console.log(
            "Dashboard user:",
            user
        );


        /* =========================
           NAME
        ========================= */

        const name =
            user.name ||
            "Student";


        /* =========================
           STUDENT ID
        ========================= */

        const studentId =
            user.student_id ||
            user.studentId ||
            user.roll_no ||
            user.rollNo ||
            user.id ||
            "";


        /* =========================
           INITIALS
        ========================= */

        let initials = "ST";

        const parts =
            name
                .trim()
                .split(/\s+/);

        if (parts.length === 1) {

            initials =
                parts[0]
                    .substring(0, 2)
                    .toUpperCase();

        } else {

            initials =
                (
                    parts[0][0] +
                    parts[parts.length - 1][0]
                ).toUpperCase();

        }


        /* =========================
           WELCOME MESSAGE
        ========================= */

        const welcome =
            document.getElementById(
                "dashboardUserName"
            );

        if (welcome) {
            welcome.textContent = name;
        }


        /* =========================
           NAVBAR
        ========================= */

        const navName =
            document.getElementById(
                "navUserName"
            );

        const navId =
            document.getElementById(
                "navStudentId"
            );

        const navAvatar =
            document.getElementById(
                "navUserAvatar"
            );

        if (navName) {
            navName.textContent = name;
        }

        if (navId) {
            navId.textContent = studentId;
        }

        if (navAvatar) {
            navAvatar.textContent = initials;
        }


        /* =========================
           STUDENT PROFILE CARD
        ========================= */

        const profileName =
            document.getElementById(
                "sidebarUserName"
            );

        const profileId =
            document.getElementById(
                "sidebarStudentId"
            );

        const profileAvatar =
            document.getElementById(
                "profileAvatar"
            );

        if (profileName) {
            profileName.textContent = name;
        }

        if (profileId) {
            profileId.textContent = studentId;
        }

        if (profileAvatar) {
            profileAvatar.textContent = initials;
        }

    } catch (error) {

        console.error(
            "Could not read logged-in user:",
            error
        );

    }
}


/* =========================================================
   RUN ON DASHBOARD
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadDashboardUser();

        loadStudentDashboard();

    }
);

/* =========================================================
   DYNAMIC STUDENT EXAM
   Loads questions from FastAPI
   ========================================================= */

let studentExamQuestions = [];
let currentExamQuestionIndex = 0;
let selectedAnswers = {};

let studentAttemptId = null;
let examExpiresAt = null;
let examTimerInterval = null;
let examTimerSyncInterval = null;
let timerStatusAbortController = null;

function updateExamStats() {
    const solvedElement = document.getElementById("solved");
    const unsolvedElement = document.getElementById("unsolved");

    const total = studentExamQuestions.length;
    const solved = Object.keys(selectedAnswers).length;
    const unsolved = total - solved;

    if (solvedElement) {
        solvedElement.textContent = solved;
    }
 if (unsolvedElement) {
        unsolvedElement.textContent = unsolved;
    }
}
/* =========================================================
   TIMER 
   ========================================================= */
function formatExamTime(totalSeconds) {

    const seconds =
        Math.max(
            0,
            Math.floor(totalSeconds)
        );

    const minutes =
        Math.floor(seconds / 60);

    const remainingSeconds =
        seconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}


function updateExamTimerDisplay(seconds) {

    const timer =
        document.getElementById("timer");

    if (!timer) {
        return;
    }

    timer.textContent =
        formatExamTime(seconds);
}


function startBackendExamTimer() {

    if (!examExpiresAt) {
        return;
    }

    if (examTimerInterval) {
        clearInterval(examTimerInterval);
    }

    if (examTimerSyncInterval) {
        clearInterval(examTimerSyncInterval);
    }

    function updateTimer() {

        const now =
            Date.now() / 1000;

        const remaining =
            Math.max(
                0,
                Math.floor(
                    examExpiresAt - now
                )
            );

        updateExamTimerDisplay(
            remaining
        );

        if (remaining <= 0) {

            clearInterval(
                examTimerInterval
            );

            clearInterval(
                examTimerSyncInterval
            );

            examTimerInterval = null;
            examTimerSyncInterval = null;

            handleExamTimeExpired();
        }
    }

    updateTimer();

    examTimerInterval =
        setInterval(
            updateTimer,
            1000
        );

    examTimerSyncInterval =
        setInterval(
            refreshBackendExamTimer,
            10000
        );
}

async function refreshBackendExamTimer() {

    if (!studentAttemptId) {
        return;
    }

    const token =
        localStorage.getItem("access_token");

    if (!token) {
        return;
    }

    const apiBase =
        window.EPS_API?.baseUrl ||
        window.API_BASE_URL;

    if (timerStatusAbortController) {
        return;
    }

    timerStatusAbortController = new AbortController();
    try {

        const response =
            await fetch(
                `${apiBase}/api/attempts/${encodeURIComponent(studentAttemptId)}/status`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`,

                        "Content-Type":
                            "application/json"
                    },
                    signal: timerStatusAbortController.signal
                }
            );

        if (!response.ok) {
            console.error(
                "Timer status error:",
                response.status
            );
            return;
        }

        const status =
            await response.json();

        console.log(
            "SERVER TIMER:",
            status
        );

        updateExamTimerDisplay(
            status.time_remaining_seconds
        );

        if (
            status.status !==
            "in_progress"
        ) {

           if (status.status !== "in_progress") {

    clearInterval(examTimerInterval);
    clearInterval(examTimerSyncInterval);

    examTimerInterval = null;
    examTimerSyncInterval = null;

    if (status.time_remaining_seconds <= 0) {
        handleExamTimeExpired();
    }
}
            if (
                status.time_remaining_seconds <= 0
            ) {
                handleExamTimeExpired();
            }
        }

    } catch (error) {

        if (error.name !== "AbortError") {
            console.error(
                "Failed to refresh server timer:",
                error
            );
        }
    } finally {
        timerStatusAbortController = null;
    }
}

function handleExamTimeExpired() {

    alert(
        "Your exam time has expired. Your attempt will be submitted."
    );

    submitExamToBackend(true);
}




/* =========================================================
   LOAD QUESTIONS
   ========================================================= */

async function loadStudentExamQuestions() {

    const optionsContainer =
        document.getElementById("options");

    if (!optionsContainer) {
        return;
    }

    const params = new URLSearchParams(window.location.search);

const examId = params.get("exam");
const setId = params.get("set");
const setNumberElement =
    document.getElementById("setNumber");

if (setNumberElement) {
    setNumberElement.textContent =
        setId ? String(setId).padStart(2, "0") : "--";
}

    if (!setId) {
        console.error("No exam set ID found in URL.");
        optionsContainer.innerHTML =
            "<p>Exam set was not selected.</p>";
        return;
    }

    const token =
        localStorage.getItem("access_token");

    if (!token) {
        console.error("No access token found.");

        window.location.href =
            `login.html?next=${encodeURIComponent(
                window.location.pathname +
                window.location.search
            )}`;

        return;
    }

    const apiBase =
        window.EPS_API?.baseUrl ||
        window.API_BASE_URL;

    try {

        /* =========================================
           STEP 1 â€” START / RESUME ATTEMPT
           ========================================= */

        console.log(
            "Starting exam attempt for:",
            setId
        );

console.log("========== EXAM START DEBUG ==========");
console.log("API Base:", apiBase);
console.log("Exam ID:", examId);
console.log("Set ID:", setId);
console.log("Token exists:", !!token);
console.log(
    "Start URL:",
    `${apiBase}/api/attempts/start/${encodeURIComponent(examId)}?set_id=${encodeURIComponent(setId)}`
);
console.log("======================================");


       const startResponse = await fetch(
    `${apiBase}/api/attempts/start/${encodeURIComponent(examId)}?set_id=${encodeURIComponent(setId)}`,
    {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    }
);

        if (!startResponse.ok) {

            const errorText =
                await startResponse.text();

            console.error(
                "Start attempt error:",
                startResponse.status,
                errorText
            );

            throw new Error(
                `Unable to start exam (${startResponse.status})`
            );
        }

        const started =
            await startResponse.json();

        console.log(
            "ATTEMPT STARTED:",
            started
        );

        /* =========================================
           SAVE ATTEMPT INFORMATION
           ========================================= */

        studentAttemptId =
            started.attempt_id;

        examExpiresAt =
            Number(started.expires_at);

        if (!studentAttemptId) {
            throw new Error(
                "Backend did not return an attempt ID."
            );
        }

        if (!examExpiresAt) {
            throw new Error(
                "Backend did not return an exam expiry time."
            );
        }

        console.log(
            "Attempt ID:",
            studentAttemptId
        );

        console.log(
    "Expires at:",
    examExpiresAt
);


/* =========================================
   STEP 2 â€” START BACKEND TIMER
   ========================================= */

startBackendExamTimer();
    


        /* =========================================
           STEP 3 â€” LOAD QUESTIONS FOR ATTEMPT
           ========================================= */

console.log("========== QUESTIONS DEBUG ==========");
console.log("API Base:", apiBase);
console.log("Exam ID:", examId);
console.log("Set ID:", setId);
console.log(
    "Questions URL:",
    `${apiBase}/api/exam-sets/${encodeURIComponent(setId)}/questions`
);
console.log("Token exists:", !!token);
console.log("=====================================");

const questionsUrl =
    `${apiBase}/api/exam-sets/${encodeURIComponent(setId)}/questions`;
const questionPageSize = 200;
const questionHeaders = {
    "Authorization": `Bearer ${token}`
};

const fetchQuestionPage = async (offset) => {
    const pageResponse = await fetch(
        `${questionsUrl}?limit=${questionPageSize}&offset=${offset}`,
        { method: "GET", headers: questionHeaders }
    );

    if (!pageResponse.ok) {
        const errorText = await pageResponse.text();
        console.error(
            "Exam questions API error:",
            pageResponse.status,
            errorText
        );
        throw new Error(
            `Unable to load exam questions (${pageResponse.status})`
        );
    }

    const totalHeader = pageResponse.headers.get("X-Total-Count");
    return {
        questions: await pageResponse.json(),
        total: totalHeader === null ? NaN : Number(totalHeader)
    };
};

const firstQuestionPage = await fetchQuestionPage(0);
const allQuestions = Array.isArray(firstQuestionPage.questions)
    ? [...firstQuestionPage.questions]
    : (firstQuestionPage.questions.questions || []);
const questionCount = Number.isFinite(firstQuestionPage.total)
    ? firstQuestionPage.total
    : NaN;

if (Number.isFinite(questionCount)) {
    // Fetch later pages in small parallel batches to keep large sets quick
    // without opening an unbounded number of requests at once.
    for (
        let offset = questionPageSize;
        offset < questionCount;
        offset += questionPageSize * 4
    ) {
        const offsets = [];
        for (let batchOffset = offset;
            batchOffset < questionCount &&
            batchOffset < offset + questionPageSize * 4;
            batchOffset += questionPageSize
        ) {
            offsets.push(batchOffset);
        }

        const pages = await Promise.all(
            offsets.map((pageOffset) => fetchQuestionPage(pageOffset))
        );
        pages.forEach((page) => {
            if (Array.isArray(page.questions)) {
                allQuestions.push(...page.questions);
            } else if (Array.isArray(page.questions.questions)) {
                allQuestions.push(...page.questions.questions);
            }
        });
    }
} else {
    // Compatibility fallback for older API deployments that don't expose
    // the pagination count header yet.
    const seenQuestionIds = new Set(
        allQuestions.map((question) => String(question.id))
    );
    let offset = allQuestions.length;
    while (offset > 0) {
        const page = await fetchQuestionPage(offset);
        const questions = Array.isArray(page.questions)
            ? page.questions
            : (page.questions.questions || []);
        if (questions.length === 0) break;
        const newQuestions = questions.filter((question) => {
            const id = String(question.id);
            if (seenQuestionIds.has(id)) return false;
            seenQuestionIds.add(id);
            return true;
        });
        if (newQuestions.length === 0) break;
        allQuestions.push(...newQuestions);
        if (questions.length < questionPageSize) break;
        offset += questions.length;
    }
}

        console.log(
            "QUESTIONS FROM ATTEMPT API:",
            allQuestions
        );

        studentExamQuestions = allQuestions;

        if (
            studentExamQuestions.length === 0
        ) {
            throw new Error(
                "No questions found for this exam."
            );
        }

        currentExamQuestionIndex = 0;

        renderStudentExamQuestion();

    } catch (error) {

        console.error(
            "Failed to start/load exam:",
            error
        );

        optionsContainer.innerHTML = `
            <p style="color:red;">
                ${escapeStudentHtml(error.message)}
            </p>
        `;
    }
}

/* =========================================================
   RENDER CURRENT QUESTION
   ========================================================= */

function resolveStudentMediaUrl(value) {
    const source = String(value || "").trim();
    if (!source) return "";
    if (/^(?:data:|blob:|https?:\/\/)/i.test(source)) return source;

    const apiBase = window.EPS_API?.baseUrl || window.API_BASE_URL || window.location.origin;
    try {
        return new URL(source, `${apiBase.replace(/\/+$/, "")}/`).href;
    } catch (error) {
        console.warn("Could not resolve exam media URL:", error);
        return source;
    }
}

let activeExamAudioElement = null;
let activeExamAudioQuestionId = null;

async function playExamAudio(questionId, audioElement, button, statusElement) {
    if (!audioElement?.src) return;

    if (activeExamAudioElement === audioElement && !audioElement.paused) {
        audioElement.pause();
        button.textContent = "▶";
        if (statusElement) statusElement.textContent = "Audio paused";
        return;
    }

    // Pausing and resuming the same clip counts as one play; replaying a finished clip counts again.
    if (audioElement._authorizedPlayback && audioElement.paused && !audioElement.ended) {
        try {
            await audioElement.play();
            button.textContent = "⏸";
            if (statusElement) statusElement.textContent = "Playing audio";
        } catch (error) {
            if (statusElement) statusElement.textContent = "Tap play to start the audio.";
        }
        return;
    }

    const attemptId = studentAttemptId;
    const token = localStorage.getItem("access_token");
    if (!attemptId || !token) {
        if (statusElement) statusElement.textContent = "Your exam session is unavailable. Reload the exam.";
        return;
    }

    button.disabled = true;
    if (statusElement) statusElement.textContent = "Checking audio access…";

    try {
        const response = await fetch(
            `${window.API_BASE_URL}/api/attempts/${encodeURIComponent(attemptId)}/audio-play`,
            {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ question_id: String(questionId) })
            }
        );
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.allowed === false) {
            throw new Error(data.detail || "The allowed audio plays for this question have been used.");
        }

        if (activeExamAudioElement && activeExamAudioElement !== audioElement) {
            activeExamAudioElement.pause();
        }
        activeExamAudioElement = audioElement;
        activeExamAudioQuestionId = String(questionId);
        audioElement._authorizedPlayback = true;
        audioElement.onended = function () {
            audioElement._authorizedPlayback = false;
            button.textContent = "▶";
            if (statusElement) statusElement.textContent = "Audio finished";
        };
        await audioElement.play();
        button.textContent = "⏸";
        if (statusElement) {
            statusElement.textContent = `${data.plays_remaining} replay${data.plays_remaining === 1 ? "" : "s"} remaining`;
        }
    } catch (error) {
        audioElement._authorizedPlayback = false;
        button.textContent = "▶";
        if (statusElement) statusElement.textContent = error.message || "Unable to play this audio.";
    } finally {
        button.disabled = false;
    }
}

function renderStudentExamQuestion() {

    const question =
        studentExamQuestions[
            currentExamQuestionIndex
        ];

    if (!question) {
        return;
    }

    if (activeExamAudioElement && activeExamAudioQuestionId !== String(question.id)) {
        activeExamAudioElement.pause();
        activeExamAudioElement = null;
        activeExamAudioQuestionId = null;
    }


    /* =========================
       QUESTION NUMBER
       ========================= */

    const title =
        document.getElementById("qTitle");

    if (title) {

        title.textContent =
            `${question.question_number}.`;
    }


    /* =========================
       QUESTION GROUP
       ========================= */

    const group =
        document.getElementById("group");

    if (group) {

        group.textContent =
            question.question_type || "";
    }


    /* =========================
       QUESTION TEXT
       ========================= */

    const prompt =
        document.getElementById("prompt");

    if (prompt) {

    prompt.textContent =
        question.text || "";

}


    /* =========================
       QUESTION IMAGE
       ========================= */

    const image =
        document.getElementById("mediaImage");

    if (image) {

        if (question.image_url) {

            image.onerror = function () {
                image.classList.add("hidden");
                image.removeAttribute("src");
            };
            image.src = resolveStudentMediaUrl(question.image_url);

            image.classList.remove(
                "hidden"
            );

        } else {

            image.src = "";

            image.classList.add(
                "hidden"
            );
        }
    }


    /* =========================
       QUESTION AUDIO
       ========================= */

    const audioPlaceholder =
        document.getElementById(
            "audioPlaceholder"
        );

    if (audioPlaceholder) {

        if (question.audio_url) {

            audioPlaceholder.classList.remove(
                "hidden"
            );

        } else {

            audioPlaceholder.classList.add(
                "hidden"
            );
        }
    }

    const questionAudio = document.getElementById("questionAudio");
    if (questionAudio) {
        const audioUrl = question.audio_url
            ? resolveStudentMediaUrl(question.audio_url)
            : "";
        if (questionAudio._examSource !== audioUrl) {
            questionAudio.pause();
            questionAudio._examSource = audioUrl;
            questionAudio.src = audioUrl;
            if (audioUrl) questionAudio.load();
            else questionAudio.removeAttribute("src");
        }
    }


    /* =========================
       OPTIONS
       ========================= */

    renderStudentExamOptions(
        question
    );


    /* =========================
       TOTAL QUESTIONS
       ========================= */

    const totalQuestions =
        document.getElementById(
            "totalQuestions"
        );

    if (totalQuestions) {

        totalQuestions.textContent =
            studentExamQuestions.length;
    }


    const sectionTotal =
        document.getElementById(
            "sectionTotal"
        );

    if (sectionTotal) {

        sectionTotal.textContent =
            `Total Questions: ${studentExamQuestions.length}`;
    }


    /* =========================
       NAVIGATION
       ========================= */

    updateExamStats();
    updateNavigationButtons();
}

/* =========================================================
   VIEW ALL QUESTIONS
========================================================= */

function openAllQuestions() {
    const modal =
        document.getElementById("allQuestionsModal");

    const grid =
        document.getElementById("allQuestionsGrid");

    if (!modal || !grid) {
        return;
    }

    grid.innerHTML = "";

    studentExamQuestions.forEach(
        (question, index) => {

            const button =
                document.createElement("button");

            button.type = "button";
            button.className =
                "all-question-number";

            button.textContent =
                question.question_number || index + 1;

            /* Current question */
            if (
                index ===
                currentExamQuestionIndex
            ) {
                button.classList.add("current");
            }

            /* Answered question */
            if (
                selectedAnswers[question.id] !==
                undefined
            ) {
                button.classList.add("answered");
            }

            button.addEventListener(
                "click",
                () => {

                    currentExamQuestionIndex =
                        index;

                    modal.classList.add(
                        "hidden"
                    );

                    renderStudentExamQuestion();
                }
            );

            grid.appendChild(button);
        }
    );

    modal.classList.remove("hidden");
}


function closeAllQuestions() {
    const modal =
        document.getElementById("allQuestionsModal");

    if (modal) {
        modal.classList.add("hidden");
    }
}


/* =========================================================
   RENDER OPTIONS
   ========================================================= */

function renderStudentExamOptions(question) {

    const container =
        document.getElementById("options");

    if (!container) {
        return;
    }

    container.innerHTML = "";

    question.options.forEach(
        function (option) {

            const optionItem = document.createElement("div");
            optionItem.className = "exam-option-item";
            const optionButton = document.createElement("button");

            optionButton.type =
                "button";

            optionButton.className =
                "exam-option";

            optionButton.dataset.optionId =
                option.id;

            const selected =
                selectedAnswers[
                    question.id
                ] == option.id;

            if (selected) {

                optionButton.classList.add(
                    "selected"
                );
            }

            const label = document.createElement("span");
            label.className = "option-label";
            label.textContent = option.option_label || "";
            optionButton.appendChild(label);

            if (option.image_url) {
                const optionImage = document.createElement("img");
                optionImage.className = "option-image";
                optionImage.alt = `Option ${option.option_label || ""} image`;
                optionImage.src = resolveStudentMediaUrl(option.image_url);
                optionImage.onerror = () => optionImage.remove();
                optionButton.appendChild(optionImage);
            }

            if (option.text) {
                const optionText = document.createElement("span");
                optionText.className = "option-text";
                optionText.textContent = option.text;
                optionButton.appendChild(optionText);
            }

            optionButton.addEventListener(
                "click",
                function () {

                    selectedAnswers[
                        question.id
                    ] = option.id;

                    renderStudentExamQuestion();
                }
            );

            optionItem.appendChild(optionButton);

            if (option.audio_url) {
                const audioControls = document.createElement("div");
                audioControls.className = "exam-option-audio";
                const audioButton = document.createElement("button");
                audioButton.type = "button";
                audioButton.textContent = "▶ Play audio";
                const audioStatus = document.createElement("span");
                const optionAudio = document.createElement("audio");
                optionAudio.className = "exam-audio-source";
                optionAudio.preload = "none";
                optionAudio.src = resolveStudentMediaUrl(option.audio_url);
                audioButton.addEventListener("click", (event) => {
                    event.stopPropagation();
                    playExamAudio(question.id, optionAudio, audioButton, audioStatus);
                });
                audioControls.append(audioButton, audioStatus, optionAudio);
                optionItem.appendChild(audioControls);
            }

            container.appendChild(optionItem);
        }
    );
}


/* =========================================================
   NEXT BUTTON
   ========================================================= */

function goToNextStudentQuestion() {

    if (
        currentExamQuestionIndex <
        studentExamQuestions.length - 1
    ) {

        currentExamQuestionIndex++;

        renderStudentExamQuestion();
    }
}


/* =========================================================
   PREVIOUS BUTTON
   ========================================================= */

function goToPreviousStudentQuestion() {

    if (
        currentExamQuestionIndex > 0
    ) {

        currentExamQuestionIndex--;

        renderStudentExamQuestion();
    }
}

/* =========================================================
   OPEN SUBMIT MODAL
   ========================================================= */

function openSubmitModal() {

    const modal =
        document.getElementById("submitModal");

    const submitText =
        document.getElementById("submitText");

    if (!modal) {
        return;
    }

    const total =
        studentExamQuestions.length;

    const answered =
        Object.keys(selectedAnswers).length;

    const unanswered =
        total - answered;

    if (submitText) {

        submitText.textContent =
            `You have answered ${answered} of ${total} questions. ` +
            `${unanswered} question${unanswered === 1 ? "" : "s"} ` +
            `remain unanswered. Do you want to submit your exam?`;

    }

    modal.classList.remove("hidden");
}

/* =========================================================
   CLOSE SUBMIT MODAL
   ========================================================= */

function closeSubmitModal() {

    const modal =
        document.getElementById("submitModal");

    if (modal) {
        modal.classList.add("hidden");
    }
}

/* =========================================================
   SUBMIT EXAM TO BACKEND
   ========================================================= */

async function submitExamToBackend(autoSubmit = false) {

    if (!studentAttemptId) {

        console.error(
            "Cannot submit exam: attempt ID is missing."
        );

        alert(
            "Unable to submit the exam because the attempt was not started."
        );

        return;
    }


    const token =
        localStorage.getItem("access_token");


    if (!token) {

        console.error(
            "Cannot submit exam: access token is missing."
        );

        alert(
            "Your login session has expired. Please log in again."
        );

        return;
    }

    // Keep the periodic timer poll from competing with the save/submit calls
    // for the backend's deliberately small database connection pool.
    if (examTimerSyncInterval) {
        clearInterval(examTimerSyncInterval);
        examTimerSyncInterval = null;
    }
    if (timerStatusAbortController) {
        timerStatusAbortController.abort();
    }

    try {

        /* =====================================================
   STEP 1
   SAVE EVERY SELECTED ANSWER IN PARALLEL
   ===================================================== */

const answersToSave = Object.entries(selectedAnswers)
    .filter(([, selectedOptionId]) => selectedOptionId)
    .map(([questionId, selectedOptionId]) => ({
        question_id: String(questionId),
        selected_option_id: String(selectedOptionId)
    }));

if (answersToSave.length) {
    const saveResponse = await fetch(
        `${API_BASE_URL}/api/attempts/${encodeURIComponent(studentAttemptId)}/answers/batch`,
        {
            method: "POST",
            signal: AbortSignal.timeout(20000),
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ answers: answersToSave })
        }
    );
    const saveResult = await saveResponse.json().catch(() => ({}));
    if (!saveResponse.ok) {
        throw new Error(saveResult.detail || "Could not save your answers.");
    }
}

        /* =====================================================
           STEP 2
           SUBMIT THE ATTEMPT
           ===================================================== */

        const submitResponse =
            await fetch(
                `${API_BASE_URL}/api/attempts/${encodeURIComponent(studentAttemptId)}/submit`,
                {
                    method: "POST",
                    signal: AbortSignal.timeout(25000),

                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );


        const submitData =
            await submitResponse.json();


        if (!submitResponse.ok) {

            console.error(
                "Submit attempt failed:",
                submitData
            );


            throw new Error(
                submitData.detail ||
                "Failed to submit the exam."
            );
        }


        console.log(
            "EXAM SUBMITTED SUCCESSFULLY:",
            submitData
        );

        const submittedAttemptId = studentAttemptId;
        localStorage.setItem("last_attempt_id", submittedAttemptId);
        studentAttemptId = null;


        /* =====================================================
           STEP 3
           STOP FRONTEND TIMERS
           ===================================================== */

        if (examTimerInterval) {

            clearInterval(
                examTimerInterval
            );

            examTimerInterval = null;
        }


        if (examTimerSyncInterval) {

            clearInterval(
                examTimerSyncInterval
            );

            examTimerSyncInterval = null;
        }


        /* =====================================================
           STEP 4
           CLOSE SUBMIT MODAL
           ===================================================== */

        closeSubmitModal();


        /* =====================================================
           STEP 5
           GET FINAL RESULT FROM BACKEND
           ===================================================== */

        let resultData;
        try {
            const resultResponse = await fetch(
                `${API_BASE_URL}/api/attempts/${encodeURIComponent(submittedAttemptId)}/result`,
                {
                    method: "GET",
                    signal: AbortSignal.timeout(20000),
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );
            resultData = await resultResponse.json().catch(() => ({}));
            if (!resultResponse.ok) {
                throw new Error(resultData.detail || `Result request failed (${resultResponse.status}).`);
            }
        } catch (resultError) {
            console.error("Exam was submitted, but result loading failed:", resultError);
            // Answers page retries the result request and retains the attempt ID.
            window.location.href = "answers.html";
            return;
        }


        console.log(
            "FINAL EXAM RESULT:",
            resultData
        );


        /* =====================================================
           STEP 6
           SAVE RESULT FOR REVIEW PAGE
           ===================================================== */

        localStorage.setItem(
            "last_exam_result",
            JSON.stringify(resultData)
        );
        localStorage.setItem(
            "last_attempt_id",
            String(resultData.attempt_id || submittedAttemptId)
        );


        /* =====================================================
           STEP 7
           PREVENT ANOTHER SUBMISSION
           ===================================================== */

        /* =====================================================
           STEP 8
           OPEN RESULT / REVIEW PAGE
           ===================================================== */

        window.location.href = "answers.html";


        /* =====================================================
           AUTO SUBMIT LOG
           ===================================================== */

        if (autoSubmit) {

            console.log(
                "Exam was automatically submitted because the timer expired."
            );
        }


    } catch (error) {

        console.error(
            "Error while submitting exam:",
            error
        );


        alert(
            error.message ||
            "Something went wrong while submitting your exam."
        );

        if (!autoSubmit && examExpiresAt && !examTimerSyncInterval) {
            examTimerSyncInterval = setInterval(
                refreshBackendExamTimer,
                10000
            );
        }
    }
}

/* =========================================================
   UPDATE EXAM NAVIGATION
   ========================================================= */

function updateNavigationButtons() {

    const nextButton =
        document.getElementById("nextBtn");

    const previousButton =
        document.getElementById("prevBtn");

    if (!nextButton) {
        return;
    }

    const isFirstQuestion =
        currentExamQuestionIndex === 0;

    const isLastQuestion =
        currentExamQuestionIndex ===
        studentExamQuestions.length - 1;


    /* =========================
       PREVIOUS
       ========================= */

    if (previousButton) {

        previousButton.disabled =
            isFirstQuestion;

    }


    /* =========================
       LAST QUESTION
       ========================= */

    if (isLastQuestion) {

        nextButton.textContent =
            "Submit Exam";

        nextButton.classList.add(
            "submit-navigation"
        );

    }

    else {

        nextButton.textContent =
            "Next >>";

        nextButton.classList.remove(
            "submit-navigation"
        );

    }

}


/* =========================================================
   BUTTON EVENTS
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const examPage =
            document.getElementById(
                "options"
            );

        if (!examPage) {
            return;
        }

        const allBtn =
    document.getElementById("allBtn");

        const closeAllQuestionsBtn =
    document.getElementById(
        "closeAllQuestions"
    );

if (allBtn) {
    allBtn.addEventListener(
        "click",
        openAllQuestions
    );
}

if (closeAllQuestionsBtn) {
    closeAllQuestionsBtn.addEventListener(
        "click",
        closeAllQuestions
    );
}

const audioButton = document.getElementById("audioButton");
if (audioButton) {
    audioButton.addEventListener("click", function () {
        const question = studentExamQuestions[currentExamQuestionIndex];
        playExamAudio(
            question?.id,
            document.getElementById("questionAudio"),
            audioButton,
            document.getElementById("audioStatus")
        );
    });
}

const allQuestionsModal =
    document.getElementById(
        "allQuestionsModal"
    );

if (allQuestionsModal) {
    allQuestionsModal.addEventListener(
        "click",
        (event) => {

            if (
                event.target ===
                allQuestionsModal
            ) {
                closeAllQuestions();
            }
        }
    );
}


        /* =========================
           NEXT BUTTON
           ========================= */

        const nextButton =
            document.getElementById(
                "nextBtn"
            );


        /* =========================
           PREVIOUS BUTTON
           ========================= */

        const previousButton =
            document.getElementById(
                "prevBtn"
            );


        /* =========================
           NEXT / SUBMIT
           ========================= */

        if (nextButton) {

            nextButton.addEventListener(
                "click",
                function () {

                    const isLastQuestion =
                        currentExamQuestionIndex ===
                        studentExamQuestions.length - 1;


                    if (isLastQuestion) {

                        openSubmitModal();

                    }

                    else {

                        goToNextStudentQuestion();

                    }

                }
            );

        }


        /* =========================
           PREVIOUS
           ========================= */

        if (previousButton) {

            previousButton.addEventListener(
                "click",
                goToPreviousStudentQuestion
            );

        }


        /* =========================
           CANCEL SUBMIT
           ========================= */

       const cancelSubmitButton =
    document.getElementById("cancelSubmitBtn");

if (cancelSubmitButton) {
    cancelSubmitButton.onclick = function (event) {
        event.preventDefault();
        event.stopPropagation();
        closeSubmitModal();
    };
}

const confirmSubmitButton =
    document.getElementById("confirmSubmit");

if (confirmSubmitButton) {

    confirmSubmitButton.onclick =
        async function (event) {

            event.preventDefault();
            event.stopPropagation();

            confirmSubmitButton.disabled =
                true;

            confirmSubmitButton.textContent =
                "Submitting...";

            await submitExamToBackend(false);

            if (studentAttemptId) {

                confirmSubmitButton.disabled =
                    false;

                confirmSubmitButton.textContent =
                    "Submit Exam";
            }
        };
}

        /* =========================
           LOAD QUESTIONS
           ========================= */

        loadStudentExamQuestions();

    }
);

/* =========================================================
   STUDENT ACTIONS - LOGIN REQUIRED
   ========================================================= */

const loginRequiredModal = document.getElementById("loginRequiredModal");
const loginRequiredLink = document.getElementById("loginRequiredLink");
const loginRequiredTitle = document.getElementById("loginRequiredTitle");
const loginRequiredMessage = document.getElementById("loginRequiredMessage");
const closeLoginModal = document.getElementById("closeLoginModal");
const cancelLoginModal = document.getElementById("cancelLoginModal");
const studentActionDestinations = {
  test: "student/set.html",
  subscription: "student/subscription.html"
};

function closeLoginRequiredModal() {
  if (loginRequiredModal) loginRequiredModal.style.display = "none";
}

document.querySelectorAll("[data-student-gate]").forEach(function (link) {
  link.addEventListener("click", function (event) {
    const action = link.dataset.studentGate;
    const destination = studentActionDestinations[action];
    if (!destination) return;

    event.preventDefault();
    let accessToken = null;
    try {
      accessToken = localStorage.getItem("access_token");
    } catch (error) {
      // Treat unavailable storage as a signed-out visitor.
    }

    if (accessToken) {
      window.location.href = destination;
      return;
    }

    if (!loginRequiredModal) {
      window.location.href = `student/login.html?next=${encodeURIComponent(`../${destination}`)}`;
      return;
    }

    const isSubscription = action === "subscription";
    if (loginRequiredTitle) {
      loginRequiredTitle.textContent = isSubscription
        ? "Log in to view subscriptions"
        : "Log in to start a test";
    }
    if (loginRequiredMessage) {
      loginRequiredMessage.textContent = isSubscription
        ? "Sign in to your student account to view test access and subscription options."
        : "Sign in to your student account before starting a practice test.";
    }
    if (loginRequiredLink) {
      loginRequiredLink.href = `student/login.html?next=${encodeURIComponent(`../${destination}`)}`;
    }
    loginRequiredModal.style.display = "flex";
    if (closeLoginModal) closeLoginModal.focus();
  });
});

if (closeLoginModal) closeLoginModal.addEventListener("click", closeLoginRequiredModal);
if (cancelLoginModal) cancelLoginModal.addEventListener("click", closeLoginRequiredModal);
if (loginRequiredModal) {
  loginRequiredModal.addEventListener("click", function (event) {
    if (event.target === loginRequiredModal) closeLoginRequiredModal();
  });
}

const contactInquiryForm = document.getElementById("contactInquiryForm");
if (contactInquiryForm) {
  contactInquiryForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const submitButton = contactInquiryForm.querySelector(".contact-submit");
    const statusMessage = document.getElementById("contactFormStatus");
    const formData = Object.fromEntries(new FormData(contactInquiryForm).entries());

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Sending…";
    }
    if (statusMessage) {
      statusMessage.dataset.state = "";
      statusMessage.textContent = "Sending your message securely…";
    }

    try {
      const response = await fetch(`${API_BASE_URL}/contact/inquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      let result = {};
      try {
        result = await response.json();
      } catch (error) {
        // Use the helpful fallback below if the server response is not JSON.
      }
      if (!response.ok) {
        throw new Error(result.detail || result.message || "We couldn’t send your message. Please try again.");
      }

      contactInquiryForm.reset();
      if (statusMessage) {
        statusMessage.dataset.state = "success";
        statusMessage.textContent = "Message sent. The administrator can now see it in the portal inbox.";
      }
    } catch (error) {
      if (statusMessage) {
        statusMessage.dataset.state = "error";
        statusMessage.textContent = error.message || "Unable to send your message right now. Please try again.";
      }
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Send message <span aria-hidden="true">→</span>';
      }
    }
  });
}
