import unicodedata

from kikamba_corpus.clean import clean_text, normalize


def test_keeps_kikamba_diacritics_nfc(samples):
    s = "Mbaka hĩĩ nĩ yakwa."
    decomposed = unicodedata.normalize("NFD", s)
    assert decomposed != s
    out = clean_text(decomposed)
    assert out == s
    assert unicodedata.is_normalized("NFC", out)
    # Genuine text passes through unchanged apart from quote unification and the
    # circumflex/macron -> tilde mapping (FLORES itself has e.g. "usuvîi" for "usuvĩi").
    expected = str.maketrans({"“": '"', "”": '"', "î": "ĩ", "û": "ũ", "ī": "ĩ", "ū": "ũ"})
    for t in samples["kam_short"] + samples["kam_long"]:
        assert clean_text(t) == t.translate(expected)


def test_grave_vowels_mapped_to_tilde():
    # kndomboi CC0 text writes ĩ/ũ as ì/ù
    assert normalize("Katiwa nì mùtumìa wì kìthito mùno.") == "Katiwa nĩ mũtumĩa wĩ kĩthito mũno."
    # macron / circumflex substitutes seen in the DDD ASR transcripts and web text
    assert normalize("andū ūla nī mūno, nî Yesū") == "andũ ũla nĩ mũno, nĩ Yesũ"
    assert normalize("Müller José") == "Müller José"  # foreign-name diacritics untouched


def test_apostrophes_normalised():
    assert normalize("Ngali ya mwaki isovetw’e") == "Ngali ya mwaki isovetw'e"
    assert normalize("ngʼombe") == "ng'ombe"


def test_mojibake_repaired():
    broken = "Mbaka hĩĩ nĩ yakwa.".encode("utf-8").decode("latin-1")
    assert normalize(broken) == "Mbaka hĩĩ nĩ yakwa."


def test_html_and_boilerplate_stripped_sentence_boundaries_kept():
    html = (
        "<html><head><script>var x=1;</script><style>p{}</style></head><body>"
        "<nav>Home | About</nav>"
        "<p>Mbaka nikwataa mbia.</p><p>Ngiti nisyiukuma.</p>"
        "<p>Copyright © 2024 All rights reserved</p>"
        "<p>https://example.org/page</p><p>12 / 34</p>"
        "</body></html>"
    )
    out = clean_text(html)
    assert out.split("\n") == ["Mbaka nikwataa mbia.", "Ngiti nisyiukuma."]


def test_whitespace_normalised():
    assert clean_text("  Ngiti  nisyiukuma.\t \n\n\n Mbaka  nikwataa mbia. ") == \
        "Ngiti nisyiukuma.\nMbaka nikwataa mbia."
    assert clean_text("Ũvoo!​") == "Ũvoo!"


def test_repeated_lines_collapsed_and_entities_unescaped():
    assert clean_text("Ũvoo!\nŨvoo!\nNgiti nisyiukuma.") == "Ũvoo!\nNgiti nisyiukuma."
    assert clean_text("Tom &amp; Mbaka") == "Tom & Mbaka"


def test_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""
