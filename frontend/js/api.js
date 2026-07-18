/* ============================================================
   api.js — Lớp gọi backend Hòa Tiến AI Assistant
   Đổi API_BASE_URL trước khi deploy (trỏ tới domain Railway/Render).
   ============================================================ */

const API_BASE_URL = window.__HOATIEN_API_BASE__ || "http://localhost:8000";

const TOKEN_KEY = "hoatien_token";
const USER_KEY = "hoatien_user";

function getToken() { return localStorage.getItem(TOKEN_KEY); }
function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}
function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch (e) {
    throw new ApiError("network", 0); // mất mạng / server không phản hồi
  }

  if (!res.ok) {
    let detail = "Đã có lỗi xảy ra";
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return null;
  return res.json();
}

const api = {
  getProcedures: () => apiFetch("/procedures"),
  getProcedure: (id) => apiFetch(`/procedures/${id}`),
  getFaq: () => apiFetch("/faq"),
  getContacts: () => apiFetch("/contacts"),
  chat: (question) => apiFetch("/chat", { method: "POST", body: JSON.stringify({ question }) }),
  getHistory: () => apiFetch("/chat/history"),
  register: (email, password, display_name) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify({ email, password, display_name }) }),
  login: (email, password) =>
    apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
};
