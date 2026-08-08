"""Indicative data tables used by carbonmix.

All values in this subpackage are order-of-magnitude / indicative figures
for screening only. Refresh them from the current editions of the source
documents (BS 8500-1, ICE embodied carbon database) before relying on any
result.
"""

from carbonmix.data.carbon_factors import (
    AIR_CONTENT,
    CARBON_FACTORS,
    COARSE_AGG_FRACTION,
    PARTICLE_DENSITY,
    SAND_FRACTION,
)
from carbonmix.data.durability_limits import (
    DURABILITY_LIMITS,
    MAX_COMBINED_SCM_FRACTION,
    MAX_FA_FRACTION,
    MAX_GGBS_FRACTION,
)

__all__ = [
    "AIR_CONTENT",
    "CARBON_FACTORS",
    "COARSE_AGG_FRACTION",
    "DURABILITY_LIMITS",
    "MAX_COMBINED_SCM_FRACTION",
    "MAX_FA_FRACTION",
    "MAX_GGBS_FRACTION",
    "PARTICLE_DENSITY",
    "SAND_FRACTION",
]
