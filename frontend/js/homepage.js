const words = ["inspiration.", "passion.", "motivation."];
let i = 0;

setInterval(() => {
  i = (i + 1) % words.length;
  document.getElementById("word").textContent = words[i];
}, 1500);

// Default API base
let API_BASE;

// Use localhost/127 if running locally, otherwise use current host
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  API_BASE = "http://127.0.0.1:8000"; // local backend
} else {
  API_BASE = 'https://api.gym-assistant.app';
}

const API_PREFIX = "/api/";

let FRONTEND_URL;
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  FRONTEND_URL = "http://localhost:5500"; // local frontend
} else {
  FRONTEND_URL = 'https://gym-assistant.app';
}

function updateAuthLinks() {
  const loggedIn = !!localStorage.getItem("access_token");
  const loginLink = document.getElementById("login-link");
  const signupLink = document.getElementById("signup-link");
  const logoutLink = document.getElementById("logout-link");
  const authContainer = document.getElementById("auth-links");

  if (!authContainer) return;
  if (loggedIn) {
    if (loginLink) loginLink.style.display = "none";
    if (signupLink) signupLink.style.display = "none";
    if (logoutLink) {
      logoutLink.style.display = "inline-block";
      logoutLink.replaceWith(logoutLink.cloneNode(true));
      document.getElementById("logout-link").addEventListener("click", (e) => {
        e.preventDefault();
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = FRONTEND_URL + "/index.html";
      });
    }
    authContainer.setAttribute("data-auth", "logged-in");
  } else {
    if (loginLink) loginLink.style.display = "inline-block";
    if (signupLink) signupLink.style.display = "inline-block";
    if (logoutLink) logoutLink.style.display = "none";
    authContainer.setAttribute("data-auth", "logged-out");

  }
    const authenticatedLinks = document.getElementById("authenticated-links");
    if (authenticatedLinks) {
      authenticatedLinks.style.display = loggedIn ? "flex" : "none";
    }
}

window.addEventListener("DOMContentLoaded", updateAuthLinks);

window.addEventListener("DOMContentLoaded", () => {
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

  const googleLogin = document.getElementById("googleLogin");
  if (googleLogin) {
    googleLogin.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.href = `${API_BASE}/social/google/login/`;
    });
  }
});
