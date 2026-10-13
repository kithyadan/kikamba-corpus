"""GlotStoryBook: Kikamba children's storybooks (Global Storybooks / African Storybook),
one monolingual doc per story, plus sentence-level kam-eng / kam-swh pairs via Parallel ID."""
import csv
import sys
from collections import defaultdict

from .base import SourceInfo, hf_file, record

REPO = "cis-lmu/GlotStoryBook"

INFO = SourceInfo(
    id="glotstorybook",
    name="GlotStoryBook (Global Storybooks / African Storybook, kam)",
    url=f"https://huggingface.co/datasets/{REPO}",
    license="CC-BY / CC-BY-NC (per story, see record)",
    genre="children-stories",
    curated=True,
    priority=15,
)

LIC = {"CC-BY": "CC-BY-4.0", "CC-BY-NC": "CC-BY-NC-4.0"}
PAIR_LANGS = {"eng": "eng", "swh": "swh", "swa": "swh"}


def fetch():
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    p = hf_file(REPO, "GlotStoryBook.csv")
    kam_rows, others = [], defaultdict(dict)
    with open(p, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            iso = row["ISO639-3"]
            if iso == "kam":
                kam_rows.append(row)
            elif iso in PAIR_LANGS and row["Parallel ID"]:
                others[(row["Parallel ID"], row["Text Number"])][PAIR_LANGS[iso]] = row["Text"]

    stories = defaultdict(list)
    for r in kam_rows:
        stories[(r["Source"], r["File Name"])].append(r)
    for (src, fname), rows in stories.items():
        rows.sort(key=lambda r: int(r["Text Number"] or 0))
        first = rows[0]
        url = f"https://github.com/{src.split('/', 1)[0]}/{src.split('/', 1)[1]}" if "/" in src else INFO.url
        lic = LIC.get(first["License"], first["License"])
        attribution = {"text_by": first["Text By"], "translation_by": first["Translation By"],
                       "story_category": first["Story Category"], "file": fname}
        yield record(INFO, "\n".join(r["Text"] for r in rows), key=(src, fname), url=url,
                     license=lic, extra=attribution)
        for r in rows:
            for lang, tr in others.get((r["Parallel ID"], r["Text Number"]), {}).items():
                yield record(INFO, r["Text"], key=(src, fname, r["Text Number"], lang), url=url,
                             license=lic, kind="parallel", translation=tr, translation_lang=lang,
                             extra=attribution)
