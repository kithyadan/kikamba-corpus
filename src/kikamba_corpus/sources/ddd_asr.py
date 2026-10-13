"""Digital Divide Data Kamba ASR (484h) — transcripts only, via the HF dataset-viewer API.

The full dataset is ~200 GB of Arrow shards with embedded audio; the dataset viewer has
indexed only a partial prefix, and only those rows are reachable without downloading
audio. Speaker names/ages/genders are deliberately NOT stored.
"""
from ..net import session
from .base import SourceInfo, record

DATASET = "Digital-Divide-Data/Kamba-ASR-Data-Subset-484H"
API = "https://datasets-server.huggingface.co"
PAGE = 100

INFO = SourceInfo(
    id="ddd_asr",
    name="Digital Divide Data Kamba ASR 484h (transcripts, partial)",
    url=f"https://huggingface.co/datasets/{DATASET}",
    license="CC-BY-4.0",
    genre="speech-transcript",
    curated=True,
    priority=20,
)


def fetch():
    size = session().get(f"{API}/size", params={"dataset": DATASET}).json()
    n = next(s["num_rows"] for s in size["size"]["splits"] if s["split"] == "train")
    for off in range(0, n, PAGE):
        r = session().get(f"{API}/rows", params={"dataset": DATASET, "config": "default", "split": "train",
                                                 "offset": off, "length": PAGE})
        for row in r.json().get("rows", []):
            d = row["row"]
            text = d.get("transcripts") or ""
            if not text.strip():
                continue
            yield record(INFO, text, key=(d.get("filename"), row["row_idx"]),
                         extra={"domain": d.get("domain"), "sub_domain": d.get("sub_domain"),
                                "theme": d.get("theme"), "sentence_id": d.get("sentence_id")})
