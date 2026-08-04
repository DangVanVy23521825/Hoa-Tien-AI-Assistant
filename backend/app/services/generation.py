"""
Generate câu trả lời từ ngữ cảnh đã retrieve.

Khi có hit, ưu tiên gọi Gemini (call_gemini) để diễn giải câu trả lời tự nhiên hơn,
ép grounding vào context qua system prompt (services/llm.py). Nếu Gemini lỗi/timeout
hoặc chưa cấu hình GEMINI_API_KEY, fallback về _generate_template() (logic thuần
template, không đổi so với bản trước khi nối Gemini) — chat không bao giờ vỡ.
Giữ nguyên response shape {answer_html, source, matched, matched_source_type}
để frontend không đổi.
"""

from app.models import Contact, Faq, KnowledgeArticle, Procedure
from app.services.llm import REFUSAL_PHRASE, LlmError, call_gemini
from app.services.retrieval import Hit

NO_MATCH_RESPONSE_TEMPLATE = (
    "Xin lỗi, tôi chưa có thông tin cho câu hỏi này trong dữ liệu của xã Hòa Tiến. "
    "Bạn vui lòng liên hệ trực tiếp <b>Bộ phận Một cửa – UBND xã Hòa Tiến</b>{phone_txt} "
    "để được hỗ trợ chính xác nhất."
)


def _no_match_response(fallback_phone: str) -> dict:
    phone_txt = f" qua số <b>{fallback_phone}</b>" if fallback_phone else ""
    return {
        "answer_html": NO_MATCH_RESPONSE_TEMPLATE.format(phone_txt=phone_txt),
        "source": "Nguyên tắc: không tự tạo thông tin ngoài dữ liệu xã.",
        "matched": False,
        "matched_source_type": "none",
    }


def _hit_context_text(hit: Hit) -> str:
    if hit.type == "procedure":
        p: Procedure = hit.ref
        return (
            f"Thủ tục: {p.name}\nMô tả: {p.description}\n"
            f"Hồ sơ cần chuẩn bị: {'; '.join(p.documents or [])}\n"
            f"Lệ phí: {p.fee}\nThời gian xử lý: {p.processing_time}\n"
            f"Nơi nộp: {p.place_of_submission}\nCăn cứ pháp lý: {p.legal_basis}"
        )
    if hit.type == "faq":
        f: Faq = hit.ref
        return f"Câu hỏi: {f.question}\nTrả lời: {f.answer}"
    if hit.type == "article":
        a: KnowledgeArticle = hit.ref
        return f"{a.title}\n{a.content}\nNguồn: {a.source_citation}"
    if hit.type == "contact":
        c: Contact = hit.ref
        wh = c.working_hours or {}
        return f"{c.office}\nĐịa chỉ: {c.address}\nĐiện thoại: {c.phone}\nGiờ làm việc: {wh.get('weekdays', '')}"
    # commune
    c: Contact = hit.ref
    commune = c.commune_info or {}
    return f"Thông tin xã Hòa Tiến: {commune.get('note', '')} Diện tích: {commune.get('area_km2', '?')} km², dân số: {commune.get('population', '?')}"


def _generate_llm(query: str, hits: list[Hit]) -> dict:
    context = "\n\n---\n\n".join(_hit_context_text(h) for h in hits)
    answer = call_gemini(f"Ngữ cảnh:\n{context}\n\nCâu hỏi: {query}")

    template = _generate_template(query, hits)
    if REFUSAL_PHRASE in answer:
        # Guardrail lớp 2: retrieval trả hit nhưng context không thực sự đủ trả lời cụ thể.
        no_match = _no_match_response("")
        no_match["source"] = template["source"]
        return no_match

    return {**template, "answer_html": answer}


def generate(query: str, hits: list[Hit], fallback_phone: str = "") -> dict:
    if not hits:
        return _no_match_response(fallback_phone)

    try:
        return _generate_llm(query, hits)
    except LlmError:
        return _generate_template(query, hits)


def _generate_template(query: str, hits: list[Hit], fallback_phone: str = "") -> dict:
    top = hits[0]

    if top.type == "procedure":
        p: Procedure = top.ref
        docs_html = "".join(f"<li>{d}</li>" for d in (p.documents or []))
        html = (
            f"Về thủ tục <b>{p.name}</b>: {p.description}<br/>"
            f"<b>Hồ sơ cần chuẩn bị:</b><ul>{docs_html}</ul>"
            f"<b>Lệ phí:</b> {p.fee} · <b>Thời gian:</b> {p.processing_time}<br/>"
            f"<b>Nơi nộp:</b> {p.place_of_submission}"
        )
        return {
            "answer_html": html,
            "source": f"Nguồn: Danh mục thủ tục xã Hòa Tiến · {p.legal_basis}",
            "matched": True,
            "matched_source_type": "procedure",
            "online_url": p.online_url,
            "matched_source_id": p.code,
        }

    if top.type == "faq":
        f: Faq = top.ref
        return {
            "answer_html": f.answer,
            "source": "Nguồn: Mục Hỏi đáp – xã Hòa Tiến",
            "matched": True,
            "matched_source_type": "faq",
            "matched_source_id": str(f.id),
        }

    if top.type == "contact":
        c: Contact = top.ref
        wh = c.working_hours or {}
        html = (
            f"<b>{c.office}</b><br/>📍 {c.address}<br/>☎️ {c.phone}<br/>"
            f"🕒 {wh.get('weekdays', '')}"
        )
        return {
            "answer_html": html,
            "source": "Nguồn: Thông tin liên hệ UBND xã Hòa Tiến",
            "matched": True,
            "matched_source_type": "contact",
            "matched_source_id": str(c.id),
        }

    if top.type == "article":
        a: KnowledgeArticle = top.ref
        return {
            "answer_html": f"<b>{a.title}</b><br/>{a.content}",
            "source": f"Nguồn: {a.source_citation}",
            "matched": True,
            "matched_source_type": "article",
            "matched_source_id": str(a.id),
        }

    # commune
    c: Contact = top.ref
    commune = c.commune_info or {}
    html = (
        f"{commune.get('note', '')} Diện tích khoảng <b>{commune.get('area_km2', '?')} km²</b>, "
        f"dân số khoảng <b>{commune.get('population', '?')}</b> người."
    )
    return {
        "answer_html": html,
        "source": "Nguồn: Thông tin chung xã Hòa Tiến",
        "matched": True,
        "matched_source_type": "commune",
        "matched_source_id": str(c.id),
    }
