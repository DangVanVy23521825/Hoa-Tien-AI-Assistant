const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://hoa-tien-ai-assistant-production.up.railway.app";

const TOKEN_KEY = "hoatien_token";
const USER_KEY = "hoatien_user";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "admin";
}

export interface AuthResponse {
  access_token: string;
  user: User;
}

export interface Procedure {
  id: string;
  code: string;
  name: string;
  category: string;
  description: string;
  documents: string[];
  fee: string;
  processing_time: string;
  place_of_submission: string;
  legal_basis: string;
  online_url: string;
}

export interface Faq {
  id: string;
  question: string;
  answer: string;
}

export interface Contact {
  address: string;
  phone: string;
  working_hours: { weekdays: string; saturday?: string };
  portal_url: string;
}

export interface ChatResponse {
  /* Backend chỉ trả answer_html (đã là HTML), không có trường answer thuần văn bản. */
  answer_html: string;
  matched: boolean;
  source: string;
  matched_source_type: string | null;
  matched_source_id: string | null;
  online_url: string | null;
  message_id: string | null;
}

export interface ChatHistoryItem {
  id: string;
  question: string;
  answer: string;
  created_at: string;
}

export interface PublicStats {
  total_answered: number;
  top_questions: string[];
}

export interface AdminStats {
  total: number;
  matched: number;
  unmatched: number;
  /** Lượt chào hỏi/cảm ơn — không tính vào matched lẫn unmatched */
  smalltalk: number;
  helpful: number;
  unhelpful: number;
  top_procedures: { name: string; count: number }[];
  recent_unmatched: { question: string; created_at: string }[];
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

function setSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("network", 0);
  }

  if (!res.ok) {
    let detail = "Đã có lỗi xảy ra";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null as T;
  return res.json();
}

export const api = {
  getProcedures: () => apiFetch<Procedure[]>("/procedures"),
  getProcedure: (id: string) => apiFetch<Procedure>(`/procedures/${id}`),
  getFaq: () => apiFetch<Faq[]>("/faq"),
  getContacts: () => apiFetch<Contact>("/contacts"),
  chat: (question: string) =>
    apiFetch<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  getHistory: () => apiFetch<ChatHistoryItem[]>("/chat/history"),
  sendFeedback: (messageId: string, helpful: boolean) =>
    apiFetch("/chat/feedback", {
      method: "POST",
      body: JSON.stringify({ message_id: messageId, helpful }),
    }),
  getPublicStats: () => apiFetch<PublicStats>("/chat/stats/public"),
  getAdminStats: () => apiFetch<AdminStats>("/admin/stats"),
  register: (email: string, password: string, display_name: string) =>
    apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),
  login: (email: string, password: string) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
};

export { getToken, getStoredUser, setSession, clearSession };

export function qr(data: string, size = 96) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=0&data=${encodeURIComponent(data)}`;
}
