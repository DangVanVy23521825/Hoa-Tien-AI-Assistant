from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import api_error
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    OtpSentResponse,
    RegisterRequest,
    ResendOtpRequest,
    TokenResponse,
    VerifyOtpRequest,
)
from app.services.otp import issue_otp, verify_otp

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: User) -> TokenResponse:
    role = user.role.value if hasattr(user.role, "value") else user.role
    return TokenResponse(access_token=create_access_token(str(user.id), role), user=user)


@router.post("/register", response_model=OtpSentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_otp)
def register(
    request: Request,
    payload: RegisterRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Tạo tài khoản chưa xác thực và gửi mã OTP. Chưa trả token."""
    existing = db.query(User).filter(User.email == payload.email).first()

    if existing is not None and existing.is_verified:
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")

    if existing is not None:
        # Đăng ký dở rồi bỏ giữa chừng: cho đăng ký lại đè lên thay vì báo "email đã
        # dùng" — nếu không, người dân sẽ kẹt vĩnh viễn với một email không vào được.
        existing.password_hash = hash_password(payload.password)
        existing.display_name = payload.display_name
        user = existing
    else:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            role="user",
        )
        db.add(user)
    db.commit()
    db.refresh(user)

    expires_in = issue_otp(db, user.email, user.display_name, background)
    return OtpSentResponse(email=user.email, expires_in_seconds=expires_in)


@router.post("/verify-otp", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_otp)
def verify_email_otp(
    request: Request,
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
):
    """Nhập đúng mã là xác thực xong và đăng nhập luôn, không bắt nhập lại mật khẩu."""
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise api_error(404, "user_not_found", "Không tìm thấy tài khoản với email này.")

    if user.is_verified:
        raise api_error(400, "already_verified", "Tài khoản đã được xác thực. Vui lòng đăng nhập.")

    verify_otp(db, user.email, payload.code)

    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _token_response(user)


@router.post("/resend-otp", response_model=OtpSentResponse)
@limiter.limit(settings.rate_limit_otp)
def resend_otp(
    request: Request,
    payload: ResendOtpRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise api_error(404, "user_not_found", "Không tìm thấy tài khoản với email này.")
    if user.is_verified:
        raise api_error(400, "already_verified", "Tài khoản đã được xác thực. Vui lòng đăng nhập.")

    expires_in = issue_otp(db, user.email, user.display_name, background)
    return OtpSentResponse(email=user.email, expires_in_seconds=expires_in)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    if not user.is_verified:
        # Frontend bắt code này để mở thẳng màn nhập OTP và gọi /auth/resend-otp.
        raise api_error(
            403,
            "email_unverified",
            "Email chưa được xác thực. Vui lòng nhập mã đã gửi tới hộp thư của bạn.",
        )

    return _token_response(user)
