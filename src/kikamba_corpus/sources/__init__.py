"""Source registry. Add a new source by writing a module with INFO + fetch() and listing it here."""
from importlib import import_module

MODULES = [
    "flores",
    "fleurs",
    "tatoeba",
    "bloom",
    "glotstorybook",
    "ddd_asr",
    "kndomboi",
    "fineweb2",
    "finetranslations",
    "hplt2",
    "glotcc",
    "finepdfs",
    "opus_nllb",
    "unverified",
    "bsk_bible",
]


def load(name: str):
    return import_module(f"{__name__}.{name}")


def all_sources():
    return [load(m) for m in MODULES]


# Sources that were searched for and checked but not used, with the reason.
# (Kept in code so REPORT.md / README can be regenerated and so re-checks are easy.)
SKIPPED = [
    ("eBible.org", "https://ebible.org/Scriptures/translations.csv", "No Kikamba (kam) edition listed in translations.csv (checked 2026-09-26)."),
    ("open.bible", "https://open.bible", "No Kikamba resources found."),
    ("Digital Bible Library", "https://app.thedigitalbiblelibrary.org", "Kikamba Bible (Bible Society of Kenya) is not open-licensed; no open-access kam entry. Bible text only reachable via the unverified KnoxDevelopers verse pairs."),
    ("Wikipedia / Wikimedia Incubator", "https://incubator.wikimedia.org/wiki/Wp/kam", "No kam Wikipedia and no Wp/kam test wiki exists."),
    ("Common Voice", "https://commonvoice.mozilla.org/kam", "Locale 'kam' exists but is not contributable; no released sentence set."),
    ("MasakhaNEWS", "https://huggingface.co/datasets/masakhane/masakhanews", "No Kikamba subset."),
    ("AfriBERTa corpus", "https://huggingface.co/datasets/castorini/afriberta-corpus", "No Kikamba subset."),
    ("AfroLM data", "https://huggingface.co/datasets/bonadossou/afrolm_active_learning_dataset", "No Kikamba subset."),
    ("NLLB-Seed", "https://github.com/openlanguagedata/seed", "Gated on HF; Kikamba not among Seed languages."),
    ("MADLAD-400 / MaLA monolingual", "https://huggingface.co/datasets/allenai/MADLAD-400", "No kam subset."),
    ("SIL bloom-lm (HF)", "https://huggingface.co/datasets/sil-ai/bloom-lm", "Gated (needs HF token). Replaced by fetching Bloom Library directly (bloom source)."),
    ("FLORES+ / facebook/flores (HF)", "https://huggingface.co/datasets/openlanguagedata/flores_plus", "Gated. Replaced by the ungated mteb/flores mirror (flores200 source)."),
    ("FLORES-200 tarball", "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz", "Host robots.txt is 'Disallow: /'. Replaced by mteb/flores."),
    ("facebook/bouquet", "https://huggingface.co/datasets/facebook/bouquet", "Gated (needs HF token)."),
    ("LughaGen Multilingual African Corpus", "https://huggingface.co/datasets/LughaGen-Organization/LughaGen-Multilingual-African-Corpus", "Gated (needs HF token)."),
    ("FarmerlineML/kamba_dataset", "https://huggingface.co/datasets/FarmerlineML/kamba_dataset", "Manually gated, no licence."),
    ("thiomi/thiomi-5k", "https://huggingface.co/datasets/thiomi/thiomi-5k", "No licence; ~1 GB speech parquet."),
    ("NjeriKahoro/thiomi-multilingual-text", "https://huggingface.co/datasets/NjeriKahoro/thiomi-multilingual-text", "No kam text files found beyond the thiomi speech set; not pursued."),
    ("StoryWeaver", "https://storyweaver.org.in/", "14 Kikamba books found, but story text API returns 401 without login; mostly African Storybook translations already covered via GlotStoryBook/Bloom."),
    ("African Storybook (direct)", "https://www.africanstorybook.org/", "Reader is a JS app with no documented bulk/text endpoint; Kikamba ASb stories are covered via GlotStoryBook (Global-ASP) and Bloom."),
    ("michsethowusu/*-kamba sentence pairs, kamba-sentiments/emotions", "https://huggingface.co/michsethowusu", "Re-packagings of OPUS NLLB (duplicates of opus_nllb). Verified for kamba-sentiments-corpus: 26,389/26,389 unique texts occur verbatim on the OPUS NLLB kam side; labels are English-model (DistilBERT SST-2) projections, not Kikamba annotations."),
    ("FineWeb-2 kam_Latn_removed", "https://huggingface.co/datasets/HuggingFaceFW/fineweb-2", "Docs rejected by FineWeb-2 quality filters; excluded on quality grounds."),
    ("xP3x / SIB-200 / Belebele-style derivatives", "https://huggingface.co/datasets/CohereLabs/xP3x", "Derived from FLORES; duplicates of flores200."),
    ("PanLex", "https://huggingface.co/datasets/lbourdois/panlex", "Lexical translations (word lists), not running text; 1.2 GB CSV for a small kam slice."),
    ("KambaBench-ASR", "https://huggingface.co/datasets/lawmaluki/KambaBench-ASR", "Contains only documentation files, no text."),
    ("DDD Kamba ASR (remaining rows)", "https://huggingface.co/datasets/Digital-Divide-Data/Kamba-ASR-Data-Subset-484H", "Only the dataset-viewer-indexed prefix was fetched; the rest needs ~200 GB of audio shards."),
    ("Swarthmore LING073 Kamba corpora (kam corpus, kam-eng parallel)", "https://wikis.swarthmore.edu/ling073/Kamba", "Hosted on github.swarthmore.edu, which requires a Swarthmore login (HTTP 302 -> /login)."),
    ("Rosetta Project Kikamba Genesis (archive.org)", "https://archive.org/details/rosettaproject_kam_gen-1", "Publisher United Bible Societies (1974), no licence in item metadata; OCR'd PDF of Genesis only."),
    ("Ĩvuku ya Mboya kwa andũ Onthe (Book of Common Prayer, 1963)", "https://mammana.org/bcp/kamba1963/", "SPCK 1963 edition incl. catechism; still in copyright with no open licence stated, and distributed as scanned PDFs (would need OCR). Good candidate if permission is obtained."),
    ("Global-ASP Storybooks Kenya (kam)", "https://global-asp.github.io/storybooks-kenya/stories/kam/", "Already covered: GlotStoryBook's global-asp/asp-source rows are these stories (47 kam stories fetched)."),
    ("Yukawa 1984, 'On the Nature of the Accent of Kamba Nouns' (Senri Ethnological Studies 15)", "https://doi.org/10.15021/00003319", "English-language linguistics paper (~4.8k words); Kamba appears only as isolated tone-marked nouns with OCR errors; (c) National Museum of Ethnology, no open licence. Useful as a tone/lexicon reference, not corpus text."),
    ("Kenyan government Kikamba publications", "https://www.kenyalaw.org", "No Kikamba publications with an explicit open licence found."),
]
