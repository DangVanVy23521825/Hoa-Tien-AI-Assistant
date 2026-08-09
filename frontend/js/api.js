/* ============================================================
   api.js — Lớp gọi backend Hòa Tiến AI Assistant
   Đổi API_BASE_URL trước khi deploy (trỏ tới domain Railway/Render).
   ============================================================ */

const API_BASE_URL = window.__HOATIEN_API_BASE__ || "https://hoa-tien-ai-assistant-production.up.railway.app";

const TOKEN_KEY = "hoatien_token";
const USER_KEY = "hoatien_user";
const GUEST_KEY = "hoatien_guest_id";

/* UUID gắn với trình duyệt này — backend đếm lượt hỏi thử của khách theo nó.
   Đếm theo thiết bị chứ không theo IP vì cả hội trường dùng chung wifi NAT. */
function guestId() {
  let id = localStorage.getItem(GUEST_KEY);
  if (!id) {
    id = (crypto.randomUUID && crypto.randomUUID()) ||
      `g-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(GUEST_KEY, id);
  }
  return id;
}

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
  constructor(message, status, code = null) { super(message); this.status = status; this.code = code; }
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!token) headers["X-Guest-Id"] = guestId();

  let res;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch (e) {
    throw new ApiError("network", 0); // mất mạng / server không phản hồi
  }

  if (!res.ok) {
    let detail = "Đã có lỗi xảy ra";
    let code = null;
    try {
      const body = await res.json();
      // Lỗi có ý nghĩa với UI trả detail dạng {code, message}; lỗi thường vẫn là chuỗi.
      if (body.detail && typeof body.detail === "object") {
        detail = body.detail.message || detail;
        code = body.detail.code || null;
      } else if (body.detail) {
        detail = body.detail;
      }
    } catch (_) {}
    throw new ApiError(detail, res.status, code);
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
  sendFeedback: (messageId, helpful) =>
    apiFetch("/chat/feedback", { method: "POST", body: JSON.stringify({ message_id: messageId, helpful }) }),
  getPublicStats: () => apiFetch("/chat/stats/public"),
  getAdminStats: () => apiFetch("/admin/stats"),
  register: (email, password, display_name) =>
    apiFetch("/auth/register", { method: "POST", body: JSON.stringify({ email, password, display_name }) }),
  login: (email, password) =>
    apiFetch("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
};
