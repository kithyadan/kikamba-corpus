"""FLEURS kam_ke transcripts (read-speech recordings of FLORES sentences). Text only; no audio."""
from .base import SourceInfo, hf_file, record

REPO = "google/fleurs"
SPLITS = ["train", "dev", "test"]

INFO = SourceInfo(
    id="fleurs",
    name="FLEURS (kam_ke) transcriptions",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="CC-BY-4.0",
    genre="wiki-news",
    curated=True,
    priority=5,
    tags=("benchmark-derived",),
)


def fetch():
    seen = set()
    for split in SPLITS:
        p = hf_file(REPO, f"data/kam_ke/{split}.tsv")
        for line in open(p, encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            fid, raw = parts[0], parts[2]
            if fid in seen:  # several speakers read the same sentence
                continue
            seen.add(fid)
            yield record(INFO, raw, key=fid, extra={"fleurs_id": fid, "fleurs_split": split})
