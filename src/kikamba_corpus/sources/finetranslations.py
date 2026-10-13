"""FineTranslations kam_Latn: FineWeb-2 Kikamba docs + machine translation into English.

The Kikamba side is original web text (used as monolingual + parallel source side);
the English side is MACHINE-GENERATED, which is flagged in every record.
"""
from .base import SourceInfo, hf_parquet_rows, record

REPO = "HuggingFaceFW/finetranslations"
FILES = ["data/kam_Latn/000_00000.parquet"]

INFO = SourceInfo(
    id="finetranslations",
    name="FineTranslations (kam_Latn -> eng, machine-translated target)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="ODC-By-1.0 (dataset); source text subject to Common Crawl Terms of Use",
    genre="web",
    priority=41,
)


def fetch():
    for path in FILES:
        for row in hf_parquet_rows(REPO, path, ["id", "og_full_text", "translated_text", "url"]):
            yield record(INFO, row["og_full_text"], key=row["id"], url=row["url"], kind="both",
                         translation=row["translated_text"], translation_lang="eng",
                         extra={"translation_origin": "machine", "hf_file": path})
