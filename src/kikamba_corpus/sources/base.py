"""Shared types/helpers for source fetchers.

Each fetcher module exposes ``INFO: SourceInfo`` and ``fetch() -> Iterator[dict]``.
Records follow jsonl.DOC_FIELDS (+ translation fields for parallel records) and
carry ``kind``: "mono" (monolingual doc), "parallel" (sentence pair only) or
"both" (a pair whose Kikamba side is also used as a monolingual doc).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import pyarrow.parquet as pq

from .. import config
from ..jsonl import make_id, today
from ..net import session


@dataclass(frozen=True)
class SourceInfo:
    id: str
    name: str
    url: str
    license: str
    genre: str
    bucket: str = "main"  # "main" or "unverified"
    curated: bool = False  # human-curated Kikamba (relaxed LID threshold)
    priority: int = 50  # lower wins when deduplicating
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return asdict(self)


def record(
    info: SourceInfo,
    text: str,
    *,
    key: object,
    url: str | None = None,
    kind: str = "mono",
    genre: str | None = None,
    license: str | None = None,
    translation: str | None = None,
    translation_lang: str | None = None,
    extra: dict | None = None,
) -> dict:
    r = {
        "id": make_id(info.id, key, kind),
        "text": text,
        "source": info.id,
        "url": url or info.url,
        "license": license or info.license,
        "genre": genre or info.genre,
        "date_fetched": today(),
        "lang_declared": "kam",
        "kind": kind,
        "bucket": info.bucket,
    }
    if translation is not None:
        r["translation"] = translation
        r["translation_lang"] = translation_lang
    if extra:
        r["extra"] = extra
    return r


def hf_file(repo: str, path: str, *, repo_type: str = "datasets", revision: str = "main") -> Path:
    """Download (cached) one file from the Hugging Face Hub."""
    prefix = "" if repo_type == "models" else "datasets/"
    url = f"https://huggingface.co/{prefix}{repo}/resolve/{revision}/{path}"
    dest = config.CACHE / "hf" / repo.replace("/", "__") / path
    return session().download(url, dest)


def hf_parquet_rows(repo: str, path: str, columns: list[str] | None = None):
    p = hf_file(repo, path)
    t = pq.read_table(p, columns=columns)
    yield from t.to_pylist()
