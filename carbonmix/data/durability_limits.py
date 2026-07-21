"""Indicative BS 8500-style durability limits per exposure class.

INDICATIVE VALUES — verify against the current BS 8500-1 Table A.4 / A.5
before using any output for real design work. These figures are
BS 8500-*style* screening limits chosen for a coursework tool; they are
not a transcription of the standard, they ignore cover/cement-type
interactions, intended working life, and aggregate size adjustments, and
the standard is revised periodically.

``max_wc`` is the maximum water/binder ratio (applied here to the
EN 206 k-value *effective* w/c ratio) and ``min_binder`` is the minimum
total binder content in kg/m3.
"""

DURABILITY_LIMITS: dict[str, dict[str, float]] = {
    # Carbonation, dry or permanently wet (interior)
    "XC1": {"max_wc": 0.65, "min_binder": 260},
    # Carbonation, moderate humidity / cyclic wet-dry (external verticals)
    "XC3_XC4": {"max_wc": 0.55, "min_binder": 300},
    # Chlorides other than seawater, cyclic wet-dry (e.g. de-icing salt spray)
    "XD3": {"max_wc": 0.45, "min_binder": 360},
    # Seawater, tidal / splash / spray zones
    "XS3": {"max_wc": 0.45, "min_binder": 380},
}

# Replacement caps on supplementary cementitious materials (fractions of
# total binder mass). Indicative of common BS 8500 cement-type limits
# (e.g. CEM III/B-type GGBS levels, CEM II/B-V-type fly ash levels).
MAX_GGBS_FRACTION: float = 0.70
MAX_FA_FRACTION: float = 0.35
MAX_COMBINED_SCM_FRACTION: float = 0.70
