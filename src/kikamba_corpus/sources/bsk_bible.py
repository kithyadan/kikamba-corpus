"""Kikamba Bible, Bible Society of Kenya 2011 ("MBIVILIA ŨVOO MŨSEO"), from a local XML file.

The XML's own header says "BIBLE SOCIETY OF KENYA © 2011" (text taken from bible.com/bible/2773),
so this is all-rights-reserved text: it goes to the UNVERIFIED bucket only, never to train.txt,
and must not be redistributed. One document per chapter, one verse per line.

Path: $KIKAMBA_BSK_BIBLE, else ~/Downloads/KambaBible.xml (copied into data/cache/local/).
"""
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from .. import config
from .base import SourceInfo, record

DEFAULT = Path.home() / "Downloads" / "KambaBible.xml"

INFO = SourceInfo(
    id="bsk_bible_2011",
    name="Kikamba Bible (Bible Society of Kenya 2011), local XML",
    url="https://www.bible.com/bible/2773",
    license="(c) Bible Society of Kenya 2011 - all rights reserved; NOT redistributable",
    genre="religious",
    bucket="unverified",
    curated=True,
    priority=80,  # wins over the knox_bible verse pairs (same translation) in dedup
)


def _local_copy() -> Path | None:
    src = Path(os.environ.get("KIKAMBA_BSK_BIBLE", DEFAULT))
    dest = config.CACHE / "local" / "KambaBible.xml"
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
    return dest if dest.exists() else None


def fetch():
    path = _local_copy()
    if path is None:
        return  # logged as "empty" by the fetch runner
    root = ET.parse(path).getroot()
    for testament in root.iter("testament"):
        for book in testament.iter("book"):
            bn = int(book.get("number"))
            for chapter in book.iter("chapter"):
                cn = int(chapter.get("number"))
                verses = [(v.text or "").strip() for v in chapter.iter("verse")]
                text = "\n".join(v for v in verses if v)
                if text:
                    yield record(INFO, text, key=(bn, cn),
                                 url=f"https://www.bible.com/bible/2773/{bn}.{cn}",
                                 extra={"book_number": bn, "chapter": cn, "verses": len(verses),
                                        "testament": testament.get("name")})
