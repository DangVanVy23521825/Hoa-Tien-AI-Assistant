# rules/deploy.md — Deploy

## Tổng quan

| Thành phần | Nền tảng | Ghi chú |
|---|---|---|
| Frontend | Vercel | Static site, build đơn giản (hoặc không cần build nếu vanilla JS) |
| Backend | Railway | FastAPI — self-host embedding (mặc định) cần ~700MB RAM khi model đã load, xem bên dưới |
| Database | Railway Postgres **có pgvector** | Không dùng plugin Postgres mặc định — xem bên dưới |

## Biến môi trường backend

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=<random-string-dài>
CORS_ORIGINS=https://<domain-frontend>.vercel.app,http://localhost:5500
ENV=production
GEMINI_API_KEY=<khóa API Gemini>
GEMINI_GENERATION_MODEL=gemini-2.5-flash
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# Chỉ cần nếu EMBEDDING_PROVIDER=deepinfra (phương án dự phòng nếu local vẫn OOM —
# lưu ý đổi provider cần migration đổi dimension cột embedding, xem rules/ai-module.md):
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

**2. Backend — 2 provider embedding chọn qua `EMBEDDING_PROVIDER`:**
- **`local` (mặc định)**: self-host `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều, ~470MB tải về, ~700MB RAM khi model đã load) qua `sentence-transformers` — không cần API key, không tốn chi phí biến đổi.
  - Lịch sử: đã thử 2 lần self-host bge-m3 (full ~2.2GB và bản quantize int8 ~1.4GB) — **cả 2 đều OOM-kill thật trên Railway Trial plan** (mỗi lần `/chat` gọi tới embedding, container bị kill cứng và tự restart, log không có traceback). Model nhẹ hơn (multilingual-e5) né được RAM nhưng chất lượng phân biệt kém; model tiếng Anh-only (bge-micro-v2) cho kết quả sai với tiếng Việt. `paraphrase-multilingual-MiniLM-L12-v2` là điểm cân bằng tốt nhất tìm được — **cần test deploy thật để xác nhận không OOM**, nếu vẫn OOM thì đây thực sự là giới hạn cứng của Trial plan cho bất kỳ self-host nào.
  - Model tải về từ HuggingFace Hub lần đầu `embed_text()` được gọi (không phải lúc build) — request đầu tiên chậm hơn hẳn.
- **`deepinfra`** (phương án dự phòng nếu `local` vẫn OOM): gọi API DeepInfra, model `BAAI/bge-m3` (1024 chiều), cần đăng ký tài khoản (deepinfra.com), tạo API key, set `DEEPINFRA_API_KEY`. Backend nhẹ nhất (gần như không tốn RAM), nhưng tính phí theo token (~$0.01/triệu, rất thấp).
- **Chuyển đổi khi cần**: 2 provider ra vector khác dimension (384 vs 1024) nên phải chạy migration đổi cột `Vector()` trước, không chỉ đổi biến env. Đã có sẵn migration mẫu (`d5f2dd0ed353`) chuyển 1024→384 — nếu cần đổi ngược lại (384→1024, sang `deepinfra`), viết migration tương tự đảo chiều rồi chạy `backfill_embeddings.py --force`.

## Quy trình deploy (gợi ý)

1. **Database**: tạo Postgres instance trên Railway từ template có pgvector (xem mục trên) → lấy `DATABASE_URL`.
2. **Backend**: push `backend/` lên Railway, set biến môi trường (kể cả `GEMINI_API_KEY`), chạy `alembic upgrade head` khi deploy, seed dữ liệu ban đầu từ `data/seed-knowledge-base.json` (script tự embed theo `EMBEDDING_PROVIDER` đang cấu hình). Test `/chat` ngay sau deploy để xác nhận `local` không bị OOM — nếu bị, cần migration đổi cột `Vector()` sang 1024 chiều, đổi `EMBEDDING_PROVIDER=deepinfra` + set `DEEPINFRA_API_KEY` + redeploy + chạy lại `python3 scripts/backfill_embeddings.py --force`.
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
- [ ] Test `/chat` với câu hỏi có match trên production không bị lỗi 502/500 (xác nhận `EMBEDDING_PROVIDER=local` không OOM trên Railway plan hiện tại — nếu OOM, có phương án dự phòng `deepinfra` sẵn, xem mục trên).
