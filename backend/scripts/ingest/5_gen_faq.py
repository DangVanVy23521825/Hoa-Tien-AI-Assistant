"""Bước 5 (tuỳ chọn): sinh FAQ từ chính KB đã có, không cần nguồn web mới.

    python3 scripts/ingest/5_gen_faq.py --dry-run   # xem sẽ tốn bao nhiêu lượt API
    python3 scripts/ingest/5_gen_faq.py --limit 12  # thử trên vài bản ghi trước
    python3 scripts/ingest/5_gen_faq.py

Vì sao cần: retrieval là hybrid keyword + semantic, mà người dân hỏi bằng khẩu ngữ
("làm giấy cho con", "sổ đỏ sang tên") chứ không dùng tên thủ tục trong văn bản. Mỗi FAQ
là một cách hỏi khác được neo vào đúng dữ liệu đã có, nên tăng tỉ lệ khớp mà **không thêm
một sự thật mới nào** — đây là điểm khác căn bản so với crawl: nguồn ở đây là KB đã duyệt,
không phải trang web lạ.

Ứng viên sinh ra đi vào cùng `candidates.json`, duyệt bằng `3_review.py` và gộp bằng
`4_merge.py` như mọi ứng viên khác.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import common  # noqa: E402
from google.genai import types  # noqa: E402

# Dùng lại client, cơ chế chọn key và settings của bước 2 — không nhân bản logic.
# Phải nạp bằng importlib vì tên file bắt đầu bằng số nên không import thẳng được.
_spec = importlib.util.spec_from_file_location(
    "_ex", Path(__file__).resolve().parent / "2_extract.py"
)
_ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ex)

#: Số bản ghi KB gộp vào một lần gọi. Bản ghi ngắn hơn trang web nhiều nên gộp được rộng.
RECORDS_PER_CALL = 6

#: Số FAQ sinh ra cho mỗi bản ghi. Nhiều hơn nữa thì bắt đầu lặp ý.
FAQ_PER_RECORD = 3

PROMPT = """\
Bạn đang bổ sung câu hỏi thường gặp cho trợ lý hành chính của UBND xã Hòa Tiến, TP Đà Nẵng.

Dưới đây là các BẢN GHI đã được kiểm chứng trong cơ sở dữ liệu của xã. Với MỖI bản ghi, \
hãy viết {n} câu hỏi–trả lời theo đúng cách người dân thật sẽ hỏi.

QUY TẮC BẮT BUỘC:

1. **Câu trả lời chỉ được dùng thông tin có trong chính bản ghi đó.** Không thêm lệ phí, \
thời hạn, giấy tờ, căn cứ pháp lý nào không có sẵn. Không suy diễn, không "thường thì...". \
Nếu bản ghi không đủ để trả lời một câu hỏi hay, hãy bỏ câu hỏi đó đi.

2. **Câu hỏi phải là khẩu ngữ**, đúng giọng người dân mọi lứa tuổi ở nông thôn — không \
dùng lại nguyên văn tên thủ tục trong văn bản. Ví dụ tốt: "Làm giấy khai sinh cho con cần \
mang gì?", "Sổ đỏ muốn sang tên cho con thì làm sao?", "Chứng thực giấy tờ hết bao nhiêu tiền?". \
Ví dụ xấu (lặp văn bản): "Thủ tục đăng ký khai sinh là gì?".

3. **{n} câu hỏi của cùng một bản ghi phải hỏi về {n} khía cạnh KHÁC NHAU** (giấy tờ cần \
mang / lệ phí / thời gian / nơi nộp / trường hợp đặc biệt) — không diễn đạt lại cùng một ý.

4. `evidence_quote`: trích NGUYÊN VĂN đoạn trong bản ghi làm căn cứ cho câu trả lời.

5. `keywords`: 5–8 cách hỏi khác nữa cho cùng nội dung, viết thường, có dấu.

6. Đặt `record_index` đúng bằng số của bản ghi mà câu hỏi thuộc về.

KHÔNG được trùng ý với các câu hỏi đã có sau đây:
{existing}

--- CÁC BẢN GHI ---
{records}
"""


class GeneratedFaq(BaseModel):
    record_index: int = 1
    question: str
    answer: str
    evidence_quote: str
    keywords: list[str] = Field(default_factory=list)


def flatten(seed: dict) -> list[dict]:
    """KB → danh sách bản ghi phẳng để sinh FAQ. Bỏ qua contact (đã có FAQ riêng)."""
    rows: list[dict] = []
    for p in seed["procedures"]:
        body = (
            f"Thủ tục: {p['name']} (nhóm {p['category']})\n"
            f"Mô tả: {p['description']}\n"
            f"Hồ sơ cần chuẩn bị: {'; '.join(p.get('documents') or []) or 'không nêu'}\n"
            f"Lệ phí: {p['fee']}\nThời gian giải quyết: {p['processingTime']}\n"
            f"Nơi nộp: {p['placeOfSubmission']}\nCăn cứ pháp lý: {p['legalBasis']}"
        )
        rows.append({"id": p["id"], "label": p["name"], "body": body})
    for a in seed["knowledge_articles"]:
        rows.append(
            {
                "id": a["id"],
                "label": a["title"],
                "body": f"Bài viết: {a['title']} (loại {a['category']})\nNội dung: {a['content']}",
            }
        )
    return rows


def chunk(rows: list[dict], size: int) -> list[list[dict]]:
    return [rows[i : i + size] for i in range(0, len(rows), size)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="chỉ ước lượng số lượt API")
    parser.add_argument("--limit", type=int, help="chỉ xử lý N bản ghi đầu")
    parser.add_argument("--per-record", type=int, default=FAQ_PER_RECORD)
    parser.add_argument("--force", action="store_true", help="sinh lại cho cả bản ghi đã sinh")
    args = parser.parse_args()

    seed = common.read_json(common.SEED_PATHS[0])
    if seed is None:
        sys.exit(f"Không thấy {common.SEED_PATHS[0]}")

    candidates = common.read_json(common.CANDIDATES_PATH, default=[]) or []
    by_id = {c["id"]: c for c in candidates}
    already = {c["source_url"] for c in candidates if c["source_url"].startswith("kb://")}

    rows = flatten(seed)
    if not args.force:
        rows = [r for r in rows if f"kb://{r['id']}" not in already]
    if args.limit:
        rows = rows[: args.limit]

    groups = chunk(rows, RECORDS_PER_CALL)
    print(
        f"{len(rows)} bản ghi cần sinh FAQ · {len(groups)} lượt gọi API · "
        f"{args.per_record} FAQ/bản ghi → tối đa {len(rows) * args.per_record} ứng viên"
    )
    if args.dry_run:
        print("(--dry-run: không gọi API)")
        return
    if not rows:
        print("Không còn bản ghi nào cần sinh FAQ.")
        return

    existing_questions = "\n".join(f"- {f['question']}" for f in seed["faq"])
    new_count = 0

    for index, group in enumerate(groups, 1):
        blocks = "\n\n".join(
            f"### BẢN GHI {i}\n{r['body']}" for i, r in enumerate(group, 1)
        )
        prompt = PROMPT.format(n=args.per_record, existing=existing_questions, records=blocks)

        try:
            response = _ex.client().models.generate_content(
                model=_ex.settings.gemini_generation_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,  # cao hơn bước trích: cần đa dạng cách hỏi
                    response_mime_type="application/json",
                    response_schema=list[GeneratedFaq],
                    http_options=types.HttpOptions(timeout=240_000),
                ),
            )
            faqs = response.parsed or []
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            if "PerDay" in message:
                print("\nHết quota theo ngày — dừng. Ứng viên đã sinh vẫn giữ nguyên.")
                break
            print(f"[{index}/{len(groups)}] ! LỖI {type(exc).__name__}: {message[:100]}")
            continue

        added = 0
        for faq in faqs:
            if not 1 <= faq.record_index <= len(group):
                continue
            row = group[faq.record_index - 1]
            cid = hashlib.sha1(f"kb://{row['id']}|faq|{faq.question}".encode()).hexdigest()[:16]
            if cid in by_id and not args.force:
                continue
            by_id[cid] = {
                "id": cid,
                "status": by_id.get(cid, {}).get("status", "pending"),
                "kind": "faq",
                "source_url": f"kb://{row['id']}",
                "source_title": row["label"],
                "evidence_quote": faq.evidence_quote,
                "record": {
                    "question": faq.question,
                    "answer": faq.answer,
                    "keywords": [k.strip().lower() for k in faq.keywords if k.strip()],
                },
            }
            added += 1

        new_count += added
        print(f"[{index}/{len(groups)}] + {added:2d} FAQ  ({', '.join(r['id'] for r in group)})")
        common.write_json(
            common.CANDIDATES_PATH, sorted(by_id.values(), key=lambda c: (c["kind"], c["id"]))
        )

    print(
        f"\nXong. Thêm {new_count} ứng viên FAQ, tổng {len(by_id)}."
        f"\nDuyệt: python3 scripts/ingest/3_review.py --kind faq"
    )


if __name__ == "__main__":
    main()
