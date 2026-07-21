"""Tests for the indicative durability screen."""

import pytest

from carbonmix.durability import (
    durability_failures,
    exposure_limits,
    meets_durability,
    within_replacement_caps,
)


def test_rejects_wc_above_cap():
    # XD3 cap is max w/c_eff 0.45
    assert not meets_durability("XD3", wc_eff=0.50, binder=400)
    assert meets_durability("XD3", wc_eff=0.44, binder=400)


def test_wc_exactly_on_cap_passes():
    assert meets_durability("XC3_XC4", wc_eff=0.55, binder=300)


def test_rejects_binder_below_minimum():
    assert not meets_durability("XS3", wc_eff=0.40, binder=350)
    assert meets_durability("XS3", wc_eff=0.40, binder=380)


def test_failure_reasons_are_reported():
    reasons = durability_failures("XS3", wc_eff=0.60, binder=300)
    assert len(reasons) == 2
    assert any("w/c" in r for r in reasons)
    assert any("binder" in r for r in reasons)


def test_replacement_caps():
    assert within_replacement_caps(0.70, 0.0)      # GGBS at cap
    assert not within_replacement_caps(0.75, 0.0)  # GGBS above cap
    assert within_replacement_caps(0.0, 0.35)      # fly ash at cap
    assert not within_replacement_caps(0.0, 0.40)  # fly ash above cap
    assert not within_replacement_caps(0.50, 0.25) # combined 75% > 70% cap
    assert within_replacement_caps(0.40, 0.30)     # combined exactly 70%


def test_unknown_exposure_raises():
    with pytest.raises(ValueError):
        exposure_limits("XF4")
