"""
Retrieval hybrid: keyword/fuzzy scoring (port trực tiếp từ legacy/index.html) +
semantic similarity qua embedding Gemini đã lưu sẵn (pgvector). Hai tín hiệu
cộng dồn vào cùng một score, giữ nguyên MIN_MATCH_SCORE làm ngưỡng matched/fallback
để không phá vỡ hành vi đã kiểm chứng (15/15 câu mẫu) khi chưa có embedding.
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Contact, Faq, KnowledgeArticle, Procedure
from app.services.embeddings import embed_text

SourceType = Literal["procedure", "faq", "contact", "commune", "article"]


@dataclass
class Hit:
    type: SourceType
    ref: Procedure | Faq | Contact
    score: float


def normalize(s: str | None) -> str:
    if not s:
        return ""
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


MIN_MATCH_SCORE = 4.0  # yêu cầu ít nhất 2 từ khớp độc lập (2×2) hoặc 1 cụm keyword khớp (+4)

# Cosine của gemini-embedding có "nền" ~0.5 giữa mọi cặp văn bản tiếng Việt kể cả
# hoàn toàn không liên quan (đo trên KB production 08/2026: câu rác đạt 0.48–0.625,
# đích đúng 0.66–0.82). Hai hằng số dưới tách phần nền đó ra khỏi score:
# - SEMANTIC_FLOOR: chỉ phần cosine vượt nền mới được cộng điểm (rescale về [0..weight])
# - SEMANTIC_GATE_MIN_COS: doc có embedding mà cosine dưới ngưỡng này thì bị loại hẳn,
#   dù keyword score cao (chặn token rác kiểu "thu"/"do"/"gia" cộng dồn 4đ+ cho câu
#   ngoài phạm vi).
#
# Trước đây doc khớp nguyên một cụm keyword được MIỄN cổng này. Đo lại 08/2026 trên
# toàn bộ KB (15 câu hỏi chuẩn + 12 câu khẩu ngữ): doc đúng luôn có cosine 0.737–0.821,
# tức không câu hợp lệ nào cần tới miễn cổng — trong khi miễn cổng chính là đường lọt
# của mọi false-positive đo được ("đặt vé máy bay online" khớp cụm "online" của FAQ-02
# ở cos 0.603; "vì sao ý kiến…" khớp cụm "sao y" của CT-01 ở cos 0.589; "giờ làm việc
# của ngân hàng Vietcombank" khớp cụm "giờ làm việc" của FAQ-01 ở cos 0.633). Vì vậy
# miễn cổng đã bị bỏ. Lưu ý cổng cosine KHÔNG tách được mọi câu rác: câu gần nghĩa thật
# như "nộp thuế thu nhập cá nhân online" vẫn đạt cos 0.708 với FAQ-02 và lọt qua —
# guardrail lớp 2 (refusal phrase của Gemini) mới là lưới cuối.
SEMANTIC_FLOOR = 0.60
SEMANTIC_GATE_MIN_COS = 0.65

# Từ phổ biến không mang tín hiệu phân biệt — lọc trước khi tính điểm để tránh
# khớp nhầm kiểu "làm" (trong "làm giấy cho con") hay "hộ" (trong "Hộ tịch")
# vô tình cộng dồn điểm cho câu hỏi hoàn toàn không liên quan.
STOPWORDS = {
    "lam", "co", "la", "can", "gi", "o", "dau", "cho", "duoc", "va", "cua",
    "de", "khi", "nao", "the", "nay", "day", "toi", "minh", "muon", "xin",
    "hay", "voi", "nhu", "neu", "thi", "mot", "nhung", "da", "se", "ve",
    "tai", "ra", "vao", "len", "xuong", "ho", "ai", "sao", "bao", "nhieu",
}


def _tokenize(query_norm: str) -> list[str]:
    return [t for t in query_norm.split(" ") if len(t) > 1 and t not in STOPWORDS]


def _score_doc(
    query_tokens: list[str], query_norm: str, text: str, keywords: list[str]
) -> float:
    """Điểm keyword của một tài liệu: khớp nguyên từ +2, khớp prefix +0.5,
    câu hỏi chứa nguyên một cụm keyword của tài liệu +4."""
    score = 0.0
    words = text.split()
    word_set = set(words)
    for t in query_tokens:
        if t in word_set:
            score += 2  # khớp nguyên từ
        else:
            for w in words:
                if w.startswith(t) and len(t) >= 3:  # prefix chỉ tính khi token đủ dài, tránh khớp rác
                    score += 0.5
                    break
    for k in keywords:
        if normalize(k) in query_norm:
            score += 4
    return score


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a), np.asarray(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def _cosine_or_none(
    query_embedding: list[float] | None, doc_embedding: list[float] | None
) -> float | None:
    """None nếu chưa có embedding câu hỏi hoặc tài liệu (chưa backfill) — an toàn,
    không lỗi, hành vi rơi về keyword-only như bản cũ khi thiếu dữ liệu embedding."""
    if query_embedding is None or doc_embedding is None:
        return None
    return _cosine_similarity(query_embedding, doc_embedding)


def _semantic_score(cos: float | None) -> float:
    """Chỉ cộng phần cosine vượt nền SEMANTIC_FLOOR, rescale về [0..weight] —
    tài liệu không liên quan (cos quanh nền) nhận 0 điểm thay vì ~0.5×weight."""
    if cos is None:
        return 0.0
    return max(0.0, cos - SEMANTIC_FLOOR) / (1.0 - SEMANTIC_FLOOR) * settings.rag_semantic_weight


def _passes_semantic_gate(cos: float | None) -> bool:
    """Cổng lớp 1: doc có embedding phải đạt cosine tối thiểu. Doc/câu hỏi chưa có
    embedding thì bỏ qua cổng (chế độ keyword-only cũ)."""
    if cos is None:
        return True
    return cos >= SEMANTIC_GATE_MIN_COS


@lru_cache(maxsize=256)
def embed_query(query: str) -> list[float] | None:
    """Embedding của câu hỏi, None nếu provider lỗi (retrieval rơi về keyword-only).

    Có cache để lớp xã giao ngữ nghĩa (services/smalltalk.py) dùng lại được vector
    này sau khi retrieval chạy xong mà không tốn thêm một lần gọi API.
    """
    try:
        return embed_text(query, "RETRIEVAL_QUERY")
    except Exception:
        return None


# Contact/commune không có cột `embedding` trong DB như procedure/faq/article: text của
# chúng được ghép tại query-time từ bảng contacts. Embed một lần rồi cache theo tiến
# trình (text gần như không đổi) để chúng đi qua đúng cổng cosine như mọi nguồn khác —
# trước đây 2 nguồn này bỏ qua cổng hoàn toàn, nên "giờ làm việc của ngân hàng
# Vietcombank ở đâu?" khớp contact chỉ nhờ token "gio" + "viec" (4.0 = MIN_MATCH_SCORE).
_static_doc_embeddings: dict[str, list[float] | None] = {}


def _embed_static_doc(text: str) -> list[float] | None:
    if text not in _static_doc_embeddings:
        try:
            _static_doc_embeddings[text] = embed_text(text, "RETRIEVAL_DOCUMENT")
        except Exception:
            _static_doc_embeddings[text] = None
    return _static_doc_embeddings[text]


def retrieve(db: Session, query: str, top_k: int = 3) -> list[Hit]:
    q_norm = normalize(query)
    q_tokens = _tokenize(q_norm)
    q_embedding = embed_query(query)

    hits: list[Hit] = []

    def add_hit(source_type: SourceType, ref, text: str, keywords: list[str], embedding) -> None:
        kw_score = _score_doc(q_tokens, q_norm, text, keywords)
        cos = _cosine_or_none(q_embedding, embedding)
        if not _passes_semantic_gate(cos):
            return
        score = kw_score + _semantic_score(cos)
        if score > 0:
            hits.append(Hit(type=source_type, ref=ref, score=score))

    for p in db.query(Procedure).all():
        text = normalize(" ".join([p.name, p.category, p.description, " ".join(p.keywords or [])]))
        add_hit("procedure", p, text, p.keywords or [], p.embedding)

    for f in db.query(Faq).all():
        text = normalize(" ".join([f.question, " ".join(f.keywords or []), f.answer]))
        add_hit("faq", f, text, f.keywords or [], f.embedding)

    for a in db.query(KnowledgeArticle).all():
        text = normalize(" ".join([a.title, " ".join(a.keywords or []), a.content]))
        add_hit("article", a, text, a.keywords or [], a.embedding)

    contact = db.query(Contact).first()
    if contact:
        contact_text = normalize(
            "lien he dia chi so dien thoai gio lam viec ubnd tru so " + contact.address
        )
        add_hit("contact", contact, contact_text, [], _embed_static_doc(contact_text))

        commune = contact.commune_info or {}
        commune_text = normalize(
            "xa hoa tien thong tin dan so dien tich sap nhap " + str(commune.get("note", ""))
        )
        add_hit("commune", contact, commune_text, [], _embed_static_doc(commune_text))

    hits.sort(key=lambda h: h.score, reverse=True)
    hits = [h for h in hits if h.score >= MIN_MATCH_SCORE]
    return hits[:top_k]
