const API_BASE = window.API_BASE || "http://127.0.0.1:8000";

document.getElementById("signupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const email = document.getElementById("email").value.trim();
  const password1 = document.getElementById("password1").value;
  const password2 = document.getElementById("password2").value;
  const errorDiv = document.getElementById("error");

  errorDiv.textContent = "";

  if (password1 !== password2) {
    errorDiv.textContent = "Passwords do not match.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/auth/signup/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password1, password2 }),
    });

    const data = await res.json();

    if (res.ok) {
      errorDiv.textContent = data.message || "Account created. You can log in.";
      errorDiv.style.color = "#aaffaa";
      document.getElementById("signupForm").reset();
      setTimeout(() => {
        window.location.href = "login.html";
      }, 2000);
    } else {
  // API returned an error (400, 401, etc.)
        let messages = [];

        if (typeof data === "object") {
          // flatten all fields into one message array
          for (const [key, value] of Object.entries(data)) {
            if (Array.isArray(value)) {
              messages.push(`${key}: ${value.join(", ")}`);
            } else {
              messages.push(`${key}: ${value}`);
            }
          }
        } else {
          messages.push(data);
        }

        errorDiv.textContent = messages.join(" | ") || "Sign up failed.";
      }
    } catch (err) {
      // Real network error
      errorDiv.textContent = `Network error: ${err.message}`;
    }
});

document.getElementById("googleSignup").addEventListener("click", (e) => {
  e.preventDefault();
  window.location.href = `${API_BASE}/social/google/login/`;
});
