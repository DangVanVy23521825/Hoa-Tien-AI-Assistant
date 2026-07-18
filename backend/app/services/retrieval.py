"""
Retrieval offline (keyword/fuzzy scoring) — port trực tiếp từ legacy/index.html.
Nguồn dữ liệu đổi từ JSON in-memory sang query PostgreSQL, thuật toán giữ nguyên.

Nâng cấp lên RAG thật: thay hàm retrieve() bằng vector similarity search
(bật pgvector trên cùng PostgreSQL này), giữ nguyên chữ ký hàm và Hit schema
để generation.py và router chat.py không phải đổi.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.models import Contact, Faq, Procedure

SourceType = Literal["procedure", "faq", "contact", "commune"]


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


def _score_doc(query_tokens: list[str], query_norm: str, text: str, keywords: list[str]) -> float:
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


def retrieve(db: Session, query: str, top_k: int = 3) -> list[Hit]:
    q_norm = normalize(query)
    q_tokens = _tokenize(q_norm)

    hits: list[Hit] = []

    for p in db.query(Procedure).all():
        text = normalize(" ".join([p.name, p.category, p.description, " ".join(p.keywords or [])]))
        score = _score_doc(q_tokens, q_norm, text, p.keywords or [])
        if score > 0:
            hits.append(Hit(type="procedure", ref=p, score=score))

    for f in db.query(Faq).all():
        text = normalize(" ".join([f.question, " ".join(f.keywords or []), f.answer]))
        score = _score_doc(q_tokens, q_norm, text, f.keywords or [])
        if score > 0:
            hits.append(Hit(type="faq", ref=f, score=score))

    contact = db.query(Contact).first()
    if contact:
        contact_text = normalize(
            "lien he dia chi so dien thoai gio lam viec ubnd tru so " + contact.address
        )
        score = _score_doc(q_tokens, q_norm, contact_text, [])
        if score > 0:
            hits.append(Hit(type="contact", ref=contact, score=score))

        commune = contact.commune_info or {}
        commune_text = normalize(
            "xa hoa tien thong tin dan so dien tich sap nhap " + str(commune.get("note", ""))
        )
        score = _score_doc(q_tokens, q_norm, commune_text, [])
        if score > 0:
            hits.append(Hit(type="commune", ref=contact, score=score))

    hits.sort(key=lambda h: h.score, reverse=True)
    hits = [h for h in hits if h.score >= MIN_MATCH_SCORE]
    return hits[:top_k]
