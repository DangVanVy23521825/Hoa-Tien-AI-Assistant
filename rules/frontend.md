# rules/frontend.md — Quy ước giao diện

## Frontend chính hiện tại: `frontend-next/` (Next.js 16)

Từ 08/2026, bản deploy chính là **`frontend-next/`** — Next.js 16 (App Router, Turbopack)
+ Tailwind CSS v4 + shadcn/ui (base-ui) + TypeScript. `frontend/` (vanilla HTML/CSS/JS)
giữ lại làm tham chiếu; bản offline dự phòng nằm ở `frontend-next/public/legacy/index.html`
(copy của `frontend/legacy/index.html`, phải giữ đồng bộ).

### Bản dự phòng offline — ngưỡng retrieval RIÊNG, cố ý khác bản online

Cập nhật 12/08/2026 khi KB tăng lên 225 bản ghi:

- KB nhúng trong `index.html` nay là **toàn bộ** `data/seed-knowledge-base.json` (~180 KB),
  kèm `legacy/data/knowledge-base.json` cho trường hợp còn mạng nhưng backend sập. Trước đó
  bản nhúng chỉ có ~7 KB và **thiếu hẳn `knowledge_articles`** — mất 97/225 bản ghi.
- `retrieve()` chỉ đánh chỉ mục **tiêu đề + từ khoá**, không lấy toàn văn nội dung.
- Ngưỡng: `MIN_MATCH_SCORE = 10` và `MIN_COVERAGE = 0.5` — **cao hơn hẳn bản online (4.0)**.
  Bản online còn cổng cosine chặn câu rác, bản này chỉ có keyword; bỏ dấu xong "phở bò"
  trùng token với "phổ biến / bộ" nên câu rác nào cũng nhặt được 4–8 điểm. Đo trên đúng bộ
  câu của `eval_retrieval.py`: ngưỡng 10 + phủ 50% cho **20/20 câu hợp lệ · 14/14 câu rác
  fallback**; hạ xuống 8 thì lọt 1 câu rác.

Sửa KB mà quên đồng bộ 3 chỗ (`frontend/legacy/`, `frontend-next/public/legacy/`, và file
`data/knowledge-base.json` trong cả hai) thì bản dự phòng trả lời thiếu so với bản live.

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

## Ảnh nền quê hương + mascot (2026-08-09)

Nguồn gốc nằm ngoài repo build ở `images/`; bản dùng thật đã tối ưu trong `frontend-next/public/`.

| File | Nguồn | Dùng ở đâu |
|------|-------|-----------|
| `public/bg/hoa-tien.jpg` | ảnh drone xã Hòa Tiến | Nền cố định toàn site |
| `public/mascot/mascot.png` (900²) | mascot cú AI | Hero trang chủ |
| `public/mascot/mascot-face.png` (512²) | crop đầu mascot | Logo header, avatar chat |
| `public/icons/icon-192/512(-maskable).png` | mascot-face trên nền kem | Favicon + PWA |
| `public/header/hoa-tien-band.jpg` (622×280) | ảnh xóm làng nhìn từ trên cao | Dải ảnh nửa phải header |

- **Nền**: `components/site-background.tsx` — layer `fixed inset-0 -z-10`, ảnh `blur-[3px] scale-105`
  phủ `bg-cream/92`. Vì thế `body` phải giữ `bg-transparent` (màu kem đặt ở `html`); đặt lại
  `bg-background` cho `body` sẽ che mất ảnh.
- **Section full-bleed đục sẽ che nền.** Dải "Cách hoạt động" (trang chủ) và khung `/tro-ly`
  dùng `from-white/75` và `/55`. Thêm section nền đục mới thì cân nhắc hạ opacity tương tự.
- **Avatar mascot**: dùng `components/mascot-avatar.tsx`, không tự viết `<Image>` mới. Component
  đặt `width/height` bằng inline style vì hàng tin nhắn là flex `align-items: stretch` — thiếu
  chiều cao tường minh thì ảnh bị kéo giãn dọc theo chiều cao bong bóng.
- Layer nền là con trực tiếp của `<body>` nên `@media print` (`body > *:not(#printArea)`) tự ẩn nó.

## Header + footer (2026-08-10)

Header (`components/header.tsx`) rộng `max-w-7xl` (rộng hơn nội dung trang `max-w-6xl` là cố ý)
và gồm 2 tầng:

1. **Thanh chính** — trái là mascot + tên app, nửa phải là `hoa-tien-band.jpg` phủ gradient kem
   `from-cream via-cream/45 to-cream/10` cộng một lớp `backdrop-blur` + quầng sáng trắng ở mép
   trái, để ảnh loang ra từ tên app chứ không cắt khối. Chỉnh 3 lớp này phải xem lại bằng mắt,
   không đoán theo số.
   - Nav và nút đăng nhập **nằm đè lên ảnh** nên phải giữ nền riêng (`bg-cream/70` cho nav pill,
     `bg-cream/80` cho nút). Bỏ nền đi là chữ chìm vào mái nhà sáng trong ảnh.
   - Dải ảnh ẩn dưới `sm`; dòng "TRỢ LÝ HÀNH CHÍNH SỐ" cũng ẩn dưới `sm` vì hẹp thì xuống hàng
     làm header cao vống.
2. **Dải thông báo xanh** — câu miễn trừ ("hệ thống thử nghiệm phục vụ dự thi…"). Trước ở footer,
   chuyển lên header để giám khảo/người dân đọc trước khi hỏi. Header sticky nên dải này phải
   **luôn gọn 1 dòng ở desktop**; câu thứ hai `hidden sm:inline`.

Footer (`components/footer.tsx`) giờ là **khối liên hệ UBND** (địa chỉ, SĐT bấm gọi được, giờ làm
việc, cổng thông tin + QR), cộng một dòng chân trang ghi sản phẩm dự thi. Đây là client component
gọi `GET /contacts`, khởi tạo bằng hằng `FALLBACK` chép từ `data/seed-knowledge-base.json` —
backend chết thì người dân vẫn thấy số điện thoại xã. **Sửa seed thì sửa luôn `FALLBACK`.**

Trang `/lien-he` **đã xoá** (2026-08-10) vì trùng hoàn toàn với footer; mục "Liên hệ" cũng đã bỏ
khỏi nav, nút CTA trang chủ đổi thành `tel:` gọi thẳng UBND. Bản offline dự phòng
`public/legacy/index.html` vẫn giữ mục `#lien-he` của riêng nó — không đụng vào.

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
- **Chips gợi ý** dưới nhãn "Bạn có thể hỏi:" — mặc định là 5 câu hỏi hoàn chỉnh đã biên tập, mỗi câu **đã thử trên API thật và khớp dữ liệu**; thêm câu mới thì phải thử trước, chip rơi vào câu từ chối là mất điểm ngay trước mặt người dùng (ví dụ "Thủ tục cấp CCCD?" không khớp — xã không cấp CCCD). Điện thoại chỉ hiện 3 chip. `GET /chat/stats/public` trả `top_questions` nhưng đó là **tên thủ tục**, không phải câu hỏi, nên chỉ nhận khi đúng dạng câu hỏi ngắn (kết thúc "?", ≤52 ký tự); muốn chip động thật thì backend phải trả câu người dùng gõ. Hero hiện "N câu hỏi đã trả lời" khi N ≥ 10.
- **Chia sẻ**: `navigator.share` trên mobile (sheet có Zalo), desktop fallback popover QR + copy link.
- **PWA**: `manifest.webmanifest` + `sw.js` (network-first shell tĩnh, không cache API) — mất mạng vẫn mở được shell. Đổi tên `CACHE` trong `sw.js` khi cần force refresh.
- **Thống kê admin**: nút 📊 trong dropdown user (chỉ role admin) → modal đọc `GET /admin/stats`.
- **A11y modal**: focus trap + trả focus (`trapFocus`/`releaseFocus`), card thủ tục focus + mở bằng Enter được.
- **Lịch sử chat**: click item render lại answer đã lưu, không gọi lại `/chat`.

## Cổng đăng ký + OTP (2026-08)

- `lib/api.ts` tự sinh `hoatien_guest_id` (UUID trong localStorage) và gắn header
  `X-Guest-Id` cho mọi request khi chưa có token. `ApiError` mang thêm `.code`, đọc từ
  `detail = {code, message}` của backend.
- `/tro-ly`: badge "Còn N lượt hỏi thử" ở header khung chat (chỉ khi chưa đăng nhập; lấy
  từ `GET /chat/guest-quota` lúc mở trang, rồi từ `guest_turns_left` trong mỗi response
  `/chat`). Gặp `code === "guest_quota_exceeded"` → thay cả hàng chips lẫn ô nhập bằng
  khối CTA đăng ký.
- `/dang-nhap`: tab Đăng ký là 2 bước — form → màn nhập mã 6 số (đếm ngược gửi lại 60s,
  nút đổi email). Đăng nhập trả `code === "email_unverified"` cũng rơi vào màn này và tự
  gọi `resend-otp`.
- Trang chủ có demo chat **theo kịch bản, không gọi API**, nên không tiêu lượt hỏi thử;
  ô nhập ở đó chuyển sang `/tro-ly?q=…` mới thực sự gọi backend.

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
