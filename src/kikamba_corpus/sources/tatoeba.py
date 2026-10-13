"""Tatoeba: Kikamba sentences (per-language export) + en-kam pairs (OPUS Tatoeba)."""
import bz2
import io
import zipfile

from .. import config
from ..net import session
from .base import SourceInfo, record

SENTENCES_URL = "https://downloads.tatoeba.org/exports/per_language/kam/kam_sentences.tsv.bz2"
OPUS_URL = "https://object.pouta.csc.fi/OPUS-Tatoeba/v2026-07-08/moses/en-kam.txt.zip"

INFO = SourceInfo(
    id="tatoeba",
    name="Tatoeba (kam)",
    url="https://tatoeba.org/en/sentences/search?from=kam",
    license="CC-BY-2.0-FR",
    genre="conversational",
    curated=True,
    priority=10,
)


def fetch():
    p = session().download(SENTENCES_URL, config.CACHE / "tatoeba" / "kam_sentences.tsv.bz2")
    for line in bz2.open(p, "rt", encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 3 and parts[1] == "kam":
            sid = parts[0]
            yield record(INFO, parts[2], key=sid, url=f"https://tatoeba.org/en/sentences/show/{sid}")
    z = session().download(OPUS_URL, config.CACHE / "tatoeba" / "opus-en-kam.txt.zip")
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        kam = io.TextIOWrapper(zf.open(next(n for n in names if n.endswith(".kam"))), encoding="utf-8")
        eng = io.TextIOWrapper(zf.open(next(n for n in names if n.endswith(".en"))), encoding="utf-8")
        for i, (k, e) in enumerate(zip(kam, eng)):
            yield record(INFO, k.strip(), key=("opus", i), url=OPUS_URL, kind="parallel",
                         translation=e.strip(), translation_lang="eng")
