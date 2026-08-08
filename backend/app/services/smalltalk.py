"""Nhận diện câu xã giao (chào hỏi, cảm ơn, tạm biệt, hỏi trợ lý làm được gì).

Vì sao cần lớp này: retrieval chấm điểm theo mức trùng khớp với knowledge base, mà
"xin chào" thì không có tài liệu nào là câu trả lời đúng — điểm cao nhất chỉ ~2.0 trong
khi MIN_MATCH_SCORE là 4.0. Kết quả là người dân chào một câu cũng nhận nguyên văn câu
từ chối "tôi chưa có thông tin… liên hệ Bộ phận Một cửa", nghe rất máy móc.

Hạ ngưỡng KHÔNG phải cách sửa: nó vừa làm câu rác lọt lại (xem rules/ai-module.md), vừa
không giải quyết được gốc vấn đề. Đúng hơn là chặn các ý định hội thoại này trước khi vào
retrieval và trả lời bằng kịch bản cố định — vẫn không bịa thông tin hành chính nào.

Chạy trước retrieval nên còn tiết kiệm 1 lần gọi API embedding cho mỗi câu chào.
"""

import re

from app.services.retrieval import normalize

#: Giá trị `matched_source_type` cho lượt xã giao — thống kê dùng để loại chúng ra
#: khỏi cả "đã khớp" lẫn "chưa có dữ liệu".
SOURCE_TYPE = "smalltalk"

# Câu xã giao chỉ được nhận khi phần còn lại của câu hỏi không có nội dung thực chất —
# "chào bạn, tôi muốn làm khai sinh" phải đi tiếp vào retrieval như bình thường.
_FILLER = {
    "ban", "toi", "minh", "nhe", "nha", "a", "oi", "voi", "cac", "anh", "chi", "em",
    "co", "chu", "moi", "nguoi", "moi nguoi", "shop", "ad", "admin", "trolý", "tro",
    "ly", "assistant", "bot", "ai", "khong", "khong a", "gi", "the", "vay", "day",
    "va", "cho", "duoc", "nay", "u", "ha", "hen", "yeu", "cam", "on",
}

_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "thanks",
        ("cam on", "cam on nhieu", "cam on ban", "thank you", "thanks", "thank", "tks", "ty"),
    ),
    (
        "goodbye",
        ("tam biet", "chao tam biet", "bye", "goodbye", "bai bai", "hen gap lai"),
    ),
    (
        "capability",
        (
            "ban la ai", "ban ten gi", "ban lam duoc gi", "ban giup duoc gi",
            "ban co the lam gi", "ban giup gi duoc", "giup toi voi", "help",
            "huong dan su dung", "dung the nao", "hoi gi duoc",
        ),
    ),
    (
        "greeting",
        (
            "xin chao", "chao", "hello", "helo", "hallo", "hi", "hey", "alo",
            "chao buoi sang", "chao buoi chieu", "chao buoi toi",
        ),
    ),
]

_GREETING_HTML = (
    "<p>Xin chào 👋 Tôi là trợ lý hành chính số của <b>xã Hòa Tiến</b>.</p>"
    "<p>Tôi có thể giúp bạn:</p>"
    "<ul>"
    "<li>Tra cứu thủ tục hành chính của xã</li>"
    "<li>Biết cần chuẩn bị giấy tờ gì, lệ phí và thời gian xử lý</li>"
    "<li>Tìm nơi nộp hồ sơ, giờ làm việc và cách nộp trực tuyến</li>"
    "</ul>"
    "<p>Bạn thử hỏi: <b>“Đăng ký khai sinh cần giấy tờ gì?”</b> hoặc "
    "<b>“Chứng thực bản sao mất bao nhiêu tiền?”</b></p>"
)

_CAPABILITY_HTML = (
    "<p>Tôi là trợ lý hành chính số của <b>xã Hòa Tiến</b>. Tôi trả lời dựa trên dữ liệu "
    "thủ tục và hỏi đáp do UBND xã cung cấp, và luôn kèm nguồn để bạn đối chiếu.</p>"
    "<p>Tôi giúp được:</p>"
    "<ul>"
    "<li>Tra cứu thủ tục: khai sinh, kết hôn, chứng thực, thường trú, đất đai…</li>"
    "<li>Liệt kê hồ sơ cần chuẩn bị, lệ phí, thời gian xử lý, nơi nộp</li>"
    "<li>Hướng dẫn nộp trực tuyến qua Cổng Dịch vụ công</li>"
    "</ul>"
    "<p>Việc ngoài phạm vi dữ liệu của xã thì tôi sẽ nói rõ là không có thông tin, "
    "không tự suy đoán.</p>"
)

_THANKS_HTML = (
    "<p>Rất vui được hỗ trợ bạn 🙂 Nếu còn thủ tục nào cần tra cứu, bạn cứ hỏi tiếp nhé.</p>"
)

_GOODBYE_HTML = (
    "<p>Tạm biệt bạn! Chúc bạn làm thủ tục thuận lợi. Khi cần, bạn quay lại hỏi bất cứ lúc nào.</p>"
)

_ANSWERS = {
    "greeting": _GREETING_HTML,
    "capability": _CAPABILITY_HTML,
    "thanks": _THANKS_HTML,
    "goodbye": _GOODBYE_HTML,
}


def _has_substance(text: str) -> bool:
    """True khi phần còn lại của câu vẫn mang nội dung thực chất cần tra cứu."""
    return any(t for t in text.split() if t not in _FILLER and len(t) > 1)


def detect(question: str) -> str | None:
    """Trả về loại ý định xã giao, hoặc None nếu nên đưa câu hỏi vào retrieval."""
    q = normalize(question)
    if not q:
        return None

    for kind, phrases in _PATTERNS:
        for phrase in phrases:
            # Neo biên từ: "hi" không được khớp trong "hien", "chao" không khớp "chaof"
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            if re.search(pattern, q) and not _has_substance(re.sub(pattern, " ", q)):
                return kind
    return None


def respond(question: str) -> dict | None:
    """Response cho câu xã giao, hoặc None nếu không phải xã giao.

    `matched=False` vì không khớp tài liệu nào; `matched_source_type="smalltalk"` để
    thống kê admin không xếp câu chào vào danh sách "câu hỏi chưa có dữ liệu trả lời"
    (danh sách đó dùng để tìm chỗ thiếu trong KB). `source` rỗng nên frontend không
    hiện dòng dẫn nguồn — câu xã giao không có nguồn để dẫn.
    """
    kind = detect(question)
    if kind is None:
        return None
    return {
        "answer_html": _ANSWERS[kind],
        "source": "",
        "matched": False,
        "matched_source_type": SOURCE_TYPE,
    }
