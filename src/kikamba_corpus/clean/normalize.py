"""Text cleaning: encoding repair, HTML stripping, NFC, Kikamba orthography, whitespace, boilerplate.

Sentence boundaries are preserved: we never join or split lines inside a paragraph and never
touch sentence-final punctuation. Kikamba diacritics (ĩ Ĩ ũ Ũ) are kept as precomposed NFC.
"""
from __future__ import annotations

import html
import re
import unicodedata

import ftfy
from bs4 import BeautifulSoup

_FTFY = ftfy.TextFixerConfig(
    unescape_html=False,  # handled below, only when the text actually is HTML
    uncurl_quotes=False,  # handled below with our own mapping
    fix_line_breaks=True,
    normalization="NFC",
    explain=False,
)

_HTML_TAG = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(\s[^<>]*)?/?>")
_ENTITY = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]{2,8});")

# Grave, macron and circumflex i/u are keyboard substitutes for the tilde vowels (seen as
# nī, andū, mūno, nî ... in ASR transcripts and web text). Standard Kikamba marks neither tone
# nor length (long vowels are doubled), so these map to ĩ/ũ. Acute í and ü are left alone
# (they occur in foreign names).
_ORTHO = str.maketrans({
    "ì": "ĩ", "Ì": "Ĩ", "ù": "ũ", "Ù": "Ũ",
    "ī": "ĩ", "Ī": "Ĩ", "ū": "ũ", "Ū": "Ũ",
    "î": "ĩ", "Î": "Ĩ", "û": "ũ", "Û": "Ũ",
})
_QUOTES = str.maketrans({
    "’": "'", "‘": "'", "ʼ": "'", "ʻ": "'", "´": "'", "`": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
})
_ZERO_WIDTH = re.compile("[​‌‍⁠﻿­]")
_SPACES = re.compile(r"[ \t  -   　]+")
_URL_ONLY = re.compile(r"^(https?://|www\.)\S+$", re.I)
_EMAIL_ONLY = re.compile(r"^\S+@\S+\.\S+$")

_BOILERPLATE = re.compile(
    r"(cookie|all rights reserved|copyright\s*(©|\(c\)|\d{4})|©\s*\d{4}|privacy policy|terms of (use|service)"
    r"|click here|read more|share (this|on)|subscribe|log ?in|sign ?up|javascript|skip to (main )?content"
    r"|powered by|follow us|download (the )?app|\bfacebook\b.*\btwitter\b)",
    re.I,
)


def looks_like_html(text: str) -> bool:
    return len(_HTML_TAG.findall(text[:20000])) >= 2


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "form"]):
        tag.decompose()
    return soup.get_text("\n")


def is_boilerplate_line(line: str) -> bool:
    if _URL_ONLY.match(line) or _EMAIL_ONLY.match(line):
        return True
    letters = sum(c.isalpha() for c in line)
    if line and letters == 0:
        return True  # pure numbers / symbols (page numbers, separators)
    # Only short lines are judged by keyword, so a real paragraph mentioning e.g. "copyright" survives.
    return len(line) <= 120 and bool(_BOILERPLATE.search(line))


def normalize(text: str) -> str:
    """Character-level normalisation (no line removal)."""
    text = ftfy.fix_text(text, _FTFY)
    if _ENTITY.search(text):
        text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_ORTHO).translate(_QUOTES)
    text = _ZERO_WIDTH.sub("", text)
    text = unicodedata.normalize("NFC", text)
    return text


def clean_text(text: str | None, *, strip_boilerplate: bool = True) -> str:
    if not text:
        return ""
    if looks_like_html(text):
        text = strip_html(text)
    text = normalize(text)
    out: list[str] = []
    for line in text.replace("\r", "\n").split("\n"):
        line = _SPACES.sub(" ", line).strip()
        if not line:
            continue
        if strip_boilerplate and is_boilerplate_line(line):
            continue
        out.append(line)
    # drop immediately repeated lines (menus, repeated headers)
    dedup = [l for i, l in enumerate(out) if i == 0 or l != out[i - 1]]
    return "\n".join(dedup)
