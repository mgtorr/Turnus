#!/usr/bin/env python3
"""
Chaos Generator for Turnus Risk Audit

Generates messy Norwegian Excel exports to stress-test the Gat-Slayer parser.
Includes:
- Merged cells (simulated via empty values)
- Norwegian characters (AEOeAa)
- Fuzzy date formats
- Human noise (sick notes, comments)
- Unknown shift codes
- Inconsistent headers
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl


def generate_chaos_data(
    num_employees: int = 5,
    days: int = 14,
    chaos_level: float = 0.3,
) -> pl.DataFrame:
    """
    Generate chaotic shift data simulating real Norwegian Gat exports.

    Args:
        num_employees: Number of employees to generate
        days: Number of days to generate
        chaos_level: Probability of chaos (0.0 to 1.0)
    """
    # Norwegian names with special characters
    norwegian_names = [
        "Kari Nordmann",
        "Ola Haegeland",
        "Bjorn Aasen",
        "Ingrid Oestby",
        "Lars Groenvold",
        "Astrid Bjoernstad",
        "Erik Saetre",
        "Hilde Loeken",
        "Magnus Hoeg",
        "Silje Aas",
    ]

    # Shift codes (including some unknown ones for testing)
    shift_codes = ["D1", "D2", "D3", "A1", "A2", "N1", "N2", "N3", "L", "F"]
    unknown_codes = ["X1", "FLEX", "VAK", "???"]

    # Human noise patterns
    noise_patterns = [
        "Syk - ringt kl 06",
        "Ferie (godkjent)",
        "Byttet med Kari",
        "Permisjon - barn sykt",
        "Kurs i Oslo",
        "OBS: Sjekk timer",
        "Mote kl 14",
    ]

    # Date formats to randomly use
    def random_date_format(dt: datetime) -> str:
        formats = [
            dt.strftime("%d.%m.%Y"),      # 01.01.2026
            dt.strftime("%d.%m.%y"),       # 01.01.26
            dt.strftime("%Y-%m-%d"),       # 2026-01-01
            dt.strftime("%d/%m/%Y"),       # 01/01/2026
        ]
        return random.choice(formats)

    # Header variations
    header_variations = {
        "employee_id": ["Pers.nr", "Ansattnr", "ID", "Personnummer"],
        "employee_name": ["Navn", "Ansatt", "Fullt navn"],
        "date": ["Dato", "Vaktdato", "Dag"],
        "shift_code": ["Vakt", "Vaktkode", "Turnus"],
        "department": ["Avdeling", "Post", "Enhet"],
    }

    # Generate data
    rows = []
    start_date = datetime(2026, 1, 6)  # Start on a Monday

    for emp_idx in range(num_employees):
        emp_id = f"EMP{emp_idx + 1:03d}"
        emp_name = norwegian_names[emp_idx % len(norwegian_names)]
        dept = random.choice(["Medisin 1", "Kirurgi", "Akutten", "Pediatri"])

        # Simulate merged cells: sometimes employee info is empty (forward-fill needed)
        include_emp_info = True

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            # Chaos: randomly add human noise
            if random.random() < chaos_level * 0.3:
                shift = random.choice(noise_patterns)
            # Chaos: use unknown shift code
            elif random.random() < chaos_level * 0.2:
                shift = random.choice(unknown_codes)
            else:
                # Normal shift pattern with some logic
                weekday = current_date.weekday()
                if weekday >= 5:  # Weekend
                    shift = random.choice(["L", "D1", "A1", "N1"])
                else:
                    shift = random.choice(shift_codes)

            # Chaos: fuzzy date format
            if random.random() < chaos_level:
                date_str = random_date_format(current_date)
            else:
                date_str = current_date.strftime("%d.%m.%Y")

            # Chaos: simulate merged cells (empty employee info)
            if random.random() < chaos_level * 0.4 and not include_emp_info:
                row_emp_id = None
                row_emp_name = None
                row_dept = None
            else:
                row_emp_id = emp_id
                row_emp_name = emp_name
                row_dept = dept
                include_emp_info = False  # Next row might be "merged"

            rows.append({
                "Pers.nr": row_emp_id,
                "Navn": row_emp_name,
                "Dato": date_str,
                "Vakt": shift,
                "Avdeling": row_dept,
            })

    # Create intentional violations:
    # Add a sequence that violates 11h rest (N3 followed immediately by D1)
    violation_emp = "EMP001"
    violation_rows = [
        {"Pers.nr": violation_emp, "Navn": "Kari Nordmann", "Dato": "20.01.2026", "Vakt": "N3", "Avdeling": "Medisin 1"},
        {"Pers.nr": violation_emp, "Navn": "Kari Nordmann", "Dato": "21.01.2026", "Vakt": "D1", "Avdeling": "Medisin 1"},
        {"Pers.nr": violation_emp, "Navn": "Kari Nordmann", "Dato": "21.01.2026", "Vakt": "N3", "Avdeling": "Medisin 1"},
        {"Pers.nr": violation_emp, "Navn": "Kari Nordmann", "Dato": "22.01.2026", "Vakt": "D1", "Avdeling": "Medisin 1"},
    ]
    rows.extend(violation_rows)

    # Add consecutive Sunday violations
    sunday_rows = [
        {"Pers.nr": "EMP002", "Navn": "Ola Haegeland", "Dato": "11.01.2026", "Vakt": "D1", "Avdeling": "Kirurgi"},  # Sun
        {"Pers.nr": "EMP002", "Navn": "Ola Haegeland", "Dato": "18.01.2026", "Vakt": "D1", "Avdeling": "Kirurgi"},  # Sun
        {"Pers.nr": "EMP002", "Navn": "Ola Haegeland", "Dato": "25.01.2026", "Vakt": "D1", "Avdeling": "Kirurgi"},  # Sun
        {"Pers.nr": "EMP002", "Navn": "Ola Haegeland", "Dato": "01.02.2026", "Vakt": "D1", "Avdeling": "Kirurgi"},  # Sun (4th!)
    ]
    rows.extend(sunday_rows)

    return pl.DataFrame(rows)


def save_chaos_excel(output_path: Path | str, **kwargs) -> None:
    """Generate and save chaos data to Excel file"""
    df = generate_chaos_data(**kwargs)

    # Write to Excel
    df.write_excel(output_path, worksheet="Vaktliste")
    print(f"Generated chaos Excel: {output_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns}")


if __name__ == "__main__":
    import sys

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/chaos_test.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)

    save_chaos_excel(
        output,
        num_employees=5,
        days=21,
        chaos_level=0.3,
    )
