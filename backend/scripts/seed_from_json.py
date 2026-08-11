"""
Nạp data/seed-knowledge-base.json vào PostgreSQL. Idempotent: upsert theo code/question,
chạy lại nhiều lần không tạo trùng lặp.

Chạy: python3 scripts/seed_from_json.py
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Contact, Faq, KnowledgeArticle, Procedure  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "seed-knowledge-base.json"


#: Bản ghi seed được nhưng không có embedding — đếm để báo to ở cuối, xem `_report_failures`.
_embed_failures: list[str] = []


def _try_embed(text: str, label: str) -> list[float] | None:
    """Embedding cho một bản ghi. `wait_on_quota` vì hạn mức là 100 request/phút và
    KB đã hơn 200 bản ghi — không chờ thì quá nửa số bản ghi seed xong mà không có vector.
    """
    try:
        return embed_text(text, "RETRIEVAL_DOCUMENT", wait_on_quota=True)
    except Exception as exc:  # noqa: BLE001 — lỗi tạm thời không nên bỏ dở cả mẻ seed
        print(f"  ! lỗi embed, bỏ qua: {exc}")
        _embed_failures.append(label)
        return None


def _report_failures() -> None:
    """Bản ghi thiếu embedding vẫn tra được bằng keyword nên KHÔNG có lỗi nào hiện ra —
    trợ lý chỉ âm thầm kém đi ở đúng những bản ghi đó. Phải báo to, và thoát khác 0 để
    người chạy không tưởng là xong việc.
    """
    if not _embed_failures:
        return
    print(f"\n!!! {len(_embed_failures)} bản ghi đã seed NHƯNG KHÔNG CÓ EMBEDDING:")
    for label in _embed_failures:
        print(f"  - {label}")
    print("Chúng chỉ khớp được bằng keyword, không khớp ngữ nghĩa. "
          "Chạy lại script này để bù (idempotent) trước khi demo.")
    sys.exit(1)


def seed():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        # Procedures
        for p in data["procedures"]:
            existing = db.query(Procedure).filter(Procedure.code == p["id"]).first()
            fields = dict(
                category=p["category"],
                name=p["name"],
                keywords=p.get("keywords", []),
                description=p["description"],
                documents=p.get("documents", []),
                fee=p["fee"],
                processing_time=p["processingTime"],
                place_of_submission=p["placeOfSubmission"],
                online_url=p["onlineUrl"],
                legal_basis=p["legalBasis"],
            )
            embed_source = " ".join([fields["name"], fields["category"], fields["description"], " ".join(fields["keywords"])])
            embedding = _try_embed(embed_source, f"thủ tục {p['id']}")
            if embedding is not None:
                fields["embedding"] = embedding
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                print(f"  ~ cập nhật thủ tục {p['id']}")
            else:
                db.add(Procedure(code=p["id"], **fields))
                print(f"  + thêm thủ tục {p['id']}")

        # FAQ
        for f in data["faq"]:
            existing = db.query(Faq).filter(Faq.question == f["question"]).first()
            fields = dict(keywords=f.get("keywords", []), answer=f["answer"])
            embed_source = " ".join([f["question"], " ".join(fields["keywords"]), fields["answer"]])
            embedding = _try_embed(embed_source, f"FAQ {f['question'][:50]}")
            if embedding is not None:
                fields["embedding"] = embedding
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                print(f"  ~ cập nhật FAQ: {f['question'][:40]}...")
            else:
                db.add(Faq(question=f["question"], **fields))
                print(f"  + thêm FAQ: {f['question'][:40]}...")

        # Knowledge articles (lịch sử / địa danh / làng nghề)
        for a in data.get("knowledge_articles", []):
            existing = db.query(KnowledgeArticle).filter(KnowledgeArticle.title == a["title"]).first()
            fields = dict(
                category=a["category"],
                keywords=a.get("keywords", []),
                content=a["content"],
                source_citation=a["source"],
            )
            embed_source = " ".join([a["title"], " ".join(fields["keywords"]), fields["content"]])
            embedding = _try_embed(embed_source, f"bài viết {a['title'][:50]}")
            if embedding is not None:
                fields["embedding"] = embedding
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                print(f"  ~ cập nhật bài viết: {a['title'][:40]}...")
            else:
                db.add(KnowledgeArticle(title=a["title"], **fields))
                print(f"  + thêm bài viết: {a['title'][:40]}...")

        # Contact (single-row)
        contact = db.query(Contact).first()
        c = data["contact"]
        commune = data["commune"]
        fields = dict(
            office=c["office"],
            address=c["address"],
            phone=c["phone"],
            portal_url=c["portal"],
            public_service_url=c["publicServicePortal"],
            working_hours=c["workingHours"],
            commune_info=commune,
        )
        if contact:
            for k, v in fields.items():
                setattr(contact, k, v)
            print("  ~ cập nhật thông tin liên hệ")
        else:
            db.add(Contact(**fields))
            print("  + thêm thông tin liên hệ")

        db.commit()
        print("Seed hoàn tất.")
        _report_failures()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
