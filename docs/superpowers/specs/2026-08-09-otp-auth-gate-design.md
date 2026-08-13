# Thiết kế: bắt buộc đăng ký + xác thực OTP email trước khi dùng trợ lý AI

Ngày: 2026-08-09 · Trạng thái: đã duyệt

## Vấn đề

Hiện tại ai vào web cũng hỏi trợ lý được, đăng nhập chỉ là tuỳ chọn để lưu lịch sử.
Yêu cầu mới: người dùng phải có tài khoản **đã xác thực OTP** mới dùng được tính năng
hỏi AI, và lịch sử chat gắn với tài khoản đó.

Yêu cầu này đảo ngược nguyên tắc cũ trong `rules/auth.md` ("không ép đăng nhập để dùng
thử" — để ban giám khảo bấm vào là hỏi được ngay). Giải pháp dung hoà đã chốt: **cho
khách hỏi thử 3 lượt rồi mới ép đăng ký**.

## Quyết định đã chốt

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Kênh OTP | Chỉ email | SMS ở VN cần hợp đồng nhà mạng + brandname, không kịp hạn hội trại |
| Chặn khách | Cho hỏi thử 3 lượt | Giám khảo vẫn trải nghiệm được ngay, vẫn đạt mục tiêu ép đăng ký |
| Đếm lượt | Guest ID theo thiết bị | Đếm theo IP sẽ hỏng: cả hội trường chung 1 wifi NAT sẽ chia nhau 3 lượt |
| Gửi mail | ~~Resend~~ → **Gmail SMTP** | Đổi khi triển khai: Resend với `onboarding@resend.dev` **chỉ gửi được về đúng email chủ tài khoản**, muốn gửi cho người dân phải có domain xác thực DNS — dự án không có domain. Gmail + App Password gửi được cho mọi địa chỉ ngay, đổi lại ~500 mail/ngày. Nhánh `resend` vẫn giữ trong code cho tương lai. |

## 1. Dữ liệu (1 migration Alembic)

- `users` **+ `email_verified_at`** (`timestamptz NULL`). `NULL` = chưa xác thực.
  Migration backfill `now()` cho toàn bộ user đang có (admin + tài khoản test) để
  không tự khoá mình ra ngoài production.
- Bảng mới **`email_otps`**: `id (uuid pk), email (varchar index), code_hash (varchar),
  expires_at, consumed_at (null), attempt_count (int default 0), created_at`.
  Chỉ lưu **hash** của mã, không lưu mã thật.
- `chat_history` **+ `guest_id`** (`varchar(64) NULL`, index). Đếm hạn mức khách bằng
  chính bảng này thay vì tạo bảng quota riêng — ít code hơn và cho luôn thống kê
  "khách dùng thử rồi bỏ".

## 2. Luồng OTP

Chính sách: mã **6 chữ số**, hạn **10 phút**, sai quá **5 lần** thì mã chết (phải xin mã
mới), gửi lại có cooldown **60 giây**/email và tối đa **5 lần/giờ**/email.

| Endpoint | Hành vi |
|---|---|
| `POST /auth/register` | Tạo user `email_verified_at=NULL`, **không trả token**, sinh OTP, gửi mail. Trả `{email, expires_in_seconds}`. Email đã tồn tại nhưng *chưa xác thực* → cập nhật lại mật khẩu/tên + gửi mã mới (tránh bẫy "email đã dùng" khi người dân bỏ dở giữa chừng). Đã xác thực → 400. |
| `POST /auth/verify-otp` | `{email, code}` → hợp lệ thì set `email_verified_at`, tiêu mã, **trả JWT luôn** (không bắt đăng nhập lại). |
| `POST /auth/resend-otp` | `{email}` → gửi mã mới nếu qua cooldown. |
| `POST /auth/login` | User chưa xác thực → **403** `detail = {code: "email_unverified", message: ...}`; FE tự chuyển sang màn nhập OTP và gọi resend. |

Lỗi có ý nghĩa với FE trả dưới dạng `detail` là object `{code, message}`; lỗi thường vẫn
là chuỗi. FE xử lý được cả hai dạng.

## 3. Cổng lượt hỏi thử cho khách

- FE sinh `guest_id` (UUID v4) lưu localStorage, gửi header `X-Guest-Id` ở mọi request chat.
- `POST /chat` không kèm JWT: đếm `chat_history` có `guest_id` đó và `user_id IS NULL`;
  vượt `FREE_GUEST_TURNS` (env, mặc định 10 — bản thiết kế gốc là 3, nới lên 10 ngày
  14/08/2026 cho buổi thi) → **403** `{code: "guest_quota_exceeded"}`.
- **Câu xã giao không trừ lượt.** "Xin chào"/"cảm ơn" đi qua tầng smalltalk, không phải
  tra cứu thật, nên không tính vào hạn mức (lưu với `guest_id = NULL`).
- Người đã đăng nhập: không giới hạn, lịch sử lưu theo `user_id` như hiện tại.
- Giới hạn đã biết: xoá dữ liệu trình duyệt là reset được hạn mức. Chấp nhận — mục tiêu là
  khuyến khích đăng ký chứ không phải chống gian lận.
- Chat demo ở trang chủ dùng chung hạn mức này (cùng một API).

## 4. Gửi mail

`app/services/email.py`, chọn provider qua env `EMAIL_PROVIDER`:

- `console` (mặc định ở dev): in mã ra log, không cần mạng — chạy test local không tốn mail.
- `smtp` (production hiện tại): Gmail qua `smtplib`, STARTTLS cổng 587, đăng nhập bằng
  App Password. `From` luôn là chính `SMTP_USER` vì Gmail không cho gửi hộ địa chỉ khác.
- `resend`: `POST https://api.resend.com/emails` với `RESEND_API_KEY` — chỉ dùng khi đã
  có domain xác thực DNS.

Gửi qua `BackgroundTasks` để không giữ response. Mail hỏng không được làm hỏng đăng ký:
log lỗi, người dùng bấm "gửi lại mã".

Env mới: `EMAIL_PROVIDER`, `RESEND_API_KEY`, `RESEND_FROM` (mặc định
`Hòa Tiến AI <onboarding@resend.dev>`), `FREE_GUEST_TURNS` (mặc định 10),
`OTP_TTL_MINUTES` (10), `OTP_MAX_ATTEMPTS` (5), `OTP_RESEND_COOLDOWN_SECONDS` (60).

## 5. Frontend (`frontend-next`)

- `lib/api.ts`: helper `guestId()` (tạo/đọc UUID trong localStorage, gắn header
  `X-Guest-Id`), `ApiError` mang thêm `code`, thêm `registerRequestOtp` / `verifyOtp` /
  `resendOtp`.
- `/dang-nhap`: tab Đăng ký thành 2 bước — form thông tin → màn nhập OTP (ô 6 số, đếm
  ngược nút "Gửi lại mã", nút đổi email). Đăng nhập gặp `email_unverified` cũng rơi vào
  màn này.
- `/tro-ly`: khi chưa đăng nhập hiện badge "Còn N lượt hỏi thử"; nhận
  `guest_quota_exceeded` thì thay ô nhập bằng CTA "Đăng ký miễn phí để hỏi tiếp và lưu
  lịch sử".
- Lịch sử chat theo JWT đã chạy sẵn, không phải sửa.

## 6. Kiểm thử

Chạy local với `EMAIL_PROVIDER=console`, lấy OTP từ log. Checklist:

1. Đăng ký → nhận mã trong log → nhập sai 5 lần → mã chết → xin mã mới → nhập đúng → vào được.
2. Mã hết hạn (chỉnh `OTP_TTL_MINUTES=0`) → báo hết hạn.
3. Đăng nhập bằng tài khoản chưa xác thực → nhảy màn OTP.
4. Khách hỏi 3 câu tra cứu → câu thứ 4 bị chặn; xen câu "xin chào" không trừ lượt.
5. Đăng ký xong hỏi tiếp không bị chặn, lịch sử hiện đúng.
6. Tài khoản admin cũ vẫn đăng nhập được sau migration.

## 7. Tài liệu phải cập nhật

`rules/auth.md` (đảo nguyên tắc "không ép đăng nhập"), `rules/frontend.md`,
`rules/deploy.md` (env mới), `CLAUDE.md` (trạng thái).
