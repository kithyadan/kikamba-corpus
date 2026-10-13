"""`corpus` command-line entry point: fetch | build | tokenize | stats | all | sources."""
from __future__ import annotations

import argparse
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    p = argparse.ArgumentParser(prog="corpus", description="Kikamba corpus pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="download raw data from every source")
    f.add_argument("--sources", help="comma-separated source module names (default: all)")
    f.add_argument("--force", action="store_true", help="re-fetch even if raw file exists")
    b = sub.add_parser("build", help="clean, filter, dedup, split -> data/monolingual, data/parallel")
    b.add_argument("--only-unverified", action="store_true",
                   help="rebuild data/unverified/ only (main corpus untouched)")
    t = sub.add_parser("tokenize", help="train SentencePiece BPE tokenizers on train.txt")
    t.add_argument("--vocab", default="8000,16000")
    sub.add_parser("stats", help="write stats/stats.json + stats/STATS.md")
    sub.add_parser("all", help="fetch + build + tokenize + stats")
    sub.add_parser("build-personal", help="PRIVATE USE: train split + deduped unverified bucket -> "
                                          "~/kikamba-personal/ (outside the repo), plus tokenizers")
    sub.add_parser("sources", help="list sources")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt="%H:%M:%S")

    if a.cmd in ("fetch", "all"):
        from . import fetch, models
        models.ensure_models()
        names = a.sources.split(",") if getattr(a, "sources", None) else None
        fetch.run(names, force=getattr(a, "force", False))
    if a.cmd in ("build", "all"):
        from . import build
        build.run(("unverified",) if getattr(a, "only_unverified", False) else ("main", "unverified"))
    if a.cmd in ("tokenize", "all"):
        from .tokenizer import train
        train.run([int(v) for v in getattr(a, "vocab", "8000,16000").split(",")])
    if a.cmd in ("stats", "all"):
        from . import stats
        stats.run()
    if a.cmd == "build-personal":
        from . import personal
        from .tokenizer import train
        personal.run()
        train.run([8000, 16000], input_path=personal.PERSONAL / "train_all.txt",
                  out_dir=personal.PERSONAL_TOKENIZERS, name="kam_bpe_all")
    if a.cmd == "sources":
        from . import sources
        for m in sources.all_sources():
            i = m.INFO
            print(f"{i.id:18s} [{i.bucket}] {i.license}  <{i.url}>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
