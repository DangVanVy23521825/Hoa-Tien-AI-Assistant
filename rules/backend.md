# rules/backend.md — Backend (FastAPI)

## Trách nhiệm

Backend phục vụ: auth, CRUD nội dung (procedures/faq/contacts), endpoint chat (retrieve+generate), lưu lịch sử chat theo user.

## Cấu trúc thư mục

```
backend/
  app/
    main.py              # Khởi tạo FastAPI, mount routers, CORS
    core/
      config.py           # Settings từ env (DATABASE_URL, JWT_SECRET, ...)
      security.py          # Hash mật khẩu, tạo/giải mã JWT
    db/
      session.py           # SQLAlchemy engine + session
    models/                # SQLAlchemy ORM models (1 file/bảng)
    schemas/                # Pydantic request/response schemas
    routers/
      auth.py              # POST /auth/register, /auth/login
      procedures.py         # GET /procedures, GET /procedures/{id}
      faq.py                # GET /faq
      contacts.py           # GET /contacts
      chat.py               # POST /chat  (retrieve + generate, lưu chat_history nếu có user)
      admin.py              # CRUD procedures/faq/contacts — yêu cầu role admin
    services/
      retrieval.py          # retrieve(query, topK) — đọc từ DB
      generation.py          # generate(query, hits) — hoặc callLLM khi nâng RAG
  alembic/                  # migrations
  requirements.txt
  .env.example
```

## Endpoint chính (đối chiếu SRS mục 11)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| POST | `/auth/register` | — | Tạo tài khoản user thường |
| POST | `/auth/login` | — | Đăng nhập, trả JWT |
| GET | `/procedures` | — (public) | Danh mục thủ tục |
| GET | `/procedures/{id}` | — (public) | Chi tiết 1 thủ tục |
| GET | `/faq` | — (public) | Danh sách FAQ |
| GET | `/contacts` | — (public) | Thông tin liên hệ |
| POST | `/chat` | optional | Gửi câu hỏi, nhận trả lời; nếu có JWT → lưu vào `chat_history` |
| GET | `/chat/history` | user | Lấy lịch sử chat của user hiện tại |
| POST/PUT/DELETE | `/admin/procedures/*`, `/admin/faq/*`, `/admin/contacts/*` | admin | Quản trị nội dung |

> **Khách vãng lai (giám khảo) không bắt buộc đăng nhập** để dùng `/chat`, `/procedures`, `/faq`, `/contacts` — chỉ cần đăng nhập nếu muốn lưu lịch sử. Đây là quyết định UX quan trọng: đừng chặn trải nghiệm demo bằng tường đăng nhập.

## Nguyên tắc

1. Mọi input qua Pydantic schema, không nhận dữ liệu thô chưa validate.
2. Endpoint public (`/chat`, `/procedures`, `/faq`, `/contacts`) không được để lộ dữ liệu admin/user khác.
3. CORS: chỉ whitelist domain frontend thật (Vercel/Netlify URL) + localhost khi dev.
4. `retrieve()`/`generate()` trong `services/` phải giữ cùng chữ ký hàm như bản offline cũ (`rules/ai-module.md`) để logic cũ dễ port sang.
5. Lỗi trả về theo chuẩn: `{ "detail": "..." }`, đúng HTTP status code (400/401/403/404/500).
6. Không log nội dung câu hỏi/trả lời chứa thông tin định danh cá nhân ra log thô nếu không cần thiết.
