"""Simplified Abrams-type 28-day strength model.

Model
-----
Mean 28-day cylinder strength::

    fcm = K1 / K2 ** (w/c_eff)

with defaults K1 = 110 MPa and K2 = 10, which gives fcm ~ 34.8 MPa at an
effective w/c of 0.50 - a sane order of magnitude for a CEM I concrete.

The effective water/binder ratio follows the EN 206 k-value concept::

    w/c_eff = water / (cement + k_ggbs * ggbs + k_fa * fly_ash)

with default k-values k_ggbs = 0.6 and k_fa = 0.4 (both configurable).

Characteristic strength assumes the EN 1992 margin::

    fck = fcm - 8 MPa

Limitations: this is a screening correlation, not a calibrated strength
model. Real strength depends on cement source and strength class,
aggregate, curing, admixtures and age; the constants here are NOT
calibrated to any specific materials. Verify with trial mixes.
"""

from __future__ import annotations

DEFAULT_K1: float = 110.0  # MPa
DEFAULT_K2: float = 10.0   # dimensionless
DEFAULT_K_GGBS: float = 0.6
DEFAULT_K_FA: float = 0.4
CHARACTERISTIC_MARGIN: float = 8.0  # MPa, fck = fcm - 8 (EN 1992 style)

# Strength class -> required characteristic CYLINDER strength fck (MPa).
STRENGTH_CLASSES: dict[str, float] = {
    "C25/30": 25.0,
    "C28/35": 28.0,
    "C32/40": 32.0,
    "C35/45": 35.0,
    "C40/50": 40.0,
}


def effective_wc(
    water: float,
    cement: float,
    ggbs: float = 0.0,
    fly_ash: float = 0.0,
    k_ggbs: float = DEFAULT_K_GGBS,
    k_fa: float = DEFAULT_K_FA,
) -> float:
    """Effective water/binder ratio using the EN 206 k-value concept.

    All masses in consistent units (typically kg per m3 of concrete).
    """
    if water < 0:
        raise ValueError("water content must be non-negative")
    effective_binder = cement + k_ggbs * ggbs + k_fa * fly_ash
    if effective_binder <= 0:
        raise ValueError("effective binder content must be positive")
    return water / effective_binder


def mean_strength(
    wc_eff: float,
    k1: float = DEFAULT_K1,
    k2: float = DEFAULT_K2,
) -> float:
    """Mean 28-day strength fcm (MPa) from the Abrams-type law."""
    if wc_eff <= 0:
        raise ValueError("effective w/c ratio must be positive")
    if k1 <= 0 or k2 <= 1:
        raise ValueError("require K1 > 0 and K2 > 1")
    return k1 / (k2**wc_eff)


def characteristic_strength(
    fcm: float,
    margin: float = CHARACTERISTIC_MARGIN,
) -> float:
    """Characteristic cylinder strength fck = fcm - margin (MPa)."""
    return fcm - margin


def required_fck(strength_class: str) -> float:
    """Required characteristic cylinder strength for a strength class."""
    try:
        return STRENGTH_CLASSES[strength_class]
    except KeyError:
        supported = ", ".join(STRENGTH_CLASSES)
        raise ValueError(
            f"unknown strength class {strength_class!r}; supported: {supported}"
        ) from None
