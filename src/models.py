# --- top of file additions/changes ---
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple, TypedDict
from pydantic import BaseModel, field_validator, model_validator

import json
import os
from importlib import resources as importlib_resources  # robust package data loading

__all__ = [
    "ICRP103Factors",
    "load_icrp103_from_json",
    "get_tissue_factors_dict",
    "get_base_wr_dict",
    "get_remainder_tissues_list",
    "data_origin_path",
]

# Canonical names as immutable tuples
CANONICAL_TISSUES: Tuple[str, ...] = (
    "red_bone_marrow",
    "colon",
    "lung",
    "stomach",
    "breast",
    "remainder_tissues",
    "gonads",
    "bladder",
    "oesophagus",
    "liver",
    "thyroid",
    "bone_surface",
    "brain",
    "salivary_glands",
    "skin",
)

REMAINDER_TISSUES_EXPECTED: Tuple[str, ...] = (
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
)

BASE_RADIATION_KINDS: Tuple[str, ...] = (
    "photon",
    "electron",
    "muon",
    "proton",
    "pion",
    "alpha",
    "heavy_ion",
)

SUM_TOL = 1e-12
DATA_PACKAGE = "src"  # your package is literally named 'src'
DATA_RESOURCE = "data/icrp103_factors.json"


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
            raise ValueError(f"radiation_weighting_factors.base has unexpected keys: {sorted(extra)}")
        for k, v in self.base.items():
            if not isinstance(v, (int, float)):
                raise ValueError(f"w_R for '{k}' must be numeric, got {type(v).__name__}")
            if float(v) <= 0:
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
        exp = {"w_T": "dimensionless", "w_R": "dimensionless", "energy": "MeV"}
        for key, expected in exp.items():
            if key not in u:
                raise ValueError(f"units must contain '{key}'")
            if str(u[key]).lower() != expected:
                raise ValueError(f"units['{key}'] should be '{expected}', got '{u[key]}'")
        return u

    @model_validator(mode="after")
    def _validate_tissues(self) -> "ICRP103Factors":
        keys = list(self.tissue_weighting_factors.keys())
        if tuple(keys) != CANONICAL_TISSUES:
            raise ValueError(
                "tissue_weighting_factors keys must exactly match canonical list "
                f"(order sensitive). Expected {list(CANONICAL_TISSUES)}, got {keys}"
            )

        total = 0.0
        for t, w in self.tissue_weighting_factors.items():
            if not isinstance(w, (int, float)):
                raise ValueError(f"w_T for '{t}' must be numeric, got {type(w).__name__}")
            wf = float(w)
            if wf <= 0:
                raise ValueError(f"w_T for '{t}' must be > 0, got {w}")
            total += wf
        if abs(total - 1.0) > SUM_TOL:
            raise ValueError(f"Sum of tissue weighting factors must be 1.0, got {total}")

        if sorted(self.remainder_tissues_list) != sorted(REMAINDER_TISSUES_EXPECTED):
            raise ValueError(
                "remainder_tissues_list must contain the 14 ICRP 103 remainder tissues. "
                "See REMAINDER_TISSUES_EXPECTED."
            )
        return self


# ---- Data loading helpers using importlib.resources ----

def _load_resource_bytes() -> bytes:
    """
    Load the JSON data file from the installed package using importlib.resources.
    Falls back to filesystem path if needed for local dev.
    """
    try:
        # Try the packaged resource first
        with importlib_resources.files(DATA_PACKAGE).joinpath(DATA_RESOURCE).open("rb") as f:
            return f.read()
    except Exception:
        # Fallback: local filesystem relative to repo layout
        fallback_path = os.path.join(os.path.dirname(__file__), "data", "icrp103_factors.json")
        with open(fallback_path, "rb") as f:
            return f.read()


@lru_cache(maxsize=1)
def load_icrp103_from_json(path: Optional[str] = None) -> ICRP103Factors:
    """
    Load and validate ICRP 103 factor data from JSON.

    If 'path' is provided, load that file explicitly.
    Otherwise, load from the packaged resource with a filesystem fallback.

    Returns a cached pydantic model instance.
    """
    if path is not None:
        with open(path, "rb") as f:
            data = json.load(f)
        model = ICRP103Factors(**data)
        # Stash origin for debugging
        model._origin_path = os.path.abspath(path)  # type: ignore[attr-defined]
        return model

    raw = _load_resource_bytes()
    data = json.loads(raw.decode("utf-8"))
    model = ICRP103Factors(**data)
    model._origin_path = f"package:{DATA_PACKAGE}/{DATA_RESOURCE}"  # type: ignore[attr-defined]
    return model


def data_origin_path() -> str:
    """
    Returns a human friendly string indicating where the factors JSON was loaded from.
    """
    model = load_icrp103_from_json()
    return getattr(model, "_origin_path", "unknown")


def get_tissue_factors_dict(path: Optional[str] = None) -> Dict[str, float]:
    return load_icrp103_from_json(path).tissue_weighting_factors.copy()


def get_base_wr_dict(path: Optional[str] = None) -> Dict[str, float]:
    return load_icrp103_from_json(path).radiation_weighting_factors.base.copy()


def get_remainder_tissues_list(path: Optional[str] = None) -> List[str]:
    return list(load_icrp103_from_json(path).remainder_tissues_list)
