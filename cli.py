#!/usr/bin/env python3
"""Command-line interface for CHA2DS2-VASc / CHA2DS2-VA / HAS-BLED."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

from chadsvasc import assess_patient, calculate_chadsvasc, calculate_hasbled

_TRUE = {"1", "true", "yes", "y"}
_FALSE = {"0", "false", "no", "n", ""}
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _age_arg(value: str) -> float:
    try:
        age = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("age must be numeric") from exc
    if not math.isfinite(age) or age < 0 or age > 130:
        raise argparse.ArgumentTypeError("age must be between 0 and 130 years")
    return age


def _add_chadsvasc_args(parser: argparse.ArgumentParser, *, age_required: bool = True) -> None:
    parser.add_argument("--chf", action="store_true", help="Congestive heart failure / LV dysfunction")
    parser.add_argument("--hypertension", action="store_true", help="History of hypertension")
    parser.add_argument("--age", type=_age_arg, required=age_required, help="Patient age in years")
    parser.add_argument("--diabetes", action="store_true", help="Diabetes mellitus")
    parser.add_argument("--stroke-tia", action="store_true", help="Prior stroke, TIA, or systemic embolism")
    parser.add_argument("--vascular-disease", action="store_true", help="Prior MI, PAD, or aortic plaque")
    parser.add_argument("--female", action="store_true", help="Female sex category (+1 in CHA2DS2-VASc)")


def _add_hasbled_args(parser: argparse.ArgumentParser, *, include_stroke: bool = False) -> None:
    parser.add_argument("--hypertension-uncontrolled", action="store_true", help="Uncontrolled SBP > 160 mmHg")
    parser.add_argument("--abnormal-renal", action="store_true", help="Abnormal renal function")
    parser.add_argument("--abnormal-liver", action="store_true", help="Abnormal liver function")
    if include_stroke:
        parser.add_argument("--stroke", action="store_true", help="Prior stroke")
    parser.add_argument("--bleeding-history", action="store_true", help="Prior bleeding or bleeding predisposition")
    parser.add_argument("--labile-inr", action="store_true", help="Labile INR / poor time in therapeutic range")
    parser.add_argument("--drugs", action="store_true", help="Concomitant antiplatelet or NSAID use")
    parser.add_argument("--alcohol", action="store_true", help="Alcohol excess")


def _print_chadsvasc(result: dict[str, Any]) -> None:
    print(f"CHA2DS2-VASc Score: {result['score']} / 9")
    print(f"CHA2DS2-VA Score:   {result['cha2ds2_va']} / 8")
    print(f"Risk Category:      {result['risk_category']}")
    print(f"Historical Risk:    {result['risk_percent']}%/year (population estimate; not patient-specific)")
    print(f"Guidance:           {result['anticoagulation']}")
    if result["detail"]:
        print("Scoring breakdown:")
        for factor, points in result["detail"].items():
            print(f"  +{points}  {factor}")


def _print_hasbled(result: dict[str, Any]) -> None:
    print(f"HAS-BLED Score:     {result['score']} / 9")
    print(f"High-risk flag:     {'Yes' if result['high_risk'] else 'No'}")
    print(f"Guidance:           {result['guidance']}")
    if result["detail"]:
        print("Scoring breakdown:")
        for factor, points in result["detail"].items():
            print(f"  +{points}  {factor}")


def cmd_chadsvasc(args: argparse.Namespace) -> int:
    result = calculate_chadsvasc(
        chf=args.chf,
        hypertension=args.hypertension,
        age=args.age,
        diabetes=args.diabetes,
        stroke_tia=args.stroke_tia,
        vascular_disease=args.vascular_disease,
        female=args.female,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_chadsvasc(result)
    return 0


def cmd_hasbled(args: argparse.Namespace) -> int:
    elderly = args.elderly or (args.age is not None and args.age > 65)
    result = calculate_hasbled(
        hypertension_uncontrolled=args.hypertension_uncontrolled,
        abnormal_renal=args.abnormal_renal,
        abnormal_liver=args.abnormal_liver,
        stroke=args.stroke,
        bleeding_history=args.bleeding_history,
        labile_inr=args.labile_inr,
        elderly=elderly,
        drugs=args.drugs,
        alcohol=args.alcohol,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_hasbled(result)
    return 0


def cmd_assess(args: argparse.Namespace) -> int:
    result = assess_patient(
        chf=args.chf,
        hypertension=args.hypertension,
        age=args.age,
        diabetes=args.diabetes,
        stroke_tia=args.stroke_tia,
        vascular_disease=args.vascular_disease,
        female=args.female,
        hypertension_uncontrolled=args.hypertension_uncontrolled,
        abnormal_renal=args.abnormal_renal,
        abnormal_liver=args.abnormal_liver,
        bleeding_history=args.bleeding_history,
        labile_inr=args.labile_inr,
        drugs=args.drugs,
        alcohol=args.alcohol,
    )
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    _print_chadsvasc(result["chadsvasc"])
    print()
    _print_hasbled(result["hasbled"])
    print()
    print(f"Assessment: {result['recommendation']}")
    print(f"Note:       {result['disclaimer']}")
    return 0


def _parse_bool_cell(value: Any, *, column: str, row_number: int) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    raise ValueError(
        f"row {row_number}: {column!r} must be one of 1/0, true/false, yes/no, y/n"
    )


def _sanitize_csv_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def cmd_batch(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        with input_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            if "age" not in fieldnames:
                raise ValueError("input CSV must contain an 'age' column")
            rows = list(reader)

        computed_fields = [
            "chadsvasc_score",
            "cha2ds2_va_score",
            "chadsvasc_risk_pct",
            "chadsvasc_category",
            "hasbled_score",
            "hasbled_high_risk",
            "recommendation",
        ]
        out_fields = fieldnames + [name for name in computed_fields if name not in fieldnames]
        out_rows: list[dict[str, Any]] = []

        for index, row in enumerate(rows, start=2):
            age_text = str(row.get("age", "")).strip()
            if not age_text:
                raise ValueError(f"row {index}: age is required")
            age = _age_arg(age_text)
            result = assess_patient(
                chf=_parse_bool_cell(row.get("chf"), column="chf", row_number=index),
                hypertension=_parse_bool_cell(row.get("hypertension"), column="hypertension", row_number=index),
                age=age,
                diabetes=_parse_bool_cell(row.get("diabetes"), column="diabetes", row_number=index),
                stroke_tia=_parse_bool_cell(row.get("stroke_tia"), column="stroke_tia", row_number=index),
                vascular_disease=_parse_bool_cell(row.get("vascular_disease"), column="vascular_disease", row_number=index),
                female=_parse_bool_cell(row.get("female"), column="female", row_number=index),
                hypertension_uncontrolled=_parse_bool_cell(row.get("hypertension_uncontrolled"), column="hypertension_uncontrolled", row_number=index),
                abnormal_renal=_parse_bool_cell(row.get("abnormal_renal"), column="abnormal_renal", row_number=index),
                abnormal_liver=_parse_bool_cell(row.get("abnormal_liver"), column="abnormal_liver", row_number=index),
                bleeding_history=_parse_bool_cell(row.get("bleeding_history"), column="bleeding_history", row_number=index),
                labile_inr=_parse_bool_cell(row.get("labile_inr"), column="labile_inr", row_number=index),
                drugs=_parse_bool_cell(row.get("drugs"), column="drugs", row_number=index),
                alcohol=_parse_bool_cell(row.get("alcohol"), column="alcohol", row_number=index),
            )
            merged = {key: _sanitize_csv_value(value) for key, value in row.items()}
            merged.update(
                {
                    "chadsvasc_score": result["chadsvasc"]["score"],
                    "cha2ds2_va_score": result["chadsvasc"]["cha2ds2_va"],
                    "chadsvasc_risk_pct": result["chadsvasc"]["risk_percent"],
                    "chadsvasc_category": result["chadsvasc"]["risk_category"],
                    "hasbled_score": result["hasbled"]["score"],
                    "hasbled_high_risk": result["hasbled"]["high_risk"],
                    "recommendation": result["recommendation"],
                }
            )
            out_rows.append(merged)

        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
    except (OSError, csv.Error, ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Processed {len(out_rows)} patient(s) -> {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chadsvasc",
        description="CHA2DS2-VASc, CHA2DS2-VA, and HAS-BLED calculator for atrial fibrillation.",
    )
    sub = parser.add_subparsers(dest="command")

    p_cs = sub.add_parser("chadsvasc", help="Calculate CHA2DS2-VASc and CHA2DS2-VA")
    _add_chadsvasc_args(p_cs)
    p_cs.add_argument("--json", action="store_true", help="Output JSON")

    p_hb = sub.add_parser("hasbled", help="Calculate HAS-BLED")
    p_hb.add_argument("--age", type=_age_arg, help="Patient age; age >65 adds one point")
    p_hb.add_argument("--elderly", action="store_true", help="Explicitly score age >65")
    _add_hasbled_args(p_hb, include_stroke=True)
    p_hb.add_argument("--json", action="store_true", help="Output JSON")

    p_as = sub.add_parser("assess", help="Combined stroke-risk and bleeding-risk assessment")
    _add_chadsvasc_args(p_as)
    _add_hasbled_args(p_as)
    p_as.add_argument("--json", action="store_true", help="Output JSON")

    p_batch = sub.add_parser("batch", help="Batch-process a CSV file")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "chadsvasc": cmd_chadsvasc,
        "hasbled": cmd_hasbled,
        "assess": cmd_assess,
        "batch": cmd_batch,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
