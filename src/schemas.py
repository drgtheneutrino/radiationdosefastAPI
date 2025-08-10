"""
schemas.py
----------
Pydantic models for request and response payloads used by the Radiation Dose Calculator API.

Key conventions
- Units:
    absorbed_dose_Gy: gray (Gy)
    H_T_Sv, contribution_to_E_Sv, effective_dose_Sv: sievert (Sv)
- Radiation kinds are constrained to a fixed set of strings via Literal.
- Validation:
    - absorbed_dose_Gy must be > 0
    - tissue is stripped of surrounding whitespace
    - neutron parameters are not enforced here because custom_wR can override;
      that logic is handled in the service layer.

These models are deliberately API focused and contain no physics logic.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Allowed radiation kinds for API inputs
RadiationKind = Literal[
    "photon",       # gamma or x ray
    "electron",
    "muon",
    "proton",
    "pion",
    "alpha",
    "heavy_ion",
    "neutron",
]


class Irradiation(BaseModel):
    """
    Single irradiation record for one tissue and one radiation type.

    Notes
    - If radiation == "neutron" and custom_wR is not provided, the service layer
      will require neutron_energy_MeV to compute w_R(E).
    - If custom_wR is provided, it takes precedence for research or what-if analysis.
    """
    tissue: str = Field(..., description="ICRP 103 tissue name or alias, e.g., 'lung' or 'red_bone_marrow'.")
    radiation: RadiationKind = Field(..., description="Particle or photon category.")
    absorbed_dose_Gy: float = Field(..., gt=0.0, description="Absorbed dose in gray for this tissue and radiation.")
    neutron_energy_MeV: Optional[float] = Field(
        None,
        description="Neutron energy in MeV. Required if radiation == 'neutron' and custom_wR is not given."
    )
    custom_wR: Optional[float] = Field(
        None,
        description="Optional override for radiation weighting factor w_R. Must be positive if provided."
    )

    @field_validator("tissue")
    @classmethod
    def _strip_tissue(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("tissue must be a non-empty string.")
        return v

    @field_validator("custom_wR")
    @classmethod
    def _validate_custom_wr(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        if v <= 0:
            raise ValueError("custom_wR must be greater than zero when provided.")
        return v


class DoseRequest(BaseModel):
    """
    Batch of irradiation entries forming one effective dose computation.
    """
    irradiation: List[Irradiation] = Field(..., description="List of per-tissue, per-radiation dose entries.")


class TissueContribution(BaseModel):
    """
    Contribution of a single tissue to the total effective dose.

    Fields
    - tissue: canonical tissue name as used internally.
    - w_T: tissue weighting factor from ICRP 103.
    - H_T_Sv: equivalent dose to the tissue in sievert.
    - contribution_to_E_Sv: w_T * H_T contribution to effective dose.
    """
    tissue: str
    w_T: float
    H_T_Sv: float
    contribution_to_E_Sv: float


class DoseResponse(BaseModel):
    """
    Full result payload for an effective dose computation.
    """
    by_tissue: List[TissueContribution]
    effective_dose_Sv: float
class TissueEquivalent(BaseModel):
    """
    Equivalent dose for a single tissue.
    """
    tissue: str
    H_T_Sv: float


class EquivalentDoseResponse(BaseModel):
    """
    Response for the equivalent dose endpoint.
    """
    by_tissue: List[TissueEquivalent]

