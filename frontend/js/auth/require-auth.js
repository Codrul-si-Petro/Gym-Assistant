(function () {
    if (!localStorage.getItem("access_token")) {
      var isLocal =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.hostname === "::1";
      var base = isLocal ? window.location.origin : "https://gym-assistant.app";
      window.location.replace(base + "/pages/auth/login.html");
      return;
    }
  })();
