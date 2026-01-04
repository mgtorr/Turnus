# Turnus Risk Audit - Verification Plan

## Overview

This document outlines the complete verification strategy for the Turnus Risk Audit system, a Norwegian labor law compliance engine targeting AML § 10-8 (Rest Periods) and AML § 4-3 (Psychosocial Workload).

## Test Suite Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── test_parser.py        # The Gat-Slayer (71 test cases)
├── test_auditor.py       # The Auditor (68 test cases)
├── test_fatigue.py       # The Economist (52 test cases)
├── test_integration.py   # End-to-end pipeline (24 test cases)
└── generate_chaos.py     # Adversarial data generator
```

**Total: 215+ test cases**

---

## Test Categories

### 1. Happy Path Tests
Standard expected usage scenarios:
- Clean data parsing
- Compliant schedules
- Correct coefficient calculations
- Proper audit trail generation

### 2. Edge Cases
Boundary conditions:
- Empty schedules
- Single shift schedules
- Exactly-at-threshold values (11h rest, 35h weekly)
- One-minute-off boundaries

### 3. Error Handling
Graceful failure scenarios:
- Missing files
- Invalid formats
- Corrupted data
- Missing columns
- Null values

### 4. Adversarial Tests
Designed to break the system:
- SQL/XSS injection in cell values
- Unicode bombs
- Extremely long strings
- Formula injection
- Mixed encodings
- 10,000+ row files
- 100 consecutive violations

---

## Module-Specific Verification

### The Gat-Slayer (Parser)

| Function | Test Focus | Adversarial |
|----------|-----------|-------------|
| `clean_gat_export` | Merged cells, Norwegian chars (ÆØÅ), forward-fill | Formula injection, encoding bombs |
| `fuzzy_header_match` | Header variants, case insensitivity | SQL injection in headers |
| `vakt_code_mapper` | Standard codes, unknown codes → MAPPING_REQUIRED | Malformed codes |
| `data_validation_report` | Human noise detection, duplicates | All-invalid data |

### The Auditor (Legal Engine)

| Function | Test Focus | Legal Reference |
|----------|-----------|-----------------|
| `sliding_window_11h` | Rest < 11h in 24h window | AML § 10-8 |
| `weekly_rest_35h` | 168h rolling window check | AML § 10-8 |
| `HTA_compliance_check` | 35.5h/33.6h limits, Sunday rotation | HTA 2024-2026 |
| `compensatory_rest_tracker` | 8h exception debt, 168h deadline | AML § 10-8 |

### The Economist (Risk Analysis)

| Function | Test Focus | Coefficients |
|----------|-----------|--------------|
| `calculate_fatigue_index` | Score calculation, risk levels | 1.94, 0.49, 0.68, 0.22 |
| `vikar_leak_estimator` | Cost projection, sick leave | NOK hourly rates |
| `psychosocial_risk_map` | AML § 4-3 evidence, department aggregation | Risk thresholds |

---

## Verification Checklist

### Pre-Implementation (TDD)

- [ ] All test files created
- [ ] Fixtures defined in conftest.py
- [ ] rules.json with correct thresholds
- [ ] Chaos generator operational
- [ ] Tests properly skip when modules not implemented

### During Implementation

For each module:
- [ ] Implement minimum viable function
- [ ] Run targeted tests: `pytest tests/test_<module>.py`
- [ ] Fix failing tests
- [ ] Add implementation-specific tests if needed
- [ ] Verify no regressions

### Post-Implementation

- [ ] All unit tests pass: `pytest tests/test_*.py`
- [ ] Integration tests pass: `pytest tests/test_integration.py`
- [ ] Adversarial tests pass: `pytest -k adversarial`
- [ ] Performance acceptable: <60s for 500 employees × 365 days
- [ ] Coverage >80%: `pytest --cov=logic`

---

## Running Verification

### Quick Check
```bash
./scripts/verify.sh --quick
```

### Full Suite
```bash
./scripts/verify.sh
```

### With Chaos Data
```bash
./scripts/verify.sh --chaos --verbose
```

### CI Mode (Strict)
```bash
./scripts/verify.sh --ci --coverage
```

### Manual pytest
```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_parser.py -v

# By marker
pytest -m adversarial
pytest -m "not slow"

# With coverage
pytest --cov=logic --cov-report=html
```

---

## Legal Compliance Verification

### AML § 10-8 (Rest Periods)

| Rule | Threshold | Test Coverage |
|------|-----------|---------------|
| Daily rest | ≥11 hours in 24h | `test_sliding_window_11h` |
| Weekly rest | ≥35 hours in 168h | `test_weekly_rest_35h` |
| Reduced rest | ≥8 hours (compensable) | `test_compensatory_rest_tracker` |

### AML § 10-4 (Sunday Work)

| Rule | Threshold | Test Coverage |
|------|-----------|---------------|
| Consecutive Sundays | ≤3 without agreement | `test_4_consecutive_sundays_violation` |

### HTA 2024-2026

| Rule | Threshold | Test Coverage |
|------|-----------|---------------|
| Weekly hours (day) | ≤35.5h | `test_compliant_35_5h_week` |
| Weekly hours (night) | ≤33.6h | `test_night_shift_33_6h_limit` |

---

## Fatigue Coefficient Verification

From CLAUDE.md specification:

| Trigger | Expected Value | Test |
|---------|---------------|------|
| Short Rest (<11h) | 1.94 | `test_short_rest_adds_coefficient` |
| Backward Rotation | 0.49 | `test_backward_rotation_detected` |
| Successive Nights | 0.68/night | `test_successive_nights_accumulate` |
| Night Shift Base | 0.22 | `test_night_shift_adds_base_coefficient` |

Risk Level Thresholds:

| Level | Score Range | Color |
|-------|-------------|-------|
| Low | < 2.0 | Green |
| Moderate | 2.0 - 4.0 | Yellow |
| High | 4.0 - 6.0 | Orange |
| Critical | ≥ 6.0 | Red |

---

## Acceptance Criteria

The system is verified when:

1. **Functional**: All 215+ tests pass
2. **Legal**: Correct thresholds from AML/HTA applied
3. **Robust**: Adversarial tests don't crash the system
4. **Performant**: 500 employees × 1 year < 60 seconds
5. **Traceable**: Every violation includes legal paragraph reference
6. **Sovereign**: No US-based subprocessors (Polars, not cloud-dependent)

---

## Known Limitations

- Tests use mocked Excel files (no real Gat exports in repo)
- Performance tests assume local execution
- Some edge cases require real-world validation

---

## Next Steps After Verification

1. Implement stub modules to make tests pass
2. Integrate with Streamlit UI
3. Load real Gat export samples
4. Municipality pilot testing
5. Production deployment to Azure Norway East
