# rules/frontend.md — Quy ước giao diện

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
