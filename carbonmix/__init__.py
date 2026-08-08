"""carbonmix -- low-carbon concrete mix SCREENING tool.

Estimates 28-day strength with a simplified Abrams-type model (EN 206
k-value binder weighting), screens candidate mixes against indicative
BS 8500-style durability limits, and ranks feasible mixes by embodied
carbon (kgCO2e per m3).

IMPORTANT: this is a screening / coursework tool. It is NOT a substitute
for mix design to BS 8500 / EN 206, trial mixes, or a chartered
engineer's judgement.
"""

from carbonmix.strength import (
    STRENGTH_CLASSES,
    characteristic_strength,
    effective_wc,
    mean_strength,
)
from carbonmix.durability import meets_durability, within_replacement_caps
from carbonmix.carbon import embodied_carbon, mix_proportions
from carbonmix.optimise import MixCandidate, OptimisationResult, grid_search
from carbonmix.earlyage import EarlyAgeNote, assess, early_ratio
from carbonmix.transport import transport_carbon, parse_distances
from carbonmix.sensitivity import SensitivityResult, run as sensitivity_run

__version__ = "0.2.0"

__all__ = [
    "STRENGTH_CLASSES",
    "characteristic_strength",
    "effective_wc",
    "mean_strength",
    "meets_durability",
    "within_replacement_caps",
    "embodied_carbon",
    "mix_proportions",
    "MixCandidate",
    "OptimisationResult",
    "grid_search",
    "EarlyAgeNote",
    "assess",
    "early_ratio",
    "transport_carbon",
    "parse_distances",
    "SensitivityResult",
    "sensitivity_run",
    "__version__",
]
