# carbonmix — low-carbon concrete mix screening tool

Ranks candidate concrete mixes by embodied carbon (kgCO2e/m3) for a target
strength class and exposure class, using a simplified strength model, an
indicative BS 8500-style durability screen, and ICE-database-style carbon
factors. Built as a civil engineering portfolio project.

> **This is a SCREENING tool.** It is **not** a substitute for concrete mix
> design to BS 8500 / EN 206, trial mixes, supplier mix designs, or a
> chartered engineer's judgement. Every data table in it is indicative and
> must be refreshed from current sources before any number is quoted.

## What it does

Given a target strength class (e.g. C32/40) and an exposure class (e.g.
XC3_XC4), it grid-searches candidate mixes over:

| Variable | Range | Step |
|---|---|---|
| Total binder | 260–450 kg/m3 | 10 |
| Free w/c | 0.35–0.65 | 0.01 |
| GGBS (% of binder) | 0–70% | 5% |
| Fly ash (% of binder) | 0–35% | 5% |

(combined GGBS + fly ash capped at 70% of binder), keeps the mixes that
meet both the strength target and the durability limits, ranks them by
embodied carbon, and reports the % saving of the best mix against a
CEM I-only baseline (the lowest-carbon feasible mix with no replacement).

## The model

**Strength** — simplified Abrams-type law for mean 28-day strength:

```
fcm = K1 / K2^(w/c_eff)        (defaults K1 = 110 MPa, K2 = 10)
```

which gives fcm ≈ 34.8 MPa at w/c_eff = 0.50. The effective water/binder
ratio uses the EN 206 k-value concept:

```
w/c_eff = water / (cement + 0.6·GGBS + 0.4·fly ash)
```

(k-values configurable). Characteristic strength takes the EN 1992-style
margin `fck = fcm − 8 MPa`, and strength classes map to required
characteristic **cylinder** strength: C25/30 → 25, C28/35 → 28,
C32/40 → 32, C35/45 → 35, C40/50 → 40 MPa.

**Durability** — indicative BS 8500-style limits per exposure class
(max effective w/c, min binder content), e.g. XC3_XC4: w/c ≤ 0.55 and
binder ≥ 300 kg/m3. See `carbonmix/data/durability_limits.py` — the
values are marked "indicative, verify against current BS 8500-1
Table A.4/A.5" and are deliberately a *simplification*.

**Embodied carbon** — mass balance for 1 m3: binder split by replacement
fractions, water = w/c × binder, 2% air, and aggregate filling the
remaining absolute volume (particle densities: cement 3150, GGBS 2900,
fly ash 2300, water 1000, aggregate 2650 kg/m3; aggregate split 40% sand /
60% coarse). Carbon = Σ massᵢ × factorᵢ with indicative cradle-to-gate
factors (kgCO2e/kg): CEM I 0.91, GGBS 0.08, fly ash 0.01, aggregates
0.005, water 0.0003 — order-of-magnitude values in the spirit of the ICE
database v3; refresh from the current ICE DB or supplier EPDs.

## Assumptions and limitations (read these)

- The Abrams constants are **not calibrated** to any real cement,
  aggregate or admixture system; real strength varies widely with
  materials, curing and age. Trial mixes are the only way to confirm
  strength.
- Durability limits are indicative screening values, not a transcription
  of BS 8500-1; cover, cement/combination designations, intended working
  life, aggregate size and freeze–thaw (XF) classes are **not** modelled.
- Strength classes are checked on characteristic *cylinder* strength with
  a flat 8 MPa margin; no statistical quality-control model.
- Carbon factors are cradle-to-gate materials only: no transport,
  batching, pumping, formwork, reinforcement, wastage or in-use
  carbonation. GGBS/fly ash factors are allocation-sensitive and contested.
- No workability/rheology model: a w/c of 0.35 without superplasticiser is
  not placeable; admixtures are outside scope.
- Mass balance assumes saturated-surface-dry aggregate and fixed 2% air.
- Grid search only — answers are only as fine as the grid steps.

## Install

Python ≥ 3.11. From the repository root:

```
python -m pip install -e .
```

(dev extras for testing: `python -m pip install -e ".[dev]"` then `pytest`).
Only runtime dependency is matplotlib; everything else is stdlib.

## Run

```
python -m carbonmix --class C32/40 --exposure XC3_XC4 --top 10 --plot out.png
```

Exposure classes: `XC1`, `XC3_XC4`, `XD3`, `XS3`. Strength classes:
`C25/30`, `C28/35`, `C32/40`, `C35/45`, `C40/50`.

### Example output

```
carbonmix 0.1.0 - low-carbon concrete mix screening
Screening estimates only - indicative data, simplified models. NOT a substitute for BS 8500 / EN 206 mix design or trial mixes.

Target: C32/40 (fck >= 32 MPa), exposure XC3_XC4 (max w/c_eff 0.55, min binder 300 kg/m3)
Grid: 57040 combinations evaluated, 2688 feasible

Top 10 mixes by embodied carbon:
  #   binder   GGBS    FA    w/c  w/c_eff    fck  kgCO2e/m3   saving
       kg/m3      %     %                    MPa             vs CEM I
--------------------------------------------------------------------
  1      300     50     0   0.35    0.437   32.2      158.8    43.9%
  2      310     50     0   0.35    0.437   32.2      163.7    42.2%
  3      320     50     0   0.35    0.437   32.2      168.5    40.5%
  4      300     35    10   0.35    0.437   32.2      169.1    40.2%
  5      300     40     5   0.35    0.432   32.7      170.2    39.9%
  6      300     45     0   0.36    0.439   32.0      171.2    39.5%
  7      300     45     0   0.35    0.427   33.2      171.3    39.5%
  8      330     50     0   0.35    0.437   32.2      173.4    38.7%
  9      310     35    10   0.35    0.437   32.2      174.3    38.4%
 10      310     40     5   0.35    0.432   32.7      175.4    38.0%

CEM I-only baseline: binder 300 kg/m3, w/c 0.43 -> 283.1 kgCO2e/m3
Best mix saves 43.9% embodied carbon vs the CEM I-only baseline.
Plot saved to out.png
```

The plot (see `examples/c32_40_xc3_xc4.png`) scatters embodied carbon
against estimated fck for every feasible mix, with the best mix and the
CEM I baseline highlighted.

The headline result is the textbook one: for C32/40 in XC3_XC4, a
50% GGBS blend at low w/c screens at roughly **44% less embodied carbon**
than a plain CEM I mix — with the honest caveat that the k-value approach
penalises high-replacement strength, so real GGBS mixes (which gain
strength beyond 28 days) may do even better than this model suggests.

## Library use

```python
from carbonmix import grid_search

result = grid_search("C32/40", "XC3_XC4")
print(result.best.carbon, result.saving_pct)
```

See `examples/api_example.py` for point calculations (effective w/c,
strength, mix proportions) as well.

## Tests

```
python -m pytest
```

30 tests cover: strength falls with w/c, hand-checked k-value maths,
carbon falls as GGBS rises, the volume balance closes to 1 m3, durability
caps reject non-compliant mixes, and the optimiser's feasible set,
ordering, baseline and saving for C32/40 XC3_XC4.

## Roadmap

- XF (freeze–thaw) exposure classes and air-entrainment handling
- Cost data alongside carbon (Pareto front: cost vs CO2e)
- Limestone (CEM II/A-L) and calcined-clay (LC3) binder options
- Age-dependent strength for GGBS mixes (28 vs 56-day compliance)
- Load factors/carbon factors from a user-supplied JSON/EPD file
- Simple workability guardrail (min water content / plasticiser flag)

## License

MIT — see `LICENSE`. Copyright (c) 2026 Harvey Sohal.
