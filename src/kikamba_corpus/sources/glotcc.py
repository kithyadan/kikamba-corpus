"""GlotCC-V1 kam-Latn (Common Crawl, GlotLID-labelled)."""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "cis-lmu/GlotCC-V1"
FILES = ["v1.0/kam-Latn/kam-Latn_0.parquet"]

INFO = SourceInfo(
    id="glotcc",
    name="GlotCC-V1 (kam-Latn)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="CC0-1.0 (GlotCC packaging); underlying web text subject to Common Crawl Terms of Use",
    genre="web",
    priority=43,
)


def fetch():
    for path in FILES:
        for row in hf_parquet_rows(REPO, path, ["content", "warc-target-uri", "warc-record-id"]):
            yield record(INFO, row["content"], key=row["warc-record-id"], url=row["warc-target-uri"],
                         extra={"hf_file": path})
