"""Tests for the Monte Carlo sensitivity analysis.

Draw counts are kept small deliberately: each draw runs a full grid search,
so a large count would make CI slow for no extra confidence in the plumbing.
The statistical result is checked in the technical note, not here.
"""

from __future__ import annotations

import pytest

from carbonmix.data import carbon_factors as cf_module
from carbonmix.sensitivity import FACTOR_RANGES, K1_RANGE, K2_RANGE, run


def test_runs_and_reports_a_distribution():
    res = run("C32/40", "XC3_XC4", draws=5, seed=1)
    assert res.n_draws == 5
    assert res.savings
    assert res.median is not None
    lo, hi = res.interval()
    assert lo <= res.median <= hi


def test_restores_the_global_carbon_factors():
    """The sampler patches a module-level dict. It must put it back."""
    before = dict(cf_module.CARBON_FACTORS)
    run("C32/40", "XC3_XC4", draws=3, seed=1)
    assert cf_module.CARBON_FACTORS == before


def test_restores_factors_even_if_a_draw_raises(monkeypatch):
    before = dict(cf_module.CARBON_FACTORS)

    def boom(*a, **k):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr("carbonmix.sensitivity.grid_search", boom)
    with pytest.raises(RuntimeError):
        run("C32/40", "XC3_XC4", draws=3, seed=1)
    assert cf_module.CARBON_FACTORS == before


def test_is_reproducible_for_a_given_seed():
    a = run("C32/40", "XC3_XC4", draws=5, seed=42)
    b = run("C32/40", "XC3_XC4", draws=5, seed=42)
    assert a.savings == b.savings


def test_different_seeds_give_different_draws():
    a = run("C32/40", "XC3_XC4", draws=5, seed=1)
    b = run("C32/40", "XC3_XC4", draws=5, seed=2)
    assert a.savings != b.savings


def test_rejects_zero_draws():
    with pytest.raises(ValueError):
        run("C32/40", "XC3_XC4", draws=0)


def test_ranges_are_ordered_and_positive():
    for name, (lo, hi) in FACTOR_RANGES.items():
        assert 0 < lo < hi, name
    assert 0 < K1_RANGE[0] < K1_RANGE[1]
    assert 1 < K2_RANGE[0] < K2_RANGE[1]


def test_default_factors_lie_inside_their_sampled_ranges():
    """A default outside its own range would mean one of them is wrong."""
    for name, (lo, hi) in FACTOR_RANGES.items():
        assert lo <= cf_module.CARBON_FACTORS[name] <= hi, name


def test_summary_is_readable():
    res = run("C32/40", "XC3_XC4", draws=5, seed=7)
    s = res.summary()
    assert "median" in s and "interval" in s
