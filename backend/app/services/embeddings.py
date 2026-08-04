"""
Sinh embedding bằng BAAI/bge-m3 (self-host qua sentence-transformers, chạy CPU).
Model được tải và giữ trong bộ nhớ (singleton) — chỉ tải lần đầu khi có request
cần embedding đầu tiên, tránh chặn thời gian khởi động app cho các endpoint khác.

bge-m3 không cần prefix "query:"/"passage:" như một số model BGE đời trước
(xem model card BAAI/bge-m3) nên `task_type` chỉ giữ lại để tương thích chữ ký
hàm với các nơi gọi (retrieval.py, scripts, admin.py) — không ảnh hưởng kết quả.
"""

from typing import Literal

from sentence_transformers import SentenceTransformer

from app.core.config import settings

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]

EMBEDDING_DIM = 1024

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name, device="cpu")
    return _model


def embed_text(text: str, task_type: TaskType) -> list[float]:
    """Trả về vector embedding (1024 chiều, đã normalize) cho `text`."""
    embedding = _get_model().encode(text, normalize_embeddings=True)
    return embedding.tolist()
