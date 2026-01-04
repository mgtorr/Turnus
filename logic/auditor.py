"""
The Auditor: Legal Logic Engine for Turnus Risk Audit

Evaluates shift data against Norwegian labor rules:
- AML ss 10-8: Daily and weekly rest requirements
- HTA: Specific health sector agreements
- Compensatory rest tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class AuditRules:
    """Rules loaded from rules.json"""
    daily_rest_hours: float
    weekly_rest_hours: float
    weekly_window_hours: float
    reduced_rest_minimum: float
    max_consecutive_sundays: int
    fatigue_coefficients: dict[str, float]

    @classmethod
    def from_json(cls, path: Path | str) -> AuditRules:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        aml = data.get("aml", {}).get("section_10_8", {})
        fatigue = data.get("fatigue_coefficients", {})

        return cls(
            daily_rest_hours=aml.get("daily_rest", {}).get("threshold_hours", 11),
            weekly_rest_hours=aml.get("weekly_rest", {}).get("threshold_hours", 35),
            weekly_window_hours=aml.get("weekly_rest", {}).get("window_hours", 168),
            reduced_rest_minimum=aml.get("reduced_rest", {}).get("minimum_hours", 8),
            max_consecutive_sundays=aml.get("sunday_rule", {}).get("max_consecutive", 3),
            fatigue_coefficients={
                "short_rest": fatigue.get("short_rest", {}).get("multiplier", 1.94),
                "backward_rotation": fatigue.get("backward_rotation", {}).get("multiplier", 0.49),
                "successive_nights": fatigue.get("successive_nights", {}).get("multiplier", 0.68),
                "night_shift_base": fatigue.get("night_shift_base", {}).get("multiplier", 0.22),
            },
        )


@dataclass
class Violation:
    """A single compliance violation"""
    employee_id: str
    employee_name: str | None
    violation_type: str
    severity: str  # "critical", "warning", "info"
    date: datetime | None
    details: str
    legal_reference: str
    rest_hours: float | None = None
    required_hours: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "date": self.date.isoformat() if self.date else None,
            "details": self.details,
            "legal_reference": self.legal_reference,
            "rest_hours": self.rest_hours,
            "required_hours": self.required_hours,
        }


@dataclass
class AuditResult:
    """Complete audit result for a dataset"""
    violations: list[Violation] = field(default_factory=list)
    employees_audited: int = 0
    shifts_analyzed: int = 0
    fatigue_scores: dict[str, float] = field(default_factory=dict)
    compensatory_rest_debt: dict[str, float] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "TURNUS RISK AUDIT - COMPLIANCE REPORT",
            "=" * 60,
            f"Employees audited: {self.employees_audited}",
            f"Shifts analyzed: {self.shifts_analyzed}",
            "",
            "--- VIOLATION SUMMARY ---",
            f"CRITICAL violations: {self.critical_count}",
            f"WARNING violations: {self.warning_count}",
            "",
        ]

        if self.violations:
            lines.append("--- TOP VIOLATIONS ---")
            # Group by type
            by_type: dict[str, list[Violation]] = {}
            for v in self.violations:
                by_type.setdefault(v.violation_type, []).append(v)

            for vtype, vlist in sorted(by_type.items(), key=lambda x: -len(x[1])):
                lines.append(f"\n{vtype} ({len(vlist)} occurrences):")
                lines.append(f"  Legal basis: {vlist[0].legal_reference}")
                # Show first few
                for v in vlist[:3]:
                    emp = v.employee_name or v.employee_id
                    date_str = v.date.strftime("%d.%m.%Y") if v.date else "N/A"
                    lines.append(f"  - {emp} on {date_str}: {v.details}")
                if len(vlist) > 3:
                    lines.append(f"  ... and {len(vlist) - 3} more")

        if self.fatigue_scores:
            lines.append("\n--- FATIGUE RISK SCORES ---")
            sorted_scores = sorted(self.fatigue_scores.items(), key=lambda x: -x[1])
            for emp_id, score in sorted_scores[:5]:
                risk_level = "HIGH" if score > 5 else "MEDIUM" if score > 2 else "LOW"
                lines.append(f"  {emp_id}: {score:.2f} ({risk_level})")

        if self.compensatory_rest_debt:
            lines.append("\n--- COMPENSATORY REST DEBT (AML ss 10-8(3)) ---")
            for emp_id, hours in sorted(self.compensatory_rest_debt.items(), key=lambda x: -x[1]):
                if hours > 0:
                    lines.append(f"  {emp_id}: {hours:.1f} hours owed")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


class Auditor:
    """
    The Auditor: Evaluates shift data against Norwegian labor law.
    """

    def __init__(self, rules: AuditRules):
        self.rules = rules

    def _parse_time_str(self, time_str: str | None) -> time | None:
        """Parse time string to time object"""
        if not time_str:
            return None
        try:
            parts = time_str.split(":")
            return time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return None

    def _get_shift_datetime(self, date_val: Any, time_val: str | None, is_night_end: bool = False) -> datetime | None:
        """Combine date and time into datetime"""
        if date_val is None or time_val is None:
            return None

        t = self._parse_time_str(time_val)
        if t is None:
            return None

        # Handle various date types
        if isinstance(date_val, datetime):
            d = date_val.date()
        elif isinstance(date_val, str):
            try:
                d = datetime.fromisoformat(date_val).date()
            except ValueError:
                return None
        else:
            return None

        dt = datetime.combine(d, t)

        # Night shifts ending in the morning are next day
        if is_night_end and t.hour < 12:
            dt += timedelta(days=1)

        return dt

    def sliding_window_11h(self, shifts: pl.DataFrame, employee_id: str) -> list[Violation]:
        """
        Identifies Daily Rest violations within any 24h period.
        AML ss 10-8(1): Minimum 11 hours continuous rest.
        """
        violations = []

        # Filter to this employee's working shifts
        emp_shifts = shifts.filter(
            (pl.col("employee_id") == employee_id) &
            (pl.col("shift_type").is_in(["day", "evening", "night"]))
        ).sort("date")

        if len(emp_shifts) < 2:
            return violations

        rows = list(emp_shifts.iter_rows(named=True))
        employee_name = rows[0].get("employee_name") if rows else None

        for i in range(len(rows) - 1):
            current = rows[i]
            next_shift = rows[i + 1]

            # Calculate end of current shift
            is_night = current.get("shift_type") == "night"
            current_end = self._get_shift_datetime(
                current.get("date"),
                current.get("end_time"),
                is_night_end=is_night
            )

            # Calculate start of next shift
            next_start = self._get_shift_datetime(
                next_shift.get("date"),
                next_shift.get("start_time"),
                is_night_end=False
            )

            if current_end is None or next_start is None:
                continue

            # Calculate rest period
            rest_hours = (next_start - current_end).total_seconds() / 3600

            if rest_hours < self.rules.daily_rest_hours:
                severity = "critical" if rest_hours < self.rules.reduced_rest_minimum else "warning"

                violations.append(Violation(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    violation_type="DAILY_REST_VIOLATION",
                    severity=severity,
                    date=next_shift.get("date") if isinstance(next_shift.get("date"), datetime) else None,
                    details=f"Only {rest_hours:.1f}h rest between shifts (minimum {self.rules.daily_rest_hours}h)",
                    legal_reference="AML ss 10-8 (1)",
                    rest_hours=rest_hours,
                    required_hours=self.rules.daily_rest_hours,
                ))

        return violations

    def weekly_rest_35h(self, shifts: pl.DataFrame, employee_id: str) -> list[Violation]:
        """
        Scans 168h windows for continuous 35h rest gap.
        AML ss 10-8(2): 35 hours continuous rest per 7 days.
        """
        violations = []

        emp_shifts = shifts.filter(
            (pl.col("employee_id") == employee_id) &
            (pl.col("shift_type").is_in(["day", "evening", "night"]))
        ).sort("date")

        if len(emp_shifts) == 0:
            return violations

        rows = list(emp_shifts.iter_rows(named=True))
        employee_name = rows[0].get("employee_name") if rows else None

        # Build list of (start, end) datetimes
        shift_periods = []
        for row in rows:
            is_night = row.get("shift_type") == "night"
            start = self._get_shift_datetime(row.get("date"), row.get("start_time"))
            end = self._get_shift_datetime(row.get("date"), row.get("end_time"), is_night_end=is_night)
            if start and end:
                shift_periods.append((start, end, row.get("date")))

        if len(shift_periods) < 2:
            return violations

        # Sort by start time
        shift_periods.sort(key=lambda x: x[0])

        # Check each 7-day window
        window_hours = self.rules.weekly_window_hours
        required_rest = self.rules.weekly_rest_hours

        first_date = shift_periods[0][0]
        last_date = shift_periods[-1][1]

        current_window_start = first_date
        while current_window_start < last_date:
            window_end = current_window_start + timedelta(hours=window_hours)

            # Get shifts in this window
            window_shifts = [
                (s, e) for s, e, _ in shift_periods
                if s < window_end and e > current_window_start
            ]

            if len(window_shifts) >= 2:
                # Sort and find max rest gap
                window_shifts.sort(key=lambda x: x[0])
                max_gap = 0
                for i in range(len(window_shifts) - 1):
                    gap = (window_shifts[i + 1][0] - window_shifts[i][1]).total_seconds() / 3600
                    max_gap = max(max_gap, gap)

                if max_gap < required_rest:
                    violations.append(Violation(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        violation_type="WEEKLY_REST_VIOLATION",
                        severity="critical",
                        date=current_window_start,
                        details=f"No {required_rest}h rest period in 7-day window (max gap: {max_gap:.1f}h)",
                        legal_reference="AML ss 10-8 (2)",
                        rest_hours=max_gap,
                        required_hours=required_rest,
                    ))

            current_window_start += timedelta(days=1)

        return violations

    def sunday_rule_check(self, shifts: pl.DataFrame, employee_id: str) -> list[Violation]:
        """
        Check for max consecutive Sundays worked.
        AML ss 10-8(4): Max 3 consecutive Sundays.
        """
        violations = []

        emp_shifts = shifts.filter(
            (pl.col("employee_id") == employee_id) &
            (pl.col("shift_type").is_in(["day", "evening", "night"]))
        ).sort("date")

        if len(emp_shifts) == 0:
            return violations

        rows = list(emp_shifts.iter_rows(named=True))
        employee_name = rows[0].get("employee_name") if rows else None

        # Find Sundays worked
        sundays_worked = []
        for row in rows:
            date_val = row.get("date")
            if isinstance(date_val, datetime) and date_val.weekday() == 6:
                sundays_worked.append(date_val)

        if len(sundays_worked) < self.rules.max_consecutive_sundays + 1:
            return violations

        # Check for consecutive Sundays
        consecutive = 1
        for i in range(1, len(sundays_worked)):
            diff = (sundays_worked[i] - sundays_worked[i - 1]).days
            if diff == 7:
                consecutive += 1
                if consecutive > self.rules.max_consecutive_sundays:
                    violations.append(Violation(
                        employee_id=employee_id,
                        employee_name=employee_name,
                        violation_type="SUNDAY_RULE_VIOLATION",
                        severity="warning",
                        date=sundays_worked[i],
                        details=f"Worked {consecutive} consecutive Sundays (max {self.rules.max_consecutive_sundays})",
                        legal_reference="AML ss 10-8 (4)",
                    ))
            else:
                consecutive = 1

        return violations

    def calculate_fatigue_score(self, shifts: pl.DataFrame, employee_id: str) -> float:
        """
        Calculate fatigue risk score using research-backed coefficients.
        Higher score = higher burnout risk.
        """
        score = 0.0

        emp_shifts = shifts.filter(
            (pl.col("employee_id") == employee_id) &
            (pl.col("shift_type").is_in(["day", "evening", "night"]))
        ).sort("date")

        if len(emp_shifts) == 0:
            return score

        rows = list(emp_shifts.iter_rows(named=True))
        prev_type = None
        night_streak = 0

        for i, row in enumerate(rows):
            shift_type = row.get("shift_type")

            # Night shift base risk
            if shift_type == "night":
                score += self.rules.fatigue_coefficients["night_shift_base"]
                night_streak += 1
                if night_streak > 1:
                    score += self.rules.fatigue_coefficients["successive_nights"]
            else:
                night_streak = 0

            # Backward rotation detection
            if prev_type and shift_type:
                if (prev_type == "night" and shift_type in ["evening", "day"]) or \
                   (prev_type == "evening" and shift_type == "day"):
                    score += self.rules.fatigue_coefficients["backward_rotation"]

            # Short rest penalty (from daily violations)
            if i > 0:
                prev = rows[i - 1]
                is_night = prev.get("shift_type") == "night"
                prev_end = self._get_shift_datetime(prev.get("date"), prev.get("end_time"), is_night_end=is_night)
                curr_start = self._get_shift_datetime(row.get("date"), row.get("start_time"))
                if prev_end and curr_start:
                    rest_hours = (curr_start - prev_end).total_seconds() / 3600
                    if 0 < rest_hours < self.rules.daily_rest_hours:
                        score += self.rules.fatigue_coefficients["short_rest"]

            prev_type = shift_type

        return score

    def compensatory_rest_tracker(self, shifts: pl.DataFrame, employee_id: str) -> float:
        """
        Track rest debt from reduced rest periods.
        Returns total hours of compensatory rest owed.
        """
        debt = 0.0

        emp_shifts = shifts.filter(
            (pl.col("employee_id") == employee_id) &
            (pl.col("shift_type").is_in(["day", "evening", "night"]))
        ).sort("date")

        if len(emp_shifts) < 2:
            return debt

        rows = list(emp_shifts.iter_rows(named=True))

        for i in range(len(rows) - 1):
            current = rows[i]
            next_shift = rows[i + 1]

            is_night = current.get("shift_type") == "night"
            current_end = self._get_shift_datetime(current.get("date"), current.get("end_time"), is_night_end=is_night)
            next_start = self._get_shift_datetime(next_shift.get("date"), next_shift.get("start_time"))

            if current_end and next_start:
                rest_hours = (next_start - current_end).total_seconds() / 3600
                # If rest is between minimum (8h) and required (11h), compensatory rest is owed
                if self.rules.reduced_rest_minimum <= rest_hours < self.rules.daily_rest_hours:
                    debt += self.rules.daily_rest_hours - rest_hours

        return debt

    def audit(self, shifts: pl.DataFrame) -> AuditResult:
        """
        Run full audit on shift data.
        """
        result = AuditResult()

        # Get unique employees
        if "employee_id" not in shifts.columns:
            return result

        employees = shifts.select("employee_id").unique().to_series().to_list()
        employees = [e for e in employees if e is not None]

        result.employees_audited = len(employees)
        result.shifts_analyzed = len(shifts)

        for emp_id in employees:
            # Run all checks
            result.violations.extend(self.sliding_window_11h(shifts, emp_id))
            result.violations.extend(self.weekly_rest_35h(shifts, emp_id))
            result.violations.extend(self.sunday_rule_check(shifts, emp_id))

            # Calculate fatigue score
            fatigue = self.calculate_fatigue_score(shifts, emp_id)
            if fatigue > 0:
                result.fatigue_scores[emp_id] = fatigue

            # Track compensatory rest
            debt = self.compensatory_rest_tracker(shifts, emp_id)
            if debt > 0:
                result.compensatory_rest_debt[emp_id] = debt

        return result


def load_auditor(config_path: Path | str | None = None) -> Auditor:
    """Factory function to create a configured Auditor instance"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "rules.json"
    rules = AuditRules.from_json(config_path)
    return Auditor(rules)
