"""carbonmix -- low-carbon concrete mix SCREENING tool.

Estimates 28-day strength with a simplified Abrams-type model (EN 206
k-value binder weighting), screens candidate mixes against indicative
BS 8500-style durability limits, and ranks feasible mixes by embodied
carbon (kgCO2e per m3).

IMPORTANT: this is a screening / coursework tool. It is NOT a substitute
for mix design to BS 8500 / EN 206, trial mixes, or a chartered
engineer's judgement.
"""

from carbonmix.carbon import embodied_carbon, mix_proportions
from carbonmix.durability import meets_durability, within_replacement_caps
from carbonmix.earlyage import EarlyAgeNote, assess, early_ratio
from carbonmix.optimise import MixCandidate, OptimisationResult, grid_search
from carbonmix.sensitivity import SensitivityResult
from carbonmix.sensitivity import run as sensitivity_run
from carbonmix.strength import (
    STRENGTH_CLASSES,
    characteristic_strength,
    effective_wc,
    mean_strength,
)
from carbonmix.transport import parse_distances, transport_carbon

__version__ = "0.2.0"

__all__ = [
    "EarlyAgeNote",
    "MixCandidate",
    "OptimisationResult",
    "STRENGTH_CLASSES",
    "SensitivityResult",
    "__version__",
    "assess",
    "characteristic_strength",
    "early_ratio",
    "effective_wc",
    "embodied_carbon",
    "grid_search",
    "mean_strength",
    "meets_durability",
    "mix_proportions",
    "parse_distances",
    "sensitivity_run",
    "transport_carbon",
    "within_replacement_caps",
]
