"""
Sinh embedding qua 1 trong 2 provider chọn bằng `settings.embedding_provider`:

- "local" (mặc định): self-host `paraphrase-multilingual-MiniLM-L12-v2` qua
  `sentence-transformers` (~470MB tải về, ~700MB RAM lúc chạy) — không cần API key.
  384 chiều.
- "deepinfra": gọi API DeepInfra (tương thích OpenAI), model `BAAI/bge-m3`, cần
  DEEPINFRA_API_KEY, backend nhẹ nhất nhưng có phí theo token. 1024 chiều.

QUAN TRỌNG: 2 provider ra vector KHÁC dimension (384 vs 1024) — đổi provider phải
chạy migration đổi cột `Vector()` + `backfill_embeddings.py --force`, không chỉ
đổi biến môi trường.

Lịch sử quyết định (xem thêm `rules/deploy.md`): bge-m3 full self-host (torch,
~2.5-3GB RAM) và cả bản quantize int8 (onnxruntime, ~1.4GB RAM) đều OOM-kill thật
trên Railway Trial plan. Model nhẹ hơn cùng họ multilingual-e5 (small/base) né
được RAM nhưng chất lượng phân biệt kém (margin cosine similarity ~0.02-0.05).
Model tiếng Anh-only (bge-micro-v2) cho kết quả sai hẳn với tiếng Việt (tokenizer
xé nát dấu, xếp hạng sai). `paraphrase-multilingual-MiniLM-L12-v2` là điểm cân
bằng tốt nhất tìm được: ~700MB RAM (thấp hơn cả 2 lần OOM trước) và margin phân
tách ~0.30-0.35 (tốt hơn cả bge-m3 gốc theo tỷ lệ tương đối, theo test thủ công).
"""

from typing import Literal

import httpx
from sentence_transformers import SentenceTransformer

from app.core.config import settings

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]

EMBEDDING_DIM = 384  # chiều của provider "local" (mặc định) — "deepinfra" là 1024

_local_model: SentenceTransformer | None = None


def _get_local_model() -> SentenceTransformer:
    global _local_model
    if _local_model is None:
        _local_model = SentenceTransformer(settings.local_embedding_model_name, device="cpu")
    return _local_model


def _embed_local(text: str) -> list[float]:
    embedding = _get_local_model().encode(text, normalize_embeddings=True)
    return embedding.tolist()


def _embed_deepinfra(text: str) -> list[float]:
    if not settings.deepinfra_api_key:
        raise RuntimeError("DEEPINFRA_API_KEY chưa được cấu hình")

    response = httpx.post(
        settings.embedding_api_base_url,
        headers={"Authorization": f"Bearer {settings.deepinfra_api_key}"},
        json={"model": settings.deepinfra_embedding_model_name, "input": text, "encoding_format": "float"},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def embed_text(text: str, task_type: TaskType) -> list[float]:
    """Trả về vector embedding cho `text`. `task_type` giữ lại cho tương thích
    chữ ký hàm — cả 2 model hiện dùng đều không cần prefix "query:"/"passage:"."""
    if settings.embedding_provider == "deepinfra":
        return _embed_deepinfra(text)
    return _embed_local(text)
