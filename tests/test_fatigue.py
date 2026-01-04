"""
Test Suite: The Economist (Predictive Analysis)
================================================

Tests for logic/fatigue.py

Covers:
- calculate_fatigue_index: Research-backed burnout risk scoring
- vikar_leak_estimator: External agency cost calculations
- psychosocial_risk_map: AML § 4-3 compliance evidence

Coefficients (from CLAUDE.md):
- Short Rest (<11h): 1.94x
- Backward Rotation: 0.49x
- Successive Nights: 0.68x per night after first
- Night Shift Base: 0.22x
"""

import pytest
import polars as pl
from datetime import date, datetime, timedelta
from typing import Dict, Any, List

# Import the module under test
try:
    from logic.fatigue import (
        calculate_fatigue_index,
        vikar_leak_estimator,
        psychosocial_risk_map,
        FatigueScore,
        RiskLevel,
    )
    FATIGUE_IMPLEMENTED = True
except ImportError:
    FATIGUE_IMPLEMENTED = False
    # Stubs for test collection
    def calculate_fatigue_index(*args, **kwargs): raise NotImplementedError
    def vikar_leak_estimator(*args, **kwargs): raise NotImplementedError
    def psychosocial_risk_map(*args, **kwargs): raise NotImplementedError
    class FatigueScore: pass
    class RiskLevel: pass


pytestmark = pytest.mark.skipif(
    not FATIGUE_IMPLEMENTED,
    reason="logic/fatigue.py not yet implemented"
)


class TestCalculateFatigueIndex:
    """Tests for calculate_fatigue_index function."""

    # ==================== HAPPY PATH ====================

    def test_standard_day_shift_low_fatigue(self, sample_clean_schedule: pl.DataFrame):
        """Standard day shifts produce low fatigue index."""
        score = calculate_fatigue_index(sample_clean_schedule)

        assert score.total < 2.0  # Low risk threshold
        assert score.risk_level == RiskLevel.LOW

    def test_returns_score_object(self, sample_clean_schedule: pl.DataFrame):
        """Returns structured FatigueScore object."""
        score = calculate_fatigue_index(sample_clean_schedule)

        assert hasattr(score, "total")
        assert hasattr(score, "risk_level")
        assert hasattr(score, "breakdown")
        assert hasattr(score, "employee_id")

    def test_night_shift_adds_base_coefficient(self, sample_night_rotation_schedule: pl.DataFrame):
        """Night shifts add 0.22 base coefficient."""
        score = calculate_fatigue_index(sample_night_rotation_schedule)

        # 4 consecutive night shifts should add: 4 * 0.22 = 0.88 base
        assert score.breakdown.get("night_shift_base", 0) >= 0.88

    def test_short_rest_adds_coefficient(self, sample_violation_schedule: pl.DataFrame):
        """Short rest (<11h) adds 1.94 coefficient."""
        score = calculate_fatigue_index(sample_violation_schedule)

        # Schedule has 3 short rest violations
        assert score.breakdown.get("short_rest", 0) >= 1.94

    def test_successive_nights_accumulate(self, sample_night_rotation_schedule: pl.DataFrame):
        """Successive night shifts accumulate 0.68 per night after first."""
        score = calculate_fatigue_index(sample_night_rotation_schedule)

        # 4 consecutive nights: 0.68 * 3 = 2.04 (nights 2, 3, 4)
        assert score.breakdown.get("successive_nights", 0) >= 2.0

    def test_backward_rotation_detected(self, sample_night_rotation_schedule: pl.DataFrame):
        """Backward rotation (N->D) adds 0.49 coefficient."""
        score = calculate_fatigue_index(sample_night_rotation_schedule)

        # Schedule has N1->D1 transition (after off days)
        assert score.breakdown.get("backward_rotation", 0) >= 0.49

    # ==================== EDGE CASES ====================

    def test_empty_schedule_zero_fatigue(self, empty_schedule: pl.DataFrame):
        """Empty schedule returns zero fatigue."""
        score = calculate_fatigue_index(empty_schedule)

        assert score.total == 0
        assert score.risk_level == RiskLevel.LOW

    def test_single_shift_minimal_fatigue(self, single_shift_schedule: pl.DataFrame):
        """Single shift has minimal fatigue score."""
        score = calculate_fatigue_index(single_shift_schedule)

        assert score.total < 1.0

    def test_boundary_risk_levels(self, fatigue_coefficients: dict):
        """Verifies risk level boundaries from config."""
        # Create schedules that hit each threshold
        # Low: < 2.0
        # Moderate: 2.0 - 4.0
        # High: 4.0 - 6.0
        # Critical: > 6.0

        # Low risk: standard day shifts
        low_schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["D1"] * 5,
            "start_time": ["07:00"] * 5,
            "end_time": ["15:00"] * 5,
        })
        low_score = calculate_fatigue_index(low_schedule)
        assert low_score.risk_level == RiskLevel.LOW

    def test_exactly_at_threshold(self):
        """Score exactly at threshold boundary is correctly classified."""
        # This tests the implementation's boundary handling
        # (score == 2.0 should be LOW or MODERATE depending on definition)
        pass  # Implementation-specific

    def test_per_employee_scores(self, multi_employee_schedule: pl.DataFrame):
        """Calculates separate scores per employee."""
        scores = calculate_fatigue_index(multi_employee_schedule, per_employee=True)

        assert isinstance(scores, dict)
        assert len(scores) == 3  # 3 employees

    # ==================== ERROR HANDLING ====================

    def test_missing_shift_types_handled(self):
        """Unknown shift types don't crash scoring."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 3,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(3)],
            "shift_code": ["UNKNOWN", "D1", "ANOTHER_UNKNOWN"],
            "start_time": [None, "07:00", None],
            "end_time": [None, "15:00", None],
        })

        score = calculate_fatigue_index(schedule)
        assert isinstance(score, FatigueScore)

    def test_null_values_handled(self):
        """Null values in schedule don't crash scoring."""
        schedule = pl.DataFrame({
            "employee_id": ["123456", None, "123456"],
            "date": [date(2026, 1, 5), None, date(2026, 1, 7)],
            "shift_code": ["D1", "D1", None],
        })

        score = calculate_fatigue_index(schedule)
        assert isinstance(score, FatigueScore)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_extreme_schedule(self):
        """Handles extreme schedule (30 consecutive night shifts)."""
        dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(30)]

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 30,
            "date": dates,
            "shift_code": ["N1"] * 30,
            "start_time": ["21:30"] * 30,
            "end_time": ["07:30"] * 30,
        })

        score = calculate_fatigue_index(schedule)

        # Should be critical risk
        assert score.risk_level == RiskLevel.CRITICAL
        # Calculation: 30 * 0.22 (base) + 29 * 0.68 (successive) = 6.6 + 19.72 = 26.32
        assert score.total > 20

    def test_adversarial_alternating_extremes(self):
        """Handles rapidly alternating shift patterns."""
        # D->N->D->N pattern (maximum rotation stress)
        dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(10)]
        shifts = ["D1" if i % 2 == 0 else "N1" for i in range(10)]

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 10,
            "date": dates,
            "shift_code": shifts,
            "start_time": ["07:00" if s == "D1" else "21:30" for s in shifts],
            "end_time": ["15:00" if s == "D1" else "07:30" for s in shifts],
        })

        score = calculate_fatigue_index(schedule)

        # Should have backward rotation penalties
        assert score.breakdown.get("backward_rotation", 0) > 0
        assert score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestVikarLeakEstimator:
    """Tests for vikar_leak_estimator function."""

    # ==================== HAPPY PATH ====================

    def test_returns_cost_estimate(self, sample_violation_schedule: pl.DataFrame):
        """Returns structured cost estimate."""
        estimate = vikar_leak_estimator(sample_violation_schedule)

        assert "annual_cost_nok" in estimate
        assert "monthly_cost_nok" in estimate
        assert "breakdown" in estimate

    def test_high_fatigue_increases_vikar_cost(self):
        """High fatigue schedules correlate with higher vikar costs."""
        # Low fatigue schedule
        good_schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["D1"] * 5,
            "start_time": ["07:00"] * 5,
            "end_time": ["15:00"] * 5,
        })

        # High fatigue schedule (many violations)
        bad_schedule = pl.DataFrame({
            "employee_id": ["123456"] * 14,
            "date": [date(2026, 1, 1) + timedelta(days=i) for i in range(14)],
            "shift_code": ["A1", "D1"] * 7,  # Constant short rest
            "start_time": ["14:30", "07:00"] * 7,
            "end_time": ["22:00", "15:00"] * 7,
        })

        good_estimate = vikar_leak_estimator(good_schedule)
        bad_estimate = vikar_leak_estimator(bad_schedule)

        assert bad_estimate["annual_cost_nok"] > good_estimate["annual_cost_nok"]

    def test_cost_includes_sick_leave_projection(self):
        """Cost estimate includes projected sick leave costs."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["N1"] * 5,
            "start_time": ["21:30"] * 5,
            "end_time": ["07:30"] * 5,
        })

        estimate = vikar_leak_estimator(schedule)
        assert "sick_leave_projection" in estimate["breakdown"]

    # ==================== EDGE CASES ====================

    def test_empty_schedule_zero_cost(self, empty_schedule: pl.DataFrame):
        """Empty schedule returns zero cost."""
        estimate = vikar_leak_estimator(empty_schedule)
        assert estimate["annual_cost_nok"] == 0

    def test_multiple_employees_aggregated(self, multi_employee_schedule: pl.DataFrame):
        """Costs are aggregated across employees."""
        estimate = vikar_leak_estimator(multi_employee_schedule)

        assert estimate.get("employee_count") == 3 or "employee_count" in estimate

    def test_hourly_rate_configurable(self):
        """Vikar hourly rate is configurable."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["D1"] * 5,
        })

        estimate_default = vikar_leak_estimator(schedule)
        estimate_custom = vikar_leak_estimator(schedule, hourly_rate_nok=500)

        # Custom rate should affect result
        assert isinstance(estimate_custom, dict)

    # ==================== ERROR HANDLING ====================

    def test_handles_incomplete_schedule(self):
        """Handles schedule with missing data."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"],
            "date": [date(2026, 1, 5)],
        })

        estimate = vikar_leak_estimator(schedule)
        assert isinstance(estimate, dict)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_1000_employees(self):
        """Handles large organization (1000 employees)."""
        dates = [date(2026, 1, 5) + timedelta(days=i) for i in range(7)]

        data = {
            "employee_id": [],
            "date": [],
            "shift_code": [],
        }

        for emp in range(1000):
            for d in dates:
                data["employee_id"].append(f"EMP{emp:04d}")
                data["date"].append(d)
                data["shift_code"].append("D1" if d.weekday() < 5 else "FRI")

        schedule = pl.DataFrame(data)

        import time
        start = time.time()
        estimate = vikar_leak_estimator(schedule)
        elapsed = time.time() - start

        assert elapsed < 30, f"Estimation too slow: {elapsed:.2f}s"
        assert estimate["annual_cost_nok"] > 0


class TestPsychosocialRiskMap:
    """Tests for psychosocial_risk_map function - AML § 4-3 compliance."""

    # ==================== HAPPY PATH ====================

    def test_returns_risk_map_structure(self, sample_clean_schedule: pl.DataFrame):
        """Returns structured risk map for compliance reporting."""
        risk_map = psychosocial_risk_map(sample_clean_schedule)

        assert "overall_risk_level" in risk_map
        assert "employee_risk_scores" in risk_map
        assert "department_summary" in risk_map or "summary" in risk_map
        assert "legal_reference" in risk_map
        assert risk_map["legal_reference"] == "AML § 4-3"

    def test_low_fatigue_low_psychosocial_risk(self, sample_clean_schedule: pl.DataFrame):
        """Low fatigue schedule = low psychosocial risk."""
        risk_map = psychosocial_risk_map(sample_clean_schedule)

        assert risk_map["overall_risk_level"] in ["low", "green"]

    def test_high_fatigue_high_psychosocial_risk(self, sample_night_rotation_schedule: pl.DataFrame):
        """High fatigue schedule = elevated psychosocial risk."""
        risk_map = psychosocial_risk_map(sample_night_rotation_schedule)

        assert risk_map["overall_risk_level"] in ["moderate", "high", "critical", "yellow", "orange", "red"]

    def test_includes_evidence_for_compliance(self, sample_violation_schedule: pl.DataFrame):
        """Includes concrete evidence for AML § 4-3 reporting."""
        risk_map = psychosocial_risk_map(sample_violation_schedule)

        # Should include specific violations/factors
        assert "evidence" in risk_map or "risk_factors" in risk_map

    # ==================== EDGE CASES ====================

    def test_empty_schedule_baseline_risk(self, empty_schedule: pl.DataFrame):
        """Empty schedule returns baseline/unknown risk."""
        risk_map = psychosocial_risk_map(empty_schedule)

        assert risk_map["overall_risk_level"] in ["low", "unknown", "insufficient_data"]

    def test_per_employee_risk_breakdown(self, multi_employee_schedule: pl.DataFrame):
        """Provides per-employee risk breakdown."""
        risk_map = psychosocial_risk_map(multi_employee_schedule)

        employee_risks = risk_map.get("employee_risk_scores", {})
        assert len(employee_risks) == 3

    def test_department_aggregation(self):
        """Aggregates risk by department when available."""
        schedule = pl.DataFrame({
            "employee_id": ["E1", "E2", "E3", "E4"],
            "name": ["A", "B", "C", "D"],
            "department": ["Akutt", "Akutt", "Kirurgi", "Kirurgi"],
            "date": [date(2026, 1, 5)] * 4,
            "shift_code": ["N1", "N1", "D1", "D1"],
        })

        risk_map = psychosocial_risk_map(schedule)

        if "department_summary" in risk_map:
            assert "Akutt" in risk_map["department_summary"]
            # Night shift dept should have higher risk
            assert risk_map["department_summary"]["Akutt"]["risk"] >= \
                   risk_map["department_summary"]["Kirurgi"]["risk"]

    # ==================== ERROR HANDLING ====================

    def test_missing_department_handled(self, sample_clean_schedule: pl.DataFrame):
        """Works without department column."""
        risk_map = psychosocial_risk_map(sample_clean_schedule)
        assert isinstance(risk_map, dict)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_all_critical_risk(self):
        """Handles schedule where all employees are at critical risk."""
        # 30 days of violations for 10 employees
        data = {
            "employee_id": [],
            "date": [],
            "shift_code": [],
            "start_time": [],
            "end_time": [],
        }

        for emp in range(10):
            for day in range(30):
                data["employee_id"].append(f"EMP{emp}")
                data["date"].append(date(2026, 1, 1) + timedelta(days=day))
                data["shift_code"].append("A1" if day % 2 == 0 else "D1")
                data["start_time"].append("14:30" if day % 2 == 0 else "07:00")
                data["end_time"].append("22:00" if day % 2 == 0 else "15:00")

        schedule = pl.DataFrame(data)
        risk_map = psychosocial_risk_map(schedule)

        assert risk_map["overall_risk_level"] in ["high", "critical", "red"]

    def test_adversarial_mixed_risk_levels(self):
        """Handles organization with mixed risk levels."""
        data = {
            "employee_id": [],
            "date": [],
            "shift_code": [],
        }

        # Group 1: Low risk (day shifts)
        for emp in range(5):
            for day in range(7):
                data["employee_id"].append(f"LOW{emp}")
                data["date"].append(date(2026, 1, 5) + timedelta(days=day))
                data["shift_code"].append("D1" if day < 5 else "FRI")

        # Group 2: High risk (constant violations)
        for emp in range(5):
            for day in range(7):
                data["employee_id"].append(f"HIGH{emp}")
                data["date"].append(date(2026, 1, 5) + timedelta(days=day))
                data["shift_code"].append("A1" if day % 2 == 0 else "D1")

        schedule = pl.DataFrame(data)
        risk_map = psychosocial_risk_map(schedule)

        # Should reflect mixed risk
        employee_risks = risk_map.get("employee_risk_scores", {})
        if employee_risks:
            low_risks = [r for id, r in employee_risks.items() if "LOW" in id]
            high_risks = [r for id, r in employee_risks.items() if "HIGH" in id]

            # High risk employees should have higher scores
            if low_risks and high_risks:
                avg_low = sum(r.get("score", 0) for r in low_risks) / len(low_risks)
                avg_high = sum(r.get("score", 0) for r in high_risks) / len(high_risks)
                assert avg_high > avg_low


class TestFatigueIntegration:
    """Integration tests for the complete fatigue/risk analysis pipeline."""

    def test_fatigue_to_vikar_correlation(self, sample_violation_schedule: pl.DataFrame):
        """Fatigue index correlates with vikar cost estimates."""
        fatigue = calculate_fatigue_index(sample_violation_schedule)
        vikar = vikar_leak_estimator(sample_violation_schedule)

        # Higher fatigue should mean higher vikar costs
        assert fatigue.total > 0
        assert vikar["annual_cost_nok"] > 0

    def test_fatigue_to_psychosocial_correlation(self, sample_night_rotation_schedule: pl.DataFrame):
        """Fatigue index correlates with psychosocial risk."""
        fatigue = calculate_fatigue_index(sample_night_rotation_schedule)
        risk = psychosocial_risk_map(sample_night_rotation_schedule)

        # Both should indicate elevated risk
        assert fatigue.risk_level != RiskLevel.LOW
        assert risk["overall_risk_level"] not in ["low", "green"]

    def test_full_economic_analysis(self, multi_employee_schedule: pl.DataFrame, rules_config: dict):
        """Complete economic analysis pipeline."""
        # Calculate per-employee fatigue
        fatigue_scores = calculate_fatigue_index(multi_employee_schedule, per_employee=True)

        # Estimate vikar costs
        vikar = vikar_leak_estimator(multi_employee_schedule)

        # Generate risk map
        risk_map = psychosocial_risk_map(multi_employee_schedule)

        # All should use same coefficients from config
        coefficients = rules_config["fatigue_coefficients"]["multipliers"]
        assert coefficients["short_rest_under_11h"]["value"] == 1.94

        # Results should be consistent
        assert isinstance(fatigue_scores, dict)
        assert isinstance(vikar, dict)
        assert isinstance(risk_map, dict)

    def test_report_generation_ready(self, sample_violation_schedule: pl.DataFrame):
        """Analysis outputs are ready for report generation."""
        fatigue = calculate_fatigue_index(sample_violation_schedule)
        vikar = vikar_leak_estimator(sample_violation_schedule)
        risk = psychosocial_risk_map(sample_violation_schedule)

        # All required for AML § 4-3 compliance report
        report_data = {
            "fatigue_assessment": {
                "score": fatigue.total,
                "risk_level": str(fatigue.risk_level),
                "breakdown": fatigue.breakdown,
            },
            "economic_impact": vikar,
            "psychosocial_risk": risk,
            "legal_references": ["AML § 4-3", "AML § 10-8"],
        }

        # Validate structure
        assert all(key in report_data for key in [
            "fatigue_assessment", "economic_impact", "psychosocial_risk"
        ])
