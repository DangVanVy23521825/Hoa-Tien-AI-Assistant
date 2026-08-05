"""
Sinh embedding qua 1 trong 2 provider chọn bằng `settings.embedding_provider`:

- "gemini" (mặc định): API embedding của Google (`gemini-embedding-001`, 768 chiều)
  — tận dụng chung `GEMINI_API_KEY` đã dùng cho generation, không cần thêm
  tài khoản/vendor mới. Không tự host nên không có rủi ro OOM.
- "deepinfra": gọi API DeepInfra (tương thích OpenAI), model `BAAI/bge-m3`
  (1024 chiều), cần `DEEPINFRA_API_KEY` riêng — chất lượng tốt hơn (đã test:
  margin phân tách cosine similarity ~0.39 so với ~0.10 của Gemini) nhưng thêm
  1 vendor phải quản lý.

QUAN TRỌNG: 2 provider ra vector KHÁC dimension (768 vs 1024) — đổi provider phải
chạy migration đổi cột `Vector()` + `backfill_embeddings.py --force`, không chỉ
đổi biến môi trường.

Lịch sử quyết định (xem thêm `rules/deploy.md`): đã thử tự host 5 cấu hình khác
nhau (bge-m3 full ~2.5-3GB, bge-m3 quantize int8 ~1.4GB, multilingual-MiniLM
fp32 ~700MB, MiniLM quantize int8 ~850MB, vietnamese-sbert ~910MB) — tất cả đều
tốn RAM vượt quá Railway Trial plan hoặc không cải thiện được so với các lần
trước, chưa kể model nhẹ hơn (multilingual-e5, bge-micro-v2) thì chất lượng quá
kém với tiếng Việt. Chuyển hẳn sang API hosted (Gemini, tận dụng key sẵn có) để
né triệt để vấn đề RAM.
"""

from typing import Literal

import httpx
from google import genai
from google.genai import types

from app.core.config import settings

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]

EMBEDDING_DIM = 768  # chiều của provider "gemini" (mặc định) — "deepinfra" là 1024

_gemini_client: genai.Client | None = None


def _get_gemini_client() -> genai.Client:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=settings.gemini_api_key)
    return _gemini_client


def _embed_gemini(text: str, task_type: TaskType) -> list[float]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY chưa được cấu hình")

    response = _get_gemini_client().models.embed_content(
        model=settings.gemini_embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=settings.gemini_embedding_dim,
        ),
    )
    return response.embeddings[0].values


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
    """Trả về vector embedding cho `text`."""
    if settings.embedding_provider == "deepinfra":
        return _embed_deepinfra(text)
    return _embed_gemini(text, task_type)
