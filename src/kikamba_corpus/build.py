"""Build: raw -> clean -> quality filter -> LID -> exact/near dedup -> genre -> split -> outputs.

Every dropped document / line / pair is logged to logs/drops.jsonl.gz with stage + reason,
and counts go to logs/drop_summary.json.
"""
from __future__ import annotations

import gzip
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path

from . import config, sources
from .clean import clean_text
from .dedup import MinHasher, dedup_docs, exact_key
from .filter import LanguageIdentifier, lang_matches, quality_check
from .filter.langid import TargetLanguageIdentifier
from .filter.quality import letter_ratio
from .genre import assign_genre
from .jsonl import read_jsonl, write_jsonl, write_jsonl_gz_shards
from .split import assign_splits

log = logging.getLogger(__name__)
BATCH = 20000
OUT_FIELDS = ("id", "text", "source", "url", "license", "genre", "lang", "date_fetched", "lang_declared")


class DropLog:
    def __init__(self, path: Path):
        self.f = gzip.open(path, "wt", encoding="utf-8")
        self.counts: Counter = Counter()

    def __call__(self, rec: dict, stage: str, reason: str, text: str | None = None) -> None:
        key_reason = reason.split(":", 1)[0] if reason.startswith(("exact_dup_of", "near_dup_of")) else reason
        if stage == "lid":
            key_reason = "lid:" + reason.split(":")[1]  # aggregate by predicted label only
        self.counts[(rec.get("bucket", "main"), rec["source"], stage, key_reason)] += 1
        t = text if text is not None else rec.get("text", "")
        self.f.write(json.dumps({"id": rec["id"], "source": rec["source"], "stage": stage, "reason": reason,
                                 "chars": len(t or ""), "preview": (t or "")[:100]}, ensure_ascii=False) + "\n")

    def close(self) -> dict:
        self.f.close()
        summary = defaultdict(lambda: defaultdict(Counter))
        for (bucket, src, stage, reason), n in sorted(self.counts.items()):
            summary[bucket][src][f"{stage}/{reason}"] += n
        return {b: {s: dict(c) for s, c in v.items()} for b, v in summary.items()}


# In curated sources only lines confidently in these contact languages are removed
# (e.g. English licence paragraphs embedded in Bloom/ASb story pages).
CURATED_STRIP_LANGS = {"eng", "swh", "swa", "swc", "fra"}


def _strip_foreign_lines(text: str, lid: LanguageIdentifier, curated: bool = False) -> tuple[str, list[tuple[str, str]]]:
    lines = text.split("\n")
    if len(lines) < 3:
        return text, []
    idx = [i for i, l in enumerate(lines) if len(l) >= config.LINE_DROP_MIN_CHARS]
    if not idx:
        return text, []
    preds = lid.predict_many([lines[i] for i in idx], k=1)
    bad = {}
    for i, r in zip(idx, preds):
        if curated:
            if r.label.split("_")[0] in CURATED_STRIP_LANGS and r.prob >= 0.9:
                bad[i] = f"{r.label}:{r.prob:.2f}"
        elif r.label != config.TARGET_LABEL and r.prob >= config.LINE_DROP_PROB:
            bad[i] = f"{r.label}:{r.prob:.2f}"
    kept = [l for i, l in enumerate(lines) if i not in bad]
    return "\n".join(kept), [(lines[i], why) for i, why in bad.items()]


def _mono_doc(rec: dict, text: str, info, lid_prob: float, extra_add: dict | None = None) -> dict:
    d = {k: rec.get(k) for k in OUT_FIELDS}
    d.update(text=text, lang="kam", lid_prob=round(lid_prob, 4), priority=info.priority)
    extra = dict(rec.get("extra") or {})
    if extra_add:
        extra.update(extra_add)
    if extra:
        d["extra"] = extra
    return d


def process_source(mod, lid: LanguageIdentifier, drop: DropLog, seen_mono: dict, seen_pairs: set,
                   mono_out: dict, par_out: dict, tlid: TargetLanguageIdentifier) -> None:
    info = mod.INFO
    raw = config.RAW / f"{info.id}.jsonl"
    if not raw.exists():
        log.warning("no raw data for %s (fetch failed or skipped)", info.id)
        return
    curated = info.curated
    benchmark = "benchmark" in info.tags  # human-translated eval set: never dropped by LID
    batch: list[dict] = []
    lid_cache: dict[str, object] = {}  # exact_key -> LidResult; mined data repeats lines a lot

    def kam_lid(texts: list[str]) -> list:
        keys = [exact_key(t) for t in texts]
        todo = {}
        for k, t in zip(keys, texts):
            if k not in lid_cache and k not in todo:
                todo[k] = t
        if todo:
            for k, p in zip(todo, lid.predict_many(list(todo.values()), k=3)):
                lid_cache[k] = p
        return [lid_cache[k] for k in keys]

    def flush():
        # ---- clean
        for r in batch:
            r["_text"] = clean_text(r["text"])
            if "translation" in r:
                r["_tr"] = clean_text(r.get("translation") or "", strip_boilerplate=False)
        # ---- monolingual path: quality -> (line LID) -> doc LID
        cand = []
        for r in batch:
            if r["kind"] not in ("mono", "both"):
                continue
            ok, why = quality_check(r["_text"])
            if not ok:
                drop(r, "quality", why, r["_text"])
                continue
            cand.append(r)
        removed_lines = {}
        for r in cand:
            if r["_text"].count("\n") >= 2:
                new, bad = _strip_foreign_lines(r["_text"], lid, curated)
                for line, why in bad:
                    drop(r, "line_lid", why, line)
                if bad:
                    removed_lines[r["id"]] = len(bad)
                    r["_text"] = new
        cand2 = []
        for r in cand:
            ok, why = quality_check(r["_text"])
            if ok:
                cand2.append(r)
            else:
                drop(r, "quality_after_line_lid", why, r["_text"])
        cand = cand2
        preds = kam_lid([r["_text"] for r in cand])
        for r, p in zip(cand, preds):
            ok = benchmark or lid.is_kikamba(r["_text"], curated=curated, result=p)[0]
            if not ok:
                drop(r, "lid", f"lid:{p.label}:{p.prob:.2f}", r["_text"])
                continue
            bucket = r["bucket"]
            k = exact_key(r["_text"])
            if k in seen_mono[bucket]:
                drop(r, "exact_dup", f"exact_dup_of:{seen_mono[bucket][k]}", r["_text"])
                continue
            seen_mono[bucket][k] = r["id"]
            extra_add = {"lines_removed_lid": removed_lines[r["id"]]} if r["id"] in removed_lines else None
            mono_out[bucket].append(_mono_doc(r, r["_text"], info, p.prob if p.label == config.TARGET_LABEL
                                              else dict(p.top).get(config.TARGET_LABEL, 0.0), extra_add))
        # ---- parallel path
        pcand = []
        for r in batch:
            if r["kind"] not in ("parallel", "both"):
                continue
            kam, tr = r["_text"], r.get("_tr", "")
            if not kam or not tr:
                drop(r, "pair_quality", "empty_side", kam)
                continue
            if norm(kam) == norm(tr):
                drop(r, "pair_quality", "untranslated", kam)
                continue
            if letter_ratio(kam) < 0.5 or letter_ratio(tr) < 0.5:
                drop(r, "pair_quality", "low_letter_ratio", kam)
                continue
            ratio = len(kam) / max(1, len(tr))
            if not curated and not (0.2 <= ratio <= 5.0):
                drop(r, "pair_quality", f"length_ratio:{ratio:.2f}", kam)
                continue
            pcand.append(r)
        if pcand and not curated:
            kp = kam_lid([r["_text"] for r in pcand])
            tp = tlid.predict_many([r["_tr"] for r in pcand])
            keep = []
            for r, p, t in zip(pcand, kp, tp):
                ok = lid.is_kikamba(r["_text"], result=p)[0]
                if not ok:
                    drop(r, "pair_lid", f"lid:{p.label}:{p.prob:.2f}", r["_text"])
                elif not lang_matches(t.label, r["translation_lang"]):
                    drop(r, "pair_lid", f"target_lid:{t.label}:{t.prob:.2f}", r["_tr"])
                else:
                    keep.append(r)
            pcand = keep
        for r in pcand:
            key = (r["bucket"], r["source"], exact_key(r["_text"]), exact_key(r["_tr"]), r["translation_lang"])
            if key in seen_pairs:
                drop(r, "pair_dup", "exact_pair_dup", r["_text"])
                continue
            seen_pairs.add(key)
            d = {k: r.get(k) for k in OUT_FIELDS}
            d.update(text=r["_text"], lang="kam", translation=r["_tr"], translation_lang=r["translation_lang"])
            if r.get("extra"):
                d["extra"] = r["extra"]
            par_out[(r["bucket"], r["source"])].append(d)
        batch.clear()

    n = 0
    for rec in read_jsonl(raw):
        batch.append(rec)
        n += 1
        if len(batch) >= BATCH:
            flush()
    if batch:
        flush()
    log.info("%-18s processed %d raw records", info.id, n)


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def _public(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "priority"}


def drop_contained(docs: list[dict]) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Drop single-line docs whose text is a whole line of a longer multi-line doc
    (e.g. Bible verse pairs whose verses already occur in a full chapter document)."""
    line_owner: dict[str, str] = {}
    for d in docs:
        if "\n" in d["text"]:
            for line in d["text"].split("\n"):
                line_owner.setdefault(exact_key(line), d["id"])
    kept, dropped = [], []
    for d in docs:
        owner = line_owner.get(exact_key(d["text"])) if "\n" not in d["text"] else None
        if owner and owner != d["id"]:
            dropped.append((d, f"contained_in:{owner}"))
        else:
            kept.append(d)
    return kept, dropped


def _merge_json(path: Path, update: dict) -> dict:
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    old.update(update)
    path.write_text(json.dumps(old, indent=1, ensure_ascii=False), encoding="utf-8")
    return old


def run(buckets: tuple[str, ...] = ("main", "unverified")) -> dict:
    """Build the given buckets. ("unverified",) alone rebuilds data/unverified/ without
    touching the main corpus (used when an unverified source is added)."""
    config.ensure_dirs()
    full = set(buckets) == {"main", "unverified"}
    lid = LanguageIdentifier()
    tlid = TargetLanguageIdentifier(lid)
    drop = DropLog(config.LOGS / ("drops.jsonl.gz" if full else f"drops_{'_'.join(buckets)}.jsonl.gz"))
    seen_mono = {"main": {}, "unverified": {}}
    mono_out = {"main": [], "unverified": []}
    par_out: dict = defaultdict(list)
    seen_pairs: set = set()
    mods = sorted((m for m in sources.all_sources() if m.INFO.bucket in buckets), key=lambda m: m.INFO.priority)
    for mod in mods:
        process_source(mod, lid, drop, seen_mono, seen_pairs, mono_out, par_out, tlid)

    hasher = MinHasher()
    report = {"lid_backend": lid.backend}
    for bucket in buckets:
        docs = mono_out[bucket]
        if bucket in config.CONTAINMENT_DEDUP_BUCKETS:
            docs, contained = drop_contained(docs)
            for d, why in contained:
                drop({**d, "bucket": bucket}, "contained_dup", why, d["text"])
            report[f"{bucket}_contained_dropped"] = len(contained)
        log.info("[%s] near-dedup over %d docs", bucket, len(docs))
        kept, dropped = dedup_docs(docs, config.NEAR_DUP_THRESHOLD, hasher)
        for d, why in dropped:
            drop({**d, "bucket": bucket}, "near_dup" if why.startswith("near") else "exact_dup", why, d["text"])
        for d in kept:
            g = assign_genre(d)
            if g != d["genre"]:
                d.setdefault("extra", {})["genre_source"] = d["genre"]
                d["genre"] = g
        mono_out[bucket] = kept
        report[f"{bucket}_after_dedup"] = len(kept)

    if "main" in buckets:
        splits, sdropped, moved = assign_splits(mono_out["main"], hasher=hasher)
        for d, why in sdropped:
            drop({**d, "bucket": "main"}, "split_leak", why, d["text"])
        report["split_moved_to_train"] = moved
        report["split_dropped_benchmark_neardup"] = len(sdropped)
        for name, docs in splits.items():
            docs.sort(key=lambda d: (d["source"], d["id"]))
            n = write_jsonl(config.MONO / f"{name}.jsonl", (_public(d) for d in docs))
            report[f"mono_{name}"] = n
            log.info("wrote %s: %d docs", name, n)
        with open(config.MONO / "train.txt", "w", encoding="utf-8", newline="\n") as f:
            for d in splits["train"]:
                f.write(" ".join(d["text"].split()) + "\n")
        heldout = {exact_key(d["text"]): name for name in ("dev", "test") for d in splits[name]}
    else:
        heldout = {exact_key(d["text"]): name for name in ("dev", "test")
                   if (config.MONO / f"{name}.jsonl").exists() for d in read_jsonl(config.MONO / f"{name}.jsonl")}

    if "unverified" in buckets:
        report["unverified_mono"] = write_jsonl(config.UNVERIFIED / "monolingual.jsonl",
                                                (_public(d) for d in mono_out["unverified"]))

    # ---- parallel (flag pairs whose Kikamba side is a dev/test monolingual doc)
    stale = (list(config.PARALLEL.glob("*.jsonl*")) if "main" in buckets else []) + (
        list(config.UNVERIFIED.glob("parallel_*.jsonl*")) if "unverified" in buckets else [])
    for f in stale:
        f.unlink()
    by_file: dict = defaultdict(list)
    for (bucket, src), rows in par_out.items():
        for r in rows:
            h = heldout.get(exact_key(r["text"]))
            if h:
                r["mono_split"] = h
        path = config.PARALLEL / f"{src}.jsonl" if bucket == "main" else config.UNVERIFIED / f"parallel_{src}.jsonl"
        by_file[path].extend(rows)
    for path, rows in by_file.items():
        if len(rows) > config.PARALLEL_SHARD_ROWS:  # e.g. OPUS-NLLB: gzip shards stay under GitHub's 100 MB limit
            n, _ = write_jsonl_gz_shards(path.with_suffix(""), rows, config.PARALLEL_SHARD_ROWS)
        else:
            n = write_jsonl(path, rows)
        report[f"parallel:{path.parent.name}/{path.name}"] = n

    summary = drop.close()
    if full:
        (config.LOGS / "drop_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False),
                                                       encoding="utf-8")
        (config.LOGS / "build_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    else:
        _merge_json(config.LOGS / "drop_summary.json", summary)
        report = _merge_json(config.LOGS / "build_report.json", report)
    log.info("build report: %s", report)
    return report
