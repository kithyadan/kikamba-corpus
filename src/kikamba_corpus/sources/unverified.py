"""Sources whose upstream licence is unclear -> data/unverified/ only (never in train.txt).

* knox_bible     31k English/Kikamba Bible verse pairs. Tagged CC-BY-NC on HF, but the Kikamba
                 Bible text is (c) Bible Society of Kenya; the uploader cannot relicense it.
* mt560_kam      MT560 en-kam pairs; content is jw.org / JW300-derived (Watch Tower copyright).
* jonathan_kamba 51k en-kam pairs, no licence, no provenance statement (content looks JW-derived).
* glot500_kam    Glot500-c kam_Latn; licence "other" (mix of FLORES, Bloom, Bible, ...).
* dcad2000_kam   DCAD-2000 kam_Latn (MaLA/Glot500-derived); licence "other".
"""
import csv
import sys

import pyarrow as pa
import pyarrow.parquet as pq

from .base import SourceInfo, hf_file, record

INFO = SourceInfo(
    id="unverified",
    name="Unverified-licence bucket",
    url="https://huggingface.co/datasets?language=language:kam",
    license="UNVERIFIED",
    genre="mixed",
    bucket="unverified",
    priority=90,
)


def _info(sub: str, url: str, lic: str, genre: str) -> SourceInfo:
    return SourceInfo(id=sub, name=sub, url=url, license=lic, genre=genre, bucket="unverified", priority=90)


def _knox():
    repo = "KnoxDevelopers/english_kikamba_pair_sentences"
    info = _info("knox_bible", f"https://huggingface.co/datasets/{repo}",
                 "UNVERIFIED (HF card: CC-BY-NC-4.0; Kikamba Bible (c) Bible Society of Kenya)", "religious")
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    with open(hf_file(repo, "kikamba_dataset.csv"), encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            yield record(info, row["Kikamba"], key=i, kind="both",
                         translation=row["English"], translation_lang="eng")


def _pairs(sub, repo, path, lic, kam_col, eng_col):
    info = _info(sub, f"https://huggingface.co/datasets/{repo}", lic, "religious")
    for i, row in enumerate(pq.read_table(hf_file(repo, path), columns=[kam_col, eng_col]).to_pylist()):
        yield record(info, row[kam_col] or "", key=(path, i), kind="both",
                     translation=row[eng_col], translation_lang="eng")


def _glot500():
    repo = "cis-lmu/Glot500"
    info = _info("glot500_kam", f"https://huggingface.co/datasets/{repo}", "UNVERIFIED (Glot500-c: 'other')", "mixed")
    with pa.memory_map(str(hf_file(repo, "kam_Latn/train/data-00000-of-00001.arrow"))) as src:
        t = pa.ipc.open_stream(src).read_all()
    for i, row in enumerate(t.to_pylist()):
        yield record(info, row["text"], key=i, extra={"glot500_dataset": row.get("dataset")})


def _dcad():
    import json
    repo = "openbmb/DCAD-2000"
    info = _info("dcad2000_kam", f"https://huggingface.co/datasets/{repo}", "UNVERIFIED (DCAD-2000: 'other')", "mixed")
    for i, line in enumerate(open(hf_file(repo, "kam_Latn/mala_000001_keep.jsonl"), encoding="utf-8")):
        row = json.loads(line)
        yield record(info, row["text"], key=i, extra={"upstream_source": row.get("source")})


def fetch():
    yield from _knox()
    yield from _pairs("mt560_kam", "michsethowusu/english-kamba_sentence-pairs_mt560",
                      "data/train-00000-of-00001.parquet", "UNVERIFIED (HF card CC-BY-4.0; JW300/jw.org-derived)",
                      "kam", "eng")
    for split in ("train", "validation", "test"):
        yield from _pairs("jonathan_kamba", "JonathanAI23/kamba_full", f"data/{split}-00000-of-00001.parquet",
                          "UNVERIFIED (no licence on HF card)", "kamba", "english")
    yield from _glot500()
    yield from _dcad()
