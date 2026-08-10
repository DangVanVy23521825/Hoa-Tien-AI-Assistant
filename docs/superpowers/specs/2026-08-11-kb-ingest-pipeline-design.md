# Thiết kế: pipeline mở rộng knowledge base bằng crawl web công khai

Ngày: 2026-08-11 · Trạng thái: đã duyệt

## Vấn đề

KB hiện có 49 bản ghi (19 thủ tục · 20 FAQ · 10 bài kiến thức). Người dân hỏi ra ngoài
phạm vi đó là trợ lý fallback "liên hệ Bộ phận Một cửa" — đúng theo guardrail, nhưng
làm trợ lý trông nghèo nàn khi trình bày trước ban giám khảo.

Mong muốn: trợ lý biết **mọi thứ trong phạm vi xã Hòa Tiến** — hành chính, địa danh,
văn hoá, ẩm thực, luật lệ — nhưng vẫn **không được ra khỏi phạm vi xã** và vẫn không bịa.

## Tiền đề đã loại bỏ

| Ý tưởng ban đầu | Vì sao loại |
|---|---|
| Nối model mạnh hơn (Sonnet / GPT / Haiku) | Xã Hòa Tiến thành lập 01/7/2025 — **không model nào có dữ liệu về xã này trong training**. Đổi model chỉ đổi văn phong trên context ta đưa vào, không thêm một sự thật nào. Model mạnh hơn còn tự tin lấp chỗ trống hơn → bịa lệ phí, thời hạn, căn cứ pháp lý. Với trợ lý hành chính đó là sai lệch pháp lý, không phải lỗi UX. |
| Web search live (Gemini Google Search grounding) | Không whitelist domain một cách chắc chắn được. **"Hòa Tiến" trùng tên với xã ở tỉnh khác** → rất dễ trả về đình làng / làng nghề / lệ phí của một Hòa Tiến khác; giám khảo hỏi một câu là lộ. Cộng thêm +2–4s latency và bản dự phòng offline không có tính năng này. Có thể xét lại sau, chỉ cho nhóm câu "mềm" và phải có nhãn cảnh báo. |

Nút thắt thật là **độ phủ dữ liệu**, không phải model. Nên giải pháp là một pipeline
nạp dữ liệu, không phải một thay đổi kiến trúc AI.

## Quyết định đã chốt

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Phạm vi kiến thức | Domain đóng: chỉ những gì *của xã Hòa Tiến* | Giữ nguyên guardrail chống hallucination (nguyên tắc kiến trúc #2) |
| Nguồn dữ liệu | Crawl web công khai, whitelist URL thủ công | Không có đầu mối trong UBND xã; làm được ngay |
| Vị trí pipeline | **Script offline** trong `backend/scripts/ingest/`, output là `seed-knowledge-base.json` | Backend đang live với guardrail đã hiệu chỉnh — không đụng một dòng runtime nào, rủi ro bằng 0 |
| Dependency | **Không thêm gì**: chỉ stdlib + `httpx` (đã có) | `requirements.txt` cũng được cài trên Railway; plan đó đã OOM nhiều lần, không bơm thêm bs4/pyyaml/trafilatura cho một script chạy tay vài lần |
| File cấu hình nguồn | `sources.json` (không phải YAML) | Tránh dependency `pyyaml`; repo vốn đã JSON-based |
| Migration DB | **Không cần** | `knowledge_articles.category` là `String(50)` tự do — thêm `village`/`cuisine`/`festival`/`legal` là nạp được ngay |

## 1. Kiến trúc pipeline

Bốn bước rời nhau, mỗi bước ghi file ra đĩa để chạy lại được từng bước độc lập:

```
sources.json
   │  1_crawl.py      httpx + stdlib HTMLParser, cache theo hash URL
   ▼
data/ingest/raw/<hash>.json      { url, title, text, fetched_at }
   │  2_extract.py    Gemini structured output, 1 trang → 0..n record
   ▼
data/ingest/candidates.json      [ { status: "pending", kind, record, evidence_quote, source_url } ]
   │  3_review.py     CLI y / n / e  → status: accepted | rejected
   ▼
candidates.json (đã duyệt)
   │  4_merge.py      sinh id, dedupe, gộp + sync 2 bản seed
   ▼
data/seed-knowledge-base.json  ──▶  scripts/seed_from_json.py  ──▶  Postgres + embedding
```

| Bước | File | Trách nhiệm |
|---|---|---|
| 1 | `1_crawl.py` | Fetch URL trong whitelist, lột HTML → text sạch, lưu raw kèm `fetched_at`. Có cache: chạy lại không fetch lại (`--force` để bỏ qua cache) |
| 2 | `2_extract.py` | Mỗi trang raw → gọi Gemini ép JSON schema đúng `procedures`/`faq`/`knowledge_articles`, sinh `candidates.json` |
| 3 | `3_review.py` | Duyệt tay: in record + trích dẫn gốc + URL, bấm `y`/`n`/`e`(sửa)/`q` |
| 4 | `4_merge.py` | Gộp record `accepted` vào seed JSON: sinh `id` theo quy tắc hiện có, dedupe theo title/question, **sync `data/` ↔ `backend/data/`**, nhắc chạy `eval_retrieval.py` |

## 2. Ba ràng buộc trong prompt trích xuất (bước 2)

Đây là chỗ quyết định chất lượng — biến "LLM viết nội dung" thành "LLM cắt và xếp lại":

1. **Mọi record bắt buộc có `evidence_quote`** — trích nguyên văn đoạn trên trang nguồn
   làm căn cứ. Không trích được ⇒ không sinh record. Bước 3 nhờ đó duyệt được bằng cách
   đọc quote cạnh record, không phải mở lại trang web.
2. **Bắt buộc `source`** = tên trang + URL, đúng định dạng `source_citation` đang dùng
   (`"Cổng thông tin điện tử TP Đà Nẵng — https://..."`).
3. **Cổng địa danh**: trang không nói rõ về xã Hòa Tiến / Hòa Vang / TP Đà Nẵng ⇒ trả
   rỗng. Chặn ngay từ bước trích, không đợi lúc duyệt — vì "Hòa Tiến" là tên trùng.

Thêm: bắt Gemini sinh **5–8 `keywords` khẩu ngữ** cho mỗi record. `rules/ai-module.md`
bắt buộc điền keywords vì keyword score vẫn là một nửa của hybrid score.

## 3. Rủi ro chính: retrieval bị loãng

Ba hằng số `SEMANTIC_FLOOR = 0.60`, `SEMANTIC_GATE_MIN_COS = 0.65`, `MIN_MATCH_SCORE = 4.0`
được đo và hiệu chỉnh **trên KB 49 bản ghi**. Đẩy lên 150–200 bản ghi làm đổi phân bố:

- Câu rác có nhiều "hàng xóm gần nghĩa" hơn → false-positive tăng, đúng lỗi đã sửa 2 đợt.
- Câu **hành chính** có thể bị bài **văn hoá** cướp mất — "đình làng ở thôn nào" và
  "đăng ký thường trú ở thôn nào" dùng chung nhiều token.
- Chiều ngược lại: vài câu trong battery "ngoài phạm vi" sau khi KB dày lên sẽ **đúng là
  trong phạm vi** → phải phân loại lại câu đó, **không phải nới ngưỡng cho vừa**.

**`eval_retrieval.py` là cổng bắt buộc trước khi seed production.** Battery mở rộng:
thêm ~15 câu hợp lệ cho nội dung mới, giữ nguyên nhóm rác, thêm vài câu hành chính
"dễ bị văn hoá cướp". `4_merge.py` in cảnh báo nhắc chạy eval sau khi gộp.

## 4. Hai chỗ đồng bộ dễ quên

- `data/seed-knowledge-base.json` và `backend/data/seed-knowledge-base.json` phải giống
  hệt (Railway deploy từ `backend/`). `4_merge.py` ghi cả hai.
- `frontend/legacy/index.html` nhúng KB tĩnh làm **phương án B khi mất mạng lúc thuyết
  trình**. Không cập nhật thì bản dự phòng trả lời thiếu hẳn so với bản live.

## 5. Phạm vi đợt này (deadline < 1 tuần)

Mục tiêu **~150–200 bản ghi** (từ 49). Không đuổi theo con số lớn hơn.

| Loại | Hiện có | Mục tiêu | Bổ sung gì |
|---|---|---|---|
| `procedures` | 19 | ~50 | BHXH/y tế, giáo dục, hộ kinh doanh, xây dựng, môi trường, người có công |
| `faq` | 20 | ~50 | Sinh từ chính thủ tục mới + câu dân hay hỏi |
| `knowledge_articles` | 10 | ~60 | 22 thôn, ẩm thực, lễ hội, nhân vật lịch sử, di tích còn thiếu |

Category mới cho `knowledge_articles`: `village`, `cuisine`, `festival`, `legal`
(thêm vào `history` / `landmark` / `craft_village` đang có). Không cần migration.

## 6. Chủ động KHÔNG làm (YAGNI)

- Không đổi model generation.
- Không web search live.
- Không UI quản trị cho ingest — duyệt bằng CLI là đủ.
- Không cron crawl định kỳ. Đây là công cụ chạy tay, dùng vài lần rồi để đó.

## 7. Lịch trình

| Ngày | Việc |
|---|---|
| 1 | `sources.json` + `1_crawl.py` + `2_extract.py` chạy thông trên 5–10 trang mẫu, soi kỹ chất lượng record |
| 2 | Crawl + extract toàn bộ → `candidates.json` |
| 3 | Duyệt (`3_review.py`) |
| 4 | Merge + mở rộng eval battery + hiệu chỉnh ngưỡng nếu eval đỏ |
| 5 | Seed production + test tay + sync bản dự phòng offline |
