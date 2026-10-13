"""Train/dev/test assignment with no cross-split near-duplicates.

1. Benchmark docs (FLORES-200) are pinned: FLORES dev -> dev, devtest -> test. Never train.
2. Every other doc is hashed (sha1 of id) into dev / test / train by DEV_FRAC / TEST_FRAC.
3. A second MinHash/LSH pass at a looser threshold (SPLIT_LEAK_THRESHOLD) clusters survivors;
   any cluster spanning several splits is resolved:
     - cluster contains a benchmark doc -> non-benchmark members are dropped (protects FLORES);
     - otherwise all members are moved to train.
"""
from __future__ import annotations

import hashlib

from .. import config
from ..dedup import MinHasher, clusters, near_dup_clusters


def hash_split(doc_id: str, dev_frac: float = config.DEV_FRAC, test_frac: float = config.TEST_FRAC) -> str:
    u = int(hashlib.sha1(doc_id.encode("utf-8")).hexdigest()[:8], 16) / 2**32
    if u < dev_frac:
        return "dev"
    if u < dev_frac + test_frac:
        return "test"
    return "train"


def is_benchmark(doc: dict) -> bool:
    return bool((doc.get("extra") or {}).get("benchmark"))


def initial_split(doc: dict) -> str:
    if is_benchmark(doc):
        return "dev" if doc["extra"].get("flores_split") == "dev" else "test"
    return hash_split(doc["id"])


def assign_splits(docs: list[dict], threshold: float = config.SPLIT_LEAK_THRESHOLD,
                  hasher: MinHasher | None = None):
    """Returns (splits: dict[name, list[doc]], dropped: list[(doc, reason)], moved: int)."""
    hasher = hasher or MinHasher()
    split_of = [initial_split(d) for d in docs]
    uf = near_dup_clusters([hasher.signature(d["text"]) for d in docs], threshold)
    dropped, moved, drop_idx = [], 0, set()
    for members in clusters(uf).values():
        if len(members) < 2 or len({split_of[i] for i in members}) < 2:
            continue
        bench = [i for i in members if is_benchmark(docs[i])]
        if bench:
            for i in members:
                if not is_benchmark(docs[i]):
                    drop_idx.add(i)
                    dropped.append((docs[i], f"near_dup_of_benchmark:{docs[bench[0]]['id']}"))
        else:
            for i in members:
                if split_of[i] != "train":
                    split_of[i] = "train"
                    moved += 1
    out = {"train": [], "dev": [], "test": []}
    for i, d in enumerate(docs):
        if i not in drop_idx:
            out[split_of[i]].append(d)
    return out, dropped, moved
