"""Gọi Gemini để diễn giải câu trả lời từ context đã retrieve.

Đây là guardrail lớp 2 (lớp 1 là ngưỡng similarity trong retrieval.py):
system prompt ép model chỉ trả lời dựa trên context, và bắt buộc trả về
đúng REFUSAL_PHRASE khi context không đủ — generation.py sẽ dò câu này để
coi là "không khớp" dù retrieval đã trả về hit.
"""

from google import genai
from google.genai import types

from app.core.config import settings

REFUSAL_PHRASE = "Tôi không thể trả lời câu hỏi này vì không có đủ thông tin trong dữ liệu của xã."

SYSTEM_PROMPT = (
    "Bạn là trợ lý của UBND xã Hòa Tiến. CHỈ được trả lời dựa trên NGỮ CẢNH được cung cấp. "
    f"Nếu ngữ cảnh không đủ để trả lời chính xác câu hỏi, phải trả lời đúng nguyên văn: "
    f"\"{REFUSAL_PHRASE}\". "
    "Không suy đoán, không thêm chi tiết ngoài ngữ cảnh. "
    "Giọng văn lịch sự, ngắn gọn, dễ hiểu cho người dân mọi lứa tuổi."
)


class LlmError(Exception):
    pass


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def call_gemini(user_prompt: str, timeout_s: float = 10.0) -> str:
    if not settings.gemini_api_key:
        raise LlmError("GEMINI_API_KEY chưa được cấu hình")

    try:
        response = _get_client().models.generate_content(
            model=settings.gemini_generation_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),
            ),
        )
    except Exception as exc:  # noqa: BLE001 — bất kỳ lỗi API/mạng nào đều fallback về template
        raise LlmError(str(exc)) from exc

    text = (response.text or "").strip()
    if not text:
        raise LlmError("Gemini trả về nội dung rỗng")
    return text
