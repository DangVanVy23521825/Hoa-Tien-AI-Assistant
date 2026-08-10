"""Bước 3: duyệt tay từng ứng viên trước khi cho vào KB.

    python3 scripts/ingest/3_review.py                 # duyệt các bản còn "pending"
    python3 scripts/ingest/3_review.py --kind procedure
    python3 scripts/ingest/3_review.py --stats         # chỉ xem thống kê, không duyệt
    python3 scripts/ingest/3_review.py --reset         # đưa tất cả về pending

Phím: [y] nhận · [n] loại · [s] để lại sau · [e] sửa bằng $EDITOR · [q] thoát (đã lưu).

Người duyệt là lớp bảo vệ cuối trước khi dữ liệu tới tay người dân. Đọc `evidence_quote`
rồi mới quyết định — quote là đoạn nguyên văn trên trang nguồn, không phải câu Gemini viết.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

BOLD, DIM, GREEN, RED, YELLOW, CYAN, RESET = (
    "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m",
)


def show(candidate: dict, index: int, total: int) -> None:
    record = candidate["record"]
    headline = record.get("name") or record.get("question") or record.get("title") or "(không tên)"

    print("\n" + "=" * 78)
    print(f"{DIM}[{index}/{total}]{RESET}  {CYAN}{candidate['kind']}{RESET}  {BOLD}{headline}{RESET}")
    print(f"{DIM}nguồn: {candidate['source_url']}{RESET}")
    print("-" * 78)

    if candidate["kind"] == "procedure":
        print(f"  nhóm       : {record.get('category')}")
        print(f"  mô tả      : {record.get('description')}")
        for doc in record.get("documents") or []:
            print(f"  giấy tờ    : • {doc}")
        print(f"  lệ phí     : {record.get('fee') or DIM + '(trang không ghi)' + RESET}")
        print(f"  thời gian  : {record.get('processing_time') or DIM + '(trang không ghi)' + RESET}")
        print(f"  nơi nộp    : {record.get('place_of_submission') or DIM + '(trang không ghi)' + RESET}")
        print(f"  căn cứ     : {record.get('legal_basis') or DIM + '(trang không ghi)' + RESET}")
    elif candidate["kind"] == "faq":
        print(f"  trả lời    : {record.get('answer')}")
    else:
        print(f"  loại       : {record.get('category')}")
        print(f"  nội dung   : {record.get('content')}")

    print(f"  keywords   : {', '.join(record.get('keywords') or []) or RED + 'TRỐNG — nên sửa' + RESET}")
    print(f"\n{YELLOW}  TRÍCH NGUYÊN VĂN TỪ TRANG:{RESET}")
    print(f"{YELLOW}  “{candidate['evidence_quote']}”{RESET}")


def edit(candidate: dict) -> None:
    """Mở record trong $EDITOR. JSON hỏng thì giữ nguyên bản cũ."""
    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(candidate["record"], fh, ensure_ascii=False, indent=2)
        path = fh.name
    subprocess.call([editor, path])
    try:
        candidate["record"] = json.loads(Path(path).read_text(encoding="utf-8"))
        print(f"{GREEN}  đã cập nhật.{RESET}")
    except json.JSONDecodeError as exc:
        print(f"{RED}  JSON hỏng ({exc}) — giữ nguyên bản cũ.{RESET}")
    finally:
        os.unlink(path)


def stats(candidates: list[dict]) -> None:
    print(f"\nTổng {len(candidates)} ứng viên:")
    for status in ("pending", "accepted", "rejected"):
        rows = [c for c in candidates if c["status"] == status]
        by_kind = {k: sum(1 for c in rows if c["kind"] == k) for k in ("procedure", "faq", "article")}
        detail = " · ".join(f"{k} {v}" for k, v in by_kind.items() if v)
        print(f"  {status:9s} {len(rows):4d}   {DIM}{detail}{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["procedure", "faq", "article"])
    parser.add_argument("--stats", action="store_true", help="chỉ xem thống kê")
    parser.add_argument("--reset", action="store_true", help="đưa tất cả về pending")
    parser.add_argument("--all", action="store_true", help="duyệt lại cả bản đã quyết định")
    args = parser.parse_args()

    candidates = common.read_json(common.CANDIDATES_PATH, default=[]) or []
    if not candidates:
        sys.exit("Chưa có ứng viên nào — chạy 2_extract.py trước.")

    if args.reset:
        for candidate in candidates:
            candidate["status"] = "pending"
        common.write_json(common.CANDIDATES_PATH, candidates)
        print("Đã đưa tất cả về pending.")
        return

    if args.stats:
        stats(candidates)
        return

    queue = [
        c
        for c in candidates
        if (args.all or c["status"] == "pending") and (not args.kind or c["kind"] == args.kind)
    ]
    if not queue:
        print("Không còn gì để duyệt.")
        stats(candidates)
        return

    print(__doc__.split("Phím:")[1].split("\n")[0].strip())
    for index, candidate in enumerate(queue, 1):
        while True:
            show(candidate, index, len(queue))
            choice = input(f"\n  [y]nhận [n]loại [s]sau [e]sửa [q]thoát > ").strip().lower()
            if choice == "e":
                edit(candidate)
                continue
            if choice in ("y", "n", "s", "q", ""):
                break
            print(f"{RED}  phím không hợp lệ{RESET}")

        if choice == "q":
            break
        if choice == "y":
            candidate["status"] = "accepted"
            print(f"{GREEN}  → nhận{RESET}")
        elif choice == "n":
            candidate["status"] = "rejected"
            print(f"{RED}  → loại{RESET}")
        else:
            print(f"{DIM}  → để lại sau{RESET}")

        common.write_json(common.CANDIDATES_PATH, candidates)  # lưu sau từng bản, mất điện không mất công

    stats(candidates)
    print(f"\nTiếp theo: python3 scripts/ingest/4_merge.py")


if __name__ == "__main__":
    main()
