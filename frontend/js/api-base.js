// Shared API / frontend base URLs for classic (non-module) scripts.
// ES modules import from config.js / utils.js instead.
(function (global) {
  var isLocal =
    global.location.hostname === "localhost" ||
    global.location.hostname === "127.0.0.1" ||
    global.location.hostname === "::1";

  global.API_BASE = isLocal
    ? "http://127.0.0.1:8000"
    : "https://api.gym-assistant.app";

  global.FRONTEND_URL = isLocal
    ? global.location.origin
    : "https://gym-assistant.app";

  global.API_PREFIX = "/api/";

  global.getAuthHeaders = function getAuthHeaders() {
    var token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
      Authorization: "Bearer " + token,
      Accept: "application/json",
      "Content-Type": "application/json",
    };
  };

  global.refreshAccessToken = async function refreshAccessToken() {
    var refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;
    try {
      var res = await fetch(global.API_BASE + global.API_PREFIX + "token/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: refresh }),
      });
      if (!res.ok) return false;
      var data = await res.json();
      if (!data.access) return false;
      localStorage.setItem("access_token", data.access);
      if (data.refresh) localStorage.setItem("refresh_token", data.refresh);
      return true;
    } catch (e) {
      return false;
    }
  };

  global.apiFetch = async function apiFetch(url, options) {
    options = options || {};
    var res = await fetch(url, options);
    if (res.status === 401 && localStorage.getItem("refresh_token")) {
      var refreshed = await global.refreshAccessToken();
      if (refreshed) {
        var retryOptions = Object.assign({}, options, {
          headers: Object.assign({}, options.headers, global.getAuthHeaders()),
        });
        res = await fetch(url, retryOptions);
      } else {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
    return res;
  };

  function flattenErrorLeaves(data) {
    if (data == null) return [];
    if (typeof data === "string") return [data];
    if (Array.isArray(data)) {
      var out = [];
      data.forEach(function (item) {
        out = out.concat(flattenErrorLeaves(item));
      });
      return out;
    }
    if (typeof data === "object") {
      var parts = [];
      Object.keys(data).forEach(function (key) {
        parts = parts.concat(flattenErrorLeaves(data[key]));
      });
      return parts;
    }
    return [String(data)];
  }

  /**
   * Flatten DRF-style error payloads into a single user-facing string.
   * @param {*} data
   * @param {{ fallback?: string, humanize?: function, includeKey?: boolean, leavesOnly?: boolean, joiner?: string }} [opts]
   */
  global.formatApiErrors = function formatApiErrors(data, opts) {
    opts = opts || {};
    var fallback = opts.fallback || "Something went wrong.";
    if (data == null) return fallback;
    if (typeof data === "string") return data;

    if (opts.leavesOnly) {
      var leaves = flattenErrorLeaves(data);
      var seen = {};
      var unique = leaves.filter(function (m) {
        if (seen[m]) return false;
        seen[m] = true;
        return true;
      });
      return unique.length ? unique.join(opts.joiner || " ") : fallback;
    }

    if (Array.isArray(data)) {
      return data.map(String).join(opts.joiner || " ") || fallback;
    }
    if (typeof data !== "object") return String(data);
    if (data.detail) return String(data.detail);
    if (data.non_field_errors) {
      return data.non_field_errors.map(String).join(opts.joiner || " ") || fallback;
    }

    var parts = [];
    var includeKey = opts.includeKey !== false;
    Object.keys(data).forEach(function (key) {
      var val = data[key];
      var messages = Array.isArray(val) ? val : [String(val)];
      messages.forEach(function (msg) {
        if (opts.humanize) parts.push(opts.humanize(key, String(msg)));
        else if (includeKey) parts.push(key + ": " + msg);
        else parts.push(String(msg));
      });
    });
    return parts.length ? parts.join(opts.joiner || " ") : fallback;
  };
})(window);
