# Pipeline mở rộng knowledge base

Công cụ **chạy tay**, không phải phần của backend đang chạy. Nó chỉ sinh ra
`data/seed-knowledge-base.json` dày hơn; việc nạp vào DB vẫn là `scripts/seed_from_json.py`
như cũ. Thiết kế đầy đủ: `docs/superpowers/specs/2026-08-11-kb-ingest-pipeline-design.md`.

Chỉ dùng stdlib + `httpx` (đã có trong requirements) — **đừng thêm dependency** cho mấy
script này, `requirements.txt` cũng được cài trên Railway và plan đó đã OOM nhiều lần.

## Chạy

```bash
cd backend
source venv/bin/activate

python3 scripts/ingest/1_crawl.py       # → data/ingest/raw/*.json      (có cache)
python3 scripts/ingest/2_extract.py     # → data/ingest/candidates.json (gọi Gemini)
python3 scripts/ingest/3_review.py      # duyệt tay: y / n / s / e / q
python3 scripts/ingest/4_merge.py       # → seed-knowledge-base.json (ghi cả 2 bản)

python3 scripts/eval_retrieval.py       # BẮT BUỘC — xem mục dưới
python3 scripts/seed_from_json.py       # nạp DB + sinh embedding
```

## Hạn mức Gemini free tier — đọc trước khi chạy bước 2

`gemini-2.5-flash` free tier: **20 request/ngày** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
đo thật 11/08/2026). Vì vậy bước 2 **gộp nhiều trang vào một lần gọi**:

| `--batch` | Số lần gọi cho 87 trang | Ghi chú |
|---|---|---|
| 1 | 82 | chất lượng cao nhất, cần billing |
| 4 | 22 | vẫn vượt hạn mức ngày |
| **6 (mặc định)** | **17** | lọt hạn mức, còn dư 3 lần cho retry |
| 8 | 15 | không giảm thêm — đã chạm `MAX_CHARS_PER_CALL` |

Hết quota giữa chừng: script dừng sạch, giữ nguyên ứng viên đã trích, hôm sau chạy lại
đúng lệnh đó là đi tiếp (không có `--force` thì nó bỏ qua trang đã xong).

**Dùng key riêng cho ingest.** Trợ lý production cũng gọi `gemini-2.5-flash` bằng
`GEMINI_API_KEY`; nếu dùng chung một key thì chạy ingest sẽ đốt hết lượt của người dân
đang hỏi, và trợ lý tụt xuống câu trả lời template cho tới hết ngày.

## Vì sao có `extra_ca/`

`hoatien.danang.gov.vn` chỉ gửi cert lá, không gửi intermediate `GlobalSign RSA OV SSL
CA 2018`, nên Python không dựng được chain (curl qua vì dùng CA hệ thống). `common.ca_bundle()`
nối intermediate đó vào bundle certifi rồi verify bình thường.
**Không được "sửa" bằng cách tắt xác thực chứng chỉ.**

Cert hết hạn 21/11/2028. Khi nào lỗi `CERTIFICATE_VERIFY_FAILED` quay lại thì tải bản mới
từ URL trong extension AIA của cert:

```bash
openssl s_client -connect hoatien.danang.gov.vn:443 -servername hoatien.danang.gov.vn \
  </dev/null 2>/dev/null | openssl x509 -noout -text | grep -A2 "Authority Information Access"
```

## Sau khi merge — không được bỏ qua

1. **`python3 scripts/eval_retrieval.py`.** `SEMANTIC_FLOOR` / `SEMANTIC_GATE_MIN_COS` /
   `MIN_MATCH_SCORE` được hiệu chỉnh trên KB 49 bản ghi; KB dày lên là đổi phân bố điểm.
   Eval đỏ thì **sửa keywords/nội dung bản ghi**, không nới ngưỡng — xem `rules/ai-module.md`.
2. Câu trong battery "ngoài phạm vi" mà nay KB đã có dữ liệu thật thì phải **chuyển sang
   nhóm hợp lệ**, không phải hạ ngưỡng cho vừa.
3. Cập nhật KB nhúng trong `frontend/legacy/index.html` — bản dự phòng khi mất mạng lúc
   thuyết trình, không sync là nó trả lời thiếu hẳn so với bản live.

## Ghi chú về nguồn

- `sources.json` là whitelist. Mỗi URL đã mở tay kiểm. **"Hòa Tiến" trùng tên với xã ở
  tỉnh khác** — thêm nguồn mới mà không kiểm là rước dữ liệu của xã khác vào KB. Prompt
  bước 2 có cổng địa danh chặn thêm một lớp.
- `dichvucong.gov.vn` đã thử và loại: SPA, HTML trả về 0 ký tự text.
- Cổng xã chạy ASP.NET WebForms — bọc cả trang trong một `<form>`, nên `common._TextExtractor`
  **không được** loại thẻ `form`.
