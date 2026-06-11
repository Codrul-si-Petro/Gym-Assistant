(function () {
  var params = new URLSearchParams(window.location.search);
  var access = params.get("access");
  var refresh = params.get("refresh");
  if (!access || !refresh) return;

  try {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
    window.history.replaceState({}, document.title, window.location.pathname);
    window.dispatchEvent(new CustomEvent("jwt-stored"));
  } catch (e) {
    /* localStorage unavailable */
  }
})();