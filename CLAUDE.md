# CLAUDE.md — Hòa Tiến AI Assistant

> File điều hướng cho Claude Code. Đọc file này đầu tiên mỗi phiên làm việc.

## Dự án là gì

**Hòa Tiến AI Assistant** — hệ thống trợ lý hành chính số cho người dân xã Hòa Tiến (TP Đà Nẵng). Người dân hỏi bằng tiếng Việt tự nhiên, trợ lý tra cứu thủ tục hành chính, hướng dẫn hồ sơ cần chuẩn bị, cung cấp QR nộp trực tuyến và thông tin liên hệ UBND.

Sản phẩm dự thi phần **"Ý tưởng sáng tạo · Hòa Tiến số"**. Bản triển khai được **deploy thật** để ban giám khảo, người dự khảo, khán giả bấm vào trải nghiệm trực tiếp (không phải demo local nữa) — chấm điểm dựa trên: ý tưởng/thông điệp, nội dung tuyên truyền, tính sáng tạo–ứng dụng–hiệu quả thực tiễn, khả năng triển khai/nhân rộng.

## Kiến trúc hệ thống

```
┌─────────────┐      HTTPS/REST      ┌──────────────┐      SQL      ┌──────────────┐
│  Frontend   │  ──────────────────▶ │   Backend    │ ────────────▶ │  PostgreSQL  │
│  (static)   │ ◀──────────────────  │   FastAPI    │ ◀──────────── │              │
│  Vercel/    │        JWT           │  Railway/    │               │  Railway/    │
│  Netlify    │                      │  Render      │               │  Render      │
└─────────────┘                      └──────────────┘               └──────────────┘
```

- **Frontend**: static HTML/CSS/JS (giữ nguyên UI/UX đã thiết kế — bản sắc Hòa Tiến). Gọi backend qua `fetch` thay vì đọc JSON nhúng. Deploy Vercel hoặc Netlify.
- **Backend**: FastAPI. Xử lý auth (JWT), CRUD thủ tục/FAQ/liên hệ, endpoint chat (retrieve + generate), lưu lịch sử chat theo user. Deploy Railway hoặc Render.
- **Database**: PostgreSQL. Bảng cho procedures, faq, contacts, users, chat_history. Deploy cùng Railway/Render (managed Postgres).
- **Auth**: JWT-based. Hai vai trò — `admin` (quản lý nội dung) và `user` (người dùng thường, có lịch sử chat). Khách vãng lai (giám khảo bấm thử) có thể dùng ở chế độ ẩn danh giới hạn — xem `rules/auth.md`.

> Bản offline single-file trước đây (`index.html` nhúng KB) được giữ lại làm **bản dự phòng demo** khi mất mạng tại chỗ — xem `legacy/`. Bản chính thức để giám khảo/khán giả trải nghiệm là hệ thống deploy thật.

## Nguyên tắc kiến trúc (KHÔNG vi phạm)

1. **Tách lớp AI rõ ràng.** Luồng: `KB (DB) → retrieve() → generate()`. Nâng lên RAG thật (embedding + vector search + LLM API) không được đổi contract giữa các lớp.
2. **Không hallucinate.** Trợ lý CHỈ trả lời trong phạm vi dữ liệu trong DB. Không có dữ liệu → hướng người dân liên hệ UBND. Luôn kèm dẫn nguồn.
3. **Auth tối giản, đúng vai trò.** Không thu thập dữ liệu ngoài nhu cầu (email/username + mật khẩu hash). Không lưu thông tin cá nhân nhạy cảm.
4. **Có kế hoạch dự phòng khi demo trực tiếp.** Vì hệ thống phụ thuộc mạng/server, luôn có phương án B (`legacy/index.html` offline) nếu deploy sập lúc thuyết trình.
5. **Migration có kiểm soát.** Không sửa DB bằng tay trên production — dùng migration script (Alembic).

## Cấu trúc repo

```
frontend/                    # Static site — deploy Vercel/Netlify
  index.html, css/, js/
  js/api.js                  # Lớp gọi backend (thay cho fetch KB tĩnh)
backend/                     # FastAPI — deploy Railway/Render
  app/
    main.py
    routers/                 # auth, procedures, faq, contacts, chat, admin
    models/                  # SQLAlchemy models
    schemas/                 # Pydantic schemas
    services/                # retrieve(), generate(), auth logic
  alembic/                   # DB migrations
  requirements.txt
legacy/                      # Bản offline single-file cũ — dự phòng khi demo mất mạng
  index.html
data/
  seed-knowledge-base.json   # Dữ liệu gốc để seed vào DB (nguồn sự thật ban đầu)
rules/                       # Đặc tả kỹ thuật & quy ước — đọc trước khi sửa code liên quan
docs/                        # SRS, kịch bản thuyết minh, tài liệu dự thi
```

## Quy tắc làm việc với Claude Code

- Trước khi sửa **backend/API** → đọc `rules/backend.md`.
- Trước khi sửa **auth/phân quyền** → đọc `rules/auth.md`.
- Trước khi sửa **schema DB** → đọc `rules/data-schema.md`, luôn tạo migration Alembic, không sửa tay.
- Trước khi sửa **logic AI** (retrieve/generate) → đọc `rules/ai-module.md`.
- Trước khi sửa **frontend** → đọc `rules/frontend.md`.
- Trước khi **deploy** → đọc `rules/deploy.md`.
- Không thêm dependency nặng ngoài nhu cầu MVP. Ưu tiên chạy đúng hạn hội trại hơn là kiến trúc hoàn hảo.

## Trạng thái hiện tại

- [x] Bản offline single-file (giữ làm dự phòng ở `legacy/`)
- [x] Knowledge base gốc (JSON) — dùng làm seed data
- [x] Backend FastAPI: models, routers, auth (đã test end-to-end)
- [x] Database PostgreSQL: schema + migration Alembic + seed (đã chạy thử, idempotent)
- [x] Frontend: chuyển từ đọc JSON nhúng sang gọi API (đã test qua trình duyệt thật)
- [x] Auth: đăng ký/đăng nhập user thường + admin, lưu lịch sử chat (đã test qua UI)
- [x] Retrieval: đã sửa lỗi false-positive (stopword filter + ngưỡng điểm), test 15/15 câu mẫu đúng
- [x] Xử lý mất kết nối backend: banner lỗi + trỏ về bản dự phòng offline
- [ ] Deploy: Vercel/Netlify (FE) + Railway/Render (BE + DB) — xem `rules/deploy.md`
- [ ] (Future) Nâng `retrieve()` lên vector similarity search thật
- [ ] (Future) Admin panel UI đầy đủ (hiện tại có API, chưa có giao diện quản trị riêng)

## Đã test (local, PostgreSQL thật)

- Public: `/procedures`, `/faq`, `/contacts` trả đúng dữ liệu đã seed.
- Chat: 10 câu hỏi hợp lệ khớp đúng, 5 câu ngoài phạm vi fallback đúng (không bịa).
- Auth: đăng ký, đăng nhập, sai mật khẩu → 401, JWT hoạt động.
- Phân quyền: user thường gọi `/admin/*` → 403; admin CRUD FAQ → phản ánh ngay trong `/faq` và `/chat`.
- Lịch sử chat: chỉ lưu khi có JWT hợp lệ; khách vãng lai dùng chat bình thường không bị ép đăng nhập.
- Frontend: test qua trình duyệt thật (Playwright) — load dữ liệu từ API, đăng ký qua UI, hỏi & xem lịch sử, banner lỗi khi backend sập.

## Roadmap nâng cấp AI lên RAG thật (khi cần)

1. Chunk dữ liệu procedures/faq trong DB theo từng bản ghi.
2. Sinh embedding (`text-embedding-3-small` hoặc model đa ngữ) → lưu trong `pgvector` (mở rộng ngay trên PostgreSQL đang dùng, không cần vector DB riêng).
3. Thay `retrieve()` trong `backend/app/services/` bằng vector similarity query.
4. Thay `generate()` bằng `callLLM(query, context)` — gọi LLM API, ép grounding + citation.
5. Giữ nguyên response schema của `/chat` để frontend không phải đổi.
