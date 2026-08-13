from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hoatien"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h — đủ cho một buổi hội trại
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    env: str = "development"

    # Rate limit (slowapi, đếm theo IP). Mặc định nới cho kịch bản demo: cả hội
    # trường có thể dùng chung 1 mạng wifi (1 IP NAT) nên limit phải đủ cho
    # vài chục khán giả truy cập cùng lúc. Siết lại qua env nếu cần.
    rate_limit_chat: str = "120/minute"
    rate_limit_login: str = "30/minute"
    # Đăng ký/gửi lại mã cũng bị đếm theo IP nên phải nới tương tự; chống spam thật
    # nằm ở cooldown theo email trong services/otp.py, không phải ở đây.
    rate_limit_otp: str = "60/minute"

    # Xác thực email bằng OTP
    otp_ttl_minutes: int = 10
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60
    otp_max_sends_per_hour: int = 5

    # Gửi mail: "console" (dev — in mã ra log, không cần mạng), "smtp" (Gmail App
    # Password — gửi được cho mọi địa chỉ mà không cần domain riêng) hoặc "resend"
    # (cần domain đã xác thực DNS, nếu không chỉ gửi được về đúng email chủ tài khoản).
    email_provider: str = "console"
    resend_api_key: str = ""
    resend_from: str = "Hòa Tiến AI <onboarding@resend.dev>"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    # Gmail: App Password 16 ký tự (cần bật 2FA), KHÔNG phải mật khẩu đăng nhập.
    smtp_password: str = ""
    smtp_from_name: str = "Trợ lý AI xã Hòa Tiến"
    # Để trống thì dùng chính SMTP_USER làm địa chỉ gửi (Gmail bắt buộc như vậy).
    smtp_from_email: str = ""

    # Relay qua Google Apps Script (provider "gas"): dùng khi hạ tầng chặn cổng SMTP
    # — Railway chặn 25/465/587 nên smtp không dùng được ở production.
    gas_webapp_url: str = ""
    gas_shared_secret: str = ""

    # Số câu hỏi khách chưa đăng nhập được hỏi thử trước khi bị yêu cầu đăng ký.
    free_guest_turns: int = 10

    # Phản ánh, kiến nghị. Hòm thư nhận là của NHÓM PHÁT TRIỂN, cố ý không phải mail
    # của UBND xã — đây là sản phẩm dự thi, không phải kênh tiếp nhận chính thức.
    # Để trống thì phiếu vẫn được lưu DB, chỉ bỏ qua bước gửi mail.
    report_to_email: str = ""
    # Hạn mức đếm theo TÀI KHOẢN trong DB, không dùng slowapi per-IP: hội trại cả xã
    # chung một wifi NAT nên chặn theo IP sẽ chặn nhầm người thật.
    report_daily_limit: int = 5

    gemini_api_key: str = ""
    gemini_generation_model: str = "gemini-2.5-flash"

    # "gemini" (mặc định — API embedding của Google, tận dụng chung GEMINI_API_KEY,
    # 768 chiều, không tự host nên không có rủi ro OOM) hoặc "deepinfra" (bge-m3
    # qua API ngoài, 1024 chiều, chất lượng tốt hơn nhưng cần thêm DEEPINFRA_API_KEY).
    # Khác dimension nên đổi provider cần migration + backfill lại, không chỉ đổi env.
    embedding_provider: str = "gemini"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dim: int = 768
    deepinfra_api_key: str = ""
    deepinfra_embedding_model_name: str = "BAAI/bge-m3"
    embedding_api_base_url: str = "https://api.deepinfra.com/v1/openai/embeddings"

    rag_semantic_weight: float = 4.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
