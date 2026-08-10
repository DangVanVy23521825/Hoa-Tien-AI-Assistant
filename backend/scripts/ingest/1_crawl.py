"""Bước 1: crawl các trang trong whitelist `sources.json` → data/ingest/raw/*.json

    python3 scripts/ingest/1_crawl.py            # dùng cache, chỉ tải trang chưa có
    python3 scripts/ingest/1_crawl.py --force    # tải lại tất cả
    python3 scripts/ingest/1_crawl.py --site "Wikipedia tiếng Việt"

Depth 2: seed → các link khớp `follow_pattern` trên chính seed đó. Không đi sâu hơn —
cổng thông tin có phân trang vô tận, đi sâu là crawl cả nghìn trang tin không dùng được.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

#: Trang ngắn hơn ngưỡng này gần như chắc chắn chỉ có menu, không có nội dung thật.
MIN_TEXT_LEN = 400


def _save(page: common.Page, note: str) -> None:
    common.write_json(
        common.RAW_DIR / f"{common.url_key(page.url)}.json",
        {
            "url": page.url,
            "title": page.title,
            "text": page.text,
            "fetched_at": page.fetched_at,
            "note": note,
        },
    )


def crawl_site(site: dict, force: bool) -> tuple[int, int]:
    domain = site["allow_domain"]
    pattern = re.compile(site["follow_pattern"]) if site.get("follow_pattern") else None
    max_follow = site.get("max_follow_per_seed", 0)

    queued: list[tuple[str, str]] = [(s["url"], s.get("note", "")) for s in site["seeds"]]
    seen: set[str] = set()
    saved = skipped = 0

    for url, note in queued:
        if url in seen:
            continue
        seen.add(url)

        cache_path = common.RAW_DIR / f"{common.url_key(url)}.json"
        if cache_path.exists() and not force:
            skipped += 1
            # Vẫn phải mở seed ra để lấy link con, nếu không lần chạy sau không đi tiếp được.
            is_seed = any(s["url"] == url for s in site["seeds"])
            if not (is_seed and pattern and max_follow):
                continue

        try:
            page = common.fetch(url)
        except Exception as exc:  # noqa: BLE001 — 1 trang hỏng không được làm chết cả mẻ
            print(f"  ! LỖI {type(exc).__name__}: {url}\n    {str(exc)[:120]}")
            continue

        if len(page.text) < MIN_TEXT_LEN:
            print(f"  - bỏ (chỉ {len(page.text)} ký tự, không có nội dung): {url}")
        elif not cache_path.exists() or force:
            _save(page, note)
            saved += 1
            print(f"  + {len(page.text):6d} ký tự  {page.title[:58]}")

        # Chỉ mở rộng từ seed, không mở rộng từ trang con → giữ đúng depth 2.
        if pattern and max_follow and any(s["url"] == url for s in site["seeds"]):
            children = [
                link
                for link in common.extract_links(page.html, url)
                if urlparse(link).netloc.endswith(domain)
                and pattern.search(link)
                and link not in seen
            ]
            for child in children[:max_follow]:
                queued.append((child, f"{note} → bài con"))

    return saved, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="tải lại cả trang đã có cache")
    parser.add_argument("--site", help="chỉ crawl 1 site theo tên trong sources.json")
    args = parser.parse_args()

    sources = common.read_json(common.SOURCES_PATH)
    if sources is None:
        sys.exit(f"Không thấy {common.SOURCES_PATH}")

    total_saved = total_skipped = 0
    for site in sources["sites"]:
        if args.site and site["name"] != args.site:
            continue
        print(f"\n=== {site['name']} ({site['allow_domain']}) ===")
        saved, skipped = crawl_site(site, args.force)
        total_saved += saved
        total_skipped += skipped

    print(
        f"\nXong. Lưu mới/cập nhật {total_saved} trang, bỏ qua {total_skipped} trang đã có cache."
        f"\nRaw: {common.RAW_DIR}"
        f"\nTiếp theo: python3 scripts/ingest/2_extract.py"
    )


if __name__ == "__main__":
    main()
