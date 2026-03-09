(function() {
    var params = new URLSearchParams(window.location.search);
    var access = params.get("access");
    var refresh = params.get("refresh");
    if (access && refresh) {
      try {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        window.history.replaceState({}, document.title, window.location.pathname);
      } catch (e) {}
      if (window.opener) {
        var frontendUrl = window.FRONTEND_URL || "http://localhost:5500";
        window.opener.location.href = frontendUrl + "/index.html";
        window.close();
      }
    }
  })();