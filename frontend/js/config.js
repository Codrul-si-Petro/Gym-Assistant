// Shared frontend configuration
export const SUPPORT_EMAIL = "gym-assistant@outlook.com";

export const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://127.0.0.1:8000"
  : "https://api.gym-assistant.app";

export const FRONTEND_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:5500"
  : "https://gym-assistant.app";

export const API_PREFIX = "/api/";
