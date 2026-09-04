# CHA2DS2-VASc & HAS-BLED Atrial Fibrillation Anticoagulation Calculator

> **Domain:** Cardiology, Stroke Prevention & Hemostasis  
> **Clinical Guidelines:** 2023 ACC/AHA/ACCP/HRS Atrial Fibrillation Guideline, 2024 ESC Guidelines for the Management of Atrial Fibrillation, Lip et al. (Chest 2010), Pisters et al. (Chest 2010)

---

## 📖 Clinical Overview

The **CHA2DS2-VASc & HAS-BLED Calculator** provides standardized clinical risk stratification for thromboembolic stroke and major bleeding risk in patients diagnosed with non-valvular atrial fibrillation (AF). 

By synthesizing thromboembolic predictors against modifiable and non-modifiable bleeding diathesis factors, the system generates concordant clinical guidance regarding oral anticoagulation (DOACs / VKAs) initiation versus active bleeding risk mitigation.

### Scoring Systems

#### 1. CHA2DS2-VASc Score (Thromboembolic Stroke Risk)
| Factor | Criteria | Points |
|:---|:---|:---|
| **C** | Congestive Heart Failure / LVEF $\le 40\%$ | +1 |
| **H** | Hypertension (or on antihypertensive therapy) | +1 |
| **A2** | Age $\ge 75$ years | +2 |
| **D** | Diabetes Mellitus | +1 |
| **S2** | Prior Stroke, TIA, or Thromboembolism | +2 |
| **V** | Vascular Disease (Prior MI, PAD, or Complex Aortic Plaque) | +1 |
| **A** | Age 65 to 74 years | +1 |
| **Sc** | Sex Category (Female) | +1 |

*Max Score: 9 points.*

| Score | Adjusted Annual Stroke Risk | Anticoagulation Recommendation (AHA/ACC & ESC) |
|:---|:---|:---|
| **0 (Men) / 1 (Women)** | 0.0% – 0.2% | **Low Risk**: No oral anticoagulation recommended. |
| **1 (Men) / 2 (Women)** | 0.6% – 1.3% | **Intermediate Risk**: Oral anticoagulation may be considered based on clinical judgment. |
| **$\ge 2$ (Men) / $\ge 3$ (Women)** | 2.2% – 15.2% | **High Risk**: Oral anticoagulation strongly recommended (DOAC preferred over Warfarin). |

#### 2. HAS-BLED Score (1-Year Major Bleeding Risk)
- **H**: Hypertension (uncontrolled, SBP > 160 mmHg) (+1)
- **A**: Abnormal renal or liver function (+1 or +2)
- **S**: Stroke history (+1)
- **B**: Bleeding history or predisposition (+1)
- **L**: Labile INRs (TTR < 60%) (+1)
- **E**: Elderly (Age > 65) (+1)
- **D**: Drugs (antiplatelets/NSAIDs) or Alcohol excess (+1 or +2)

*Score $\ge 3$ represents high bleeding risk, warranting caution and regular clinical review rather than withholding anticoagulation.*

---

## 💻 CLI Quickstart & Usage

### 1. Combined Clinical Assessment
```bash
python cli.py assess --age 72 --chf --hypertension --diabetes --female
```

### 2. Isolated CHA2DS2-VASc Calculation
```bash
python cli.py chadsvasc --age 68 --stroke-tia --vascular-disease
```

### 3. Isolated HAS-BLED Calculation
```bash
python cli.py hasbled --hypertension-uncontrolled --elderly --bleeding-history
```

### 4. Batch Process Patient CSV Dataset
```bash
python cli.py batch -i sample.csv -o out_results.csv
```

---

## 🧪 Verification & Testing

Execute comprehensive unit tests via pytest:
```bash
python -m pytest -p no:zarr
```
