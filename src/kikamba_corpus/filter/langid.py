"""Language identification: GlotLID v3 (has kam_Latn) with fastText lid.176 as fallback.

lid.176 has no Kikamba label, so in fallback mode we can only *reject* text it confidently
assigns to another language, and we additionally require a Kikamba function-word score.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .. import config

log = logging.getLogger(__name__)

# Frequent Kikamba function words / affix-bearing forms (used only by the lid.176 fallback).
KAM_MARKERS = {
    "na", "nĩ", "ni", "wa", "ya", "sya", "kwa", "ũla", "ĩla", "ila", "ula", "ũndũ", "undu", "mũndũ", "mundu",
    "andũ", "andu", "kana", "ta", "vyũ", "mũno", "muno", "onthe", "ĩndĩ", "indi", "nĩkĩ", "yĩla", "yila",
    "ũu", "ũsu", "ĩsu", "mwaka", "vala", "kĩla", "kila", "nũndũ", "nundu", "ngai", "kũ", "vamwe",
}
_WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)


def kam_marker_score(text: str) -> float:
    words = [w.lower() for w in _WORD.findall(text)]
    if not words:
        return 0.0
    tilde = sum(("ĩ" in w or "ũ" in w) for w in words) / len(words)
    marker = sum(w in KAM_MARKERS for w in words) / len(words)
    return min(1.0, marker + tilde)


@dataclass
class LidResult:
    label: str  # e.g. "kam_Latn"
    prob: float
    top: list[tuple[str, float]]


class LanguageIdentifier:
    def __init__(self, glotlid_path: Path = config.GLOTLID_MODEL, lid176_path: Path = config.LID176_MODEL,
                 prefer: str = "glotlid"):
        import fasttext

        fasttext.FastText.eprint = lambda *a, **k: None  # silence load warning
        self.backend = None
        if prefer == "glotlid" and glotlid_path.exists():
            try:
                self.model = fasttext.load_model(str(glotlid_path))
                self.backend = "glotlid"
            except Exception as e:  # corrupt / partial download
                log.warning("GlotLID failed to load (%s); falling back to lid.176", e)
        if self.backend is None:
            if not lid176_path.exists():
                raise FileNotFoundError("No LID model available (run `corpus fetch` or download models)")
            self.model = fasttext.load_model(str(lid176_path))
            self.backend = "lid176"
        log.info("language ID backend: %s", self.backend)

    def predict(self, text: str, k: int = 3) -> LidResult:
        t = " ".join(text.split())
        if not t:
            return LidResult("und", 0.0, [])
        labels, probs = self.model.predict(t, k=k)
        top = [(l.replace("__label__", ""), float(min(p, 1.0))) for l, p in zip(labels, probs)]
        if self.backend == "lid176":
            top = [(_lid176_to_glot(l), p) for l, p in top]
        return LidResult(top[0][0], top[0][1], top)

    def predict_many(self, texts: list[str], k: int = 3) -> list[LidResult]:
        clean = [" ".join(t.split()) or "." for t in texts]
        labels, probs = self.model.predict(clean, k=k)
        out = []
        for ls, ps in zip(labels, probs):
            top = [(l.replace("__label__", ""), float(min(p, 1.0))) for l, p in zip(ls, ps)]
            if self.backend == "lid176":
                top = [(_lid176_to_glot(l), p) for l, p in top]
            out.append(LidResult(top[0][0], top[0][1], top))
        return out

    def is_kikamba(self, text: str, *, curated: bool = False, result: LidResult | None = None) -> tuple[bool, LidResult]:
        r = result or self.predict(text)
        if self.backend == "glotlid":
            if curated:
                # Human-curated Kikamba: LID is a contamination check, not a gate. Reject only
                # when another language is predicted confidently and kam is not a close contender.
                kam_close = any(l == config.TARGET_LABEL and p >= config.LID_THRESHOLD_CURATED for l, p in r.top)
                ok = r.label == config.TARGET_LABEL or kam_close or r.prob < config.LID_THRESHOLD
            else:
                ok = r.label == config.TARGET_LABEL and r.prob >= config.LID_THRESHOLD
            return ok, r
        # lid.176 fallback: reject confident other-language predictions, require Kikamba markers
        confident_other = r.prob >= (0.9 if curated else 0.5)
        ok = not confident_other and kam_marker_score(text) >= (0.15 if curated else 0.25)
        return ok, r


class TargetLanguageIdentifier:
    """Checks the non-Kikamba side of parallel pairs (English / Swahili).

    Uses fastText lid.176 — accurate for en/sw and ~50x faster than GlotLID, which matters
    for 1.8M+ mined pairs. Falls back to the GlotLID instance if lid.176 is missing.
    """

    def __init__(self, fallback: LanguageIdentifier, lid176_path: Path = config.LID176_MODEL):
        import fasttext

        self.fallback = fallback
        self.model = fasttext.load_model(str(lid176_path)) if lid176_path.exists() else None

    def predict_many(self, texts: list[str]) -> list[LidResult]:
        if self.model is None:
            return self.fallback.predict_many(texts, k=1)
        labels, probs = self.model.predict([" ".join(t.split()) or "." for t in texts], k=1)
        return [LidResult(_lid176_to_glot(l[0].replace("__label__", "")), float(min(p[0], 1.0)),
                          [(_lid176_to_glot(l[0].replace("__label__", "")), float(min(p[0], 1.0)))])
                for l, p in zip(labels, probs)]


_LID176_MAP = {"en": "eng_Latn", "sw": "swh_Latn", "fr": "fra_Latn", "de": "deu_Latn", "es": "spa_Latn"}


def _lid176_to_glot(label: str) -> str:
    return _LID176_MAP.get(label, f"{label}_lid176")


def lang_matches(label: str, expected: str) -> bool:
    """expected is an ISO 639-3 code like 'eng' or 'swh' (swa macro-language / swc accepted for swh)."""
    code = label.split("_")[0]
    return code == expected or (expected == "swh" and code in ("swa", "swh", "swc"))
