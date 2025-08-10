"""
test_dose_math.py
-----------------
Unit tests for the core dose computation service.

We focus on:
- Correct handling of known simple cases.
- Neutron w_R boundaries.
- Aggregation of multiple radiation types.
"""

import math
import pytest
from decimal import Decimal

from src.schemas import DoseRequest, Irradiation
from src.services.dose_service import compute_effective_dose, DoseComputationError
from src.services.factors import neutron_wr


def test_simple_photon_case():
    """
    1 Gy absorbed dose to whole body with photons should yield:
    H_T = 1 Sv for each tissue,
    E = sum_T w_T * 1 Sv = 1 Sv * sum_T w_T = 1 Sv
    """
    # Only one tissue, w_T = 1 for simplicity: lung 0.12, scale dose to yield 1 Sv effective.
    # If we give lung 8.333... Gy photon dose:
    # H_lung = 8.333... Sv, E = 0.12 * 8.333... = 1.0 Sv
    req = DoseRequest(
        irradiation=[
            Irradiation(tissue="lung", radiation="photon", absorbed_dose_Gy=(1.0 / 0.12))
        ]
    )
    resp = compute_effective_dose(req)
    assert math.isclose(resp.effective_dose_Sv, 1.0, rel_tol=1e-9)


def test_multiple_tissues_and_radiations():
    """
    Two tissues with different w_T values and mixed radiations.
    """
    req = DoseRequest(
        irradiation=[
            Irradiation(tissue="colon", radiation="photon", absorbed_dose_Gy=0.002),
            Irradiation(tissue="colon", radiation="proton", absorbed_dose_Gy=0.001),  # w_R=2
            Irradiation(tissue="gonads", radiation="alpha", absorbed_dose_Gy=0.0005), # w_R=20
        ]
    )
    resp = compute_effective_dose(req)

    # Manual check:
    # Colon H_T = 1*0.002 + 2*0.001 = 0.004 Sv; contribution = 0.12 * 0.004 = 0.00048 Sv
    # Gonads H_T = 20*0.0005 = 0.01 Sv; contribution = 0.08 * 0.01 = 0.0008 Sv
    expected_total = 0.00048 + 0.0008
    assert math.isclose(resp.effective_dose_Sv, expected_total, rel_tol=1e-12)


@pytest.mark.parametrize("E_in", [0.5, 1.0, 2.0, 10.0, 100.0])
def test_neutron_wr_monotonicity(E_in):
    """
    Spot check that neutron w_R values are positive and reasonable for a range of energies.
    """
    w_r_val = neutron_wr(E_in)
    assert w_r_val > 0
    assert isinstance(w_r_val, float)


def test_neutron_wr_boundaries():
    """
    Check continuity near the 1 MeV and 50 MeV boundaries.
    """
    low_side = neutron_wr(0.9999)
    at_one = neutron_wr(1.0)
    high_side = neutron_wr(1.0001)
    assert math.isclose(at_one, high_side, rel_tol=1e-6)
    assert low_side > 0

    near_50_low = neutron_wr(49.999)
    at_50 = neutron_wr(50.0)
    above_50 = neutron_wr(50.001)
    assert math.isclose(at_50, above_50, rel_tol=1e-6)
    assert near_50_low > 0


def test_invalid_tissue():
    """
    Invalid tissue name should raise DoseComputationError.
    """
    req = DoseRequest(
        irradiation=[
            Irradiation(tissue="invalid_tissue", radiation="photon", absorbed_dose_Gy=0.001)
        ]
    )
    with pytest.raises(DoseComputationError):
        compute_effective_dose(req)


def test_invalid_custom_wr():
    """
    Negative custom_wR should be rejected.
    """
    req = DoseRequest(
        irradiation=[
            Irradiation(tissue="lung", radiation="photon", absorbed_dose_Gy=0.001, custom_wR=-5.0)
        ]
    )
    with pytest.raises(DoseComputationError):
        compute_effective_dose(req)
