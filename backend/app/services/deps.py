import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Trả về User nếu có token hợp lệ, None nếu là khách vãng lai. Không raise lỗi."""
    if creds is None:
        return None
    payload = decode_access_token(creds.credentials)
    if not payload:
        return None
    user = db.get(User, uuid.UUID(payload["sub"]))
    return user


def get_current_user_required(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cần đăng nhập")
    return user


def require_admin(user: User = Depends(get_current_user_required)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yêu cầu quyền admin")
    return user
