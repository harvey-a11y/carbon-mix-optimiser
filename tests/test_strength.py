"""Tests for the Abrams-type strength model and k-value maths."""

import pytest

from carbonmix.strength import (
    STRENGTH_CLASSES,
    characteristic_strength,
    effective_wc,
    mean_strength,
    required_fck,
)


def test_strength_decreases_with_wc():
    strengths = [mean_strength(wc) for wc in (0.35, 0.45, 0.55, 0.65)]
    assert all(a > b for a, b in pairwise(strengths))


def test_default_constants_give_sane_strength_at_wc_050():
    # fcm = 110 / 10^0.5 = 34.785... MPa
    assert mean_strength(0.5) == pytest.approx(34.785, abs=0.01)


def test_k_value_hand_check():
    # water 165, cement 200, ggbs 200:
    # w/c_eff = 165 / (200 + 0.6 * 200) = 165 / 320 = 0.5156...
    wc_eff = effective_wc(water=165, cement=200, ggbs=200)
    assert wc_eff == pytest.approx(0.5156, abs=1e-4)
    assert wc_eff == pytest.approx(165 / 320)


def test_k_value_fly_ash_default():
    # water 160, cement 240, fly ash 100 -> 160 / (240 + 0.4*100) = 160/280
    assert effective_wc(160, 240, fly_ash=100) == pytest.approx(160 / 280)


def test_scm_raises_effective_wc_vs_plain_cement():
    plain = effective_wc(165, 400)
    blended = effective_wc(165, 200, ggbs=200)
    assert blended > plain  # k = 0.6 < 1.0, so GGBS counts for less


def test_characteristic_margin():
    assert characteristic_strength(40.0) == pytest.approx(32.0)


def test_strength_class_mapping():
    assert STRENGTH_CLASSES["C32/40"] == 32.0
    assert required_fck("C40/50") == 40.0
    with pytest.raises(ValueError):
        required_fck("C90/105")


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        effective_wc(165, 0)
    with pytest.raises(ValueError):
        mean_strength(0.0)
