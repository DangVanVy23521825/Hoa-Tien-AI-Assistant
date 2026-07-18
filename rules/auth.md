# rules/auth.md — Authentication & phân quyền

## Vai trò

| Role | Quyền |
|---|---|
| **Khách (ẩn danh)** | Dùng `/chat`, xem `/procedures`, `/faq`, `/contacts`. Không lưu lịch sử. |
| **`user`** | Như khách + đăng nhập để lưu và xem lại lịch sử chat của mình. |
| **`admin`** | Toàn quyền CRUD nội dung (procedures/faq/contacts). Không cần quyền trên chat của user khác trừ khi có yêu cầu kiểm duyệt cụ thể. |

## Cơ chế

- **JWT** (access token), thời hạn ngắn (ví dụ 24h — đủ cho một buổi hội trại).
- Mật khẩu hash bằng `bcrypt` (qua `passlib`), không bao giờ lưu plaintext.
- Token gửi qua header `Authorization: Bearer <token>`.
- Endpoint public không yêu cầu token; endpoint có `Depends(get_current_user)` mới bắt buộc.

## Dữ liệu tài khoản (tối giản)

`users`: `id, email (unique), password_hash, display_name, role ('user'|'admin'), created_at`.

**Không thu thập**: số điện thoại thật, CCCD, địa chỉ nhà, hay bất kỳ dữ liệu định danh nhạy cảm nào — không cần thiết cho MVP và tránh rủi ro bảo mật khi demo công khai.

## Quy tắc UX quan trọng

- **Không ép đăng nhập để dùng thử.** Giám khảo/khán giả bấm vào phải hỏi được ngay. Đăng nhập chỉ là tính năng cộng thêm ("lưu lịch sử của bạn"), đặt ở góc trên, không chặn luồng chính.
- Tài khoản admin đầu tiên tạo qua seed script (`backend/scripts/create_admin.py`), không lộ endpoint đăng ký admin công khai.

## Bảo mật tối thiểu cho bản public-facing

- Rate limit endpoint `/auth/login` và `/chat` để chống spam (ví dụ `slowapi`).
- HTTPS bắt buộc (Vercel/Netlify + Railway/Render đều tự cấp mặc định).
- Không trả chi tiết lỗi hệ thống ra ngoài (ẩn stack trace ở production).
- `JWT_SECRET`, `DATABASE_URL` chỉ để trong biến môi trường, không commit vào repo (`.env` nằm trong `.gitignore`).
