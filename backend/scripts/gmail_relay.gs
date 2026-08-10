/**
 * Relay gửi mail cho Trợ lý hành chính số Hòa Tiến.
 *
 * Vì sao cần: Railway chặn cổng SMTP ra ngoài (25/465/587), backend không nối được
 * smtp.gmail.com. Web App này chạy dưới danh nghĩa chính tài khoản Gmail của dự án và
 * nhận lệnh qua HTTPS cổng 443 — đường duy nhất không bị chặn.
 *
 * CÁCH DỰNG (làm 1 lần, ~5 phút):
 *  1. Đăng nhập script.google.com bằng CHÍNH tài khoản Gmail dùng để gửi
 *     (hoatienaiassistant@gmail.com), tạo project mới, dán toàn bộ file này vào.
 *  2. Sửa SHARED_SECRET bên dưới thành một chuỗi ngẫu nhiên dài (tự đặt, coi như mật khẩu).
 *  3. Deploy → New deployment → chọn type "Web app":
 *       - Execute as:      Me (tài khoản của bạn)   ← bắt buộc, để mail gửi từ Gmail này
 *       - Who has access:  Anyone                   ← bắt buộc, backend gọi ẩn danh
 *     Bấm Deploy, chấp nhận cảnh báo quyền, copy "Web app URL" (dạng
 *     https://script.google.com/macros/s/.../exec).
 *  4. Đặt biến môi trường trên Railway:
 *       EMAIL_PROVIDER=gas
 *       GAS_WEBAPP_URL=<Web app URL vừa copy>
 *       GAS_SHARED_SECRET=<đúng chuỗi ở bước 2>
 *
 * Hạn mức Gmail thường: 100 mail/ngày. Sửa code sau này phải Deploy lại (New version)
 * thì URL cũ mới chạy bản mới.
 */

const SHARED_SECRET = 'DOI-CHUOI-NAY-THANH-MOT-CHUOI-NGAU-NHIEN-DAI';

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);

    // Web App để "Anyone" truy cập được, nên bí mật chung là thứ duy nhất chặn người lạ
    // mượn Gmail của bạn để gửi thư rác.
    if (body.secret !== SHARED_SECRET) {
      return json({ ok: false, error: 'unauthorized' });
    }
    if (!body.to || !body.subject) {
      return json({ ok: false, error: 'missing_fields' });
    }

    MailApp.sendEmail({
      to: body.to,
      subject: body.subject,
      body: body.text || '',
      htmlBody: body.html || undefined,
      name: body.fromName || 'Trợ lý hành chính số Hòa Tiến',
    });

    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}

/** Chạy tay trong editor để kiểm tra quyền gửi mail đã được cấp chưa. */
function testSend() {
  MailApp.sendEmail({
    to: Session.getActiveUser().getEmail(),
    subject: 'Thử relay Hòa Tiến AI',
    body: 'Nếu bạn nhận được thư này thì relay đã sẵn sàng.',
  });
}
