// URLS for local development and production
const FRONTEND_URL = window.FRONTEND_URL || "http://localhost:5500";
const API_BASE = window.API_BASE || "http://127.0.0.1:8000";
const API_PREFIX = "/api/";

window.addEventListener("DOMContentLoaded", () => {
  // --- Normal login ---
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      const errorDiv = document.getElementById("error");

      try {
        const res = await fetch(`${API_BASE}${API_PREFIX}token/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (res.ok && data.access && data.refresh) {
          localStorage.setItem("access_token", data.access);
          localStorage.setItem("refresh_token", data.refresh);
          window.location.href = `${FRONTEND_URL}/index.html`;
        } else {
          errorDiv.textContent = data.detail || "Login failed";
        }
      } catch (err) {
        errorDiv.textContent = "Network error";
      }
    });
  }

  // --- Google OAuth login (popup so main window stays on frontend) ---
  const googleLogin = document.getElementById("googleLogin");
  if (googleLogin) {
    googleLogin.addEventListener("click", (e) => {
      e.preventDefault();
      const w = window.open(
        `${API_BASE}/social/google/login/`,
        "googleLogin",
        "width=500,height=600,scrollbars=yes"
      );
      if (w) w.focus();
    });
  }

  // --- Handle JWTs from URL query string ---
  const params = new URLSearchParams(window.location.search);
  const access = params.get("access");
  const refresh = params.get("refresh");

  if (access && refresh) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    // Remove tokens from URL without redirect
    const cleanPath = window.location.pathname;
    window.history.replaceState({}, document.title, cleanPath);
  }

});
