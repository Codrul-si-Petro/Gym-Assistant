// Shared frontend configuration
export const SUPPORT_EMAIL = "gym-assistant@outlook.com";
const IS_LOCAL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "::1";

export const API_BASE = IS_LOCAL
  ? "http://127.0.0.1:8000"
  : "https://api.gym-assistant.app";

export const FRONTEND_URL = IS_LOCAL
  ? window.location.origin
  : "https://gym-assistant.app";

export const API_PREFIX = "/api/";
