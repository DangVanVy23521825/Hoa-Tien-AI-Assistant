# rules/ai-module.md — Đặc tả module AI

## Luồng xử lý (contract) — RAG thật: embedding + generation đều qua Gemini API

Hai model khác nhau, hai vai trò khác nhau:
- **Embedding (retrieval)**: qua 1 trong 2 provider chọn bằng `EMBEDDING_PROVIDER`:
  - `gemini` (**mặc định**): API embedding của Google (`gemini-embedding-001`, 768 chiều) — tận dụng chung `GEMINI_API_KEY` đã dùng cho generation, không cần vendor mới, không tự host nên không có rủi ro OOM.
  - `deepinfra`: gọi API DeepInfra (tương thích OpenAI), model `BAAI/bge-m3` (1024 chiều), cần `DEEPINFRA_API_KEY` riêng — chất lượng tốt hơn hẳn (đã test: margin phân tách ~0.39 so với ~0.10 của Gemini) nhưng thêm 1 vendor.
  - **2 provider ra vector khác dimension (768 vs 1024)** — đổi provider phải chạy migration đổi cột `Vector()` + `backfill_embeddings.py --force`, không chỉ đổi 1 biến env. Chi tiết lịch sử quyết định (đã thử tự host 5 cấu hình model khác nhau, từ bge-m3 full ~2.5-3GB đến vietnamese-sbert ~910MB — tất cả đều OOM trên Railway Trial plan hoặc không cải thiện; các model càng nhỏ thì chất lượng càng kém với tiếng Việt) xem docstring `backend/app/services/embeddings.py`.
- **Generation**: Gemini (`gemini_generation_model`) — qua API, cần `GEMINI_API_KEY`.

```
POST /chat { question: string, [token?] }
   → retrieve(db, question, topK)  [backend/app/services/retrieval.py]  → hits
       keyword score (giữ nguyên thuật toán cũ) + semantic score (embedding, pgvector)
   → generate(question, hits)      [backend/app/services/generation.py]
       không hit → fallback tĩnh, KHÔNG gọi Gemini
       có hit    → call_gemini(context, question) [backend/app/services/llm.py]
                   lỗi/timeout Gemini → fallback về _generate_template() (logic cũ)
                   refusal phrase → coi như unmatched (guardrail lớp 2)
   → (nếu có user) lưu vào chat_history
   → response: { answer_html, source, matched: bool, matched_source_type, online_url?, message_id, matched_source_id? }
       online_url chỉ có khi matched thủ tục — frontend dùng sinh QR nộp hồ sơ trực tuyến
       message_id: id bản ghi chat_history — frontend gửi feedback 👍👎 qua POST /chat/feedback
       matched_source_id (code thủ tục) — frontend dùng in checklist hồ sơ
```

| Hàm | Trách nhiệm |
|-----|-------------|
| `normalize(s)` | Chuẩn hoá tiếng Việt: bỏ dấu, đ→d, hạ thường |
| `retrieve(db, query, topK)` | Hybrid: keyword scoring (như cũ) + semantic similarity (cosine, embedding lưu sẵn qua pgvector) |
| `embed_text(text, task_type)` | `backend/app/services/embeddings.py` — định tuyến theo `EMBEDDING_PROVIDER` tới `_embed_gemini()` hoặc `_embed_deepinfra()`. `task_type` dùng thật với Gemini (`RETRIEVAL_QUERY`/`RETRIEVAL_DOCUMENT`), giữ cho tương thích khi gọi `_embed_deepinfra()` (bge-m3 không cần) |
| `call_gemini(prompt)` | `backend/app/services/llm.py` — gọi Gemini generation, ép grounding qua system prompt, raise `LlmError` nếu lỗi/timeout để caller fallback |
| `generate(query, hits)` | Gọi Gemini khi có hit, fallback `_generate_template()` khi Gemini lỗi hoặc trả refusal phrase |

> Retrieval hybrid giữ nguyên thuật toán keyword-scoring đã kiểm chứng (`_score_doc`) làm tín hiệu chính, cộng thêm điểm semantic — nếu record chưa có embedding (`embedding is None`, ví dụ chưa chạy `backfill_embeddings.py`) thì hành vi giống hệt bản keyword-only cũ, không lỗi.

## Câu xã giao (chào hỏi / cảm ơn / hỏi trợ lý là ai / ừ, ok)

`backend/app/services/smalltalk.py` trả lời nhóm này bằng kịch bản cố định (giới thiệu +
gợi ý câu hỏi), không gọi Gemini, không bịa thông tin hành chính nào.

Vì sao cần lớp riêng: retrieval chấm điểm theo mức trùng khớp với KB, mà "xin chào" thì
không có tài liệu nào là câu trả lời đúng — điểm keyword cao nhất chỉ ~2.0 so với
`MIN_MATCH_SCORE` 4.0. Không có lớp này thì người dân chào một câu cũng nhận nguyên văn
câu từ chối "tôi chưa có thông tin… liên hệ Bộ phận Một cửa".

**Không được hạ `MIN_MATCH_SCORE` để "chữa" việc này** — vừa làm câu rác lọt lại, vừa
không giải quyết được gốc vấn đề.

### Hai tầng nhận diện

| | Chạy khi nào | Chi phí | Bắt được gì |
|---|---|---|---|
| 1. Khớp cụm từ (`detect`) | **Trước** retrieval | 0 (không gọi API) | Cụm liệt kê sẵn: "xin chào", "cảm ơn", "ok", "bạn là ai"… |
| 2. Đối chiếu ngữ nghĩa (`detect_semantic`) | **Sau** retrieval, chỉ khi không có hit nào | 0 (dùng lại `embed_query` đã cache) | Biến thể ngoài danh sách: "chàooo", "ơi", "có ai ở đó không"… |

Tầng 2 đặt **sau** retrieval là có chủ đích: câu tra cứu được thì không bao giờ bị lớp xã
giao cướp mất. Câu mẫu (`_EXEMPLARS`) được embed **một lần cho cả tiến trình, gộp trong
một lần gọi API** qua `embed_texts()`; provider lỗi thì tầng 2 tự tắt, tầng 1 vẫn chạy.

- `SEMANTIC_MIN_COS = 0.68` — đo 08/2026 trên gemini-embedding: 27 biến thể xã giao đạt
  cosine 0.626–1.000 với câu mẫu, 13 câu rác thật ngoài phạm vi chỉ đạt tối đa 0.640
  ("giá vàng hôm nay"). 0.68 nằm trên toàn bộ nhóm rác với biên 0.04. Hai biến thể rơi
  dưới ngưỡng ("good morning" 0.626, "ê" 0.646) đưa thẳng vào danh sách cụm từ tầng 1.
- Tầng 1 chỉ nhận khi phần còn lại của câu **không có nội dung thực chất**: "chào bạn,
  tôi muốn làm khai sinh" vẫn đi vào retrieval. Khớp có neo biên từ nên "hi" không dính
  trong "hiến", "chào" không dính trong "chào mừng năm mới có nghỉ làm việc không".
- Câu chỉ có emoji/dấu câu ("?", "😀") trả về lời mời đặt câu hỏi, không phải câu từ chối.
- `matched=False`, `matched_source_type="smalltalk"`, `source=""` (frontend không hiện
  dòng dẫn nguồn — câu xã giao không có nguồn để dẫn).
- Thống kê tách riêng: `smalltalk` không tính vào `matched` lẫn `unmatched` của
  `/admin/stats`, và không tính vào `total_answered` của `/chat/stats/public` — nếu không
  danh sách "câu hỏi chưa có dữ liệu trả lời" (dùng để tìm chỗ thiếu trong KB) sẽ đầy câu chào.
- **Đo lại bằng `backend/scripts/eval_smalltalk.py`** (không cần DB, exit ≠ 0 khi sai).
  Kết quả 08/2026: **81/81** — 50 câu xã giao nhận đúng, 12 câu tra cứu thật tầng 1 bỏ qua,
  13 câu ngoài phạm vi cả 2 tầng bỏ qua. Chạy lại khi sửa danh sách cụm từ, câu mẫu,
  ngưỡng, hoặc đổi provider embedding.

## Guardrail chống hallucination (2 lớp)

1. **Ngưỡng similarity/keyword** (`MIN_MATCH_SCORE` trong `retrieval.py`) — quyết định trước khi gọi Gemini, miễn phí, chặn câu hỏi hoàn toàn ngoài phạm vi KB.
2. **System prompt ép grounding** (`SYSTEM_PROMPT` trong `llm.py`) — Gemini phải trả đúng nguyên văn `REFUSAL_PHRASE` nếu context không đủ trả lời cụ thể; `generation.py` dò câu này và coi là "không khớp" dù retrieval đã trả hit.

Không được nới lỏng threshold ở lớp 1 với kỳ vọng lớp 2 "sẽ bắt được" — hai lớp độc lập, đều phải giữ chặt.

## Quy tắc trả lời (business rules — bắt buộc)

1. **Chỉ trả lời trong phạm vi dữ liệu DB.** Không suy diễn ngoài dữ liệu xã.
2. **Không khớp → fallback liên hệ UBND.** Không được bịa.
3. **Luôn kèm dẫn nguồn** (`source`): tên mục dữ liệu + căn cứ pháp lý nếu có.
4. **Thủ tục → luôn kèm `online_url`** để frontend tự sinh QR.
5. Giọng văn: lịch sự, ngắn gọn, dễ hiểu cho người dân mọi lứa tuổi.

## Chấm điểm retrieval (scoring hiện tại)

- Lọc stop-word tiếng Việt trước khi tính điểm (từ như "làm", "có", "ở", "đâu"…) — tránh một từ phổ biến vô tình khớp nhầm nhiều tài liệu không liên quan.
- Token câu hỏi khớp **nguyên từ** trong text tài liệu: **+2**/token (không dùng substring thô trên toàn chuỗi — dễ khớp nhầm, ví dụ "hộ" khớp nhầm "Hòa" nếu so substring).
- Prefix match (từ bắt đầu bằng token, token ≥ 3 ký tự): **+0.5**.
- Cụm keyword của tài liệu nằm trong câu hỏi: **+4** (tín hiệu keyword mạnh nhất). Trước đây cụm keyword còn được **miễn cổng cosine**; đã bỏ 08/2026 — xem mục dưới.
- **Điểm semantic đã trừ nền** (`SEMANTIC_FLOOR = 0.60` trong `retrieval.py`): cosine của gemini-embedding có "nền" ~0.5 giữa mọi cặp văn bản tiếng Việt kể cả không liên quan (đo trên KB production 08/2026: câu rác 0.48–0.625, đích đúng 0.66–0.82). Chỉ phần cosine vượt nền được rescale về `[0..rag_semantic_weight]` và cộng vào score — tài liệu không liên quan nhận ~0 điểm semantic thay vì ~0.5×weight "miễn phí".
- **Cổng cosine per-hit** (`SEMANTIC_GATE_MIN_COS = 0.65`): doc có embedding mà cosine < 0.65 → loại hẳn khỏi kết quả, dù keyword score cao. Chặn token rác ("thu", "do", "gia"…) cộng dồn ≥4đ cho câu hoàn toàn ngoài phạm vi. Doc chưa có embedding (chưa backfill) bỏ qua cổng — giữ chế độ keyword-only cũ.
- **Cổng áp dụng cho MỌI nguồn, kể cả `contact`/`commune`.** Hai nguồn này không có cột `embedding` (text ghép tại query-time từ bảng `contacts`) nên trước 08/2026 chúng đi thẳng vào kết quả, bỏ qua cổng — "giờ làm việc của ngân hàng Vietcombank ở đâu?" khớp `contact` chỉ nhờ 2 token "gio" + "viec" (đúng 4.0 = ngưỡng). Nay `_embed_static_doc()` embed text của chúng một lần rồi cache theo tiến trình; embed lỗi → trả `None` → cổng bỏ qua như cũ (fail-open, chat không vỡ).
- **Khớp cụm keyword KHÔNG còn miễn cổng cosine.** Đo lại 08/2026 trên toàn KB: doc đúng của mọi câu hợp lệ (15 câu chuẩn + 12 câu khẩu ngữ) đều có cosine 0.737–0.821, tức không câu hợp lệ nào cần miễn cổng; trong khi miễn cổng là đường lọt của mọi false-positive đo được — "đặt vé máy bay online" khớp cụm `online` của FAQ-02 (cos 0.603), "vì sao ý kiến…" khớp cụm `sao y` của CT-01 (cos 0.589), "giờ làm việc của ngân hàng Vietcombank" khớp cụm `giờ làm việc` của FAQ-01 (cos 0.633).
- **Giới hạn đã biết:** cổng cosine không tách được câu rác *gần nghĩa thật* — ví dụ "nộp thuế thu nhập cá nhân online thế nào" đạt cos 0.708 với FAQ-02 và vẫn lọt lớp 1. Lớp 2 (refusal phrase của Gemini) là lưới cuối cho nhóm này.
- **Ngưỡng khớp tối thiểu: 4.0** trên tổng (keyword + semantic-đã-trừ-nền).
- **Đo lại bằng `backend/scripts/eval_retrieval.py`** (`cd backend && python3 scripts/eval_retrieval.py`, thêm `--verbose` để xem điểm từng doc). Script chạy trên `data/seed-knowledge-base.json` với embedding thật, **không cần DB**, và exit code ≠ 0 khi có câu sai. Kết quả sau lần sửa 08/2026: **18/18 câu hợp lệ khớp đúng · 14/14 câu ngoài phạm vi fallback đúng**.
- **Bắt buộc chạy lại script này trước khi deploy** mỗi khi đổi `SEMANTIC_FLOOR`/`SEMANTIC_GATE_MIN_COS`/`MIN_MATCH_SCORE`, đổi `EMBEDDING_PROVIDER`, hoặc sửa `keywords` trong seed.

> Khi thêm thủ tục mới qua `/admin`, **bắt buộc điền `keywords`** đa dạng cách người dân hỏi (khẩu ngữ, viết tắt, từ đồng nghĩa) — vẫn cần dù đã có semantic search, vì keyword score vẫn là một phần của hybrid score.

## Mở rộng KB bằng pipeline ingest

Công cụ chạy tay ở `backend/scripts/ingest/` (crawl → trích xuất → duyệt tay → gộp).
Hướng dẫn vận hành: `backend/scripts/ingest/README.md`. Thiết kế:
`docs/superpowers/specs/2026-08-11-kb-ingest-pipeline-design.md`.

Hai điều liên quan trực tiếp tới module AI:

1. **KB dày lên là phải đo lại retrieval.** Ba ngưỡng ở mục trên được hiệu chỉnh trên KB
   49 bản ghi. Thêm hàng trăm bản ghi làm câu rác có nhiều "hàng xóm gần nghĩa" hơn, và
   làm câu hành chính dễ bị bài văn hoá cướp mất (cùng token "thôn", "ở đâu"). Chạy
   `eval_retrieval.py` sau **mỗi** lần merge, và mở rộng battery cho nội dung mới.
   Câu trong nhóm "ngoài phạm vi" mà nay KB đã có dữ liệu thật thì **chuyển sang nhóm hợp
   lệ**, không phải hạ ngưỡng cho vừa.

2. **Quota Gemini là tài nguyên chung.** `gemini-2.5-flash` free tier chỉ
   **20 request/ngày** trên mỗi project (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
   đo thật 11/08/2026). `generate()` của trợ lý và bước trích xuất của ingest dùng chung
   model đó. Chạy ingest bằng đúng key production sẽ đốt hết lượt của người dân và trợ lý
   tụt xuống `_generate_template()` cho tới hết ngày — **dùng key riêng cho ingest**.

## Vận hành embedding

- `embedding` (cột `Vector(768)`, pgvector — 768 chiều vì đây là dimension đã chọn cho `gemini-embedding-001`, provider mặc định) được tính và lưu ở **write-time**: seed (`scripts/seed_from_json.py`) và admin CRUD (`routers/admin.py`) — không tính lại cho toàn bộ KB mỗi lần chat.
- Sau khi apply migration thêm/đổi cột `embedding`, chạy `python3 scripts/backfill_embeddings.py --force` để embed lại toàn bộ record trong DB.
- Cả 2 provider cần API key hợp lệ (`GEMINI_API_KEY` hoặc `DEEPINFRA_API_KEY` tùy provider) — thiếu key: `embed_text()` raise lỗi, seed/admin CRUD bắt lỗi này và bỏ qua embed (log cảnh báo), retrieval tự động chỉ dùng keyword score cho các record chưa có embedding.
- Đổi provider (`EMBEDDING_PROVIDER`) → **bắt buộc migration đổi dimension cột `Vector()`** (768 ↔ 1024) rồi mới `backfill_embeddings.py --force` — 2 provider hiện tại ra vector khác chiều nên không thể chỉ đổi biến env.
- **Chi phí**: cả 2 đều tính phí theo token (rất rẻ) — `gemini` gộp chung billing với Gemini generation đã dùng sẵn; `deepinfra` là chi phí riêng nhưng rẻ hơn (~$0.01/triệu token) và chất lượng tốt hơn.
