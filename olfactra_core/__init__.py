"""OLFACTRA — The Intelligence of Scent (Core).

Clean-room, MIT-licensed fragrance intelligence: an atlas of scent history, a
public molecule library, a dilution studio with a safety gate, and an
interpretable accord recommender.

    >>> from olfactra_core import recommender, studio
    >>> top = recommender.recommend(mood="calm", space="study", style="green")[0]
    >>> f = studio.formulate(top.product_hint, 50, 20, top.accord.materials)
    >>> f.status in {"ok", "caution", "over"}
    True

Science boundary: OLFACTRA proposes candidate combinations from public molecule
and odour data. It does not predict how a blend will smell; it supports, and is
meant to be checked by, real perfumery and GC-MS validation.
"""
from __future__ import annotations

__version__ = "0.1.0"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026 FEI · HEL Lab, Gyeongsang National University"

from . import atlas, docking, exporter, molecule, pyrfume, recommender, structure3d, studio  # noqa: E402

__all__ = [
    "__version__",
    "atlas",
    "docking",
    "molecule",
    "pyrfume",
    "structure3d",
    "studio",
    "recommender",
    "exporter",
]
