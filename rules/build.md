# rules/build.md — Chạy dev local

## Yêu cầu

- Python 3.11+, PostgreSQL (local hoặc Docker), Node không bắt buộc (frontend là static HTML/CSS/JS thuần).

## Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt   # tải torch CPU + bge-m3 deps, có thể mất vài phút lần đầu
cp .env.example .env   # điền DATABASE_URL, JWT_SECRET, GEMINI_API_KEY local
alembic upgrade head
python3 scripts/seed_from_json.py            # nạp data/seed-knowledge-base.json vào DB, tự embed bằng bge-m3 (tải model ~2.2GB lần đầu, không cần GEMINI_API_KEY)
python3 scripts/backfill_embeddings.py        # chỉ cần chạy nếu seed từng lỗi/bỏ sót embedding
uvicorn app.main:app --reload --port 8000
```

> Embedding dùng `BAAI/bge-m3` self-host qua `sentence-transformers` (không cần API key) — chỉ Gemini (generation) mới cần `GEMINI_API_KEY`. Lần chạy đầu tiên gọi tới embedding sẽ tải model từ HuggingFace Hub, cần mạng ổn định.

## Frontend

```bash
cd frontend
python3 -m http.server 5500
# mở http://localhost:5500, đảm bảo API_BASE_URL trỏ tới http://localhost:8000
```

## Database local nhanh (Docker)

Cần image có sẵn extension `pgvector` (RAG dùng embedding lưu trong PostgreSQL):

```bash
docker run --name hoatien-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hoatien -p 5432:5432 -d pgvector/pgvector:pg16
```

## Kiểm thử nhanh trước khi demo/deploy

1. `/chat` trả lời đúng các câu hỏi mẫu (xem `docs/demo-script.md`) — cả khi có token lẫn không có token.
2. Đăng ký → đăng nhập → hỏi vài câu → xem lịch sử chat hiện đúng.
3. Admin đăng nhập → thêm/sửa 1 thủ tục → kiểm tra `/procedures` phản ánh thay đổi ngay.
4. Tắt backend giả lập sự cố → frontend hiển thị lỗi lịch sự, không trắng trang.
5. Test trên mobile thật (không chỉ resize trình duyệt).
6. Test `legacy/index.html` vẫn chạy độc lập làm phương án dự phòng.

## Sau khi sửa dữ liệu seed

Nếu sửa `data/seed-knowledge-base.json`, chạy lại `scripts/seed_from_json.py` (nên viết idempotent — upsert theo `code`/`id`, không tạo trùng lặp mỗi lần chạy).
