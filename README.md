# Kikamba (kam) corpus + tokenizer

A cleaned, deduplicated, licence-tracked Kikamba (Kamba, ISO 639-3 `kam`) text corpus for
language technology and linguistic research: machine translation, language identification,
spell-checking and keyboard tools, and vocabulary/orthography studies. It includes
Kikamba–English/Swahili parallel data and SentencePiece BPE subword models (8k, 16k).

**Final size (main corpus, 2026-09-26 build):** 48,859 documents · 150,240 sentences ·
**1,740,538 words** · 10,725,191 characters (`train.txt` = 11.3 MB).
Religious vs non-religious (by words): **60.1% / 39.9%**.
Parallel: **1,248,276 pairs** (1,156,532 kam–eng, 91,744 kam–swh). Unverified bucket (not in train):
51,846 docs / 1,644,826 words + 129,118 pairs.
Tokenizers: 16k BPE = 3.67 chars/token, 1.649 tokens/word on dev.

## Contents

```
data/monolingual/train.jsonl  dev.jsonl  test.jsonl   main corpus, one JSON doc per line
data/monolingual/train.txt                            train docs, one per line, no metadata
data/parallel/<source>.jsonl                          kam <-> eng / swh pairs (large sets as <source>-NNNNN.jsonl.gz shards)
data/unverified/                                      unclear / all-rights-reserved material (NOT in train.txt, gitignored)
tokenizer_models/kam_bpe_{8k,16k}.model|.vocab        SentencePiece BPE
tokenizer_models/tokenizer_report.json                compression, fertility, top tokens
stats/STATS.md, stats/stats.json                      counts per source / genre / split, vocab, characters
logs/drops.jsonl.gz, logs/drop_summary.json           every dropped doc / line / pair + reason
logs/fetch_log.jsonl, logs/build_report.json          fetch outcomes, build counts
REPORT.md                                             every autonomous decision, sources found vs skipped
DATASHEET.md                                          Datasheets-for-Datasets documentation
```

**Record fields:** `id, text, source, url, license, genre, lang, date_fetched, lang_declared,
lid_prob, extra`. Parallel records add `translation, translation_lang`, plus `mono_split` if the
Kikamba side is a monolingual dev/test doc.

## Per-source counts and licences (monolingual)

| source | docs | words | share of words | genre(s) | licence | bucket |
|---|---:|---:|---:|---|---|---|
| [fineweb2](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) | 1,450 | 590,476 | 33.9% | web | ODC-By-1.0 (dataset); underlying web text subject to Common Crawl Terms of Use | main |
| [opus_nllb](https://opus.nlpl.eu/NLLB/corpus/version/NLLB) | 41,770 | 550,408 | 31.6% | web | ODC-By-1.0 (NLLB mined data, released by Meta/AllenAI via OPUS); subject to Common Crawl Terms of Use | main |
| [finepdfs](https://huggingface.co/datasets/HuggingFaceFW/finepdfs) | 36 | 374,773 | 21.5% | pdf | ODC-By-1.0 (dataset); underlying PDF text subject to Common Crawl Terms of Use | main |
| [hplt2](https://huggingface.co/datasets/HPLT/HPLT2.0_cleaned) | 219 | 121,254 | 7.0% | web | CC0-1.0 (HPLT packaging); underlying web text subject to Internet Archive / Common Crawl terms | main |
| [ddd_asr](https://huggingface.co/datasets/Digital-Divide-Data/Kamba-ASR-Data-Subset-484H) | 3,301 | 45,293 | 2.6% | speech-transcript | CC-BY-4.0 | main |
| [flores200](https://github.com/facebookresearch/flores/tree/main/flores200) | 2,004 | 41,466 | 2.4% | wiki-news | CC-BY-SA-4.0 | main |
| [bloom](https://bloomlibrary.org/language:kam) | 26 | 8,527 | 0.5% | children-stories | CC-BY-NC-ND-4.0; CC-BY-NC-SA-4.0 | main |
| [glotstorybook](https://huggingface.co/datasets/cis-lmu/GlotStoryBook) | 45 | 8,055 | 0.5% | children-stories | CC-BY-4.0; CC-BY-NC-4.0 | main |
| [glotcc](https://huggingface.co/datasets/cis-lmu/GlotCC-V1) | 1 | 236 | 0.0% | web | CC0-1.0 (GlotCC packaging); underlying web text subject to Common Crawl Terms of Use | main |
| [tatoeba](https://tatoeba.org/en/sentences/search?from=kam) | 6 | 30 | 0.0% | conversational | CC-BY-2.0-FR | main |
| [kndomboi_cc0](https://huggingface.co/kndomboi) | 1 | 20 | 0.0% | narrative | CC0-1.0 | main |
| mt560_kam | 48,639 | 937,839 | – | religious/mixed | UNVERIFIED (see REPORT) | unverified |
| glot500_kam | 1,905 | 39,780 | – | religious/mixed | UNVERIFIED (see REPORT) | unverified |
| bsk_bible_2011 | 1,186 | 664,739 | – | religious/mixed | UNVERIFIED (see REPORT) | unverified |
| knox_bible | 116 | 2,468 | – | religious/mixed | UNVERIFIED (see REPORT) | unverified |

Parallel pairs per source: bloom: 134 eng, finetranslations: 1,435 eng, flores200: 2,009 eng / 2,009 swh, glotstorybook: 442 eng / 377 swh, opus_nllb: 1,152,502 eng / 89,358 swh, tatoeba: 10 eng.

Full tables (per genre, per split, top vocabulary, character inventory): `stats/STATS.md`.

## Quick start

```bash
uv sync --group dev          # Python 3.11, installs deps
export KIKAMBA_CONTACT="you@example.org"   # optional: contact put in the scraper User-Agent
uv run corpus all            # fetch -> build -> tokenize -> stats (downloads ~3 GB incl. LID models)
uv run pytest -q             # tests: cleaner, language filter, dedup/split
```
Or step by step: `corpus fetch [--sources a,b] [--force]`, `corpus build [--only-unverified]`,
`corpus tokenize [--vocab 8000,16000]`, `corpus stats`, `corpus sources`. On systems with `make`,
use `make all` or `make test`.

```python
import sentencepiece as spm
sp = spm.SentencePieceProcessor(model_file="tokenizer_models/kam_bpe_16k.model")
sp.encode("Mbaka hĩĩ nĩ yakwa.", out_type=str)
```

## Extended private corpus (not distributed)

`uv run corpus build-personal` writes `~/kikamba-personal/data/train_all.txt` (outside this repo; override
with `KIKAMBA_PERSONAL_DIR`): main train + deduplicated unverified bucket (75,222 docs, **2.88M words**), plus
subword models in `~/kikamba-personal/tokenizers/`. It contains all-rights-reserved text (BSK 2011 Bible,
jw.org-derived pairs), so it is for private study only and must not be redistributed. Near-copies of the
`dev`/`test` files were removed from it.

## Known issues

- **Religious skew.** Most openly available Kikamba web text is from jw.org. It's tagged
  `religious` but still dominates the web portion. Filter by `url` or `genre` if needed.
- **Web-text rights.** ODC-By / CC0 applies to the *dataset packaging* (FineWeb-2, FinePDFs,
  HPLT, GlotCC, NLLB). The underlying pages keep their own copyright (jw.org is © Watch Tower).
  This is standard practice for research corpora, but check it before any commercial use.
- **NC / ND licences.** All Bloom books and part of GlotStoryBook are CC-BY-NC(-SA/-ND). Drop them
  for commercial use: `license` contains `NC`.
- **LID confusion.** GlotLID mixes up Kikamba with Kikuyu, Tharaka, Embu/Meru and Swahili on short
  text, so some errors remain in both directions. It correctly removed Nilamba Bible text that HPLT
  had labelled `kam`.
- **Mined bitext noise.** OPUS-NLLB pairs are machine-mined. Many are loosely aligned, and the same
  Kikamba sentence is paired with many English sentences.
- **No open Kikamba Bible.** eBible.org / open.bible have none. The Bible Society of Kenya text
  (user-supplied XML, and the Knox verse pairs) is all-rights-reserved, so it's only in
  `data/unverified/`.
- **Orthography.** Diacritic use (ĩ ũ) varies by source. Some sources omit them entirely (e.g.
  FLORES kam is largely lowercase without tildes).
- **Partial ASR transcripts.** Only 5.6k DDD ASR transcripts are included (dataset-viewer prefix).

## Adding a source

1. Create `src/kikamba_corpus/sources/<name>.py` exposing:
   ```python
   from .base import SourceInfo, record, hf_file          # net.session() for other HTTP
   INFO = SourceInfo(id="myname", name="…", url="…", license="CC-BY-4.0", genre="news",
                     bucket="main",       # or "unverified" if the licence is unclear
                     curated=False,       # True = human-made Kikamba (relaxed LID)
                     priority=50)         # lower wins in dedup
   def fetch():
       for i, text in enumerate(...):
           yield record(INFO, text, key=i, url="…")      # kind="both", translation=…, translation_lang="eng" for pairs
   ```
   Always use `net.session()` or `hf_file()` for downloads (they enforce robots.txt and rate limits).
2. Add `"<name>"` to `MODULES` in `src/kikamba_corpus/sources/__init__.py`.
3. `uv run corpus fetch --sources <name> && uv run corpus build && uv run corpus stats`.
4. Record the licence decision in `REPORT.md`. If you checked a source and rejected it, add it to
   `SKIPPED` in `sources/__init__.py` with the reason.

## Licence

Code: MIT. Data: per-record licence (see `license` field and the table above). The collection is
not relicensed as a whole.
