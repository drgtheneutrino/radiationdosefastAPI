"""
factors.py
----------
ICRP 103 factor accessors backed by the repository JSON file at
src/data/icrp103_factors.json, validated through src/models.py.

This module exposes:
- get_tissue_factors() -> dict of w_T by tissue
- get_base_wr() -> dict of non-neutron w_R by radiation kind
- neutron_wr(E_MeV) -> energy dependent neutron w_R per ICRP 103
- get_remainder_tissues_list() -> list of the 14 remainder tissues

Design goals
- Single source of truth: numbers live in JSON and are validated by pydantic.
- Immutable API surface so other modules do not need to change.
- Clear physics comments and tight input validation for neutron w_R.
"""

from __future__ import annotations

from typing import Dict, List

# Load canonical factors from the validated JSON model.
# The loader in src.models is cached, so repeated calls are cheap.
from src.models import (
    get_tissue_factors_dict,
    get_base_wr_dict,
    get_remainder_tissues_list as _json_remainder_list,
)


# ------------------------------
# JSON backed factor tables
# ------------------------------

# These are plain dict or list snapshots taken at import time.
# They remain constant for the process lifetime.
_TISSUE_WEIGHTING_FACTORS: Dict[str, float] = get_tissue_factors_dict()
_BASE_RADIATION_WEIGHTING_FACTORS: Dict[str, float] = get_base_wr_dict()
_REMAINDER_TISSUES_LIST: List[str] = _json_remainder_list()


def get_tissue_factors() -> Dict[str, float]:
    """
    Return a shallow copy of ICRP 103 tissue weighting factors w_T.

    Units: dimensionless
    The factors are validated by src.models to sum to 1.0 within tolerance.
    """
    return _TISSUE_WEIGHTING_FACTORS.copy()


def get_base_wr() -> Dict[str, float]:
    """
    Return a shallow copy of base radiation weighting factors w_R
    for non neutron radiation kinds.

    Units: dimensionless
    """
    return _BASE_RADIATION_WEIGHTING_FACTORS.copy()


def get_remainder_tissues_list() -> List[str]:
    """
    Return a copy of the 14 remainder tissues that roll up under the
    'remainder_tissues' bucket in ICRP 103.
    """
    return list(_REMAINDER_TISSUES_LIST)


# -------------------------------------------------
# Neutron radiation weighting factor w_R(E)
# -------------------------------------------------

def neutron_wr(energy_MeV: float) -> float:
    """
    Compute the neutron radiation weighting factor w_R as a function of energy E in MeV,
    per ICRP Publication 103 piecewise definition. Natural logarithms are used.

    Piecewise definition with E in MeV:
      1) E < 1:
         w_R = 2.5 + 18.2 * exp(- (ln(E))^2 / 6)
      2) 1 <= E <= 50:
         w_R = 5.0 + 17.0 * exp(- (ln(E))^2 / 6)
      3) E > 50:
         w_R = 2.5 + 3.25 * exp(- (ln(0.04 * E))^2 / 6)

    Parameters
    ----------
    energy_MeV : float
        Neutron energy in MeV. Must be greater than 0.

    Returns
    -------
    float
        Radiation weighting factor w_R for neutrons.

    Raises
    ------
    ValueError
        If energy_MeV <= 0.
    """
    import math

    if energy_MeV <= 0.0:
        raise ValueError("Neutron energy must be greater than zero in MeV.")

    lnE = math.log(energy_MeV)

    if energy_MeV < 1.0:
        return 2.5 + 18.2 * math.exp(- (lnE ** 2) / 6.0)
    elif energy_MeV <= 50.0:
        return 5.0 + 17.0 * math.exp(- (lnE ** 2) / 6.0)
    else:
        # Note the shift in the argument for the high energy branch
        return 2.5 + 3.25 * math.exp(- (math.log(0.04 * energy_MeV) ** 2) / 6.0)
