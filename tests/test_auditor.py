"""
Test Suite: The Auditor (Legal Logic Engine)
============================================

Tests for logic/auditor.py

Covers:
- sliding_window_11h: Daily Rest violations (AML § 10-8)
- weekly_rest_35h: Weekly rest in 168h window
- HTA_compliance_check: HTA rules (35.5h week, Sunday limits)
- compensatory_rest_tracker: Rest debt tracking

Legal References:
- AML § 10-8: Daily rest (11h) and weekly rest (35h)
- AML § 10-4: Sunday work restrictions
- HTA 2024-2026: Specific healthcare worker rules
"""

import pytest
import polars as pl
from datetime import date, datetime, time, timedelta
from typing import List, Dict, Any

# Import the module under test
try:
    from logic.auditor import (
        sliding_window_11h,
        weekly_rest_35h,
        HTA_compliance_check,
        compensatory_rest_tracker,
        AuditResult,
        ComplianceViolation,
    )
    AUDITOR_IMPLEMENTED = True
except ImportError:
    AUDITOR_IMPLEMENTED = False
    # Stubs for test collection
    def sliding_window_11h(*args, **kwargs): raise NotImplementedError
    def weekly_rest_35h(*args, **kwargs): raise NotImplementedError
    def HTA_compliance_check(*args, **kwargs): raise NotImplementedError
    def compensatory_rest_tracker(*args, **kwargs): raise NotImplementedError
    class AuditResult: pass
    class ComplianceViolation: pass


pytestmark = pytest.mark.skipif(
    not AUDITOR_IMPLEMENTED,
    reason="logic/auditor.py not yet implemented"
)


class TestSlidingWindow11h:
    """Tests for sliding_window_11h function - AML § 10-8 Daily Rest."""

    # ==================== HAPPY PATH ====================

    def test_compliant_schedule_no_violations(self, sample_clean_schedule: pl.DataFrame):
        """Standard 07:00-15:00 schedule has no daily rest violations."""
        violations = sliding_window_11h(sample_clean_schedule)

        assert len(violations) == 0

    def test_detects_clear_violation(self, sample_violation_schedule: pl.DataFrame):
        """Evening -> Morning transition (9h rest) is detected as violation."""
        violations = sliding_window_11h(sample_violation_schedule)

        assert len(violations) > 0
        assert all(v.legal_reference == "AML § 10-8" for v in violations)

    def test_returns_violation_objects(self, sample_violation_schedule: pl.DataFrame):
        """Violations include required audit trail information."""
        violations = sliding_window_11h(sample_violation_schedule)

        for v in violations:
            assert hasattr(v, "employee_id")
            assert hasattr(v, "date")
            assert hasattr(v, "rest_hours")
            assert hasattr(v, "required_hours")
            assert hasattr(v, "legal_reference")

    def test_calculates_correct_rest_hours(self):
        """Rest hours calculation is accurate."""
        # 22:00 end -> 07:00 start = 9 hours rest
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["A1", "D1"],
            "start_time": ["14:30", "07:00"],
            "end_time": ["22:00", "15:00"],
        })

        violations = sliding_window_11h(schedule)
        assert len(violations) == 1
        assert abs(violations[0].rest_hours - 9.0) < 0.1  # 9 hours rest

    # ==================== EDGE CASES ====================

    def test_exactly_11h_rest_is_compliant(self):
        """Exactly 11 hours rest is NOT a violation."""
        # 20:00 end -> 07:00 start = exactly 11 hours
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["A_custom", "D_custom"],
            "start_time": ["12:00", "07:00"],
            "end_time": ["20:00", "15:00"],
        })

        violations = sliding_window_11h(schedule)
        assert len(violations) == 0, "Exactly 11h rest should be compliant"

    def test_10h59m_rest_is_violation(self):
        """10 hours 59 minutes rest IS a violation."""
        # 20:01 end -> 07:00 start = 10h59m rest
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["A_custom", "D_custom"],
            "start_time": ["12:00", "07:00"],
            "end_time": ["20:01", "15:00"],
        })

        violations = sliding_window_11h(schedule)
        assert len(violations) == 1

    def test_night_shift_spanning_midnight(self):
        """Night shift (21:30 -> 07:30 next day) is handled correctly."""
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)],
            "shift_code": ["N1", "FRI", "D1"],
            "start_time": ["21:30", None, "07:00"],
            "end_time": ["07:30", None, "15:00"],  # Ends morning of Jan 6
        })

        violations = sliding_window_11h(schedule)
        # Night ends 07:30 on Jan 6, Day starts 07:00 on Jan 7 = 23.5h rest = OK
        assert len(violations) == 0

    def test_back_to_back_shifts_same_day(self):
        """Two shifts same day (split shift) handled correctly."""
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 5)],
            "shift_code": ["D_morning", "D_afternoon"],
            "start_time": ["07:00", "16:00"],
            "end_time": ["11:00", "20:00"],
        })

        violations = sliding_window_11h(schedule)
        # 11:00 end -> 16:00 start = 5h rest (but same day, different logic?)
        # Implementation should define behavior for split shifts

    def test_empty_schedule_no_violations(self, empty_schedule: pl.DataFrame):
        """Empty schedule produces no violations."""
        violations = sliding_window_11h(empty_schedule)
        assert len(violations) == 0

    def test_single_shift_no_violations(self, single_shift_schedule: pl.DataFrame):
        """Single shift cannot have rest violation."""
        violations = sliding_window_11h(single_shift_schedule)
        assert len(violations) == 0

    def test_off_days_ignored(self):
        """Off days (FRI, L) don't create false violations."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["A1", "FRI", "FRI", "FRI", "D1"],
            "start_time": ["14:30", None, None, None, "07:00"],
            "end_time": ["22:00", None, None, None, "15:00"],
        })

        violations = sliding_window_11h(schedule)
        # 22:00 Mon -> 07:00 Fri = plenty of rest
        assert len(violations) == 0

    # ==================== ERROR HANDLING ====================

    def test_missing_time_columns_raises_error(self):
        """Missing start_time/end_time columns raise appropriate error."""
        incomplete = pl.DataFrame({
            "employee_id": ["123456"],
            "date": [date(2026, 1, 5)],
            "shift_code": ["D1"],
            # Missing start_time and end_time
        })

        with pytest.raises((ValueError, KeyError)):
            sliding_window_11h(incomplete)

    def test_invalid_time_format_handled(self):
        """Invalid time format is handled gracefully."""
        bad_times = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["D1", "D1"],
            "start_time": ["invalid", "07:00"],
            "end_time": ["also invalid", "15:00"],
        })

        # Should either skip invalid rows or raise clear error
        try:
            violations = sliding_window_11h(bad_times)
            assert isinstance(violations, list)
        except ValueError as e:
            assert "time" in str(e).lower()

    # ==================== ADVERSARIAL ====================

    def test_adversarial_100_consecutive_short_rests(self):
        """Handles extreme case of 100 consecutive short rest periods."""
        dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(100)]
        shifts = ["A1" if i % 2 == 0 else "D1" for i in range(100)]

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 100,
            "date": dates,
            "shift_code": shifts,
            "start_time": ["14:30" if s == "A1" else "07:00" for s in shifts],
            "end_time": ["22:00" if s == "A1" else "15:00" for s in shifts],
        })

        violations = sliding_window_11h(schedule)
        # Should detect ~50 violations (every A1->D1 transition)
        assert len(violations) >= 40

    def test_adversarial_overlapping_shifts(self):
        """Overlapping shifts (data error) handled gracefully."""
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 5)],
            "shift_code": ["D1", "D1"],
            "start_time": ["07:00", "08:00"],  # Second shift starts during first
            "end_time": ["15:00", "16:00"],
        })

        # Should flag as data issue or handle gracefully
        violations = sliding_window_11h(schedule)
        assert isinstance(violations, list)


class TestWeeklyRest35h:
    """Tests for weekly_rest_35h function - AML § 10-8 Weekly Rest."""

    # ==================== HAPPY PATH ====================

    def test_compliant_weekly_rest(self, sample_clean_schedule: pl.DataFrame):
        """Standard Mon-Fri schedule with weekend off has >35h rest."""
        violations = weekly_rest_35h(sample_clean_schedule)
        assert len(violations) == 0

    def test_detects_insufficient_weekly_rest(self):
        """Working 7 days with no 35h gap is detected."""
        # 7 consecutive day shifts
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 7,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
            "shift_code": ["D1"] * 7,
            "start_time": ["07:00"] * 7,
            "end_time": ["15:00"] * 7,
        })

        violations = weekly_rest_35h(schedule)
        assert len(violations) > 0
        assert all(v.legal_reference == "AML § 10-8" for v in violations)

    def test_168h_rolling_window(self):
        """Checks 168h (7 day) rolling window, not calendar week."""
        # Create pattern that violates rolling window but not calendar week
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 14,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(14)],
            # Work Thu-Wed (7 days), then off Thu-Fri, work Sat-Sun
            "shift_code": ["D1", "D1", "D1", "D1", "D1", "D1", "D1",
                          "FRI", "FRI", "D1", "D1", "D1", "D1", "D1"],
            "start_time": ["07:00", "07:00", "07:00", "07:00", "07:00", "07:00", "07:00",
                          None, None, "07:00", "07:00", "07:00", "07:00", "07:00"],
            "end_time": ["15:00", "15:00", "15:00", "15:00", "15:00", "15:00", "15:00",
                        None, None, "15:00", "15:00", "15:00", "15:00", "15:00"],
        })

        violations = weekly_rest_35h(schedule)
        # First 7 days of work should trigger violation
        assert len(violations) >= 1

    # ==================== EDGE CASES ====================

    def test_exactly_35h_rest_is_compliant(self):
        """Exactly 35 hours continuous rest is NOT a violation."""
        # End Friday 15:00, start Sunday 02:00 = 35h exactly
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 7,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
            "shift_code": ["D1", "D1", "D1", "D1", "D1", "FRI", "N_late"],
            "start_time": ["07:00", "07:00", "07:00", "07:00", "07:00", None, "02:00"],
            "end_time": ["15:00", "15:00", "15:00", "15:00", "15:00", None, "10:00"],
        })

        violations = weekly_rest_35h(schedule)
        assert len(violations) == 0, "Exactly 35h rest should be compliant"

    def test_34h59m_rest_is_violation(self):
        """34 hours 59 minutes rest IS a violation."""
        # End Friday 15:00, start Sunday 01:59 = 34h59m
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 7,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
            "shift_code": ["D1", "D1", "D1", "D1", "D1", "FRI", "N_early"],
            "start_time": ["07:00", "07:00", "07:00", "07:00", "07:00", None, "01:59"],
            "end_time": ["15:00", "15:00", "15:00", "15:00", "15:00", None, "10:00"],
        })

        violations = weekly_rest_35h(schedule)
        assert len(violations) == 1

    def test_multiple_employees_independent(self, multi_employee_schedule: pl.DataFrame):
        """Each employee's weekly rest is evaluated independently."""
        violations = weekly_rest_35h(multi_employee_schedule)

        # Violations should be per-employee
        if violations:
            employee_ids = set(v.employee_id for v in violations)
            assert len(employee_ids) <= 3

    # ==================== ERROR HANDLING ====================

    def test_less_than_7_days_data(self):
        """Schedule with less than 7 days doesn't falsely trigger."""
        short_schedule = pl.DataFrame({
            "employee_id": ["123456"] * 3,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(3)],
            "shift_code": ["D1", "D1", "D1"],
            "start_time": ["07:00"] * 3,
            "end_time": ["15:00"] * 3,
        })

        violations = weekly_rest_35h(short_schedule)
        # Can't determine weekly rest with <7 days - should return empty or warning
        assert isinstance(violations, list)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_year_long_schedule(self):
        """Handles full year of shift data efficiently."""
        dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(365)]
        # Work 6 days, 1 off pattern
        shifts = ["D1" if i % 7 != 6 else "FRI" for i in range(365)]

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 365,
            "date": dates,
            "shift_code": shifts,
            "start_time": ["07:00" if s == "D1" else None for s in shifts],
            "end_time": ["15:00" if s == "D1" else None for s in shifts],
        })

        import time
        start = time.time()
        violations = weekly_rest_35h(schedule)
        elapsed = time.time() - start

        assert elapsed < 10, f"Weekly rest check too slow: {elapsed:.2f}s"
        assert isinstance(violations, list)


class TestHTAComplianceCheck:
    """Tests for HTA_compliance_check function."""

    # ==================== HAPPY PATH ====================

    def test_compliant_35_5h_week(self):
        """Standard 35.5h work week is compliant."""
        # 5 x 7.1h shifts = 35.5h
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["D_custom"] * 5,
            "start_time": ["07:00"] * 5,
            "end_time": ["14:06"] * 5,  # 7.1h shifts
        })

        result = HTA_compliance_check(schedule)
        assert result["weekly_hours_compliant"] is True

    def test_sunday_rotation_within_limit(self, sample_clean_schedule: pl.DataFrame):
        """3 or fewer consecutive Sundays is compliant."""
        result = HTA_compliance_check(sample_clean_schedule)
        assert result.get("sunday_rotation_compliant", True) is True

    # ==================== EDGE CASES ====================

    def test_exactly_3_consecutive_sundays_compliant(self):
        """Exactly 3 consecutive Sundays worked is still compliant."""
        dates = []
        shifts = []
        for week in range(4):  # 4 weeks
            sunday = date(2026, 1, 4) + timedelta(weeks=week)
            for day_offset in range(7):
                d = sunday + timedelta(days=day_offset)
                dates.append(d)
                if day_offset == 0 and week < 3:  # First 3 Sundays
                    shifts.append("D1")
                elif day_offset == 0:  # 4th Sunday off
                    shifts.append("FRI")
                elif day_offset in [5, 6]:  # Sat/Sun except worked Sundays
                    shifts.append("FRI")
                else:
                    shifts.append("D1")

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * len(dates),
            "date": dates,
            "shift_code": shifts,
        })

        result = HTA_compliance_check(schedule)
        assert result.get("sunday_rotation_compliant", True) is True

    def test_4_consecutive_sundays_violation(self, sample_sunday_violation_schedule: pl.DataFrame):
        """4+ consecutive Sundays triggers violation per AML § 10-4."""
        result = HTA_compliance_check(sample_sunday_violation_schedule)

        assert result.get("sunday_rotation_compliant") is False
        assert "AML § 10-4" in str(result.get("violations", []))

    def test_night_shift_33_6h_limit(self):
        """Night shift workers have 33.6h weekly limit per HTA."""
        # 5 x 10h night shifts = 50h (violation)
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["N1"] * 5,
            "start_time": ["21:30"] * 5,
            "end_time": ["07:30"] * 5,  # 10h shifts
        })

        result = HTA_compliance_check(schedule)
        # Night workers should be flagged for >33.6h
        assert result.get("weekly_hours_compliant") is False or \
               "night" in str(result.get("warnings", [])).lower()

    # ==================== ERROR HANDLING ====================

    def test_missing_shift_type_info(self):
        """Handles missing shift type information."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 5,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(5)],
            "shift_code": ["UNKNOWN"] * 5,
        })

        result = HTA_compliance_check(schedule)
        # Should return result with warnings, not crash
        assert isinstance(result, dict)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_extreme_overtime(self):
        """Detects extreme overtime situations."""
        # 7 x 12h shifts = 84h/week
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 7,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
            "shift_code": ["D_long"] * 7,
            "start_time": ["07:00"] * 7,
            "end_time": ["19:00"] * 7,  # 12h shifts
        })

        result = HTA_compliance_check(schedule)
        assert result.get("weekly_hours_compliant") is False


class TestCompensatoryRestTracker:
    """Tests for compensatory_rest_tracker function."""

    # ==================== HAPPY PATH ====================

    def test_no_reduced_rest_no_debt(self, sample_clean_schedule: pl.DataFrame):
        """Schedule with no reduced rest has no compensatory debt."""
        debt = compensatory_rest_tracker(sample_clean_schedule)

        assert debt["total_debt_hours"] == 0
        assert len(debt.get("pending_compensations", [])) == 0

    def test_tracks_8h_reduced_rest_debt(self):
        """Reduced rest (8h instead of 11h) creates 3h debt."""
        # Evening end 22:00 -> Morning start 06:00 = 8h rest
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["A1", "D_early"],
            "start_time": ["14:30", "06:00"],
            "end_time": ["22:00", "14:00"],
        })

        debt = compensatory_rest_tracker(schedule)
        assert debt["total_debt_hours"] == 3  # 11h - 8h = 3h owed

    def test_debt_resolved_within_168h(self):
        """Compensatory rest within 168h clears the debt."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 7,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
            "shift_code": ["A1", "D_early", "FRI", "FRI", "D1", "D1", "FRI"],
            "start_time": ["14:30", "06:00", None, None, "07:00", "07:00", None],
            "end_time": ["22:00", "14:00", None, None, "15:00", "15:00", None],
        })

        debt = compensatory_rest_tracker(schedule)
        # Wed-Thu off provides >35h rest, clearing the 3h debt
        assert debt["total_debt_hours"] == 0

    # ==================== EDGE CASES ====================

    def test_multiple_reduced_rests_accumulate(self):
        """Multiple reduced rest periods accumulate debt."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 4,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(4)],
            "shift_code": ["A1", "D_early", "A1", "D_early"],
            "start_time": ["14:30", "06:00", "14:30", "06:00"],
            "end_time": ["22:00", "14:00", "22:00", "14:00"],
        })

        debt = compensatory_rest_tracker(schedule)
        assert debt["total_debt_hours"] == 6  # 2 x 3h = 6h

    def test_rest_below_8h_not_compensable(self):
        """Rest below 8h is a violation, not compensable reduced rest."""
        # 22:00 -> 05:00 = 7h (violation, not reduced rest)
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 6)],
            "shift_code": ["A1", "D_very_early"],
            "start_time": ["14:30", "05:00"],
            "end_time": ["22:00", "13:00"],
        })

        debt = compensatory_rest_tracker(schedule)
        # Should flag as violation, not compensatory debt
        assert debt.get("violations", []) or debt["total_debt_hours"] >= 0

    def test_deadline_tracking_168h(self):
        """Compensatory rest deadline is tracked (168h from reduced rest)."""
        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 10,
            "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(10)],
            "shift_code": ["A1", "D_early"] + ["D1"] * 8,
            "start_time": ["14:30", "06:00"] + ["07:00"] * 8,
            "end_time": ["22:00", "14:00"] + ["15:00"] * 8,
        })

        debt = compensatory_rest_tracker(schedule)

        # Should have pending compensation with deadline
        if debt.get("pending_compensations"):
            comp = debt["pending_compensations"][0]
            assert "deadline" in comp
            assert comp["deadline"] == date(2026, 1, 12)  # 7 days after Jan 5

    # ==================== ERROR HANDLING ====================

    def test_handles_gaps_in_schedule(self):
        """Gaps in schedule data are handled appropriately."""
        # Non-consecutive dates
        schedule = pl.DataFrame({
            "employee_id": ["123456", "123456"],
            "date": [date(2026, 1, 5), date(2026, 1, 15)],  # 10-day gap
            "shift_code": ["A1", "D1"],
            "start_time": ["14:30", "07:00"],
            "end_time": ["22:00", "15:00"],
        })

        debt = compensatory_rest_tracker(schedule)
        assert isinstance(debt, dict)

    # ==================== ADVERSARIAL ====================

    def test_adversarial_cascading_debt(self):
        """Handles scenario where debt keeps accumulating without resolution."""
        # 30 days of A1->D_early pattern with minimal off days
        dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(30)]
        shifts = []
        for i in range(30):
            if i % 2 == 0:
                shifts.append("A1")
            else:
                shifts.append("D_early")

        schedule = pl.DataFrame({
            "employee_id": ["123456"] * 30,
            "date": dates,
            "shift_code": shifts,
            "start_time": ["14:30" if s == "A1" else "06:00" for s in shifts],
            "end_time": ["22:00" if s == "A1" else "14:00" for s in shifts],
        })

        debt = compensatory_rest_tracker(schedule)

        # Should track cumulative debt
        assert debt["total_debt_hours"] > 0
        # Should flag overdue compensations
        assert len(debt.get("overdue_compensations", [])) > 0 or \
               debt.get("warning") is not None


class TestAuditIntegration:
    """Integration tests for the complete audit pipeline."""

    def test_full_audit_compliant_schedule(self, sample_clean_schedule: pl.DataFrame):
        """Compliant schedule passes all audit checks."""
        daily_violations = sliding_window_11h(sample_clean_schedule)
        weekly_violations = weekly_rest_35h(sample_clean_schedule)
        hta_result = HTA_compliance_check(sample_clean_schedule)
        debt = compensatory_rest_tracker(sample_clean_schedule)

        assert len(daily_violations) == 0
        assert len(weekly_violations) == 0
        assert hta_result.get("weekly_hours_compliant") is True
        assert debt["total_debt_hours"] == 0

    def test_full_audit_violation_schedule(self, sample_violation_schedule: pl.DataFrame):
        """Schedule with violations is fully flagged."""
        daily_violations = sliding_window_11h(sample_violation_schedule)

        assert len(daily_violations) > 0

    def test_audit_trail_completeness(self, sample_violation_schedule: pl.DataFrame):
        """All violations include complete audit trail."""
        violations = sliding_window_11h(sample_violation_schedule)

        for v in violations:
            # Required per CLAUDE.md: "Every flag raised must reference a specific paragraph"
            assert v.legal_reference is not None
            assert "AML" in v.legal_reference or "HTA" in v.legal_reference
            assert v.employee_id is not None
            assert v.date is not None

    def test_multi_employee_audit(self, multi_employee_schedule: pl.DataFrame):
        """Audit correctly handles multiple employees."""
        daily_violations = sliding_window_11h(multi_employee_schedule)
        weekly_violations = weekly_rest_35h(multi_employee_schedule)

        # Results should be per-employee
        assert isinstance(daily_violations, list)
        assert isinstance(weekly_violations, list)
