from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hoatien"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h — đủ cho một buổi hội trại
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    env: str = "development"

    gemini_api_key: str = ""
    gemini_generation_model: str = "gemini-2.5-flash"

    # "local_onnx" (self-host, quantized bge-m3, nhẹ hơn bản gốc nhưng vẫn cần RAM
    # đáng kể) hoặc "deepinfra" (gọi API ngoài, backend nhẹ nhất, cần DEEPINFRA_API_KEY).
    # Đổi biến này + redeploy là chuyển được ngay, không cần sửa code — dùng làm
    # phương án dự phòng nếu local_onnx bị OOM trên Railway.
    embedding_provider: str = "local_onnx"
    local_embedding_model_repo: str = "gpahal/bge-m3-onnx-int8"
    deepinfra_api_key: str = ""
    deepinfra_embedding_model_name: str = "BAAI/bge-m3"
    embedding_api_base_url: str = "https://api.deepinfra.com/v1/openai/embeddings"

    rag_semantic_weight: float = 4.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
