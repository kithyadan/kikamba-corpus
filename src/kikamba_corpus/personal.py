"""Extended private corpus: main train split + the unverified bucket.

For private study only. Written to ~/kikamba-personal/ (override with $KIKAMBA_PERSONAL_DIR),
outside the repository. It contains all-rights-reserved text (BSK 2011 Bible,
jw.org-derived pairs) and must not be redistributed. dev/test are the unchanged main splits.

Unverified docs are dropped if they are exact or near duplicates (MinHash Jaccard >=
SPLIT_LEAK_THRESHOLD) of ANY main-corpus doc: duplicates of train would double-count text,
and duplicates of dev/test would leak the evaluation sets (incl. FLORES).
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from . import config
from .dedup import MinHasher, clusters, exact_key, near_dup_clusters
from .jsonl import read_jsonl, write_jsonl

log = logging.getLogger(__name__)
# Deliberately OUTSIDE the repository so it can never be committed/pushed.
PERSONAL_ROOT = Path(os.environ.get("KIKAMBA_PERSONAL_DIR", Path.home() / "kikamba-personal"))
PERSONAL = PERSONAL_ROOT / "data"
PERSONAL_TOKENIZERS = PERSONAL_ROOT / "tokenizers"


def run() -> dict:
    PERSONAL.mkdir(parents=True, exist_ok=True)
    main = {s: list(read_jsonl(config.MONO / f"{s}.jsonl")) for s in ("train", "dev", "test")}
    unv = list(read_jsonl(config.UNVERIFIED / "monolingual.jsonl"))
    main_all = [(s, d) for s, docs in main.items() for d in docs]

    main_keys = {exact_key(d["text"]): s for s, d in main_all}
    dropped = []
    cand = []
    for d in unv:
        s = main_keys.get(exact_key(d["text"]))
        if s:
            dropped.append((d, f"exact_dup_of_main_{s}"))
        else:
            cand.append(d)

    hasher = MinHasher()
    docs = [d for _, d in main_all] + cand
    uf = near_dup_clusters([hasher.signature(d["text"]) for d in docs], config.SPLIT_LEAK_THRESHOLD)
    n_main = len(main_all)
    bad = {}
    for members in clusters(uf).values():
        main_splits = {main_all[i][0] for i in members if i < n_main}
        if main_splits:
            why = "near_dup_of_main_" + ("heldout" if main_splits & {"dev", "test"} else "train")
            for i in members:
                if i >= n_main:
                    bad[i - n_main] = why
    kept = []
    for i, d in enumerate(cand):
        if i in bad:
            dropped.append((d, bad[i]))
        else:
            kept.append(d)

    rows = main["train"] + kept
    write_jsonl(PERSONAL / "train_all.jsonl", rows)
    with open(PERSONAL / "train_all.txt", "w", encoding="utf-8", newline="\n") as f:
        for d in rows:
            f.write(" ".join(d["text"].split()) + "\n")
    write_jsonl(PERSONAL / "dropped_unverified.jsonl",
                ({"id": d["id"], "source": d["source"], "reason": r, "preview": d["text"][:100]} for d, r in dropped))

    def words(ds):
        return sum(len(d["text"].split()) for d in ds)

    report = {
        "main_train_docs": len(main["train"]), "main_train_words": words(main["train"]),
        "unverified_docs_in": len(unv), "unverified_docs_added": len(kept), "unverified_words_added": words(kept),
        "unverified_dropped": len(dropped),
        "dropped_by_reason": {r: sum(1 for _, x in dropped if x == r) for r in sorted({x for _, x in dropped})},
        "added_by_source": {s: sum(1 for d in kept if d["source"] == s) for s in sorted({d["source"] for d in kept})},
        "train_all_docs": len(rows), "train_all_words": words(rows),
    }
    (PERSONAL / "personal_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    (PERSONAL / "README.md").write_text(
        "# data/personal — PRIVATE USE ONLY\n\n"
        "`train_all.txt` = main train split + deduplicated unverified bucket (BSK 2011 Bible, "
        "jw.org-derived MT560/Knox text, Glot500 slice). Contains all-rights-reserved text: do not "
        "redistribute this folder.\n"
        "Held-out sets are the unchanged `data/monolingual/dev.jsonl` / `test.jsonl` (near-copies removed).\n",
        encoding="utf-8")
    log.info("personal train set: %s", report)
    return report
