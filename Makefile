# Thin wrapper around the `corpus` CLI (works anywhere `uv` is on PATH).
UV ?= uv
RUN = $(UV) run

.PHONY: all setup models fetch build tokenize stats test clean

all: setup models fetch build tokenize stats

setup:
	$(UV) sync --group dev

# GlotLID v3 (primary LID) and fastText lid.176 (fallback), both from Hugging Face.
models:
	$(RUN) python -m kikamba_corpus.models

fetch:
	$(RUN) corpus fetch

build:
	$(RUN) corpus build

tokenize:
	$(RUN) corpus tokenize

stats:
	$(RUN) corpus stats

test:
	$(RUN) pytest -q

clean:
	rm -rf data/monolingual data/parallel data/unverified tokenizer_models stats logs
