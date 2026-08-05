# rules/ai-module.md — Đặc tả module AI

## Luồng xử lý (contract) — RAG thật: bge-m3 embedding + Gemini generation

Hai model khác nhau, hai vai trò khác nhau:
- **Embedding (retrieval)**: `BAAI/bge-m3`, qua 1 trong 2 provider chọn bằng `EMBEDDING_PROVIDER`:
  - `local_onnx` (**mặc định**): self-host bản quantize int8 (`gpahal/bge-m3-onnx-int8`, ~570MB, ~1.4GB RAM lúc chạy) qua `onnxruntime`, không cần API key.
  - `deepinfra`: gọi API DeepInfra (tương thích OpenAI), cần `DEEPINFRA_API_KEY`, backend nhẹ nhất nhưng có phí theo token.
  - Đổi 1 biến `EMBEDDING_PROVIDER` + redeploy là chuyển được, không cần sửa code — dùng làm phương án dự phòng nếu `local_onnx` OOM trên Railway. Chi tiết lịch sử quyết định (đã thử bge-m3 full self-host → OOM, thử model nhẹ hơn (e5-small/e5-base) → chất lượng phân biệt kém) xem docstring `backend/app/services/embeddings.py`.
- **Generation**: Gemini (`gemini_generation_model`) — qua API, cần `GEMINI_API_KEY`.

```
POST /chat { question: string, [token?] }
   → retrieve(db, question, topK)  [backend/app/services/retrieval.py]  → hits
       keyword score (giữ nguyên thuật toán cũ) + semantic score (embedding bge-m3, pgvector)
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
| `embed_text(text, task_type)` | `backend/app/services/embeddings.py` — định tuyến theo `EMBEDDING_PROVIDER` tới `_embed_local_onnx()` hoặc `_embed_deepinfra()`. `task_type` giữ lại cho tương thích chữ ký hàm nhưng không dùng — bge-m3 không cần prefix "query:"/"passage:" như một số model BGE đời trước |
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

- `embedding` (cột `Vector(1024)`, pgvector — 1024 chiều vì đây là dimension gốc của bge-m3) được tính và lưu ở **write-time**: seed (`scripts/seed_from_json.py`) và admin CRUD (`routers/admin.py`) — không tính lại cho toàn bộ KB mỗi lần chat.
- Sau khi apply migration thêm cột `embedding` lần đầu, chạy `python3 scripts/backfill_embeddings.py` để embed các record đã có sẵn trong DB.
- Provider `deepinfra` cần `DEEPINFRA_API_KEY` hợp lệ; provider `local_onnx` tự tải model từ HuggingFace Hub lần đầu gọi (không cần key nhưng cần mạng ổn định lúc đó). Lỗi ở cả 2 trường hợp: `embed_text()` raise lỗi, seed/admin CRUD bắt lỗi này và bỏ qua embed (log cảnh báo), retrieval tự động chỉ dùng keyword score cho các record chưa có embedding.
- Đổi provider (`EMBEDDING_PROVIDER`) hoặc model → phải chạy lại `backfill_embeddings.py --force` cho toàn bộ KB (embedding từ model/provider khác nhau không so sánh trực tiếp được với nhau — dù cùng là bge-m3, bản quantize và bản gốc cho vector hơi khác nhau về mặt số học).
- **Chi phí/tài nguyên**: `local_onnx` không tốn tiền nhưng cần ~1.4GB RAM cố định trên backend; `deepinfra` gần như không tốn RAM nhưng tính phí theo token (~$0.01/triệu token cho bge-m3, rất rẻ).
