"""HPLT v2.0 cleaned, kam_Latn (Internet Archive + Common Crawl)."""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "HPLT/HPLT2.0_cleaned"
FILES = ["kam_Latn/train-00000-of-00001.parquet"]

INFO = SourceInfo(
    id="hplt2",
    name="HPLT v2.0 cleaned (kam_Latn)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="CC0-1.0 (HPLT packaging); underlying web text subject to Internet Archive / Common Crawl terms",
    genre="web",
    priority=42,
)


def fetch():
    for path in FILES:
        for row in hf_parquet_rows(REPO, path, ["id", "u", "text", "filter"]):
            if row.get("filter") not in (None, "keep"):
                continue
            yield record(INFO, row["text"], key=row["id"], url=row["u"], extra={"hf_file": path})
