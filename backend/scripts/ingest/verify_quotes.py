"""Kiểm máy: `evidence_quote` của mọi ứng viên có thật sự là nguyên văn từ nguồn không.

    python3 scripts/ingest/verify_quotes.py            # kiểm tất cả
    python3 scripts/ingest/verify_quotes.py --only pending
    python3 scripts/ingest/verify_quotes.py --reject   # đánh 'rejected' cho bản không khớp

Đây là cổng chống bịa **tự động**, chạy trước khi người ngồi duyệt: quote không tìm thấy
trong nguồn nghĩa là model đã viết ra chứ không trích ra, và bản ghi đó không đáng tin dù
đọc nghe rất hợp lý. Người duyệt không thể tự nhớ 87 trang nguồn, máy thì tra được.

Nguồn đối chiếu:
- `kb://<id>`  → bản ghi trong seed-knowledge-base.json (bước 5_gen_faq)
- `http(s)://` → text trang đã crawl trong data/ingest/raw (bước 2_extract)
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

#: Nhãn trường mà prompt hay kèm vào đầu quote — không tính là bịa.
_FIELD_LABEL = re.compile(
    r"^(hồ sơ cần chuẩn bị|lệ phí|thời gian giải quyết|thời gian|nơi nộp|mô tả|"
    r"căn cứ pháp lý|thủ tục|bài viết|nội dung)\s*:\s*",
    re.I,
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).lower()).strip()


def squash(text: str) -> str:
    """Bỏ sạch khoảng trắng VÀ dấu câu, chỉ giữ chữ và số.

    Hai lý do, đều gặp thật:
    - Model bỏ ký tự xuống dòng khi trích: "đơn vịa)" trong khi trang gốc là "đơn vị\\na)".
    - Chỗ nối giữa hai đoạn ghép thường sinh thêm dấu chấm không có trong nguồn, làm
      thuật toán phủ tham lam kẹt ở đúng một ký tự.
    Cả hai đều là khác biệt trình bày. Sai khác CHỮ (ví dụ "MẶN TRẬN" ở quote trong khi
    nguồn là "MẶT TRẬN") vẫn bị bắt, vì chữ cái được giữ nguyên.
    """
    normalized = unicodedata.normalize("NFC", text).lower()
    return "".join(ch for ch in normalized if ch.isalnum())


#: Mảnh ngắn hơn ngưỡng này không đủ đặc trưng — khớp được cũng có thể chỉ là trùng ngẫu nhiên.
_MIN_PIECE = 24

#: Ghép quá nhiều mảnh thì không còn là "trích" nữa, coi như tự viết.
_MAX_PIECES = 6


def classify(quote: str, source: str) -> str:
    """→ 'verbatim' | 'stitched' | 'missing'.

    Phủ tham lam: liên tục lấy đoạn dài nhất còn lại của quote mà tìm được trong nguồn.
    Tách mảnh bằng regex (dấu chấm, xuống dòng…) không đủ tin: model ghép hai mục cách
    xa nhau ngay giữa câu, chỗ nối không có dấu câu nào để mà tách.

    - phủ hết bằng 1 mảnh  → verbatim
    - phủ hết bằng ≤6 mảnh → stitched (có căn cứ, nhưng trích không liền)
    - có chỗ không phủ nổi → missing (model tự viết hoặc gõ sai chữ trong nguồn)
    """
    q, src = squash(quote), squash(source)
    if not q:
        return "missing"
    if q in src:
        return "verbatim"

    position = pieces = 0
    while position < len(q):
        low, high = 0, len(q) - position
        while low < high:  # nhị phân: tiền tố dài nhất từ `position` còn nằm trong nguồn
            mid = (low + high + 1) // 2
            if q[position : position + mid] in src:
                low = mid
            else:
                high = mid - 1
        if low < _MIN_PIECE:
            return "missing"
        position += low
        pieces += 1
        if pieces > _MAX_PIECES:
            return "missing"
    return "stitched"


def kb_bodies() -> dict[str, str]:
    """Nguồn đối chiếu cho `kb://<id>` — đúng chuỗi mà bước sinh đưa cho model xem.

    Phải là `common.kb_rows`, không phải một bản ghép field tự chế: quote hợp lệ hay
    kèm nhãn trường ("Lệ phí: …; Nơi nộp: …") vì model đọc được nhãn trong nguồn.
    """
    seed = common.read_json(common.SEED_PATHS[0]) or {}
    bodies: dict[str, str] = {row["id"]: norm(row["body"]) for row in common.kb_rows(seed)}
    for f in seed.get("faq", []):
        bodies[f["id"]] = norm(f"{f['question']} {f['answer']}")
    return bodies


def page_texts() -> dict[str, str]:
    return {p["url"]: norm(p["text"]) for p in common.load_raw_pages()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["pending", "accepted", "rejected"])
    parser.add_argument("--reject", action="store_true", help="đánh rejected cho bản không khớp")
    args = parser.parse_args()

    candidates = common.read_json(common.CANDIDATES_PATH, default=[]) or []
    if not candidates:
        sys.exit("Chưa có ứng viên nào.")

    bodies, pages = kb_bodies(), page_texts()
    rows = [c for c in candidates if not args.only or c["status"] == args.only]

    counts = {"verbatim": 0, "stitched": 0, "missing": 0}
    missing_source = 0
    flagged: dict[str, list[dict]] = {"stitched": [], "missing": []}

    for candidate in rows:
        url = candidate["source_url"]
        source = bodies.get(url[5:], None) if url.startswith("kb://") else pages.get(url)
        if source is None:
            missing_source += 1
            continue

        quote = _FIELD_LABEL.sub("", candidate["evidence_quote"]).strip().rstrip(".")
        verdict = classify(quote, source)
        counts[verdict] += 1
        if verdict != "verbatim":
            flagged[verdict].append(candidate)

    for verdict, label in (("missing", "KHÔNG TÌM THẤY TRONG NGUỒN"), ("stitched", "ghép từ nhiều đoạn rời")):
        for candidate in flagged[verdict][:15]:
            record = candidate["record"]
            headline = record.get("name") or record.get("question") or record.get("title") or "?"
            print(f"[{label}] {candidate['kind']} · {headline[:58]}")
            print(f"   nguồn: {candidate['source_url'][:88]}")
            print(f"   quote: {candidate['evidence_quote'][:110]}\n")

    print(
        f"Đã kiểm {len(rows)} ứng viên: {counts['verbatim']} nguyên văn · "
        f"{counts['stitched']} ghép đoạn (có căn cứ, trích không liền) · "
        f"{counts['missing']} KHÔNG có căn cứ"
        + (f" · {missing_source} không đối chiếu được" if missing_source else "")
    )

    if args.reject and flagged["missing"]:
        ids = {c["id"] for c in flagged["missing"]}
        for candidate in candidates:
            if candidate["id"] in ids:
                candidate["status"] = "rejected"
        common.write_json(common.CANDIDATES_PATH, candidates)
        print(f"Đã đánh 'rejected' cho {len(ids)} ứng viên không có căn cứ.")
    elif flagged["missing"]:
        print("Chạy lại với --reject để loại thẳng nhóm KHÔNG có căn cứ.")

    # Chỉ nhóm 'missing' mới là lỗi thật; 'stitched' để người duyệt tự quyết.
    sys.exit(1 if counts["missing"] else 0)


if __name__ == "__main__":
    main()
