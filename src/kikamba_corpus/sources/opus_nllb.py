"""OPUS NLLB mined bitext: en-kam and kam-sw (LASER-mined from Common Crawl; noisy)."""
import io
import zipfile

from .. import config
from ..net import session
from .base import SourceInfo, record

PAIRS = {
    # zip url, kam member suffix, other member suffix, other lang
    "en-kam": ("https://object.pouta.csc.fi/OPUS-NLLB/v1/moses/en-kam.txt.zip", ".kam", ".en", "eng"),
    "kam-sw": ("https://object.pouta.csc.fi/OPUS-NLLB/v1/moses/kam-sw.txt.zip", ".kam", ".sw", "swh"),
}

INFO = SourceInfo(
    id="opus_nllb",
    name="OPUS NLLB v1 mined bitext (en-kam, kam-sw)",
    url="https://opus.nlpl.eu/NLLB/corpus/version/NLLB",
    license="ODC-By-1.0 (NLLB mined data, released by Meta/AllenAI via OPUS); subject to Common Crawl Terms of Use",
    genre="web",
    priority=60,
    notes="Automatically mined; many Kikamba-side lines are misidentified or misaligned, hence strict LID + pair filters.",
)


def fetch():
    for pair, (url, kam_suf, oth_suf, oth_lang) in PAIRS.items():
        z = session().download(url, config.CACHE / "opus" / f"NLLB-{pair}.txt.zip")
        with zipfile.ZipFile(z) as zf:
            names = zf.namelist()
            kam_name = next(n for n in names if n.endswith(kam_suf))
            oth_name = next(n for n in names if n.endswith(oth_suf))
            with zf.open(kam_name) as fk, zf.open(oth_name) as fo:
                kr = io.TextIOWrapper(fk, encoding="utf-8", errors="replace")
                orr = io.TextIOWrapper(fo, encoding="utf-8", errors="replace")
                for i, (k, o) in enumerate(zip(kr, orr)):
                    k, o = k.strip(), o.strip()
                    if not k:
                        continue
                    yield record(INFO, k, key=(pair, i), url=url, kind="both",
                                 translation=o, translation_lang=oth_lang,
                                 extra={"pair": pair, "line": i})
