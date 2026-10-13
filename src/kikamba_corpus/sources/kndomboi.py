"""Small CC0 Kikamba texts uploaded by HF user kndomboi (a short story and its sentences)."""
import csv

from .base import SourceInfo, hf_file, record

FILES = [
    ("kndomboi/kikamba-story-katiwa-cc0", "Kikamba_story.csv"),
    ("kndomboi/kikamba-sentences-500-cc0", "kikamba_sentences.csv"),
]

INFO = SourceInfo(
    id="kndomboi_cc0",
    name="kndomboi CC0 Kikamba story + sentences",
    url="https://huggingface.co/kndomboi",
    license="CC0-1.0",
    genre="narrative",
    curated=True,
    priority=30,
)


def fetch():
    for repo, path in FILES:
        p = hf_file(repo, path)
        with open(p, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        body = [r[0] for r in rows[1:] if r and r[0].strip()]
        # The sentence file is one CSV row padded with runs of spaces between sentences.
        text = "\n".join(body)
        yield record(INFO, text, key=(repo, path), url=f"https://huggingface.co/datasets/{repo}")
