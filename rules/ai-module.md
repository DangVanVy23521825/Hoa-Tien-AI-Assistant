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
   → response: { answer_html, source, matched: bool }
```

| Hàm | Trách nhiệm |
|-----|-------------|
| `normalize(s)` | Chuẩn hoá tiếng Việt: bỏ dấu, đ→d, hạ thường |
| `retrieve(db, query, topK)` | Hybrid: keyword scoring (như cũ) + semantic similarity (cosine, embedding lưu sẵn qua pgvector) |
| `embed_text(text, task_type)` | `backend/app/services/embeddings.py` — định tuyến theo `EMBEDDING_PROVIDER` tới `_embed_gemini()` hoặc `_embed_deepinfra()`. `task_type` dùng thật với Gemini (`RETRIEVAL_QUERY`/`RETRIEVAL_DOCUMENT`), giữ cho tương thích khi gọi `_embed_deepinfra()` (bge-m3 không cần) |
| `call_gemini(prompt)` | `backend/app/services/llm.py` — gọi Gemini generation, ép grounding qua system prompt, raise `LlmError` nếu lỗi/timeout để caller fallback |
| `generate(query, hits)` | Gọi Gemini khi có hit, fallback `_generate_template()` khi Gemini lỗi hoặc trả refusal phrase |

> Retrieval hybrid giữ nguyên thuật toán keyword-scoring đã kiểm chứng (`_score_doc`) làm tín hiệu chính, cộng thêm điểm semantic — nếu record chưa có embedding (`embedding is None`, ví dụ chưa chạy `backfill_embeddings.py`) thì hành vi giống hệt bản keyword-only cũ, không lỗi.

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
- Cụm keyword của tài liệu nằm trong câu hỏi: **+4** (tín hiệu mạnh nhất).
- **Ngưỡng khớp tối thiểu: 4.0** — yêu cầu ít nhất 2 tín hiệu từ độc lập hoặc 1 cụm keyword khớp, để 1 từ đơn lẻ trùng ngẫu nhiên không đủ kích hoạt câu trả lời sai.
- Đã kiểm thử 15/15 câu mẫu (10 câu hợp lệ khớp đúng, 5 câu ngoài phạm vi đều fallback đúng) — xem `docs/demo-script.md`.

> Khi thêm thủ tục mới qua `/admin`, **bắt buộc điền `keywords`** đa dạng cách người dân hỏi (khẩu ngữ, viết tắt, từ đồng nghĩa) — vẫn cần dù đã có semantic search, vì keyword score vẫn là một phần của hybrid score.

## Vận hành embedding

- `embedding` (cột `Vector(768)`, pgvector — 768 chiều vì đây là dimension đã chọn cho `gemini-embedding-001`, provider mặc định) được tính và lưu ở **write-time**: seed (`scripts/seed_from_json.py`) và admin CRUD (`routers/admin.py`) — không tính lại cho toàn bộ KB mỗi lần chat.
- Sau khi apply migration thêm/đổi cột `embedding`, chạy `python3 scripts/backfill_embeddings.py --force` để embed lại toàn bộ record trong DB.
- Cả 2 provider cần API key hợp lệ (`GEMINI_API_KEY` hoặc `DEEPINFRA_API_KEY` tùy provider) — thiếu key: `embed_text()` raise lỗi, seed/admin CRUD bắt lỗi này và bỏ qua embed (log cảnh báo), retrieval tự động chỉ dùng keyword score cho các record chưa có embedding.
- Đổi provider (`EMBEDDING_PROVIDER`) → **bắt buộc migration đổi dimension cột `Vector()`** (768 ↔ 1024) rồi mới `backfill_embeddings.py --force` — 2 provider hiện tại ra vector khác chiều nên không thể chỉ đổi biến env.
- **Chi phí**: cả 2 đều tính phí theo token (rất rẻ) — `gemini` gộp chung billing với Gemini generation đã dùng sẵn; `deepinfra` là chi phí riêng nhưng rẻ hơn (~$0.01/triệu token) và chất lượng tốt hơn.
