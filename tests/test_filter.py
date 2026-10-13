from kikamba_corpus.filter import kam_marker_score, lang_matches, quality_check


def test_glotlid_accepts_kikamba(lid, samples):
    # Strict mode (web/mined text): GlotLID mislabels some loanword-heavy Kikamba as Swahili
    # (e.g. the "Steve Jobs ... iPhone ... mfukoni" FLORES sentence), so require a large majority.
    res = [lid.is_kikamba(t)[0] for t in samples["kam_long"]]
    assert sum(res) >= 0.8 * len(res), res


def test_curated_mode_accepts_all_long_kikamba(lid, samples):
    for t in samples["kam_long"]:
        ok, r = lid.is_kikamba(t, curated=True)
        assert ok, (t, r)


def test_glotlid_rejects_swahili_and_english_decoys(lid, samples):
    for t in samples["swh"] + samples["eng"]:
        ok, r = lid.is_kikamba(t)
        assert not ok, (t, r)
        assert r.label.split("_")[0] in {"swh", "swa", "swc", "eng"}, (t, r)


def test_curated_short_sentences_mostly_accepted(lid, samples):
    res = [lid.is_kikamba(t, curated=True)[0] for t in samples["kam_short"]]
    assert sum(res) >= 0.7 * len(res), res


def test_curated_mode_still_rejects_decoys(lid, samples):
    for t in samples["swh"] + samples["eng"]:
        assert not lid.is_kikamba(t, curated=True)[0], t


def test_batch_predict_matches_single(lid, samples):
    texts = samples["kam_long"][:3] + samples["swh"][:3]
    batch = lid.predict_many(texts)
    for t, b in zip(texts, batch):
        assert lid.predict(t).label == b.label


def test_marker_score_separates_kam_from_decoys(samples):
    kam = sum(map(kam_marker_score, samples["kam_long"])) / len(samples["kam_long"])
    eng = sum(map(kam_marker_score, samples["eng"])) / len(samples["eng"])
    assert kam > eng


def test_quality_filter_reasons():
    assert quality_check("Ũvoo!") == (False, "too_short_chars")
    assert quality_check("Mbakaaaaaaaaaaaaaaaaa") == (False, "too_few_words")
    assert quality_check("12 34 56 78 90 12 34 56 !!") == (False, "low_letter_ratio")
    assert quality_check("Шла Саша по шоссе и сосала сушку") == (False, "non_latin_script")
    assert quality_check("na na na na na na na na na na na na na na na na na na na na na") == (False, "repetitive_words")
    assert quality_check("Mbaka hĩĩ nĩ yakwa na nĩ nzeo.") == (True, "ok")


def test_lang_matches():
    assert lang_matches("eng_Latn", "eng")
    assert lang_matches("swa_Latn", "swh") and lang_matches("swh_Latn", "swh") and lang_matches("swc_Latn", "swh")
    assert not lang_matches("kam_Latn", "eng")
