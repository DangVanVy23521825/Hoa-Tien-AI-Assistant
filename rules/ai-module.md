# rules/ai-module.md — Đặc tả module AI

## Luồng xử lý (contract) — giờ nằm trong backend

```
POST /chat { question: string, [token?] }
   → retrieve(question, topK)  [backend/app/services/retrieval.py]  → hits
   → generate(question, hits)  [backend/app/services/generation.py] → { answer_html, source }
   → (nếu có user) lưu vào chat_history
   → response: { answer_html, source, matched: bool }
```

| Hàm | Trách nhiệm | Nâng cấp production |
|-----|-------------|---------------------|
| `normalize(s)` | Chuẩn hoá tiếng Việt: bỏ dấu, đ→d, hạ thường | Giữ nguyên |
| `retrieve(query, topK)` | Query DB (`procedures`, `faq`, `contacts`), tính điểm khớp keyword | Thay bằng vector similarity search (pgvector) |
| `generate(query, hits)` | Dựng câu trả lời HTML từ ngữ cảnh + dẫn nguồn | Thay bằng `callLLM(query, context)` |

> Đây là port trực tiếp từ logic đã kiểm chứng trong bản offline cũ (`legacy/index.html`) — giữ nguyên thuật toán scoring, chỉ đổi nguồn dữ liệu từ JSON in-memory sang query DB.

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

> Khi thêm thủ tục mới qua `/admin`, **bắt buộc điền `keywords`** đa dạng cách người dân hỏi (khẩu ngữ, viết tắt, từ đồng nghĩa).

## Khi nâng lên RAG thật

- Bật extension `pgvector` trên PostgreSQL đang dùng (không cần vector DB riêng ở quy mô này).
- `callLLM()` truyền context đã retrieve vào prompt, ép model chỉ trả lời dựa trên context, trích nguồn, trả "không có thông tin" khi context rỗng.
- Prompt system khoá phạm vi: "Bạn là trợ lý của UBND xã Hòa Tiến, chỉ trả lời dựa trên tài liệu được cung cấp."
- Nhiệt độ thấp, log lại cặp (context, answer) để soát hallucination định kỳ.
