"""
dose_service.py
---------------
Core dose math for the Radiation Dose Calculator API.

Responsibilities:
- Validate incoming irradiation entries.
- Map tissues to ICRP 103 tissue weighting factors w_T.
- Map radiation types to weighting factors w_R, including neutron energy dependence.
- Aggregate absorbed doses by tissue to compute:
    H_T = sum_R w_R * D_{T,R}
    E   = sum_T w_T * H_T

Design notes:
- Internal arithmetic uses Decimal for stable sums.
- Conversion to float happens only at the API boundary.
- Validation is explicit and fails fast with helpful error messages.

This module is intentionally free of FastAPI specifics. It operates on
Pydantic request models and returns Pydantic response models.
"""

from __future__ import annotations

from decimal import Decimal, getcontext
from typing import Dict, Tuple

from src.schemas import (
    DoseRequest,
    DoseResponse,
    TissueContribution,
    Irradiation,
)
from src.services.factors import (
    get_tissue_factors,
    get_base_wr,
    neutron_wr,
)

# Set a reasonably high precision for Decimal to avoid accumulation errors.
# We quantize only at the API boundary.
getcontext().prec = 28


class DoseComputationError(ValueError):
    """Raised when inputs are inconsistent or not physically meaningful."""


# Cache factor tables once since they are constant for the process lifetime.
_TISSUE_WT: Dict[str, float] = get_tissue_factors()
_BASE_WR: Dict[str, float] = get_base_wr()

# Build a canonical set of valid tissues and a lowercase lookup for robustness.
_VALID_TISSUES = set(_TISSUE_WT.keys())
_TISSUE_ALIASES: Dict[str, str] = {
    # friendly aliases to canonical keys
    "rbm": "red_bone_marrow",
    "red bone marrow": "red_bone_marrow",
    "bone marrow": "red_bone_marrow",
    "esophagus": "oesophagus",  # common spelling variant
    "salivary glands": "salivary_glands",
    "bone surface": "bone_surface",
    "remainder": "remainder_tissues",
    "remainder tissues": "remainder_tissues",
}
# Build a quick lowercase map of canonical names to themselves for case-insensitive lookup.
for _canon in list(_VALID_TISSUES):
    _TISSUE_ALIASES[_canon.replace("_", " ")] = _canon


def _canonical_tissue(name: str) -> str:
    """
    Normalize a user-supplied tissue name to the canonical ICRP 103 key.

    Strategy:
    - Try direct hit.
    - Try lowercase and underscore normalization.
    - Try alias map.

    Raises:
        DoseComputationError if no mapping found.
    """
    if name in _VALID_TISSUES:
        return name

    key = name.strip().lower().replace("-", " ").replace("  ", " ")
    key_underscore = key.replace(" ", "_")

    if key_underscore in _VALID_TISSUES:
        return key_underscore
    if key in _TISSUE_ALIASES:
        return _TISSUE_ALIASES[key]

    raise DoseComputationError(
        f"Unknown tissue '{name}'. Allowed tissues include: {sorted(_VALID_TISSUES)}"
    )


def _resolve_wr(entry: Irradiation) -> Decimal:
    """
    Determine the radiation weighting factor w_R for a single irradiation entry.

    Rules:
    - If custom_wR provided, must be positive and will be used exactly.
    - If radiation is neutron, require energy unless custom_wR present.
    - Else use base w_R table.

    Returns:
        Decimal w_R

    Raises:
        DoseComputationError for invalid or missing parameters.
    """
    if entry.custom_wR is not None:
        if entry.custom_wR <= 0:
            raise DoseComputationError("custom_wR must be greater than zero.")
        return Decimal(str(entry.custom_wR))

    kind = entry.radiation

    if kind == "neutron":
        if entry.neutron_energy_MeV is None:
            raise DoseComputationError(
                "neutron_energy_MeV is required for neutron radiation when custom_wR is not provided."
            )
        wr_val = neutron_wr(float(entry.neutron_energy_MeV))
        return Decimal(str(wr_val))

    # Non-neutron case
    if kind not in _BASE_WR:
        raise DoseComputationError(
            f"Unknown radiation kind '{kind}'. Valid kinds: {sorted(list(_BASE_WR.keys()) + ['neutron'])}"
        )
    return Decimal(str(_BASE_WR[kind]))


def _quantize_float(x: Decimal) -> float:
    """
    Convert Decimal to float for Pydantic response.
    We do not hard round here, but Decimal to float is enough for API serialization.
    Any UI rounding should happen at presentation time.
    """
    return float(x)


def compute_effective_dose(req: DoseRequest) -> DoseResponse:
    """
    Compute H_T by tissue and total effective dose E for the given request.

    Steps:
    1. Validate and canonicalize tissue names.
    2. Resolve w_R per entry.
    3. Accumulate H_T per tissue as sum_R w_R * D_{T,R}.
    4. Compute E as sum_T w_T * H_T.
    5. Return detailed by-tissue contributions and total E.

    Input units:
        absorbed_dose_Gy is in gray.
    Output units:
        H_T in sievert.
        E in sievert.
        Since sievert equals gray times w_R for stochastic quantities, units match.

    Raises:
        DoseComputationError for invalid inputs.
    """
    if not req.irradiation:
        raise DoseComputationError("At least one irradiation entry is required.")

    # Accumulator for H_T by tissue.
    # Dict[tissue, Decimal sievert]
    H_by_tissue: Dict[str, Decimal] = {}

    for entry in req.irradiation:
        # Pydantic already enforces absorbed_dose_Gy > 0, but we re-check to be explicit.
        if entry.absorbed_dose_Gy <= 0:
            raise DoseComputationError("absorbed_dose_Gy must be greater than zero.")

        tissue = _canonical_tissue(entry.tissue)
        w_r = _resolve_wr(entry)
        D_T_R = Decimal(str(entry.absorbed_dose_Gy))  # gray

        H_increment = w_r * D_T_R  # sievert contribution for this radiation to this tissue
        H_by_tissue[tissue] = H_by_tissue.get(tissue, Decimal("0")) + H_increment

    # Compute contributions to E per tissue and total E.
    contributions = []
    E_total = Decimal("0")

    for tissue, H_T in H_by_tissue.items():
        w_T = Decimal(str(_TISSUE_WT[tissue]))
        contribution = w_T * H_T
        E_total += contribution

        contributions.append(
            TissueContribution(
                tissue=tissue,
                w_T=_quantize_float(w_T),
                H_T_Sv=_quantize_float(H_T),
                contribution_to_E_Sv=_quantize_float(contribution),
            )
        )

    # Sort by descending contribution for easy reading.
    contributions.sort(key=lambda c: c.contribution_to_E_Sv, reverse=True)

    return DoseResponse(
        by_tissue=contributions,
        effective_dose_Sv=_quantize_float(E_total),
    )
