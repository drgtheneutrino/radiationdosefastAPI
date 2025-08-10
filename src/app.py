"""
app.py
------
FastAPI entry point for the Radiation Dose Calculator API.

Routes:
- GET  /health
- GET  /v1/factors/tissue
- GET  /v1/factors/radiation
- POST /v1/dose/effective
- POST /v1/dose/convert/neutron-wr

Run locally:
    uvicorn src.app:app --reload

Swagger docs:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware  # <-- add this import

from src.schemas import DoseRequest, DoseResponse
from src.services.dose_service import compute_effective_dose, DoseComputationError
from src.services.factors import get_tissue_factors, get_base_wr, neutron_wr

# FastAPI app metadata
app = FastAPI(
    title="Radiation Dose Calculator API",
    version="0.1.0",
    description="""
A reference implementation of ICRP 103-based effective dose computation.

Notes:
- Units: input absorbed_dose_Gy (gray), output sievert (Sv).
- Effective dose is a reference person protection quantity, not a patient-specific risk.
""",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific domains in production
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict:
    """Simple health check to confirm API is alive."""
    return {"status": "ok"}


@app.get("/v1/factors/tissue")
def tissue_factors() -> dict:
    """Return ICRP 103 tissue weighting factors (w_T)."""
    return get_tissue_factors()


@app.get("/v1/factors/radiation")
def radiation_factors() -> dict:
    """
    Return base radiation weighting factors (w_R) for non-neutron types.
    Neutron values depend on energy; see /v1/dose/convert/neutron-wr.
    """
    return get_base_wr()


@app.post("/v1/dose/effective", response_model=DoseResponse)
def effective_dose(req: DoseRequest) -> DoseResponse:
    """
    Compute equivalent doses H_T and total effective dose E for the given scenario.
    """
    try:
        return compute_effective_dose(req)
    except DoseComputationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/dose/convert/neutron-wr")
def neutron_wr_endpoint(energy_MeV: float = Body(..., embed=True)) -> dict:
      """
    Compute neutron radiation weighting factor w_R from neutron energy in MeV.

    Example:
        POST /v1/dose/convert/neutron-wr
        {
            "energy_MeV": 2.0
        }
    """

    try:
        w_r = neutron_wr(float(energy_MeV))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"w_R": w_r}
