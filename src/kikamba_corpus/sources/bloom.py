"""Bloom Library (SIL) books with Kikamba content: children's readers + Bible-story readers.

Book list comes from the public Bloom Parse API; book text from the published .htm on S3.
Only ``div.bloom-editable[lang=kam]`` inside content pages is kept (front/back matter,
credits and licence boilerplate pages are skipped). Where the same translation group
also has an English/Swahili editable, a sentence-group pair is emitted.
"""
import json
import re
from html import unescape as html_unescape
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup

from ..net import session
from .base import SourceInfo, record

PARSE_URL = "https://server.bloomlibrary.org/parse/classes/books"
PARSE_APP_ID = "R6qNTeumQXjJCMutAJYAwPtip1qBulkFyLefkCE5"  # public app id used by bloomlibrary.org
S3 = "https://s3.amazonaws.com/BloomLibraryBooks"

INFO = SourceInfo(
    id="bloom",
    name="Bloom Library (kam)",
    url="https://bloomlibrary.org/language:kam",
    license="CC-BY-NC-SA / CC-BY-NC-ND (per book, see record)",
    genre="children-stories",
    curated=True,
    priority=12,
)

LICENSES = {
    "cc-by": "CC-BY-4.0", "cc-by-sa": "CC-BY-SA-4.0", "cc-by-nc": "CC-BY-NC-4.0",
    "cc-by-nc-sa": "CC-BY-NC-SA-4.0", "cc-by-nd": "CC-BY-ND-4.0", "cc-by-nc-nd": "CC-BY-NC-ND-4.0",
    "cc0": "CC0-1.0",
}
PAIR_LANGS = {"en": "eng", "sw": "swh"}
RELIGIOUS_MARKERS = re.compile(r"bibleforchildren|Bible-for-Children|\bBible\b", re.I)


def _books():
    where = {"langPointers": {"$inQuery": {"where": {"isoCode": "kam"}, "className": "language"}}}
    params = {"where": json.dumps(where), "limit": 1000,
              "keys": "title,license,copyright,baseUrl,harvestState,tags,inCirculation"}
    r = session().get(PARSE_URL, params=params, headers={"X-Parse-Application-Id": PARSE_APP_ID})
    return r.json()["results"]


def _htm_key(prefix: str) -> str | None:
    """prefix = '<uploader>/<timestamp>/'; the book's .htm sits in the single folder below it."""
    r = session().get(f"{S3}?prefix={quote(prefix)}")
    keys = [html_unescape(k) for k in re.findall(r"<Key>(.*?)</Key>", r.text)]
    htm = [k for k in keys if k.endswith(".htm") and k[len(prefix):].count("/") == 1]
    return htm[0] if htm else None


def fetch():
    for b in _books():
        if b.get("inCirculation") is False:
            continue
        lic_raw = (b.get("license") or "").lower()
        if lic_raw not in LICENSES:  # unknown / all-rights-reserved: not usable
            continue
        path = unquote(b["baseUrl"].split("/BloomLibraryBooks/", 1)[1])
        prefix = "/".join(path.split("/")[:2]) + "/"
        key = _htm_key(prefix)
        if not key:
            continue
        html = session().get(f"{S3}/{quote(key)}").content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        religious = bool(RELIGIOUS_MARKERS.search(html))
        genre = "religious" if religious else INFO.genre
        book_url = f"https://bloomlibrary.org/book/{b['objectId']}"
        extra = {"title": b.get("title"), "copyright": b.get("copyright"), "tags": b.get("tags")}
        paras, gi = [], 0
        for page in soup.select("div.bloom-page"):
            cls = page.get("class") or []
            if "bloom-frontMatter" in cls or "bloom-backMatter" in cls:
                continue
            for group in page.select("div.bloom-translationGroup"):
                by_lang = {}
                for ed in group.select("div.bloom-editable"):
                    t = ed.get_text("\n", strip=True)
                    if t:
                        by_lang[ed.get("lang")] = t
                kam = by_lang.get("kam")
                if not kam:
                    continue
                paras.append(kam)
                gi += 1
                for bl, lang in PAIR_LANGS.items():
                    if by_lang.get(bl):
                        yield record(INFO, kam, key=(b["objectId"], gi, lang), url=book_url, kind="parallel",
                                     license=LICENSES[lic_raw], genre=genre, translation=by_lang[bl],
                                     translation_lang=lang, extra=extra)
        if paras:
            yield record(INFO, "\n".join(paras), key=b["objectId"], url=book_url,
                         license=LICENSES[lic_raw], genre=genre, extra=extra)

