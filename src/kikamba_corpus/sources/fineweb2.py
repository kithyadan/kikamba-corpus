"""FineWeb-2 kam_Latn subset (Common Crawl, GlotLID-labelled, filtered)."""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "HuggingFaceFW/fineweb-2"
FILES = ["data/kam_Latn/train/000_00000.parquet", "data/kam_Latn/test/000_00000.parquet"]

INFO = SourceInfo(
    id="fineweb2",
    name="FineWeb-2 (kam_Latn)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="ODC-By-1.0 (dataset); underlying web text subject to Common Crawl Terms of Use",
    genre="web",
    priority=40,
    notes="The kam_Latn_removed split (docs FineWeb-2's own quality filters rejected) is deliberately not used.",
)


def fetch():
    for path in FILES:
        for row in hf_parquet_rows(REPO, path, ["text", "id", "url", "date"]):
            yield record(INFO, row["text"], key=row["id"], url=row["url"],
                         extra={"crawl_date": str(row["date"]), "hf_file": path})
