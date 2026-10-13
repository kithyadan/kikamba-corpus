"""Religious-content tagging for documents whose source genre is generic (web, pdf, ...).

Signals: (1) URL on a known religious publisher domain; (2) density of Kikamba religious
terms. Strong terms are unambiguous (Jesus, Jehovah, Christ, Bible, Lord, angel, Satan);
weak terms are common in religious text but also appear elsewhere (Ngai = God; -thaith- = worship).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

RELIGIOUS_DOMAINS = (
    "jw.org", "jw-cdn.org", "watchtower", "bible.com", "bible.is", "biblegateway", "bibleforchildren",
    "ebible.org", "gospelgo", "biblica", "churchofjesuschrist", "lds.org", "adventist", "sermon",
    "gospel", "bibles.", "globalrecordings", "4laws", "jesusfilm", "christ",
)
_STRONG = re.compile(
    r"\b(yes[uũ]|yeova|yehova|jehova\w*|jesus|kl[iĩ]sto|kilisto|kristo|m[uũ]kl[iĩ]sto|akl[iĩ]sto|"
    r"mbivil[iĩ]a|mbibilia|bibilia|mw[iĩ]a[iĩ]i|malaika|satani|ivang[eĩi]li|ivanjeli)\b",
    re.I,
)
_WEAK = re.compile(r"\b(ngai|\w*thaith\w*|\w*thaithi\w*|isilaeli|islaeli|nabii|mũthembi|muthembi)\b", re.I)
_WORD = re.compile(r"\w+")


def religious_score(text: str) -> tuple[int, int]:
    return len(_STRONG.findall(text)), len(_WEAK.findall(text))


def is_religious(text: str, url: str | None = None) -> bool:
    if url:
        host = urlparse(url).netloc.lower() + urlparse(url).path.lower()[:40]
        if any(d in host for d in RELIGIOUS_DOMAINS):
            return True
    strong, weak = religious_score(text)
    score = 2 * strong + weak
    n = max(1, len(_WORD.findall(text)))
    if n < 40:
        return score >= 2 and strong >= 1
    return score >= 3 and score / n >= 0.01


def assign_genre(doc: dict) -> str:
    g = doc.get("genre") or "unknown"
    if g == "religious":
        return g
    return "religious" if is_religious(doc["text"], doc.get("url")) else g
