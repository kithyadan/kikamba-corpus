"""JSONL helpers and the shared document schema."""
from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

# Every raw record carries at least these fields.
DOC_FIELDS = ("id", "text", "source", "url", "license", "genre", "date_fetched", "lang_declared")
PARALLEL_FIELDS = ("translation", "translation_lang")


def today() -> str:
    return dt.date.today().isoformat()


def make_id(source: str, *parts: object) -> str:
    h = hashlib.sha1("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]
    return f"{source}-{h}"


def read_jsonl(path: Path) -> Iterator[dict]:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    tmp = path.with_suffix(path.suffix + ".part")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    tmp.replace(path)
    return n


def write_jsonl_gz_shards(base: Path, rows: list[dict], shard_rows: int) -> tuple[int, list[Path]]:
    """Write rows as <base>-00000.jsonl.gz, <base>-00001.jsonl.gz, ... (keeps files under GitHub's 100 MB cap)."""
    base.parent.mkdir(parents=True, exist_ok=True)
    for old in base.parent.glob(f"{base.name}-*.jsonl.gz"):
        old.unlink()
    paths = []
    for i, start in enumerate(range(0, len(rows), shard_rows)):
        p = base.parent / f"{base.name}-{i:05d}.jsonl.gz"
        with gzip.open(p, "wt", encoding="utf-8", newline="\n") as f:
            for r in rows[start:start + shard_rows]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        paths.append(p)
    return len(rows), paths


class JsonlAppender:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "a", encoding="utf-8", newline="\n")

    def write(self, row: dict) -> None:
        self.f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def close(self) -> None:
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
