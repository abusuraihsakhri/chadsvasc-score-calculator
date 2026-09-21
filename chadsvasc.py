#!/usr/bin/env python3
"""CHA2DS2-VASc, CHA2DS2-VA, and HAS-BLED scoring helpers.

The scoring arithmetic is deterministic and dependency-free. The returned
clinical guidance is intentionally concise and is not a substitute for an
individual treatment decision.
"""

from __future__ import annotations

import math
from typing import Any

# Historical annual stroke-risk estimates commonly reproduced with the
# CHA2DS2-VASc score. Absolute risk varies substantially across populations;
# these values must not be treated as a current patient-specific prediction.
STROKE_RISK = {
    0: 0.0,
    1: 1.3,
    2: 2.2,
    3: 3.2,
    4: 4.0,
    5: 6.7,
    6: 9.8,
    7: 9.6,
    8: 6.7,
    9: 15.2,
}

TRUTHY_STRINGS = {"1", "true", "yes", "y"}


def _boolish(value: Any) -> bool:
    """Coerce common boolean representations without treating arbitrary text as true."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in TRUTHY_STRINGS
    return bool(value)


def _validate_age(age: Any) -> float:
    """Return a finite age in years, rejecting implausible or malformed values."""
    try:
        parsed = float(age)
    except (TypeError, ValueError) as exc:
        raise ValueError("age must be a number") from exc
    if not math.isfinite(parsed):
        raise ValueError("age must be finite")
    if parsed < 0 or parsed > 130:
        raise ValueError("age must be between 0 and 130 years")
    return parsed


def _stroke_guidance(score: int, female: bool, cha2ds2_va: int) -> tuple[str, str, str]:
    """Return category plus guideline-oriented summaries for clinical AF."""
    if female:
        if score <= 1:
            category = "Low"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: female sex alone is a risk modifier; "
                "this score alone does not indicate oral anticoagulation."
            )
        elif score == 2:
            category = "Intermediate"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: intermediate thromboembolic risk; "
                "oral anticoagulation is reasonable within shared decision-making."
            )
        else:
            category = "High"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: thromboembolic risk is in the range where "
                "oral anticoagulation is recommended for eligible patients."
            )
    else:
        if score == 0:
            category = "Low"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: low thromboembolic risk; "
                "oral anticoagulation is not indicated on this score alone."
            )
        elif score == 1:
            category = "Intermediate"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: intermediate thromboembolic risk; "
                "oral anticoagulation is reasonable within shared decision-making."
            )
        else:
            category = "High"
            acc = (
                "ACC/AHA/ACCP/HRS 2023: thromboembolic risk is in the range where "
                "oral anticoagulation is recommended for eligible patients."
            )

    if cha2ds2_va == 0:
        esc = "ESC 2024 (CHA2DS2-VA): low risk; oral anticoagulation is generally not recommended."
    elif cha2ds2_va == 1:
        esc = "ESC 2024 (CHA2DS2-VA): oral anticoagulation should be considered."
    else:
        esc = "ESC 2024 (CHA2DS2-VA): oral anticoagulation is recommended for eligible patients."

    return category, acc, esc


def calculate_chadsvasc(
    chf: Any = False,
    hypertension: Any = False,
    age: Any = 0,
    diabetes: Any = False,
    stroke_tia: Any = False,
    vascular_disease: Any = False,
    female: Any = False,
) -> dict[str, Any]:
    """Calculate CHA2DS2-VASc and the sex-independent CHA2DS2-VA score."""
    age_value = _validate_age(age)
    female_value = _boolish(female)
    detail: dict[str, int] = {}

    if _boolish(chf):
        detail["CHF/LV dysfunction"] = 1
    if _boolish(hypertension):
        detail["Hypertension"] = 1
    if age_value >= 75:
        detail["Age >= 75"] = 2
    elif age_value >= 65:
        detail["Age 65-74"] = 1
    if _boolish(diabetes):
        detail["Diabetes"] = 1
    if _boolish(stroke_tia):
        detail["Stroke/TIA/systemic embolism"] = 2
    if _boolish(vascular_disease):
        detail["Vascular disease"] = 1
    if female_value:
        detail["Female sex"] = 1

    score = sum(detail.values())
    cha2ds2_va = score - (1 if female_value else 0)
    category, acc_guidance, esc_guidance = _stroke_guidance(score, female_value, cha2ds2_va)

    return {
        "score": score,
        "cha2ds2_va": cha2ds2_va,
        "detail": detail,
        "risk_percent": STROKE_RISK[score],
        "risk_percent_context": (
            "Historical cohort estimate only; absolute annual risk varies across populations "
            "and should not be used as a patient-specific prediction."
        ),
        "risk_category": category,
        "anticoagulation": f"{acc_guidance} {esc_guidance}",
        "guideline_guidance": {
            "acc_aha_accp_hrs_2023": acc_guidance,
            "esc_2024": esc_guidance,
        },
    }


def calculate_hasbled(
    hypertension_uncontrolled: Any = False,
    abnormal_renal: Any = False,
    abnormal_liver: Any = False,
    stroke: Any = False,
    bleeding_history: Any = False,
    labile_inr: Any = False,
    elderly: Any = False,
    drugs: Any = False,
    alcohol: Any = False,
) -> dict[str, Any]:
    """Calculate HAS-BLED (0-9) and return interpretation guidance."""
    factors = (
        ("Uncontrolled hypertension", hypertension_uncontrolled),
        ("Abnormal renal function", abnormal_renal),
        ("Abnormal liver function", abnormal_liver),
        ("Stroke history", stroke),
        ("Bleeding history/predisposition", bleeding_history),
        ("Labile INR", labile_inr),
        ("Age > 65", elderly),
        ("Drugs increasing bleeding risk", drugs),
        ("Alcohol excess", alcohol),
    )
    detail = {name: 1 for name, value in factors if _boolish(value)}
    score = sum(detail.values())
    high_risk = score >= 3

    if high_risk:
        guidance = (
            "HAS-BLED >= 3 identifies increased bleeding risk and a need to address modifiable "
            "risk factors and arrange closer review. The score should not be used by itself to "
            "withhold or discontinue indicated anticoagulation."
        )
    else:
        guidance = (
            "Use HAS-BLED to identify modifiable bleeding risks and follow-up needs. "
            "Do not use the score in isolation to decide for or against anticoagulation."
        )

    return {
        "score": score,
        "detail": detail,
        "high_risk": high_risk,
        "guidance": guidance,
    }


def assess_patient(
    chf: Any = False,
    hypertension: Any = False,
    age: Any = 0,
    diabetes: Any = False,
    stroke_tia: Any = False,
    vascular_disease: Any = False,
    female: Any = False,
    hypertension_uncontrolled: Any = False,
    abnormal_renal: Any = False,
    abnormal_liver: Any = False,
    bleeding_history: Any = False,
    labile_inr: Any = False,
    drugs: Any = False,
    alcohol: Any = False,
) -> dict[str, Any]:
    """Return a combined stroke-risk and bleeding-risk assessment."""
    age_value = _validate_age(age)
    stroke = calculate_chadsvasc(
        chf=chf,
        hypertension=hypertension,
        age=age_value,
        diabetes=diabetes,
        stroke_tia=stroke_tia,
        vascular_disease=vascular_disease,
        female=female,
    )
    bleeding = calculate_hasbled(
        hypertension_uncontrolled=hypertension_uncontrolled,
        abnormal_renal=abnormal_renal,
        abnormal_liver=abnormal_liver,
        stroke=stroke_tia,
        bleeding_history=bleeding_history,
        labile_inr=labile_inr,
        elderly=age_value > 65,
        drugs=drugs,
        alcohol=alcohol,
    )

    recommendation = (
        f"{stroke['guideline_guidance']['acc_aha_accp_hrs_2023']} "
        f"{stroke['guideline_guidance']['esc_2024']} {bleeding['guidance']}"
    )
    return {
        "chadsvasc": stroke,
        "hasbled": bleeding,
        "recommendation": recommendation,
        "disclaimer": "Clinical decision support only; confirm patient-specific indications and contraindications.",
    }
