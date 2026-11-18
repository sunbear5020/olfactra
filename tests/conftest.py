import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from olfactra_core import recommender, studio  # noqa: E402


@pytest.fixture(scope="session")
def sample_accord() -> dict[str, float]:
    return {
        "linalool": 40,
        "geraniol": 25,
        "phenylethyl alcohol": 25,
        "cedrol": 10,
    }


@pytest.fixture(scope="session")
def sample_formula(sample_accord):
    return studio.formulate("edp", 50, 20, sample_accord)


@pytest.fixture(scope="session")
def top_pick():
    return recommender.recommend(mood="calm", season="autumn", space="study", style="green")[0]
