# CLAUDE.md — Project: Turnus Risk Audit (2026)

## 🎯 Vision

A "Sovereign" compliance and burnout prediction engine for Norwegian health leaders. The tool transforms messy Gat/Excel exports into high-stakes financial and legal risk reports, specifically targeting **AML § 4-3** (Psychosocial Workload) and **§ 10-8** (Rest Periods) compliance.

## 🛠 Tech Stack

* **Backend:** Python 3.12+ (FastAPI)
* **Data Engine:** Polars (High-performance data manipulation)
* **Logic:** Versioned JSON-based Rule Engine (AML/HTA 2024-2026)
* **Infrastructure:** Sovereign Norwegian Cloud (Azure Norway East)
* **Frontend:** Streamlit (v1 MVP) -> Next.js (Production)

---

## 🤖 Agent Definitions & Skills

### 1. Agent: "The Gat-Slayer" (Data Ingestion)

**Goal:** Sanitize and map inconsistent Norwegian Excel/Gat exports.
**Skills:**

* `clean_gat_export`: Handles merged cells (forward-fill), handles Norwegian characters (ÆØÅ).
* `fuzzy_header_match`: Maps variable column names (e.g., "Pers.nr" vs "Ansattnr") to a standard schema.
* `vakt_code_mapper`: Translates shift codes (D1, N3) into `start_time` and `end_time`.
* `data_validation_report`: Flags rows with "human noise" (e.g., "Syk - ringt") for manual verification.

### 2. Agent: "The Auditor" (Legal Logic Engine)

**Goal:** Evaluate shift data against a hierarchy of Norwegian labor rules.
**Skills:**

* `sliding_window_11h`: Identifies Daily Rest violations within any 24h period.
* `weekly_rest_35h`: Scans 168h windows for a continuous 35h rest gap.
* `HTA_compliance_check`: Applies specific HTA rules (35.5h week, Sunday rotation limits).
* `compensatory_rest_tracker`: Tracks "rest debt" created by reduced rest periods (8h exceptions).

### 3. Agent: "The Economist" (Predictive Analysis)

**Goal:** Translate breaches into financial risk and health outcomes.
**Skills:**

* `calculate_fatigue_index`: Uses research-backed coefficients to score burnout risk.
* `vikar_leak_estimator`: Calculates potential savings in external agency costs.
* `psychosocial_risk_map`: Generates evidence for **AML § 4-3** compliance reporting.

---

## ⚖️ Legal Logic & Coefficients (2026 Standards)

### AML § 10-8 Baseline

* **Daily Rest:** 11 hours (Threshold).
* **Weekly Rest:** 35 hours (Rolling 168h window).
* **Sunday Rule:** Max 3 consecutive Sundays unless locally agreed.

### Fatigue Score Coefficients ()

| Trigger | Multiplier | Description |
| --- | --- | --- |
| **Short Rest (< 11h)** | 1.94 | Violation of AML § 10-8 |
| **Backward Rotation** | 0.49 | Night -> Evening or Evening -> Day |
| **Successive Nights** | 0.68 | Added for every night after the first |
| **Night Shift (Base)** | 0.22 | Standard health risk multiplier |

---

## 📁 File Structure

```text
/
├── CLAUDE.md              # This file
├── main.py                # Streamlit Entry Point
├── data/                  # Sample Gat Exports (Excluded from Git)
├── logic/
│   ├── parser.py          # The Gat-Slayer
│   ├── auditor.py         # The Logic Engine
│   └── fatigue.py         # The Burnout Predictor
├── config/
│   └── rules.json         # Versioned AML/HTA Thresholds
└── tests/
    └── test_scenarios.py  # 20 Stress Test Scenarios

```

---

## 🛠 Strategic Directives for Claude Code

1. **Sovereignty First:** Do not use US-based subprocessors (Sentry, Firebase, etc.). All logic and data must remain local to the Python instance.
2. **Polars Over Pandas:** Always use Polars for data processing to handle large municipality datasets efficiently.
3. **No Fake Truths:** If a shift code is unknown, do not guess. Trigger a `MAPPING_REQUIRED` state.
4. **Audit Trail:** Every flag raised must reference a specific paragraph in the **AML** or **HTA**.

---

## 🚀 Execution Commands

* **Initialize:** `pip install polars openpyxl streamlit fastapi`
* **Run Stress Test:** `python tests/generate_chaos.py && pytest tests/test_scenarios.py`
* **Start UI:** `streamlit run main.py`

---

### Your Immediate Next Step

Now that you have `CLAUDE.md`, open your terminal with Claude Code and give it this **First Directive**:

> "Read CLAUDE.md. Your first task is to implement the 'Gat-Slayer' parser in `logic/parser.py`. It must handle merged cells and fuzzy date formats. Create a test script using the 'Chaos Generator' script we discussed to prove the parser cannot be broken by messy Norwegian Excel files."

**Would you like me to refine the `rules.json` file now, so you can give Claude the exact JSON structure it needs to power the versioned logic engine?**
