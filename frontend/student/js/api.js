/* Central backend configuration for the static EPS-TOPIK frontend. */
(function () {
  const baseUrl = window.API_BASE_URL || "";
  async function request(path, options) {
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || data.message || `Request failed (${response.status})`);
    }
    return data;
  }

  window.EPS_API = {
    baseUrl,
    request,
    auth: {
      register: (body) => request("/auth/register", { method: "POST", body: JSON.stringify(body) }),
      verifyRegistrationOtp: (body) => request("/auth/verify-registration-otp", { method: "POST", body: JSON.stringify(body) }),
      resendRegistrationOtp: (body) => request("/auth/resend-registration-otp", { method: "POST", body: JSON.stringify(body) }),
      login: (body) => request("/auth/login", { method: "POST", body: JSON.stringify(body) }),
      forgotPassword: (body) => request("/auth/forgot-password", { method: "POST", body: JSON.stringify(body) }),
      verifyOtp: (body) => request("/auth/verify-otp", { method: "POST", body: JSON.stringify(body) }),
      resetPassword: (body) => request("/auth/reset-password", { method: "POST", body: JSON.stringify(body) }),
    },
  };
}());
