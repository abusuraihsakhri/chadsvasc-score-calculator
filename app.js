(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const form = $("calculator-form");
  const ageInput = $("age");
  const ageError = $("age-error");
  const themeToggle = $("theme-toggle");
  const themeIcon = $("theme-icon");

  const strokeRiskLegacy = [0.0, 1.3, 2.2, 3.2, 4.0, 6.7, 9.8, 9.6, 6.7, 15.2];

  function checked(id) {
    return $(id).checked;
  }

  function validateAge() {
    const raw = ageInput.value.trim();
    const age = Number(raw);
    if (!raw) {
      ageError.textContent = "Age is required.";
      ageInput.setAttribute("aria-invalid", "true");
      return null;
    }
    if (!Number.isFinite(age) || age < 0 || age > 130) {
      ageError.textContent = "Enter an age from 0 to 130 years.";
      ageInput.setAttribute("aria-invalid", "true");
      return null;
    }
    ageError.textContent = "";
    ageInput.removeAttribute("aria-invalid");
    return age;
  }

  function calculate() {
    const age = validateAge();
    if (age === null) return null;

    const female = checked("female");
    const strokeDetails = [];
    let score = 0;

    const addStroke = (condition, label, points) => {
      if (condition) {
        score += points;
        strokeDetails.push([label, points]);
      }
    };

    addStroke(checked("chf"), "CHF / LV dysfunction", 1);
    addStroke(checked("hypertension"), "Hypertension", 1);
    if (age >= 75) addStroke(true, "Age ≥75", 2);
    else if (age >= 65) addStroke(true, "Age 65–74", 1);
    addStroke(checked("diabetes"), "Diabetes", 1);
    addStroke(checked("stroke"), "Stroke / TIA / embolism", 2);
    addStroke(checked("vascular"), "Vascular disease", 1);
    addStroke(female, "Female sex", 1);

    const vaScore = score - (female ? 1 : 0);
    let category;
    let acc;
    if (female) {
      if (score <= 1) {
        category = "Low";
        acc = "Female sex alone is a risk modifier; this score alone does not indicate oral anticoagulation.";
      } else if (score === 2) {
        category = "Intermediate";
        acc = "Intermediate thromboembolic risk; oral anticoagulation is reasonable within shared decision-making.";
      } else {
        category = "High";
        acc = "Risk is in the range where oral anticoagulation is recommended for eligible patients.";
      }
    } else if (score === 0) {
      category = "Low";
      acc = "Low thromboembolic risk; oral anticoagulation is not indicated on this score alone.";
    } else if (score === 1) {
      category = "Intermediate";
      acc = "Intermediate thromboembolic risk; oral anticoagulation is reasonable within shared decision-making.";
    } else {
      category = "High";
      acc = "Risk is in the range where oral anticoagulation is recommended for eligible patients.";
    }

    let esc;
    if (vaScore === 0) esc = "CHA₂DS₂-VA = 0: low risk; oral anticoagulation is generally not recommended.";
    else if (vaScore === 1) esc = "CHA₂DS₂-VA = 1: oral anticoagulation should be considered.";
    else esc = "CHA₂DS₂-VA ≥2: oral anticoagulation is recommended for eligible patients.";

    const bleedingDetails = [];
    let hbScore = 0;
    const addBleeding = (condition, label) => {
      if (condition) {
        hbScore += 1;
        bleedingDetails.push([label, 1]);
      }
    };

    addBleeding(checked("hb-hypertension"), "SBP >160 mmHg");
    addBleeding(checked("renal"), "Abnormal renal function");
    addBleeding(checked("liver"), "Abnormal liver function");
    addBleeding(checked("stroke"), "Stroke history");
    addBleeding(checked("bleeding"), "Bleeding history / predisposition");
    addBleeding(checked("labile"), "Labile INR");
    addBleeding(age > 65, "Age >65");
    addBleeding(checked("drugs"), "Antiplatelet / NSAID use");
    addBleeding(checked("alcohol"), "Alcohol excess");

    const hbGuidance = hbScore >= 3
      ? "HAS-BLED ≥3 flags increased bleeding risk: address modifiable factors and arrange closer review. Do not use the score alone to withhold or stop indicated anticoagulation."
      : "Use HAS-BLED to identify modifiable bleeding risks and follow-up needs; do not use it in isolation to decide for or against anticoagulation.";

    return {
      score,
      vaScore,
      category,
      acc,
      esc,
      hbScore,
      hbGuidance,
      strokeDetails,
      bleedingDetails,
      historicalRisk: strokeRiskLegacy[score],
    };
  }

  function render(result) {
    $("cs-score").textContent = String(result.score);
    $("va-score").textContent = String(result.vaScore);
    $("hb-score").textContent = String(result.hbScore);
    $("cs-category").textContent = `${result.category} category · historical estimate ${result.historicalRisk}%/yr*`;
    $("hb-category").textContent = result.hbScore >= 3 ? "High-risk review flag" : "Below high-risk threshold";
    $("acc-guidance").textContent = result.acc;
    $("esc-guidance").textContent = result.esc;
    $("hb-guidance").textContent = result.hbGuidance;

    const status = $("risk-status");
    status.textContent = result.category;
    status.className = `status-pill ${result.category.toLowerCase()}`;

    const breakdown = $("breakdown");
    breakdown.replaceChildren();
    const allItems = [
      ...result.strokeDetails.map(([label, points]) => [`CHA₂DS₂-VASc · ${label}`, `+${points}`]),
      ...result.bleedingDetails.map(([label, points]) => [`HAS-BLED · ${label}`, `+${points}`]),
    ];
    if (allItems.length === 0) {
      const empty = document.createElement("span");
      empty.textContent = "No scoring factors selected.";
      breakdown.appendChild(empty);
      return;
    }
    for (const [label, points] of allItems) {
      const row = document.createElement("span");
      const name = document.createElement("span");
      const value = document.createElement("strong");
      name.textContent = label;
      value.textContent = points;
      row.append(name, value);
      breakdown.appendChild(row);
    }
  }

  function resetResults() {
    $("cs-score").textContent = "—";
    $("va-score").textContent = "—";
    $("hb-score").textContent = "—";
    $("cs-category").textContent = "Enter age to calculate";
    $("hb-category").textContent = "Review flag at ≥3";
    $("acc-guidance").textContent = "Calculate to view guidance.";
    $("esc-guidance").textContent = "Uses CHA₂DS₂-VA for anticoagulation decisions.";
    $("hb-guidance").textContent = "HAS-BLED is intended to identify modifiable risk factors and follow-up needs.";
    $("risk-status").textContent = "Ready";
    $("risk-status").className = "status-pill neutral";
    $("breakdown").replaceChildren();
    ageError.textContent = "";
    ageInput.removeAttribute("aria-invalid");
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const result = calculate();
    if (!result) {
      ageInput.focus();
      return;
    }
    render(result);
  });

  form.addEventListener("reset", () => {
    window.requestAnimationFrame(resetResults);
  });

  let storedTheme = null;
  try {
    storedTheme = localStorage.getItem("theme");
  } catch (_) {
    // Persistent storage can be unavailable in hardened/private browsing modes.
  }
  const preferredDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initialTheme = storedTheme === "dark" || storedTheme === "light" ? storedTheme : (preferredDark ? "dark" : "light");

  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch (_) {
      // Theme switching still works when storage is unavailable.
    }
    const isDark = theme === "dark";
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
    themeIcon.textContent = isDark ? "☀" : "◐";
  }

  setTheme(initialTheme);
  themeToggle.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
})();
