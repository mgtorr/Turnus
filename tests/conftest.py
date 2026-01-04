"""
Pytest Configuration and Shared Fixtures
Turnus Risk Audit Test Suite
"""

import json
import pytest
import polars as pl
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Generator
import tempfile
import os

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "rules.json"


@pytest.fixture(scope="session")
def rules_config() -> dict:
    """Load the rules.json configuration."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def shift_codes(rules_config: dict) -> dict:
    """Extract shift code mappings from config."""
    return rules_config["shift_codes"]["standard"]


@pytest.fixture(scope="session")
def fatigue_coefficients(rules_config: dict) -> dict:
    """Extract fatigue coefficients from config."""
    return rules_config["fatigue_coefficients"]["multipliers"]


@pytest.fixture
def sample_clean_schedule() -> pl.DataFrame:
    """A properly formatted schedule with no issues."""
    return pl.DataFrame({
        "employee_id": ["123456"] * 7,
        "name": ["Ola Nordmann"] * 7,
        "date": [
            date(2026, 1, 5),  # Monday
            date(2026, 1, 6),  # Tuesday
            date(2026, 1, 7),  # Wednesday
            date(2026, 1, 8),  # Thursday
            date(2026, 1, 9),  # Friday
            date(2026, 1, 10), # Saturday
            date(2026, 1, 11), # Sunday
        ],
        "shift_code": ["D1", "D1", "D1", "D1", "D1", "FRI", "FRI"],
        "start_time": ["07:00", "07:00", "07:00", "07:00", "07:00", None, None],
        "end_time": ["15:00", "15:00", "15:00", "15:00", "15:00", None, None],
    })


@pytest.fixture
def sample_violation_schedule() -> pl.DataFrame:
    """Schedule with clear AML § 10-8 violations."""
    return pl.DataFrame({
        "employee_id": ["123456"] * 7,
        "name": ["Kari Nordmann"] * 7,
        "date": [
            date(2026, 1, 5),  # Monday - evening
            date(2026, 1, 6),  # Tuesday - day (only 9h rest!)
            date(2026, 1, 7),  # Wednesday - evening
            date(2026, 1, 8),  # Thursday - day (only 9h rest!)
            date(2026, 1, 9),  # Friday - evening
            date(2026, 1, 10), # Saturday - day (only 9h rest!)
            date(2026, 1, 11), # Sunday - off
        ],
        "shift_code": ["A1", "D1", "A1", "D1", "A1", "D1", "FRI"],
        "start_time": ["14:30", "07:00", "14:30", "07:00", "14:30", "07:00", None],
        "end_time": ["22:00", "15:00", "22:00", "15:00", "22:00", "15:00", None],
    })


@pytest.fixture
def sample_night_rotation_schedule() -> pl.DataFrame:
    """Schedule with consecutive night shifts and backward rotation."""
    return pl.DataFrame({
        "employee_id": ["789012"] * 10,
        "name": ["Per Hansen"] * 10,
        "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(10)],
        "shift_code": ["N1", "N1", "N1", "N1", "FRI", "FRI", "D1", "D1", "A1", "A1"],
        "start_time": ["21:30", "21:30", "21:30", "21:30", None, None, "07:00", "07:00", "14:30", "14:30"],
        "end_time": ["07:30", "07:30", "07:30", "07:30", None, None, "15:00", "15:00", "22:00", "22:00"],
    })


@pytest.fixture
def sample_sunday_violation_schedule() -> pl.DataFrame:
    """Schedule with more than 3 consecutive Sundays worked."""
    # Build 5 weeks of schedule
    dates = []
    shifts = []
    for week in range(5):
        base = date(2026, 1, 4) + timedelta(weeks=week)  # Sunday
        for day_offset in range(7):
            d = base + timedelta(days=day_offset)
            dates.append(d)
            if d.weekday() == 6:  # Sunday
                shifts.append("D1")  # Working Sunday
            elif d.weekday() in [5]:  # Saturday
                shifts.append("FRI")
            else:
                shifts.append("D1")

    return pl.DataFrame({
        "employee_id": ["456789"] * len(dates),
        "name": ["Anne Olsen"] * len(dates),
        "date": dates,
        "shift_code": shifts,
    })


@pytest.fixture
def messy_excel_data() -> dict:
    """Simulates messy Norwegian Excel export with common issues."""
    return {
        "merged_cells": True,
        "data": [
            # Header row with inconsistent naming
            ["Pers.nr", "Navn", "Avdeling", "Uke 1", None, None, None, None, None, None],
            [None, None, None, "Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"],
            # Employee 1 - merged cell in first column
            ["12345678901", "Ørjan Ås", "Avd. Øst", "D1", "D1", "D1", "D1", "D1", "F", "F"],
            [None, None, None, None, None, None, None, None, None, None],  # Empty row
            # Employee 2 - Norwegian special chars
            ["98765432101", "Bjørn Bærum", "Sør-Øst", "A1", "A1", "A1", "F", "F", "N1", "N1"],
            # Employee 3 - human noise in cells
            ["11122233344", "Lars Berg", "Nord", "D1", "Syk - ringt", "D1", "D1", "D1", "F", "F"],
        ]
    }


@pytest.fixture
def fuzzy_header_variants() -> list:
    """Different header naming conventions found in real Gat exports."""
    return [
        # Variant 1: Full Norwegian
        ["Personnummer", "Fullt navn", "Avdeling", "Dato", "Vakttype"],
        # Variant 2: Abbreviated
        ["Pers.nr", "Navn", "Avd", "Dato", "Vakt"],
        # Variant 3: English mix
        ["Employee ID", "Name", "Department", "Date", "Shift"],
        # Variant 4: Very abbreviated
        ["PNr", "N", "A", "D", "V"],
        # Variant 5: With typos
        ["Persnr", "Navnm", "Avdlng", "Datao", "Vaktkode"],
        # Variant 6: Ansattnr variant
        ["Ansattnr", "Ansatt", "Enhet", "Tidspunkt", "Turnus"],
    ]


@pytest.fixture
def temp_excel_file(messy_excel_data: dict) -> Generator[Path, None, None]:
    """Create a temporary Excel file with messy data."""
    try:
        import openpyxl
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Turnus"

        for row_idx, row_data in enumerate(messy_excel_data["data"], start=1):
            for col_idx, value in enumerate(row_data, start=1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Simulate merged cells
        ws.merge_cells("A3:A4")  # Employee ID merged
        ws.merge_cells("B3:B4")  # Name merged
        ws.merge_cells("C3:C4")  # Department merged

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            wb.save(f.name)
            yield Path(f.name)

    except ImportError:
        pytest.skip("openpyxl not installed")
    finally:
        if 'f' in locals():
            os.unlink(f.name)


@pytest.fixture
def empty_schedule() -> pl.DataFrame:
    """Empty DataFrame for edge case testing."""
    return pl.DataFrame({
        "employee_id": [],
        "name": [],
        "date": [],
        "shift_code": [],
    })


@pytest.fixture
def single_shift_schedule() -> pl.DataFrame:
    """Single shift - minimum viable schedule."""
    return pl.DataFrame({
        "employee_id": ["123456"],
        "name": ["Test Person"],
        "date": [date(2026, 1, 5)],
        "shift_code": ["D1"],
    })


@pytest.fixture
def boundary_11h_schedule() -> pl.DataFrame:
    """Schedule with exactly 11h rest (boundary case)."""
    return pl.DataFrame({
        "employee_id": ["123456"] * 2,
        "name": ["Boundary Test"] * 2,
        "date": [date(2026, 1, 5), date(2026, 1, 6)],
        "shift_code": ["A2", "D3"],  # 22:30 -> 08:00 = exactly 9.5h rest (VIOLATION)
    })


@pytest.fixture
def exactly_35h_rest_schedule() -> pl.DataFrame:
    """Schedule with exactly 35h weekly rest (boundary case)."""
    # Friday end 15:00, Sunday start 02:00 = 35h exactly
    return pl.DataFrame({
        "employee_id": ["123456"] * 7,
        "name": ["Weekly Boundary"] * 7,
        "date": [date(2026, 1, 5) + timedelta(days=i) for i in range(7)],
        "shift_code": ["D1", "D1", "D1", "D1", "D1", "FRI", "N1"],
    })


@pytest.fixture
def multi_employee_schedule() -> pl.DataFrame:
    """Schedule with multiple employees for aggregation testing."""
    employees = [
        ("100001", "Employee A"),
        ("100002", "Employee B"),
        ("100003", "Employee C"),
    ]

    data = {
        "employee_id": [],
        "name": [],
        "date": [],
        "shift_code": [],
    }

    for emp_id, name in employees:
        for i in range(14):  # 2 weeks
            data["employee_id"].append(emp_id)
            data["name"].append(name)
            data["date"].append(date(2026, 1, 5) + timedelta(days=i))
            # Varying shift patterns
            if i % 7 < 5:
                data["shift_code"].append("D1")
            else:
                data["shift_code"].append("FRI")

    return pl.DataFrame(data)
