#!/usr/bin/env python3
"""
Unit tests for the CHA2DS2-VASc and HAS-BLED calculator.

Run:  python -m pytest test_chadsvasc.py -v
  or: python -m unittest test_chadsvasc -v
"""
import unittest
import csv
import json
import sys
import os

from chadsvasc import calculate_chadsvasc, calculate_hasbled, assess_patient, STROKE_RISK


class TestChadsvascScore(unittest.TestCase):
    """Tests for calculate_chadsvasc()."""

    # ------------------------------------------------------------------
    # Score of 0 — low risk, no factors
    # ------------------------------------------------------------------
    def test_score_zero_low_risk(self):
        """A young male with no risk factors should score 0."""
        res = calculate_chadsvasc(age=40)
        self.assertEqual(res["score"], 0)
        self.assertEqual(res["risk_percent"], 0.0)
        self.assertEqual(res["risk_category"], "Low")
        self.assertIn("No anticoagulation", res["anticoagulation"])
        self.assertEqual(res["detail"], {})

    # ------------------------------------------------------------------
    # All factors present — maximum score of 9
    # ------------------------------------------------------------------
    def test_all_factors_max_score(self):
        """An elderly female with every risk factor should score 9."""
        res = calculate_chadsvasc(
            chf=True,
            hypertension=True,
            age=80,           # >= 75 → 2 points
            diabetes=True,
            stroke_tia=True,  # 2 points
            vascular_disease=True,
            female=True,
        )
        self.assertEqual(res["score"], 9)
        self.assertEqual(res["risk_percent"], 15.2)
        self.assertEqual(res["risk_category"], "Moderate-High")
        # Verify all 7 factors are in detail
        self.assertEqual(len(res["detail"]), 7)
        self.assertEqual(res["detail"]["Age >= 75"], 2)
        self.assertEqual(res["detail"]["Stroke/TIA"], 2)

    # ------------------------------------------------------------------
    # Age-based scoring: < 65, 65-74, >= 75
    # ------------------------------------------------------------------
    def test_age_under_65_no_age_points(self):
        """Patient aged 50 should get 0 age points."""
        res = calculate_chadsvasc(age=50)
        self.assertEqual(res["score"], 0)
        age_keys = [k for k in res["detail"] if "Age" in k]
        self.assertEqual(age_keys, [])

    def test_age_65_to_74_one_point(self):
        """Patient aged 70 should get 1 age point."""
        res = calculate_chadsvasc(age=70)
        self.assertEqual(res["score"], 1)
        self.assertIn("Age 65-74", res["detail"])
        self.assertEqual(res["detail"]["Age 65-74"], 1)

    def test_age_exactly_65(self):
        """Boundary: age exactly 65 should get 1 point."""
        res = calculate_chadsvasc(age=65)
        self.assertEqual(res["score"], 1)
        self.assertIn("Age 65-74", res["detail"])

    def test_age_exactly_74(self):
        """Boundary: age 74 should still be in the 65-74 bracket."""
        res = calculate_chadsvasc(age=74)
        self.assertEqual(res["score"], 1)
        self.assertIn("Age 65-74", res["detail"])

    def test_age_exactly_75_two_points(self):
        """Boundary: age exactly 75 should get 2 points."""
        res = calculate_chadsvasc(age=75)
        self.assertEqual(res["score"], 2)
        self.assertIn("Age >= 75", res["detail"])
        self.assertEqual(res["detail"]["Age >= 75"], 2)

    def test_age_90_two_points(self):
        """Very elderly patient aged 90 should still get 2 age points."""
        res = calculate_chadsvasc(age=90)
        self.assertEqual(res["score"], 2)

    # ------------------------------------------------------------------
    # Female sex category
    # ------------------------------------------------------------------
    def test_female_adds_one_point(self):
        """Female sex should add 1 point."""
        res = calculate_chadsvasc(age=40, female=True)
        self.assertEqual(res["score"], 1)
        self.assertIn("Female sex", res["detail"])
        self.assertEqual(res["detail"]["Female sex"], 1)

    def test_male_no_sex_point(self):
        """Male (female=False) should not get a sex point."""
        res = calculate_chadsvasc(age=40, female=False)
        self.assertEqual(res["score"], 0)
        self.assertNotIn("Female sex", res["detail"])

    # ------------------------------------------------------------------
    # Individual factor scoring
    # ------------------------------------------------------------------
    def test_chf_one_point(self):
        res = calculate_chadsvasc(chf=True)
        self.assertEqual(res["score"], 1)
        self.assertEqual(res["detail"]["CHF"], 1)

    def test_hypertension_one_point(self):
        res = calculate_chadsvasc(hypertension=True)
        self.assertEqual(res["score"], 1)
        self.assertEqual(res["detail"]["Hypertension"], 1)

    def test_diabetes_one_point(self):
        res = calculate_chadsvasc(diabetes=True)
        self.assertEqual(res["score"], 1)
        self.assertEqual(res["detail"]["Diabetes"], 1)

    def test_stroke_tia_two_points(self):
        res = calculate_chadsvasc(stroke_tia=True)
        self.assertEqual(res["score"], 2)
        self.assertEqual(res["detail"]["Stroke/TIA"], 2)

    def test_vascular_disease_one_point(self):
        res = calculate_chadsvasc(vascular_disease=True)
        self.assertEqual(res["score"], 1)
        self.assertEqual(res["detail"]["Vascular disease"], 1)

    # ------------------------------------------------------------------
    # High-risk patient example (realistic clinical scenario)
    # ------------------------------------------------------------------
    def test_high_risk_patient_scenario(self):
        """
        78-year-old female with hypertension, diabetes, and prior stroke.
        Expected: A2(2) + H(1) + D(1) + S2(2) + Sc(1) = 7
        """
        res = calculate_chadsvasc(
            hypertension=True,
            age=78,
            diabetes=True,
            stroke_tia=True,
            female=True,
        )
        self.assertEqual(res["score"], 7)
        self.assertEqual(res["risk_percent"], 9.6)
        self.assertEqual(res["risk_category"], "Moderate-High")
        self.assertIn("recommended", res["anticoagulation"].lower())

    def test_moderate_risk_patient_scenario(self):
        """
        68-year-old male with hypertension only.
        Expected: H(1) + A(1) = 2
        """
        res = calculate_chadsvasc(hypertension=True, age=68)
        self.assertEqual(res["score"], 2)
        self.assertEqual(res["risk_percent"], 2.2)

    # ------------------------------------------------------------------
    # Risk lookup table completeness
    # ------------------------------------------------------------------
    def test_stroke_risk_table_covers_0_to_9(self):
        """The STROKE_RISK dict should have entries for scores 0 through 9."""
        for i in range(10):
            self.assertIn(i, STROKE_RISK)

    # ------------------------------------------------------------------
    # Score is clamped to 0-9
    # ------------------------------------------------------------------
    def test_score_never_exceeds_9(self):
        """Even with all factors, score should not exceed 9."""
        res = calculate_chadsvasc(
            chf=True, hypertension=True, age=80,
            diabetes=True, stroke_tia=True, vascular_disease=True, female=True,
        )
        self.assertLessEqual(res["score"], 9)
        self.assertGreaterEqual(res["score"], 0)

    # ------------------------------------------------------------------
    # String coercion for boolean fields
    # ------------------------------------------------------------------
    def test_string_true_values(self):
        """String 'true', 'yes', '1' should be treated as True."""
        for val in ("true", "True", "yes", "Yes", "1", "y"):
            res = calculate_chadsvasc(chf=val)
            self.assertEqual(res["score"], 1, f"Failed for chf={val!r}")

    def test_string_false_values(self):
        """String 'false', 'no', '0' should be treated as False."""
        for val in ("false", "False", "no", "0", ""):
            res = calculate_chadsvasc(chf=val)
            self.assertEqual(res["score"], 0, f"Failed for chf={val!r}")


class TestHasbledScore(unittest.TestCase):
    """Tests for calculate_hasbled()."""

    def test_score_zero(self):
        """No risk factors should give HAS-BLED = 0."""
        res = calculate_hasbled()
        self.assertEqual(res["score"], 0)
        self.assertFalse(res["high_risk"])

    def test_high_risk_threshold(self):
        """Score of 3 should be flagged as high risk."""
        res = calculate_hasbled(
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            elderly=True,
        )
        self.assertEqual(res["score"], 3)
        self.assertTrue(res["high_risk"])
        self.assertIn("High bleeding risk", res["guidance"])

    def test_score_just_below_threshold(self):
        """Score of 2 should NOT be high risk."""
        res = calculate_hasbled(hypertension_uncontrolled=True, elderly=True)
        self.assertEqual(res["score"], 2)
        self.assertFalse(res["high_risk"])

    def test_renal_and_liver_both_scored(self):
        """Abnormal renal and abnormal liver should each score 1 (max 2 for 'A')."""
        res = calculate_hasbled(abnormal_renal=True, abnormal_liver=True)
        self.assertEqual(res["score"], 2)
        self.assertIn("Abnormal renal", res["detail"])
        self.assertIn("Abnormal liver", res["detail"])

    def test_drugs_and_alcohol_both_scored(self):
        """Drugs and alcohol should each score 1 (max 2 for 'D')."""
        res = calculate_hasbled(drugs=True, alcohol=True)
        self.assertEqual(res["score"], 2)
        self.assertIn("Drugs", res["detail"])
        self.assertIn("Alcohol", res["detail"])

    def test_max_score(self):
        """All factors present should give HAS-BLED = 9."""
        res = calculate_hasbled(
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            abnormal_liver=True,
            stroke=True,
            bleeding_history=True,
            labile_inr=True,
            elderly=True,
            drugs=True,
            alcohol=True,
        )
        self.assertEqual(res["score"], 9)
        self.assertTrue(res["high_risk"])

    def test_elderly_flag(self):
        """Elderly flag should add 1 point."""
        res = calculate_hasbled(elderly=True)
        self.assertEqual(res["score"], 1)
        self.assertIn("Elderly (>65)", res["detail"])


class TestAssessPatient(unittest.TestCase):
    """Tests for the combined assess_patient() function."""

    def test_returns_both_scores(self):
        """assess_patient should return chadsvasc and hasbled sub-dicts."""
        res = assess_patient(age=50)
        self.assertIn("chadsvasc", res)
        self.assertIn("hasbled", res)
        self.assertIn("recommendation", res)

    def test_low_risk_no_anticoagulation(self):
        """Score 0 should recommend no anticoagulation."""
        res = assess_patient(age=40)
        self.assertEqual(res["chadsvasc"]["score"], 0)
        self.assertIn("No anticoagulation", res["recommendation"])

    def test_high_score_low_bleeding(self):
        """High CHA2DS2-VASc with low HAS-BLED should recommend anticoagulation."""
        res = assess_patient(
            age=75, hypertension=True, diabetes=True, stroke_tia=True,
        )
        self.assertGreaterEqual(res["chadsvasc"]["score"], 5)
        self.assertFalse(res["hasbled"]["high_risk"])
        self.assertIn("recommended", res["recommendation"].lower())

    def test_high_score_high_bleeding(self):
        """High CHA2DS2-VASc with high HAS-BLED should note the bleeding risk."""
        res = assess_patient(
            age=78,
            hypertension=True,
            diabetes=True,
            stroke_tia=True,
            female=True,
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            bleeding_history=True,
        )
        self.assertGreaterEqual(res["chadsvasc"]["score"], 6)
        self.assertTrue(res["hasbled"]["high_risk"])
        self.assertIn("HAS-BLED", res["recommendation"])

    def test_score_one_with_high_bleeding(self):
        """Score 1 with high bleeding risk should discuss tradeoffs."""
        res = assess_patient(
            age=70,  # 1 point for age 65-74; elderly (>65) auto-derived for HAS-BLED
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            bleeding_history=True,
        )
        self.assertEqual(res["chadsvasc"]["score"], 1)
        self.assertTrue(res["hasbled"]["high_risk"])
        self.assertIn("risks/benefits", res["recommendation"].lower())

    def test_stroke_shared_between_scores(self):
        """stroke_tia=True should appear in both CHA2DS2-VASc and HAS-BLED."""
        res = assess_patient(stroke_tia=True)
        self.assertIn("Stroke/TIA", res["chadsvasc"]["detail"])
        self.assertIn("Stroke", res["hasbled"]["detail"])


class TestCLI(unittest.TestCase):
    """Basic CLI integration tests."""

    def test_chadsvasc_subcommand(self):
        """CLI chadsvasc subcommand should produce correct output."""
        from cli import main
        # Capture stdout
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["chadsvasc", "--age", "75", "--hypertension", "--diabetes"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("4", output)  # H(1) + A2(2) + D(1) = 4

    def test_chadsvasc_json_output(self):
        """CLI --json should produce valid JSON."""
        from cli import main
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["chadsvasc", "--age", "50", "--json"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        data = json.loads(output)
        self.assertEqual(data["score"], 0)

    def test_assess_subcommand(self):
        """CLI assess subcommand should run without error."""
        from cli import main
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["assess", "--age", "72", "--chf", "--female"])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("CHA2DS2-VASc", output)
        self.assertIn("HAS-BLED", output)

    def test_no_command_shows_help(self):
        """Running with no subcommand should return 1."""
        from cli import main
        import io
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            rc = main([])
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        self.assertEqual(rc, 1)


class TestBatchProcessing(unittest.TestCase):
    """Test CSV batch processing."""

    def test_batch_csv(self):
        """Batch processing a CSV should produce correct output."""
        import tempfile
        from cli import main

        # Write a temp input CSV
        input_csv = os.path.join(tempfile.gettempdir(), "test_batch_in.csv")
        output_csv = os.path.join(tempfile.gettempdir(), "test_batch_out.csv")

        with open(input_csv, "w", newline="") as f:
            f.write("age,chf,hypertension,diabetes,stroke_tia,vascular_disease,female\n")
            f.write("40,0,0,0,0,0,0\n")       # score 0
            f.write("70,0,1,0,0,0,0\n")       # H(1) + A(1) = 2
            f.write("80,1,1,1,1,1,1\n")       # max = 9

        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = main(["batch", "-i", input_csv, "-o", output_csv])
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        self.assertEqual(rc, 0)
        self.assertIn("3", output)

        # Verify output CSV
        with open(output_csv, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 3)
        self.assertEqual(int(rows[0]["chadsvasc_score"]), 0)
        self.assertEqual(int(rows[1]["chadsvasc_score"]), 2)
        self.assertEqual(int(rows[2]["chadsvasc_score"]), 9)

        # Cleanup
        os.unlink(input_csv)
        os.unlink(output_csv)


if __name__ == "__main__":
    unittest.main()
