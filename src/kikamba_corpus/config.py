"""Project-wide paths and constants."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("KIKAMBA_ROOT", Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"
RAW = DATA / "raw"
CACHE = DATA / "cache"
MONO = DATA / "monolingual"
PARALLEL = DATA / "parallel"
UNVERIFIED = DATA / "unverified"
LOGS = ROOT / "logs"
MODELS = ROOT / "models"
TOKENIZER_DIR = ROOT / "tokenizer_models"
STATS_DIR = ROOT / "stats"

# Set KIKAMBA_CONTACT (e.g. an e-mail) locally so site operators can reach you; kept out of the repo.
CONTACT = os.environ.get("KIKAMBA_CONTACT", "contact: see project README")
USER_AGENT = (
    "KikambaCorpusBuilder/0.1 (low-resource language research corpus; "
    f"{CONTACT}; respects robots.txt, >=2s between requests)"
)
MIN_REQUEST_INTERVAL = 2.0  # seconds between requests to the same host

GLOTLID_MODEL = MODELS / "glotlid_v3.bin"
GLOTLID_URL = "https://huggingface.co/cis-lmu/glotlid/resolve/main/model_v3.bin"
LID176_MODEL = MODELS / "lid.176.bin"
# dl.fbaipublicfiles.com disallows all robots, so use the HF mirror of the same file.
LID176_URL = "https://huggingface.co/julien-c/fasttext-language-id/resolve/main/lid.176.bin"

TARGET_LABEL = "kam_Latn"

# Filtering thresholds (documented in REPORT.md)
MIN_CHARS = 15
MIN_WORDS = 3
MIN_LETTER_RATIO = 0.6
LID_THRESHOLD = 0.5  # web / mined / unknown-provenance sources
LID_THRESHOLD_CURATED = 0.2  # curated sources: kam in top-3 at >= this counts as Kikamba
LINE_DROP_PROB = 0.8  # drop a line inside a doc if confidently another language
LINE_DROP_MIN_CHARS = 40

# Dedup / split
NEAR_DUP_THRESHOLD = 0.8
SPLIT_LEAK_THRESHOLD = 0.7
# Drop single-line docs that are verbatim lines of a longer doc (verse pairs vs full Bible chapters).
CONTAINMENT_DEDUP_BUCKETS = ("unverified",)
NUM_PERM = 128
SHINGLE_K = 5
DEV_FRAC = 0.01
TEST_FRAC = 0.01
SEED = 13
PARALLEL_SHARD_ROWS = 250_000  # larger parallel sets are written as gzip shards


def ensure_dirs() -> None:
    for p in (RAW, CACHE, MONO, PARALLEL, UNVERIFIED, LOGS, MODELS, TOKENIZER_DIR, STATS_DIR):
        p.mkdir(parents=True, exist_ok=True)
