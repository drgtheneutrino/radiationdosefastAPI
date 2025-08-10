"""
models.py
---------
Domain models and validated loader for ICRP 103 factor data stored in
src/data/icrp103_factors.json.

This module is optional for the API runtime but useful for:
- validating the JSON factors file at import or test time
- providing a single place to read factor tables from disk
- documenting canonical tissue and radiation names

The FastAPI service currently uses src/services/factors.py for fast, in-code
constants. You can switch that module to call these helpers if you want the
JSON file to be the single source of truth.

Usage example
-------------
from src.models import load_icrp103_from_json, get_tissue_factors_dict
factors = load_icrp103_from_json()        # validated object model
tissue_wt = get_tissue_factors_dict()     # plain dict copy
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, TypedDict

import json
from pydantic import BaseModel, field_validator, model_validator


# -------------------------------
# Canonical names and type hints
# -------------------------------

CANONICAL_TISSUES: List[str] = [
    # 0.12 group
    "red_bone_marrow",
    "colon",
    "lung",
    "stomach",
    "breast",
    "remainder_tissues",
    # 0.08 group
    "gonads",
    # 0.04 group
    "bladder",
    "oesophagus",
    "liver",
    "thyroid",
    # 0.01 group
    "bone_surface",
    "brain",
    "salivary_glands",
    "skin",
]

REMAINDER_TISSUES_EXPECTED: List[str] = [
    "adrenals",
    "extrathoracic_region",
    "gall_bladder",
    "heart",
    "kidneys",
    "lymphatic_nodes",
    "muscle",
    "oral_mucosa",
    "pancreas",
    "prostate_or_uterus_cervix",
    "small_intestine",
    "spleen",
    "thymus",
    "tonsils",
]

BASE_RADIATION_KINDS: List[str] = [
    "photon",
    "electron",
    "muon",
    "proton",
    "pion",
    "alpha",
    "heavy_ion",
    # neutron is handled separately by energy dependent function
]

# Tight numeric tolerances for validations
SUM_TOL = 1e-12


# -------------------------------
# Pydantic models for the JSON
# -------------------------------

class NeutronWRPiece(TypedDict):
    range: str
    expression: str


class RadiationWeightingFactorsModel(BaseModel):
    base: Dict[str, float]
    neutron_wr_definition: Dict[str, List[NeutronWRPiece]]

    @model_validator(mode="after")
    def _validate_base_keys(self) -> "RadiationWeightingFactorsModel":
        base_keys: Set[str] = set(self.base.keys())
        expected_keys = set(BASE_RADIATION_KINDS)
        missing = expected_keys.difference(base_keys)
        extra = base_keys.difference(expected_keys)
        if missing:
            raise ValueError(f"radiation_weighting_factors.base missing keys: {sorted(missing)}")
        if extra:
            # Allow extra keys only if they are clearly documented by the JSON
            raise ValueError(f"radiation_weighting_factors.base has unexpected keys: {sorted(extra)}")
        # All base values must be positive
        for k, v in self.base.items():
            if v <= 0:
                raise ValueError(f"w_R for '{k}' must be > 0, got {v}")
        return self


class ICRP103Factors(BaseModel):
    icrp_publication: str
    version: str
    units: Dict[str, str]
    tissue_weighting_factors: Dict[str, float]
    remainder_tissues_list: List[str]
    radiation_weighting_factors: RadiationWeightingFactorsModel

    @field_validator("icrp_publication")
    @classmethod
    def _validate_pub(cls, v: str) -> str:
        if v.strip() != "103":
            raise ValueError("icrp_publication must be '103'")
        return v

    @field_validator("units")
    @classmethod
    def _validate_units(cls, u: Dict[str, str]) -> Dict[str, str]:
        # Soft validation of expected unit strings
        exp = {"w_T": "dimensionless", "w_R": "dimensionless", "energy": "MeV"}
        for key, expected in exp.items():
            if key not in u:
                raise ValueError(f"units must contain '{key}'")
            # Do not force exact match to allow future clarifications, but warn if mismatch
            if str(u[key]).lower() != expected:
                raise ValueError(f"units['{key}'] should be '{expected}', got '{u[key]}'")
        return u

    @model_validator(mode="after")
    def _validate_tissues(self) -> "ICRP103Factors":
        keys = list(self.tissue_weighting_factors.keys())
        if keys != CANONICAL_TISSUES:
            # Enforce order and content to avoid accidental renaming
            raise ValueError(
                "tissue_weighting_factors keys must exactly match canonical list "
                f"(order sensitive). Expected {CANONICAL_TISSUES}, got {keys}"
            )

        # All weights positive
        for t, w in self.tissue_weighting_factors.items():
            if w <= 0:
                raise ValueError(f"w_T for '{t}' must be > 0, got {w}")

        # Sum to 1 within tolerance
        total = sum(self.tissue_weighting_factors.values())
        if abs(total - 1.0) > SUM_TOL:
            raise ValueError(f"Sum of tissue weighting factors must be 1.0, got {total}")

        # Remainder list must be exactly the expected 14 tissues
        if sorted(self.remainder_tissues_list) != sorted(REMAINDER_TISSUES_EXPECTED):
            raise ValueError(
                "remainder_tissues_list must contain the 14 ICRP 103 remainder tissues. "
                "See REMAINDER_TISSUES_EXPECTED."
            )
        return self


# -------------------------------
# Loader helpers
# -------------------------------

def _default_json_path() -> Path:
    """
    Compute the default absolute path to src/data/icrp103_factors.json.
    """
    return Path(__file__).resolve().parent / "data" / "icrp103_factors.json"


@lru_cache(maxsize=1)
def load_icrp103_from_json(path: Optional[str] = None) -> ICRP103Factors:
    """
    Load and validate ICRP 103 factor data from JSON.

    Caching
    - Results are cached, since the file is static for a given process.

    :param path: optional explicit path to the JSON file
    :return: validated ICRP103Factors model
    :raises FileNotFoundError: if the file does not exist
    :raises ValueError: if validation fails
    """
    json_path = Path(path) if path is not None else _default_json_path()
    if not json_path.exists():
        raise FileNotFoundError(f"ICRP 103 JSON file not found at {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate and return
    return ICRP103Factors(**data)


def get_tissue_factors_dict(path: Optional[str] = None) -> Dict[str, float]:
    """
    Convenience accessor that returns a shallow copy of w_T as a plain dict.
    """
    return load_icrp103_from_json(path).tissue_weighting_factors.copy()


def get_base_wr_dict(path: Optional[str] = None) -> Dict[str, float]:
    """
    Convenience accessor that returns a shallow copy of non-neutron w_R as a plain dict.
    """
    return load_icrp103_from_json(path).radiation_weighting_factors.base.copy()


def get_remainder_tissues_list(path: Optional[str] = None) -> List[str]:
    """
    Convenience accessor that returns a copy of the 14 remainder tissues.
    """
    return list(load_icrp103_from_json(path).remainder_tissues_list)
