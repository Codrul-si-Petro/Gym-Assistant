import { API_BASE, API_PREFIX } from "../config.js";

function getPage() {
  const path = window.location.pathname;
  if (path.includes("password_reset_confirm")) return "confirm";
  if (path.includes("password_reset_sent")) return "sent";
  if (path.includes("password_reset_complete")) return "complete";
  return "request";
}

async function handleRequest(e) {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const errorDiv = document.getElementById("error");
  const successDiv = document.getElementById("success");
  errorDiv.textContent = "";
  successDiv.textContent = "";

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/password-reset/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await res.json();
    if (res.ok) {
      window.location.href = "password_reset_sent.html";
    } else {
      errorDiv.textContent = data.email?.[0] || data.detail || "Request failed.";
    }
  } catch {
    errorDiv.textContent = "Network error. Please try again.";
  }
}

async function handleConfirm(e) {
  e.preventDefault();
  const params = new URLSearchParams(window.location.search);
  const uid = params.get("uid");
  const token = params.get("token");
  const errorDiv = document.getElementById("error");

  if (!uid || !token) {
    errorDiv.textContent = "Invalid reset link. Please request a new one.";
    return;
  }

  const new_password1 = document.getElementById("password1").value;
  const new_password2 = document.getElementById("password2").value;

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/password-reset/confirm/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uid, token, new_password1, new_password2 }),
    });
    const data = await res.json();
    if (res.ok) {
      window.location.href = "password_reset_complete.html";
    } else {
      const msg = Array.isArray(data.error) ? data.error.join(" ") : (data.error || data.new_password2?.[0] || "Reset failed.");
      errorDiv.textContent = msg;
    }
  } catch {
    errorDiv.textContent = "Network error. Please try again.";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  const page = getPage();
  const requestForm = document.getElementById("resetRequestForm");
  const confirmForm = document.getElementById("resetConfirmForm");
  if (page === "request" && requestForm) requestForm.addEventListener("submit", handleRequest);
  if (page === "confirm" && confirmForm) confirmForm.addEventListener("submit", handleConfirm);
});
