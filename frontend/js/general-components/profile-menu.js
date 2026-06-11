import { API_BASE, API_PREFIX, FRONTEND_URL, SUPPORT_EMAIL } from "../config.js";

function getInitials(username) {
  if (!username) return "?";
  const parts = username.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return username.slice(0, 2).toUpperCase();
}

function closeAllMenus() {
  document.querySelectorAll(".profile-dropdown.is-open").forEach((menu) => {
    menu.classList.remove("is-open");
    const trigger = menu.parentElement?.querySelector(".profile-trigger");
    if (trigger) trigger.setAttribute("aria-expanded", "false");
  });
}

function buildProfileMenu(container, user) {
  container.innerHTML = `
    <div class="profile-menu">
      <button type="button" class="profile-trigger" aria-expanded="false" aria-haspopup="true" aria-label="Open profile menu">
        ${getInitials(user?.username)}
      </button>
      <div class="profile-dropdown" role="menu">
        <div class="profile-email">${user?.username || "Account"}</div>
        <a href="${resolveCorePath("profile.html")}" role="menuitem">Profile</a>
        <a href="${resolveCorePath("account.html")}" role="menuitem">Account settings</a>
        <a href="${resolveCorePath("explore.html")}" role="menuitem">Explore / Glossary</a>
        <a href="mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Support" role="menuitem">Support</a>
        <hr>
        <button type="button" id="profile-logout-btn" role="menuitem">Log out</button>
      </div>
    </div>
  `;

  const trigger = container.querySelector(".profile-trigger");
  const dropdown = container.querySelector(".profile-dropdown");

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.contains("is-open");
    closeAllMenus();
    if (!isOpen) {
      dropdown.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
    }
  });

  container.querySelector("#profile-logout-btn")?.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = `${FRONTEND_URL}/index.html`;
  });
}

function resolveCorePath(filename) {
  if (window.location.pathname.includes("/pages/core/")) return filename;
  if (window.location.pathname.includes("/pages/auth/")) return `../core/${filename}`;
  return `pages/core/${filename}`;
}

function resolveAuthPath(filename) {
  if (window.location.pathname.includes("/pages/core/")) return `../auth/${filename}`;
  if (window.location.pathname.includes("/pages/auth/")) return filename;
  return `pages/auth/${filename}`;
}

function buildAuthLinks(container) {
  container.innerHTML = `
    <div class="auth-links auth-links--cta">
      <a href="${resolveAuthPath("signup.html")}" class="cta-button">Get started</a>
      <a href="${resolveAuthPath("login.html")}" class="cta-button cta-button--ghost">Log in</a>
    </div>
  `;
}

async function fetchCurrentUser() {
  const token = localStorage.getItem("access_token");
  if (!token) return { unauthorized: true };
  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    });
    if (res.status === 401) return { unauthorized: true };
    if (!res.ok) return { username: "Account" };
    const data = await res.json();
    if (!data) return { username: "Account" };
    return data;
  } catch {
    // Transient network errors should not wipe a valid session.
    return { username: "Account" };
  }
}

export async function initProfileMenu(containerId = "nav-actions") {
  const container = document.getElementById(containerId);
  if (!container) return;

  const loggedIn = !!localStorage.getItem("access_token");
  if (!loggedIn) {
    buildAuthLinks(container);
    return;
  }

  const user = await fetchCurrentUser();
  if (user?.unauthorized) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    buildAuthLinks(container);
    return;
  }

  buildProfileMenu(container, user);
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".profile-menu")) closeAllMenus();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAllMenus();
});

function bootProfileMenu() {
  initProfileMenu();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootProfileMenu);
} else {
  bootProfileMenu();
}

window.addEventListener("jwt-stored", bootProfileMenu);
