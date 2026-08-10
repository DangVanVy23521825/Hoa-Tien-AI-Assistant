"""Tiện ích dùng chung cho pipeline ingest (crawl → extract → review → merge).

Chỉ dùng stdlib + httpx (đã có trong requirements). KHÔNG thêm bs4/pyyaml/trafilatura:
`requirements.txt` cũng được cài trên Railway và plan đó đã OOM nhiều lần — không đáng
bơm thêm dependency cho một script chạy tay vài lần.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

# common.py nằm ở backend/scripts/ingest/ → parents[3] là gốc repo
INGEST_DIR = Path(__file__).resolve().parent
BACKEND_DIR = INGEST_DIR.parents[1]
REPO_ROOT = INGEST_DIR.parents[2]

SOURCES_PATH = INGEST_DIR / "sources.json"
RAW_DIR = REPO_ROOT / "data" / "ingest" / "raw"
CANDIDATES_PATH = REPO_ROOT / "data" / "ingest" / "candidates.json"

#: Hai bản seed phải giống hệt nhau — Railway deploy từ backend/ nên có bản copy riêng.
SEED_PATHS = (
    REPO_ROOT / "data" / "seed-knowledge-base.json",
    BACKEND_DIR / "data" / "seed-knowledge-base.json",
)

# Header HTTP chỉ nhận latin-1 → phải viết không dấu, đừng "sửa" lại thành có dấu.
# Phải kèm URL + email liên hệ: Wikimedia trả 403 cho User-Agent chung chung (đã gặp thật).
USER_AGENT = (
    "HoaTienAI-KB-Ingest/1.0 "
    "(https://hoa-tien-ai-assistant-nu.vercel.app; dangvanvy112@gmail.com) python-httpx"
)

#: Nghỉ giữa 2 request tới cùng một host — lịch sự với cổng thông tin của xã/thành phố.
POLITE_DELAY_S = 1.0

#: Intermediate CA tải sẵn về đây. `hoatien.danang.gov.vn` (và danang.gov.vn) chỉ gửi
#: cert lá, KHÔNG gửi intermediate "GlobalSign RSA OV SSL CA 2018", nên Python không
#: dựng được chain dù root R3 đã có trong certifi (curl qua được vì dùng CA hệ thống).
#: Cách xử lý: nối intermediate vào bundle rồi verify như bình thường — TUYỆT ĐỐI
#: không tắt xác thực chứng chỉ để "cho nhanh".
EXTRA_CA_DIR = INGEST_DIR / "extra_ca"
_ca_bundle_cache: Path | None = None


def ca_bundle() -> Path:
    """Bundle = certifi + các intermediate trong extra_ca/. Cache theo tiến trình."""
    global _ca_bundle_cache
    if _ca_bundle_cache is not None:
        return _ca_bundle_cache

    import certifi  # đi kèm httpx, không phải dependency mới

    pems = [Path(certifi.where()).read_text(encoding="utf-8")]
    if EXTRA_CA_DIR.exists():
        pems += [p.read_text(encoding="utf-8") for p in sorted(EXTRA_CA_DIR.glob("*.pem"))]

    bundle = REPO_ROOT / "data" / "ingest" / "ca-bundle.pem"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    bundle.write_text("\n".join(pems), encoding="utf-8")
    _ca_bundle_cache = bundle
    return bundle


# --------------------------------------------------------------------------- HTML


class _TextExtractor(HTMLParser):
    """Lột HTML → text. Bỏ hẳn nội dung trong script/style/nav/header/footer/form.

    Không dùng regex trên HTML thô: trang của cổng thông tin có nhiều <script> chứa
    chuỗi trông như thẻ, regex sẽ cắt nhầm.
    """

    # KHÔNG loại <form>: cổng thông tin xã chạy ASP.NET WebForms, bọc TOÀN BỘ trang
    # trong một <form runat="server"> — loại form là mất sạch nội dung (đã dính thật:
    # 314KB HTML ra 0 ký tự text).
    _DROP = {"script", "style", "noscript", "svg"}
    _BLOCK = {
        "p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6",
        "table", "section", "article", "blockquote", "td", "th",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title = ""
        self._drop_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in self._DROP:
            self._drop_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._DROP:
            self._drop_depth = max(0, self._drop_depth - 1)
        elif tag == "title":
            self._in_title = False
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._drop_depth == 0:
            self.parts.append(data)


def html_to_text(html: str) -> tuple[str, str]:
    """→ (title, text). Text đã gộp khoảng trắng và bỏ dòng rỗng thừa."""
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:  # noqa: BLE001 — HTML hỏng thì lấy được đến đâu dùng đến đó
        pass
    raw = "".join(parser.parts)
    lines = [re.sub(r"[ \t\xa0]+", " ", ln).strip() for ln in raw.split("\n")]
    text = "\n".join(ln for ln in lines if ln)
    return parser.title.strip(), re.sub(r"\n{3,}", "\n\n", text)


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag == "a":
            for key, value in attrs:
                if key == "href" and value:
                    self.hrefs.append(value)


def extract_links(html: str, base_url: str) -> list[str]:
    """Link tuyệt đối, cùng scheme http(s), đã bỏ fragment và trùng lặp."""
    collector = _LinkCollector()
    try:
        collector.feed(html)
    except Exception:  # noqa: BLE001
        pass
    seen: dict[str, None] = {}
    for href in collector.hrefs:
        absolute = urljoin(base_url, href.strip())
        absolute, _, _ = absolute.partition("#")
        if absolute.startswith(("http://", "https://")):
            seen.setdefault(absolute, None)
    return list(seen)


# --------------------------------------------------------------------------- fetch


@dataclass
class Page:
    url: str
    title: str
    text: str
    fetched_at: str
    html: str = field(default="", repr=False)


_last_hit: dict[str, float] = {}


def fetch(url: str, timeout_s: float = 20.0) -> Page:
    """Tải 1 trang, tự giãn cách theo host. Raise httpx.HTTPError nếu hỏng."""
    host = urlparse(url).netloc
    elapsed = time.monotonic() - _last_hit.get(host, 0.0)
    if elapsed < POLITE_DELAY_S:
        time.sleep(POLITE_DELAY_S - elapsed)
    _last_hit[host] = time.monotonic()

    response = httpx.get(
        url,
        timeout=timeout_s,
        follow_redirects=True,
        verify=str(ca_bundle()),
        headers={"User-Agent": USER_AGENT, "Accept-Language": "vi,en;q=0.8"},
    )
    response.raise_for_status()
    title, text = html_to_text(response.text)
    return Page(
        url=str(response.url),
        title=title,
        text=text,
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        html=response.text,
    )


def url_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------- I/O


def read_json(path: Path, default=None):  # noqa: ANN001, ANN201
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:  # noqa: ANN001
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# --------------------------------------------------------------- lọc boilerplate


#: Dòng trông như HTML thô. Trang view.aspx nhúng lại nguyên body bài viết dưới dạng
#: chuỗi HTML (phần meta description) → nội dung bị lặp 2 lần, tốn token vô ích.
_RAW_HTML_LINE = re.compile(r"<(p|span|img|br|div|table|font)\b[^>]*>", re.I)

#: Dòng xuất hiện trên >= tỉ lệ này số trang cùng domain thì coi là menu/sidebar/footer.
BOILERPLATE_RATIO = 0.5


def boilerplate_lines(pages: list[dict], ratio: float = BOILERPLATE_RATIO) -> set[str]:
    """Dòng lặp trên phần lớn trang của cùng một site = menu/sidebar/footer.

    Rẻ và không cần thư viện: cổng thông tin bê nguyên sidebar vào mọi trang, chiếm
    ~50% text. Không lọc thì bước extract vừa tốn gấp đôi token vừa dễ trích nhầm mục
    trong sidebar thành nội dung của bài.
    """
    if len(pages) < 4:  # quá ít trang thì thống kê không có ý nghĩa
        return set()
    counter: dict[str, int] = {}
    for page in pages:
        for line in set(page["text"].split("\n")):
            counter[line] = counter.get(line, 0) + 1
    threshold = len(pages) * ratio
    return {line for line, count in counter.items() if count >= threshold}


def clean_text(text: str, boiler: set[str]) -> str:
    kept = [
        line
        for line in text.split("\n")
        if line not in boiler and not _RAW_HTML_LINE.search(line)
    ]
    return "\n".join(kept).strip()


def load_raw_pages() -> list[dict]:
    """Trang đã crawl, sắp theo url cho ổn định giữa các lần chạy."""
    if not RAW_DIR.exists():
        return []
    pages = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RAW_DIR.glob("*.json"))]
    return sorted(pages, key=lambda p: p["url"])
