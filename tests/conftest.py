import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def samples() -> dict:
    return json.loads((FIXTURES / "lid_samples.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def lid():
    from kikamba_corpus import config
    from kikamba_corpus.filter import LanguageIdentifier

    if not config.GLOTLID_MODEL.exists():
        pytest.skip("GlotLID model not downloaded (models/glotlid_v3.bin)")
    return LanguageIdentifier()
