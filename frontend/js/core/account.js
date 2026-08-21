import { API_BASE, API_PREFIX } from "../config.js";
import { getAuthHeaders, apiFetch, showMessage as showStatus, formatApiErrors } from "../utils.js";

function showMessage(text, type = "") {
  showStatus(text, type, {
    elementId: "account-msg",
    baseClass: "account-msg",
    autoHideMs: null,
  });
}

const ERROR_MESSAGES = {
  current_password: {
    "Incorrect password.": "You entered an incorrect password. Please try again",
  },
  username: {
    "This username is already taken.": "This username is already taken. Please choose another.",
  },
  new_password2: {
    "Passwords do not match.": "The new passwords do not match. Please try again.",
  },
};

function humanizeFieldError(key, message) {
  const mapped = ERROR_MESSAGES[key]?.[message];
  if (mapped) return mapped;
  if (key === "current_password" && /incorrect/i.test(message)) {
    return "You entered an incorrect password. Please try again";
  }
  return message;
}

function formatErrors(data) {
  return formatApiErrors(data, { humanize: humanizeFieldError });
}

async function submitUsername(event) {
  event.preventDefault();
  const headers = getAuthHeaders();
  if (!headers) {
    showMessage("Please log in first.", "error");
    return;
  }

  const form = event.target;
  const payload = {
    username: form.username.value.trim(),
  };

  const res = await apiFetch(`${API_BASE}${API_PREFIX}auth/update-username/`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage(formatErrors(data), "error");
    return;
  }
  showMessage(data.message || "Username updated.", "success");
  form.reset();
}

async function submitPassword(event) {
  event.preventDefault();
  const headers = getAuthHeaders();
  if (!headers) {
    showMessage("Please log in first.", "error");
    return;
  }

  const form = event.target;
  const payload = {
    current_password: form.current_password.value,
    new_password1: form.new_password1.value,
    new_password2: form.new_password2.value,
  };

  const res = await apiFetch(`${API_BASE}${API_PREFIX}auth/change-password/`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage(formatErrors(data), "error");
    return;
  }
  showMessage(data.message || "Password updated.", "success");
  form.reset();
}

document.getElementById("username-form")?.addEventListener("submit", submitUsername);
document.getElementById("password-form")?.addEventListener("submit", submitPassword);
