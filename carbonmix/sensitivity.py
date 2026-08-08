"""Monte Carlo uncertainty on the headline carbon saving.

Why this module exists
----------------------
The tool's headline output is a single number: the percentage carbon
saving of the best blended mix against a CEM I baseline. That number rests
on two sets of inputs this package openly describes as uncertain:

* the Abrams constants K1 and K2, which ``strength.py`` states are not
  calibrated to any specific materials, and
* the embodied carbon factors, which ``carbon_factors.py`` describes as
  order-of-magnitude ICE-database-style values.

Quoting one figure to one decimal place on top of that is more precision
than the inputs support. This module replaces it with a distribution.

Method
------
Sample K1, K2 and the carbon factors from independent uniform ranges,
re-run the full grid search for each draw, and collect the saving. Report
the median and a percentile interval.

Uniform rather than normal is deliberate: these are ranges of plausible
values rather than measurement errors around a known mean, and pretending
to know the shape would be a second unjustified assumption on top of the
first. Independence between factors is also an assumption, and a
questionable one for cement and GGBS, which share a supply chain.

The sampler is seeded so results are reproducible.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field

from carbonmix.data import carbon_factors as cf_module
from carbonmix.optimise import grid_search

# Plausible ranges. Carbon factors are kgCO2e/kg and bracket the spread
# seen across ICE v3-era entries, supplier EPDs and allocation choices.
# The GGBS range is the widest in relative terms because the allocation
# method (by-product vs co-product of steelmaking) genuinely moves it.
FACTOR_RANGES: dict[str, tuple[float, float]] = {
    "cem1": (0.75, 0.95),
    "ggbs": (0.05, 0.13),
    "fly_ash": (0.004, 0.030),
    "coarse_agg": (0.003, 0.008),
    "sand": (0.003, 0.008),
    "water": (0.0002, 0.0005),
}

# Abrams constants. Wide, because they are uncalibrated.
K1_RANGE: tuple[float, float] = (95.0, 130.0)
K2_RANGE: tuple[float, float] = (8.0, 13.0)


@dataclass
class SensitivityResult:
    """Distribution of the headline saving across sampled inputs."""

    strength_class: str
    exposure: str
    savings: list[float] = field(repr=False)
    n_draws: int = 0
    n_infeasible: int = 0

    @property
    def median(self) -> float | None:
        return statistics.median(self.savings) if self.savings else None

    @property
    def mean(self) -> float | None:
        return statistics.fmean(self.savings) if self.savings else None

    def interval(
        self, lower: float = 5.0, upper: float = 95.0
    ) -> tuple[float, float] | None:
        """Percentile interval of the saving, in percent."""
        if not self.savings:
            return None
        s = sorted(self.savings)

        def pct(p: float) -> float:
            if len(s) == 1:
                return s[0]
            k = (len(s) - 1) * p / 100.0
            lo, hi = int(k), min(int(k) + 1, len(s) - 1)
            return s[lo] + (s[hi] - s[lo]) * (k - lo)

        return pct(lower), pct(upper)

    def summary(self) -> str:
        if not self.savings:
            return "no feasible mix in any draw"
        lo, hi = self.interval()
        return (
            f"saving {self.median:.1f}% (median), 90% interval {lo:.1f}% to {hi:.1f}%, "
            f"from {self.n_draws} draws"
            + (f", {self.n_infeasible} infeasible" if self.n_infeasible else "")
        )


def run(
    strength_class: str,
    exposure: str,
    draws: int = 200,
    seed: int = 12345,
) -> SensitivityResult:
    """Monte Carlo the carbon saving over uncertain inputs.

    The carbon factor dict is patched in place and restored afterwards, so
    calling this leaves the package's defaults untouched.
    """
    if draws < 1:
        raise ValueError("draws must be >= 1")
    rng = random.Random(seed)
    original = dict(cf_module.CARBON_FACTORS)
    savings: list[float] = []
    infeasible = 0

    try:
        for _ in range(draws):
            for name, (lo, hi) in FACTOR_RANGES.items():
                cf_module.CARBON_FACTORS[name] = rng.uniform(lo, hi)
            k1 = rng.uniform(*K1_RANGE)
            k2 = rng.uniform(*K2_RANGE)
            res = grid_search(strength_class, exposure, k1=k1, k2=k2)
            s = res.saving_pct
            if s is None:
                infeasible += 1
            else:
                savings.append(s)
    finally:
        cf_module.CARBON_FACTORS.clear()
        cf_module.CARBON_FACTORS.update(original)

    return SensitivityResult(
        strength_class=strength_class, exposure=exposure,
        savings=savings, n_draws=draws, n_infeasible=infeasible,
    )
