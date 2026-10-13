# Datasheet: Kikamba (kam) text corpus v0.1

Following *Datasheets for Datasets* (Gebru et al., 2021). Numbers are from the 2026-09-26 build;
see `stats/STATS.md` for the full tables.

## Motivation

**For what purpose was the dataset created?**
To give Kikamba (Kamba; ISO 639-3 `kam`; Bantu E55, spoken by ~4.7M people mainly in Machakos,
Kitui and Makueni counties, Kenya) a clean, openly licensed text resource for language technology
and linguistic research. Existing open Kikamba text is scattered across web crawls, mined bitext,
children's-book platforms and speech datasets; this corpus gathers it with per-document licences
and provenance, cleans and deduplicates it, and provides subword segmentation models.

**Who created it and on whose behalf? Who funded it?**
Built by an automated pipeline (Claude Code, Anthropic's coding agent) for the repository owner. No external
funding.

## Composition

**What do the instances represent?**
Monolingual instances are *documents*: a web page, a PDF, a children's book, a story, a Bible
chapter (unverified bucket only), or, for sentence-level sources (FLORES, OPUS-NLLB, Tatoeba,
ASR transcripts), a single sentence. Parallel instances are Kikamba sentence/segment pairs with
English or Swahili.

**How many instances?** Main corpus: 48,859 documents (1,740,538 words; train 45,949 /
dev 1,464 / test 1,446). Parallel: 1,248,276 pairs (1,156,532 kam–eng,
91,744 kam–swh). Unverified bucket: 51,846 documents (1,644,826 words).

**Sample or complete?** It's everything we could find that was licence-compatible and passed the language/quality filters.
Composition by words: fineweb2 33.9%, opus_nllb 31.6%, finepdfs 21.5%, hplt2 7.0%, ddd_asr 2.6%, flores200 2.4%; religious 60.1% vs non-religious 39.9%.

**Is there a label or target?** No labels. Each record has metadata: `id, text, source, url,
license, genre, lang, date_fetched, lang_declared, lid_prob, extra` (+ `translation`,
`translation_lang` for pairs).

**Is any information missing?**
- Only ~5.6k of the ~484 h DDD ASR transcripts (the rest needs ~200 GB of audio downloads).
- Book / chapter titles are not always preserved; Bloom and GlotStoryBook keep title and
  author/translator attribution in `extra`.
- No tone marking: Kikamba is written without tone, and so is this corpus.

**Relationships between instances?** `extra` holds FLORES index/split, Bloom book id,
GlotStoryBook file / Parallel ID, Bible book/chapter. Parallel pairs whose Kikamba side is in
monolingual dev/test are flagged `mono_split`.

**Recommended splits?** `data/monolingual/{train,dev,test}.jsonl`. FLORES-200 dev is in `dev`
and devtest in `test`, and neither is ever in train. No near-duplicate (MinHash Jaccard >= 0.7) crosses
splits.

**Errors, noise, redundancy?**
- Language ID errors remain: GlotLID confuses Kikamba with Kikuyu, Tharaka, Embu/Meru and Swahili,
  especially on short lines. Some Kikuyu may remain; some genuine Kikamba was dropped.
- OPUS-NLLB is automatically mined: many pairs are misaligned or only loosely parallel, and the
  Kikamba side contains romanised Hindi and other noise that survived only if GlotLID was fooled.
- Orthography varies (with/without ĩ/ũ; older texts without diacritics). Only grave→tilde and
  apostrophe unification were normalised.
- FineTranslations English is **machine translation**, flagged `extra.translation_origin: machine`.

**Self-contained?** Yes. Raw source files are cached under `data/raw` and `data/cache` (not for
redistribution; regenerate with `corpus fetch`).

**Confidential data?** No private data was collected. ASR speaker names, ages and genders were
deliberately not stored. Web text may contain names of public figures and ordinary people as
published on the web.

**Offensive content?** Not filtered for toxicity. The web portion is dominated by religious
publishing (jw.org), which reflects a particular denominational viewpoint.

## Collection process

**How was the data acquired?** Downloaded from public repositories (Hugging Face Hub, OPUS object
storage, Tatoeba exports, Bloom Library Parse API + S3, HF dataset-viewer API) by per-source fetchers
in `src/kikamba_corpus/sources/`, plus one local file supplied by the user (BSK 2011 Bible XML ->
unverified). Every request used a descriptive User-Agent, honoured robots.txt, and waited
>= 2 s between requests to the same host.

**Sampling?** No sampling: everything licence-compatible and language-verified was kept (volume
over genre balance, as requested).

**Timeframe?** Fetched 2026-09-26. Underlying text dates from ~1960s (Bible translation lineage)
to 2026 (ASR recordings); web crawls span Common Crawl 2013–2024 and Internet Archive dumps.

**Ethical review?** None formal. Licence decisions are documented in `REPORT.md`.

## Preprocessing / cleaning / labelling

NFC; ftfy mojibake repair; HTML stripping; grave→tilde vowel mapping; apostrophe/quote
unification; whitespace normalisation; short-boilerplate-line removal; quality heuristics; GlotLID
v3 language ID (document- and line-level); exact + MinHash near-dedup with source priority;
containment dedup (unverified bucket); religious-genre heuristic; split with leak removal. Every
dropped document, line and pair is logged with a reason in `logs/drops.jsonl.gz`, and counts are in
`logs/drop_summary.json`. Raw data is kept in `data/raw/` (not distributed).

## Uses

**Intended:** Kikamba–English/Swahili machine translation (parallel files); language
identification research (corpus + drop logs); spell-checking, keyboard prediction and other
writing tools; vocabulary, orthography and corpus-linguistic studies; subword segmentation for
Kikamba NLP.

**Should not be used for:**
- Commercial products without first filtering out NC/ND-licensed records (Bloom, some
  GlotStoryBook stories) and considering the web-text caveat.
- Anything built from `data/unverified/`, unless you have obtained the rights yourself. The BSK
  Bible is all-rights-reserved.
- Treating genre labels as ground truth, since religious tagging is heuristic.

**Composition risks:** anything built on it will over-represent religious register (jw.org and Bible
language) and news-translation register (FLORES/NLLB), and under-represent everyday speech
(only a few thousand ASR utterances and ten Tatoeba sentences).

## Distribution

Distributed as JSONL + `train.txt`. Each record keeps its own licence. The collection as a whole
is not relicensed: CC-BY-SA material (FLORES) requires share-alike, CC-BY/-NC/-ND terms apply per
record, and ODC-By requires attribution of the source datasets. `data/unverified/`
is for private inspection only and must not be redistributed.

## Maintenance

Add a source by writing `src/kikamba_corpus/sources/<name>.py` (see README). Rerun
`corpus fetch && corpus build && corpus tokenize && corpus stats`. Report issues to the repository
owner.
