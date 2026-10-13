"""Train SentencePiece BPE tokenizers on data/monolingual/train.txt and evaluate them.

Reports, per vocab size: chars/token and bytes/token on dev (compression), tokens/word
(fertility), coverage of Kikamba tilde vowels as single pieces, and the most frequent tokens.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import sentencepiece as spm

from .. import config
from ..jsonl import read_jsonl

log = logging.getLogger(__name__)


def train_one(vocab: int, input_path: Path = config.MONO / "train.txt", out_dir: Path = config.TOKENIZER_DIR,
              name: str = "kam_bpe") -> str:
    prefix = out_dir / f"{name}_{vocab // 1000}k"
    spm.SentencePieceTrainer.train(
        input=str(input_path),
        model_prefix=str(prefix),
        model_type="bpe",
        vocab_size=vocab,
        character_coverage=0.9995,
        byte_fallback=True,
        normalization_rule_name="identity",  # text is already NFC-normalised by clean/
        split_digits=True,
        input_sentence_size=2_000_000,
        shuffle_input_sentence=True,
        max_sentence_length=65536,
        train_extremely_large_corpus=False,
        num_threads=8,
        unk_id=0, bos_id=1, eos_id=2, pad_id=3,
        seed_sentencepiece_size=1_000_000,
        minloglevel=2,
    )
    return str(prefix) + ".model"


def evaluate(model_path: str, top_n: int = 50, train_path: Path = config.MONO / "train.txt") -> dict:
    sp = spm.SentencePieceProcessor(model_file=model_path)
    dev = [d["text"] for d in read_jsonl(config.MONO / "dev.jsonl")]
    chars = sum(len(t) for t in dev)
    nbytes = sum(len(t.encode("utf-8")) for t in dev)
    words = sum(len(t.split()) for t in dev)
    ntok = sum(len(ids) for ids in sp.encode(dev))
    freq: Counter = Counter()
    with open(train_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 200_000:
                break
            freq.update(sp.encode(line.rstrip("\n"), out_type=str))
    vocab = [sp.id_to_piece(i) for i in range(sp.get_piece_size())]
    return {
        "model": model_path,
        "vocab_size": sp.get_piece_size(),
        "dev_docs": len(dev),
        "dev_chars": chars,
        "dev_tokens": ntok,
        "chars_per_token": round(chars / max(1, ntok), 3),
        "bytes_per_token": round(nbytes / max(1, ntok), 3),
        "tokens_per_word": round(ntok / max(1, words), 3),
        "pieces_with_tilde_vowel": sum(any(c in p for c in "ĩũĨŨ") for p in vocab),
        "byte_fallback_pieces_in_dev": sum(1 for ids in sp.encode(dev[:2000], out_type=str)
                                           for p in ids if p.startswith("<0x")),
        "top_tokens": freq.most_common(top_n),
    }


def run(vocabs: list[int], input_path: Path = config.MONO / "train.txt", out_dir: Path = config.TOKENIZER_DIR,
        name: str = "kam_bpe") -> dict:
    config.ensure_dirs()
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for v in vocabs:
        log.info("training SentencePiece BPE vocab=%d on %s", v, input_path)
        m = train_one(v, input_path, out_dir, name)
        results[str(v)] = evaluate(m, train_path=input_path)
        log.info("vocab=%d chars/token=%.3f tokens/word=%.3f", v, results[str(v)]["chars_per_token"],
                 results[str(v)]["tokens_per_word"])
    (out_dir / "tokenizer_report.json").write_text(
        json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    return results
