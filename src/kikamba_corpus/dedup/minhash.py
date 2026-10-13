"""Exact-hash dedup + MinHash/LSH near-duplicate clustering (dependency-light, deterministic).

Shingles are character 5-grams of a normalised form (lowercase, letters/digits only, single
spaces), hashed with CRC32 and permuted with (a*x + b) mod p, p = 4294967311 (prime > 2^32).
LSH banding proposes candidates; each candidate is verified by estimated Jaccard >= threshold.
"""
from __future__ import annotations

import hashlib
import re
import zlib
from collections import defaultdict

import numpy as np

from .. import config

_P = np.uint64(4294967311)
_NONWORD = re.compile(r"[^\w]+", re.UNICODE)


def norm_for_hash(text: str) -> str:
    return _NONWORD.sub(" ", text.lower()).strip()


def exact_key(text: str) -> str:
    return hashlib.sha1(norm_for_hash(text).replace(" ", "").encode("utf-8")).hexdigest()


class MinHasher:
    def __init__(self, num_perm: int = config.NUM_PERM, k: int = config.SHINGLE_K, seed: int = config.SEED):
        rng = np.random.default_rng(seed)
        self.num_perm, self.k = num_perm, k
        self.a = rng.integers(1, 2**31 - 1, size=num_perm, dtype=np.uint64)
        self.b = rng.integers(0, 2**32 - 1, size=num_perm, dtype=np.uint64)

    def shingles(self, text: str) -> np.ndarray:
        s = norm_for_hash(text)
        k = self.k
        grams = {s} if len(s) <= k else {s[i:i + k] for i in range(len(s) - k + 1)}
        return np.fromiter((zlib.crc32(g.encode("utf-8")) for g in grams), dtype=np.uint64, count=len(grams))

    def signature(self, text: str) -> np.ndarray:
        x = self.shingles(text)
        sig = np.full(self.num_perm, np.iinfo(np.uint64).max, dtype=np.uint64)
        for start in range(0, len(x), 4096):  # chunk to bound memory on long docs
            chunk = x[start:start + 4096]
            h = (np.outer(chunk, self.a) + self.b) % _P
            np.minimum(sig, h.min(axis=0), out=sig)
        return sig


def estimated_jaccard(s1: np.ndarray, s2: np.ndarray) -> float:
    return float(np.mean(s1 == s2))


class UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, i: int) -> int:
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, i: int, j: int) -> None:
        ri, rj = self.find(i), self.find(j)
        if ri != rj:
            self.p[max(ri, rj)] = min(ri, rj)


def bands_for(threshold: float, num_perm: int) -> tuple[int, int]:
    # (bands, rows): LSH S-curve midpoint ~ (1/b)^(1/r) should sit a little below the threshold
    return (16, num_perm // 16) if threshold >= 0.75 else (32, num_perm // 32)


def near_dup_clusters(sigs: list[np.ndarray], threshold: float, max_bucket_cmp: int = 8) -> UnionFind:
    n = len(sigs)
    uf = UnionFind(n)
    if n == 0:
        return uf
    b, r = bands_for(threshold, len(sigs[0]))
    for band in range(b):
        buckets: dict[bytes, list[int]] = defaultdict(list)
        for i, s in enumerate(sigs):
            key = s[band * r:(band + 1) * r].tobytes()
            members = buckets[key]
            for j in members[:max_bucket_cmp]:
                if uf.find(i) != uf.find(j) and estimated_jaccard(s, sigs[j]) >= threshold:
                    uf.union(i, j)
                    break
            if len(members) < max_bucket_cmp:
                members.append(i)
    return uf


def clusters(uf: UnionFind) -> dict[int, list[int]]:
    out: dict[int, list[int]] = defaultdict(list)
    for i in range(len(uf.p)):
        out[uf.find(i)].append(i)
    return out
