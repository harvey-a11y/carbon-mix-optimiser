"""Mix mass balance and embodied carbon (A1-A3, cradle-to-gate style).

Mass balance for 1 m3 of concrete:

1. Total binder content (kg/m3) is an input, split into CEM I, GGBS and
   fly ash by mass fractions.
2. Water mass = (free w/c) * total binder.
3. Binder + water + an assumed 2% entrapped air occupy part of the cubic
   metre by absolute volume (particle densities: cement 3150, GGBS 2900,
   fly ash 2300, water 1000 kg/m3).
4. Aggregate (density 2650 kg/m3) fills the remaining volume and is split
   40% sand / 60% coarse by mass.

Embodied carbon per m3 = sum(mass_i * factor_i), with indicative
ICE-database-style factors from ``carbonmix.data.carbon_factors``.
This covers materials only - no transport, batching, placing, formwork,
reinforcement or in-use carbonation.
"""

from __future__ import annotations

from carbonmix.data.carbon_factors import (
    AIR_CONTENT,
    CARBON_FACTORS,
    COARSE_AGG_FRACTION,
    PARTICLE_DENSITY,
    SAND_FRACTION,
)


def mix_proportions(
    binder: float,
    wc: float,
    ggbs_frac: float = 0.0,
    fa_frac: float = 0.0,
    air_content: float = AIR_CONTENT,
) -> dict[str, float]:
    """Constituent masses (kg per m3 of concrete) for a candidate mix.

    Parameters
    ----------
    binder:
        Total binder content, kg/m3 (CEM I + GGBS + fly ash).
    wc:
        Free water / total binder ratio (NOT the k-value effective ratio).
    ggbs_frac, fa_frac:
        GGBS and fly ash mass fractions of total binder.
    """
    if binder <= 0:
        raise ValueError("binder content must be positive")
    if wc <= 0:
        raise ValueError("w/c ratio must be positive")
    if ggbs_frac < 0 or fa_frac < 0 or ggbs_frac + fa_frac > 1:
        raise ValueError("replacement fractions must be in [0, 1] and sum <= 1")

    cement = binder * (1.0 - ggbs_frac - fa_frac)
    ggbs = binder * ggbs_frac
    fly_ash = binder * fa_frac
    water = wc * binder

    paste_volume = (
        cement / PARTICLE_DENSITY["cem1"]
        + ggbs / PARTICLE_DENSITY["ggbs"]
        + fly_ash / PARTICLE_DENSITY["fly_ash"]
        + water / PARTICLE_DENSITY["water"]
    )
    aggregate_volume = 1.0 - air_content - paste_volume
    if aggregate_volume <= 0:
        raise ValueError(
            "paste and air exceed 1 m3 - mix is not physically realisable"
        )
    aggregate_mass = aggregate_volume * PARTICLE_DENSITY["aggregate"]

    return {
        "cem1": cement,
        "ggbs": ggbs,
        "fly_ash": fly_ash,
        "water": water,
        "sand": SAND_FRACTION * aggregate_mass,
        "coarse_agg": COARSE_AGG_FRACTION * aggregate_mass,
    }


def embodied_carbon(
    masses: dict[str, float],
    factors: dict[str, float] = CARBON_FACTORS,
) -> float:
    """Embodied carbon (kgCO2e per m3) = sum(mass_i * factor_i)."""
    return sum(mass * factors[name] for name, mass in masses.items())


def mix_carbon(
    binder: float,
    wc: float,
    ggbs_frac: float = 0.0,
    fa_frac: float = 0.0,
) -> float:
    """Convenience: embodied carbon (kgCO2e/m3) straight from mix inputs."""
    return embodied_carbon(mix_proportions(binder, wc, ggbs_frac, fa_frac))
