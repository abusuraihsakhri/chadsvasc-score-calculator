# CHA₂DS₂-VASc & HAS-BLED Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/chadsvasc-score-calculator/)

A browser and command-line calculator for atrial-fibrillation stroke-risk and bleeding-risk assessment. It calculates CHA₂DS₂-VASc, the 2024 ESC CHA₂DS₂-VA score, and HAS-BLED, with concise guideline-oriented interpretation.

## Features

- CHA₂DS₂-VASc scoring from 0–9, including sex-specific interpretation consistent with the 2023 ACC/AHA/ACCP/HRS atrial fibrillation guideline.
- CHA₂DS₂-VA scoring from 0–8 for the 2024 ESC atrial fibrillation approach.
- HAS-BLED scoring from 0–9. A score ≥3 is presented as a flag for modifiable bleeding risks and closer review, not as a reason by itself to withhold indicated anticoagulation.
- Historical CHA₂DS₂-VASc stroke-rate estimates are displayed with an explicit population-estimate caveat.
- Responsive browser interface with light/dark themes and an explicit **Calculate scores** action.
- Dependency-free Python CLI for single-patient and CSV batch workflows.
- Input validation and spreadsheet formula-injection protection for echoed CSV fields.

## Browser use

Open the live application above, enter age, select the applicable stroke and bleeding risk factors, and choose **Calculate scores**. Stroke history and age >65 are carried into HAS-BLED automatically.

The browser application is static HTML/CSS/JavaScript. Patient inputs are processed locally in the browser and are not transmitted or persisted. Only the light/dark theme preference may be stored in browser local storage.

## Command line

Requires Python 3.10 or newer. No third-party Python packages are required.

```bash
python cli.py assess --age 72 --chf --hypertension --diabetes --female
python cli.py chadsvasc --age 68 --stroke-tia --vascular-disease
python cli.py hasbled --age 70 --hypertension-uncontrolled --bleeding-history
python cli.py batch -i sample.csv -o results.csv
```

For standalone HAS-BLED calculation, `--elderly` can be used instead of `--age` when age >65 is already known.

## Testing

```bash
python -m compileall -q chadsvasc.py cli.py tests
python -m unittest discover -s tests -v
python cli.py batch -i sample.csv -o out_smoke.csv
node --check app.js
```

GitHub Actions runs the Python test matrix on 3.10–3.13 and checks the browser JavaScript syntax. The Pages workflow deploys the static site from `master`.

## Clinical scope and references

This repository is clinical decision-support software, not a substitute for patient-specific assessment. Anticoagulation decisions require confirmation of indication, contraindications, drug choice/dose, renal function, interacting therapies, bleeding-risk mitigation, and current local guidance.

Key references:

- 2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis and Management of Atrial Fibrillation. *Circulation*. DOI: 10.1161/CIR.0000000000001193.
- 2024 ESC Guidelines for the management of atrial fibrillation. *European Heart Journal*. DOI: 10.1093/eurheartj/ehae176.
- Lip GYH, Nieuwlaat R, Pisters R, Lane DA, Crijns HJGM. *Chest*. 2010;137(2):263–272. DOI: 10.1378/chest.09-1584.
- Pisters R, Lane DA, Nieuwlaat R, de Vos CB, Crijns HJGM, Lip GYH. *Chest*. 2010;138(5):1093–1100. DOI: 10.1378/chest.10-0134.

Historical annual stroke percentages in the calculator are cohort estimates and should not be treated as current patient-specific absolute risk.

## Technology and browser compatibility

The web application uses standards-based HTML, CSS, and vanilla JavaScript with no external runtime dependencies. Current versions of Chrome, Edge, Firefox, and Safari are recommended. The Python CLI uses only the standard library.

## License

MIT. See [LICENSE](LICENSE).
