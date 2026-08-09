from fastapi import HTTPException


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    """Lỗi có mã máy đọc được cho frontend.

    `detail` là object `{code, message}` thay vì chuỗi để frontend rẽ nhánh theo
    `code` (ví dụ `email_unverified` → mở màn nhập OTP) mà không phải so khớp
    chuỗi tiếng Việt. Các lỗi thường vẫn trả `detail` dạng chuỗi như trước.
    """
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})
