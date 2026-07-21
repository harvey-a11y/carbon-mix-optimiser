"""Indicative durability screening per exposure class.

Applies BS 8500-style limits (see ``carbonmix.data.durability_limits``,
which carries the "indicative values" health warning) on:

* maximum effective water/binder ratio, and
* minimum total binder content (kg/m3),

plus caps on GGBS / fly ash replacement fractions.

This is a coarse screen only. Real BS 8500 compliance also involves
cover, cement/combination designations, intended working life, aggregate
size and more - none of which are modelled here.
"""

from __future__ import annotations

from carbonmix.data.durability_limits import (
    DURABILITY_LIMITS,
    MAX_COMBINED_SCM_FRACTION,
    MAX_FA_FRACTION,
    MAX_GGBS_FRACTION,
)

_TOL = 1e-9  # tolerance so grid values sitting exactly on a cap pass


def exposure_limits(exposure: str) -> dict[str, float]:
    """Return the indicative limits dict for an exposure class."""
    try:
        return DURABILITY_LIMITS[exposure]
    except KeyError:
        supported = ", ".join(DURABILITY_LIMITS)
        raise ValueError(
            f"unknown exposure class {exposure!r}; supported: {supported}"
        ) from None


def within_replacement_caps(ggbs_frac: float, fa_frac: float) -> bool:
    """Check GGBS / fly ash fractions (of total binder mass) against caps."""
    if ggbs_frac < 0 or fa_frac < 0:
        return False
    return (
        ggbs_frac <= MAX_GGBS_FRACTION + _TOL
        and fa_frac <= MAX_FA_FRACTION + _TOL
        and (ggbs_frac + fa_frac) <= MAX_COMBINED_SCM_FRACTION + _TOL
    )


def durability_failures(exposure: str, wc_eff: float, binder: float) -> list[str]:
    """Return a list of human-readable failure reasons (empty = passes)."""
    limits = exposure_limits(exposure)
    failures: list[str] = []
    if wc_eff > limits["max_wc"] + _TOL:
        failures.append(
            f"effective w/c {wc_eff:.3f} exceeds max {limits['max_wc']:.2f} "
            f"for {exposure}"
        )
    if binder < limits["min_binder"] - _TOL:
        failures.append(
            f"binder {binder:.0f} kg/m3 below min {limits['min_binder']:.0f} "
            f"kg/m3 for {exposure}"
        )
    return failures


def meets_durability(exposure: str, wc_eff: float, binder: float) -> bool:
    """True if the mix passes the indicative limits for ``exposure``."""
    return not durability_failures(exposure, wc_eff, binder)
