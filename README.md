# Radiation Dose Calculator API

A FastAPI-based implementation of ICRP Publication 103 radiation dose calculations for effective dose computation. This API provides precise, validated calculations for radiation protection and dosimetry applications.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Features

- **ICRP 103 Compliant**: Full implementation of tissue weighting factors (w_T) and radiation weighting factors (w_R)
- **Multi-Radiation Support**: Photons, electrons, muons, protons, pions, alpha particles, heavy ions, and neutrons
- **Energy-Dependent Neutron Calculations**: Automatic w_R calculation based on neutron energy (MeV)
- **Smart Tissue Mapping**: Flexible tissue name resolution with aliases and remainder tissue handling
- **High-Precision Arithmetic**: Uses Python's Decimal class for stable dose calculations
- **Comprehensive Validation**: Extensive input validation with clear error messages
- **RESTful API**: Clean, documented REST endpoints with OpenAPI/Swagger integration
- **Production Ready**: CORS support, error handling, and structured logging

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd radiation-dose-api

# Install dependencies
pip install -r requirements.txt

# Or install from pyproject.toml
pip install -e .
```

### Running the API

```bash
# Start the development server
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# The API will be available at:
# - API Base: http://localhost:8000
# - Interactive Docs: http://localhost:8000/docs
# - OpenAPI Schema: http://localhost:8000/openapi.json
```

### Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Simple dose calculation
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}
    ]
  }'
```

Expected result: `{"by_tissue": [...], "effective_dose_Sv": 0.0012}`

## 📚 API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check |
| GET | `/v1/factors/tissue` | ICRP 103 tissue weighting factors (w_T) |
| GET | `/v1/factors/radiation` | Base radiation weighting factors (w_R) |
| POST | `/v1/dose/effective` | Calculate effective dose E (Sv) |
| POST | `/v1/dose/equivalent` | Calculate equivalent dose H_T by tissue (Sv) |
| POST | `/v1/dose/convert/neutron-wr` | Get neutron w_R from energy |

### Interactive Documentation

Visit `http://localhost:8000/docs` for full interactive API documentation with:
- Live endpoint testing
- Request/response schemas
- Example payloads
- Parameter descriptions

## 🧬 Supported Tissues

### Primary Tissues (ICRP 103)
- **High Risk** (w_T = 0.12): red_bone_marrow, colon, lung, stomach, breast, remainder_tissues
- **Medium Risk** (w_T = 0.08): gonads
- **Lower Risk** (w_T = 0.04): bladder, oesophagus, liver, thyroid
- **Low Risk** (w_T = 0.01): bone_surface, brain, salivary_glands, skin

### Remainder Tissues
The following tissues automatically map to `remainder_tissues`:
- adrenals, extrathoracic_region, gall_bladder, heart
- kidneys, lymphatic_nodes, muscle, oral_mucosa
- pancreas, prostate_or_uterus_cervix, small_intestine
- spleen, thymus, tonsils

### Tissue Aliases
The API accepts flexible tissue names:
- `"rbm"` → `"red_bone_marrow"`
- `"esophagus"` → `"oesophagus"`
- `"bone marrow"` → `"red_bone_marrow"`
- `"salivary glands"` → `"salivary_glands"`
- Case-insensitive matching with space/underscore normalization

## ⚛️ Radiation Types and Weighting Factors

| Radiation Type | w_R Value | Notes |
|----------------|-----------|-------|
| photon (γ, X-ray) | 1.0 | Standard reference |
| electron (β⁻, β⁺) | 1.0 | |
| muon | 1.0 | |
| proton | 2.0 | |
| pion | 2.0 | |
| alpha | 20.0 | High biological effectiveness |
| heavy_ion | 20.0 | |
| neutron | f(energy) | Energy-dependent per ICRP 103 |

### Neutron Energy Dependence

Neutron radiation weighting factor follows ICRP 103's piecewise function:

- **E < 1 MeV**: w_R = 2.5 + 18.2 × exp(-(ln(E))²/6)
- **1 ≤ E ≤ 50 MeV**: w_R = 5.0 + 17.0 × exp(-(ln(E))²/6)
- **E > 50 MeV**: w_R = 2.5 + 3.25 × exp(-(ln(0.04×E))²/6)

## 💡 Usage Examples

### Basic Photon Exposure
```json
POST /v1/dose/effective
{
  "irradiation": [
    {
      "tissue": "lung",
      "radiation": "photon",
      "absorbed_dose_Gy": 0.005
    }
  ]
}
```

### Multiple Tissues and Radiation Types
```json
POST /v1/dose/effective
{
  "irradiation": [
    {
      "tissue": "colon",
      "radiation": "photon", 
      "absorbed_dose_Gy": 0.002
    },
    {
      "tissue": "colon",
      "radiation": "proton",
      "absorbed_dose_Gy": 0.001
    },
    {
      "tissue": "gonads",
      "radiation": "alpha",
      "absorbed_dose_Gy": 0.0005
    }
  ]
}
```

### Neutron Exposure with Energy Dependence
```json
POST /v1/dose/effective
{
  "irradiation": [
    {
      "tissue": "red_bone_marrow",
      "radiation": "neutron",
      "neutron_energy_MeV": 2.0,
      "absorbed_dose_Gy": 0.001
    }
  ]
}
```

### Custom Radiation Weighting Factor
```json
POST /v1/dose/effective
{
  "irradiation": [
    {
      "tissue": "liver",
      "radiation": "proton",
      "absorbed_dose_Gy": 0.003,
      "custom_wR": 1.5
    }
  ]
}
```

### Equivalent Dose (No Tissue Weighting)
```json
POST /v1/dose/equivalent
{
  "irradiation": [
    {
      "tissue": "lung",
      "radiation": "photon",
      "absorbed_dose_Gy": 0.01
    },
    {
      "tissue": "lung",
      "radiation": "proton", 
      "absorbed_dose_Gy": 0.005
    }
  ]
}
```

## 🧪 Testing

### Method 1: Interactive Testing (Recommended)
1. Start the server: `uvicorn src.app:app --reload`
2. Visit: `http://localhost:8000/docs`
3. Use the "Try it out" buttons to test each endpoint

### Method 2: Command Line Testing
```bash
# Start server in one terminal
uvicorn src.app:app --reload

# Test in another terminal
curl http://localhost:8000/health
curl http://localhost:8000/v1/factors/tissue
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{"irradiation": [{"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}]}'
```

### Method 3: Python Testing
```python
import requests

# Test basic functionality
response = requests.get("http://localhost:8000/health")
print(response.json())  # Should print: {"status": "ok"}

# Test dose calculation
payload = {
    "irradiation": [
        {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}
    ]
}
response = requests.post("http://localhost:8000/v1/dose/effective", json=payload)
print(response.json())
```

### Method 4: Unit Tests
```bash
# Run the test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_dose_math.py -v
```

## 🔧 Development

### Project Structure
```
radiation-dose-api/
├── src/
│   ├── __init__.py
│   ├── app.py                    # FastAPI application
│   ├── schemas.py                # Pydantic request/response models
│   ├── models.py                 # Data loading and validation
│   ├── data/
│   │   └── icrp103_factors.json  # ICRP 103 factor data
│   └── services/
│       ├── __init__.py
│       ├── dose_service.py       # Core dose calculations
│       └── factors.py            # Factor lookup functions
├── tests/
│   ├── test_dose_math.py         # Unit tests for dose calculations
│   └── test_endpoints.py         # Integration tests for API endpoints
├── pyproject.toml                # Project configuration
├── LICENSE                       # MIT License
└── README.md                     # This file
```

### Code Quality Tools
```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src

# Run all quality checks
black src tests && ruff check src tests && mypy src
```

### Adding New Radiation Types
1. Add the new type to `RadiationKind` in `src/schemas.py`
2. Add the w_R value to `src/data/icrp103_factors.json`
3. Update tests in `tests/`

### Adding New Tissues
1. Add tissue to `src/data/icrp103_factors.json`
2. Update validation in `src/models.py`
3. Ensure tissue factors still sum to 1.0

## 🐳 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Configuration
```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn src.app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Environment variables
export WORKERS=4
export HOST=0.0.0.0
export PORT=8000
```

### CORS Configuration
For production, update CORS settings in `src/app.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 📖 Physics Background

This API implements the ICRP 103 methodology for radiation protection dosimetry:

### Key Concepts

- **Absorbed Dose (D)**: Energy deposited per unit mass [Gray, Gy]
- **Equivalent Dose (H_T)**: D × w_R, accounting for radiation biological effectiveness [Sievert, Sv]
- **Effective Dose (E)**: Σ w_T × H_T, whole-body risk indicator [Sievert, Sv]

### Calculation Formula

```
H_T = Σ_R (w_R × D_T,R)    # Equivalent dose per tissue
E = Σ_T (w_T × H_T)        # Total effective dose
```

Where:
- D_T,R = Absorbed dose to tissue T from radiation R
- w_R = Radiation weighting factor  
- w_T = Tissue weighting factor
- H_T = Equivalent dose to tissue T
- E = Effective dose (whole body)

### Important Notes

- **Protection Quantity**: Effective dose is for radiation protection regulation, not individual risk assessment
- **Reference Person**: Based on ICRP reference anatomical models
- **Conservative**: Designed to be conservative for protection purposes
- **Not Diagnostic**: Not intended for medical diagnosis or patient-specific risk calculation

## 🔍 API Reference

### Request Schema

```json
{
  "irradiation": [
    {
      "tissue": "string",                    // Required: tissue name or alias
      "radiation": "string",                 // Required: radiation type
      "absorbed_dose_Gy": 0.0,              // Required: absorbed dose in Gray (> 0)
      "neutron_energy_MeV": 0.0,            // Optional: required for neutrons
      "custom_wR": 0.0                      // Optional: override w_R value
    }
  ]
}
```

### Response Schemas

**Effective Dose Response:**
```json
{
  "by_tissue": [
    {
      "tissue": "string",
      "w_T": 0.0,
      "H_T_Sv": 0.0,
      "contribution_to_E_Sv": 0.0
    }
  ],
  "effective_dose_Sv": 0.0
}
```

**Equivalent Dose Response:**
```json
{
  "by_tissue": [
    {
      "tissue": "string",
      "H_T_Sv": 0.0
    }
  ]
}
```

### Error Responses

The API returns structured error responses:
```json
{
  "detail": "Error description"
}
```

Common error codes:
- `400 Bad Request`: Invalid input parameters
- `422 Unprocessable Entity`: Request validation failed
- `500 Internal Server Error`: Server error

## 🧪 Comprehensive Testing Guide

### Test Categories

1. **Smoke Tests**: Basic functionality verification
2. **Unit Tests**: Individual component testing
3. **Integration Tests**: End-to-end API testing
4. **Load Tests**: Performance and stability testing
5. **Error Handling Tests**: Validation and edge cases

### Smoke Tests (Start Here)

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Factor endpoints
curl http://localhost:8000/v1/factors/tissue
curl http://localhost:8000/v1/factors/radiation

# 3. Simple dose calculation
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{"irradiation": [{"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}]}'
```

### Comprehensive Test Suite

#### Basic Functionality Tests
```bash
# Test 1: Single tissue, single radiation
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01}
    ]
  }'
# Expected: effective_dose_Sv ≈ 0.0012

# Test 2: Multiple tissues
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "colon", "radiation": "photon", "absorbed_dose_Gy": 0.002},
      {"tissue": "gonads", "radiation": "photon", "absorbed_dose_Gy": 0.003}
    ]
  }'

# Test 3: Multiple radiations to same tissue
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01},
      {"tissue": "lung", "radiation": "proton", "absorbed_dose_Gy": 0.005}
    ]
  }'
```

#### Neutron Testing
```bash
# Test 4: Low energy neutron (< 1 MeV)
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "red_bone_marrow", "radiation": "neutron", "neutron_energy_MeV": 0.5, "absorbed_dose_Gy": 0.001}
    ]
  }'

# Test 5: Medium energy neutron (1-50 MeV)
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "neutron", "neutron_energy_MeV": 10.0, "absorbed_dose_Gy": 0.002}
    ]
  }'

# Test 6: High energy neutron (> 50 MeV)
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "colon", "radiation": "neutron", "neutron_energy_MeV": 100.0, "absorbed_dose_Gy": 0.001}
    ]
  }'

# Test 7: Neutron w_R lookup
curl -X POST http://localhost:8000/v1/dose/convert/neutron-wr \
  -H "Content-Type: application/json" \
  -d '{"energy_MeV": 2.0}'
```

#### Advanced Features Testing
```bash
# Test 8: Custom w_R override
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "liver", "radiation": "proton", "absorbed_dose_Gy": 0.003, "custom_wR": 1.5}
    ]
  }'

# Test 9: Tissue aliases
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "rbm", "radiation": "alpha", "absorbed_dose_Gy": 0.0001},
      {"tissue": "esophagus", "radiation": "photon", "absorbed_dose_Gy": 0.005}
    ]
  }'

# Test 10: Remainder tissues
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "heart", "radiation": "photon", "absorbed_dose_Gy": 0.004},
      {"tissue": "kidneys", "radiation": "electron", "absorbed_dose_Gy": 0.002}
    ]
  }'

# Test 11: Equivalent dose calculation
curl -X POST http://localhost:8000/v1/dose/equivalent \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01},
      {"tissue": "lung", "radiation": "proton", "absorbed_dose_Gy": 0.005}
    ]
  }'
```

#### Error Handling Tests
```bash
# Test 12: Invalid tissue
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "invalid_tissue", "radiation": "photon", "absorbed_dose_Gy": 0.01}
    ]
  }'
# Expected: HTTP 400

# Test 13: Missing neutron energy
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "neutron", "absorbed_dose_Gy": 0.01}
    ]
  }'
# Expected: HTTP 400

# Test 14: Invalid radiation type
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "invalid_radiation", "absorbed_dose_Gy": 0.01}
    ]
  }'
# Expected: HTTP 422

# Test 15: Negative dose
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": -0.01}
    ]
  }'
# Expected: HTTP 422

# Test 16: Zero dose
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.0}
    ]
  }'
# Expected: HTTP 422

# Test 17: Negative neutron energy
curl -X POST http://localhost:8000/v1/dose/convert/neutron-wr \
  -H "Content-Type: application/json" \
  -d '{"energy_MeV": -1.0}'
# Expected: HTTP 400

# Test 18: Negative custom w_R
curl -X POST http://localhost:8000/v1/dose/effective \
  -H "Content-Type: application/json" \
  -d '{
    "irradiation": [
      {"tissue": "lung", "radiation": "photon", "absorbed_dose_Gy": 0.01, "custom_wR": -1.0}
    ]
  }'
# Expected: HTTP 422
```

### Load Testing
```bash
# Install apache bench (if available)
# Simple load test
ab -n 100 -c 10 http://localhost:8000/health

# Or use Python for POST requests
python3 -c "
import asyncio
import httpx
import time

async def test_load():
    async with httpx.AsyncClient() as client:
        tasks = []
        payload = {'irradiation': [{'tissue': 'lung', 'radiation': 'photon', 'absorbed_dose_Gy': 0.01}]}
        
        start = time.time()
        for i in range(50):
            task = client.post('http://localhost:8000/v1/dose/effective', json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f'Completed {len(responses)} requests in {duration:.2f}s')
        print(f'Success rate: {success_count}/{len(responses)}')
        print(f'Average: {duration/len(responses)*1000:.1f}ms per request')

asyncio.run(test_load())
"
```

## 🎯 Expected Test Results

### Numerical Validation

**Simple Photon Case** (0.01 Gy to lung):
- H_lung = 0.01 Gy × 1.0 = 0.01 Sv
- E = 0.01 Sv × 0.12 = 0.0012 Sv

**Mixed Radiation Case** (colon + gonads):
- H_colon = (0.002 × 1.0) + (0.001 × 2.0) = 0.004 Sv
- H_gonads = 0.0005 × 20.0 = 0.01 Sv  
- E = (0.004 × 0.12) + (0.01 × 0.08) = 0.000048 + 0.0008 = 0.001328 Sv

**Neutron w_R Values** (for verification):
- 0.1 MeV: w_R ≈ 13.6
- 1.0 MeV: w_R ≈ 22.0
- 2.0 MeV: w_R ≈ 11.2
- 10.0 MeV: w_R ≈ 5.4
- 100.0 MeV: w_R ≈ 3.7

## 📞 Support and Contributing

### Getting Help
- Check the interactive docs: `http://localhost:8000/docs`
- Review test cases in `tests/` directory
- Examine example payloads in this README

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Run code quality checks: `black src tests && ruff check src tests`
6. Submit a pull request

### Reporting Issues
Please include:
- Python version
- Operating system
- Exact error message
- Steps to reproduce
- Expected vs actual behavior

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [ICRP Publication 103](https://www.icrp.org/publication.asp?id=ICRP%20Publication%20103) - The 2007 Recommendations of the International Commission on Radiological Protection
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework for building APIs
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation using Python type annotations

---

**Note**: This implementation is for educational and research purposes. For clinical or regulatory applications, please validate against official ICRP guidelines and consult with qualified health physics professionals.
