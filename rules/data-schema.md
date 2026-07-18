# rules/data-schema.md — Schema cơ sở dữ liệu

Nguồn sự thật ban đầu vẫn là `data/seed-knowledge-base.json` (dùng để seed), nhưng **nguồn sự thật vận hành là PostgreSQL**. Mọi thay đổi schema phải qua Alembic migration, không sửa tay trên production.

## Bảng `procedures`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | uuid / serial PK | |
| `code` | varchar, unique | ví dụ `KS-01` |
| `category` | varchar | Hộ tịch / Chứng thực / Cư trú… |
| `name` | varchar | |
| `keywords` | text[] hoặc jsonb | cách người dân hỏi thực tế — quyết định chất lượng retrieval |
| `description` | text | |
| `documents` | jsonb (array string) | hồ sơ cần chuẩn bị |
| `fee` | varchar | ghi rõ "(tham khảo)" nếu chưa đối soát |
| `processing_time` | varchar | |
| `place_of_submission` | varchar | |
| `online_url` | varchar | dùng sinh QR |
| `legal_basis` | varchar | dùng cho dẫn nguồn |
| `created_at`, `updated_at` | timestamp | |

## Bảng `faq`

| Cột | Kiểu |
|---|---|
| `id` | uuid/serial PK |
| `question` | text |
| `keywords` | jsonb |
| `answer` | text |
| `created_at`, `updated_at` | timestamp |

## Bảng `contacts`

Có thể là 1 bảng single-row hoặc key-value đơn giản: `office, address, phone, portal_url, public_service_url, working_hours (jsonb)`.

## Bảng `users`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | uuid/serial PK | |
| `email` | varchar, unique | |
| `password_hash` | varchar | bcrypt |
| `display_name` | varchar | |
| `role` | enum('user','admin') | |
| `created_at` | timestamp | |

## Bảng `chat_history`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | uuid/serial PK | |
| `user_id` | FK → `users.id`, nullable | null nếu khách ẩn danh không lưu |
| `question` | text | |
| `answer` | text | |
| `matched_source_type` | varchar | `procedure` / `faq` / `contact` / `commune` / `none` |
| `matched_source_id` | varchar, nullable | |
| `created_at` | timestamp | |

## Quan hệ

`users (1) ──── (n) chat_history`. `procedures`/`faq`/`contacts` độc lập, không có FK ràng buộc lẫn nhau ở MVP.

## Quy tắc khi thêm/sửa dữ liệu

1. Sửa qua endpoint `/admin/*` hoặc migration + seed script — không sửa tay trực tiếp trên DB production.
2. `keywords` phải đa dạng cách hỏi (khẩu ngữ, viết tắt, từ đồng nghĩa).
3. Phí/thời gian chưa đối soát chính thức → ghi "(tham khảo)".
4. Không đưa thông tin cá nhân/nhạy cảm vào các bảng nội dung công khai.
5. Khi seed lần đầu, dùng script đọc `data/seed-knowledge-base.json` → insert vào `procedures`/`faq`/`contacts`.
