# Đặc tả yêu cầu phần mềm (SRS)
## Hòa Tiến AI Assistant — Trợ lý AI xã Hòa Tiến

| | |
|---|---|
| **Phiên bản** | 1.0 |
| **Ngày** | 18/07/2026 |
| **Phạm vi** | MVP phục vụ demo dự thi, kiến trúc mở rộng được |
| **Nhóm** | 1 người · 1–2 tuần |

> Tài liệu này viết ở mức MVP. Các hạng mục vượt phạm vi MVP được đánh dấu **[Future Enhancement]** thay vì đưa vào phạm vi chính.

---

## 1. Product Vision

**Mục tiêu.** Giúp người dân xã Hòa Tiến tra cứu thủ tục hành chính và biết cách chuẩn bị hồ sơ chỉ bằng cách hỏi tự nhiên bằng tiếng Việt, thay cho việc phải đến trực tiếp hỏi hoặc tự dò trong văn bản.

**Đối tượng người dùng.** Người dân xã Hòa Tiến (mọi lứa tuổi, chủ yếu dùng điện thoại); người ở xa cần tìm hiểu trước khi đến làm thủ tục.

**Giá trị mang lại.** Tiết kiệm thời gian đi lại và chờ đợi; thông tin thống nhất, có dẫn nguồn; giảm tải cho cán bộ Một cửa; thể hiện chuyển đổi số cấp xã một cách cụ thể.

**Pain points.** Người dân không biết cần giấy tờ gì; thông tin phân tán, khó tra; ngại hỏi; cán bộ phải trả lời lặp lại cùng một câu hỏi.

**Success Criteria.**

| Tiêu chí | Ngưỡng MVP |
|---|---|
| Trả lời đúng các câu hỏi thủ tục phổ biến | ≥ 90% câu mẫu |
| Thời gian phản hồi | < 1 giây (offline) |
| Chạy được khi mất mạng khi demo | 100% |
| Có dẫn nguồn cho câu trả lời thủ tục | 100% |

---

## 2. Stakeholders

| Stakeholder | Trách nhiệm / quan tâm |
|---|---|
| Người dân | Người dùng cuối — tra cứu, hỏi đáp, quét QR |
| Cán bộ UBND / Bộ phận Một cửa | Cung cấp & xác nhận nội dung thủ tục; hưởng lợi từ việc giảm tải |
| Quản trị viên nội dung | Cập nhật `knowledge-base.json` khi thủ tục thay đổi |
| Ban tổ chức / Ban giám khảo | Đánh giá ý tưởng, tính ứng dụng, khả năng nhân rộng |
| Nhóm phát triển (bạn) | Thiết kế, xây dựng, demo, bảo trì |

---

## 3. Functional Requirements

| ID | Name | Mô tả | Priority | Actors | Input | Output | Business Rules |
|---|---|---|---|---|---|---|---|
| FR-001 | AI Chat | Trả lời câu hỏi thủ tục bằng tiếng Việt tự nhiên | Must | Người dân | Câu hỏi text | Câu trả lời + dẫn nguồn (+ QR nếu là thủ tục) | Chỉ trả lời trong phạm vi KB; không bịa |
| FR-002 | Tra cứu thủ tục | Hiển thị danh mục thủ tục dạng thẻ | Must | Người dân | Thao tác duyệt/nhấn | Danh sách + chi tiết thủ tục | Dữ liệu từ KB |
| FR-003 | Chi tiết hồ sơ | Xem hồ sơ cần chuẩn bị, phí, thời gian, căn cứ | Must | Người dân | Chọn 1 thủ tục | Modal chi tiết đầy đủ | Hiển thị đúng dữ liệu KB |
| FR-004 | QR Code | Sinh QR dẫn tới Dịch vụ công / tài liệu | Must | Người dân | Thủ tục / cổng | Ảnh QR | Link lấy từ KB |
| FR-005 | FAQ | Hỏi đáp thường gặp dạng accordion | Should | Người dân | Nhấn câu hỏi | Câu trả lời | Dữ liệu từ KB |
| FR-006 | Liên hệ UBND | Hiển thị địa chỉ, ĐT, giờ làm việc, QR cổng | Must | Người dân | — | Thông tin liên hệ | Dữ liệu từ KB |
| FR-007 | Câu hỏi gợi ý | Chip câu hỏi mẫu để bấm nhanh | Should | Người dân | Nhấn chip | Kích hoạt FR-001 | — |
| FR-008 | Responsive | Chạy tốt trên mobile & desktop | Must | Người dân | — | Bố cục thích ứng | — |
| FR-009 | Fallback liên hệ | Không có dữ liệu → hướng liên hệ UBND | Must | Người dân | Câu hỏi ngoài phạm vi | Lời nhắn liên hệ | Không bịa thông tin |
| FR-010 | Quản lý nội dung | Panel quản trị cập nhật KB | Could **[Future Enhancement]** | Quản trị viên | Form nội dung | KB cập nhật | — |

---

## 4. Non-functional Requirements

| Loại | Yêu cầu |
|---|---|
| Performance | Phản hồi < 1s (offline); trang tải < 2s |
| AI Response Time | Tức thời ở chế độ offline; < 3s khi dùng LLM API [Future] |
| Security | Không thu thập dữ liệu cá nhân; không backend ở bản MVP nên bề mặt tấn công tối thiểu |
| Scalability | KB tách khỏi UI; nâng lên vector DB + LLM không phải viết lại giao diện |
| Availability | Offline-first → không phụ thuộc mạng khi demo |
| Accessibility | Tương phản đủ, focus bàn phím, aria-label nút icon |
| Responsive | Mobile-first, breakpoint 860px |
| Maintainability | Single-file, vanilla JS, dữ liệu JSON versioned |
| Logging / Monitoring | **[Future Enhancement]** khi có backend |
| Browser Compatibility | Chrome, Edge, Firefox, Safari bản hiện hành |

---

## 5. User Stories (trích)

**US-01 — Tra cứu hồ sơ.**
*As a* người dân, *I want* hỏi "làm khai sinh cần gì", *so that* tôi biết chuẩn bị đủ giấy tờ trước khi đến xã.
*Acceptance:* nhập/bấm câu hỏi → nhận danh sách hồ sơ + phí + thời gian + QR + dẫn nguồn, trong < 1s.

**US-02 — Duyệt danh mục.**
*As a* người dân, *I want* xem danh sách thủ tục, *so that* tôi tìm được thủ tục mình cần mà không biết gọi tên chính xác.
*Acceptance:* thấy grid thẻ; nhấn 1 thẻ mở chi tiết đầy đủ.

**US-03 — Nộp trực tuyến.**
*As a* người dân, *I want* quét QR, *so that* tôi tới thẳng Cổng Dịch vụ công để nộp hồ sơ.
*Acceptance:* mỗi thủ tục có QR quét ra đúng link.

**US-04 — Khi trợ lý không biết.**
*As a* người dân, *I want* được chỉ nơi liên hệ khi trợ lý chưa có thông tin, *so that* tôi không bị bỏ lửng.
*Acceptance:* câu ngoài phạm vi → trả lời hướng liên hệ UBND, không bịa.

---

## 6. Use Cases

| ID | Use Case | Actor |
|---|---|---|
| UC-01 | Chat với AI tra cứu thủ tục | Người dân |
| UC-02 | Duyệt danh mục thủ tục | Người dân |
| UC-03 | Xem chi tiết hồ sơ | Người dân |
| UC-04 | Quét QR nộp trực tuyến | Người dân |
| UC-05 | Xem FAQ | Người dân |
| UC-06 | Xem thông tin liên hệ UBND | Người dân |
| UC-07 | Quản lý dữ liệu KB **[Future Enhancement]** | Quản trị viên |

---

## 7. User Flow

Mở web → thấy hero + gợi ý → **hoặc** bấm chip câu hỏi / gõ câu hỏi vào chat → trợ lý retrieve KB → trả lời kèm hồ sơ + QR + nguồn → (tuỳ chọn) mở danh mục xem chi tiết thủ tục trong modal → quét QR sang Dịch vụ công → nếu cần thêm, xem mục Liên hệ để gọi/đến UBND.

---

## 8. Business Rules

1. AI chỉ trả lời trong phạm vi dữ liệu xã Hòa Tiến.
2. Không tự tạo thông tin ngoài KB.
3. Luôn dẫn nguồn khi trả lời thủ tục.
4. Không biết → hướng người dân liên hệ UBND.
5. Thủ tục luôn kèm QR nộp trực tuyến.
6. Thông tin phí/thời gian chưa đối soát phải ghi rõ "(tham khảo)".

---

## 9. Data Requirements

Danh mục thủ tục · hồ sơ yêu cầu · lệ phí · thời gian xử lý · nơi nộp · căn cứ pháp lý · link Dịch vụ công · thông tin xã (diện tích, dân số, lịch sử sáp nhập) · liên hệ UBND (địa chỉ, ĐT, giờ làm việc, cổng thông tin) · FAQ · từ khoá tra cứu.

---

## 10. Database Design **[Future Enhancement]**

Bản MVP dùng JSON. Khi lên production:

| Table | PK | FK | Quan hệ |
|---|---|---|---|
| `procedures` | id | category_id | n–1 với `categories` |
| `categories` | id | — | 1–n với `procedures` |
| `documents` | id | procedure_id | n–1 với `procedures` |
| `faq` | id | — | — |
| `contacts` | id | — | — |
| `chat_logs` | id | — | (phân tích câu hỏi, [Future]) |

---

## 11. API Requirements **[Future Enhancement — target khi có backend]**

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/procedures` | Danh mục thủ tục |
| GET | `/procedures/{id}` | Chi tiết 1 thủ tục |
| GET | `/faq` | Danh sách FAQ |
| GET | `/contacts` | Thông tin liên hệ |
| POST | `/chat` | Gửi câu hỏi, nhận trả lời (RAG) |

MVP hiện tại không cần backend — mọi truy vấn xử lý client-side trên KB.

---

## 12. AI Requirements

| Hạng mục | MVP (hiện tại) | Production [Future Enhancement] |
|---|---|---|
| Retrieval | Keyword/fuzzy scoring, chuẩn hoá tiếng Việt | Vector similarity search |
| Generation | Template hoá từ ngữ cảnh | LLM sinh câu trả lời có grounding |
| Knowledge Base | `knowledge-base.json` | Chunk + embedding |
| RAG | Mô phỏng (retrieve → generate) | RAG đầy đủ |
| Embedding | — | `text-embedding-3-small` / model đa ngữ |
| Vector DB | — | Qdrant / pgvector / Chroma |
| LLM đề xuất | — | GPT-4o-mini / Claude Haiku / Gemini Flash (chi phí thấp, tiếng Việt tốt) |
| Hallucination Prevention | Chỉ trả từ KB; fallback khi rỗng | Prompt khoá phạm vi + nhiệt độ thấp + bắt buộc citation |
| Citation | Dòng dẫn nguồn mỗi câu trả lời | Trích nguồn theo chunk |
| Conversation Memory | Chưa cần (mỗi câu độc lập) | Lưu ngữ cảnh hội thoại |
| Context Window | Nhỏ (1 KB) | Quản lý theo topK chunk |

**Kết luận RAG:** MVP dùng RAG *mô phỏng* (đủ cho demo và chính xác vì dữ liệu nhỏ). Khi KB lớn lên hoặc câu hỏi đa dạng hơn → nâng lên RAG thật, giữ nguyên contract `retrieve()/generate()`.

---

## 13. UI Pages / Sections

| Section | Components | Actions | Validation |
|---|---|---|---|
| Hero | Tiêu đề, CTA, thống kê, art | Cuộn tới chat/thủ tục | — |
| Trợ lý AI | Khung chat, chip gợi ý, ô nhập | Gửi câu hỏi | Chặn gửi rỗng |
| Danh mục thủ tục | Grid thẻ | Mở modal chi tiết | — |
| Modal chi tiết | Hồ sơ, phí, thời gian, QR | Đóng, hỏi trợ lý | — |
| FAQ | Accordion | Mở/đóng | — |
| Liên hệ | Địa chỉ, ĐT, giờ, QR cổng | Quét QR | — |
| Admin **[Future]** | Form quản lý KB | CRUD nội dung | Kiểm tra bắt buộc field |

---

## 14. MVP Scope

**Must Have:** AI Chat, tra cứu & chi tiết thủ tục, QR, liên hệ UBND, responsive, fallback liên hệ.
**Should Have:** FAQ, chip câu hỏi gợi ý.
**Nice to Have:** hiệu ứng typing, animation, đa nhóm thủ tục mở rộng.

---

## 15. Future Scope

Voice Assistant · OCR giấy tờ · AI Document Validation · Đa ngôn ngữ · Mobile App · Agent workflow · Tích hợp trực tiếp Cổng Dịch vụ công · Admin panel · RAG thật (embedding + vector DB + LLM) · Backend FastAPI · Analytics câu hỏi người dân.

---

## 16. Risks

| Rủi ro | Loại | Giảm thiểu |
|---|---|---|
| Mất mạng/điện khi demo | Demo | Offline-first, KB nhúng sẵn |
| Dữ liệu thủ tục sai/lỗi thời | Dữ liệu | Ghi "(tham khảo)", đối soát với UBND |
| AI bịa thông tin | AI | Chỉ trả từ KB + fallback |
| Câu hỏi ngoài dự kiến không khớp | AI | Keywords đa dạng + fallback lịch sự |
| Thời gian phát triển ngắn | Thời gian | Cắt Future Enhancement khỏi MVP |
| Lộ thông tin cá nhân | Bảo mật | Không thu thập dữ liệu người dùng ở MVP |

---

## 17. Deliverables

Source code (`index.html`) · UI hoàn chỉnh · Module AI (retrieve/generate) · Knowledge base JSON · Tài liệu (SRS này + rules/ + CLAUDE.md) · Hướng dẫn chạy (`rules/build.md`) · Kịch bản demo (`docs/demo-script.md`). **[Future]** API + backend + deployment.

---

## 18. Development Roadmap

**Tuần 1 — Nền tảng & demo chạy được.**
Thu thập & chuẩn hoá dữ liệu thủ tục vào KB → dựng UI (hero, chat, thủ tục, FAQ, liên hệ) → retrieval offline + generate → responsive → kiểm thử câu hỏi mẫu.

**Tuần 2 — Hoàn thiện & dự thi.**
Tinh chỉnh giao diện theo bản sắc Hòa Tiến → thêm QR & modal chi tiết → viết SRS + kịch bản thuyết minh → tập demo 5 phút → chuẩn bị trưng bày (thiết bị, màn hình, QR in sẵn). **[Future]** nâng lên RAG thật sau hội trại.
