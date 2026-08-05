"""
Sinh embedding bằng BAAI/bge-m3, qua 1 trong 2 provider chọn bằng `settings.embedding_provider`:

- "local_onnx" (mặc định): self-host bản quantize int8 (`gpahal/bge-m3-onnx-int8`,
  ~570MB, ~1.4GB RAM lúc chạy) qua onnxruntime — không cần API key, nhưng vẫn
  cần đủ RAM trên server chạy backend.
- "deepinfra": gọi API DeepInfra (tương thích OpenAI) — backend nhẹ nhất, cần
  DEEPINFRA_API_KEY, có phí theo token (rất thấp).

Lịch sử quyết định: bge-m3 full (~2.2GB, self-host qua sentence-transformers) gây
OOM trên Railway Trial plan. Đã thử model nhẹ hơn (multilingual-e5-small/base) để
né RAM nhưng chất lượng phân biệt kém hẳn (test thực tế: margin cosine similarity
giữa tài liệu đúng/sai chỉ ~0.02-0.05, so với ~0.4 của bge-m3) — không dùng được.
Bản quantize int8 giữ chất lượng gần bge-m3 gốc (margin ~0.17-0.25 khi test) với
RAM thấp hơn nhiều — đang thử deploy thật; nếu vẫn OOM, đổi `EMBEDDING_PROVIDER=deepinfra`
và redeploy là xong, không cần sửa code.
"""

from typing import Literal

import httpx
import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

from app.core.config import settings

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"]

EMBEDDING_DIM = 1024

_onnx_session: ort.InferenceSession | None = None
_onnx_tokenizer: AutoTokenizer | None = None


def _get_onnx_runtime() -> tuple[ort.InferenceSession, AutoTokenizer]:
    global _onnx_session, _onnx_tokenizer
    if _onnx_session is None:
        repo = settings.local_embedding_model_repo
        model_path = hf_hub_download(repo, "model_quantized.onnx")
        _onnx_tokenizer = AutoTokenizer.from_pretrained(repo)
        _onnx_session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    return _onnx_session, _onnx_tokenizer


def _embed_local_onnx(text: str) -> list[float]:
    session, tokenizer = _get_onnx_runtime()
    input_names = {i.name for i in session.get_inputs()}
    encoded = tokenizer(text, return_tensors="np", padding=True, truncation=True, max_length=512)
    feed = {k: v for k, v in encoded.items() if k in input_names}
    dense_vecs = session.run(["dense_vecs"], feed)[0]
    vector = dense_vecs[0]
    return (vector / np.linalg.norm(vector)).tolist()


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
    """Trả về vector embedding (1024 chiều) cho `text`. `task_type` giữ lại cho
    tương thích chữ ký hàm — bge-m3 không cần prefix "query:"/"passage:" như
    model họ E5."""
    if settings.embedding_provider == "deepinfra":
        return _embed_deepinfra(text)
    return _embed_local_onnx(text)
