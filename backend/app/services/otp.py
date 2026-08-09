"""Sinh, gửi và kiểm tra mã OTP xác thực email.

Chính sách (điều chỉnh qua env, xem core/config.py):
  - mã 6 chữ số, hạn `OTP_TTL_MINUTES` (mặc định 10 phút)
  - sai quá `OTP_MAX_ATTEMPTS` lần thì mã chết, phải xin mã mới
  - gửi lại cách nhau `OTP_RESEND_COOLDOWN_SECONDS`, tối đa `OTP_MAX_SENDS_PER_HOUR`/giờ

Cooldown đếm theo **email** chứ không theo IP: ở hội trại cả hội trường chung một IP
NAT nên giới hạn theo IP sẽ chặn nhầm người thật.
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import api_error
from app.core.security import hash_password, verify_password
from app.models import EmailOtp
from app.services.email import send_otp_email


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _latest_otp(db: Session, email: str) -> EmailOtp | None:
    return (
        db.query(EmailOtp)
        .filter(EmailOtp.email == email)
        .order_by(EmailOtp.created_at.desc())
        .first()
    )


def issue_otp(
    db: Session,
    email: str,
    display_name: str,
    background: BackgroundTasks,
) -> int:
    """Sinh mã mới, vô hiệu mã cũ, xếp lịch gửi mail. Trả về số giây mã còn hiệu lực."""
    now = _now()

    sent_last_hour = (
        db.query(EmailOtp)
        .filter(EmailOtp.email == email, EmailOtp.created_at > now - timedelta(hours=1))
        .count()
    )
    if sent_last_hour >= settings.otp_max_sends_per_hour:
        raise api_error(
            429,
            "otp_rate_limited",
            "Bạn đã yêu cầu mã quá nhiều lần. Vui lòng thử lại sau một giờ.",
        )

    last = _latest_otp(db, email)
    if last is not None:
        elapsed = (now - last.created_at).total_seconds()
        if elapsed < settings.otp_resend_cooldown_seconds:
            wait = int(settings.otp_resend_cooldown_seconds - elapsed)
            raise api_error(
                429, "otp_cooldown", f"Vui lòng đợi {wait} giây nữa rồi bấm gửi lại mã."
            )

    # Chỉ mã mới nhất còn giá trị — tránh cảnh người dùng bấm gửi lại rồi nhập
    # nhầm mã trong mail cũ mà hệ thống vẫn chấp nhận.
    db.query(EmailOtp).filter(
        EmailOtp.email == email, EmailOtp.consumed_at.is_(None)
    ).update({EmailOtp.consumed_at: now}, synchronize_session=False)

    code = _generate_code()
    otp = EmailOtp(
        email=email,
        code_hash=hash_password(code),
        expires_at=now + timedelta(minutes=settings.otp_ttl_minutes),
    )
    db.add(otp)
    db.commit()

    background.add_task(send_otp_email, email, code, display_name)
    return settings.otp_ttl_minutes * 60


def verify_otp(db: Session, email: str, code: str) -> None:
    """Kiểm tra mã. Đúng thì tiêu mã; sai thì raise lỗi có `code` cho frontend."""
    otp = (
        db.query(EmailOtp)
        .filter(EmailOtp.email == email, EmailOtp.consumed_at.is_(None))
        .order_by(EmailOtp.created_at.desc())
        .first()
    )
    if otp is None:
        raise api_error(400, "otp_not_found", "Chưa có mã nào đang chờ. Vui lòng bấm gửi lại mã.")

    if otp.expires_at < _now():
        raise api_error(400, "otp_expired", "Mã đã hết hạn. Vui lòng bấm gửi lại mã.")

    if otp.attempt_count >= settings.otp_max_attempts:
        raise api_error(400, "otp_locked", "Bạn đã nhập sai quá số lần cho phép. Vui lòng xin mã mới.")

    if not verify_password(code, otp.code_hash):
        otp.attempt_count += 1
        db.commit()
        remaining = settings.otp_max_attempts - otp.attempt_count
        if remaining <= 0:
            raise api_error(
                400, "otp_locked", "Bạn đã nhập sai quá số lần cho phép. Vui lòng xin mã mới."
            )
        raise api_error(400, "otp_invalid", f"Mã không đúng. Bạn còn {remaining} lần thử.")

    otp.consumed_at = _now()
    db.commit()
