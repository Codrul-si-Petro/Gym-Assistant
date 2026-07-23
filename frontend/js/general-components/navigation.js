import { bindDismissOnOutsideOrEscape } from "../utils.js";

function bootNavigation() {
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  const siteTitle = document.querySelector(".site-title");
  if (!navToggle || !navLinks) return;

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
  }

  function closeMenu() {
    navLinks.classList.remove("active");
    if (isMobile()) navToggle.classList.remove("hidden");
    siteTitle?.classList.remove("hidden");
  }

  navToggle.addEventListener("click", (e) => {
    const isActive = navLinks.classList.contains("active");

    if (isActive) {
      closeMenu();
    } else {
      navLinks.classList.add("active");
      if (isMobile()) navToggle.classList.add("hidden");
      siteTitle?.classList.add("hidden");
    }

    e.stopPropagation(); // prevent document click from immediately closing
  });

  // Close menu when clicking a link
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  bindDismissOnOutsideOrEscape({
    isOpen: () => navLinks.classList.contains("active"),
    onClose: closeMenu,
    isInside: (target) =>
      target instanceof Element &&
      (navLinks.contains(target) || navToggle.contains(target)),
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootNavigation);
} else {
  bootNavigation();
}
