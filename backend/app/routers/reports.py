"""Phản ánh, kiến nghị của người dân.

Chỉ tài khoản đã đăng nhập gửi được. Lý do không mở cho khách vãng lai: form công
khai nối thẳng vào relay mail là một đường spam, mà relay đó dùng CHUNG quota Gmail
với mã OTP đăng ký — spam hết quota là hỏng luôn đường tạo tài khoản.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import api_error
from app.db.session import get_db
from app.models import Report, User
from app.schemas.report import ReportCreate, ReportOut
from app.services.deps import get_current_user_required
from app.services.email import send_report_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


def _sent_last_24h(db: Session, user_id) -> int:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    return (
        db.query(Report)
        .filter(Report.user_id == user_id, Report.created_at >= since)
        .count()
    )


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    payload: ReportCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> Report:
    if _sent_last_24h(db, user.id) >= settings.report_daily_limit:
        raise api_error(
            429,
            "report_quota_exceeded",
            f"Bạn đã gửi {settings.report_daily_limit} phản ánh trong 24 giờ qua. "
            "Vui lòng thử lại sau, hoặc liên hệ trực tiếp UBND xã nếu việc gấp.",
        )

    report = Report(
        user_id=user.id,
        category=payload.category,
        content=payload.content,
        location=payload.location,
    )
    db.add(report)
    # Lưu DB TRƯỚC khi gửi mail: DB là nguồn sự thật, mail chỉ là bản sao báo tin.
    # Commit xong mới có `seq` do Postgres cấp, tức mới có mã phiếu.
    db.commit()
    db.refresh(report)

    # Gửi mail SAU khi trả lời, giống hệt cách issue_otp() làm. Gọi đồng bộ thì một
    # lần relay Apps Script chậm hoặc lỗi sẽ bắt người dân ngồi chờ tới 30 giây
    # timeout mới thấy phản hồi — đã gặp thật một lần Google trả 404 nhất thời.
    background.add_task(
        send_report_email,
        code=report.code,
        category=report.category,
        content=report.content,
        location=report.location,
        sender_name=user.display_name,
        sender_email=user.email,
        created_at=report.created_at,
    )
    return report


@router.get("/me", response_model=list[ReportOut])
def my_reports(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
