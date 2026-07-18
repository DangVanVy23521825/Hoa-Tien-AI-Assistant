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
from app.models import Contact, Faq, Procedure  # noqa: E402

SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "seed-knowledge-base.json"


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
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                print(f"  ~ cập nhật FAQ: {f['question'][:40]}...")
            else:
                db.add(Faq(question=f["question"], **fields))
                print(f"  + thêm FAQ: {f['question'][:40]}...")

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
    finally:
        db.close()


if __name__ == "__main__":
    seed()
