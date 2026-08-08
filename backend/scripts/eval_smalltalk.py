"""Đo lớp nhận diện câu xã giao (app/services/smalltalk.py) — cả 2 tầng.

    cd backend && python3 scripts/eval_smalltalk.py

Ba nhóm phải phân biệt được:
  XAGIAO  — chào hỏi/cảm ơn/ừ… → phải nhận là xã giao (tầng 1 hoặc tầng 2)
  TRACUU  — câu hỏi thủ tục thật (kể cả có kèm lời chào) → tầng 1 PHẢI bỏ qua
  NGOAI   — câu hỏi thật nhưng ngoài phạm vi xã → cả 2 tầng phải bỏ qua, để rơi
            vào fallback "không có thông tin" như thiết kế

Không cần database. Có gọi API embedding cho nhóm cần tầng 2 (cache lại trong
.cache/eval_smalltalk.pkl). Exit code ≠ 0 khi có ca sai.
"""

import pickle
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import smalltalk as S  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402

CACHE_PATH = BACKEND / ".cache" / "eval_smalltalk.pkl"
_cache: dict = pickle.loads(CACHE_PATH.read_bytes()) if CACHE_PATH.exists() else {}


def _embed(text: str):
    if text not in _cache:
        _cache[text] = embed_text(text, "RETRIEVAL_QUERY")
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_bytes(pickle.dumps(_cache))
    return _cache[text]


XAGIAO = [
    # chào hỏi
    "helo", "hi", "hello", "hey", "alo", "chào", "xin chào", "chào bạn", "xin chào bạn",
    "Chào bạn nhé", "chào buổi sáng", "chàooo", "hế lô", "ơi", "có ai không",
    "có ai ở đó không", "a lô a lô", "dạ em chào", "kính chào", "chào cả nhà",
    "good morning", "ê",
    # hỏi về trợ lý
    "bạn là ai", "bạn làm được gì", "bạn giúp được gì", "giúp tôi với", "help",
    "bạn có phải người thật không", "bạn là người hay máy", "ai tạo ra bạn",
    "đây là chatbot đúng không", "bot à", "bạn khỏe không",
    # cảm ơn / khen
    "cảm ơn", "cảm ơn bạn", "cám ơn nhiều nhé", "thanks", "thank you", "tks",
    "tuyệt", "hay quá", "giỏi đấy",
    # tạm biệt
    "tạm biệt", "bye", "bai bai",
    # đáp ngắn
    "ok", "oke", "ừ", "vâng", "dạ", "được rồi", "rõ rồi", "hiểu rồi",
    # không có nội dung
    "?", "😀", "...",
]

TRACUU = [
    "chào bạn, tôi muốn làm khai sinh",
    "xin chào, cho hỏi thủ tục kết hôn",
    "hi, chứng thực bản sao mất bao nhiêu",
    "cảm ơn, nhưng sổ đỏ mất thì làm sao",
    "làm khai sinh cho con cần gì",
    "tách thửa đất thủ tục thế nào",
    "hộ nghèo xin giấy ở đâu",
    "chào mừng năm mới có nghỉ làm việc không",
    "giấy chào đời của con",
    "hiến máu nhân đạo ở đâu",
    "bãi bỏ thủ tục nào rồi",
    "UBND xã Hòa Tiến ở đâu",
]

NGOAI = [
    "giá vàng hôm nay bao nhiêu",
    "thời tiết Đà Nẵng ngày mai",
    "công thức nấu phở bò",
    "hướng dẫn cài Windows 11",
    "lãi suất ngân hàng nào cao nhất",
    "vé máy bay đi Hà Nội giá bao nhiêu",
    "cách giảm cân nhanh",
    "đội tuyển Việt Nam đá với ai",
    "số điện thoại tổng đài Viettel",
    "địa chỉ quán ăn ngon ở Đà Nẵng",
    "giấy phép lái xe hạng B2 thi ở đâu",
    "hộ chiếu làm ở đâu tại Đà Nẵng",
    "nộp thuế thu nhập cá nhân online",
]


def classify(q: str) -> tuple[str | None, str]:
    """(loại ý định, tầng nào bắt được)."""
    kind = S.detect(q)
    if kind:
        return kind, "cụm từ"
    kind = S.detect_semantic(_embed(q))
    return (kind, "ngữ nghĩa") if kind else (None, "-")


def main() -> int:
    bad = 0

    print("=== XÃ GIAO (phải nhận diện được) ===")
    for q in XAGIAO:
        kind, layer = classify(q)
        ok = kind is not None
        bad += not ok
        print(f"  [{'OK ' if ok else 'SAI'}] {q[:34]:36s} -> {str(kind):11s} ({layer})")

    print("\n=== CÂU TRA CỨU THẬT (tầng cụm từ phải bỏ qua) ===")
    for q in TRACUU:
        kind = S.detect(q)
        ok = kind is None
        bad += not ok
        print(f"  [{'OK ' if ok else 'SAI'}] {q[:34]:36s} -> {kind}")

    print("\n=== NGOÀI PHẠM VI (cả 2 tầng phải bỏ qua) ===")
    for q in NGOAI:
        kind, layer = classify(q)
        ok = kind is None
        bad += not ok
        print(f"  [{'OK ' if ok else 'SAI'}] {q[:34]:36s} -> {str(kind):11s} ({layer})")

    total = len(XAGIAO) + len(TRACUU) + len(NGOAI)
    print(f"\nKẾT QUẢ: đúng {total - bad}/{total}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
