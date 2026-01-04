"""
Integration Test Suite: End-to-End Pipeline
============================================

Tests the complete Turnus Risk Audit pipeline from raw data to compliance report.

Pipeline:
1. Raw Excel/Gat Export → Gat-Slayer (parser)
2. Clean DataFrame → Auditor (legal engine)
3. Audit Results → Economist (risk/cost analysis)
4. Combined → Compliance Report

This suite validates that all components work together correctly.
"""

import pytest
import polars as pl
from pathlib import Path
from datetime import date, timedelta
import json
import tempfile
from typing import Dict, Any

# Try to import all modules
try:
    from logic.parser import (
        clean_gat_export,
        fuzzy_header_match,
        vakt_code_mapper,
        data_validation_report,
    )
    from logic.auditor import (
        sliding_window_11h,
        weekly_rest_35h,
        HTA_compliance_check,
        compensatory_rest_tracker,
    )
    from logic.fatigue import (
        calculate_fatigue_index,
        vikar_leak_estimator,
        psychosocial_risk_map,
        RiskLevel,
    )
    ALL_MODULES_IMPLEMENTED = True
except ImportError:
    ALL_MODULES_IMPLEMENTED = False


pytestmark = pytest.mark.skipif(
    not ALL_MODULES_IMPLEMENTED,
    reason="Not all modules implemented yet"
)


class TestEndToEndPipeline:
    """Full pipeline integration tests."""

    def test_excel_to_compliance_report(self, temp_excel_file: Path, rules_config: dict):
        """Complete pipeline: Excel → Parser → Auditor → Economist → Report."""

        # Step 1: Parse the Excel file
        df = clean_gat_export(temp_excel_file)
        assert isinstance(df, pl.DataFrame)
        assert len(df) > 0

        # Step 2: Validate the parsed data
        validation = data_validation_report(df)
        assert validation["status"] in ["valid", "warning"]

        # Step 3: Map shift codes (enrich with times)
        shift_codes = rules_config["shift_codes"]["standard"]
        enriched_data = []

        for row in df.iter_rows(named=True):
            code = row.get("shift_code", "")
            if code and str(code).strip():
                try:
                    mapped = vakt_code_mapper(str(code).strip(), shift_codes)
                    enriched_data.append({
                        **row,
                        "start_time": mapped.get("start"),
                        "end_time": mapped.get("end"),
                        "shift_type": mapped.get("type"),
                    })
                except:
                    enriched_data.append({**row, "shift_type": "unknown"})

        enriched_df = pl.DataFrame(enriched_data)

        # Step 4: Run audit checks
        daily_violations = sliding_window_11h(enriched_df)
        weekly_violations = weekly_rest_35h(enriched_df)
        hta_result = HTA_compliance_check(enriched_df)
        rest_debt = compensatory_rest_tracker(enriched_df)

        # Step 5: Calculate risk metrics
        fatigue = calculate_fatigue_index(enriched_df)
        vikar_cost = vikar_leak_estimator(enriched_df)
        psych_risk = psychosocial_risk_map(enriched_df)

        # Step 6: Compile compliance report
        report = {
            "generated_at": date.today().isoformat(),
            "data_quality": {
                "row_count": validation["row_count"],
                "employee_count": validation["employee_count"],
                "status": validation["status"],
            },
            "legal_compliance": {
                "daily_rest_violations": len(daily_violations),
                "weekly_rest_violations": len(weekly_violations),
                "hta_compliant": hta_result.get("weekly_hours_compliant", True),
                "sunday_rotation_compliant": hta_result.get("sunday_rotation_compliant", True),
                "compensatory_rest_debt_hours": rest_debt["total_debt_hours"],
            },
            "risk_assessment": {
                "fatigue_index": fatigue.total,
                "risk_level": str(fatigue.risk_level),
                "psychosocial_risk": psych_risk["overall_risk_level"],
            },
            "economic_impact": {
                "projected_annual_vikar_cost_nok": vikar_cost["annual_cost_nok"],
                "projected_monthly_vikar_cost_nok": vikar_cost["monthly_cost_nok"],
            },
            "legal_references": [
                "AML § 10-8 (Daglig og ukentlig hvile)",
                "AML § 10-4 (Søndagsarbeid)",
                "AML § 4-3 (Psykososialt arbeidsmiljø)",
                "HTA 2024-2026",
            ],
        }

        # Validate report structure
        assert "legal_compliance" in report
        assert "risk_assessment" in report
        assert "economic_impact" in report

    def test_multi_employee_pipeline(self, multi_employee_schedule: pl.DataFrame):
        """Pipeline handles multiple employees correctly."""

        # Run all audit checks
        daily = sliding_window_11h(multi_employee_schedule)
        weekly = weekly_rest_35h(multi_employee_schedule)

        # Calculate per-employee metrics
        fatigue_scores = calculate_fatigue_index(multi_employee_schedule, per_employee=True)

        # Verify per-employee breakdown
        assert len(fatigue_scores) == 3  # 3 employees

        # Each employee should have independent scores
        for emp_id, score in fatigue_scores.items():
            assert hasattr(score, "total")
            assert hasattr(score, "risk_level")

    def test_violation_cascade(self, sample_violation_schedule: pl.DataFrame):
        """Violations in one module cascade correctly to downstream analysis."""

        # Audit finds violations
        daily_violations = sliding_window_11h(sample_violation_schedule)
        assert len(daily_violations) > 0

        # Fatigue reflects these violations
        fatigue = calculate_fatigue_index(sample_violation_schedule)
        assert fatigue.breakdown.get("short_rest", 0) > 0

        # Risk assessment reflects elevated risk
        risk = psychosocial_risk_map(sample_violation_schedule)
        assert risk["overall_risk_level"] not in ["low", "green"]

        # Economic impact is non-zero
        vikar = vikar_leak_estimator(sample_violation_schedule)
        assert vikar["annual_cost_nok"] > 0

    def test_compliant_schedule_zero_impact(self, sample_clean_schedule: pl.DataFrame):
        """Compliant schedules produce zero/minimal violations and costs."""

        daily = sliding_window_11h(sample_clean_schedule)
        weekly = weekly_rest_35h(sample_clean_schedule)
        fatigue = calculate_fatigue_index(sample_clean_schedule)
        debt = compensatory_rest_tracker(sample_clean_schedule)

        assert len(daily) == 0
        assert len(weekly) == 0
        assert fatigue.risk_level == RiskLevel.LOW
        assert debt["total_debt_hours"] == 0


class TestDataFlowIntegrity:
    """Tests that data flows correctly between components."""

    def test_employee_ids_preserved(self, multi_employee_schedule: pl.DataFrame):
        """Employee IDs are preserved through the pipeline."""

        original_ids = set(multi_employee_schedule["employee_id"].unique().to_list())

        # Run through parser validation
        report = data_validation_report(multi_employee_schedule)

        # Run through auditor
        violations = sliding_window_11h(multi_employee_schedule)
        violation_ids = set(v.employee_id for v in violations) if violations else set()

        # All violation IDs should be from original data
        assert violation_ids.issubset(original_ids)

    def test_dates_preserved(self, sample_violation_schedule: pl.DataFrame):
        """Dates are preserved and correctly handled."""

        original_dates = set(sample_violation_schedule["date"].to_list())

        violations = sliding_window_11h(sample_violation_schedule)

        for v in violations:
            assert v.date in original_dates or \
                   v.date - timedelta(days=1) in original_dates

    def test_shift_codes_mapped_consistently(self, rules_config: dict):
        """Shift codes map consistently across components."""

        shift_codes = rules_config["shift_codes"]["standard"]

        # Create schedule with all standard codes
        all_codes = list(shift_codes.keys())
        dates = [date(2026, 1, 5) + timedelta(days=i) for i in range(len(all_codes))]

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * len(all_codes),
            "date": dates,
            "shift_code": all_codes,
        })

        # Map all codes
        for code in all_codes:
            mapped = vakt_code_mapper(code, shift_codes)

            # Verify mapping consistency
            expected = shift_codes.get(code, {})
            if expected.get("start"):
                assert mapped["start"] == expected["start"]
            if expected.get("type"):
                assert mapped["type"] == expected["type"]


class TestConfigConsistency:
    """Tests that configuration is used consistently."""

    def test_fatigue_coefficients_from_config(self, rules_config: dict):
        """Fatigue calculations use coefficients from config."""

        coefficients = rules_config["fatigue_coefficients"]["multipliers"]

        # Verify coefficients match CLAUDE.md specification
        assert coefficients["short_rest_under_11h"]["value"] == 1.94
        assert coefficients["backward_rotation"]["value"] == 0.49
        assert coefficients["successive_nights"]["value"] == 0.68
        assert coefficients["night_shift_base"]["value"] == 0.22

    def test_legal_thresholds_from_config(self, rules_config: dict):
        """Legal thresholds use values from config."""

        aml = rules_config["aml"]["section_10_8"]

        # Verify AML § 10-8 thresholds
        assert aml["daily_rest"]["threshold_hours"] == 11
        assert aml["weekly_rest"]["threshold_hours"] == 35
        assert aml["reduced_rest"]["minimum_hours"] == 8

    def test_risk_level_thresholds(self, rules_config: dict):
        """Risk level classifications use config thresholds."""

        thresholds = rules_config["fatigue_coefficients"]["thresholds"]

        assert thresholds["low_risk"]["max"] == 2.0
        assert thresholds["moderate_risk"]["min"] == 2.0
        assert thresholds["moderate_risk"]["max"] == 4.0
        assert thresholds["high_risk"]["min"] == 4.0
        assert thresholds["high_risk"]["max"] == 6.0
        assert thresholds["critical_risk"]["min"] == 6.0


class TestErrorRecovery:
    """Tests system resilience and error recovery."""

    def test_partial_data_handling(self):
        """System handles partial/incomplete data gracefully."""

        # Missing columns
        incomplete = pl.DataFrame({
            "employee_id": ["123456", "123457"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            # Missing shift_code, start_time, end_time
        })

        # Should not crash, should return appropriate warnings
        try:
            report = data_validation_report(incomplete)
            assert report["status"] in ["invalid", "warning"]
        except ValueError:
            pass  # Acceptable to reject invalid data

    def test_mixed_quality_data(self):
        """System handles mixed quality data (some good, some bad)."""

        mixed = pl.DataFrame({
            "employee_id": ["123456", None, "789012", ""],
            "date": [date(2026, 1, 5), date(2026, 1, 6), None, date(2026, 1, 8)],
            "shift_code": ["D1", "INVALID", "N1", None],
        })

        report = data_validation_report(mixed)
        # Should process what it can and flag issues
        assert "flags" in report or report["status"] == "invalid"

    def test_component_isolation(self, sample_clean_schedule: pl.DataFrame):
        """Failure in one component doesn't cascade unexpectedly."""

        # Auditor should work independently of fatigue module
        violations = sliding_window_11h(sample_clean_schedule)
        assert isinstance(violations, list)

        # Fatigue should work independently of auditor
        fatigue = calculate_fatigue_index(sample_clean_schedule)
        assert hasattr(fatigue, "total")


class TestPerformanceIntegration:
    """Performance tests for the integrated pipeline."""

    def test_large_organization_performance(self):
        """Pipeline handles large organization (500 employees, 1 year)."""

        # Generate large dataset
        employees = [f"EMP{i:04d}" for i in range(500)]
        dates = [date(2026, 1, 1) + timedelta(days=d) for d in range(365)]

        data = {
            "employee_id": [],
            "date": [],
            "shift_code": [],
            "start_time": [],
            "end_time": [],
        }

        import random
        shifts = ["D1", "D1", "D1", "A1", "N1", "FRI", "FRI"]

        for emp in employees:
            for d in dates:
                data["employee_id"].append(emp)
                data["date"].append(d)
                shift = random.choice(shifts)
                data["shift_code"].append(shift)
                if shift == "D1":
                    data["start_time"].append("07:00")
                    data["end_time"].append("15:00")
                elif shift == "A1":
                    data["start_time"].append("14:30")
                    data["end_time"].append("22:00")
                elif shift == "N1":
                    data["start_time"].append("21:30")
                    data["end_time"].append("07:30")
                else:
                    data["start_time"].append(None)
                    data["end_time"].append(None)

        large_schedule = pl.DataFrame(data)

        import time
        start = time.time()

        # Run full pipeline
        validation = data_validation_report(large_schedule)
        daily = sliding_window_11h(large_schedule)
        weekly = weekly_rest_35h(large_schedule)
        fatigue = calculate_fatigue_index(large_schedule)

        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 60, f"Pipeline too slow: {elapsed:.2f}s for 500 employees x 365 days"

        # Should produce valid results
        assert validation["row_count"] == 500 * 365
        assert isinstance(daily, list)
        assert isinstance(weekly, list)
        assert hasattr(fatigue, "total")


class TestScenarioTests:
    """Real-world scenario tests."""

    def test_scenario_hospital_department(self, rules_config: dict):
        """Simulate a hospital department schedule."""

        # 20 nurses, 4-week rotation
        nurses = [f"SYK{i:04d}" for i in range(20)]
        rotation_pattern = [
            # Week 1
            ["D1", "D1", "D1", "D1", "D1", "FRI", "FRI"],
            # Week 2
            ["A1", "A1", "A1", "FRI", "FRI", "N1", "N1"],
            # Week 3
            ["N1", "N1", "FRI", "FRI", "FRI", "D1", "D1"],
            # Week 4
            ["D1", "D1", "A1", "A1", "A1", "FRI", "FRI"],
        ]

        data = {"employee_id": [], "date": [], "shift_code": [], "start_time": [], "end_time": []}

        start_date = date(2026, 1, 5)  # Monday

        for nurse_idx, nurse in enumerate(nurses):
            # Stagger rotation by nurse index
            offset = nurse_idx % 4

            for week in range(4):
                pattern = rotation_pattern[(week + offset) % 4]
                for day, shift in enumerate(pattern):
                    d = start_date + timedelta(weeks=week, days=day)
                    data["employee_id"].append(nurse)
                    data["date"].append(d)
                    data["shift_code"].append(shift)

                    times = {
                        "D1": ("07:00", "15:00"),
                        "A1": ("14:30", "22:00"),
                        "N1": ("21:30", "07:30"),
                        "FRI": (None, None),
                    }
                    data["start_time"].append(times[shift][0])
                    data["end_time"].append(times[shift][1])

        schedule = pl.DataFrame(data)

        # Run compliance check
        daily_violations = sliding_window_11h(schedule)
        weekly_violations = weekly_rest_35h(schedule)
        hta = HTA_compliance_check(schedule)
        fatigue = calculate_fatigue_index(schedule, per_employee=True)

        # Verify realistic results
        # This rotation should have some short rest issues (N1->D1 transitions)
        # but be mostly compliant

        assert isinstance(daily_violations, list)
        assert len(fatigue) == 20  # All nurses assessed

    def test_scenario_violation_investigation(self):
        """Investigate a specific compliance violation."""

        # Employee with known violation pattern
        schedule = pl.DataFrame({
            "employee_id": ["INVESTIGATE_001"] * 14,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(14)],
            "shift_code": [
                "D1", "D1", "A1", "D1",  # Violation: A1(22:00) -> D1(07:00) = 9h
                "D1", "FRI", "FRI",
                "D1", "A1", "D1",  # Another violation
                "A1", "D1",  # Another violation
                "FRI", "FRI",
            ],
            "start_time": [
                "07:00", "07:00", "14:30", "07:00",
                "07:00", None, None,
                "07:00", "14:30", "07:00",
                "14:30", "07:00",
                None, None,
            ],
            "end_time": [
                "15:00", "15:00", "22:00", "15:00",
                "15:00", None, None,
                "15:00", "22:00", "15:00",
                "22:00", "15:00",
                None, None,
            ],
        })

        violations = sliding_window_11h(schedule)

        # Should find exactly 3 violations
        assert len(violations) == 3

        # Each violation should have complete audit trail
        for v in violations:
            assert v.legal_reference == "AML § 10-8"
            assert v.rest_hours < 11
            assert v.required_hours == 11
            assert v.employee_id == "INVESTIGATE_001"
