"""Cheap heuristic quality filters. Each returns (keep, reason)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .. import config

_WORD = re.compile(r"\w+", re.UNICODE)


def letter_ratio(text: str) -> float:
    chars = [c for c in text if not c.isspace()]
    return sum(c.isalpha() for c in chars) / len(chars) if chars else 0.0


def latin_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum("LATIN" in unicodedata.name(c, "") for c in letters) / len(letters)


def quality_check(text: str, *, min_chars: int = config.MIN_CHARS, min_words: int = config.MIN_WORDS) -> tuple[bool, str]:
    if not text.strip():
        return False, "empty"
    if len(text) < min_chars:
        return False, "too_short_chars"
    words = _WORD.findall(text)
    if len(words) < min_words:
        return False, "too_few_words"
    if letter_ratio(text) < config.MIN_LETTER_RATIO:
        return False, "low_letter_ratio"
    if latin_ratio(text) < 0.8:
        return False, "non_latin_script"
    lines = text.split("\n")
    if len(lines) >= 5 and len(set(lines)) / len(lines) < 0.5:
        return False, "repetitive_lines"
    if len(words) >= 20:
        head = words[:500]
        top = Counter(w.lower() for w in head).most_common(1)[0][1]
        if top / len(head) > 0.3:
            return False, "repetitive_words"
    return True, "ok"
