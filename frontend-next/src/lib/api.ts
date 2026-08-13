const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://hoa-tien-ai-assistant-production.up.railway.app";

const TOKEN_KEY = "hoatien_token";
const USER_KEY = "hoatien_user";
const GUEST_KEY = "hoatien_guest_id";

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
  keywords: string[];
  description: string;
  documents: string[];
  fee: string;
  processing_time: string;
  place_of_submission: string;
  legal_basis: string;
  online_url: string;
}

export type ReportCategory =
  | "ha_tang"
  | "moi_truong"
  | "an_ninh"
  | "thu_tuc"
  | "khac";

export interface Report {
  id: string;
  seq: number;
  /** Mã phiếu người dân đọc được, ví dụ "PA-0007" — backend sinh từ `seq`. */
  code: string;
  category: ReportCategory;
  content: string;
  location: string | null;
  created_at: string;
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
  /** Số lượt hỏi thử còn lại của khách; null nếu đã đăng nhập (không giới hạn) */
  guest_turns_left: number | null;
}

export interface GuestQuota {
  limit: number;
  used: number;
  /** null = đã đăng nhập, không giới hạn */
  remaining: number | null;
}

export interface OtpSent {
  email: string;
  expires_in_seconds: number;
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
  /** Mã lỗi máy đọc được từ backend (email_unverified, guest_quota_exceeded…) */
  code: string | null;
  constructor(message: string, status: number, code: string | null = null) {
    super(message);
    this.status = status;
    this.code = code;
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

/** UUID gắn với trình duyệt này, dùng để backend đếm lượt hỏi thử của khách. */
function guestId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(GUEST_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(GUEST_KEY, id);
  }
  return id;
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
  // Khách chưa đăng nhập được đếm lượt theo thiết bị chứ không theo IP: ở hội trại
  // cả hội trường chung một IP NAT nên đếm theo IP sẽ chặn nhầm.
  if (!token) headers["X-Guest-Id"] = guestId();

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("network", 0);
  }

  if (!res.ok) {
    let detail = "Đã có lỗi xảy ra";
    let code: string | null = null;
    try {
      const body = await res.json();
      // Lỗi có ý nghĩa với UI trả detail dạng {code, message}; lỗi thường vẫn là chuỗi.
      if (body.detail && typeof body.detail === "object") {
        detail = body.detail.message || detail;
        code = body.detail.code ?? null;
      } else if (body.detail) {
        detail = body.detail;
      }
    } catch {}
    throw new ApiError(detail, res.status, code);
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
  getGuestQuota: () => apiFetch<GuestQuota>("/chat/guest-quota"),
  createReport: (body: {
    category: ReportCategory;
    content: string;
    location?: string;
  }) => apiFetch<Report>("/reports", { method: "POST", body: JSON.stringify(body) }),
  getMyReports: () => apiFetch<Report[]>("/reports/me"),
  /** Tạo tài khoản chưa xác thực + gửi OTP. Chưa có token cho tới khi verify. */
  register: (email: string, password: string, display_name: string) =>
    apiFetch<OtpSent>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),
  verifyOtp: (email: string, code: string) =>
    apiFetch<AuthResponse>("/auth/verify-otp", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  resendOtp: (email: string) =>
    apiFetch<OtpSent>("/auth/resend-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  login: (email: string, password: string) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
};

export { getToken, getStoredUser, setSession, clearSession, guestId };

export function qr(data: string, size = 96) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=0&data=${encodeURIComponent(data)}`;
}
