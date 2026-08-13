# Thiết kế: Phản ánh, kiến nghị

Ngày: 2026-08-13 · Trạng thái: đã duyệt

## Vấn đề

Trợ lý hiện chỉ chảy một chiều: người dân hỏi, hệ thống trả lời trong phạm vi KB. Không
có đường nào để người dân **nói ngược lại** — báo cột điện nghiêng, cống tắc, hay góp ý
về thủ tục. Với một sản phẩm dự thi mang tên "Hòa Tiến số", thiếu chiều ngược là thiếu
nửa câu chuyện: chính quyền số không chỉ là tra cứu, mà là tiếp nhận.

Mong muốn: người dân gửi được phản ánh, hệ thống ghi nhận lại và gửi email báo về.

## Ràng buộc bắt buộc

**Email đi về hòm thư của dự án, KHÔNG dùng địa chỉ của UBND xã Hòa Tiến.** Đây là yêu
cầu trực tiếp của chủ dự án. Địa chỉ nhận để trong biến môi trường `REPORT_TO_EMAIL`,
không hard-code, không lọt vào git.

**Giao diện phải nói thật về đích đến.** Xem mục 5. Không có phần này thì tính năng gây
hại thật chứ không chỉ là lỗi trải nghiệm.

## Tiền đề đã loại bỏ

| Ý tưởng | Vì sao loại |
|---|---|
| Cho khách vãng lai gửi phản ánh | Form công khai nối thẳng vào relay mail là một đường spam, mà quota Gmail của Apps Script thì hữu hạn — spam hết quota là **hỏng luôn cả OTP đăng ký**, vì hai thứ dùng chung một relay. Bắt đăng nhập thì mỗi người gửi đã tốn một email thật để xác thực OTP. |
| Ảnh đính kèm | Railway không có đĩa lưu bền → phải thêm dịch vụ lưu trữ ngoài (Cloudinary/S3) hoặc nhét base64 vào mail. Đắt nhất, dễ vỡ nhất lúc demo. Để lần sau. |
| Ô số điện thoại liên hệ | Ngược nguyên tắc kiến trúc #3 ("không thu thập dữ liệu ngoài nhu cầu"). Tài khoản đã có email xác thực rồi — liên hệ lại được qua đó. |
| Dropdown chọn thôn cho ô địa điểm | KB hiện ghi xã có **22 thôn**, trong khi UBND xã công bố **15 thôn** từ 07/07/2026. Dropdown dựng trên dữ liệu sai còn tệ hơn ô trống, và nó đập thẳng vào mắt giám khảo — là người biết rõ xã có bao nhiêu thôn. Dùng ô chữ tự do cho tới khi KB được sửa. |
| Rate limit bằng `slowapi` (per-IP) | Hội trại cả xã chung một wifi NAT → per-IP chặn nhầm người thật. Đây đúng là lý do hạn mức khách phải đếm theo `X-Guest-Id` chứ không theo IP. Hạn mức phản ánh đếm **theo user trong DB**. |
| Trạng thái xử lý + giao diện admin | Dự án chưa có giao diện quản trị nào; thêm trạng thái mà không có chỗ đổi trạng thái là code chết. |

## Quyết định đã chốt

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| Ai gửi được | Chỉ tài khoản **đã xác thực OTP** | Chống spam mà không phải dựng cơ chế mới |
| Lưu ở đâu | **DB là nguồn sự thật**, mail là bản sao | Mail hỏng thì phản ánh vẫn còn |
| Thứ tự | Lưu DB trước → gửi mail sau | Mail lỗi không được làm mất phản ánh |
| Mail lỗi | Nuốt lỗi + log, vẫn trả về thành công | Cùng nguyên tắc đã áp dụng cho OTP |
| Thiếu `REPORT_TO_EMAIL` | Log lỗi, bỏ qua bước mail, vẫn ghi nhận | Không để cấu hình thiếu làm hỏng tính năng |
| Hạn mức | `REPORT_DAILY_LIMIT` (mặc định 5) phiếu/ngày/**tài khoản**, đếm trong DB | NAT-an toàn |
| Mã phiếu | `PA-0007` sinh từ cột `seq` SERIAL của Postgres | Sequence không đua nhau, không cần khoá |

## 1. Luồng

```
Người dân (đã đăng nhập)
   │
   ├─ POST /reports  {category, content, location}
   │     ├─ kiểm hạn mức ngày (đếm trong DB theo user_id)
   │     ├─ INSERT vào bảng reports        ← nguồn sự thật
   │     └─ send_report_email(...)          ← best-effort, nuốt lỗi
   │
   └─ ← 201 {code: "PA-0007", ...}
```

## 2. Backend

### Bảng `reports`

Migration Alembic mới, `down_revision = "b3c91a7f4d20"` (head hiện tại).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | UUID | khoá chính |
| `seq` | Integer, autoincrement, unique | sinh mã phiếu hiển thị `PA-0007` |
| `user_id` | UUID FK → `users.id`, NOT NULL | |
| `category` | String(50) | một trong 5 giá trị ở dưới |
| `content` | Text | |
| `location` | String(200), nullable | |
| `created_at` | timestamp, server_default now() | |

Không có cột họ tên / số điện thoại — `display_name` và `email` lấy từ quan hệ `user`
khi soạn mail, không lưu lặp.

Năm lĩnh vực (chuỗi cố định, Pydantic `Literal` chặn giá trị lạ):
`ha_tang` · `moi_truong` · `an_ninh` · `thu_tuc` · `khac`

Nhãn tiếng Việt nằm ở frontend, không lưu trong DB — đổi chữ hiển thị không phải migration.

### `POST /reports`

- Auth: `Depends(get_current_user_required)` → 401 nếu chưa đăng nhập.
- Validate (Pydantic): `content` 20–2000 ký tự sau khi trim, `location` ≤ 200, `category`
  thuộc 5 giá trị trên.
- Hạn mức: đếm `reports` của user này trong 24 giờ gần nhất; vượt `REPORT_DAILY_LIMIT`
  → 429 với `api_error(429, "report_quota_exceeded", …)`.
- Lưu DB, commit, refresh để có `seq`.
- Gọi `send_report_email(report, user)` — bọc `try/except`, lỗi chỉ log.
- Trả 201 `ReportOut`.

### `GET /reports/me`

Auth bắt buộc. Trả danh sách phiếu của chính user, mới nhất trước. Không phân trang
(hạn mức 5/ngày nên danh sách không thể phình).

### Tách phần dùng chung trong `services/email.py`

File này hiện trộn logic OTP vào tầng vận chuyển: `_send_via_gas` tự dựng subject/html
của OTP. Tách ra:

```python
def send_email(to: str, subject: str, html: str, text: str, *, tag: str = "MAIL") -> None
```

chọn provider (`gas` / `smtp` / `resend` / `console`) và **không bao giờ raise**.
`send_otp_email` gọi lại nó; thêm `send_report_email`.

**Hành vi OTP phải giữ nguyên từng chi tiết**, đặc biệt:
- Apps Script trả HTTP 200 cả khi script lỗi → vẫn phải soi `"ok":true` trong body.
- `follow_redirects=True` vì Apps Script chuyển hướng sang `script.googleusercontent.com`.
- App Password của Gmail phải bỏ dấu cách trước khi đăng nhập.
- Chế độ `console` in nội dung ra log để dev không cần hộp thư thật.

### Cấu hình mới

```python
report_to_email: str = ""     # để trống thì bỏ qua bước gửi mail
report_daily_limit: int = 5
```

## 3. Frontend

Route mới `/phan-anh` (client component, theo đúng quy ước hiện có — metadata đặt trong
`layout.tsx` cùng thư mục).

- **Chưa đăng nhập**: thay form bằng lời mời đăng nhập + nút sang `/dang-nhap`. Không
  render form rồi mới báo lỗi khi bấm gửi.
- **Đã đăng nhập**: chọn lĩnh vực (5 nút/chip) → ô nội dung (textarea, đếm ký tự, tối
  thiểu 20) → ô địa điểm (tuỳ chọn, chữ tự do) → nút Gửi.
- **Gửi xong**: hiện mã phiếu `PA-0007` nổi bật, form reset, danh sách "Phản ánh của tôi"
  ngay bên dưới tự cập nhật.
- **Lỗi hạn mức**: hiện thông báo rõ "Bạn đã gửi 5 phản ánh trong 24 giờ qua".

Thêm mục **Phản ánh** vào header (`components/header.tsx`), cả menu desktop lẫn mobile.

`lib/api.ts`: thêm `createReport()`, `getMyReports()`, interface `Report`.

## 4. Nội dung email gửi về

Tiêu đề: `[Phản ánh PA-0007] Hạ tầng – giao thông`

Thân mail (HTML + text): mã phiếu, lĩnh vực, địa điểm, nội dung, người gửi
(`display_name` + email), thời điểm gửi. Không kèm link nào tới trang quản trị vì chưa có.

## 5. Nói thật về đích đến

Hiển thị ngay dưới form, cỡ chữ đọc được, không phải chú thích mờ:

> Phản ánh được gửi tới hòm thư của nhóm phát triển Trợ lý AI xã Hòa Tiến. Đây là sản
> phẩm dự thi, **không phải kênh tiếp nhận chính thức của UBND xã**. Việc khẩn cấp xin
> liên hệ trực tiếp UBND xã: (0236) 3846176.

Lý do bắt buộc: không có dòng này, người dân báo "cột điện nghiêng" rồi yên tâm rằng
chính quyền đã biết và không báo nữa. Đó là hại thật, không phải lỗi trải nghiệm.

## 6. Rủi ro

**Dùng chung relay với OTP.** Phản ánh và mã OTP đi qua cùng một Apps Script và cùng một
quota Gmail. Spam phản ánh sẽ làm chết cả đường đăng ký. Đây là lý do chính của cả hai
lớp chặn: bắt đăng nhập + hạn mức ngày theo tài khoản.

**Chưa ai đọc hòm thư đó theo quy trình.** Mail về một hòm thư cá nhân của dự án, không
có SLA, không có người trực. Dòng chữ ở mục 5 là thứ duy nhất giữ cho kỳ vọng của người
dân khớp với thực tế.

**Migration chạy trên DB production.** Bảng mới, không sửa bảng cũ, nên rủi ro thấp —
nhưng vẫn phải `alembic upgrade head` trên Railway trước khi frontend gọi endpoint mới.

## 7. Kiểm thử

Backend chưa có test tự động. Kiểm thủ công với `EMAIL_PROVIDER=console` ở local:

| # | Việc | Kỳ vọng |
|---|---|---|
| 1 | `POST /reports` không kèm token | 401 |
| 2 | Gửi `content` 5 ký tự | 422, không tạo bản ghi |
| 3 | Gửi `category` lạ | 422 |
| 4 | Gửi hợp lệ | 201, mã `PA-0001`, log in ra nội dung mail |
| 5 | Gửi phiếu thứ hai | mã tăng lên `PA-0002` |
| 6 | Gửi quá `REPORT_DAILY_LIMIT` | 429 mã `report_quota_exceeded` |
| 7 | `REPORT_TO_EMAIL` để trống | vẫn 201, log cảnh báo thiếu cấu hình |
| 8 | `GET /reports/me` | chỉ thấy phiếu của chính mình |
| 9 | Đăng ký tài khoản mới | OTP vẫn gửi bình thường (không hồi quy sau khi tách `send_email`) |
| 10 | `/phan-anh` khi chưa đăng nhập | hiện lời mời đăng nhập, không hiện form |
| 11 | Gửi qua giao diện | hiện mã phiếu, danh sách tự cập nhật |
| 12 | `npm run build` | sạch |

## Ngoài phạm vi

Ảnh đính kèm · trạng thái xử lý · giao diện admin · thông báo cho người gửi khi có kết
quả · sửa số thôn trong KB (22 → 15) — việc riêng, cần đối soát nguồn.
