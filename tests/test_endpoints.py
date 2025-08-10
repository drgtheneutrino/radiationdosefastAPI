"""
test_endpoints.py
-----------------
Integration tests for FastAPI routes.

Covers:
- /health
- /v1/factors/tissue
- /v1/factors/radiation
- /v1/dose/convert/neutron-wr
- /v1/dose/effective
- Error handling paths
"""

import math
from fastapi.testclient import TestClient

from src.app import app
from src.services.factors import get_tissue_factors, get_base_wr, neutron_wr

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_tissue_factors_endpoint():
    r = client.get("/v1/factors/tissue")
    assert r.status_code == 200
    data = r.json()
    ref = get_tissue_factors()
    # Ensure keys and values match reference
    assert set(data.keys()) == set(ref.keys())
    # Spot check sum to 1 within tight tolerance
    assert math.isclose(sum(data.values()), 1.0, rel_tol=1e-12)


def test_radiation_factors_endpoint():
    r = client.get("/v1/factors/radiation")
    assert r.status_code == 200
    data = r.json()
    ref = get_base_wr()
    assert data == ref
    # Neutrons are not listed here
    assert "neutron" not in data


def test_neutron_wr_endpoint_valid():
    payload = {"energy_MeV": 2.0}
    r = client.post("/v1/dose/convert/neutron-wr", json=payload)
    assert r.status_code == 200
    out = r.json()
    assert "w_R" in out and isinstance(out["w_R"], float)
    # Cross check against local function
    assert math.isclose(out["w_R"], neutron_wr(2.0), rel_tol=1e-12)


def test_neutron_wr_endpoint_invalid_energy():
    payload = {"energy_MeV": 0.0}
    r = client.post("/v1/dose/convert/neutron-wr", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "detail" in body
    assert "greater than zero" in body["detail"]


def test_effective_dose_endpoint_simple():
    """
    Case: one tissue, photons.
    Request H_lung = D * w_R with w_R=1.
    Choose dose so contribution equals a clean number.
    """
    payload = {
        "irradiation": [
            {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}
        ]
    }
    r = client.post("/v1/dose/effective", json=payload)
    assert r.status_code == 200
    out = r.json()
    assert "by_tissue" in out and "effective_dose_Sv" in out
    # H_lung = 0.01 Sv, contribution = 0.12 * 0.01 = 0.0012 Sv
    assert math.isclose(out["effective_dose_Sv"], 0.0012, rel_tol=1e-12)
    lung_rows = [row for row in out["by_tissue"] if row["tissue"] == "lung"]
    assert len(lung_rows) == 1
    lung = lung_rows[0]
    assert math.isclose(lung["H_T_Sv"], 0.01, rel_tol=1e-12)
    assert math.isclose(lung["w_T"], 0.12, rel_tol=1e-12)
    assert math.isclose(lung["contribution_to_E_Sv"], 0.0012, rel_tol=1e-12)


def test_effective_dose_with_neutrons_and_custom_wr():
    """
    Mixed case:
    - colon with neutrons at 2 MeV
    - gonads with custom w_R override
    """
    w_r_neutron = neutron_wr(2.0)
    payload = {
        "irradiation": [
            {"tissue": "colon", "radiation": "neutron", "neutron_energy_MeV": 2.0, "absorbed_dose_Gy": 0.001},
            {"tissue": "gonads", "radiation": "alpha", "absorbed_dose_Gy": 0.0005, "custom_wR": 10.0}
        ]
    }
    r = client.post("/v1/dose/effective", json=payload)
    assert r.status_code == 200
    out = r.json()

    # Manual contributions
    # Colon: H = w_r_neutron * 0.001 Sv, contrib = 0.12 * H
    colon_H = w_r_neutron * 0.001
    colon_E = 0.12 * colon_H
    # Gonads: H = 10.0 * 0.0005 = 0.005 Sv, contrib = 0.08 * 0.005 = 0.0004 Sv
    gonads_H = 0.005
    gonads_E = 0.0004
    expected_E = colon_E + gonads_E

    assert math.isclose(out["effective_dose_Sv"], expected_E, rel_tol=1e-12)

    # Check presence of both tissues
    tissues = {row["tissue"] for row in out["by_tissue"]}
    assert {"colon", "gonads"}.issubset(tissues)


def test_effective_dose_invalid_tissue_returns_400():
    payload = {
        "irradiation": [
            {"tissue": "not_a_tissue", "radiation": "photon", "absorbed_dose_Gy": 0.001}
        ]
    }
    r = client.post("/v1/dose/effective", json=payload)
    assert r.status_code == 400
    body = r.json()
    assert "detail" in body
    assert "Unknown tissue" in body["detail"]
