"""Gửi email — dùng cho mã OTP xác thực tài khoản và phiếu phản ánh của người dân.

Bốn provider chọn qua env `EMAIL_PROVIDER`:
  - "console" (mặc định, dev): in nội dung ra log, không cần mạng, không tốn quota.
  - "gas":     **provider của production**. Đẩy mail qua một Web App Google Apps Script
               chạy dưới danh nghĩa chính Gmail của dự án, gọi bằng HTTPS cổng 443.
               Lý do phải làm vậy: Railway CHẶN cổng SMTP ra ngoài (25/465/587) —
               container báo "[Errno 101] Network is unreachable" khi nối smtp.gmail.com.
  - "smtp":    Gmail + App Password. Chạy tốt ở local nhưng KHÔNG dùng được trên
               Railway vì lý do trên. Giữ lại cho môi trường không chặn SMTP.
  - "resend":  API Resend. Chỉ dùng được thật khi đã có domain xác thực DNS; với
               `onboarding@resend.dev` mail chỉ tới được đúng email chủ tài khoản
               Resend, nên KHÔNG dùng cho người dân khi chưa có domain.

Nguyên tắc: gửi mail hỏng KHÔNG được làm hỏng nghiệp vụ. `send_email` không bao giờ
raise — mọi lỗi đều nuốt lại và log. Đăng ký hỏng mail thì bấm "Gửi lại mã"; phản ánh
hỏng mail thì bản ghi vẫn nằm trong DB.

CẢNH BÁO VẬN HÀNH: OTP và phản ánh dùng CHUNG một relay và chung quota Gmail. Spam
phản ánh sẽ làm chết luôn đường đăng ký — đó là lý do `POST /reports` bắt đăng nhập
và có hạn mức ngày theo tài khoản.
"""

import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


# --------------------------------------------------------------------------- #
# Tầng vận chuyển — không biết gì về nội dung mail
# --------------------------------------------------------------------------- #


def _send_via_smtp(to: str, subject: str, html: str, text: str) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        logger.error("EMAIL_PROVIDER=smtp nhưng thiếu SMTP_USER/SMTP_PASSWORD — không gửi được mail")
        return

    # Gmail từ chối gửi hộ địa chỉ khác, nên mặc định lấy chính tài khoản SMTP.
    from_email = settings.smtp_from_email or settings.smtp_user
    # Google hiển thị App Password thành 4 cụm 4 chữ ("abcd efgh ijkl mnop"); dán
    # nguyên cả dấu cách vào env là đăng nhập hỏng, nên bỏ dấu cách ở đây.
    password = settings.smtp_password.replace(" ", "")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{from_email}>"
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_user, password)
        server.send_message(msg)


def _send_via_gas(to: str, subject: str, html: str, text: str) -> None:
    if not settings.gas_webapp_url or not settings.gas_shared_secret:
        logger.error("EMAIL_PROVIDER=gas nhưng thiếu GAS_WEBAPP_URL/GAS_SHARED_SECRET")
        return

    res = httpx.post(
        settings.gas_webapp_url,
        json={
            "secret": settings.gas_shared_secret,
            "to": to,
            "subject": subject,
            "html": html,
            "text": text,
            "fromName": settings.smtp_from_name,
        },
        timeout=30.0,
        # Apps Script trả 302 sang script.googleusercontent.com rồi mới chạy thật.
        follow_redirects=True,
    )
    body = res.text[:300]
    # Apps Script trả 200 cả khi script lỗi, nên phải soi nội dung chứ không tin status.
    if res.status_code >= 400 or '"ok":true' not in body.replace(" ", ""):
        raise RuntimeError(f"Apps Script không gửi được: {res.status_code} {body}")


def _send_via_resend(to: str, subject: str, html: str, text: str) -> None:
    if not settings.resend_api_key:
        logger.error("EMAIL_PROVIDER=resend nhưng thiếu RESEND_API_KEY — không gửi được mail")
        return

    res = httpx.post(
        RESEND_ENDPOINT,
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={
            "from": settings.resend_from,
            "to": [to],
            "subject": subject,
            "html": html,
            "text": text,
        },
        timeout=15.0,
    )
    if res.status_code >= 400:
        raise RuntimeError(f"Resend trả lỗi {res.status_code}: {res.text[:500]}")


def send_email(to: str, subject: str, html: str, text: str, *, tag: str = "MAIL") -> None:
    """Gửi một email. KHÔNG BAO GIỜ raise — lỗi chỉ được log lại.

    `tag` chỉ để nhận diện trong log ("OTP", "REPORT"), không ảnh hưởng nội dung.
    """
    provider = settings.email_provider

    if provider not in ("gas", "smtp", "resend"):
        # Chế độ dev: nội dung in thẳng ra log để test local không cần hộp thư thật.
        logger.warning("[%s][console] gửi tới %s | %s\n%s", tag, to, subject, text)
        return

    senders = {"gas": _send_via_gas, "smtp": _send_via_smtp, "resend": _send_via_resend}
    try:
        senders[provider](to, subject, html, text)
    except Exception as exc:  # noqa: BLE001 — mail hỏng không được làm hỏng nghiệp vụ
        logger.error("[%s] Gửi mail tới %s thất bại (%s): %s", tag, to, provider, exc)
    else:
        logger.info("[%s] Đã gửi mail tới %s qua %s", tag, to, provider)


# --------------------------------------------------------------------------- #
# OTP xác thực tài khoản
# --------------------------------------------------------------------------- #


def _otp_subject(code: str) -> str:
    return f"{code} là mã xác thực Trợ lý AI xã Hòa Tiến"


def _otp_html(code: str, display_name: str, ttl_minutes: int) -> str:
    return f"""\
<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1f2937">
  <h2 style="margin:0 0 4px;color:#15803d">Trợ lý AI xã Hòa Tiến</h2>
  <p style="margin:0 0 20px;color:#6b7280;font-size:14px">Xác thực địa chỉ email của bạn</p>
  <p>Xin chào <b>{display_name}</b>,</p>
  <p>Mã xác thực tài khoản của bạn là:</p>
  <p style="font-size:34px;font-weight:700;letter-spacing:10px;text-align:center;
            background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
            padding:16px;margin:20px 0;color:#15803d">{code}</p>
  <p style="font-size:14px;color:#6b7280">
    Mã có hiệu lực trong <b>{ttl_minutes} phút</b>. Nếu bạn không đăng ký tài khoản
    tại Trợ lý AI xã Hòa Tiến, hãy bỏ qua email này.
  </p>
</div>"""


def _otp_text(code: str, ttl_minutes: int) -> str:
    return (
        f"Mã xác thực Trợ lý AI xã Hòa Tiến của bạn là: {code}\n"
        f"Mã có hiệu lực trong {ttl_minutes} phút.\n"
        "Nếu bạn không đăng ký tài khoản, hãy bỏ qua email này."
    )


def send_otp_email(email: str, code: str, display_name: str) -> None:
    """Gửi mã OTP. Không bao giờ raise — lỗi chỉ được log lại."""
    ttl = settings.otp_ttl_minutes
    send_email(
        email,
        _otp_subject(code),
        _otp_html(code, display_name, ttl),
        _otp_text(code, ttl),
        tag="OTP",
    )


# --------------------------------------------------------------------------- #
# Phiếu phản ánh của người dân
# --------------------------------------------------------------------------- #

CATEGORY_LABELS = {
    "ha_tang": "Hạ tầng – giao thông",
    "moi_truong": "Môi trường – vệ sinh",
    "an_ninh": "An ninh trật tự",
    "thu_tuc": "Thủ tục hành chính",
    "khac": "Khác",
}


def _esc(s: str) -> str:
    """Nội dung do người dân nhập được nhúng vào HTML mail — phải escape."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _report_text(
    code: str, category: str, content: str, location: str | None,
    sender_name: str, sender_email: str, created_at: datetime,
) -> str:
    return (
        f"Phiếu phản ánh {code}\n"
        f"Lĩnh vực: {CATEGORY_LABELS.get(category, category)}\n"
        f"Địa điểm: {location or '(không cung cấp)'}\n"
        f"Người gửi: {sender_name} <{sender_email}>\n"
        f"Thời điểm: {created_at:%H:%M %d/%m/%Y}\n\n"
        f"Nội dung:\n{content}\n"
    )


def _report_html(
    code: str, category: str, content: str, location: str | None,
    sender_name: str, sender_email: str, created_at: datetime,
) -> str:
    rows = [
        ("Lĩnh vực", CATEGORY_LABELS.get(category, category)),
        ("Địa điểm", location or "(không cung cấp)"),
        ("Người gửi", f"{sender_name} &lt;{_esc(sender_email)}&gt;"),
        ("Thời điểm", f"{created_at:%H:%M %d/%m/%Y}"),
    ]
    rows_html = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;color:#6b7280;white-space:nowrap">{k}</td>'
        f'<td style="padding:6px 0"><b>{v}</b></td></tr>'
        for k, v in rows
    )
    return f"""\
<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1f2937">
  <h2 style="margin:0 0 4px;color:#15803d">Phản ánh mới — {code}</h2>
  <p style="margin:0 0 20px;color:#6b7280;font-size:14px">Trợ lý AI xã Hòa Tiến</p>
  <table style="font-size:14px;border-collapse:collapse;margin-bottom:20px">{rows_html}</table>
  <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;
              white-space:pre-wrap;line-height:1.6">{_esc(content)}</div>
</div>"""


def send_report_email(
    *, code: str, category: str, content: str, location: str | None,
    sender_name: str, sender_email: str, created_at: datetime,
) -> None:
    """Gửi phiếu phản ánh về hòm thư dự án. Không bao giờ raise.

    Địa chỉ nhận nằm ở env REPORT_TO_EMAIL — CỐ Ý không phải mail của UBND xã, vì
    đây là sản phẩm dự thi chứ không phải kênh tiếp nhận chính thức.
    """
    if not settings.report_to_email:
        logger.error("[REPORT] Thiếu REPORT_TO_EMAIL — phiếu %s đã lưu DB nhưng không gửi mail", code)
        return

    args = (code, category, content, location, sender_name, sender_email, created_at)
    send_email(
        settings.report_to_email,
        f"[Phản ánh {code}] {CATEGORY_LABELS.get(category, category)}",
        _report_html(*args),
        _report_text(*args),
        tag="REPORT",
    )
