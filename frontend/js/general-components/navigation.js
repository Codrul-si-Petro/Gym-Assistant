document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");

  function closeMenu() {
    navLinks.classList.remove("active");
    navToggle.classList.remove("hidden");
  }

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", (e) => {
      navLinks.classList.toggle("active"); // show/hide menu
      navToggle.classList.toggle("hidden"); // hide hamburger when active
      e.stopPropagation(); // prevent document click from immediately closing
    });
  }

  // Hide menu when clicking a link (mobile)
  navLinks?.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", closeMenu);
  });

  // Hide menu when clicking outside
  document.addEventListener("click", (e) => {
    if (navLinks.classList.contains("active") && !navLinks.contains(e.target) && !navToggle.contains(e.target)) {
      closeMenu();
    }
  });
});
