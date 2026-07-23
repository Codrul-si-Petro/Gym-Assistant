// Shared status toast for classic (non-module) pages that use #message.
// ES module pages import showMessage from utils.js instead.

var _statusHideTimer = null;
var _statusFadeTimer = null;

function cancelStatusTimers() {
  if (_statusHideTimer !== null) {
    clearTimeout(_statusHideTimer);
    _statusHideTimer = null;
  }
  if (_statusFadeTimer !== null) {
    clearTimeout(_statusFadeTimer);
    _statusFadeTimer = null;
  }
}

/**
 * @param {string} text
 * @param {"success"|"error"|""} [type]
 * @param {{ elementId?: string, baseClass?: string, autoHideMs?: number|null, fadeMs?: number }} [opts]
 */
function showMessage(text, type, opts) {
  opts = opts || {};
  var el = document.getElementById(opts.elementId || "message");
  if (!el) return;

  cancelStatusTimers();

  var baseClass = opts.baseClass || "message";
  var typeClass =
    type === "success" ? "success" : type === "error" ? "error" : type || "";
  el.textContent = text;
  el.className = typeClass ? baseClass + " " + typeClass : baseClass;
  el.removeAttribute("hidden");
  el.style.opacity = "";
  el.style.transition = "";

  var autoHideMs =
    opts.autoHideMs !== undefined
      ? opts.autoHideMs
      : type === "success"
        ? 4000
        : null;
  if (autoHideMs == null) return;

  var fadeMs = opts.fadeMs != null ? opts.fadeMs : 0;
  _statusHideTimer = setTimeout(function () {
    _statusHideTimer = null;
    if (fadeMs > 0) {
      el.style.opacity = "0";
      el.style.transition = "opacity " + fadeMs + "ms ease";
      _statusFadeTimer = setTimeout(function () {
        _statusFadeTimer = null;
        el.textContent = "";
        el.className = baseClass;
        el.style.opacity = "";
        el.style.transition = "";
      }, fadeMs);
    } else {
      el.textContent = "";
      el.className = baseClass;
    }
  }, autoHideMs);
}

function clearMessage(opts) {
  opts = opts || {};
  cancelStatusTimers();
  var el = document.getElementById(opts.elementId || "message");
  if (!el) return;
  el.textContent = "";
  el.className = opts.baseClass || "message";
  el.style.opacity = "";
  el.style.transition = "";
  el.setAttribute("hidden", "hidden");
}
