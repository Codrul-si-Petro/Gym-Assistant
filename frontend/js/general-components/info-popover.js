import { PAGE_INFO } from "./info-content.js";

const SEEN_PREFIX = "gym_assistant_info_seen_";

const PATH_PAGE_KEYS = [
  [/index\.html$/, "home"],
  [/\/$/, "home"],
  [/workouts_input\.html$/, "log"],
  [/workouts_table\.html$/, "history"],
  [/dashboard\.html$/, "metrics"],
  [/explore\.html$/, "explore"],
  [/profile\.html$/, "profile"],
  [/account\.html$/, "account"],
];

function resolvePageKey() {
  const explicit = document.body.dataset.infoPage;
  if (explicit) return explicit;
  const path = window.location.pathname;
  for (const [pattern, key] of PATH_PAGE_KEYS) {
    if (pattern.test(path)) return key;
  }
  return null;
}

function hasSeen(pageKey) {
  return localStorage.getItem(SEEN_PREFIX + pageKey) === "1";
}

function markSeen(pageKey) {
  localStorage.setItem(SEEN_PREFIX + pageKey, "1");
}

function closePanel(wrap) {
  const btn = wrap.querySelector(".info-fab");
  const panel = wrap.querySelector(".info-panel");
  if (btn) btn.setAttribute("aria-expanded", "false");
  if (panel) panel.hidden = true;
}

function closeAll(except) {
  document.querySelectorAll(".info-fab-wrap").forEach((wrap) => {
    if (wrap === except) return;
    closePanel(wrap);
  });
}

function mountPageInfo(pageKey, text) {
  const wrap = document.createElement("div");
  wrap.className = "info-fab-wrap";
  wrap.dataset.infoPage = pageKey;

  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "info-fab";
  btn.setAttribute("aria-label", "About this page");
  btn.setAttribute("aria-expanded", "false");
  btn.textContent = "ⓘ";
  if (!hasSeen(pageKey)) {
    btn.classList.add("info-fab--glow");
  }

  const panel = document.createElement("div");
  panel.className = "info-panel info-panel--fab";
  panel.setAttribute("role", "region");
  panel.hidden = true;
  panel.textContent = text;

  btn.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = btn.getAttribute("aria-expanded") === "true";
    closeAll(wrap);
    if (isOpen) {
      closePanel(wrap);
      return;
    }
    btn.setAttribute("aria-expanded", "true");
    panel.hidden = false;
    markSeen(pageKey);
    btn.classList.remove("info-fab--glow");
  });

  wrap.appendChild(panel);
  wrap.appendChild(btn);
  document.body.appendChild(wrap);
}

document.addEventListener("click", (event) => {
  if (!(event.target instanceof Element)) return;
  if (event.target.closest(".info-fab-wrap")) return;
  closeAll(null);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeAll(null);
});

document.addEventListener("DOMContentLoaded", () => {
  if (!localStorage.getItem("access_token")) return;
  const pageKey = resolvePageKey();
  if (!pageKey) return;
  const text = PAGE_INFO[pageKey];
  if (!text) return;
  mountPageInfo(pageKey, text);
});
