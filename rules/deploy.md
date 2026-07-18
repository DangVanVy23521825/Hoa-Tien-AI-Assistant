# rules/deploy.md — Deploy

## Tổng quan

| Thành phần | Nền tảng | Ghi chú |
|---|---|---|
| Frontend | Vercel hoặc Netlify | Static site, build đơn giản (hoặc không cần build nếu vanilla JS) |
| Backend | Railway hoặc Render | FastAPI, cần biến môi trường |
| Database | Railway/Render Managed PostgreSQL | Cùng nền tảng với backend để giảm độ trễ mạng |

## Biến môi trường backend

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
JWT_SECRET=<random-string-dài>
CORS_ORIGINS=https://<domain-frontend>.vercel.app,http://localhost:5500
ENV=production
```

## Quy trình deploy (gợi ý)

1. **Database**: tạo Postgres instance trên Railway/Render → lấy `DATABASE_URL`.
2. **Backend**: push `backend/` lên Railway/Render, set biến môi trường, chạy `alembic upgrade head` khi deploy, seed dữ liệu ban đầu từ `data/seed-knowledge-base.json`.
3. **Frontend**: set base URL API (biến `API_BASE_URL` trong `frontend/js/api.js` hoặc file config) trỏ tới domain backend vừa deploy → push lên Vercel/Netlify.
4. Kiểm tra CORS: domain frontend thật phải nằm trong `CORS_ORIGINS` của backend.
5. Test end-to-end trên domain thật trước khi hội trại: đăng ký, đăng nhập, chat, xem lịch sử, admin CRUD.

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
