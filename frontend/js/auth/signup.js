// API_BASE comes from api-base.js (load that script first).

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
      errorDiv.textContent =
        formatApiErrors(data, { joiner: " | ", fallback: "Sign up failed." });
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
