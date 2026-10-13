# REPORT — Kikamba corpus build (autonomous run, 2026-09-26)

This file records every decision made without asking, what was found vs. skipped, the final
numbers, and what to add next. Numbers come from `stats/stats.json`, `logs/build_report.json`
and `logs/drop_summary.json` of the final run.

## 1. Final numbers

**Final size (main corpus, 2026-09-26 build):** 48,859 documents · 150,240 sentences ·
**1,740,538 words** · 10,725,191 characters (`train.txt` = 11.3 MB).
Religious vs non-religious (by words): **60.1% / 39.9%**.
Parallel: **1,248,276 pairs** (1,156,532 kam–eng, 91,744 kam–swh). Unverified bucket (not in train):
51,846 docs / 1,644,826 words + 129,118 pairs.
Tokenizers: 16k BPE = 3.67 chars/token, 1.649 tokens/word on dev.

| split | docs | sentences | words | chars |
|---|---:|---:|---:|---:|
| train | 45,949 | 144,860 | 1,663,771 | 10,258,366 |
| dev | 1,464 | 3,200 | 43,945 | 265,880 |
| test | 1,446 | 2,180 | 32,822 | 200,945 |
| **total** | **48,859** | **150,240** | **1,740,538** | **10,725,191** |

**Religious vs non-religious** (genre heuristic D27)

| | docs | words | share of words |
|---|---:|---:|---:|
| religious | 12,714 | 1,046,258 | 60.1% |
| non-religious | 36,145 | 694,280 | 39.9% |

**Per genre**

| genre | docs | words | share |
|---|---:|---:|---:|
| religious | 12,714 | 1,046,258 | 60.1% |
| web | 30,787 | 447,291 | 25.7% |
| pdf | 14 | 148,408 | 8.5% |
| speech-transcript | 3,275 | 44,869 | 2.6% |
| wiki-news | 1,997 | 41,304 | 2.4% |
| children-stories | 65 | 12,358 | 0.7% |
| conversational | 6 | 30 | 0.0% |
| narrative | 1 | 20 | 0.0% |

**Funnel (main bucket).** 2,005,549 raw records fetched across all sources (incl. unverified). Main-bucket drops
by stage: exact duplicates 1,383,539 · LID 345,322 · quality 87,162 ·
near-duplicates 1,241 · parallel-pair LID 477,169 · duplicate pairs 132,046 ·
pair quality 1,214 · foreign lines removed inside docs 795.
Split: 35 docs moved to train to break cross-split near-dup clusters,
0 dropped as near-dups of FLORES. All 2,009 FLORES pairs are kept in
`data/parallel/flores200.jsonl`; 2,004 unique FLORES sentences are in dev/test
(4 exact duplicates inside FLORES itself and one 2-word sentence are not).

**Unverified bucket** (`data/unverified/`, excluded from train.txt): bsk_bible_2011 1,186 docs / 664,739 words, mt560_kam 48,639 docs / 937,839 words, glot500_kam 1,905 docs / 39,780 words, knox_bible 116 docs / 2,468 words; pairs: jonathan_kamba 49,316, knox_bible 30,486, mt560_kam 49,316. Containment dedup dropped 30,244 Knox verses already present in BSK 2011 chapters. `jonathan_kamba` pairs are identical to `mt560_kam` (same count; their Kikamba sides were all exact duplicates).

**Tokenizers** (evaluated on dev, 1,464 docs, 265,880 chars):

| vocab | chars/token | bytes/token | tokens/word | pieces containing ĩ/ũ | byte-fallback pieces in 2k dev docs |
|---:|---:|---:|---:|---:|---:|
| 8k | 3.417 | 3.633 | 1.771 | 3,176 | 959 |
| 16k | 3.67 | 3.902 | 1.649 | 6,757 | 959 |

Most frequent 16k tokens: `.` `▁na` `,` `'` `▁wa` `▁` `1` `:` `▁kana` `▁ya` `▁nĩ` `a` `▁ma` `2` `?` `▁ala` `▁Ngai` `o` `-` `3` `▁kwa` `▁"` `▁Yeova` `)` `▁(` `▁andũ` `0` `▁o` `4` `▁sya`

## 2. Decisions made autonomously

### Project / tooling
| # | Decision | Why |
|---|---|---|
| D1 | Project lives in `~/kikamba-corpus`, not directly in the home directory | The working directory was the user's home folder (hundreds of unrelated files). |
| D2 | `uv` installed via `pip install --user uv`; Python 3.11 pinned (`>=3.11,<3.13`) | `uv` was not installed; `fasttext-wheel` has no 3.13/3.14 wheels. `numpy<2` pinned for fastText. |
| D3 | CLI `corpus {fetch,build,tokenize,stats,all,sources}` + a `Makefile` wrapper | `make` is not installed on this Windows machine, so the CLI is the primary entry point. |

### Access, robots.txt, licensing
| # | Decision | Why |
|---|---|---|
| D4 | All HTTP goes through `net.PoliteSession`: descriptive User-Agent with contact, robots.txt check per host, >=2 s between requests to the same host, retries with backoff | Task constraint. Hosts whose robots.txt is missing / returns an XML error (S3, OPUS object store, Bloom Parse API) are treated as "no policy". |
| D5 | FLORES-200 taken from the ungated `mteb/flores` mirror (same CC-BY-SA-4.0 text) | `dl.fbaipublicfiles.com` robots.txt is `Disallow: /`; `facebook/flores` and `openlanguagedata/flores_plus` are gated and no HF token is available. |
| D6 | fastText lid.176 taken from the HF mirror `julien-c/fasttext-language-id` | Same robots.txt block on `dl.fbaipublicfiles.com`. (One copy had been downloaded from there before the robots check; it was deleted and re-downloaded from HF.) |
| D7 | Main-corpus licence rule: CC / CC0 / ODC-By / open-government / explicitly open corpora, **including NC and ND variants** | The brief allows "redistribution *or research use*". NC/ND licences permit non-commercial research redistribution; every record carries its exact licence so users can filter (e.g. drop `NC`/`ND` for commercial use). |
| D8 | Web-derived open corpora (FineWeb-2, FinePDFs, HPLT v2, GlotCC, OPUS-NLLB) are in the main corpus | They are "explicitly open corpora" (ODC-By / CC0 packaging). Caveat recorded per record: underlying page text is subject to Common Crawl / Internet Archive terms, and a large share is jw.org (Watch Tower copyright). Filter on `url` if that matters for your use. |
| D9 | Unclear-licence material -> `data/unverified/`, never in `train.txt` | Task constraint. Contents: Knox Bible verse pairs, MT560 (JW300-derived), JonathanAI23 pairs (no licence), Glot500 and DCAD-2000 kam slices (licence "other"), and the BSK 2011 Bible XML supplied locally by the user. |
| D10 | The user-supplied `KambaBible.xml` goes to **unverified** | Its own header says `BIBLE SOCIETY OF KENYA © 2011` (bible.com/bible/2773): all rights reserved, so it can't go in the main corpus. It's kept as its own source (`bsk_bible_2011`, one doc per chapter) because it is by far the largest single Kikamba text. |
| D11 | DDD Kamba ASR: only the transcripts indexed by the HF dataset viewer (5,656 rows) are used; speaker name / age / gender are **not** stored | The remaining rows would require downloading ~200 GB of audio shards. Speaker metadata is personal data and isn't needed for a text corpus. |

### Cleaning (`clean/`)
| # | Decision | Why |
|---|---|---|
| D12 | NFC normalisation; `ftfy` mojibake repair; HTML stripped only when the text actually looks like HTML | Keeps ĩ Ĩ ũ Ũ as single precomposed code points. |
| D13 | Grave, macron and circumflex i/u (ì ī î, ù ū û and capitals) -> ĩ / ũ; acute í and ü untouched | Standard Kikamba marks neither tone nor length (long vowels are doubled), so these are keyboard substitutes. Found after the first build: ~80k chars, mostly in DDD ASR transcripts (`nī, andū, mūno, ūndū, Yesū`) plus the kndomboi CC0 text (graves). Without this, every such word would get separate tokenizer pieces. í/ü occur in foreign names. |
| D14 | Curly quotes/apostrophes (’ ‘ ʼ ´ ` “ ” « ») -> ASCII `'` / `"` | Kikamba uses the apostrophe inside words (ng'ombe, kĩw'ũ); one canonical form avoids splitting the vocabulary. |
| D15 | Boilerplate lines removed only if short (<=120 chars) and keyword-matched, or pure URL / e-mail / symbols; consecutive duplicate lines collapsed | Conservative, so real paragraphs mentioning e.g. "copyright" survive. Lines/sentence punctuation are never joined or split. |

### Filtering (`filter/`)
| # | Decision | Why |
|---|---|---|
| D16 | Quality gates: >=15 chars, >=3 words, letter ratio >=0.6, Latin share >=0.8, not repetitive (unique-line ratio, top-word share) | Removes fragments, tables and spam; every drop is logged with its reason. |
| D17 | GlotLID v3 primary. Web / mined / unknown sources: top-1 must be `kam_Latn` with p >= 0.5 | Standard confidence cut. GlotLID confuses Kikamba with Kikuyu (kik), Swahili (swh) and Tharaka (thk) on short or loanword-heavy text. |
| D18 | Curated human-made sources (Bloom, GlotStoryBook, Tatoeba, FLEURS, DDD ASR, kndomboi): reject only if another language is predicted with p >= 0.5 **and** kam is not in the top-3 with p >= 0.2 | Tests showed genuine short FLORES/Tatoeba Kikamba sentences get labels like `kin_Latn` p=0.25 or `swh_Latn` p=0.60 because of names and loanwords. For curated data, LID is a contamination check, not a gate. |
| D19 | FLORES-200 bypasses the LID gate entirely | It's a human-translated benchmark; the first build dropped 44 genuine FLORES sentences (28 predicted as Swahili). |
| D20 | Line-level LID inside multi-line docs: web docs drop lines >=40 chars predicted as another language with p >= 0.8; curated docs drop only lines predicted English/Swahili/French with p >= 0.9 | Removes embedded English licence paragraphs in Bloom/ASb books and English/Arabic lines in web/PDF docs without dropping whole documents. |
| D21 | Parallel pairs: both sides non-empty, not identical, letter ratio >=0.5, char-length ratio 0.2–5 (non-curated), Kikamba side passes D17, target side checked with **lid.176** | lid.176 is accurate for en/sw and ~50× faster than GlotLID (0.3 s vs 15 s per 20k lines); GlotLID on both sides of 1.85M pairs made the first build take 65 min. |
| D22 | LID results are cached by normalised text within a source | OPUS-NLLB repeats the same Kikamba line across many pairs; ~74% of its Kikamba lines are exact duplicates. Texts that normalise identically (case/punctuation) share one prediction. |
| D23 | lid.176 fallback (if GlotLID can't load): reject confident other-language predictions and require a Kikamba function-word/tilde-vowel score | lid.176 has no Kikamba label, so it can only reject. Not used in the final run (GlotLID loaded). |

### Dedup, genre, split
| # | Decision | Why |
|---|---|---|
| D24 | Exact dedup on a normalised key (lowercase, punctuation/whitespace removed, SHA-1); near-dedup with MinHash (128 perms, char 5-grams, CRC32 + universal hashing, LSH 16×8) at Jaccard >= 0.8 | Deterministic, no external service. Near-dup catches revisions/orthographic variants of the same text (e.g. Bible revisions, FLEURS vs FLORES spellings). |
| D25 | Source priority decides which copy survives: FLORES < FLEURS < Tatoeba < Bloom < GlotStoryBook < DDD ASR < kndomboi < FineWeb-2 < FineTranslations < HPLT < GlotCC < FinePDFs < OPUS-NLLB (lower wins) | Curated, better-attributed sources should own shared text; mined data last. |
| D26 | Containment dedup in the unverified bucket: single-line docs that are a verbatim line of a longer doc are dropped | 99.6% of the Knox verse pairs are verbatim verses of the BSK 2011 Bible; without this, the same translation would be counted twice. Knox pairs are still kept as parallel data. |
| D27 | Religious genre: explicit for Bible/Bible-story sources; for other docs, religious publisher domain in the URL (jw.org, bible.com, ...) or a density rule on unambiguous Kikamba religious terms (Yesũ, Yeova, Klĩsto, Mbivilia, Mwĩaĩi, malaika, satani) plus weaker terms (Ngai, -thaith-) | The brief asks for a religious/non-religious split; most web Kikamba is jw.org. The heuristic is transparent and the source genre is kept in `extra.genre_source`. |
| D28 | Split: FLORES dev -> dev, devtest -> test (never train); other docs hashed by id into 1% dev / 1% test / 98% train; then a second MinHash pass at Jaccard >= 0.7 moves cross-split clusters to train, or drops the non-benchmark members if a FLORES doc is in the cluster | No near-duplicates across splits, and FLORES stays an uncontaminated benchmark. |
| D29 | `train.txt` = one document per line, internal newlines replaced by spaces | As specified. For sentence-level sources (NLLB, FLORES, Tatoeba, ASR) one "document" is one sentence. |
| D30 | Parallel records whose Kikamba side is also a dev/test monolingual doc get `mono_split: dev|test` | Lets users avoid train/test leakage when mixing parallel and monolingual data. |

### Tokenizer
| # | Decision | Why |
|---|---|---|
| D31 | SentencePiece BPE, 8k and 16k, `character_coverage=0.9995`, `byte_fallback=True`, `normalization_rule_name=identity`, `split_digits=True`, max sentence length 65,536 bytes | Text is already NFC-normalised (identity keeps ĩ/ũ untouched); byte fallback avoids `<unk>` for stray characters; long web docs are not silently skipped by the trainer. |

### Personal-use training set (added after delivery, at the user's request)
| # | Decision | Why |
|---|---|---|
| D32 | `corpus build-personal` writes `~/kikamba-personal/{data,tokenizers}` (outside the repo; `KIKAMBA_PERSONAL_DIR`) = main train + unverified bucket | For the owner's private study only; licence restrictions matter most for redistribution. Kept outside the git repository (the main corpus is going to GitHub) and gitignored as a second guard. |
| D34 | Parallel sets > 250k pairs are written as gzip shards (`opus_nllb-0000N.jsonl.gz`, ~19 MB each); `data/unverified/` is gitignored; scraper contact comes from `KIKAMBA_CONTACT` | GitHub rejects files > 100 MB (opus_nllb.jsonl was 651 MB, 98.5 MB even gzipped). Unverified text must not be published. The User-Agent had contained the user's e-mail, which shouldn't be in a public repo. |
| D33 | Unverified docs are dropped if they're exact duplicates, or MinHash Jaccard >= 0.7 near-duplicates, of any main-corpus doc | Result: 29,273 of 51,846 unverified docs added (+1,213,708 words, so train goes from 1.66M to 2.88M words). 2,217 were exact copies of dev/test (Glot500 contains FLORES), and removing them keeps evaluation clean. 20,301 duplicated main train text. |

## 3. Sources found and used

| source | bucket | fetch status | raw records | kept (mono docs) | licence |
|---|---|---|---:|---:|---|
| [FLORES-200 (kam_Latn, dev + devtest)](https://github.com/facebookresearch/flores/tree/main/flores200) | main | ok | 4,018 | 2,004 | CC-BY-SA-4.0 |
| [FLEURS (kam_ke) transcriptions](https://huggingface.co/datasets/google/fleurs) | main | ok | 1,992 | 0 | CC-BY-4.0 |
| [Tatoeba (kam)](https://tatoeba.org/en/sentences/search?from=kam) | main | ok | 20 | 6 | CC-BY-2.0-FR |
| [Bloom Library (kam)](https://bloomlibrary.org/language:kam) | main | ok | 170 | 26 | CC-BY-NC-SA / CC-BY-NC-ND (per book, see record) |
| [GlotStoryBook (Global Storybooks / African Storybook, kam)](https://huggingface.co/datasets/cis-lmu/GlotStoryBook) | main | ok | 885 | 45 | CC-BY / CC-BY-NC (per story, see record) |
| [Digital Divide Data Kamba ASR 484h (transcripts, partial)](https://huggingface.co/datasets/Digital-Divide-Data/Kamba-ASR-Data-Subset-484H) | main | ok | 5,656 | 3,301 | CC-BY-4.0 |
| [kndomboi CC0 Kikamba story + sentences](https://huggingface.co/kndomboi) | main | ok | 2 | 1 | CC0-1.0 |
| [FineWeb-2 (kam_Latn)](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) | main | ok | 1,454 | 1,450 | ODC-By-1.0 (dataset); underlying web text subject to Common Crawl Terms of Use |
| [FineTranslations (kam_Latn -> eng, machine-translated target)](https://huggingface.co/datasets/HuggingFaceFW/finetranslations) | main | ok | 1,438 | 0 | ODC-By-1.0 (dataset); source text subject to Common Crawl Terms of Use |
| [HPLT v2.0 cleaned (kam_Latn)](https://huggingface.co/datasets/HPLT/HPLT2.0_cleaned) | main | ok | 1,183 | 219 | CC0-1.0 (HPLT packaging); underlying web text subject to Internet Archive / Common Crawl terms |
| [GlotCC-V1 (kam-Latn)](https://huggingface.co/datasets/cis-lmu/GlotCC-V1) | main | ok | 4 | 1 | CC0-1.0 (GlotCC packaging); underlying web text subject to Common Crawl Terms of Use |
| [FinePDFs (kam_Latn)](https://huggingface.co/datasets/HuggingFaceFW/finepdfs) | main | ok | 45 | 36 | ODC-By-1.0 (dataset); underlying PDF text subject to Common Crawl Terms of Use |
| [OPUS NLLB v1 mined bitext (en-kam, kam-sw)](https://opus.nlpl.eu/NLLB/corpus/version/NLLB) | main | ok | 1,852,257 | 41,770 | ODC-By-1.0 (NLLB mined data, released by Meta/AllenAI via OPUS); subject to Common Crawl Terms of Use |
| knox_bible | unverified | ok (part of `unverified`) | – | 116 | UNVERIFIED |
| mt560_kam | unverified | ok (part of `unverified`) | – | 48,639 | UNVERIFIED |
| jonathan_kamba | unverified | ok (part of `unverified`) | – | 0 | UNVERIFIED |
| glot500_kam | unverified | ok (part of `unverified`) | – | 1,905 | UNVERIFIED |
| dcad2000_kam | unverified | ok (part of `unverified`) | – | 0 | UNVERIFIED |
| [Kikamba Bible (Bible Society of Kenya 2011), local XML](https://www.bible.com/bible/2773) | unverified | ok | 1,188 | 1,186 | (c) Bible Society of Kenya 2011 - all rights reserved; NOT redistributable |

`dcad2000_kam` kept 0 docs: all its texts were exact/near duplicates of Glot500 / FLORES / Bloom.

## 4. Sources checked and skipped

| source | reason |
|---|---|
| [eBible.org](https://ebible.org/Scriptures/translations.csv) | No Kikamba (kam) edition listed in translations.csv (checked 2026-09-26). |
| [open.bible](https://open.bible) | No Kikamba resources found. |
| [Digital Bible Library](https://app.thedigitalbiblelibrary.org) | Kikamba Bible (Bible Society of Kenya) is not open-licensed; no open-access kam entry. Bible text only reachable via the unverified KnoxDevelopers verse pairs. |
| [Wikipedia / Wikimedia Incubator](https://incubator.wikimedia.org/wiki/Wp/kam) | No kam Wikipedia and no Wp/kam test wiki exists. |
| [Common Voice](https://commonvoice.mozilla.org/kam) | Locale 'kam' exists but is not contributable; no released sentence set. |
| [MasakhaNEWS](https://huggingface.co/datasets/masakhane/masakhanews) | No Kikamba subset. |
| [AfriBERTa corpus](https://huggingface.co/datasets/castorini/afriberta-corpus) | No Kikamba subset. |
| [AfroLM data](https://huggingface.co/datasets/bonadossou/afrolm_active_learning_dataset) | No Kikamba subset. |
| [NLLB-Seed](https://github.com/openlanguagedata/seed) | Gated on HF; Kikamba not among Seed languages. |
| [MADLAD-400 / MaLA monolingual](https://huggingface.co/datasets/allenai/MADLAD-400) | No kam subset. |
| [SIL bloom-lm (HF)](https://huggingface.co/datasets/sil-ai/bloom-lm) | Gated (needs HF token). Replaced by fetching Bloom Library directly (bloom source). |
| [FLORES+ / facebook/flores (HF)](https://huggingface.co/datasets/openlanguagedata/flores_plus) | Gated. Replaced by the ungated mteb/flores mirror (flores200 source). |
| [FLORES-200 tarball](https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz) | Host robots.txt is 'Disallow: /'. Replaced by mteb/flores. |
| [facebook/bouquet](https://huggingface.co/datasets/facebook/bouquet) | Gated (needs HF token). |
| [LughaGen Multilingual African Corpus](https://huggingface.co/datasets/LughaGen-Organization/LughaGen-Multilingual-African-Corpus) | Gated (needs HF token). |
| [FarmerlineML/kamba_dataset](https://huggingface.co/datasets/FarmerlineML/kamba_dataset) | Manually gated, no licence. |
| [thiomi/thiomi-5k](https://huggingface.co/datasets/thiomi/thiomi-5k) | No licence; ~1 GB speech parquet. |
| [NjeriKahoro/thiomi-multilingual-text](https://huggingface.co/datasets/NjeriKahoro/thiomi-multilingual-text) | No kam text files found beyond the thiomi speech set; not pursued. |
| [StoryWeaver](https://storyweaver.org.in/) | 14 Kikamba books found, but story text API returns 401 without login; mostly African Storybook translations already covered via GlotStoryBook/Bloom. |
| [African Storybook (direct)](https://www.africanstorybook.org/) | Reader is a JS app with no documented bulk/text endpoint; Kikamba ASb stories are covered via GlotStoryBook (Global-ASP) and Bloom. |
| [michsethowusu/*-kamba sentence pairs, kamba-sentiments/emotions](https://huggingface.co/michsethowusu) | Re-packagings of OPUS NLLB (duplicates of opus_nllb). Verified for kamba-sentiments-corpus: 26,389/26,389 unique texts occur verbatim on the OPUS NLLB kam side; labels are English-model (DistilBERT SST-2) projections, not Kikamba annotations. |
| [FineWeb-2 kam_Latn_removed](https://huggingface.co/datasets/HuggingFaceFW/fineweb-2) | Docs rejected by FineWeb-2 quality filters; excluded on quality grounds. |
| [xP3x / SIB-200 / Belebele-style derivatives](https://huggingface.co/datasets/CohereLabs/xP3x) | Derived from FLORES; duplicates of flores200. |
| [PanLex](https://huggingface.co/datasets/lbourdois/panlex) | Lexical translations (word lists), not running text; 1.2 GB CSV for a small kam slice. |
| [KambaBench-ASR](https://huggingface.co/datasets/lawmaluki/KambaBench-ASR) | Contains only documentation files, no text. |
| [DDD Kamba ASR (remaining rows)](https://huggingface.co/datasets/Digital-Divide-Data/Kamba-ASR-Data-Subset-484H) | Only the dataset-viewer-indexed prefix was fetched; the rest needs ~200 GB of audio shards. |
| [Swarthmore LING073 Kamba corpora (kam corpus, kam-eng parallel)](https://wikis.swarthmore.edu/ling073/Kamba) | Hosted on github.swarthmore.edu, which requires a Swarthmore login (HTTP 302 -> /login). |
| [Rosetta Project Kikamba Genesis (archive.org)](https://archive.org/details/rosettaproject_kam_gen-1) | Publisher United Bible Societies (1974), no licence in item metadata; OCR'd PDF of Genesis only. |
| [Ĩvuku ya Mboya kwa andũ Onthe (Book of Common Prayer, 1963)](https://mammana.org/bcp/kamba1963/) | SPCK 1963 edition incl. catechism; still in copyright with no open licence stated, and distributed as scanned PDFs (would need OCR). Good candidate if permission is obtained. |
| [Global-ASP Storybooks Kenya (kam)](https://global-asp.github.io/storybooks-kenya/stories/kam/) | Already covered: GlotStoryBook's global-asp/asp-source rows are these stories (47 kam stories fetched). |
| [Yukawa 1984, 'On the Nature of the Accent of Kamba Nouns' (Senri Ethnological Studies 15)](https://doi.org/10.15021/00003319) | English-language linguistics paper (~4.8k words); Kamba appears only as isolated tone-marked nouns with OCR errors; (c) National Museum of Ethnology, no open licence. Useful as a tone/lexicon reference, not corpus text. |
| [Kenyan government Kikamba publications](https://www.kenyalaw.org) | No Kikamba publications with an explicit open licence found. |

## 5. Suggested next sources (ranked by expected yield)

1. **Kikamba Bible with permission.** Ask the Bible Society of Kenya for a research/redistribution licence for the 2011
   text (already processed in `data/unverified/`). It would add ~665k words, as much as ~40% of the current main corpus.
2. **Remaining DDD Kamba ASR transcripts** (484 h, CC-BY-4.0). Stream the Arrow shards and keep only the
   `transcripts` column. Needs ~200 GB of bandwidth, but it's the largest open non-religious source and is conversational.
3. **Swarthmore LING073 Kamba corpora.** Ask the course maintainers for access or a licence.
4. **African Storybook (direct).** More Kikamba stories than the Global-ASP subset; needs an agreement or a
   supported export, because the reader is a JS app.
5. **Book of Common Prayer 1963 (SPCK, catechism).** Needs a permission request plus OCR.
6. **Kenyan county government / KNBS / NGO material in Kikamba** (health, agriculture, civic education) under open
   licences. None were found online; direct requests to Machakos/Kitui/Makueni counties could help.
7. **Gated HF datasets.** `sil-ai/bloom-lm`, `facebook/bouquet` and `LughaGen` need an HF token. Bloom is already covered directly;
   BOUQuET would add a small, high-quality multi-domain eval set.
8. **Common Voice `kam`.** The locale exists but isn't open for contribution yet. Contributing CC0 sentences there would grow
   both text and speech resources.
9. **Improve LID for Kamba vs Kikuyu/Tharaka/Embu.** Fine-tune a small classifier on this corpus (positives) and the
   logged drops (negatives) to recover genuine Kikamba that GlotLID rejected (see `logs/drops.jsonl.gz`).
