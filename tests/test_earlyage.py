"""Tests for early-age strength flagging."""

from __future__ import annotations

import pytest

from carbonmix.earlyage import (
    CEM1_RATIO,
    SCM_WARN_THRESHOLD,
    assess,
    early_ratio,
)


def test_28_day_ratio_is_one_for_every_mix():
    """f(28)/f(28) is 1.0 by definition, SCM content cannot change it."""
    assert early_ratio(28, 0.0, 0.0) == 1.0
    assert early_ratio(28, 0.7, 0.0) == 1.0
    assert early_ratio(28, 0.35, 0.35) == 1.0


def test_cem1_matches_the_published_ratios():
    for day, ratio in CEM1_RATIO.items():
        assert early_ratio(day, 0.0, 0.0) == pytest.approx(ratio)


def test_scm_reduces_early_strength():
    plain = early_ratio(7, 0.0, 0.0)
    blended = early_ratio(7, 0.5, 0.0)
    heavy = early_ratio(7, 0.7, 0.0)
    assert heavy < blended < plain


def test_ggbs_is_slower_than_fly_ash_at_early_age():
    assert early_ratio(7, 0.4, 0.0) < early_ratio(7, 0.0, 0.4)


def test_ratio_never_goes_non_positive():
    assert early_ratio(3, 0.7, 0.3) > 0


def test_unknown_day_rejected():
    with pytest.raises(ValueError):
        early_ratio(5, 0.0, 0.0)


@pytest.mark.parametrize("g,f", [(-0.1, 0.0), (0.0, -0.1), (0.8, 0.4)])
def test_invalid_fractions_rejected(g, f):
    with pytest.raises(ValueError):
        early_ratio(7, g, f)


def test_warns_above_threshold():
    note = assess(32.0, 0.6, 0.0)
    assert note.warn is True
    assert "EARLY-AGE WARNING" in note.message
    assert "striking" in note.message.lower()


def test_does_not_warn_below_threshold():
    note = assess(32.0, 0.2, 0.0)
    assert note.warn is False
    assert "WARNING" not in note.message


def test_threshold_boundary_is_strict():
    """Exactly at the threshold does not warn; above it does."""
    assert assess(32.0, SCM_WARN_THRESHOLD, 0.0).warn is False
    assert assess(32.0, SCM_WARN_THRESHOLD + 0.01, 0.0).warn is True


def test_combined_scm_counts_toward_the_threshold():
    """35% GGBS + 30% fly ash is 65% SCM and must warn."""
    assert assess(32.0, 0.35, 0.30).warn is True


def test_indicative_strength_is_consistent_with_the_ratio():
    note = assess(40.0, 0.5, 0.0)
    assert note.fck_7d_indicative == pytest.approx(40.0 * note.ratio_7d)
