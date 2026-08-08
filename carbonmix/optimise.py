"""Grid-search screening optimiser.

Enumerates candidate mixes over:

* total binder 260..450 kg/m3 in steps of 10,
* free w/c 0.35..0.65 in steps of 0.01,
* GGBS 0..70% of binder in steps of 5%,
* fly ash 0..35% of binder in steps of 5%,

skipping combinations that breach the combined 70% replacement cap.

A mix is *feasible* when its estimated characteristic strength meets the
target strength class AND it passes the indicative durability limits for
the chosen exposure class. Feasible mixes are ranked by embodied carbon
(kgCO2e/m3, ascending). A CEM I-only baseline (the lowest-carbon feasible
mix with no GGBS or fly ash) is reported alongside, with the % carbon
saving of the best blended mix versus that baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from carbonmix.carbon import embodied_carbon, mix_proportions
from carbonmix.durability import meets_durability, within_replacement_caps
from carbonmix.strength import (
    DEFAULT_K1,
    DEFAULT_K2,
    DEFAULT_K_FA,
    DEFAULT_K_GGBS,
    characteristic_strength,
    effective_wc,
    mean_strength,
    required_fck,
)

# Grid definitions (integer-based to avoid floating-point drift).
BINDER_GRID: tuple[float, ...] = tuple(float(b) for b in range(260, 451, 10))
WC_GRID: tuple[float, ...] = tuple(w / 100 for w in range(35, 66))
GGBS_GRID: tuple[float, ...] = tuple(g / 100 for g in range(0, 71, 5))
FA_GRID: tuple[float, ...] = tuple(f / 100 for f in range(0, 36, 5))


@dataclass(frozen=True)
class MixCandidate:
    """One screened mix with its derived quantities."""

    binder: float        # total binder, kg/m3
    wc: float            # free water / total binder
    ggbs_frac: float     # GGBS fraction of binder mass
    fa_frac: float       # fly ash fraction of binder mass
    wc_eff: float        # k-value effective w/c
    fcm: float           # estimated mean 28-day strength, MPa
    fck: float           # estimated characteristic strength, MPa
    carbon: float        # embodied carbon, kgCO2e/m3
    masses: dict[str, float] = field(repr=False)  # kg per m3

    @property
    def ggbs_pct(self) -> float:
        return 100.0 * self.ggbs_frac

    @property
    def fa_pct(self) -> float:
        return 100.0 * self.fa_frac


@dataclass
class OptimisationResult:
    """Outcome of a grid search for one strength class + exposure class."""

    strength_class: str
    exposure: str
    feasible: list[MixCandidate]          # sorted by carbon, ascending
    baseline: MixCandidate | None          # lowest-carbon CEM I-only feasible mix
    n_enumerated: int                      # grid points enumerated (within caps)

    @property
    def best(self) -> MixCandidate | None:
        return self.feasible[0] if self.feasible else None

    @property
    def saving_pct(self) -> float | None:
        """% carbon saving of the best mix vs the CEM I-only baseline."""
        if self.best is None or self.baseline is None:
            return None
        return 100.0 * (self.baseline.carbon - self.best.carbon) / self.baseline.carbon

    def saving_vs_baseline(self, mix: MixCandidate) -> float | None:
        if self.baseline is None:
            return None
        return 100.0 * (self.baseline.carbon - mix.carbon) / self.baseline.carbon


def grid_search(
    strength_class: str,
    exposure: str,
    k1: float = DEFAULT_K1,
    k2: float = DEFAULT_K2,
    k_ggbs: float = DEFAULT_K_GGBS,
    k_fa: float = DEFAULT_K_FA,
) -> OptimisationResult:
    """Screen the full grid and return feasible mixes ranked by carbon."""
    target_fck = required_fck(strength_class)

    feasible: list[MixCandidate] = []
    baseline: MixCandidate | None = None
    n_enumerated = 0

    for ggbs_frac in GGBS_GRID:
        for fa_frac in FA_GRID:
            if not within_replacement_caps(ggbs_frac, fa_frac):
                continue  # skip combos breaching the combined cap
            cement_frac = 1.0 - ggbs_frac - fa_frac
            # k-value effective binder per kg of total binder.
            eff_binder_frac = cement_frac + k_ggbs * ggbs_frac + k_fa * fa_frac
            for wc in WC_GRID:
                # w/c_eff is independent of binder content for a fixed split.
                wc_eff = wc / eff_binder_frac
                fcm = mean_strength(wc_eff, k1=k1, k2=k2)
                fck = characteristic_strength(fcm)
                strength_ok = fck >= target_fck - 1e-9
                for binder in BINDER_GRID:
                    # Counts every grid point enumerated within the
                    # replacement caps, including points skipped once
                    # strength has already failed for this (wc, split).
                    n_enumerated += 1
                    if not strength_ok:
                        continue
                    if not meets_durability(exposure, wc_eff, binder):
                        continue
                    try:
                        masses = mix_proportions(binder, wc, ggbs_frac, fa_frac)
                    except ValueError:
                        continue  # not physically realisable
                    candidate = MixCandidate(
                        binder=binder,
                        wc=wc,
                        ggbs_frac=ggbs_frac,
                        fa_frac=fa_frac,
                        wc_eff=wc_eff,
                        fcm=fcm,
                        fck=fck,
                        carbon=embodied_carbon(masses),
                        masses=masses,
                    )
                    feasible.append(candidate)
                    if ggbs_frac == 0.0 and fa_frac == 0.0 and (
                        baseline is None or candidate.carbon < baseline.carbon
                    ):
                        baseline = candidate

    feasible.sort(key=lambda m: (m.carbon, m.binder, m.wc))

    # Sanity check on effective_wc consistency (uses the module-level helper
    # so the two formulations cannot silently drift apart).
    if feasible:
        m = feasible[0]
        check = effective_wc(
            m.masses["water"], m.masses["cem1"], m.masses["ggbs"],
            m.masses["fly_ash"], k_ggbs=k_ggbs, k_fa=k_fa,
        )
        if abs(check - m.wc_eff) >= 1e-9:
            raise RuntimeError(
                "w/c_eff consistency check failed for the best mix: "
                f"grid-search value {m.wc_eff!r} != effective_wc() "
                f"recomputation {check!r}. The two k-value formulations "
                "have drifted apart; check effective_wc() against the "
                "eff_binder_frac maths in grid_search()."
            )

    return OptimisationResult(
        strength_class=strength_class,
        exposure=exposure,
        feasible=feasible,
        baseline=baseline,
        n_enumerated=n_enumerated,
    )
