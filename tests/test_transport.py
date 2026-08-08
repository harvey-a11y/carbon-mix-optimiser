"""Tests for module A4 transport carbon."""

from __future__ import annotations

import pytest

from carbonmix.carbon import mix_proportions
from carbonmix.transport import (
    DEFAULT_TRANSPORT_FACTOR,
    parse_distances,
    transport_carbon,
)


def _masses():
    return mix_proportions(300, 0.45, 0.5, 0.0)


def test_no_distances_is_exactly_zero():
    """The whole point: A1-A3 must be unchanged unless distances are given."""
    assert transport_carbon(_masses()) == 0.0
    assert transport_carbon(_masses(), None) == 0.0
    assert transport_carbon(_masses(), {}) == 0.0


def test_zero_distance_is_zero():
    assert transport_carbon(_masses(), {"cem1": 0, "ggbs": 0, "aggregate": 0}) == 0.0


def test_scales_linearly_with_distance():
    m = _masses()
    a = transport_carbon(m, {"ggbs": 100})
    b = transport_carbon(m, {"ggbs": 200})
    assert b == pytest.approx(2 * a)


def test_scales_linearly_with_factor():
    m = _masses()
    a = transport_carbon(m, {"ggbs": 100}, factor=0.10)
    b = transport_carbon(m, {"ggbs": 100}, factor=0.20)
    assert b == pytest.approx(2 * a)


def test_hand_calculation():
    """One material, one distance, checked by hand."""
    masses = {"cem1": 1000.0}  # exactly one tonne
    got = transport_carbon(masses, {"cem1": 100.0}, factor=0.11)
    assert got == pytest.approx(1.0 * 100.0 * 0.11)  # 11.0 kgCO2e


def test_water_is_not_hauled():
    """Mains water has no road haulage term."""
    assert transport_carbon({"water": 5000.0}, {"cem1": 500, "aggregate": 500}) == 0.0


def test_sand_and_coarse_share_the_aggregate_distance():
    m = {"sand": 400.0, "coarse_agg": 600.0}
    got = transport_carbon(m, {"aggregate": 50.0}, factor=0.11)
    assert got == pytest.approx(1.0 * 50.0 * 0.11)


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        transport_carbon(_masses(), {"ggbs": -10})
    with pytest.raises(ValueError):
        transport_carbon(_masses(), {"ggbs": 10}, factor=-1)


def test_default_factor_is_used():
    m = {"cem1": 1000.0}
    assert transport_carbon(m, {"cem1": 10.0}) == pytest.approx(
        10.0 * DEFAULT_TRANSPORT_FACTOR
    )


@pytest.mark.parametrize(
    "spec,expected",
    [
        ("", {}),
        (None, {}),
        ("cem1=80", {"cem1": 80.0}),
        (
            "cem1=80,ggbs=300,aggregate=40",
            {"cem1": 80.0, "ggbs": 300.0, "aggregate": 40.0},
        ),
        (" cem1 = 80 , ggbs=300 ", {"cem1": 80.0, "ggbs": 300.0}),
    ],
)
def test_parse_distances(spec, expected):
    assert parse_distances(spec) == expected


@pytest.mark.parametrize("spec", ["cem1", "nonsense=10", "cem1=abc"])
def test_parse_distances_rejects_bad_input(spec):
    with pytest.raises(ValueError):
        parse_distances(spec)


def test_ggbs_haulage_can_erode_the_saving():
    """The reason this module exists: GGBS travelling further eats the saving."""
    best = mix_proportions(300, 0.35, 0.5, 0.0)      # blended
    baseline = mix_proportions(300, 0.43, 0.0, 0.0)  # CEM I only
    far = {"cem1": 80, "ggbs": 400, "aggregate": 40}
    a4_best = transport_carbon(best, far)
    a4_base = transport_carbon(baseline, far)
    # the blended mix hauls further, so it picks up MORE transport carbon
    assert a4_best > a4_base
