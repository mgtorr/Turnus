#!/usr/bin/env python3
"""
Chaos Generator for Turnus Risk Audit
======================================

Generates adversarial test data designed to break the Gat-Slayer parser
and stress test the entire compliance pipeline.

Usage:
    python tests/generate_chaos.py [output_dir]

Chaos Levels:
    1. MILD:     Real-world messiness (merged cells, Norwegian chars)
    2. MODERATE: Data quality issues (missing values, duplicates)
    3. EXTREME:  Adversarial inputs (injection, encoding bombs)
    4. MAXIMUM:  Everything combined at scale
"""

import argparse
import random
import string
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Try to import openpyxl for Excel generation
try:
    import openpyxl
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("Warning: openpyxl not installed. Excel generation disabled.")


# Norwegian names and departments for realistic data
NORWEGIAN_FIRST_NAMES = [
    "Ola", "Kari", "Per", "Anne", "Lars", "Ingrid", "Erik", "Liv",
    "Bjørn", "Silje", "Øyvind", "Astrid", "Håkon", "Solveig", "Arne",
    "Berit", "Geir", "Marit", "Torbjørn", "Grete", "Svein", "Randi",
    "Trond", "Hilde", "Morten", "Kristin", "Terje", "Anita", "Odd",
    "Wenche", "Rune", "Tone", "Stein", "Unni", "Ragnar", "Åse",
]

NORWEGIAN_LAST_NAMES = [
    "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen",
    "Nilsen", "Kristiansen", "Jensen", "Karlsen", "Johnsen", "Pettersen",
    "Eriksen", "Berg", "Haugen", "Hagen", "Johannessen", "Andreassen",
    "Jacobsen", "Dahl", "Jørgensen", "Henriksen", "Lund", "Halvorsen",
    "Sørensen", "Jakobsen", "Moen", "Gundersen", "Iversen", "Strand",
    "Ås", "Bø", "Ødegård", "Næss", "Løkken", "Bærum", "Ørvik",
]

DEPARTMENTS = [
    "Akuttmottak", "Kirurgisk avd.", "Medisinsk avd.", "Intensiv",
    "Føde/Barsel", "Psykiatri", "Geriatri", "Onkologi", "Pediatri",
    "Øye-avd.", "ØNH", "Radiologi", "Laboratorium", "Poliklinikk",
    "Hjerteavd.", "Lungeavd.", "Nevrologisk", "Ortopedi", "Dagkirurgi",
]

# Standard shift codes
SHIFT_CODES = ["D1", "D2", "D3", "A1", "A2", "A3", "N1", "N2", "N3", "F", "FRI", "L"]

# Human noise patterns found in real Gat exports
HUMAN_NOISE = [
    "Syk - ringt", "Syk", "SYK!", "syk igjen", "Sykemelding fra dr.",
    "Perm - bryllup", "Permisjon", "FERIE", "Fe", "ferie uke 28",
    "Byttet med Kari", "Bytte!", "byttet vakt", "BYTTE",
    "Kurs Oslo", "Kurs", "Etterutdanning", "Videreutdanning",
    "Avspasering", "Avspassering", "avspass", "AVSP",
    "Møte kl 10", "Personalmøte", "Fagdag",
    "Overtid godkjent", "OT 3t", "Mertid",
    "Vikar for Ola", "Dekker for Per", "Inn for Lars",
    "??? sjekk turnus", "Usikker", "TBD", "N/A", "n.a.",
    "Arbeidsplan endret", "Ny plan kommer", "Se mail",
    "12-20", "07:00-15:00", "Langvakt 07-21",
]

# Header variants from different Gat versions
HEADER_VARIANTS = [
    ["Personnummer", "Navn", "Avdeling", "Uke", "Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"],
    ["Pers.nr", "Ansatt", "Enhet", "Uke nr", "Ma", "Ti", "On", "To", "Fr", "Lø", "Sø"],
    ["Ansattnr", "Fullt navn", "Avd", "U", "1", "2", "3", "4", "5", "6", "7"],
    ["ID", "Name", "Dept", "Week", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ["PNR", "NAVN", "AVD", "UKE", "MAN", "TIR", "ONS", "TOR", "FRE", "LØR", "SØN"],
]


def generate_employee_id(style: str = "random") -> str:
    """Generate employee ID in various formats."""
    if style == "fnr":
        # Norwegian fødselsnummer format (11 digits)
        return "".join(random.choices(string.digits, k=11))
    elif style == "short":
        # Short numeric ID
        return "".join(random.choices(string.digits, k=6))
    elif style == "alphanumeric":
        # Hospital-style ID
        prefix = random.choice(["SYK", "HEL", "OUS", "UNN", "HUS"])
        return f"{prefix}{random.randint(1000, 9999)}"
    else:
        # Random mix
        return random.choice([
            generate_employee_id("fnr"),
            generate_employee_id("short"),
            generate_employee_id("alphanumeric"),
        ])


def generate_norwegian_name() -> str:
    """Generate a realistic Norwegian name."""
    first = random.choice(NORWEGIAN_FIRST_NAMES)
    last = random.choice(NORWEGIAN_LAST_NAMES)
    return f"{first} {last}"


def generate_date_string(d: date, style: str = "iso") -> str:
    """Generate date string in various formats."""
    formats = {
        "iso": "%Y-%m-%d",
        "norwegian": "%d.%m.%Y",
        "slash": "%d/%m/%Y",
        "dash": "%d-%m-%Y",
        "short": "%d.%m.%y",
        "english": "%m/%d/%Y",
        "written": lambda d: d.strftime("%d. %B %Y").replace(
            "January", "januar").replace("February", "februar"),
    }

    if style == "written":
        return formats["written"](d)
    elif style == "random":
        style = random.choice(["iso", "norwegian", "slash", "dash", "short"])

    return d.strftime(formats[style])


def inject_chaos(value: str, chaos_level: int) -> str:
    """Inject chaos into a value based on level."""
    if chaos_level == 0 or random.random() > 0.3:
        return value

    chaos_options = []

    if chaos_level >= 1:  # MILD
        chaos_options.extend([
            lambda v: f" {v}",  # Leading space
            lambda v: f"{v} ",  # Trailing space
            lambda v: f"  {v}  ",  # Extra spaces
            lambda v: v.lower(),  # Lowercase
            lambda v: v.upper(),  # Uppercase
        ])

    if chaos_level >= 2:  # MODERATE
        chaos_options.extend([
            lambda v: "",  # Empty
            lambda v: None,  # Null
            lambda v: v + random.choice(HUMAN_NOISE),  # Human noise
            lambda v: f"{v}?",  # Question mark
            lambda v: f"({v})",  # Parentheses
        ])

    if chaos_level >= 3:  # EXTREME
        chaos_options.extend([
            lambda v: "=1+1",  # Formula injection
            lambda v: "'; DROP TABLE users; --",  # SQL injection
            lambda v: "<script>alert('xss')</script>",  # XSS
            lambda v: "\\x00\\x01\\x02",  # Null bytes
            lambda v: "🔥💀👻" + v,  # Emoji
            lambda v: v + "Ω≈ç√∫",  # Special unicode
            lambda v: "A" * 10000,  # Very long string
        ])

    if chaos_level >= 4:  # MAXIMUM
        chaos_options.extend([
            lambda v: "\n".join([v] * 100),  # Newline bomb
            lambda v: "${" + v + "}",  # Template injection
            lambda v: "{{" + v + "}}",  # Jinja injection
            lambda v: "\r\n" + v,  # CRLF injection
        ])

    chaos_fn = random.choice(chaos_options)
    try:
        result = chaos_fn(value)
        return result if result is not None else value
    except:
        return value


def generate_schedule_row(
    employee_id: str,
    name: str,
    department: str,
    week_dates: List[date],
    chaos_level: int = 0,
    violation_probability: float = 0.1,
) -> List[Any]:
    """Generate a single schedule row with optional chaos and violations."""

    row = [employee_id, name, department]

    # Generate shift pattern
    shift_pattern = []
    for i, d in enumerate(week_dates):
        # Weekend probability of being off
        if d.weekday() >= 5 and random.random() > 0.3:
            shift = random.choice(["FRI", "F", "L"])
        else:
            # Create some violation patterns
            if random.random() < violation_probability:
                # Force a violation pattern (evening -> morning)
                if i > 0 and shift_pattern[-1] in ["A1", "A2", "A3"]:
                    shift = random.choice(["D1", "D2"])
                else:
                    shift = random.choice(["A1", "A2", "A3"])
            else:
                shift = random.choice(SHIFT_CODES)

        # Apply chaos
        if chaos_level > 0 and random.random() < 0.15:
            shift = random.choice(HUMAN_NOISE)

        shift_pattern.append(inject_chaos(shift, chaos_level))

    row.extend(shift_pattern)
    return row


def generate_chaos_excel(
    output_path: Path,
    num_employees: int = 50,
    num_weeks: int = 4,
    chaos_level: int = 2,
    violation_probability: float = 0.2,
) -> Dict[str, Any]:
    """Generate a chaotic Excel file for testing."""

    if not HAS_OPENPYXL:
        raise ImportError("openpyxl required for Excel generation")

    wb = Workbook()
    ws = wb.active
    ws.title = "Turnus"

    # Random header variant
    headers = random.choice(HEADER_VARIANTS)

    # Sometimes add extra header rows (multi-row headers)
    if chaos_level >= 2 and random.random() > 0.5:
        # Add a title row
        ws.append(["Turnusplan " + random.choice(DEPARTMENTS)])
        ws.merge_cells("A1:K1")

    ws.append(headers)

    # Generate employee data
    employees = []
    for _ in range(num_employees):
        emp_id = generate_employee_id()
        name = generate_norwegian_name()
        dept = random.choice(DEPARTMENTS)
        employees.append((emp_id, name, dept))

    # Generate weeks
    stats = {
        "employees": num_employees,
        "weeks": num_weeks,
        "chaos_level": chaos_level,
        "rows_generated": 0,
        "merged_cells": 0,
        "null_values": 0,
        "human_noise_injected": 0,
    }

    start_date = date(2026, 1, 5)  # Monday

    for week_num in range(num_weeks):
        week_start = start_date + timedelta(weeks=week_num)
        week_dates = [week_start + timedelta(days=i) for i in range(7)]

        for emp_id, name, dept in employees:
            row = generate_schedule_row(
                emp_id, name, dept, week_dates, chaos_level, violation_probability
            )

            ws.append(row)
            stats["rows_generated"] += 1

            # Track chaos stats
            for cell in row:
                if cell is None or cell == "":
                    stats["null_values"] += 1
                if cell in HUMAN_NOISE:
                    stats["human_noise_injected"] += 1

        # Sometimes add empty rows between weeks
        if chaos_level >= 1 and random.random() > 0.7:
            ws.append([None] * len(headers))

    # Apply merged cells chaos
    if chaos_level >= 2:
        # Merge some employee ID cells (simulating Gat export)
        for row in range(3, min(20, ws.max_row), 2):
            if random.random() > 0.5:
                try:
                    ws.merge_cells(f"A{row}:A{row+1}")
                    stats["merged_cells"] += 1
                except:
                    pass

    wb.save(output_path)

    return stats


def generate_chaos_csv(
    output_path: Path,
    num_employees: int = 50,
    num_weeks: int = 4,
    chaos_level: int = 2,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """Generate a chaotic CSV file for testing."""

    import csv

    # Random delimiter
    delimiters = [",", ";", "\t"]
    delimiter = random.choice(delimiters) if chaos_level >= 2 else ","

    stats = {
        "employees": num_employees,
        "encoding": encoding,
        "delimiter": repr(delimiter),
        "rows": 0,
    }

    with open(output_path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)

        # Headers
        headers = ["employee_id", "name", "department", "date", "shift_code"]
        writer.writerow(headers)

        start_date = date(2026, 1, 5)

        for _ in range(num_employees):
            emp_id = generate_employee_id()
            name = generate_norwegian_name()
            dept = random.choice(DEPARTMENTS)

            for day in range(num_weeks * 7):
                d = start_date + timedelta(days=day)
                shift = random.choice(SHIFT_CODES)

                row = [
                    inject_chaos(emp_id, chaos_level),
                    inject_chaos(name, chaos_level),
                    inject_chaos(dept, chaos_level),
                    generate_date_string(d, "random" if chaos_level >= 2 else "iso"),
                    inject_chaos(shift, chaos_level),
                ]
                writer.writerow(row)
                stats["rows"] += 1

    return stats


def generate_chaos_json(
    output_path: Path,
    num_employees: int = 50,
    chaos_level: int = 2,
) -> Dict[str, Any]:
    """Generate a chaotic JSON schedule for testing."""

    data = {
        "meta": {
            "generated": datetime.now().isoformat(),
            "source": "Chaos Generator",
            "chaos_level": chaos_level,
        },
        "schedules": []
    }

    start_date = date(2026, 1, 5)

    for _ in range(num_employees):
        emp = {
            "employee_id": generate_employee_id(),
            "name": generate_norwegian_name(),
            "department": random.choice(DEPARTMENTS),
            "shifts": []
        }

        for day in range(28):
            d = start_date + timedelta(days=day)
            shift_code = random.choice(SHIFT_CODES)

            shift = {
                "date": d.isoformat(),
                "code": inject_chaos(shift_code, chaos_level),
            }

            # Add times for non-off shifts
            if shift_code.startswith("D"):
                shift["start"] = "07:00"
                shift["end"] = "15:00"
            elif shift_code.startswith("A"):
                shift["start"] = "14:30"
                shift["end"] = "22:00"
            elif shift_code.startswith("N"):
                shift["start"] = "21:30"
                shift["end"] = "07:30"

            emp["shifts"].append(shift)

        data["schedules"].append(emp)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"employees": num_employees, "chaos_level": chaos_level}


def main():
    parser = argparse.ArgumentParser(
        description="Generate chaotic test data for Turnus Risk Audit"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="data/chaos",
        help="Output directory for generated files"
    )
    parser.add_argument(
        "--employees", "-e",
        type=int,
        default=50,
        help="Number of employees to generate"
    )
    parser.add_argument(
        "--weeks", "-w",
        type=int,
        default=4,
        help="Number of weeks of schedule data"
    )
    parser.add_argument(
        "--chaos-level", "-c",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=2,
        help="Chaos level (0=clean, 4=maximum chaos)"
    )
    parser.add_argument(
        "--violations", "-v",
        type=float,
        default=0.2,
        help="Probability of generating schedule violations (0.0-1.0)"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🌀 Chaos Generator - Level {args.chaos_level}")
    print(f"   Employees: {args.employees}")
    print(f"   Weeks: {args.weeks}")
    print(f"   Violation Probability: {args.violations}")
    print(f"   Output: {output_dir}")
    print()

    all_stats = {}

    # Generate Excel files at different chaos levels
    if HAS_OPENPYXL:
        for level in range(args.chaos_level + 1):
            filename = f"chaos_level_{level}.xlsx"
            filepath = output_dir / filename
            print(f"  Generating {filename}...")
            stats = generate_chaos_excel(
                filepath,
                num_employees=args.employees,
                num_weeks=args.weeks,
                chaos_level=level,
                violation_probability=args.violations,
            )
            all_stats[filename] = stats
            print(f"    ✓ {stats['rows_generated']} rows, {stats['merged_cells']} merged cells")

    # Generate CSV with different encodings
    encodings = ["utf-8", "iso-8859-1", "cp1252"]
    for enc in encodings[:args.chaos_level + 1]:
        filename = f"chaos_{enc.replace('-', '_')}.csv"
        filepath = output_dir / filename
        print(f"  Generating {filename}...")
        stats = generate_chaos_csv(
            filepath,
            num_employees=args.employees,
            num_weeks=args.weeks,
            chaos_level=args.chaos_level,
            encoding=enc,
        )
        all_stats[filename] = stats
        print(f"    ✓ {stats['rows']} rows, encoding: {enc}")

    # Generate JSON
    filename = "chaos_schedule.json"
    filepath = output_dir / filename
    print(f"  Generating {filename}...")
    stats = generate_chaos_json(
        filepath,
        num_employees=args.employees,
        chaos_level=args.chaos_level,
    )
    all_stats[filename] = stats
    print(f"    ✓ {stats['employees']} employees")

    # Save generation manifest
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "chaos_level": args.chaos_level,
        "files": all_stats,
    }
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print()
    print(f"✅ Generated {len(all_stats)} chaos files in {output_dir}")
    print(f"   Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
