(function () {
    if (!localStorage.getItem("access_token")) {
      var base = typeof FRONTEND_URL !== "undefined"
        ? FRONTEND_URL
        : (window.location.hostname === "localhost" ||
           window.location.hostname === "127.0.0.1" ||
           window.location.hostname === "::1")
          ? window.location.origin
          : "https://gym-assistant.app";
      window.location.replace(base + "/pages/auth/login.html");
      return;
    }
  })();
