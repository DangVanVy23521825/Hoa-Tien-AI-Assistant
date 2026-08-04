# rules/ai-module.md — Đặc tả module AI

## Luồng xử lý (contract) — RAG thật: bge-m3 embedding + Gemini generation

Hai model khác nhau, hai vai trò khác nhau:
- **Embedding (retrieval)**: `BAAI/bge-m3` — self-host trong chính backend qua `sentence-transformers`, chạy CPU, không gọi API ngoài, không cần API key.
- **Generation**: Gemini (`gemini_generation_model`) — vẫn qua API, cần `GEMINI_API_KEY`.

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
| `embed_text(text, task_type)` | `backend/app/services/embeddings.py` — chạy `BAAI/bge-m3` local (singleton, lazy-load lần đầu). `task_type` giữ lại cho tương thích chữ ký hàm nhưng không dùng — bge-m3 không cần prefix "query:"/"passage:" như một số model BGE đời trước |
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
- Model bge-m3 chỉ tải về (lần đầu, từ HuggingFace Hub, ~2.2GB) khi hàm `embed_text()` được gọi lần đầu tiên (lazy singleton trong `embeddings.py`) — request đầu tiên gọi tới sẽ chậm hơn hẳn (tải + load model vào RAM), các lần sau dùng model đã cache trong tiến trình.
- Nếu load/embed lỗi (hết RAM, mất mạng khi tải model lần đầu...): seed/admin CRUD vẫn chạy được (bỏ qua bước embed, log cảnh báo), retrieval tự động chỉ dùng keyword score cho các record chưa có embedding.
- Đổi model embedding (`EMBEDDING_MODEL_NAME`) → phải chạy lại `backfill_embeddings.py --force` cho toàn bộ KB (embedding cũ và mới không so sánh được với nhau, và nếu dimension khác 1024 phải sửa lại cột `Vector()` qua migration mới).
- **Chi phí tài nguyên**: `torch` + `sentence-transformers` + trọng số bge-m3 cần khoảng 2-3GB RAM khi model đã load — xem `rules/deploy.md` về yêu cầu Railway plan.
