"""Tests for the grid-search optimiser."""

import pytest

from carbonmix.durability import meets_durability, within_replacement_caps
from carbonmix.optimise import grid_search
from carbonmix.strength import required_fck


@pytest.fixture(scope="module")
def c32_xc3():
    return grid_search("C32/40", "XC3_XC4")


def test_feasible_set_is_non_empty(c32_xc3):
    assert len(c32_xc3.feasible) > 0


def test_best_beats_cem1_baseline(c32_xc3):
    assert c32_xc3.baseline is not None
    assert c32_xc3.best is not None
    assert c32_xc3.best.carbon < c32_xc3.baseline.carbon
    assert c32_xc3.saving_pct > 0


def test_feasible_sorted_by_carbon(c32_xc3):
    carbons = [m.carbon for m in c32_xc3.feasible]
    assert carbons == sorted(carbons)
    assert c32_xc3.best is c32_xc3.feasible[0]


def test_all_feasible_meet_constraints(c32_xc3):
    target = required_fck("C32/40")
    for mix in c32_xc3.feasible[:200]:
        assert mix.fck >= target - 1e-9
        assert meets_durability("XC3_XC4", mix.wc_eff, mix.binder)
        assert within_replacement_caps(mix.ggbs_frac, mix.fa_frac)


def test_baseline_is_pure_cem1(c32_xc3):
    assert c32_xc3.baseline.ggbs_frac == 0.0
    assert c32_xc3.baseline.fa_frac == 0.0


def test_best_mix_uses_scms(c32_xc3):
    # With GGBS at 0.08 vs cement at 0.91 kgCO2e/kg, the optimum must blend.
    assert c32_xc3.best.ggbs_frac + c32_xc3.best.fa_frac > 0


def test_severe_exposure_still_solvable():
    result = grid_search("C40/50", "XS3")
    assert result.feasible, "expected some feasible mix for C40/50 XS3"
    for mix in result.feasible[:50]:
        assert mix.wc_eff <= 0.45 + 1e-9
        assert mix.binder >= 380


def test_unknown_inputs_raise():
    with pytest.raises(ValueError):
        grid_search("C99/999", "XC1")
    with pytest.raises(ValueError):
        grid_search("C32/40", "XF4")
