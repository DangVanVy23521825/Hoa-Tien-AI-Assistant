# rules/frontend.md — Quy ước giao diện

## Frontend chính hiện tại: `frontend-next/` (Next.js 16)

Từ 08/2026, bản deploy chính là **`frontend-next/`** — Next.js 16 (App Router, Turbopack)
+ Tailwind CSS v4 + shadcn/ui (base-ui) + TypeScript. `frontend/` (vanilla HTML/CSS/JS)
giữ lại làm tham chiếu; bản offline dự phòng nằm ở `frontend-next/public/legacy/index.html`
(copy của `frontend/legacy/index.html`, phải giữ đồng bộ).

| Route | Trang |
|---|---|
| `/` | Trang chủ (hero + số liệu + nút chia sẻ) |
| `/tro-ly` | Trợ lý AI (chat, voice, feedback, lịch sử, chips động) |
| `/thu-tuc` | Danh mục thủ tục |
| `/thu-tuc/[code]` | Chi tiết thủ tục (QR + in checklist) — key là **`code`** ("KS-01"), không phải UUID `id` |
| `/hoi-dap` | FAQ (accordion) |
| `/lien-he` | Liên hệ + QR cổng dịch vụ công |
| `/dang-nhap` | Đăng nhập / Đăng ký |

Quy ước riêng của bản Next.js — **không phá**:

- **Mọi page là client component** → không export `metadata` được. Metadata mỗi route
  đặt trong `layout.tsx` cùng thư mục (`export const metadata`), title dùng template
  `"%s · Hòa Tiến AI"` khai báo ở `app/layout.tsx`.
- **`#printArea` phải là con TRỰC TIẾP của `<body>`** (đặt trong `app/layout.tsx`), vì
  CSS `@media print` ẩn mọi anh em của nó. Dùng `lib/print.ts` → `printChecklist()`.
- **Không render `answer_html` thẳng bằng `dangerouslySetInnerHTML`.** Dùng
  `<SafeHtml>` (`components/safe-html.tsx`): lọc allowlist thẻ trong `lib/sanitize.ts`
  rồi ghi `innerHTML` trong `useEffect` — chạy trong JSX sẽ ra bong bóng rỗng vì React
  không ghi đè nội dung `dangerouslySetInnerHTML` lúc hydrate.
- **Không đọc `localStorage` trong initializer của `useState`** (xem `auth-provider.tsx`)
  — HTML prerender luôn ở trạng thái chưa đăng nhập, đọc sớm gây hydration mismatch.
- API base URL: `NEXT_PUBLIC_API_BASE_URL`, mặc định trỏ domain Railway trong `lib/api.ts`.
- Service worker đăng ký qua `components/pwa-register.tsx`; `public/sw.js` precache từng
  file một (không `addAll`) để 1 file lỗi không làm hỏng cả lần cài.

Phần dưới mô tả bản vanilla `frontend/` — vẫn đúng về design tokens, nguyên tắc UX và
contract API, chỉ khác đường dẫn file.

## Nguyên tắc

- **Giữ nguyên UI/UX đã thiết kế** (bản sắc Hòa Tiến). Thay đổi duy nhất khi chuyển kiến trúc: lớp dữ liệu đổi từ đọc JSON nhúng sang gọi API qua `frontend/js/api.js`.
- **Không chặn trải nghiệm bằng đăng nhập.** Chat, danh mục thủ tục, FAQ, liên hệ dùng được ngay không cần tài khoản. Đăng nhập chỉ mở khoá "lưu lịch sử chat".
- **Responsive.** Phải chạy tốt trên điện thoại (người dùng chính) và màn hình lớn khi trưng bày.
- **A11y tối thiểu.** Focus bàn phím nhìn thấy được, tương phản đủ, `aria-label` cho nút icon.
- **Xử lý lỗi mạng rõ ràng.** Nếu backend không phản hồi (mất mạng/server sập), hiển thị thông báo lịch sự + gợi ý dùng bản dự phòng offline (`frontend/legacy/index.html`) nếu đang ở gian trưng bày.

## Design tokens (CSS variables) — giữ nguyên

| Token | Hex | Vai trò |
|-------|-----|--------|
| `--paddy` | `#2f7d4f` | Xanh lúa — màu thương hiệu chính |
| `--paddy-deep` | `#1f5a38` | Xanh lúa đậm — hover, nhấn |
| `--river` | `#1d6f8b` | Xanh sông Yên — phụ trợ |
| `--river-deep` | `#12495c` | Xanh sông đậm |
| `--rice` | `#e8b84b` | Vàng lúa — điểm nhấn |
| `--cream` | `#faf7ef` | Nền |
| `--ink` | `#1a241f` | Chữ chính |

Font: **Be Vietnam Pro** (display + body) + **Lora** italic (điểm nhấn).

## Lớp gọi API (`frontend/js/api.js`)

```js
const API_BASE_URL = "<đặt qua config, không hardcode nhiều nơi>";

async function apiChat(question) { /* POST /chat, kèm Bearer token nếu đã đăng nhập */ }
async function apiGetProcedures() { /* GET /procedures */ }
async function apiGetFaq() { /* GET /faq */ }
async function apiGetContacts() { /* GET /contacts */ }
async function apiLogin(email, password) { /* POST /auth/login, lưu token */ }
async function apiRegister(email, password, displayName) { /* POST /auth/register */ }
async function apiGetHistory() { /* GET /chat/history, cần token */ }
```

Token lưu ở `localStorage` (chấp nhận được cho MVP demo công khai — không chứa dữ liệu nhạy cảm).

## Tính năng bổ sung (feature pack 2026-08)

- **Voice input**: Web Speech API (`vi-VN`), nút mic cạnh ô chat — tự ẩn nếu trình duyệt không hỗ trợ.
- **In checklist hồ sơ**: nút 🖨️ trong câu trả lời thủ tục + modal chi tiết; render vào `#printArea`, print CSS chỉ in phần này.
- **Feedback 👍👎** dưới mỗi câu trả lời bot (`POST /chat/feedback` với `message_id`).
- **Chips động** theo top thủ tục được hỏi (`GET /chat/stats/public`), fallback 4 chip mặc định; hero hiện "N câu hỏi đã trả lời" khi N ≥ 10.
- **Chia sẻ**: `navigator.share` trên mobile (sheet có Zalo), desktop fallback popover QR + copy link.
- **PWA**: `manifest.webmanifest` + `sw.js` (network-first shell tĩnh, không cache API) — mất mạng vẫn mở được shell. Đổi tên `CACHE` trong `sw.js` khi cần force refresh.
- **Thống kê admin**: nút 📊 trong dropdown user (chỉ role admin) → modal đọc `GET /admin/stats`.
- **A11y modal**: focus trap + trả focus (`trapFocus`/`releaseFocus`), card thủ tục focus + mở bằng Enter được.
- **Lịch sử chat**: click item render lại answer đã lưu, không gọi lại `/chat`.

## Section mới cần thêm so với bản offline

- **Đăng nhập / Đăng ký** (modal hoặc trang riêng nhỏ gọn).
- **Lịch sử chat của tôi** (chỉ hiện khi đã đăng nhập).
- Trạng thái "đang tải" khi gọi API (thay cho hiệu ứng typing giả lập cố định thời gian).

## Cấu trúc trang (thứ tự section) — không đổi

`Hero → Trợ lý AI (chat) → Danh mục thủ tục → FAQ → Liên hệ (+ QR cổng) → Footer`
(+ Đăng nhập/Đăng ký ở header, Lịch sử chat trong khu vực chat khi đã đăng nhập)

## Khi sửa CSS

- Cẩn thận specificity giữa selector theo class và theo element.
- Mọi màu phải lấy từ CSS variables, không hardcode hex rải rác.
