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
          window.location.href = `${FRONTEND_URL}/homepage.html`;
        } else {
          errorDiv.textContent = data.detail || "Login failed";
        }
      } catch (err) {
        errorDiv.textContent = "Network error";
      }
    });
  }

  // --- Google OAuth login ---
  const googleLogin = document.getElementById("googleLogin");
  if (googleLogin) {
    googleLogin.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = `${API_BASE}/social/google/login/`;
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

  // --- Update nav links dynamically ---
  updateAuthLinks();
});

// --- Dynamic nav links based on login state ---
function updateAuthLinks() {
  const loggedIn = !!localStorage.getItem("access_token");

  const loginLink = document.getElementById("login-link");
  const signupLink = document.getElementById("signup-link");
  const logoutLink = document.getElementById("logout-link");

  if (!loginLink || !signupLink || !logoutLink) return;

  if (loggedIn) {
    loginLink.style.display = "none";
    signupLink.style.display = "none";
    logoutLink.style.display = "inline-block";

    logoutLink.addEventListener("click", (e) => {
      e.preventDefault();
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = `${FRONTEND_URL}/homepage.html`;
    });
  } else {
    loginLink.style.display = "inline-block";
    signupLink.style.display = "inline-block";
    logoutLink.style.display = "none";
  }
}
