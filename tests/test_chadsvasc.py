import csv
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from chadsvasc import STROKE_RISK, assess_patient, calculate_chadsvasc, calculate_hasbled
from cli import main


class ChadsvascTests(unittest.TestCase):
    def test_score_zero(self):
        result = calculate_chadsvasc(age=40)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["cha2ds2_va"], 0)
        self.assertEqual(result["risk_category"], "Low")

    def test_max_score(self):
        result = calculate_chadsvasc(
            chf=True,
            hypertension=True,
            age=80,
            diabetes=True,
            stroke_tia=True,
            vascular_disease=True,
            female=True,
        )
        self.assertEqual(result["score"], 9)
        self.assertEqual(result["cha2ds2_va"], 8)

    def test_age_boundaries(self):
        self.assertEqual(calculate_chadsvasc(age=64.9)["score"], 0)
        self.assertEqual(calculate_chadsvasc(age=65)["score"], 1)
        self.assertEqual(calculate_chadsvasc(age=74.9)["score"], 1)
        self.assertEqual(calculate_chadsvasc(age=75)["score"], 2)

    def test_female_sex_alone_is_low_risk_modifier(self):
        result = calculate_chadsvasc(age=40, female=True)
        self.assertEqual(result["score"], 1)
        self.assertEqual(result["cha2ds2_va"], 0)
        self.assertEqual(result["risk_category"], "Low")
        self.assertIn("sex alone", result["guideline_guidance"]["acc_aha_accp_hrs_2023"])

    def test_intermediate_sex_specific_thresholds(self):
        male = calculate_chadsvasc(age=65)
        female = calculate_chadsvasc(age=65, female=True)
        self.assertEqual(male["score"], 1)
        self.assertEqual(female["score"], 2)
        self.assertEqual(male["risk_category"], "Intermediate")
        self.assertEqual(female["risk_category"], "Intermediate")

    def test_esc_uses_cha2ds2_va(self):
        result = calculate_chadsvasc(age=65, female=True)
        self.assertIn("should be considered", result["guideline_guidance"]["esc_2024"])

    def test_invalid_age_rejected(self):
        for value in (-1, 131, float("nan"), float("inf"), "bad"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    calculate_chadsvasc(age=value)

    def test_bool_string_coercion_is_conservative(self):
        self.assertEqual(calculate_chadsvasc(age=40, chf="yes")["score"], 1)
        self.assertEqual(calculate_chadsvasc(age=40, chf="no")["score"], 0)
        self.assertEqual(calculate_chadsvasc(age=40, chf="unexpected")["score"], 0)

    def test_historical_risk_table_complete(self):
        self.assertEqual(set(STROKE_RISK), set(range(10)))
        self.assertEqual(STROKE_RISK[8], 6.7)


class HasbledTests(unittest.TestCase):
    def test_score_and_high_risk_flag(self):
        result = calculate_hasbled(
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            elderly=True,
        )
        self.assertEqual(result["score"], 3)
        self.assertTrue(result["high_risk"])

    def test_renal_liver_and_drugs_alcohol_score_separately(self):
        result = calculate_hasbled(
            abnormal_renal=True,
            abnormal_liver=True,
            drugs=True,
            alcohol=True,
        )
        self.assertEqual(result["score"], 4)

    def test_high_risk_guidance_does_not_withhold_anticoagulation(self):
        result = calculate_hasbled(
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            elderly=True,
        )
        self.assertIn("should not be used", result["guidance"])
        self.assertIn("withhold", result["guidance"])


class AssessmentTests(unittest.TestCase):
    def test_assessment_derives_hasbled_age(self):
        result = assess_patient(age=70)
        self.assertEqual(result["hasbled"]["score"], 1)
        self.assertIn("Age > 65", result["hasbled"]["detail"])

    def test_female_sex_alone_does_not_trigger_intermediate_recommendation(self):
        result = assess_patient(age=40, female=True)
        self.assertEqual(result["chadsvasc"]["risk_category"], "Low")
        self.assertIn("sex alone", result["recommendation"])

    def test_high_bleeding_risk_is_review_flag_not_veto(self):
        result = assess_patient(
            age=78,
            hypertension=True,
            diabetes=True,
            stroke_tia=True,
            hypertension_uncontrolled=True,
            abnormal_renal=True,
            bleeding_history=True,
        )
        self.assertTrue(result["hasbled"]["high_risk"])
        self.assertIn("not be used by itself", result["recommendation"])


class CliTests(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_chadsvasc_json(self):
        rc, out, _ = self.run_cli(["chadsvasc", "--age", "75", "--hypertension", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["score"], 3)

    def test_hasbled_elderly_flag(self):
        rc, out, _ = self.run_cli(["hasbled", "--elderly", "--hypertension-uncontrolled", "--bleeding-history"])
        self.assertEqual(rc, 0)
        self.assertIn("HAS-BLED Score:     3", out)

    def test_no_command_returns_one(self):
        rc, _, _ = self.run_cli([])
        self.assertEqual(rc, 1)

    def test_batch_processing_and_formula_sanitization(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "in.csv")
            output_path = os.path.join(tmp, "out.csv")
            headers = [
                "patient_id", "age", "chf", "hypertension", "diabetes", "stroke_tia",
                "vascular_disease", "female", "hypertension_uncontrolled", "abnormal_renal",
                "abnormal_liver", "bleeding_history", "labile_inr", "drugs", "alcohol",
            ]
            with open(input_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=headers)
                writer.writeheader()
                writer.writerow({
                    "patient_id": "=1+1", "age": "70", "chf": "0", "hypertension": "1",
                    "diabetes": "0", "stroke_tia": "0", "vascular_disease": "0", "female": "0",
                    "hypertension_uncontrolled": "0", "abnormal_renal": "0", "abnormal_liver": "0",
                    "bleeding_history": "0", "labile_inr": "0", "drugs": "0", "alcohol": "0",
                })
            rc, out, err = self.run_cli(["batch", "-i", input_path, "-o", output_path])
            self.assertEqual((rc, err), (0, ""))
            self.assertIn("Processed 1 patient", out)
            with open(output_path, newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["patient_id"], "'=1+1")
            self.assertEqual(row["chadsvasc_score"], "2")
            self.assertEqual(row["cha2ds2_va_score"], "2")

    def test_batch_rejects_unknown_boolean(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "in.csv")
            output_path = os.path.join(tmp, "out.csv")
            with open(input_path, "w", encoding="utf-8") as handle:
                handle.write("age,chf\n70,maybe\n")
            rc, _, err = self.run_cli(["batch", "-i", input_path, "-o", output_path])
            self.assertEqual(rc, 2)
            self.assertIn("must be one of", err)


if __name__ == "__main__":
    unittest.main()
