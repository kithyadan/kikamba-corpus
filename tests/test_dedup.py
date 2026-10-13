from kikamba_corpus.dedup import MinHasher, dedup_docs, estimated_jaccard, exact_key
from kikamba_corpus.genre import is_religious
from kikamba_corpus.split import assign_splits


def _doc(i, text, priority=50, **extra):
    d = {"id": f"d{i}", "text": text, "source": "t", "priority": priority}
    if extra:
        d["extra"] = extra
    return d


def test_exact_key_ignores_case_punct_space(samples):
    t = samples["kam_long"][0]
    assert exact_key(t) == exact_key("  " + t.upper().replace(",", "") + " ")
    assert exact_key(t) != exact_key(samples["kam_long"][1])


def test_minhash_similarity(samples):
    h = MinHasher()
    a = samples["kam_long"][6]
    near = a.replace("Brisbane", "Brisbane,")  # punctuation-only revision
    assert estimated_jaccard(h.signature(a), h.signature(near)) > 0.9
    assert estimated_jaccard(h.signature(a), h.signature(samples["kam_long"][2])) < 0.3


def test_dedup_exact_and_near_keeps_priority(samples):
    base = " ".join(samples["kam_long"][2:5])
    words = base.split()
    words[3] += "a"  # one-word revision of the same text
    revised = " ".join(words)
    docs = [
        _doc(1, base, priority=50),
        _doc(2, base.upper(), priority=60),  # exact dup (normalised)
        _doc(3, revised, priority=10),  # near dup, higher priority -> should win
        _doc(4, samples["kam_long"][8], priority=50),  # unrelated
    ]
    kept, dropped = dedup_docs(docs, threshold=0.8)
    kept_ids = {d["id"] for d in kept}
    assert kept_ids == {"d3", "d4"}
    reasons = {d["id"]: r for d, r in dropped}
    assert reasons["d2"].startswith("exact_dup_of:")
    assert reasons["d1"].startswith("near_dup_of:d3")


def test_bible_revision_style_near_dup_collapses(samples):
    v1 = "\n".join(samples["kam_long"])
    v2 = v1.replace("nthi", "nthĩ").replace("ngali", "ngalĩ")  # orthographic revision
    kept, _ = dedup_docs([_doc(1, v1), _doc(2, v2)], threshold=0.8)
    assert len(kept) == 1


def test_decoys_not_merged_with_kikamba(samples):
    docs = [_doc(i, t) for i, t in enumerate(samples["kam_long"] + samples["swh"] + samples["eng"])]
    kept, dropped = dedup_docs(docs, threshold=0.8)
    assert len(kept) == len(docs) and not dropped


def test_split_no_cross_split_near_dups(samples):
    docs = [_doc(i, f"{t} ({i})") for i, t in enumerate(samples["kam_long"] * 30)]
    splits, dropped, moved = assign_splits(docs, threshold=0.7)
    h = MinHasher()
    sig = {d["id"]: h.signature(d["text"]) for d in docs}
    for a in splits["dev"] + splits["test"]:
        for b in splits["train"]:
            assert estimated_jaccard(sig[a["id"]], sig[b["id"]]) < 0.7


def test_split_benchmark_pinned_and_protected(samples):
    bench = _doc(0, samples["kam_long"][0], benchmark=True, flores_split="devtest")
    copy = _doc(1, samples["kam_long"][0] + " .")
    other = _doc(2, samples["kam_long"][1])
    splits, dropped, _ = assign_splits([bench, copy, other], threshold=0.7)
    assert bench in splits["test"]
    assert [d["id"] for d, _ in dropped] == ["d1"]


def test_religious_heuristic(samples):
    assert is_religious("Mwĩaĩi Yeova akavyaĩa methoi mothyũnĩ onthe.")
    assert is_religious("anything", url="https://www.jw.org/kam/")
    assert not any(is_religious(t) for t in samples["kam_long"])


def test_contained_single_line_docs_dropped(samples):
    from kikamba_corpus.build import drop_contained

    chapter = _doc(1, "\n".join(samples["kam_long"][:5]))  # e.g. a full Bible chapter, one verse per line
    verse_copy = _doc(2, samples["kam_long"][2].upper())  # same verse from another dataset
    unrelated = _doc(3, samples["kam_long"][7])
    kept, dropped = drop_contained([chapter, verse_copy, unrelated])
    assert {d["id"] for d in kept} == {"d1", "d3"}
    assert dropped[0][1] == "contained_in:d1"
