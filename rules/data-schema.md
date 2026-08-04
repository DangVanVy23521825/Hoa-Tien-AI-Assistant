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
| `embedding` | vector(1024), pgvector | semantic embedding (bge-m3, self-host) — nullable, dùng cho hybrid retrieval, xem `rules/ai-module.md` |
| `created_at`, `updated_at` | timestamp | |

## Bảng `faq`

| Cột | Kiểu |
|---|---|
| `id` | uuid/serial PK |
| `question` | text |
| `keywords` | jsonb |
| `answer` | text |
| `embedding` | vector(1024), pgvector — nullable |
| `created_at`, `updated_at` | timestamp |

## Bảng `knowledge_articles`

Lịch sử / địa danh / làng nghề — mỗi bản ghi là 1 đơn vị kiến thức độc lập cho `/chat`, quản lý qua `/admin/articles`.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | uuid PK | |
| `category` | varchar(50) | `history` \| `landmark` \| `craft_village` |
| `title` | varchar(255) | |
| `keywords` | jsonb | |
| `content` | text | |
| `source_citation` | varchar(500) | dùng cho dẫn nguồn |
| `embedding` | vector(1024), pgvector — nullable | |
| `created_at`, `updated_at` | timestamp | |

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

`users (1) ──── (n) chat_history`. `procedures`/`faq`/`knowledge_articles`/`contacts` độc lập, không có FK ràng buộc lẫn nhau ở MVP.

## Quy tắc khi thêm/sửa dữ liệu

1. Sửa qua endpoint `/admin/*` hoặc migration + seed script — không sửa tay trực tiếp trên DB production.
2. `keywords` phải đa dạng cách hỏi (khẩu ngữ, viết tắt, từ đồng nghĩa) — vẫn cần dù có `embedding`, vì retrieval là hybrid (keyword + semantic).
3. Phí/thời gian chưa đối soát chính thức → ghi "(tham khảo)".
4. Không đưa thông tin cá nhân/nhạy cảm vào các bảng nội dung công khai.
5. Khi seed lần đầu, dùng script đọc `data/seed-knowledge-base.json` → insert vào `procedures`/`faq`/`knowledge_articles`/`contacts`.
6. Sau khi thêm/sửa qua `/admin/*` hoặc seed, `embedding` được tự động tính lại — không cần thao tác thủ công. Xem `rules/ai-module.md` mục "Vận hành embedding" khi cần backfill hàng loạt.
