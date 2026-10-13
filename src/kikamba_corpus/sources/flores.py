"""FLORES-200 kam_Latn dev/devtest (+ eng_Latn, swh_Latn), via the ungated mteb/flores mirror.

The canonical tarball on dl.fbaipublicfiles.com is disallowed by that host's robots.txt,
and facebook/flores + openlanguagedata/flores_plus are gated, so we use mteb/flores
(same CC-BY-SA-4.0 content). These rows are a benchmark: build routes them to dev/test
only (never train) to avoid contaminating FLORES evaluation.
"""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "mteb/flores"
SPLITS = {"dev": "dev.parquet", "devtest": "devtest.parquet"}

INFO = SourceInfo(
    id="flores200",
    name="FLORES-200 (kam_Latn, dev + devtest)",
    url="https://github.com/facebookresearch/flores/tree/main/flores200",
    license="CC-BY-SA-4.0",
    genre="wiki-news",
    curated=True,
    priority=1,
    tags=("benchmark",),
)


def fetch():
    for split, path in SPLITS.items():
        for i, row in enumerate(hf_parquet_rows(REPO, path, ["kam_Latn", "eng_Latn", "swh_Latn"])):
            extra = {"flores_split": split, "flores_index": i, "benchmark": True}
            yield record(INFO, row["kam_Latn"], key=(split, i, "eng"), kind="both",
                         translation=row["eng_Latn"], translation_lang="eng", extra=extra)
            yield record(INFO, row["kam_Latn"], key=(split, i, "swh"), kind="parallel",
                         translation=row["swh_Latn"], translation_lang="swh", extra=extra)
