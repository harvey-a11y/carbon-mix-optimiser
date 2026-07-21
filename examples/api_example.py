"""Using carbonmix as a library instead of via the CLI.

Run from the repository root (after `python -m pip install -e .`):

    python examples/api_example.py
"""

from carbonmix import effective_wc, grid_search, mean_strength, mix_proportions

# 1. Point calculations -------------------------------------------------
wc_eff = effective_wc(water=165, cement=200, ggbs=200)
print(f"Effective w/c for 165 kg water, 200 kg CEM I + 200 kg GGBS: {wc_eff:.4f}")
print(f"Estimated mean 28-day strength: {mean_strength(wc_eff):.1f} MPa")

masses = mix_proportions(binder=340, wc=0.45, ggbs_frac=0.5)
print("\nConstituents for 340 kg/m3 binder, 50% GGBS, w/c 0.45 (kg/m3):")
for name, mass in masses.items():
    print(f"  {name:<11} {mass:7.1f}")

# 2. Full screening run -------------------------------------------------
result = grid_search("C32/40", "XC3_XC4")
best = result.best
print(
    f"\nC32/40, XC3_XC4: {len(result.feasible)} feasible mixes; "
    f"best = {best.carbon:.1f} kgCO2e/m3 "
    f"({best.ggbs_pct:.0f}% GGBS, {best.fa_pct:.0f}% FA, w/c {best.wc:.2f}), "
    f"saving {result.saving_pct:.1f}% vs the CEM I baseline."
)
