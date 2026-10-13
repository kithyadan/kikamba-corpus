"""Run source fetchers -> data/raw/<source>.jsonl, logging outcomes to logs/fetch_log.jsonl."""
from __future__ import annotations

import datetime as dt
import logging
import time
import traceback

from . import config, sources
from .jsonl import JsonlAppender, write_jsonl

log = logging.getLogger(__name__)


def raw_path(module_info_id: str):
    return config.RAW / f"{module_info_id}.jsonl"


def run(names: list[str] | None = None, force: bool = False) -> list[dict]:
    config.ensure_dirs()
    results = []
    mods = [sources.load(n) for n in (names or sources.MODULES)]
    with JsonlAppender(config.LOGS / "fetch_log.jsonl") as flog:
        for mod in mods:
            info = mod.INFO
            out = raw_path(info.id)
            entry = {"source": info.id, "time": dt.datetime.now().isoformat(timespec="seconds")}
            if out.exists() and out.stat().st_size > 0 and not force:
                n = sum(1 for _ in open(out, encoding="utf-8"))
                entry.update(status="cached", records=n)
                log.info("%-18s cached (%d records)", info.id, n)
            else:
                t0 = time.time()
                try:
                    n = write_jsonl(out, mod.fetch())
                    entry.update(status="ok" if n else "empty", records=n, seconds=round(time.time() - t0, 1))
                    log.info("%-18s %s: %d records in %.0fs", info.id, entry["status"], n, time.time() - t0)
                    if n == 0:
                        out.unlink(missing_ok=True)
                except Exception as e:  # log and move on: never block the whole run on one source
                    entry.update(status="error", error=f"{type(e).__name__}: {e}",
                                 trace=traceback.format_exc(limit=3))
                    log.warning("%-18s ERROR %s", info.id, entry["error"])
                    out.with_suffix(".jsonl.part").unlink(missing_ok=True)
            flog.write(entry)
            results.append(entry)
    return results
