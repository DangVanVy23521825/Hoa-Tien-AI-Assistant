"""
Tạo tài khoản admin đầu tiên. Không có endpoint đăng ký admin công khai —
đây là cách duy nhất để tạo admin, theo rules/auth.md.

Chạy: python3 scripts/create_admin.py <email> <password> <ten_hien_thi>
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


def create_admin(email: str, password: str, display_name: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.role = "admin"
            db.commit()
            print(f"Đã nâng quyền admin cho tài khoản có sẵn: {email}")
            return
        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            role="admin",
        )
        db.add(user)
        db.commit()
        print(f"Đã tạo tài khoản admin: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Cách dùng: python3 scripts/create_admin.py <email> <password> <ten_hien_thi>")
        sys.exit(1)
    create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
