#!/usr/bin/env python3
"""
Command-line interface for the CHA2DS2-VASc / HAS-BLED calculator.

Usage examples:

    # Single patient assessment
    python cli.py assess --age 72 --chf --hypertension --diabetes --female

    # CHA2DS2-VASc only
    python cli.py chadsvasc --age 68 --stroke-tia --vascular-disease

    # HAS-BLED only
    python cli.py hasbled --hypertension-uncontrolled --elderly --bleeding-history

    # Batch CSV processing
    python cli.py batch -i patients.csv -o results.csv
"""
import argparse
import csv
import json
import sys

from chadsvasc import calculate_chadsvasc, calculate_hasbled, assess_patient


def _add_patient_args(parser):
    """Add the common patient factor flags to a subparser."""
    parser.add_argument("--chf", action="store_true", help="Congestive heart failure / LVEF <= 40%%")
    parser.add_argument("--hypertension", action="store_true", help="History of hypertension")
    parser.add_argument("--age", type=float, default=0, help="Patient age in years")
    parser.add_argument("--diabetes", action="store_true", help="Diabetes mellitus")
    parser.add_argument("--stroke-tia", action="store_true", help="Prior stroke / TIA / thromboembolism")
    parser.add_argument("--vascular-disease", action="store_true", help="Prior MI, PAD, or aortic plaque")
    parser.add_argument("--female", action="store_true", help="Female sex")


def _add_hasbled_args(parser):
    """Add HAS-BLED-specific flags to a subparser."""
    parser.add_argument("--hypertension-uncontrolled", action="store_true",
                        help="Uncontrolled SBP > 160 mmHg")
    parser.add_argument("--abnormal-renal", action="store_true",
                        help="Abnormal renal function")
    parser.add_argument("--abnormal-liver", action="store_true",
                        help="Abnormal liver function")
    parser.add_argument("--bleeding-history", action="store_true",
                        help="Prior bleeding or predisposition (anaemia)")
    parser.add_argument("--labile-inr", action="store_true",
                        help="Labile INRs (TTR < 60%%)")
    parser.add_argument("--drugs", action="store_true",
                        help="Concomitant antiplatelet / NSAID use")
    parser.add_argument("--alcohol", action="store_true",
                        help="Alcohol excess (>= 8 drinks/week)")


def _print_chadsvasc(res):
    """Pretty-print a CHA2DS2-VASc result dict."""
    print(f"CHA2DS2-VASc Score: {res['score']} / 9")
    print(f"Risk Category:      {res['risk_category']}")
    print(f"Annual Stroke Risk: {res['risk_percent']}%")
    print(f"Guidance:           {res['anticoagulation']}")
    if res["detail"]:
        print("Scoring breakdown:")
        for factor, pts in res["detail"].items():
            print(f"  +{pts}  {factor}")


def _print_hasbled(res):
    """Pretty-print a HAS-BLED result dict."""
    print(f"HAS-BLED Score:     {res['score']} / 9")
    print(f"High Bleeding Risk: {'Yes' if res['high_risk'] else 'No'}")
    print(f"Guidance:           {res['guidance']}")
    if res["detail"]:
        print("Scoring breakdown:")
        for factor, pts in res["detail"].items():
            print(f"  +{pts}  {factor}")


def cmd_chadsvasc(args):
    """Handle the 'chadsvasc' subcommand."""
    res = calculate_chadsvasc(
        chf=args.chf,
        hypertension=args.hypertension,
        age=args.age,
        diabetes=args.diabetes,
        stroke_tia=args.stroke_tia,
        vascular_disease=args.vascular_disease,
        female=args.female,
    )
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        _print_chadsvasc(res)
    return 0


def cmd_hasbled(args):
    """Handle the 'hasbled' subcommand."""
    res = calculate_hasbled(
        hypertension_uncontrolled=args.hypertension_uncontrolled,
        abnormal_renal=args.abnormal_renal,
        abnormal_liver=args.abnormal_liver,
        stroke=args.stroke_tia,
        bleeding_history=args.bleeding_history,
        labile_inr=args.labile_inr,
        elderly=(args.age > 65),
        drugs=args.drugs,
        alcohol=args.alcohol,
    )
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        _print_hasbled(res)
    return 0


def cmd_assess(args):
    """Handle the combined 'assess' subcommand."""
    res = assess_patient(
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
        print(json.dumps(res, indent=2))
    else:
        print("=" * 60)
        print("  CHA2DS2-VASc Assessment")
        print("=" * 60)
        _print_chadsvasc(res["chadsvasc"])
        print()
        print("-" * 60)
        print("  HAS-BLED Assessment")
        print("-" * 60)
        _print_hasbled(res["hasbled"])
        print()
        print("=" * 60)
        print(f"  Recommendation: {res['recommendation']}")
        print("=" * 60)
    return 0


def cmd_batch(args):
    """Handle the 'batch' subcommand — process a CSV of patients."""
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "chadsvasc_score", "chadsvasc_risk_pct", "chadsvasc_category",
        "hasbled_score", "hasbled_high_risk", "recommendation",
    ]
    out_rows = []
    for row in rows:
        def _get_bool(key):
            val = str(row.get(key, "")).strip().lower()
            return val in ("1", "true", "yes", "y")

        age = float(row.get("age", 0))
        res = assess_patient(
            chf=_get_bool("chf"),
            hypertension=_get_bool("hypertension"),
            age=age,
            diabetes=_get_bool("diabetes"),
            stroke_tia=_get_bool("stroke_tia"),
            vascular_disease=_get_bool("vascular_disease"),
            female=_get_bool("female"),
            hypertension_uncontrolled=_get_bool("hypertension_uncontrolled"),
            abnormal_renal=_get_bool("abnormal_renal"),
            abnormal_liver=_get_bool("abnormal_liver"),
            bleeding_history=_get_bool("bleeding_history"),
            labile_inr=_get_bool("labile_inr"),
            drugs=_get_bool("drugs"),
            alcohol=_get_bool("alcohol"),
        )
        merged = dict(row)
        merged["chadsvasc_score"] = res["chadsvasc"]["score"]
        merged["chadsvasc_risk_pct"] = res["chadsvasc"]["risk_percent"]
        merged["chadsvasc_category"] = res["chadsvasc"]["risk_category"]
        merged["hasbled_score"] = res["hasbled"]["score"]
        merged["hasbled_high_risk"] = res["hasbled"]["high_risk"]
        merged["recommendation"] = res["recommendation"]
        out_rows.append(merged)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} patient(s) -> {args.output}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="chadsvasc",
        description="CHA2DS2-VASc and HAS-BLED score calculator for atrial fibrillation stroke risk.",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of formatted text")
    sub = parser.add_subparsers(dest="command")

    # chadsvasc subcommand
    p_cs = sub.add_parser("chadsvasc", help="Calculate CHA2DS2-VASc score only")
    _add_patient_args(p_cs)
    p_cs.add_argument("--json", action="store_true", help="JSON output")

    # hasbled subcommand
    p_hb = sub.add_parser("hasbled", help="Calculate HAS-BLED score only")
    _add_patient_args(p_hb)
    _add_hasbled_args(p_hb)
    p_hb.add_argument("--json", action="store_true", help="JSON output")

    # assess subcommand (combined)
    p_as = sub.add_parser("assess", help="Combined CHA2DS2-VASc + HAS-BLED assessment")
    _add_patient_args(p_as)
    _add_hasbled_args(p_as)
    p_as.add_argument("--json", action="store_true", help="JSON output")

    # batch subcommand
    p_ba = sub.add_parser("batch", help="Batch-process a CSV file of patients")
    p_ba.add_argument("-i", "--input", required=True, help="Input CSV path")
    p_ba.add_argument("-o", "--output", default="results.csv", help="Output CSV path")
    p_ba.add_argument("--json", action="store_true", help="JSON output")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "chadsvasc":
        return cmd_chadsvasc(args)
    elif args.command == "hasbled":
        return cmd_hasbled(args)
    elif args.command == "assess":
        return cmd_assess(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
