"""Embodied carbon factors and material constants for the mass balance.

INDICATIVE VALUES — the carbon factors are order-of-magnitude figures
based on ICE (Inventory of Carbon & Energy) database v3-era cradle-to-gate
values. Refresh them from the current ICE database (or supplier EPDs)
before quoting any number: real factors vary with plant, fuel mix,
transport distance and allocation method.

Factors are in kgCO2e per kg of material.
"""

CARBON_FACTORS: dict[str, float] = {
    "cem1": 0.91,        # CEM I Portland cement
    "ggbs": 0.08,        # ground granulated blast-furnace slag
    "fly_ash": 0.01,     # fly ash (PFA)
    "coarse_agg": 0.005, # crushed rock / gravel
    "sand": 0.005,       # fine aggregate
    "water": 0.0003,     # mains water
}

# Particle densities (kg/m3) used to fill 1 m3 by absolute volume.
PARTICLE_DENSITY: dict[str, float] = {
    "cem1": 3150.0,
    "ggbs": 2900.0,
    "fly_ash": 2300.0,
    "water": 1000.0,
    "aggregate": 2650.0,  # assumed identical for sand and coarse aggregate
}

# Assumed entrapped air content (volume fraction of the finished mix).
AIR_CONTENT: float = 0.02

# Split of total aggregate mass between fine and coarse fractions.
SAND_FRACTION: float = 0.40
COARSE_AGG_FRACTION: float = 0.60
