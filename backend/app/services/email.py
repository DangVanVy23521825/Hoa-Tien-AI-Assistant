"""Gửi email — hiện chỉ dùng cho mã OTP xác thực tài khoản.

Bốn provider chọn qua env `EMAIL_PROVIDER`:
  - "console" (mặc định, dev): in mã ra log, không cần mạng, không tốn quota.
  - "gas":     **provider của production**. Đẩy mail qua một Web App Google Apps Script
               chạy dưới danh nghĩa chính Gmail của dự án, gọi bằng HTTPS cổng 443.
               Lý do phải làm vậy: Railway CHẶN cổng SMTP ra ngoài (25/465/587) —
               container báo "[Errno 101] Network is unreachable" khi nối smtp.gmail.com.
  - "smtp":    Gmail + App Password. Chạy tốt ở local nhưng KHÔNG dùng được trên
               Railway vì lý do trên. Giữ lại cho môi trường không chặn SMTP.
  - "resend":  API Resend. Chỉ dùng được thật khi đã có domain xác thực DNS; với
               `onboarding@resend.dev` mail chỉ tới được đúng email chủ tài khoản
               Resend, nên KHÔNG dùng cho người dân khi chưa có domain.

Nguyên tắc: gửi mail hỏng KHÔNG được làm hỏng đăng ký. Mọi lỗi đều nuốt lại và log,
người dùng bấm "Gửi lại mã" là xong.
"""

import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


def _otp_subject(code: str) -> str:
    return f"{code} là mã xác thực Trợ lý hành chính số Hòa Tiến"


def _otp_html(code: str, display_name: str, ttl_minutes: int) -> str:
    return f"""\
<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#1f2937">
  <h2 style="margin:0 0 4px;color:#15803d">Trợ lý hành chính số xã Hòa Tiến</h2>
  <p style="margin:0 0 20px;color:#6b7280;font-size:14px">Xác thực địa chỉ email của bạn</p>
  <p>Xin chào <b>{display_name}</b>,</p>
  <p>Mã xác thực tài khoản của bạn là:</p>
  <p style="font-size:34px;font-weight:700;letter-spacing:10px;text-align:center;
            background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
            padding:16px;margin:20px 0;color:#15803d">{code}</p>
  <p style="font-size:14px;color:#6b7280">
    Mã có hiệu lực trong <b>{ttl_minutes} phút</b>. Nếu bạn không đăng ký tài khoản
    tại Trợ lý hành chính số xã Hòa Tiến, hãy bỏ qua email này.
  </p>
</div>"""


def _otp_text(code: str, ttl_minutes: int) -> str:
    return (
        f"Mã xác thực Trợ lý hành chính số xã Hòa Tiến của bạn là: {code}\n"
        f"Mã có hiệu lực trong {ttl_minutes} phút.\n"
        "Nếu bạn không đăng ký tài khoản, hãy bỏ qua email này."
    )


def _send_via_smtp(email: str, code: str, display_name: str, ttl: int) -> None:
    if not settings.smtp_user or not settings.smtp_password:
        logger.error("[OTP] EMAIL_PROVIDER=smtp nhưng thiếu SMTP_USER/SMTP_PASSWORD — không gửi được mail")
        return

    # Gmail từ chối gửi hộ địa chỉ khác, nên mặc định lấy chính tài khoản SMTP.
    from_email = settings.smtp_from_email or settings.smtp_user
    # Google hiển thị App Password thành 4 cụm 4 chữ ("abcd efgh ijkl mnop"); dán
    # nguyên cả dấu cách vào env là đăng nhập hỏng, nên bỏ dấu cách ở đây.
    password = settings.smtp_password.replace(" ", "")

    msg = EmailMessage()
    msg["Subject"] = _otp_subject(code)
    msg["From"] = f"{settings.smtp_from_name} <{from_email}>"
    msg["To"] = email
    msg.set_content(_otp_text(code, ttl))
    msg.add_alternative(_otp_html(code, display_name, ttl), subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_user, password)
        server.send_message(msg)
    logger.info("[OTP] Đã gửi mã tới %s qua SMTP", email)


def _send_via_gas(email: str, code: str, display_name: str, ttl: int) -> None:
    if not settings.gas_webapp_url or not settings.gas_shared_secret:
        logger.error("[OTP] EMAIL_PROVIDER=gas nhưng thiếu GAS_WEBAPP_URL/GAS_SHARED_SECRET")
        return

    res = httpx.post(
        settings.gas_webapp_url,
        json={
            "secret": settings.gas_shared_secret,
            "to": email,
            "subject": _otp_subject(code),
            "html": _otp_html(code, display_name, ttl),
            "text": _otp_text(code, ttl),
            "fromName": settings.smtp_from_name,
        },
        timeout=30.0,
        # Apps Script trả 302 sang script.googleusercontent.com rồi mới chạy thật.
        follow_redirects=True,
    )
    body = res.text[:300]
    # Apps Script trả 200 cả khi script lỗi, nên phải soi nội dung chứ không tin status.
    if res.status_code >= 400 or '"ok":true' not in body.replace(" ", ""):
        logger.error("[OTP] Apps Script không gửi được tới %s: %s %s", email, res.status_code, body)
    else:
        logger.info("[OTP] Đã gửi mã tới %s qua Apps Script", email)


def send_otp_email(email: str, code: str, display_name: str) -> None:
    """Gửi mã OTP. Không bao giờ raise — lỗi chỉ được log lại."""
    ttl = settings.otp_ttl_minutes
    provider = settings.email_provider

    if provider == "gas":
        try:
            _send_via_gas(email, code, display_name, ttl)
        except Exception as exc:  # noqa: BLE001 — mail hỏng không được làm hỏng đăng ký
            logger.error("[OTP] Gọi Apps Script thất bại tới %s: %s", email, exc)
        return

    if provider not in ("smtp", "resend"):
        # Chế độ dev: mã in thẳng ra log để test local không cần hộp thư thật.
        logger.warning("[OTP][console] %s -> %s (hết hạn sau %d phút)", email, code, ttl)
        return

    if provider == "smtp":
        try:
            _send_via_smtp(email, code, display_name, ttl)
        except Exception as exc:  # noqa: BLE001 — mail hỏng không được làm hỏng đăng ký
            logger.error("[OTP] Gửi mail SMTP thất bại tới %s: %s", email, exc)
        return

    if not settings.resend_api_key:
        logger.error("[OTP] EMAIL_PROVIDER=resend nhưng thiếu RESEND_API_KEY — không gửi được mail")
        return

    try:
        res = httpx.post(
            RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.resend_from,
                "to": [email],
                "subject": _otp_subject(code),
                "html": _otp_html(code, display_name, ttl),
                "text": _otp_text(code, ttl),
            },
            timeout=15.0,
        )
        if res.status_code >= 400:
            logger.error("[OTP] Resend trả lỗi %s: %s", res.status_code, res.text[:500])
        else:
            logger.info("[OTP] Đã gửi mã tới %s", email)
    except Exception as exc:  # noqa: BLE001 — mail hỏng không được làm hỏng đăng ký
        logger.error("[OTP] Gửi mail thất bại tới %s: %s", email, exc)
