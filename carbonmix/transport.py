"""Module A4 transport carbon, kept separate from the A1-A3 mass balance.

Why this module exists
----------------------
The headline saving in this tool is cradle-to-gate (modules A1-A3). That is
the standard basis for comparing concrete mixes and it stays the headline.
But it has a specific blind spot for exactly the substitution this tool
recommends: **GGBS usually travels further than cement.**

UK GGBS supply is concentrated around a small number of blast-furnace and
import terminals, while cement plants are more widely distributed. A mix
that looks better at the factory gate can be less good delivered, and a
tool that recommends 70% GGBS without ever mentioning haulage is answering
an easier question than the one that matters on site.

So: A4 is OPTIONAL and defaults to zero. With no distances supplied the
A1-A3 result is bit-for-bit unchanged. Supply distances and you get both
numbers reported side by side.

Data
----
``DEFAULT_TRANSPORT_FACTOR`` is an indicative figure for a rigid/artic
bulk tipper or powder tanker in kgCO2e per tonne-kilometre. Like every
other constant in this package it is a screening value, not a measured
one: real figures depend on vehicle class, load factor, backhaul and fuel.
Take them from the current UK Government GHG conversion factors, or from a
supplier's own EPD, before quoting any result.

Typical UK one-way haulage distances, offered as a starting point only and
NOT as defaults, because they vary enormously by site:

* cement from an integrated works: order 50-150 km
* GGBS from a works or import terminal: order 100-400 km
* fly ash from a coal station or ash recovery site: order 50-250 km
* aggregate from a quarry: order 20-80 km

Empty running is ignored. If you want it, inflate the factor rather than
the distance, because the return leg is not carrying your material.
"""

from __future__ import annotations

# kgCO2e per tonne-kilometre. Indicative HGV bulk haulage figure.
DEFAULT_TRANSPORT_FACTOR: float = 0.11

# Constituent -> the transport key it is hauled under. Sand and coarse
# aggregate share a key because they normally come from the same quarry.
_HAUL_KEY: dict[str, str] = {
    "cem1": "cem1",
    "ggbs": "ggbs",
    "fly_ash": "fly_ash",
    "coarse_agg": "aggregate",
    "sand": "aggregate",
    # water is mains-supplied and not hauled by road
}


def transport_carbon(
    masses: dict[str, float],
    distances_km: dict[str, float] | None = None,
    factor: float = DEFAULT_TRANSPORT_FACTOR,
) -> float:
    """Module A4 carbon for one m3 of concrete, kgCO2e.

    Parameters
    ----------
    masses:
        Constituent masses in kg per m3, as returned by
        :func:`carbonmix.carbon.mix_proportions`.
    distances_km:
        One-way haul distance per material key (``cem1``, ``ggbs``,
        ``fly_ash``, ``aggregate``). Missing keys are treated as zero, so
        a partial dict is allowed and simply ignores what it omits.
    factor:
        kgCO2e per tonne-kilometre.

    Returns
    -------
    float
        Zero when ``distances_km`` is ``None`` or empty, which is what
        keeps the A1-A3 headline unchanged by default.
    """
    if not distances_km:
        return 0.0
    if factor < 0:
        raise ValueError("transport factor must be non-negative")
    for k, v in distances_km.items():
        if v < 0:
            raise ValueError(f"distance for {k!r} must be non-negative")

    total = 0.0
    for material, mass in masses.items():
        key = _HAUL_KEY.get(material)
        if key is None:
            continue
        km = distances_km.get(key, 0.0)
        total += (mass / 1000.0) * km * factor  # kg -> tonnes
    return total


def parse_distances(spec: str | None) -> dict[str, float]:
    """Parse a CLI distance spec like ``"cem1=80,ggbs=300,aggregate=40"``."""
    if not spec:
        return {}
    out: dict[str, float] = {}
    valid = set(_HAUL_KEY.values())
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"expected key=km, got {part!r}")
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in valid:
            raise ValueError(f"unknown material {k!r}; expected one of {sorted(valid)}")
        try:
            out[k] = float(v)
        except ValueError:
            raise ValueError(f"distance for {k!r} must be a number, got {v!r}") from None
    return out
