"""FinePDFs kam_Latn subset (text extracted from PDFs found in Common Crawl)."""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "HuggingFaceFW/finepdfs"
FILES = ["data/kam_Latn/train/000_00000.parquet"]

INFO = SourceInfo(
    id="finepdfs",
    name="FinePDFs (kam_Latn)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="ODC-By-1.0 (dataset); underlying PDF text subject to Common Crawl Terms of Use",
    genre="pdf",
    priority=45,
)


def fetch():
    for path in FILES:
        for row in hf_parquet_rows(REPO, path, ["text", "id", "url"]):
            yield record(INFO, row["text"], key=row["id"], url=row["url"], extra={"hf_file": path})
