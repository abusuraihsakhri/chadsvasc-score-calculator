#!/usr/bin/env python3
"""
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
"""

# ---------------------------------------------------------------------------
# CHA2DS2-VASc scoring
# ---------------------------------------------------------------------------

# Annual stroke risk percentages by CHA2DS2-VASc score (Lip 2010 Table 4)
STROKE_RISK = {
    0: 0.0,
    1: 1.3,
    2: 2.2,
    3: 3.2,
    4: 4.0,
    5: 6.7,
    6: 9.8,
    7: 9.6,
    8: 12.5,
    9: 15.2,
}


def _boolish(val):
    """Coerce various truthy representations to bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "y")
    return bool(val)


def calculate_chadsvasc(
    chf=False,
    hypertension=False,
    age=0,
    diabetes=False,
    stroke_tia=False,
    vascular_disease=False,
    female=False,
):
    """
    Calculate the CHA2DS2-VASc score.

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
    """
    detail = {}

    if _boolish(chf):
        detail["CHF"] = 1
    if _boolish(hypertension):
        detail["Hypertension"] = 1

    age = float(age)
    if age >= 75:
        detail["Age >= 75"] = 2
    elif age >= 65:
        detail["Age 65-74"] = 1

    if _boolish(diabetes):
        detail["Diabetes"] = 1
    if _boolish(stroke_tia):
        detail["Stroke/TIA"] = 2
    if _boolish(vascular_disease):
        detail["Vascular disease"] = 1
    if _boolish(female):
        detail["Female sex"] = 1

    score = sum(detail.values())
    score = max(0, min(9, score))

    risk_pct = STROKE_RISK.get(score, 0.0)

    if score == 0:
        category = "Low"
        guidance = "No anticoagulation recommended."
    elif score == 1:
        category = "Low-Moderate"
        guidance = "Consider oral anticoagulation; patient preference and bleeding risk should guide decision."
    else:
        category = "Moderate-High"
        guidance = "Oral anticoagulation recommended (unless high bleeding risk)."

    return {
        "score": score,
        "detail": detail,
        "risk_percent": risk_pct,
        "risk_category": category,
        "anticoagulation": guidance,
    }


# ---------------------------------------------------------------------------
# HAS-BLED bleeding risk score
# ---------------------------------------------------------------------------

def calculate_hasbled(
    hypertension_uncontrolled=False,
    abnormal_renal=False,
    abnormal_liver=False,
    stroke=False,
    bleeding_history=False,
    labile_inr=False,
    elderly=False,
    drugs=False,
    alcohol=False,
):
    """
    Calculate the HAS-BLED score for 1-year major bleeding risk.

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
    """
    detail = {}

    if _boolish(hypertension_uncontrolled):
        detail["Uncontrolled hypertension"] = 1

    # Renal and liver are scored separately (max 2 for "A")
    abnl_points = 0
    if _boolish(abnormal_renal):
        detail["Abnormal renal"] = 1
        abnl_points += 1
    if _boolish(abnormal_liver):
        detail["Abnormal liver"] = 1
        abnl_points += 1

    if _boolish(stroke):
        detail["Stroke"] = 1
    if _boolish(bleeding_history):
        detail["Bleeding history"] = 1
    if _boolish(labile_inr):
        detail["Labile INR"] = 1
    if _boolish(elderly):
        detail["Elderly (>65)"] = 1

    # Drugs and alcohol are scored separately (max 2 for "D")
    if _boolish(drugs):
        detail["Drugs"] = 1
    if _boolish(alcohol):
        detail["Alcohol"] = 1

    score = sum(detail.values())
    score = max(0, min(9, score))
    high_risk = score >= 3

    if high_risk:
        guidance = (
            "High bleeding risk (HAS-BLED >= 3). "
            "Caution with anticoagulation; address modifiable risk factors."
        )
    else:
        guidance = "Low-moderate bleeding risk. Bleeding risk should not preclude anticoagulation if indicated."

    return {
        "score": score,
        "detail": detail,
        "high_risk": high_risk,
        "guidance": guidance,
    }


# ---------------------------------------------------------------------------
# Combined clinical assessment
# ---------------------------------------------------------------------------

def assess_patient(
    chf=False,
    hypertension=False,
    age=0,
    diabetes=False,
    stroke_tia=False,
    vascular_disease=False,
    female=False,
    # HAS-BLED specific
    hypertension_uncontrolled=False,
    abnormal_renal=False,
    abnormal_liver=False,
    bleeding_history=False,
    labile_inr=False,
    drugs=False,
    alcohol=False,
):
    """
    Combined CHA2DS2-VASc + HAS-BLED assessment.

    Returns a dict with 'chadsvasc' and 'hasbled' sub-dicts plus a
    'recommendation' string synthesising both scores.
    """
    cs = calculate_chadsvasc(
        chf=chf,
        hypertension=hypertension,
        age=age,
        diabetes=diabetes,
        stroke_tia=stroke_tia,
        vascular_disease=vascular_disease,
        female=female,
    )

    hb = calculate_hasbled(
        hypertension_uncontrolled=hypertension_uncontrolled,
        abnormal_renal=abnormal_renal,
        abnormal_liver=abnormal_liver,
        stroke=stroke_tia,  # stroke history is shared
        bleeding_history=bleeding_history,
        labile_inr=labile_inr,
        elderly=(age > 65),
        drugs=drugs,
        alcohol=alcohol,
    )

    # Synthesise recommendation
    if cs["score"] == 0:
        rec = (
            "CHA2DS2-VASc = 0 (low stroke risk). "
            "No anticoagulation recommended regardless of bleeding risk."
        )
    elif cs["score"] == 1:
        if hb["high_risk"]:
            rec = (
                "CHA2DS2-VASc = 1 (low-moderate stroke risk) but HAS-BLED >= 3 (high bleeding risk). "
                "Discuss risks/benefits with patient; anticoagulation may be withheld."
            )
        else:
            rec = (
                "CHA2DS2-VASc = 1 (low-moderate stroke risk). "
                "Consider anticoagulation; patient preference important."
            )
    else:
        if hb["high_risk"]:
            rec = (
                f"CHA2DS2-VASc = {cs['score']} (moderate-high stroke risk, "
                f"{cs['risk_percent']}% annual) with HAS-BLED = {hb['score']} (high bleeding risk). "
                "Anticoagulation still generally recommended; address modifiable bleeding risk factors."
            )
        else:
            rec = (
                f"CHA2DS2-VASc = {cs['score']} (moderate-high stroke risk, "
                f"{cs['risk_percent']}% annual). Anticoagulation recommended."
            )

    return {
        "chadsvasc": cs,
        "hasbled": hb,
        "recommendation": rec,
    }
