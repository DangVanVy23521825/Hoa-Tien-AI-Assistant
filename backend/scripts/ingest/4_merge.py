"""Bước 4: gộp ứng viên đã duyệt vào seed-knowledge-base.json (cả 2 bản).

    python3 scripts/ingest/4_merge.py --dry-run   # xem sẽ thêm gì, không ghi file
    python3 scripts/ingest/4_merge.py

Ghi ra CẢ HAI bản seed (`data/` và `backend/data/`) — Railway deploy từ `backend/` nên
hai bản lệch nhau là production chạy dữ liệu cũ mà không ai biết.

Sau bước này BẮT BUỘC chạy `python3 scripts/eval_retrieval.py`: KB dày lên làm đổi phân
bố điểm, mà `SEMANTIC_FLOOR` / `SEMANTIC_GATE_MIN_COS` / `MIN_MATCH_SCORE` được hiệu
chỉnh trên KB 49 bản ghi.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

#: Tiền tố mã thủ tục theo nhóm. Giữ nguyên tiền tố đang dùng trong KB hiện tại.
PROCEDURE_PREFIX = {
    "Hộ tịch": "HT",
    "Chứng thực": "CT",
    "Cư trú": "CU",
    "Đất đai": "DD",
    "Lao động - Xã hội": "LD",
    "Y tế": "YT",
    "Giáo dục": "GD",
    "Kinh doanh": "KD",
    "Xây dựng": "XD",
    "Môi trường": "MT",
    "Người có công": "NC",
}

ARTICLE_PREFIX = {
    "history": "LS",
    "landmark": "DT",
    "craft_village": "LN",
    "village": "TH",
    "cuisine": "AT",
    "festival": "LH",
    "organization": "BM",
    "legal": "VB",
}

DEFAULT_ONLINE_URL = "https://dichvucong.gov.vn"
DEFAULT_PLACE = "Trung tâm Phục vụ hành chính công cấp xã Hòa Tiến"
#: Dùng cho trường bắt buộc mà trang nguồn không ghi. Nói thật là chưa biết, không bịa.
UNKNOWN = "Trang nguồn không nêu — vui lòng liên hệ Bộ phận Một cửa xã Hòa Tiến để biết chính xác"


def norm(text: str) -> str:
    """So khớp trùng lặp: bỏ dấu, hạ thường, gộp khoảng trắng."""
    stripped = "".join(
        ch for ch in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", stripped.replace("đ", "d")).strip()


def next_code(prefix: str, existing: list[str]) -> str:
    used = [
        int(m.group(1))
        for code in existing
        if (m := re.fullmatch(rf"{re.escape(prefix)}-(\d+)", code))
    ]
    return f"{prefix}-{max(used, default=0) + 1:02d}"


def source_citation(candidate: dict) -> str:
    title = (candidate.get("source_title") or "").strip()
    return f"{title} — {candidate['source_url']}" if title else candidate["source_url"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="chỉ in ra, không ghi file")
    args = parser.parse_args()

    candidates = common.read_json(common.CANDIDATES_PATH, default=[]) or []
    accepted = [c for c in candidates if c["status"] == "accepted"]
    if not accepted:
        sys.exit("Chưa có ứng viên nào ở trạng thái 'accepted' — chạy 3_review.py trước.")

    seed = common.read_json(common.SEED_PATHS[0])
    if seed is None:
        sys.exit(f"Không thấy {common.SEED_PATHS[0]}")

    codes = (
        [p["id"] for p in seed["procedures"]]
        + [f["id"] for f in seed["faq"]]
        + [a["id"] for a in seed["knowledge_articles"]]
    )
    seen_procedure = {norm(p["name"]) for p in seed["procedures"]}
    seen_faq = {norm(f["question"]) for f in seed["faq"]}
    seen_article = {norm(a["title"]) for a in seed["knowledge_articles"]}

    added = {"procedure": 0, "faq": 0, "article": 0}
    duplicates: list[str] = []
    skipped_empty: list[str] = []

    for candidate in accepted:
        record = candidate["record"]
        keywords = [k.strip().lower() for k in (record.get("keywords") or []) if k.strip()]

        if candidate["kind"] == "procedure":
            name = (record.get("name") or "").strip()
            if not name:
                skipped_empty.append(f"procedure không có tên ({candidate['id']})")
                continue
            if norm(name) in seen_procedure:
                duplicates.append(f"thủ tục đã có: {name}")
                continue
            category = record.get("category") or "Khác"
            code = next_code(PROCEDURE_PREFIX.get(category, "TT"), codes)
            seed["procedures"].append(
                {
                    "id": code,
                    "category": category,
                    "name": name,
                    "keywords": keywords,
                    "description": record.get("description") or UNKNOWN,
                    "documents": record.get("documents") or [],
                    "fee": record.get("fee") or UNKNOWN,
                    "processingTime": record.get("processing_time") or UNKNOWN,
                    "placeOfSubmission": record.get("place_of_submission") or DEFAULT_PLACE,
                    "onlineUrl": DEFAULT_ONLINE_URL,
                    "legalBasis": record.get("legal_basis") or source_citation(candidate),
                }
            )
            codes.append(code)
            seen_procedure.add(norm(name))
            added["procedure"] += 1

        elif candidate["kind"] == "faq":
            question = (record.get("question") or "").strip()
            answer = (record.get("answer") or "").strip()
            if not question or not answer:
                skipped_empty.append(f"faq thiếu câu hỏi/trả lời ({candidate['id']})")
                continue
            if norm(question) in seen_faq:
                duplicates.append(f"FAQ đã có: {question}")
                continue
            code = next_code("FAQ", codes)
            seed["faq"].append(
                {"id": code, "question": question, "keywords": keywords, "answer": answer}
            )
            codes.append(code)
            seen_faq.add(norm(question))
            added["faq"] += 1

        else:
            title = (record.get("title") or "").strip()
            content = (record.get("content") or "").strip()
            if not title or not content:
                skipped_empty.append(f"article thiếu tiêu đề/nội dung ({candidate['id']})")
                continue
            if norm(title) in seen_article:
                duplicates.append(f"bài viết đã có: {title}")
                continue
            category = record.get("category") or "history"
            code = next_code(ARTICLE_PREFIX.get(category, "BV"), codes)
            seed["knowledge_articles"].append(
                {
                    "id": code,
                    "category": category,
                    "title": title,
                    "keywords": keywords,
                    "content": content,
                    "source": source_citation(candidate),
                }
            )
            codes.append(code)
            seen_article.add(norm(title))
            added["article"] += 1

    total = sum(added.values())
    print(
        f"Thêm {total} bản ghi: {added['procedure']} thủ tục · {added['faq']} FAQ · "
        f"{added['article']} bài viết"
    )
    if duplicates:
        print(f"\nBỏ qua {len(duplicates)} bản trùng:")
        for line in duplicates[:15]:
            print(f"  - {line}")
    if skipped_empty:
        print(f"\nBỏ qua {len(skipped_empty)} bản thiếu trường bắt buộc:")
        for line in skipped_empty[:10]:
            print(f"  - {line}")

    print(
        f"\nKB sau khi gộp: {len(seed['procedures'])} thủ tục · {len(seed['faq'])} FAQ · "
        f"{len(seed['knowledge_articles'])} bài viết"
    )

    if args.dry_run:
        print("\n(--dry-run: KHÔNG ghi file)")
        return

    for path in common.SEED_PATHS:
        common.write_json(path, seed)
        print(f"  đã ghi {path}")

    print(
        "\n" + "!" * 74
        + "\nBẮT BUỘC trước khi seed production:"
        "\n  1. cd backend && python3 scripts/eval_retrieval.py"
        "\n     KB dày lên làm đổi phân bố điểm — ngưỡng cũ hiệu chỉnh trên 49 bản ghi."
        "\n     Eval đỏ thì sửa keywords/nội dung bản ghi TRƯỚC, đừng nới ngưỡng."
        "\n  2. Cập nhật KB nhúng trong frontend/legacy/index.html (bản dự phòng khi mất mạng)."
        "\n  3. python3 scripts/seed_from_json.py   (sinh embedding cho bản ghi mới)"
        + "\n" + "!" * 74
    )


if __name__ == "__main__":
    main()
