document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  const siteTitle = document.querySelector(".site-title");

  function isMobile() {
    return window.matchMedia("(max-width: 767px)").matches;
  }

  function closeMenu() {
    navLinks.classList.remove("active");
    if (isMobile()) navToggle.classList.remove("hidden");
    siteTitle?.classList.remove("hidden");
  }

  navToggle?.addEventListener("click", (e) => {
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
  navLinks?.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", closeMenu);
  });

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    if (navLinks.classList.contains("active") &&
        !navLinks.contains(e.target) &&
        !navToggle.contains(e.target)) {
      closeMenu();
    }
  });

  // Close menu with ESC key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && navLinks.classList.contains("active")) {
      closeMenu();
    }
  });
});
