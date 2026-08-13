# rules/auth.md — Authentication & phân quyền

## Vai trò

| Role | Quyền |
|---|---|
| **Khách (ẩn danh)** | Xem `/procedures`, `/faq`, `/contacts` không giới hạn. Được hỏi `/chat` **tối đa 10 lượt tra cứu** (`FREE_GUEST_TURNS`) rồi phải đăng ký. Không lưu lịch sử. |
| **`user`** (đã xác thực email) | Hỏi `/chat` không giới hạn + lưu và xem lại lịch sử chat của mình. |
| **`admin`** | Toàn quyền CRUD nội dung (procedures/faq/contacts). Không cần quyền trên chat của user khác trừ khi có yêu cầu kiểm duyệt cụ thể. |

## Cơ chế

- **JWT** (access token), thời hạn ngắn (ví dụ 24h — đủ cho một buổi hội trại).
- Mật khẩu hash bằng `bcrypt` (qua `passlib`), không bao giờ lưu plaintext.
- Token gửi qua header `Authorization: Bearer <token>`.
- Endpoint public không yêu cầu token; endpoint có `Depends(get_current_user)` mới bắt buộc.
- **Chỉ tài khoản đã xác thực email mới đăng nhập được.** `/auth/register` không trả token; token chỉ cấp sau khi `/auth/verify-otp` thành công.

### Xác thực email bằng OTP

| Endpoint | Hành vi |
|---|---|
| `POST /auth/register` | Tạo user `email_verified_at = NULL`, gửi mã 6 số qua email, trả `{email, expires_in_seconds}`. Email đã tồn tại nhưng **chưa xác thực** → cho đăng ký đè (cập nhật mật khẩu/tên + gửi mã mới) để người bỏ dở không bị kẹt vĩnh viễn. Đã xác thực → 400. |
| `POST /auth/verify-otp` | Đúng mã → set `email_verified_at`, trả JWT luôn. |
| `POST /auth/resend-otp` | Gửi lại mã, chịu cooldown. |
| `POST /auth/login` | Chưa xác thực → **403** `detail = {code: "email_unverified", …}`. |

Chính sách mã (env, xem `core/config.py`): 6 chữ số, hạn `OTP_TTL_MINUTES` (10),
sai quá `OTP_MAX_ATTEMPTS` (5) thì mã chết, gửi lại cách `OTP_RESEND_COOLDOWN_SECONDS`
(60) và tối đa `OTP_MAX_SENDS_PER_HOUR` (5) mã/giờ/email. Chỉ lưu **hash** của mã
(bảng `email_otps`); mỗi lần cấp mã mới thì mọi mã cũ chưa dùng bị vô hiệu.

Cooldown đếm theo **email**, không theo IP — ở hội trại cả hội trường chung một IP NAT
nên giới hạn theo IP sẽ chặn nhầm người thật.

Gửi mail: `app/services/email.py`, chọn provider qua `EMAIL_PROVIDER` — `console`
(dev: in mã ra log), **`gas`** (production: relay qua Google Apps Script chạy dưới danh
nghĩa Gmail dự án, vì **Railway chặn cổng SMTP**), `smtp` (Gmail App Password — chỉ chạy
ở local) hoặc `resend` (cần domain xác thực DNS). Xem bảng so sánh và lý do loại từng
phương án trong `rules/deploy.md`.
**Mail hỏng không được làm hỏng đăng ký**:
mọi lỗi gửi mail đều nuốt lại và log, người dùng bấm "Gửi lại mã".

### Cổng hạn mức cho khách

- Frontend sinh UUID lưu localStorage (`hoatien_guest_id`), gửi kèm header `X-Guest-Id`.
- `/chat` không có JWT: đếm `chat_history` theo `guest_id`; vượt `FREE_GUEST_TURNS`
  → **403** `{code: "guest_quota_exceeded"}`. `GET /chat/guest-quota` cho FE hiện badge
  "còn N lượt".
- **Câu xã giao không trừ lượt** — chỉ câu đi vào retrieval mới tính (lưu `guest_id`;
  câu chào lưu `guest_id = NULL`).
- Đếm theo thiết bị chứ **không theo IP**, vì lý do wifi NAT nói trên.
- Giới hạn đã biết và chấp nhận: xoá dữ liệu trình duyệt là reset được 3 lượt. Mục tiêu
  là khuyến khích đăng ký, không phải chống gian lận.

## Dữ liệu tài khoản (tối giản)

`users`: `id, email (unique), password_hash, display_name, role ('user'|'admin'),
email_verified_at, created_at`.

**Không thu thập**: số điện thoại thật, CCCD, địa chỉ nhà, hay bất kỳ dữ liệu định danh nhạy cảm nào — không cần thiết cho MVP và tránh rủi ro bảo mật khi demo công khai. (Đã cân nhắc OTP qua SMS và loại: cần hợp đồng nhà mạng + brandname, không kịp hạn hội trại.)

## Quy tắc UX quan trọng

- **Cho hỏi thử trước, ép đăng ký sau.** Giám khảo/khán giả bấm vào phải hỏi được ngay 3 câu; hết lượt mới hiện lời mời đăng ký ("hỏi không giới hạn + lưu lịch sử"). Không bao giờ dựng tường đăng nhập ngay ở màn đầu.
- Đăng nhập bằng tài khoản chưa xác thực phải đưa thẳng vào màn nhập OTP + tự gửi lại mã, không bắt người dùng tự mò sang tab đăng ký.
- Tài khoản admin đầu tiên tạo qua seed script (`backend/scripts/create_admin.py`), không lộ endpoint đăng ký admin công khai. Tài khoản tạo bằng script này phải có sẵn `email_verified_at`.

## Bảo mật tối thiểu cho bản public-facing

- Rate limit endpoint `/auth/login`, `/auth/register|verify-otp|resend-otp` (`RATE_LIMIT_OTP`) và `/chat` để chống spam (`slowapi`).
- HTTPS bắt buộc (Vercel/Netlify + Railway/Render đều tự cấp mặc định).
- Không trả chi tiết lỗi hệ thống ra ngoài (ẩn stack trace ở production).
- `JWT_SECRET`, `DATABASE_URL`, `RESEND_API_KEY` chỉ để trong biến môi trường, không commit vào repo (`.env` nằm trong `.gitignore`).
