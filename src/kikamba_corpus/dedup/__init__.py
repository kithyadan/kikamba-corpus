from .minhash import (MinHasher, UnionFind, clusters, estimated_jaccard, exact_key, near_dup_clusters,
                      norm_for_hash)


def dedup_docs(docs: list[dict], threshold: float, hasher: MinHasher | None = None,
               priority=lambda d: (d.get("priority", 50), -len(d["text"]))):
    """Exact + near dedup. Returns (kept, dropped) where dropped items are (doc, reason)."""
    kept_exact, dropped, seen = [], [], {}
    for d in sorted(docs, key=priority):
        k = exact_key(d["text"])
        if k in seen:
            dropped.append((d, f"exact_dup_of:{seen[k]}"))
        else:
            seen[k] = d["id"]
            kept_exact.append(d)
    hasher = hasher or MinHasher()
    sigs = [hasher.signature(d["text"]) for d in kept_exact]
    uf = near_dup_clusters(sigs, threshold)
    kept = []
    for members in clusters(uf).values():
        members.sort()  # kept_exact is already priority-ordered, so the lowest index wins
        kept.append(kept_exact[members[0]])
        for m in members[1:]:
            dropped.append((kept_exact[m], f"near_dup_of:{kept_exact[members[0]]['id']}"))
    return kept, dropped


__all__ = ["MinHasher", "UnionFind", "clusters", "estimated_jaccard", "exact_key", "near_dup_clusters",
           "norm_for_hash", "dedup_docs"]
