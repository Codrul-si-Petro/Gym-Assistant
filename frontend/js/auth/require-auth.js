(function () {
    if (!localStorage.getItem("access_token")) {
      var base = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:5500"
        : "https://gym-assistant.app";
      window.location.replace(base + "/pages/auth/login.html");
      return;
    }
  })();
