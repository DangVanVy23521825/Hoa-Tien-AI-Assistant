# rules/deploy.md — Deploy

## Tổng quan

| Thành phần | Nền tảng | Ghi chú |
|---|---|---|
| Frontend | Vercel | Static site, build đơn giản (hoặc không cần build nếu vanilla JS) |
| Backend | Railway | FastAPI — nhẹ, embedding (mặc định) gọi API Gemini, không tự host, xem bên dưới |
| Database | Railway Postgres **có pgvector** | Không dùng plugin Postgres mặc định — xem bên dưới |

## Biến môi trường backend

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=<random-string-dài>
CORS_ORIGINS=https://<domain-frontend>.vercel.app,http://localhost:5500
ENV=production
GEMINI_API_KEY=<khóa API Gemini>
GEMINI_GENERATION_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIM=768
# Chỉ cần nếu EMBEDDING_PROVIDER=deepinfra (chất lượng tốt hơn nếu cần, đổi tay khi
# muốn — lưu ý đổi provider cần migration đổi dimension cột embedding, xem rules/ai-module.md):
DEEPINFRA_API_KEY=<khóa API DeepInfra>
DEEPINFRA_EMBEDDING_MODEL_NAME=BAAI/bge-m3
EMBEDDING_API_BASE_URL=https://api.deepinfra.com/v1/openai/embeddings
RAG_SEMANTIC_WEIGHT=4.0
```

## Deploy pgvector + embedding trên Railway

**1. Database — Railway Postgres plugin mặc định KHÔNG có pgvector.** Đã kiểm tra: Railway có sẵn template Postgres đi kèm pgvector (một trong các template "PostgreSQL Extensions", "pgvector", "Postgres with pgVector Engine" trên Railway — tìm trong Railway Template marketplace). Việc cần làm:
- Nếu project **chưa có dữ liệu thật**: xoá Postgres plugin mặc định, deploy lại bằng 1 trong các template pgvector nói trên, lấy `DATABASE_URL` mới.
- Nếu đã có dữ liệu cần giữ: có thể thử `CREATE EXTENSION vector` trực tiếp trên Postgres hiện tại trước (một số image Railway hiện đại đã bundle sẵn pgvector — đã xác nhận hoạt động trên project này, pgvector 0.8.5) — nếu lỗi "extension not available", chuyển sang service Postgres dùng template pgvector, rồi `pg_dump`/`pg_restore` dữ liệu cũ sang.
- Sau khi có Postgres hỗ trợ pgvector: chạy `alembic upgrade head` — migration `82f5e29f7a0c` sẽ tự `CREATE EXTENSION IF NOT EXISTS vector` (no-op nếu đã bật).

**2. Backend — 2 provider embedding chọn qua `EMBEDDING_PROVIDER`, cả 2 đều hosted (không tự host):**
- **`gemini` (mặc định)**: API embedding của Google (768 chiều), tận dụng chung `GEMINI_API_KEY` — không cần vendor mới, không tốn RAM.
  - Lịch sử: đã thử tự host 5 cấu hình khác nhau (bge-m3 full ~2.5-3GB, bge-m3 quantize int8 ~1.4GB, multilingual-MiniLM fp32 ~700MB, MiniLM quantize int8 ~850MB, vietnamese-sbert ~910MB) — **tất cả đều OOM-kill thật trên Railway Trial plan hoặc không cải thiện được** (mỗi lần `/chat` gọi tới embedding, container bị kill cứng và tự restart, log không có traceback). Kết luận: baseline Python + bất kỳ model transformer nào (dù nhỏ) đều vượt RAM thật của Trial plan — chuyển hẳn sang API hosted để né triệt để.
  - Chất lượng thấp hơn bge-m3 (đã test: margin phân tách cosine similarity ~0.10 so với ~0.39) nhưng vẫn có giá trị vì retrieval là **hybrid** — semantic chỉ là 1 trong 2 tín hiệu, keyword score vẫn đóng góp độc lập.
- **`deepinfra`** (nếu cần chất lượng tốt hơn): gọi API DeepInfra, model `BAAI/bge-m3` (1024 chiều), cần đăng ký tài khoản (deepinfra.com), tạo API key, set `DEEPINFRA_API_KEY`. Tính phí theo token (~$0.01/triệu, rất thấp) — thêm 1 vendor phải quản lý.
- **Chuyển đổi khi cần**: 2 provider ra vector khác dimension (768 vs 1024) nên phải chạy migration đổi cột `Vector()` trước, không chỉ đổi biến env, rồi `backfill_embeddings.py --force`.

## Quy trình deploy (gợi ý)

1. **Database**: tạo Postgres instance trên Railway từ template có pgvector (xem mục trên) → lấy `DATABASE_URL`.
2. **Backend**: push `backend/` lên Railway, set biến môi trường (kể cả `GEMINI_API_KEY`), chạy `alembic upgrade head` khi deploy, seed dữ liệu ban đầu từ `data/seed-knowledge-base.json` (script tự embed theo `EMBEDDING_PROVIDER` đang cấu hình). Test `/chat` ngay sau deploy.
3. **Frontend**: set base URL API (biến `API_BASE_URL` trong `frontend/js/api.js` hoặc file config) trỏ tới domain backend vừa deploy → push lên Vercel.
4. Kiểm tra CORS: domain frontend thật phải nằm trong `CORS_ORIGINS` của backend.
5. Test end-to-end trên domain thật trước khi hội trại: đăng ký, đăng nhập, chat (kể cả câu hỏi diễn đạt lệch để test semantic), xem lịch sử, admin CRUD.

## Kế hoạch dự phòng khi thuyết trình

Deploy thật phụ thuộc mạng của địa điểm tổ chức. Luôn mang theo:
- `legacy/index.html` (bản offline single-file) chạy trên máy trình bày, phòng khi mạng hội trại kém hoặc backend gặp sự cố.
- Ảnh chụp màn hình / video ngắn quay sẵn luồng chính (chat → thủ tục → QR) làm phương án C.

## Trước ngày thi — checklist

- [ ] Domain frontend + backend hoạt động ổn định, test từ mạng di động (không chỉ wifi nhà/trường).
- [ ] Seed dữ liệu đầy đủ, đối soát lại số liệu phí/thời gian.
- [ ] Tài khoản admin đã tạo, test CRUD.
- [ ] Test đăng ký/đăng nhập user thường + xem lịch sử chat.
- [ ] Rate limit không chặn nhầm khi nhiều người bấm thử cùng lúc tại gian trưng bày.
- [ ] `legacy/index.html` vẫn chạy được như phương án dự phòng.
- [x] Railway Postgres đã xác nhận `CREATE EXTENSION vector` chạy được (pgvector 0.8.5).
- [ ] Test `/chat` với câu hỏi có match trên production không bị lỗi 502/500.
