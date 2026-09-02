# CHADSVASC Score Calculator

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics  
> **Reference Guidelines & Standards:** `AHA/ACC Practice Guidelines & ESC Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

CHA2DS2-VASc Score Calculator for atrial fibrillation stroke risk assessment.

Implements the validated CHA2DS2-VASc scoring system (Lip et al., 2010) and
the HAS-BLED bleeding risk score (Pisters et al., 2010) to support
anticoagulation decision-making in non-valvular atrial fibrillation.

References:
    - Lip GY, Nieuwlaat R, Pisters R, Lane DA, Crijns HJ. Refining clinical
      risk stratification for predicting stroke and thromboembolism in atrial
      fibrillation using a novel risk factor-based approach. Chest. 2010;137(2):263-272.
    - Pisters R, Lane DA, Nieuwlaat R, de Vos CB, Crijns HJ, Lip GY. A novel
      user-friendly score (HAS-BLED) to assess 1-year risk of major bleeding in
      patients with atrial fibrillation. Chest. 2010;138(5):1093-1100.

Stdlib only — no external dependencies.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_chadsvasc()`**: Calculate the CHA2DS2-VASc score.

Parameters
----------
chf : bool
    Congestive heart failure (or LVEF <= 40%).  +1
hypertension : bool
    History of hypertension.  +1
age : int or float
    Patient age in years.  +2 if >= 75, +1 if 65-74, 0 otherwise.
diabetes : bool
    Diabetes mellitus.  +1
stroke_tia : bool
    Prior stroke, TIA, or thromboembolism.  +2
vascular_disease : bool
    Prior MI, peripheral artery disease, or aortic plaque.  +1
female : bool
    Female sex.  +1

Returns
-------
dict with keys:
    score           – int, total CHA2DS2-VASc (0-9)
    detail          – dict mapping factor name to points awarded
    risk_percent    – float, estimated annual stroke risk %
    risk_category   – str, one of "Low", "Low-Moderate", "Moderate-High"
    anticoagulation – str, clinical guidance
- **`calculate_hasbled()`**: Calculate the HAS-BLED score for 1-year major bleeding risk.

Parameters
----------
hypertension_uncontrolled : bool
    Uncontrolled hypertension (SBP > 160 mmHg).  +1
abnormal_renal : bool
    Abnormal renal function (dialysis, transplant, Cr > 2.26 mg/dL).  +1
abnormal_liver : bool
    Abnormal liver function (cirrhosis, bilirubin > 2x ULN, AST/ALT/ALP > 3x ULN).  +1
stroke : bool
    Prior stroke.  +1
bleeding_history : bool
    Bleeding history or predisposition (anaemia).  +1
labile_inr : bool
    Labile INRs (TTR < 60%).  +1
elderly : bool
    Age > 65.  +1
drugs : bool
    Concomitant drugs (antiplatelets, NSAIDs).  +1
alcohol : bool
    Alcohol excess (>= 8 drinks/week).  +1

Returns
-------
dict with keys:
    score           – int, total HAS-BLED (0-9)
    detail          – dict mapping factor name to points awarded
    high_risk       – bool, True if score >= 3
    guidance        – str, clinical guidance
- **`assess_patient()`**: Combined CHA2DS2-VASc + HAS-BLED assessment.

Returns a dict with 'chadsvasc' and 'hasbled' sub-dicts plus a
'recommendation' string synthesising both scores.

---

## 📐 Mathematical Formulation & Logic

```text
  STROKE_RISK = {
  Calculate the CHA2DS2-VASc score.
  score = sum(detail.values())
  score = max(0, min(9, score))
  if score == 0:
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --age <value> --chf <value> --hypertension <value> --diabetes <value>
```

### Parameter Reference
- `--age`: Specifies input measurement or parameter value.
- `--chf`: Specifies input measurement or parameter value.
- `--hypertension`: Specifies input measurement or parameter value.
- `--diabetes`: Specifies input measurement or parameter value.
- `--female`: Specifies input measurement or parameter value.
- `--stroke-tia`: Specifies input measurement or parameter value.
- `--vascular-disease`: Specifies input measurement or parameter value.
- `--hypertension-uncontrolled`: Specifies input measurement or parameter value.
- `--elderly`: Specifies input measurement or parameter value.
- `--bleeding-history`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Parameter / observation metric | Required |
| `age` | Parameter / observation metric | Required |
| `chf` | Parameter / observation metric | Required |
| `hypertension` | Parameter / observation metric | Required |
| `diabetes` | Parameter / observation metric | Required |
| `stroke_tia` | Parameter / observation metric | Required |
| `vascular_disease` | Parameter / observation metric | Required |
| `female` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t chadsvasc-score-calculator .
docker run -p 8000:8000 chadsvasc-score-calculator
```
