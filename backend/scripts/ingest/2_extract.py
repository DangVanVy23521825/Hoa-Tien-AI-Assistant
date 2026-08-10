"""Bước 2: trang raw → bản ghi ứng viên đúng schema KB, bằng Gemini structured output.

    python3 scripts/ingest/2_extract.py               # chỉ xử lý trang chưa trích
    python3 scripts/ingest/2_extract.py --limit 3     # thử vài trang trước cho chắc
    python3 scripts/ingest/2_extract.py --force       # trích lại tất cả

Vai trò của Gemini ở đây là **cắt và xếp lại**, không phải viết nội dung: mỗi bản ghi
bắt buộc kèm `evidence_quote` trích nguyên văn từ trang. Không trích được ⇒ không có
bản ghi. Quyết định giữ/bỏ vẫn là của người duyệt ở bước 3.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import common  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

from app.core.config import settings  # noqa: E402

#: Cắt trang dài thành nhiều lần gọi. Đủ rộng để không xé đôi một bài viết thường.
MAX_CHARS_PER_CALL = 18_000

#: Bỏ qua trang quá ngắn sau khi lọc boilerplate — không còn nội dung thật.
MIN_CLEAN_LEN = 300

PROMPT = """\
Bạn đang xây dựng cơ sở tri thức cho trợ lý hành chính của UBND xã Hòa Tiến, thành phố \
Đà Nẵng (xã thành lập 01/7/2025 do nhập xã Hòa Tiến và xã Hòa Khương của huyện Hòa Vang cũ).

Từ NỘI DUNG TRANG dưới đây, hãy trích ra các bản ghi tri thức. Ba quy tắc BẮT BUỘC:

1. CHỈ TRÍCH, KHÔNG VIẾT THÊM. Mọi thông tin phải có trong trang. Mỗi bản ghi phải kèm \
`evidence_quote` là đoạn NGUYÊN VĂN copy từ trang làm căn cứ (30–300 ký tự). Không tìm \
được đoạn nguyên văn ⇒ KHÔNG tạo bản ghi đó. Tuyệt đối không suy đoán lệ phí, thời hạn, \
căn cứ pháp lý nếu trang không ghi.

2. CỔNG ĐỊA DANH. "Hòa Tiến" là tên trùng của nhiều xã ở tỉnh khác. Nếu trang không nói \
rõ về xã Hòa Tiến / Hòa Vang / thành phố Đà Nẵng, hãy trả về danh sách RỖNG.

3. BỎ QUA phần menu, sidebar, danh sách tin liên quan, thống kê truy cập, liên kết \
website. Chỉ lấy nội dung chính của trang.

Mỗi bản ghi chọn đúng một `kind`:

- `procedure` — thủ tục hành chính người dân làm tại xã. Điền: category (Hộ tịch / \
Chứng thực / Cư trú / Đất đai / Lao động - Xã hội / Y tế / Giáo dục / Kinh doanh / \
Xây dựng / Môi trường / Người có công), name, description, documents (giấy tờ cần nộp), \
fee, processing_time, place_of_submission, legal_basis. Trường nào trang không ghi thì \
để chuỗi rỗng — KHÔNG bịa.
- `faq` — một câu hỏi người dân hay hỏi + câu trả lời. Điền: question, answer.
- `article` — kiến thức về xã: lịch sử, di tích, danh thắng, làng nghề, thôn, ẩm thực, \
lễ hội, bộ máy/trụ sở/danh bạ, văn bản-chính sách. Điền: category — chọn ĐÚNG một trong: \
`history` (lịch sử, truyền thống), `landmark` (di tích, danh thắng), `craft_village` \
(làng nghề), `village` (thông tin thôn, địa giới, dân số), `cuisine` (ẩm thực, đặc sản), \
`festival` (lễ hội), `organization` (bộ máy, trụ sở, danh bạ, lịch tiếp dân), `legal` \
(văn bản, quy hoạch, chính sách) — rồi title, content (150–800 chữ, viết gọn từ trang).
  Lưu ý: địa chỉ trụ sở, danh bạ, lịch làm việc thuộc `organization`, KHÔNG phải `legal`.

Với mọi bản ghi: `keywords` là 5–8 cách người dân thật sẽ hỏi về nội dung đó, viết \
thường, có dấu, gồm cả khẩu ngữ và từ đồng nghĩa (ví dụ: "làm giấy cho con", \
"khai sinh cho bé", "đăng ký khai sinh").

Nếu trang chỉ là danh sách tin, trang đăng nhập, hoặc không có tri thức nào dùng được \
cho người dân — trả về danh sách RỖNG. Thà không có còn hơn có mà sai.

Dưới đây có thể có NHIỀU TRANG, mỗi trang bắt đầu bằng dòng `### TRANG <số>`. Với mỗi \
bản ghi, đặt `page_index` đúng bằng số của trang mà bạn lấy thông tin ra. Không được \
trộn thông tin của hai trang vào cùng một bản ghi.

{pages}
"""

PAGE_BLOCK = """\
### TRANG {index}
TIÊU ĐỀ: {title}
URL: {url}
NỘI DUNG:
{text}
"""


class Extracted(BaseModel):
    #: Số hiệu trang trong lần gọi gộp (1-based). Gọi 1 trang thì luôn là 1.
    page_index: int = 1
    kind: Literal["procedure", "faq", "article"]
    evidence_quote: str
    keywords: list[str] = Field(default_factory=list)
    # procedure
    category: str = ""
    name: str = ""
    description: str = ""
    documents: list[str] = Field(default_factory=list)
    fee: str = ""
    processing_time: str = ""
    place_of_submission: str = ""
    legal_basis: str = ""
    # faq
    question: str = ""
    answer: str = ""
    # article
    title: str = ""
    content: str = ""


_client: genai.Client | None = None


def _from_dotenv(name: str) -> str:
    """Đọc 1 biến từ backend/.env.

    `settings` nạp .env qua pydantic-settings chứ không đổ vào os.environ, mà thêm field
    ingest-only vào app config thì bẩn — nên script tự đọc lấy.
    """
    path = common.BACKEND_DIR / ".env"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def api_key() -> tuple[str, str]:
    """→ (key, tên biến đã dùng). Ưu tiên `INGEST_GEMINI_API_KEY`, fallback `GEMINI_API_KEY`.

    Nên đặt key riêng: free tier chỉ 20 request/ngày mỗi project, mà trợ lý production
    cũng gọi đúng model này. Dùng chung key là ingest ăn hết lượt hỏi của người dân và
    trợ lý âm thầm tụt xuống câu trả lời template cho tới hết ngày.
    """
    ingest = os.environ.get("INGEST_GEMINI_API_KEY") or _from_dotenv("INGEST_GEMINI_API_KEY")
    if ingest:
        return ingest, "INGEST_GEMINI_API_KEY"
    return settings.gemini_api_key, "GEMINI_API_KEY"


def client() -> genai.Client:
    global _client
    if _client is None:
        key, which = api_key()
        if not key:
            sys.exit(
                "Thiếu API key. Đặt INGEST_GEMINI_API_KEY (khuyến nghị — key riêng cho "
                "ingest) hoặc GEMINI_API_KEY trong backend/.env rồi chạy lại."
            )
        print(f"Dùng {which} (…{key[-6:]})")
        if which == "GEMINI_API_KEY":
            print("  ! Đang dùng chung key với trợ lý production — xem README mục hạn mức.")
        _client = genai.Client(api_key=key)
    return _client


def chunks(text: str, size: int = MAX_CHARS_PER_CALL) -> list[str]:
    """Cắt theo ranh giới dòng để không xé đôi câu."""
    if len(text) <= size:
        return [text]
    out, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > size and buf:
            out.append(buf)
            buf = ""
        buf += line + "\n"
    if buf.strip():
        out.append(buf)
    return out


def stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class QuotaExhausted(Exception):
    """Hết quota theo NGÀY — chạy tiếp cũng chỉ nhận thêm 429, phải dừng cả mẻ."""


#: Lỗi tạm thời đáng thử lại. 503 "high demand" và timeout gặp thật 11/08/2026: 4 mẻ
#: hỏng = 24 trang mất trắng chỉ vì trước đó chỉ retry mỗi 429.
_TRANSIENT = ("503", "UNAVAILABLE", "high demand", "timed out", "ReadTimeout", "500", "INTERNAL")


def _is_transient(message: str) -> bool:
    return any(marker.lower() in message.lower() for marker in _TRANSIENT)


def _retry_delay_s(error: Exception) -> float | None:
    match = re.search(r"'retryDelay': '(\d+(?:\.\d+)?)s'", str(error))
    return float(match.group(1)) if match else None


def _call(prompt: str, attempts: int = 4) -> list[Extracted]:
    """Gọi Gemini, tự lùi khi 429. Phân biệt quota theo phút (chờ được) và theo ngày (bó tay)."""
    for attempt in range(1, attempts + 1):
        try:
            response = client().models.generate_content(
                model=settings.gemini_generation_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=list[Extracted],
                    # 240s: mẻ 6 trang (~18k ký tự) sinh nhiều bản ghi, 120s đã timeout thật.
                    http_options=types.HttpOptions(timeout=240_000),
                ),
            )
            return response.parsed or []
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            rate_limited = "RESOURCE_EXHAUSTED" in message or "429" in message
            if rate_limited and "PerDay" in message:
                raise QuotaExhausted(message) from exc
            if not rate_limited and not _is_transient(message):
                raise
            if attempt == attempts:
                raise
            delay = _retry_delay_s(exc) or min(60.0, 5.0 * 2 ** (attempt - 1))
            reason = "429" if rate_limited else type(exc).__name__
            print(f"      {reason} — chờ {delay:.0f}s rồi thử lại ({attempt}/{attempts - 1})")
            time.sleep(delay + 1)
    return []


def extract_batch(pages: list[tuple[str, str, str]]) -> list[Extracted]:
    """pages = [(title, url, text)] → bản ghi, mỗi bản đã gắn `page_index` (1-based).

    Gộp nhiều trang vào một request là cách duy nhất chạy hết KB trong hạn mức free
    tier (20 request/ngày cho gemini-2.5-flash). Trang dài vẫn được cắt riêng.
    """
    if len(pages) == 1:
        title, url, text = pages[0]
        records: list[Extracted] = []
        for chunk in chunks(text):
            block = PAGE_BLOCK.format(index=1, title=title, url=url, text=chunk)
            for record in _call(PROMPT.format(pages=block)):
                record.page_index = 1
                records.append(record)
        return records

    blocks = [
        PAGE_BLOCK.format(index=i, title=t, url=u, text=x)
        for i, (t, u, x) in enumerate(pages, 1)
    ]
    records = _call(PROMPT.format(pages="\n".join(blocks)))
    # Model trả page_index ngoài khoảng → quy về trang 1 còn hơn mất bản ghi; người
    # duyệt vẫn thấy source_url nên phát hiện được nếu gán sai.
    for record in records:
        if not 1 <= record.page_index <= len(pages):
            record.page_index = 1
    return records


def batches(pages: list[dict], size: int, boiler_by_domain: dict[str, set[str]]):
    """Gom trang thành mẻ, cắt mẻ khi tổng độ dài vượt hạn mức một lần gọi."""
    batch: list[tuple[dict, str]] = []
    total = 0
    for page in pages:
        domain = page["url"].split("/")[2]
        text = common.clean_text(page["text"], boiler_by_domain[domain])
        if len(text) < MIN_CLEAN_LEN:
            yield [(page, text)]  # để vòng ngoài in lý do bỏ
            continue
        if batch and (len(batch) >= size or total + len(text) > MAX_CHARS_PER_CALL):
            yield batch
            batch, total = [], 0
        batch.append((page, text))
        total += len(text)
    if batch:
        yield batch


def primary_key(record: Extracted) -> str:
    return record.name or record.question or record.title or record.evidence_quote[:60]


def candidate_id(url: str, record: Extracted) -> str:
    raw = f"{url}|{record.kind}|{primary_key(record)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


#: Trang có `note` chứa các cụm này được trích trước — hết quota giữa chừng thì phần
#: giá trị nhất đã xong. Tin tức sự kiện để sau cùng vì ít dùng cho tra cứu hành chính.
PRIORITY_NOTES = ("Hỏi đáp", "Đất và người", "Di tích", "Cải cách hành chính", "Bộ máy", "Quy hoạch")


def priority(page: dict) -> int:
    note = page.get("note", "")
    return 0 if any(key in note for key in PRIORITY_NOTES) else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="chỉ xử lý N trang đầu")
    parser.add_argument("--force", action="store_true", help="trích lại cả trang đã trích")
    parser.add_argument(
        "--batch",
        type=int,
        default=6,
        help=(
            "số trang gộp vào một lần gọi API (mặc định 6 — đo trên 87 trang đã crawl: "
            "batch 1 tốn 82 lần gọi, batch 6 chỉ 17 lần nên lọt hạn mức 20/ngày của free "
            "tier; trên 6 không giảm thêm vì đã chạm MAX_CHARS_PER_CALL). Đặt 1 nếu có "
            "billing và muốn chất lượng cao nhất."
        ),
    )
    args = parser.parse_args()

    pages = common.load_raw_pages()
    if not pages:
        sys.exit("Chưa có trang nào trong data/ingest/raw — chạy 1_crawl.py trước.")

    # Boilerplate tính riêng theo domain: mỗi site có menu/footer khác nhau.
    by_domain: dict[str, list[dict]] = {}
    for page in pages:
        by_domain.setdefault(page["url"].split("/")[2], []).append(page)
    boiler_by_domain = {d: common.boilerplate_lines(ps) for d, ps in by_domain.items()}

    existing = common.read_json(common.CANDIDATES_PATH, default=[]) or []
    by_id = {c["id"]: c for c in existing}

    processed: dict = common.read_json(common.PROCESSED_PATH, default={}) or {}
    # Lần chạy trước chưa có processed.json → suy tạm từ candidates để không trích lại
    # những trang đã ra bản ghi. Trang ra 0 bản ghi vẫn sẽ chạy lại đúng một lần nữa.
    if not processed:
        processed = {c["source_url"]: {"records": -1, "at": "trước khi có processed.json"} for c in existing}

    todo = [p for p in pages if args.force or p["url"] not in processed]
    todo.sort(key=priority)
    if args.limit:
        todo = todo[: args.limit]
    print(
        f"{len(pages)} trang raw · {len(todo)} trang cần trích · "
        f"{len(existing)} ứng viên đã có · gộp {args.batch} trang/lần gọi\n"
    )

    new_count = calls = done = 0
    for batch in batches(todo, args.batch, boiler_by_domain):
        if len(batch) == 1 and len(batch[0][1]) < MIN_CLEAN_LEN:
            page, text = batch[0]
            done += 1
            # Ghi nhận đã xử lý: trang này sẽ không bao giờ có nội dung, đừng thử lại.
            processed[page["url"]] = {"records": 0, "at": stamp(), "note": "quá ngắn sau lọc"}
            print(f"[{done}/{len(todo)}] - bỏ (còn {len(text)} ký tự sau lọc): "
                  f"{(page['title'] or page['url'])[:56]}")
            continue

        try:
            records = extract_batch([(p["title"], p["url"], t) for p, t in batch])
            calls += 1
        except QuotaExhausted:
            print(
                f"\n{'!' * 74}\n"
                "HẾT QUOTA THEO NGÀY của Gemini free tier — dừng tại đây.\n"
                "Ứng viên đã trích được vẫn giữ nguyên; mai chạy lại lệnh này là đi tiếp\n"
                "(không có --force thì nó bỏ qua trang đã trích).\n"
                "Muốn chạy một mạch: bật billing cho GEMINI_API_KEY, hoặc tăng --batch,\n"
                "hoặc dùng key riêng cho ingest để không đụng quota của trợ lý production.\n"
                f"{'!' * 74}"
            )
            break
        except Exception as exc:  # noqa: BLE001 — 1 mẻ lỗi không được làm chết cả lượt chạy
            done += len(batch)
            print(f"[{done}/{len(todo)}] ! LỖI {type(exc).__name__}: {str(exc)[:100]}")
            continue

        added_per_page = [0] * len(batch)
        for record in records:
            page = batch[record.page_index - 1][0]
            cid = candidate_id(page["url"], record)
            if cid in by_id and not args.force:
                continue  # giữ nguyên quyết định duyệt cũ
            previous = by_id.get(cid, {})
            by_id[cid] = {
                "id": cid,
                # Trích lại không được xoá quyết định người đã duyệt.
                "status": previous.get("status", "pending"),
                "kind": record.kind,
                "source_url": page["url"],
                "source_title": page["title"],
                "evidence_quote": record.evidence_quote,
                "record": record.model_dump(exclude={"kind", "evidence_quote", "page_index"}),
            }
            added_per_page[record.page_index - 1] += 1

        for (page, _), added in zip(batch, added_per_page):
            done += 1
            new_count += added
            processed[page["url"]] = {"records": added, "at": stamp()}
            print(f"[{done}/{len(todo)}] + {added:2d} ứng viên  {(page['title'] or page['url'])[:56]}")

        # Lưu sau từng mẻ: hết quota hoặc lỗi giữa chừng vẫn giữ được phần đã làm.
        common.write_json(
            common.CANDIDATES_PATH, sorted(by_id.values(), key=lambda c: (c["kind"], c["id"]))
        )
        common.write_json(common.PROCESSED_PATH, processed)

    common.write_json(common.CANDIDATES_PATH, sorted(by_id.values(), key=lambda c: (c["kind"], c["id"])))
    common.write_json(common.PROCESSED_PATH, processed)
    remaining = len([p for p in pages if p["url"] not in processed])
    print(f"\nĐã dùng {calls} lần gọi API. Còn {remaining} trang chưa trích "
          f"(lỗi mạng/API — chạy lại lệnh này để thử tiếp).")
    print(
        f"\nXong. Thêm {new_count} ứng viên, tổng {len(by_id)}."
        f"\nFile: {common.CANDIDATES_PATH}"
        f"\nTiếp theo: python3 scripts/ingest/3_review.py"
    )


if __name__ == "__main__":
    main()
