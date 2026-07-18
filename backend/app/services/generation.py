"""
Generate câu trả lời từ ngữ cảnh đã retrieve.

Nâng cấp lên RAG thật: thay generate() bằng callLLM(query, context) gọi LLM API,
ép grounding vào context + yêu cầu citation. Giữ nguyên response shape
{answer_html, source, matched, matched_source_type} để frontend không đổi.
"""

from app.models import Contact, Faq, Procedure
from app.services.retrieval import Hit


def generate(query: str, hits: list[Hit], fallback_phone: str = "") -> dict:
    if not hits:
        phone_txt = f" qua số <b>{fallback_phone}</b>" if fallback_phone else ""
        return {
            "answer_html": (
                "Xin lỗi, tôi chưa có thông tin cho câu hỏi này trong dữ liệu của xã Hòa Tiến. "
                f"Bạn vui lòng liên hệ trực tiếp <b>Bộ phận Một cửa – UBND xã Hòa Tiến</b>{phone_txt} "
                "để được hỗ trợ chính xác nhất."
            ),
            "source": "Nguyên tắc: không tự tạo thông tin ngoài dữ liệu xã.",
            "matched": False,
            "matched_source_type": "none",
        }

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
