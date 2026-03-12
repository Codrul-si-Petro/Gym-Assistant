(function () {
    if (!localStorage.getItem("access_token")) {
      var base = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:5500"
        : "https://gym-assistant-6z0m.onrender.com";
      window.location.replace(base + "/pages/auth/login.html");
      return;
    }
  })();