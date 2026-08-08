"""Nhận diện câu xã giao: chào hỏi, cảm ơn, tạm biệt, hỏi trợ lý là ai/làm được gì, ừ/ok.

Vì sao cần lớp này: retrieval chấm điểm theo mức trùng khớp với knowledge base, mà
"xin chào" thì không có tài liệu nào là câu trả lời đúng — điểm keyword cao nhất chỉ ~2.0
trong khi MIN_MATCH_SCORE là 4.0. Không có lớp này thì người dân chào một câu cũng nhận
nguyên văn câu từ chối "tôi chưa có thông tin… liên hệ Bộ phận Một cửa".

Hạ MIN_MATCH_SCORE KHÔNG phải cách sửa: vừa làm câu rác lọt lại (xem rules/ai-module.md),
vừa không giải quyết được gốc vấn đề.

Nhận diện hai tầng:

1. **Khớp cụm từ** (`detect`) — miễn phí, chạy trước retrieval nên câu chào phổ biến
   không tốn lần gọi API embedding nào. Nhược điểm: chỉ bắt đúng những cụm liệt kê sẵn.
2. **Đối chiếu ngữ nghĩa** (`detect_semantic`) — chỉ chạy khi retrieval KHÔNG tìm được
   tài liệu nào, và dùng lại chính vector câu hỏi mà retrieval đã tính (`embed_query` có
   cache) nên cũng không tốn thêm lần gọi API nào. Tầng này bắt được biến thể không có
   trong danh sách: "hế lô", "có ai ở đó không", "bạn là người hay máy", "được rồi"…

Đặt tầng 2 sau retrieval là có chủ đích: câu hỏi tra cứu được thì không bao giờ bị
lớp xã giao cướp mất.
"""

import re

from app.services.embeddings import embed_texts
from app.services.retrieval import _cosine_similarity, normalize

#: Giá trị `matched_source_type` cho lượt xã giao — thống kê dùng để loại chúng ra
#: khỏi cả "đã khớp" lẫn "chưa có dữ liệu".
SOURCE_TYPE = "smalltalk"

# Ngưỡng cho tầng ngữ nghĩa. Đo 08/2026 trên gemini-embedding: 27 biến thể xã giao đạt
# cosine 0.626–1.000 với câu mẫu, trong khi 13 câu rác thật ngoài phạm vi chỉ đạt tối đa
# 0.640 ("giá vàng hôm nay bao nhiêu"). Chọn 0.68 để nằm trên toàn bộ nhóm rác với biên
# 0.04. Hai biến thể xã giao rơi dưới ngưỡng ("good morning" 0.626, "ê" 0.646) được đưa
# thẳng vào danh sách cụm từ ở tầng 1.
SEMANTIC_MIN_COS = 0.68

# Câu xã giao chỉ được nhận ở tầng 1 khi phần còn lại của câu hỏi không có nội dung thực
# chất — "chào bạn, tôi muốn làm khai sinh" phải đi tiếp vào retrieval như bình thường.
_FILLER = {
    "ban", "toi", "minh", "nhe", "nha", "a", "oi", "voi", "cac", "anh", "chi", "em",
    "co", "chu", "moi", "nguoi", "shop", "ad", "admin", "tro", "ly", "bot", "ai",
    "khong", "gi", "the", "vay", "day", "va", "cho", "duoc", "nay", "u", "ha", "hen",
    "cam", "on", "da", "ạ", "qua", "that", "lam", "roi", "y",
}

_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        "thanks",
        (
            "cam on", "cam on nhieu", "thank you", "thanks", "thank", "tks", "ty",
            "hay qua", "tuyet", "gioi day", "gioi that", "qua tuyet",
        ),
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
            "ban co phai nguoi that khong", "ban la nguoi hay may", "ai tao ra ban",
            "ban dung ai gi", "day la chatbot", "ban la bot", "ban la robot",
        ),
    ),
    (
        "greeting",
        (
            "xin chao", "chao", "hello", "helo", "hallo", "hi", "hey", "alo", "a lo",
            "he lo", "chao buoi sang", "chao buoi chieu", "chao buoi toi",
            "kinh chao", "chao ca nha", "good morning", "good afternoon", "good evening",
            "co ai khong", "co ai o do khong", "co ai do khong", "e", "ban khoe khong",
        ),
    ),
    (
        "ack",
        ("ok", "oke", "okie", "okay", "u", "vang", "da", "duoc roi", "ro roi", "hieu roi", "biet roi"),
    ),
]

# Câu mẫu cho tầng ngữ nghĩa — mỗi nhóm vài cách diễn đạt khác nhau để phủ biến thể.
_EXEMPLARS: dict[str, tuple[str, ...]] = {
    "greeting": ("xin chào", "chào bạn", "alo có ai ở đó không", "hello bạn ơi"),
    "capability": (
        "bạn là ai",
        "bạn làm được những gì",
        "bạn có phải người thật không",
        "đây là chatbot phải không",
    ),
    "thanks": ("cảm ơn bạn nhiều", "thank you", "hay quá giỏi thật"),
    "goodbye": ("tạm biệt nhé", "bye bạn"),
    "ack": ("ok", "ừ được rồi", "vâng tôi hiểu rồi"),
}

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
    "<p>Tôi là trợ lý hành chính số của <b>xã Hòa Tiến</b> — một chương trình máy tính, "
    "không phải cán bộ. Tôi trả lời dựa trên dữ liệu thủ tục và hỏi đáp do UBND xã cung "
    "cấp, và luôn kèm nguồn để bạn đối chiếu.</p>"
    "<p>Tôi giúp được:</p>"
    "<ul>"
    "<li>Tra cứu thủ tục: khai sinh, kết hôn, chứng thực, thường trú, đất đai…</li>"
    "<li>Liệt kê hồ sơ cần chuẩn bị, lệ phí, thời gian xử lý, nơi nộp</li>"
    "<li>Hướng dẫn nộp trực tuyến qua Cổng Dịch vụ công</li>"
    "</ul>"
    "<p>Việc ngoài phạm vi dữ liệu của xã thì tôi sẽ nói rõ là không có thông tin, "
    "không tự suy đoán. Trường hợp cần chắc chắn, bạn liên hệ Bộ phận Một cửa của xã.</p>"
)

_THANKS_HTML = (
    "<p>Rất vui được hỗ trợ bạn 🙂 Nếu còn thủ tục nào cần tra cứu, bạn cứ hỏi tiếp nhé.</p>"
)

_GOODBYE_HTML = (
    "<p>Tạm biệt bạn! Chúc bạn làm thủ tục thuận lợi. Khi cần, bạn quay lại hỏi bất cứ lúc nào.</p>"
)

_ACK_HTML = (
    "<p>Vâng 🙂 Bạn cần tra cứu thủ tục nào nữa không? Ví dụ: "
    "<b>“Chứng thực bản sao cần gì?”</b> hoặc <b>“Bộ phận Một cửa làm việc mấy giờ?”</b></p>"
)

_EMPTY_HTML = (
    "<p>Bạn muốn hỏi điều gì về thủ tục hành chính của <b>xã Hòa Tiến</b> ạ?</p>"
    "<p>Ví dụ: <b>“Đăng ký khai sinh cần giấy tờ gì?”</b>, "
    "<b>“Đăng ký thường trú thế nào?”</b> hoặc <b>“UBND xã ở đâu?”</b></p>"
)

_ANSWERS = {
    "greeting": _GREETING_HTML,
    "capability": _CAPABILITY_HTML,
    "thanks": _THANKS_HTML,
    "goodbye": _GOODBYE_HTML,
    "ack": _ACK_HTML,
    "empty": _EMPTY_HTML,
}


def _has_substance(text: str) -> bool:
    """True khi phần còn lại của câu vẫn mang nội dung thực chất cần tra cứu."""
    return any(t for t in text.split() if t not in _FILLER and len(t) > 1)


def detect(question: str) -> str | None:
    """Tầng 1 — khớp cụm từ. None nếu nên đưa câu hỏi vào retrieval."""
    q = normalize(question)
    if not q:
        # Chỉ có emoji/dấu câu: không phải câu hỏi, cũng không đáng nhận câu từ chối.
        return "empty" if question.strip() else None

    for kind, phrases in _PATTERNS:
        for phrase in phrases:
            # Neo biên từ: "hi" không được khớp trong "hien", "chao" không khớp "chao mung"
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            if re.search(pattern, q) and not _has_substance(re.sub(pattern, " ", q)):
                return kind
    return None


_exemplar_vectors: dict[str, list[list[float]]] | None = None


def _get_exemplar_vectors() -> dict[str, list[list[float]]]:
    """Embed câu mẫu một lần cho cả tiến trình, gộp vào MỘT lần gọi API."""
    global _exemplar_vectors
    if _exemplar_vectors is None:
        texts = [t for group in _EXEMPLARS.values() for t in group]
        try:
            vectors = embed_texts(texts, "RETRIEVAL_QUERY")
        except Exception:
            # Provider lỗi: bỏ hẳn tầng ngữ nghĩa, tầng 1 vẫn chạy bình thường.
            _exemplar_vectors = {}
            return _exemplar_vectors
        out, i = {}, 0
        for kind, group in _EXEMPLARS.items():
            out[kind] = vectors[i : i + len(group)]
            i += len(group)
        _exemplar_vectors = out
    return _exemplar_vectors


def detect_semantic(query_embedding: list[float] | None) -> str | None:
    """Tầng 2 — đối chiếu ngữ nghĩa. Chỉ gọi khi retrieval không có hit nào.

    `query_embedding` là vector đã tính trong retrieval (`embed_query`), truyền vào để
    không phải embed lại. None (provider lỗi) thì bỏ qua tầng này.
    """
    if query_embedding is None:
        return None
    best_kind, best_cos = None, 0.0
    for kind, vectors in _get_exemplar_vectors().items():
        for v in vectors:
            cos = _cosine_similarity(query_embedding, v)
            if cos > best_cos:
                best_kind, best_cos = kind, cos
    return best_kind if best_cos >= SEMANTIC_MIN_COS else None


def _response(kind: str) -> dict:
    """`matched=False` vì không khớp tài liệu nào; `matched_source_type="smalltalk"` để
    thống kê admin không xếp câu chào vào danh sách "câu hỏi chưa có dữ liệu trả lời"
    (danh sách đó dùng để tìm chỗ thiếu trong KB). `source` rỗng nên frontend không hiện
    dòng dẫn nguồn — câu xã giao không có nguồn để dẫn."""
    return {
        "answer_html": _ANSWERS[kind],
        "source": "",
        "matched": False,
        "matched_source_type": SOURCE_TYPE,
    }


def respond(question: str) -> dict | None:
    """Tầng 1: response cho câu xã giao, hoặc None nếu nên đi tiếp vào retrieval."""
    kind = detect(question)
    return _response(kind) if kind else None


def respond_semantic(query_embedding: list[float] | None) -> dict | None:
    """Tầng 2: response cho câu xã giao biến thể, hoặc None nếu nên trả lời fallback."""
    kind = detect_semantic(query_embedding)
    return _response(kind) if kind else None
