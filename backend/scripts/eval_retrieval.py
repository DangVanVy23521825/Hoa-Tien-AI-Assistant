"""Đo chất lượng retrieval: câu hợp lệ phải khớp đúng nguồn, câu ngoài phạm vi phải fallback.

Chạy trên `data/seed-knowledge-base.json` với embedding thật của provider đang cấu hình,
KHÔNG cần database — dùng đúng các hàm chấm điểm trong app/services/retrieval.py nên
phản ánh trung thực hành vi production (miễn là DB đã được seed từ cùng file JSON).

    cd backend && python3 scripts/eval_retrieval.py

Embedding được cache ra .cache/eval_embeddings.pkl để chạy lại không tốn API. Sau khi
đổi ngưỡng (SEMANTIC_FLOOR / SEMANTIC_GATE_MIN_COS), đổi provider embedding, hay sửa
keywords trong seed → chạy lại script này trước khi deploy.

`--verbose` in điểm keyword / cosine / kết quả cổng của từng tài liệu cho mỗi câu hỏi.
"""

import json
import os
import pickle
import sys
from pathlib import Path
from types import SimpleNamespace

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import retrieval as R  # noqa: E402
from app.services.embeddings import embed_text  # noqa: E402

SEED_PATH = BACKEND / "data" / "seed-knowledge-base.json"
CACHE_PATH = BACKEND / ".cache" / "eval_embeddings.pkl"

SEED = json.loads(SEED_PATH.read_text(encoding="utf-8"))
_cache: dict = pickle.loads(CACHE_PATH.read_bytes()) if CACHE_PATH.exists() else {}


def emb(text: str, task: str) -> list[float]:
    key = (task, text)
    if key not in _cache:
        _cache[key] = embed_text(text, task)
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_bytes(pickle.dumps(_cache))
    return _cache[key]


def _build_docs():
    """Text của từng doc phải khớp scripts/backfill_embeddings.py, nếu không cosine đo
    ở đây sẽ lệch với embedding thật đang nằm trong DB."""
    docs = []
    for p in SEED["procedures"]:
        text = " ".join([p["name"], p["category"], p["description"], " ".join(p.get("keywords") or [])])
        docs.append(("procedure", SimpleNamespace(**p), text, p.get("keywords") or []))
    for f in SEED["faq"]:
        text = " ".join([f["question"], " ".join(f.get("keywords") or []), f["answer"]])
        docs.append(("faq", SimpleNamespace(**f), text, f.get("keywords") or []))
    for a in SEED.get("knowledge_articles", []):
        text = " ".join([a["title"], " ".join(a.get("keywords") or []), a["content"]])
        docs.append(("article", SimpleNamespace(**a), text, a.get("keywords") or []))
    return docs


DOCS = _build_docs()
CONTACT = SEED["contact"]
COMMUNE = SEED["commune"]


def label(kind: str, o) -> str:
    if kind == "procedure":
        return f"{o.id} {o.name[:38]}"
    if kind == "faq":
        return f"FAQ {o.id} {o.question[:34]}"
    if kind == "article":
        return f"ART {o.title[:38]}"
    return kind.upper()


def retrieve(query: str, top_k: int = 3, verbose: bool = False):
    q_norm = R.normalize(query)
    q_tokens = R._tokenize(q_norm)
    q_emb = emb(query, "RETRIEVAL_QUERY")

    hits = []

    def consider(kind, ref, text, keywords):
        kw = R._score_doc(q_tokens, q_norm, R.normalize(text), keywords)
        cos = R._cosine_similarity(q_emb, emb(text, "RETRIEVAL_DOCUMENT"))
        passed = R._passes_semantic_gate(cos)
        if verbose and (kw > 0 or cos >= R.SEMANTIC_GATE_MIN_COS):
            name = label(kind, ref) if ref else kind.upper()
            print(f"      {name:46s} kw={kw:5.1f} cos={cos:.3f} {'ok' if passed else 'BLOCK'}")
        if not passed:
            return
        score = kw + R._semantic_score(cos)
        if score > 0:
            hits.append((kind, ref, score))

    for kind, ref, text, keywords in DOCS:
        consider(kind, ref, text, keywords)

    # contact/commune: text ghép tại query-time, không có cột embedding trong DB
    consider(
        "contact",
        None,
        R.normalize("lien he dia chi so dien thoai gio lam viec ubnd tru so " + CONTACT["address"]),
        [],
    )
    consider(
        "commune",
        None,
        R.normalize("xa hoa tien thong tin dan so dien tich sap nhap " + str(COMMUNE.get("note", ""))),
        [],
    )

    hits.sort(key=lambda h: h[2], reverse=True)
    return [h for h in hits if h[2] >= R.MIN_MATCH_SCORE][:top_k]


# (câu hỏi, các nhãn chấp nhận được — khớp chuỗi con, ngăn bằng "|")
VALID = [
    ("Làm khai sinh cho con cần giấy tờ gì?", "KS-01"),
    ("Đăng ký kết hôn cần chuẩn bị hồ sơ gì?", "KT-01"),
    ("Chứng thực bản sao từ bản chính mất bao nhiêu tiền?", "CT-01"),
    ("Tôi muốn chứng thực chữ ký thì làm ở đâu?", "CT-02"),
    ("Xác nhận tình trạng hôn nhân làm thế nào?", "XN-01"),
    ("Thủ tục khai tử cần những gì?", "TT-01"),
    ("Khai báo tạm vắng khi nào phải làm?", "CU-04|FAQ-17"),
    ("Đăng ký thường trú cần hồ sơ gì?", "CU-01|CU-02"),
    ("Tách hộ khẩu thủ tục ra sao?", "CU-03"),
    ("Chuyển nhượng quyền sử dụng đất cần làm gì?", "DD-01|DD-03|FAQ-11"),
    ("Sổ đỏ bị mất thì xin cấp lại thế nào?", "DD-02|FAQ-10"),
    ("Tách thửa đất thủ tục thế nào?", "DD-04"),
    ("Bộ phận một cửa làm việc mấy giờ?", "FAQ-01|CONTACT"),
    ("Xin giấy xác nhận hộ nghèo ở đâu?", "FAQ-08"),
    ("Xã Hòa Tiến có bao nhiêu thôn?", "FAQ|COMMUNE|ART"),
    # contact/commune — 2 nguồn từng không đi qua cổng cosine
    ("UBND xã Hòa Tiến ở đâu, số điện thoại bao nhiêu?", "CONTACT"),
    ("Trụ sở ủy ban xã địa chỉ nào?", "CONTACT"),
    ("Xã Hòa Tiến rộng bao nhiêu, dân số bao nhiêu?", "COMMUNE|FAQ|ART"),
]

JUNK = [
    "giá vàng hôm nay bao nhiêu",
    "thời tiết Đà Nẵng ngày mai thế nào",
    "cho tôi công thức nấu phở bò",
    "đội tuyển Việt Nam đá với ai tối nay",
    "hướng dẫn cài Windows 11",
    "vé máy bay đi Hà Nội giá bao nhiêu",
    "lãi suất gửi tiết kiệm ngân hàng nào cao nhất",
    "cách giảm cân nhanh trong 1 tuần",
    # câu rác nhưng vô tình trùng token/cụm keyword của KB — lớp dễ lọt nhất
    "địa chỉ quán ăn ngon ở Đà Nẵng",
    "số điện thoại tổng đài Viettel",
    "dân số Việt Nam hiện nay bao nhiêu",
    "giờ làm việc của ngân hàng Vietcombank ở đâu?",
    "đặt vé máy bay online",
    "vì sao ý kiến của tôi không được ghi nhận",
]


def _top_label(query, verbose):
    h = retrieve(query, verbose=verbose)
    if not h:
        return "FALLBACK", 0.0
    kind, ref, score = h[0]
    return (label(kind, ref) if ref else kind.upper()), score


def main(verbose: bool = False) -> int:
    ok_valid = 0
    print("=== CÂU HỢP LỆ (phải khớp đúng nguồn) ===")
    for q, expect in VALID:
        if verbose:
            print(f"  Q: {q}")
        got, score = _top_label(q, verbose)
        good = any(e.lower() in got.lower() for e in expect.split("|"))
        ok_valid += good
        print(f"  [{'OK ' if good else 'SAI'}] {q[:44]:46s} -> {got[:44]:46s} {score:5.2f}")

    ok_junk = 0
    print("\n=== CÂU NGOÀI PHẠM VI (phải fallback) ===")
    for q in JUNK:
        if verbose:
            print(f"  Q: {q}")
        got, score = _top_label(q, verbose)
        good = got == "FALLBACK"
        ok_junk += good
        print(f"  [{'OK ' if good else 'SAI'}] {q[:44]:46s} -> {got[:44]:46s} {score:5.2f}")

    print(f"\nKẾT QUẢ: hợp lệ {ok_valid}/{len(VALID)} · ngoài phạm vi {ok_junk}/{len(JUNK)}")
    return 0 if (ok_valid == len(VALID) and ok_junk == len(JUNK)) else 1


if __name__ == "__main__":
    os.chdir(BACKEND)
    sys.exit(main("--verbose" in sys.argv))
