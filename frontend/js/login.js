const API_BASE = "http://127.0.0.1:8000"; // no trailing /api here for OAuth
const API_PREFIX = "/api/";

// Normal login
document.getElementById("loginForm").addEventListener("submit", async (e) => {
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
      window.location.href = "homepage.html";
    } else {
      errorDiv.textContent = data.detail || "Login failed";
    }
  } catch (err) {
    errorDiv.textContent = "Network error";
  }
});

// Google OAuth login
document.getElementById("googleLogin").addEventListener("click", (e) => {
  e.preventDefault();
  window.location.href = `${API_BASE}/social/google/login/?next=/frontend/homepage.html`;
});

// Handle redirect back from backend after Google OAuth
window.addEventListener("DOMContentLoaded", () => {
  // Check if the URL has tokens in query string (your backend should send them)
  const params = new URLSearchParams(window.location.search);
  const access = params.get("access");
  const refresh = params.get("refresh");

  if (access && refresh) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    // Clean URL and redirect to homepage
    window.history.replaceState({}, document.title, "/homepage.html");
    window.location.href = "/homepage.html";
  }
});
