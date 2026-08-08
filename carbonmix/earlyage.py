"""Early-age strength flagging for high-SCM mixes.

Why this module exists
----------------------
Everything else in this package is a 28-day calculation. That is the right
basis for specifying strength class, and it is also the single biggest
practical omission in the tool, because **high-GGBS mixes gain strength
slowly**.

That is not a modelling nicety. It is the first objection any engineer who
has poured concrete in February will raise, and it is a real programme
risk: formwork striking times, early loading, transfer of prestress and
cold-weather working are all governed by early strength, not by the 28-day
figure. A tool that recommends a 70% GGBS mix and says nothing about it is
giving advice that reads as naive.

So this module does the honest minimum: it estimates an indicative
early-age strength ratio and raises a clear warning when the recommended
mix is SCM-heavy. It does NOT pretend to be a maturity model.

Model
-----
Indicative strength-development ratios ``f(t) / f(28)`` for a normal
CEM I concrete at 20 degrees C, with a crude reduction applied per unit of
SCM replacement. The reduction constants are judgement figures chosen to
reflect the well-known direction and rough magnitude of the effect. They
are NOT calibrated against test data and must not be used to justify a
striking time.

Anything that actually governs a striking decision needs cube or maturity
data from the real mix at the real temperature.
"""

from __future__ import annotations

from dataclasses import dataclass

# Indicative f(t)/f(28) for CEM I at 20 C.
CEM1_RATIO: dict[int, float] = {3: 0.45, 7: 0.65, 14: 0.85, 28: 1.00}

# Crude fractional reduction in the EARLY ratio per unit replacement
# fraction. GGBS is slower than fly ash at very early ages.
GGBS_EARLY_PENALTY: float = 0.45
FA_EARLY_PENALTY: float = 0.35

# Replacement fraction above which the tool warns.
SCM_WARN_THRESHOLD: float = 0.50


@dataclass(frozen=True)
class EarlyAgeNote:
    """Indicative early-age position for one mix."""

    scm_frac: float
    ratio_7d: float          # indicative f(7)/f(28)
    fck_7d_indicative: float # MPa, indicative only
    warn: bool
    message: str


def early_ratio(day: int, ggbs_frac: float, fa_frac: float) -> float:
    """Indicative f(day)/f(28), reduced for SCM content."""
    if day not in CEM1_RATIO:
        raise ValueError(f"day must be one of {sorted(CEM1_RATIO)}")
    if ggbs_frac < 0 or fa_frac < 0 or ggbs_frac + fa_frac > 1:
        raise ValueError("replacement fractions must be in [0, 1] and sum <= 1")
    base = CEM1_RATIO[day]
    if day >= 28:
        return base  # by definition the 28-day ratio is 1.0 for every mix
    penalty = GGBS_EARLY_PENALTY * ggbs_frac + FA_EARLY_PENALTY * fa_frac
    return max(0.05, base * (1.0 - penalty))


def assess(fck_28: float, ggbs_frac: float, fa_frac: float) -> EarlyAgeNote:
    """Flag a mix whose early strength needs separate checking."""
    scm = ggbs_frac + fa_frac
    r7 = early_ratio(7, ggbs_frac, fa_frac)
    warn = scm > SCM_WARN_THRESHOLD
    if warn:
        msg = (
            f"EARLY-AGE WARNING: {100 * scm:.0f}% of the binder is GGBS/fly ash. "
            f"Indicative 7-day strength is only about {100 * r7:.0f}% of the 28-day "
            f"value (~{fck_28 * r7:.0f} MPa). Striking times, early loading and "
            f"cold-weather working must be checked separately against cube or "
            f"maturity data for the actual mix. Do not take a striking time from "
            f"this tool."
        )
    else:
        msg = (
            f"Early-age: {100 * scm:.0f}% SCM. Indicative 7-day strength about "
            f"{100 * r7:.0f}% of 28-day (~{fck_28 * r7:.0f} MPa)."
        )
    return EarlyAgeNote(
        scm_frac=scm, ratio_7d=r7, fck_7d_indicative=fck_28 * r7,
        warn=warn, message=msg,
    )
