# Kịch bản thuyết minh — Hòa Tiến AI Assistant
### Phần thi "Ý tưởng sáng tạo · Hòa Tiến số" · 3–5 phút

> Cấu trúc bám đúng 4 tiêu chí chấm: **(1) ý tưởng & thông điệp · (2) nội dung tuyên truyền · (3) sáng tạo–ứng dụng–hiệu quả thực tiễn · (4) khả năng triển khai & nhân rộng.**

---

## Chuẩn bị trước khi lên (checklist trưng bày)

- [ ] Laptop mở sẵn `index.html` ở chế độ toàn màn hình, đã test offline.
- [ ] Màn hình phụ / TV để giám khảo dễ nhìn (nếu có).
- [ ] Điện thoại mở sẵn web để minh hoạ mobile + quét QR thật.
- [ ] In sẵn 1 QR cổng thông tin xã dán ở giá trưng bày.
- [ ] Tắt wifi trước khi demo để chứng minh chạy offline (điểm nhấn mạnh).
- [ ] Chuẩn bị 2–3 câu hỏi "tủ" đã test chắc chắn khớp.

---

## Kịch bản (khoảng 5 phút)

### ⏱ 0:00–0:40 — Mở đầu & thông điệp (Tiêu chí 1)

> "Kính chào ban giám khảo. Ở xã Hòa Tiến, mỗi ngày có rất nhiều người dân đến UBND chỉ để hỏi một câu: *thủ tục này cần giấy tờ gì?* Nhiều người đi cả chục cây số, chờ đợi, rồi phải quay về vì thiếu giấy tờ.
>
> Nhóm em mang đến **Hòa Tiến AI** — Trợ lý AI xã Hòa Tiến, với thông điệp: **'Hiểu Hòa Tiến, chỉ bằng một câu hỏi.'** Người dân chỉ cần hỏi bằng tiếng Việt tự nhiên, ngay trên điện thoại, là biết cần chuẩn bị gì — và không chỉ thủ tục: cả lịch sử, văn hóa, làng nghề của xã cũng hỏi được."

### ⏱ 0:40–2:20 — Demo trực tiếp (Tiêu chí 2 & 3)

> "Em xin demo trực tiếp. Và xin lưu ý — em đã **tắt mạng**, sản phẩm vẫn chạy hoàn toàn bình thường."

**Thao tác 1 — Chat:** Bấm chip *"Làm khai sinh cần gì?"*
> "Trợ lý trả lời ngay: đầy đủ hồ sơ cần chuẩn bị, lệ phí, thời gian xử lý, nơi nộp — và quan trọng là **có dẫn nguồn** và **mã QR để nộp trực tuyến**. Thông tin thống nhất, không phải nghe mỗi nơi một kiểu."

**Thao tác 2 — Hỏi tự nhiên:** Gõ một câu khẩu ngữ, ví dụ *"xin giấy độc thân"*.
> "Người dân không cần biết tên thủ tục chính xác. Em hỏi 'giấy độc thân', trợ lý hiểu đây là *xác nhận tình trạng hôn nhân* và trả lời đúng."

**Thao tác 3 — Chống bịa:** Hỏi câu ngoài phạm vi, ví dụ *"làm hộ chiếu ở đâu?"*
> "Điểm cốt lõi: khi không có dữ liệu, trợ lý **không bịa** — mà hướng người dân liên hệ UBND. Đây là nguyên tắc bắt buộc, vì thông tin hành chính sai còn nguy hiểm hơn không có."

**Thao tác 4 — Danh mục + QR:** Mở 1 thủ tục, cho xem modal + quét QR thật bằng điện thoại.

### ⏱ 2:20–3:20 — Sáng tạo & hiệu quả thực tiễn (Tiêu chí 3)

> "Điểm sáng tạo nằm ở chỗ: đây không phải một trang thông tin tĩnh, mà là một trợ lý AI theo kiến trúc **RAG** — tra cứu trong kho tri thức của xã rồi trả lời có căn cứ, có trích nguồn.
>
> Hiệu quả thực tiễn: **giảm tải cho cán bộ Một cửa** khỏi trả lời lặp lại; **tiết kiệm thời gian đi lại** cho người dân; thông tin **thống nhất và minh bạch**. Dữ liệu em dùng là thông tin thật của xã Hòa Tiến sau sáp nhập — trụ sở tại Thôn Phú Sơn Tây, Quốc lộ 14B."

### ⏱ 3:20–4:30 — Khả năng triển khai & nhân rộng (Tiêu chí 4)

> "Về triển khai: sản phẩm là một web app nhẹ, **chạy offline, mở là dùng**, không cần hạ tầng phức tạp — có thể đưa lên cổng thông tin xã ngay.
>
> Về nhân rộng: toàn bộ nội dung nằm trong một file dữ liệu. **Đổi dữ liệu là thành trợ lý của xã khác** — mô hình này nhân rộng cho bất kỳ xã, phường nào ở Đà Nẵng hay cả nước.
>
> Và kiến trúc đã sẵn sàng nâng cấp: chỉ cần cắm thêm mô hình ngôn ngữ lớn và cơ sở dữ liệu vector là thành một hệ thống RAG production đầy đủ, xử lý được kho thủ tục lớn hơn nhiều."

### ⏱ 4:30–5:00 — Chốt

> "Hòa Tiến AI biến việc tra cứu thủ tục từ một buổi đi lại thành một câu hỏi. Đó là chuyển đổi số bắt đầu từ điều gần gũi nhất với người dân. Em xin cảm ơn ban giám khảo."

---

## Câu hỏi giám khảo có thể hỏi & gợi ý trả lời

**"AI này có phải ChatGPT không? Có tốn tiền API không?"**
→ Bản demo chạy AI ngay trên máy, không gọi API nên không tốn phí và không lộ dữ liệu. Kiến trúc tách lớp cho phép cắm mô hình ngôn ngữ lớn khi cần xử lý kho tri thức lớn hơn.

**"Làm sao đảm bảo thông tin đúng?"**
→ Trợ lý chỉ trả lời trong phạm vi dữ liệu do xã cung cấp, luôn dẫn nguồn, và không bịa. Dữ liệu do cán bộ xã duyệt trước khi đưa vào.

**"Triển khai thật mất bao lâu?"**
→ Bản chạy được đã có. Để triển khai chính thức chủ yếu là công đoạn UBND đối soát và chuẩn hoá nội dung thủ tục — phần kỹ thuật đã sẵn sàng.

**"Người lớn tuổi dùng được không?"**
→ Giao diện đơn giản, hỏi bằng tiếng Việt thường ngày, có sẵn câu hỏi gợi ý để bấm. Hướng phát triển tiếp theo là trợ lý giọng nói cho người không quen gõ.
