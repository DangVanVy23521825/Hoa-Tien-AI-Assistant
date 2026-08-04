# rules/deploy.md — Deploy

## Tổng quan

| Thành phần | Nền tảng | Ghi chú |
|---|---|---|
| Frontend | Vercel | Static site, build đơn giản (hoặc không cần build nếu vanilla JS) |
| Backend | Railway | FastAPI — cần plan đủ RAM để chạy bge-m3 (xem mục "Deploy pgvector + bge-m3 trên Railway") |
| Database | Railway Postgres **có pgvector** | Không dùng plugin Postgres mặc định — xem bên dưới |

## Biến môi trường backend

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=<random-string-dài>
CORS_ORIGINS=https://<domain-frontend>.vercel.app,http://localhost:5500
ENV=production
GEMINI_API_KEY=<khóa API Gemini>
GEMINI_GENERATION_MODEL=gemini-2.5-flash
EMBEDDING_MODEL_NAME=BAAI/bge-m3
RAG_SEMANTIC_WEIGHT=4.0
```

## Deploy pgvector + bge-m3 trên Railway

**1. Database — Railway Postgres plugin mặc định KHÔNG có pgvector.** Đã kiểm tra: Railway có sẵn template Postgres đi kèm pgvector (một trong các template "PostgreSQL Extensions", "pgvector", "Postgres with pgVector Engine" trên Railway — tìm trong Railway Template marketplace). Việc cần làm:
- Nếu project **chưa có dữ liệu thật** (khả năng cao ở giai đoạn hiện tại): xoá Postgres plugin mặc định, deploy lại bằng 1 trong các template pgvector nói trên, lấy `DATABASE_URL` mới.
- Nếu đã có dữ liệu cần giữ: có thể thử `CREATE EXTENSION vector` trực tiếp trên Postgres hiện tại trước (một số image Railway hiện đại đã bundle sẵn pgvector) — nếu lỗi "extension not available", bắt buộc phải chuyển sang service Postgres dùng template pgvector, rồi `pg_dump`/`pg_restore` dữ liệu cũ sang.
- Sau khi có Postgres hỗ trợ pgvector: chạy `alembic upgrade head` như bình thường — migration `82f5e29f7a0c` sẽ tự `CREATE EXTENSION IF NOT EXISTS vector`.

**2. Backend — bge-m3 chạy CPU ngay trong container FastAPI**, không cần service riêng. Cần lưu ý khi deploy trên Railway:
- `torch` + `sentence-transformers` + trọng số bge-m3 (~2.2GB tải lần đầu từ HuggingFace Hub) cần khoảng **2-3GB RAM** khi model đã load vào bộ nhớ — chọn Railway plan đủ RAM (Hobby/free tier mặc định thường không đủ, cần nâng plan hoặc tăng resource limit cho service).
- `requirements.txt` đã trỏ `--extra-index-url https://download.pytorch.org/whl/cpu` để cài bản torch CPU-only (nhẹ hơn nhiều so với bản có CUDA) — giữ nguyên dòng này khi build trên Railway.
- Request đầu tiên gọi `embed_text()` sau mỗi lần deploy/restart sẽ chậm hơn hẳn (tải + load model) — cân nhắc gọi thử 1 lần (warm-up) ngay sau khi service start nếu độ trễ lần đầu ảnh hưởng demo.
- Railway filesystem là ephemeral — model sẽ tải lại từ HuggingFace Hub mỗi lần container restart/redeploy (không cache lâu dài) trừ khi gắn Railway Volume và trỏ `HF_HOME` vào đó.

## Quy trình deploy (gợi ý)

1. **Database**: tạo Postgres instance trên Railway từ template có pgvector (xem mục trên) → lấy `DATABASE_URL`.
2. **Backend**: push `backend/` lên Railway, set biến môi trường (kể cả `GEMINI_API_KEY`), chọn plan đủ RAM cho bge-m3, chạy `alembic upgrade head` khi deploy, seed dữ liệu ban đầu từ `data/seed-knowledge-base.json` (script tự embed bằng bge-m3, không cần chờ Gemini key). Nếu vì lý do nào đó seed chạy mà chưa embed đủ, chạy thêm `python3 scripts/backfill_embeddings.py`.
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
- [ ] Railway Postgres đã xác nhận `CREATE EXTENSION vector` chạy được (dùng template pgvector, không phải plugin Postgres mặc định).
- [ ] Railway backend đủ RAM cho bge-m3 (torch load model) — test câu hỏi đầu tiên sau khi deploy không bị timeout/OOM.
