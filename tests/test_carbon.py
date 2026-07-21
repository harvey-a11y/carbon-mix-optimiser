"""Tests for the mass balance and embodied carbon model."""

import pytest

from carbonmix.carbon import embodied_carbon, mix_carbon, mix_proportions
from carbonmix.data.carbon_factors import AIR_CONTENT, PARTICLE_DENSITY


def test_carbon_decreases_as_ggbs_rises():
    carbons = [
        mix_carbon(binder=300, wc=0.5, ggbs_frac=g)
        for g in (0.0, 0.2, 0.5, 0.7)
    ]
    assert all(a > b for a, b in zip(carbons, carbons[1:]))


def test_fly_ash_also_cuts_carbon():
    assert mix_carbon(300, 0.5, fa_frac=0.3) < mix_carbon(300, 0.5)


def test_mass_balance_fills_one_cubic_metre():
    masses = mix_proportions(binder=340, wc=0.5, ggbs_frac=0.3, fa_frac=0.1)
    volume = (
        masses["cem1"] / PARTICLE_DENSITY["cem1"]
        + masses["ggbs"] / PARTICLE_DENSITY["ggbs"]
        + masses["fly_ash"] / PARTICLE_DENSITY["fly_ash"]
        + masses["water"] / PARTICLE_DENSITY["water"]
        + (masses["sand"] + masses["coarse_agg"]) / PARTICLE_DENSITY["aggregate"]
        + AIR_CONTENT
    )
    assert volume == pytest.approx(1.0, abs=1e-9)


def test_binder_split_and_water():
    masses = mix_proportions(binder=400, wc=0.45, ggbs_frac=0.5, fa_frac=0.1)
    assert masses["cem1"] == pytest.approx(160.0)
    assert masses["ggbs"] == pytest.approx(200.0)
    assert masses["fly_ash"] == pytest.approx(40.0)
    assert masses["water"] == pytest.approx(0.45 * 400)


def test_aggregate_split_40_60():
    masses = mix_proportions(binder=300, wc=0.5)
    total_agg = masses["sand"] + masses["coarse_agg"]
    assert masses["sand"] == pytest.approx(0.40 * total_agg)
    assert masses["coarse_agg"] == pytest.approx(0.60 * total_agg)


def test_cem1_mix_carbon_order_of_magnitude():
    # CEM I 300 kg/m3 at w/c 0.5: cement dominates at ~273 kgCO2e,
    # aggregate + water add ~10 more.
    carbon = mix_carbon(binder=300, wc=0.5)
    assert 270 < carbon < 300


def test_embodied_carbon_is_mass_weighted_sum():
    masses = {"cem1": 100.0, "ggbs": 100.0}
    assert embodied_carbon(masses) == pytest.approx(100 * 0.91 + 100 * 0.08)


def test_unrealisable_mix_raises():
    with pytest.raises(ValueError):
        mix_proportions(binder=1500, wc=1.5)
