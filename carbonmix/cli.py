"""Command-line interface.

Usage::

    python -m carbonmix --class C32/40 --exposure XC3_XC4 --top 10 --plot out.png
"""

from __future__ import annotations

import argparse
import sys

from carbonmix import __version__
from carbonmix.data.durability_limits import DURABILITY_LIMITS
from carbonmix.optimise import OptimisationResult, grid_search
from carbonmix.strength import STRENGTH_CLASSES

DISCLAIMER = (
    "Screening estimates only - indicative data, simplified models. "
    "NOT a substitute for BS 8500 / EN 206 mix design or trial mixes."
)

# Chart colours (validated light-mode dataviz palette).
_SURFACE = "#fcfcfb"
_INK_PRIMARY = "#0b0b0b"
_INK_SECONDARY = "#52514e"
_INK_MUTED = "#898781"
_GRIDLINE = "#e1e0d9"
_AXIS = "#c3c2b7"
_SERIES_FEASIBLE = "#2a78d6"  # blue
_SERIES_BEST = "#eb6834"      # orange
_SERIES_BASELINE = "#1baf7a"  # aqua


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="carbonmix",
        description=(
            "Low-carbon concrete mix screening: rank feasible mixes by "
            "embodied carbon for a target strength and exposure class."
        ),
        epilog=DISCLAIMER,
    )
    parser.add_argument(
        "--class",
        dest="strength_class",
        required=True,
        choices=sorted(STRENGTH_CLASSES),
        metavar="CLASS",
        help=f"target strength class: {', '.join(STRENGTH_CLASSES)}",
    )
    parser.add_argument(
        "--exposure",
        required=True,
        choices=sorted(DURABILITY_LIMITS),
        metavar="EXPOSURE",
        help=f"exposure class: {', '.join(DURABILITY_LIMITS)}",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="number of top (lowest-carbon) mixes to print (default 10)",
    )
    parser.add_argument(
        "--plot",
        metavar="PATH",
        default=None,
        help="save a scatter plot (embodied carbon vs fck) to this PNG path",
    )
    parser.add_argument(
        "--version", action="version", version=f"carbonmix {__version__}"
    )
    return parser


def format_table(result: OptimisationResult, top: int) -> str:
    header = (
        f"{'#':>3}  {'binder':>7}  {'GGBS':>5}  {'FA':>4}  {'w/c':>5}  "
        f"{'w/c_eff':>7}  {'fck':>5}  {'kgCO2e/m3':>9}  {'saving':>7}"
    )
    units = (
        f"{'':>3}  {'kg/m3':>7}  {'%':>5}  {'%':>4}  {'':>5}  "
        f"{'':>7}  {'MPa':>5}  {'':>9}  {'vs CEM I':>8}"
    )
    lines = [header, units, "-" * len(header)]
    for rank, mix in enumerate(result.feasible[:top], start=1):
        saving = result.saving_vs_baseline(mix)
        saving_txt = f"{saving:6.1f}%" if saving is not None else "    n/a"
        lines.append(
            f"{rank:>3}  {mix.binder:>7.0f}  {mix.ggbs_pct:>5.0f}  "
            f"{mix.fa_pct:>4.0f}  {mix.wc:>5.2f}  {mix.wc_eff:>7.3f}  "
            f"{mix.fck:>5.1f}  {mix.carbon:>9.1f}  {saving_txt:>7}"
        )
    return "\n".join(lines)


def save_plot(result: OptimisationResult, path: str) -> None:
    """Scatter of embodied carbon vs estimated fck for all feasible mixes."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    best = result.best
    baseline = result.baseline
    others = [
        m for m in result.feasible if m is not best and m is not baseline
    ]

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    fig.patch.set_facecolor(_SURFACE)
    ax.set_facecolor(_SURFACE)

    ax.scatter(
        [m.fck for m in others],
        [m.carbon for m in others],
        s=26,
        color=_SERIES_FEASIBLE,
        edgecolors=_SURFACE,
        linewidths=0.6,
        label="Feasible mixes",
        zorder=2,
    )
    if baseline is not None:
        ax.scatter(
            [baseline.fck], [baseline.carbon],
            s=70, color=_SERIES_BASELINE, edgecolors=_SURFACE,
            linewidths=1.2, label="CEM I baseline", zorder=3,
        )
        ax.annotate(
            f"baseline {baseline.carbon:.0f}",
            (baseline.fck, baseline.carbon),
            textcoords="offset points", xytext=(8, 6),
            fontsize=8, color=_INK_SECONDARY, zorder=5,
            bbox={"facecolor": _SURFACE, "edgecolor": "none",
                  "alpha": 0.85, "pad": 1.5},
        )
    if best is not None:
        ax.scatter(
            [best.fck], [best.carbon],
            s=90, color=_SERIES_BEST, edgecolors=_SURFACE,
            linewidths=1.2, label="Best (lowest carbon)", zorder=4,
        )
        ax.annotate(
            f"best {best.carbon:.0f} kgCO2e/m3\n"
            f"{best.ggbs_pct:.0f}% GGBS, {best.fa_pct:.0f}% FA, "
            f"w/c {best.wc:.2f}",
            (best.fck, best.carbon),
            textcoords="offset points", xytext=(10, -4),
            fontsize=8, color=_INK_PRIMARY, zorder=5,
            bbox={"facecolor": _SURFACE, "edgecolor": "none",
                  "alpha": 0.85, "pad": 1.5},
        )

    ax.set_xlabel("Estimated characteristic strength fck (MPa)",
                  color=_INK_SECONDARY, fontsize=9)
    ax.set_ylabel("Embodied carbon (kgCO2e per m3)",
                  color=_INK_SECONDARY, fontsize=9)
    ax.set_title(
        f"Feasible mixes - {result.strength_class}, {result.exposure}",
        color=_INK_PRIMARY, fontsize=11, loc="left", pad=14,
    )
    ax.text(
        0, 1.015, "Screening estimates - indicative data, not BS 8500 design",
        transform=ax.transAxes, fontsize=7.5, color=_INK_MUTED,
    )

    ax.grid(True, color=_GRIDLINE, linewidth=0.7, zorder=0)
    ax.tick_params(colors=_INK_MUTED, labelsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_AXIS)
        ax.spines[side].set_linewidth(0.8)

    legend = ax.legend(
        loc="upper right", fontsize=8, frameon=True,
        labelcolor=_INK_SECONDARY, facecolor=_SURFACE,
        edgecolor=_GRIDLINE, framealpha=0.95,
    )
    for handle in legend.legend_handles:
        handle.set_edgecolor(_SURFACE)

    fig.tight_layout()
    fig.savefig(path, facecolor=_SURFACE)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.top < 1:
        print("error: --top must be >= 1", file=sys.stderr)
        return 2

    result = grid_search(args.strength_class, args.exposure)

    print(f"carbonmix {__version__} - low-carbon concrete mix screening")
    print(DISCLAIMER)
    print()
    print(
        f"Target: {args.strength_class} (fck >= "
        f"{STRENGTH_CLASSES[args.strength_class]:.0f} MPa), "
        f"exposure {args.exposure} "
        f"(max w/c_eff {DURABILITY_LIMITS[args.exposure]['max_wc']:.2f}, "
        f"min binder {DURABILITY_LIMITS[args.exposure]['min_binder']:.0f} kg/m3)"
    )
    print(
        f"Grid: {result.n_enumerated} combinations enumerated, "
        f"{len(result.feasible)} feasible"
    )
    print()

    if not result.feasible:
        print(
            "No feasible mix found in the search grid for this "
            "strength/exposure combination."
        )
        return 1

    print(f"Top {min(args.top, len(result.feasible))} mixes by embodied carbon:")
    print(format_table(result, args.top))
    print()

    if result.baseline is not None:
        b = result.baseline
        print(
            f"CEM I-only baseline: binder {b.binder:.0f} kg/m3, w/c {b.wc:.2f} "
            f"-> {b.carbon:.1f} kgCO2e/m3"
        )
        saving = result.saving_pct
        if saving is not None:
            print(
                f"Best mix saves {saving:.1f}% embodied carbon vs the "
                f"CEM I-only baseline."
            )
    else:
        print("No CEM I-only mix is feasible; no baseline saving reported.")

    if args.plot:
        save_plot(result, args.plot)
        print(f"Plot saved to {args.plot}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
