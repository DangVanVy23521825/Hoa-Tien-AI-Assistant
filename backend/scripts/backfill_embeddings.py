"""
Sinh embedding cho các bản ghi Procedure/Faq/KnowledgeArticle chưa có (hoặc --force
để embed lại toàn bộ). Chạy 1 lần sau khi apply migration thêm cột embedding,
và bất cứ khi nào cần re-embed lại toàn bộ KB (đổi model embedding chẳng hạn).

Chạy: python3 scripts/backfill_embeddings.py [--force]
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Faq, KnowledgeArticle, Procedure  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402


def _procedure_text(p: Procedure) -> str:
    return " ".join([p.name, p.category, p.description, " ".join(p.keywords or [])])


def _faq_text(f: Faq) -> str:
    return " ".join([f.question, " ".join(f.keywords or []), f.answer])


def _article_text(a: KnowledgeArticle) -> str:
    return " ".join([a.title, " ".join(a.keywords or []), a.content])


def backfill(force: bool = False):
    db = SessionLocal()
    count = 0
    try:
        for p in db.query(Procedure).all():
            if force or p.embedding is None:
                p.embedding = embed_text(_procedure_text(p), "RETRIEVAL_DOCUMENT")
                count += 1
                print(f"  + embed thủ tục {p.code}")

        for f in db.query(Faq).all():
            if force or f.embedding is None:
                f.embedding = embed_text(_faq_text(f), "RETRIEVAL_DOCUMENT")
                count += 1
                print(f"  + embed FAQ: {f.question[:40]}...")

        for a in db.query(KnowledgeArticle).all():
            if force or a.embedding is None:
                a.embedding = embed_text(_article_text(a), "RETRIEVAL_DOCUMENT")
                count += 1
                print(f"  + embed bài viết: {a.title[:40]}...")

        db.commit()
        print(f"Backfill hoàn tất — {count} bản ghi đã embed.")
    finally:
        db.close()


if __name__ == "__main__":
    backfill(force="--force" in sys.argv)
