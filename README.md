# CHA₂DS₂-VASc Score Calculator

A command-line tool for calculating **CHA₂DS₂-VASc** stroke risk and **HAS-BLED** bleeding risk scores in patients with non-valvular atrial fibrillation.

## What This Actually Is

This is a straightforward Python implementation of two well-validated clinical scoring systems:

- **CHA₂DS₂-VASc** (Lip et al., 2010) — estimates annual stroke risk in atrial fibrillation patients and guides anticoagulation decisions.
- **HAS-BLED** (Pisters et al., 2010) — estimates 1-year major bleeding risk to balance against stroke risk when considering anticoagulation.

**This is NOT a medical device.** It is an educational/reference calculator. Clinical decisions should always involve a qualified physician.

## Scoring Systems

### CHA₂DS₂-VASc (0–9 points)

| Factor | Points |
|--------|--------|
| **C** — Congestive heart failure (or LVEF ≤ 40%) | 1 |
| **H** — Hypertension | 1 |
| **A₂** — Age ≥ 75 | 2 |
| **D** — Diabetes mellitus | 1 |
| **S₂** — Prior stroke / TIA / thromboembolism | 2 |
| **V** — Vascular disease (prior MI, PAD, aortic plaque) | 1 |
| **A** — Age 65–74 | 1 |
| **Sc** — Sex category (female) | 1 |

### Annual Stroke Risk by Score

| Score | Risk (%) | Category | Anticoagulation |
|-------|----------|----------|-----------------|
| 0 | 0.0 | Low | Not recommended |
| 1 | 1.3 | Low-Moderate | Consider |
| 2 | 2.2 | Moderate-High | Recommended |
| 3 | 3.2 | Moderate-High | Recommended |
| 4 | 4.0 | Moderate-High | Recommended |
| 5 | 6.7 | Moderate-High | Recommended |
| 6 | 9.8 | Moderate-High | Recommended |
| 7 | 9.6 | Moderate-High | Recommended |
| 8 | 12.5 | Moderate-High | Recommended |
| 9 | 15.2 | Moderate-High | Recommended |

### HAS-BLED (0–9 points)

| Factor | Points |
|--------|--------|
| **H** — Hypertension uncontrolled (SBP > 160) | 1 |
| **A** — Abnormal renal function | 1 |
| **A** — Abnormal liver function | 1 |
| **S** — Stroke history | 1 |
| **B** — Bleeding history / predisposition | 1 |
| **L** — Labile INRs (TTR < 60%) | 1 |
| **E** — Elderly (age > 65) | 1 |
| **D** — Drugs (antiplatelets, NSAIDs) | 1 |
| **D** — Alcohol excess (≥ 8 drinks/week) | 1 |

Score ≥ 3 = high bleeding risk.

## Requirements

Python 3.8+ (stdlib only, no external packages).

## Usage

### Single Patient — CHA₂DS₂-VASc Only

```bash
python cli.py chadsvasc --age 72 --chf --hypertension --diabetes --female
```

### Single Patient — HAS-BLED Only

```bash
python cli.py hasbled --age 72 --hypertension-uncontrolled --elderly --bleeding-history
```

### Combined Assessment

```bash
python cli.py assess --age 72 --chf --hypertension --diabetes --female \
    --hypertension-uncontrolled --bleeding-history
```

### JSON Output

Add `--json` to any subcommand for machine-readable output:

```bash
python cli.py chadsvasc --age 68 --stroke-tia --json
```

### Batch CSV Processing

```bash
python cli.py batch -i patients.csv -o results.csv
```

The input CSV should have columns matching the factor names: `chf`, `hypertension`, `age`, `diabetes`, `stroke_tia`, `vascular_disease`, `female`, and optionally HAS-BLED columns.

### Python API

```python
from chadsvasc import calculate_chadsvasc, calculate_hasbled, assess_patient

# CHA2DS2-VASc only
result = calculate_chadsvasc(age=72, chf=True, hypertension=True, diabetes=True)
print(result["score"])          # 4
print(result["risk_percent"])   # 4.0
print(result["risk_category"])  # Moderate-High

# Combined assessment
full = assess_patient(age=72, chf=True, hypertension=True, stroke_tia=True)
print(full["recommendation"])
```

## Running Tests

```bash
python -m pytest test_chadsvasc.py -v
```

Or without pytest:

```bash
python -m unittest test_chadsvasc -v
```

## Project Structure

```
chadsvasc.py          Core scoring functions (calculate_chadsvasc, calculate_hasbled, assess_patient)
cli.py                Command-line interface (argparse)
test_chadsvasc.py     Unit tests
README.md             This file
```

## References

1. Lip GYH, Nieuwlaat R, Pisters R, Lane DA, Crijns HJGM. Refining clinical risk stratification for predicting stroke and thromboembolism in atrial fibrillation using a novel risk factor-based approach. *Chest*. 2010;137(2):263-272.
2. Pisters R, Lane DA, Nieuwlaat R, de Vos CB, Crijns HJGM, Lip GYH. A novel user-friendly score (HAS-BLED) to assess 1-year risk of major bleeding in patients with atrial fibrillation. *Chest*. 2010;138(5):1093-1100.

## License

MIT License. See [LICENSE](LICENSE).
