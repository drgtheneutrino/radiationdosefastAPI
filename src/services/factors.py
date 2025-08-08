"""
factors.py
----------
Stores and provides ICRP 103 tissue weighting factors (w_T) and radiation weighting factors (w_R),
including the energy-dependent formula for neutron weighting factors.

References:
- ICRP Publication 103, 2007. The 2007 Recommendations of the International Commission on Radiological Protection.
- NCBI Bookshelf: "Tissue Weighting Factors" table and "Radiation Weighting Factors" section.
- Neutron w_R formula per ICRP 103 piecewise definition.
"""

from typing import Dict

# ------------------------------
#  Tissue weighting factors (w_T)
# ------------------------------
# Units: dimensionless
# Sum of all weighting factors = 1.0
# These represent reference person fractional contribution to overall stochastic risk.

_TISSUE_WEIGHTING_FACTORS: Dict[str, float] = {
    # 0.12 group
    "red_bone_marrow": 0.12,
    "colon": 0.12,
    "lung": 0.12,
    "stomach": 0.12,
    "breast": 0.12,
    "remainder_tissues": 0.12,  # combined fraction for 14 remainder tissues

    # 0.08 group
    "gonads": 0.08,

    # 0.04 group
    "bladder": 0.04,
    "oesophagus": 0.04,
    "liver": 0.04,
    "thyroid": 0.04,

    # 0.01 group
    "bone_surface": 0.01,
    "brain": 0.01,
    "salivary_glands": 0.01,
    "skin": 0.01,
}

# Remainder tissues per ICRP 103 for documentation purposes
_REMAINDER_TISSUES_LIST = [
    "adrenals", "extrathoracic_region", "gall_bladder", "heart",
    "kidneys", "lymphatic_nodes", "muscle", "oral_mucosa",
    "pancreas", "prostate_or_uterus_cervix", "small_intestine",
    "spleen", "thymus", "tonsils"
]

# ------------------------------------
#  Base radiation weighting factors (w_R)
# ------------------------------------
# Units: dimensionless
# Not including neutron energy-dependent case.

_BASE_RADIATION_WEIGHTING_FACTORS: Dict[str, float] = {
    "photon": 1.0,
    "electron": 1.0,
    "muon": 1.0,
    "proton": 2.0,
    "pion": 2.0,
    "alpha": 20.0,
    "heavy_ion": 20.0
    # Neutrons handled separately via neutron_wr(E)
}

# -------------------------------------------------
#  Public access functions for factors
# -------------------------------------------------
def get_tissue_factors() -> Dict[str, float]:
    """
    Returns a copy of the ICRP 103 tissue weighting factors.

    :return: dict mapping tissue name to w_T
    """
    return _TISSUE_WEIGHTING_FACTORS.copy()

def get_base_wr() -> Dict[str, float]:
    """
    Returns a copy of the base radiation weighting factors (excluding neutrons).

    :return: dict mapping radiation type to w_R
    """
    return _BASE_RADIATION_WEIGHTING_FACTORS.copy()

# -------------------------------------------------
#  Neutron radiation weighting factor function
# -------------------------------------------------
def neutron_wr(energy_MeV: float) -> float:
    """
    Computes the energy-dependent radiation weighting factor w_R for neutrons
    as defined in ICRP Publication 103 (2007).

    The formula is piecewise, with E in MeV:
    1) For E < 1 MeV:
       w_R = 2.5 + 18.2 * exp(- (log(E))^2 / 6)
    2) For 1 MeV <= E <= 50 MeV:
       w_R = 5.0 + 17.0 * exp(- (log(E))^2 / 6)
    3) For E > 50 MeV:
       w_R = 2.5 + 3.25 * exp(- (log(0.04*E))^2 / 6)

    :param energy_MeV: neutron energy in MeV (must be > 0)
    :return: radiation weighting factor w_R (dimensionless)
    :raises ValueError: if energy_MeV <= 0
    """
    import math

    if energy_MeV <= 0:
        raise ValueError("Neutron energy must be greater than zero (MeV).")

    lnE = math.log(energy_MeV)

    if energy_MeV < 1.0:
        return 2.5 + 18.2 * math.exp(- (lnE ** 2) / 6.0)
    elif energy_MeV <= 50.0:
        return 5.0 + 17.0 * math.exp(- (lnE ** 2) / 6.0)
    else:
        return 2.5 + 3.25 * math.exp(- (math.log(0.04 * energy_MeV) ** 2) / 6.0)
