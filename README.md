# Hòa Tiến AI Assistant

Hệ thống trợ lý hành chính số cho người dân xã Hòa Tiến (TP Đà Nẵng).
Sản phẩm dự thi "Ý tưởng sáng tạo · Hòa Tiến số" — deploy thật để ban giám khảo,
người dự khảo, khán giả trải nghiệm trực tiếp.

## Đọc trước

`CLAUDE.md` — điều hướng kiến trúc & quy tắc làm việc (đọc đầu tiên).

## Kiến trúc

Frontend (static, Vercel/Netlify) ⇄ Backend (FastAPI, Railway/Render) ⇄ PostgreSQL.
Đã build và test end-to-end local. Chi tiết: `CLAUDE.md`, `rules/backend.md`, `rules/deploy.md`.

## Cấu trúc

- `frontend/` — static HTML/CSS/JS, gọi API qua `js/api.js`
- `backend/` — FastAPI: auth, CRUD, chat (retrieve+generate), lịch sử chat
- `data/seed-knowledge-base.json` — dữ liệu gốc để seed DB
- `legacy/index.html` — bản offline single-file cũ, **giữ làm phương án dự phòng** khi demo mất mạng
- `rules/` — đặc tả kỹ thuật (backend, auth, data-schema, ai-module, frontend, deploy, build)
- `docs/` — SRS + kịch bản thuyết minh 5 phút

## Chạy nhanh (dev local)

```bash
# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # sửa DATABASE_URL nếu cần
alembic upgrade head
python3 scripts/seed_from_json.py
python3 scripts/create_admin.py admin@example.com MatKhauManh "Quản trị viên"
uvicorn app.main:app --reload --port 8000

# Frontend (terminal khác)
cd frontend
python3 -m http.server 5500
# mở http://localhost:5500
```

Chi tiết đầy đủ: `rules/build.md`. Hướng dẫn deploy production: `rules/deploy.md`.
