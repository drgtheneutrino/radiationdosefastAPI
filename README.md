# Radiation Dose Calculator API

A **FastAPI** service that computes equivalent dose (_H<sub>T</sub>_) and effective dose (_E_) from radiation exposure scenarios, based on **ICRP Publication 103 (2007)** tissue and radiation weighting factors.

## 📖 Overview

Effective dose (_E_) is calculated as:

\[
H_T = \sum_R w_R \cdot \overline{D}_{T,R}
\]
\[
E = \sum_T w_T \cdot H_T
\]

Where:
- _D<sub>T,R</sub>_ is the absorbed dose (Gy) in tissue _T_ from radiation type _R_.
- _w<sub>R</sub>_ is the radiation weighting factor for type _R_.
- _w<sub>T</sub>_ is the tissue weighting factor for tissue _T_.

> **Note:** Effective dose is a protection quantity for the **reference person** and should not be used to estimate individual patient risk.

---

## 📂 Project Structure
radiation-dose-api/
├─ src/
│ ├─ app.py # FastAPI entrypoint
│ ├─ schemas.py # Pydantic models for API IO
│ ├─ services/
│ │ ├─ dose_service.py # Core dose computation logic
│ │ └─ factors.py # ICRP 103 constants + neutron w_R(E)
├─ tests/ # Unit + endpoint tests
│ ├─ test_dose_math.py
│ └─ test_endpoints.py
├─ pyproject.toml
├─ README.md
└─ Dockerfile # Optional for containerization

yaml
Copy
Edit

---

## ⚡ Quick Start

### 1. Clone and install
```bash
git clone https://github.com/yourusername/radiation-dose-api.git
cd radiation-dose-api
pip install -e .[dev]
2. Run locally
bash
Copy
Edit
uvicorn src.app:app --reload
Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

🧪 Running Tests
bash
Copy
Edit
pytest
🔬 API Examples
Health check
bash
Copy
Edit
curl http://127.0.0.1:8000/health
Get tissue factors
bash
Copy
Edit
curl http://127.0.0.1:8000/v1/factors/tissue
Compute effective dose
bash
Copy
Edit
curl -X POST "http://127.0.0.1:8000/v1/dose/effective" \
     -H "Content-Type: application/json" \
     -d '{
           "irradiation": [
             {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.004},
             {"tissue": "colon", "radiation": "neutron", "neutron_energy_MeV": 2.0, "absorbed_dose_Gy": 0.001}
           ]
         }'
📊 Physics Data Sources
Tissue weighting factors (w<sub>T</sub>) and radiation weighting factors (w<sub>R</sub>) from:
International Commission on Radiological Protection, ICRP Publication 103, 2007.

Neutron w<sub>R</sub> energy dependence implemented per ICRP 103 piecewise function.
