"""Download the language-ID models (GlotLID v3 primary, fastText lid.176 fallback) from Hugging Face."""
from __future__ import annotations

import logging

from . import config
from .net import session

log = logging.getLogger(__name__)


def ensure_models() -> None:
    config.ensure_dirs()
    for url, dest in ((config.GLOTLID_URL, config.GLOTLID_MODEL), (config.LID176_URL, config.LID176_MODEL)):
        if dest.exists() and dest.stat().st_size > 0:
            continue
        log.info("downloading %s", url)
        try:
            session().download(url, dest)
        except Exception as e:  # the other model is the fallback
            log.warning("could not download %s: %s", url, e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_models()
