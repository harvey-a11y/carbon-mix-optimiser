"""Tests for the command-line interface: table formatting and exit codes."""

import pytest

from carbonmix import __version__
from carbonmix.cli import build_parser, format_table, main
from carbonmix.optimise import MixCandidate, OptimisationResult


def make_mix(**overrides):
    """A hand-built candidate matching the README's #1 mix for C32/40 XC3_XC4."""
    values = {
        "binder": 300.0, "wc": 0.35, "ggbs_frac": 0.50, "fa_frac": 0.0,
        "wc_eff": 0.437, "fcm": 40.2, "fck": 32.2, "carbon": 158.8, "masses": {},
    }
    values.update(overrides)
    return MixCandidate(**values)


def make_result(feasible, baseline=None, n_enumerated=57040):
    return OptimisationResult(
        strength_class="C32/40",
        exposure="XC3_XC4",
        feasible=feasible,
        baseline=baseline,
        n_enumerated=n_enumerated,
    )


# --- format_table -----------------------------------------------------------


def test_format_table_known_result_set():
    baseline = make_mix(
        ggbs_frac=0.0, wc=0.43, wc_eff=0.43, fck=34.4, carbon=283.1
    )
    second = make_mix(binder=310.0, carbon=163.7)
    result = make_result([make_mix(), second, baseline], baseline=baseline)

    lines = format_table(result, top=2).splitlines()
    assert len(lines) == 5  # header + units + rule + 2 rows
    assert lines[0].split() == [
        "#", "binder", "GGBS", "FA", "w/c", "w/c_eff", "fck",
        "kgCO2e/m3", "saving",
    ]
    assert lines[1].split() == ["kg/m3", "%", "%", "MPa", "vs", "CEM", "I"]
    assert lines[2] == "-" * len(lines[0])
    # Byte-exact rows as shown in the README example output.
    assert lines[3] == (
        "  1      300     50     0   0.35    0.437   32.2      158.8    43.9%"
    )
    assert lines[4] == (
        "  2      310     50     0   0.35    0.437   32.2      163.7    42.2%"
    )


def test_format_table_truncates_to_top():
    mixes = [make_mix(carbon=c) for c in (150.0, 151.0, 152.0, 153.0)]
    result = make_result(mixes, baseline=mixes[-1])
    assert len(format_table(result, top=2).splitlines()) == 5
    # top larger than the feasible set prints every mix, no padding rows
    assert len(format_table(result, top=99).splitlines()) == 7


def test_format_table_without_baseline_prints_na():
    result = make_result([make_mix()])
    row = format_table(result, top=5).splitlines()[3]
    assert row.endswith("n/a")


# --- main(): exit code 0 (feasible results) ---------------------------------


def test_main_feasible_run_exits_zero(capsys):
    code = main(["--class", "C32/40", "--exposure", "XC3_XC4", "--top", "3"])
    out = capsys.readouterr().out
    assert code == 0
    assert f"carbonmix {__version__}" in out
    assert "Target: C32/40 (fck >= 32 MPa), exposure XC3_XC4" in out
    # These lines are quoted verbatim in the README example output.
    assert "Grid: 57040 combinations enumerated, 2688 feasible" in out
    assert "Top 3 mixes by embodied carbon:" in out
    assert (
        "  1      300     50     0   0.35    0.437   32.2      158.8    43.9%"
        in out
    )
    assert (
        "CEM I-only baseline: binder 300 kg/m3, w/c 0.43 -> 283.1 kgCO2e/m3"
        in out
    )
    assert "Best mix saves 43.9% embodied carbon" in out


def test_main_reports_no_baseline_when_missing(capsys, monkeypatch):
    result = make_result([make_mix()], baseline=None)
    monkeypatch.setattr("carbonmix.cli.grid_search", lambda *a, **kw: result)
    code = main(["--class", "C32/40", "--exposure", "XC3_XC4"])
    out = capsys.readouterr().out
    assert code == 0
    assert "No CEM I-only mix is feasible" in out


def test_main_plot_flag_writes_png(tmp_path, capsys):
    pytest.importorskip("matplotlib")
    path = tmp_path / "out.png"
    code = main([
        "--class", "C32/40", "--exposure", "XC3_XC4",
        "--top", "1", "--plot", str(path),
    ])
    out = capsys.readouterr().out
    assert code == 0
    assert f"Plot saved to {path}" in out
    assert path.is_file() and path.stat().st_size > 0


# --- main(): exit code 1 (no feasible mix) ----------------------------------


def test_main_no_feasible_mix_exits_one(capsys, monkeypatch):
    empty = make_result([], baseline=None)
    monkeypatch.setattr("carbonmix.cli.grid_search", lambda *a, **kw: empty)
    code = main(["--class", "C40/50", "--exposure", "XS3"])
    out = capsys.readouterr().out
    assert code == 1
    assert "No feasible mix found" in out


# --- main(): exit code 2 (bad arguments) ------------------------------------


def test_main_rejects_top_below_one(capsys):
    code = main(["--class", "C32/40", "--exposure", "XC3_XC4", "--top", "0"])
    captured = capsys.readouterr()
    assert code == 2
    assert "--top must be >= 1" in captured.err


def test_main_rejects_unknown_strength_class(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--class", "C99/999", "--exposure", "XC3_XC4"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_main_rejects_unknown_exposure(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--class", "C32/40", "--exposure", "XF4"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_main_requires_class_and_exposure(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


# --- --version --------------------------------------------------------------


def test_version_flag_reports_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["--version"])
    assert excinfo.value.code == 0
    assert f"carbonmix {__version__}" in capsys.readouterr().out
