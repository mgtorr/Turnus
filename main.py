#!/usr/bin/env python3
"""
Turnus Risk Audit - CLI Entry Point

A sovereign compliance and burnout prediction engine for Norwegian health leaders.
Transforms messy Gat/Excel exports into AML ss 10-8 compliance reports.

Usage:
    python main.py <excel_file>
    python main.py --help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def print_banner() -> None:
    """Print the Turnus banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║              TURNUS RISK AUDIT (2026)                      ║
    ║    Sovereign Compliance Engine for Norwegian Healthcare    ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main() -> int:
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Turnus Risk Audit - AML ss 10-8 Compliance Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py data/vaktliste.xlsx
    python main.py --verbose data/shifts.xlsx
    python main.py --json data/export.xlsx > report.json

Legal References:
    AML ss 10-8(1): Daily rest - minimum 11 hours
    AML ss 10-8(2): Weekly rest - 35 hours in 168h window
    AML ss 10-8(3): Reduced rest - minimum 8h with compensation
    AML ss 10-8(4): Sunday rule - max 3 consecutive
        """,
    )

    parser.add_argument(
        "excel_file",
        type=Path,
        help="Path to the Gat/Excel export file to analyze",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output including parsing details",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of text",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to custom rules.json configuration",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.excel_file.exists():
        print(f"Error: File not found: {args.excel_file}", file=sys.stderr)
        return 1

    if not args.json:
        print_banner()

    # Import here to avoid slow startup for --help
    from logic.parser import load_parser
    from logic.auditor import load_auditor

    # Determine config path
    config_path = args.config
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "rules.json"

    if not config_path.exists():
        print(f"Error: Configuration not found: {config_path}", file=sys.stderr)
        return 1

    # Phase 1: Parse the Excel file
    if not args.json:
        print(f"\n[1/3] Parsing: {args.excel_file.name}")

    gat_slayer = load_parser(config_path)
    parse_result = gat_slayer.parse_excel(args.excel_file)

    if args.verbose and not args.json:
        print(f"      Raw rows: {parse_result.raw_row_count}")
        print(f"      Clean rows: {parse_result.clean_row_count}")
        print()
        print(parse_result.validation.summary())

    if parse_result.validation.unmapped_codes:
        if not args.json:
            print("\n[!] MAPPING_REQUIRED: Unknown shift codes detected")
            print(f"    Codes: {sorted(parse_result.validation.unmapped_codes)}")
            print("    Add these to config/rules.json -> shift_codes")

    # Phase 2: Audit for violations
    if not args.json:
        print(f"\n[2/3] Auditing against AML ss 10-8...")

    auditor = load_auditor(config_path)
    audit_result = auditor.audit(parse_result.shifts)

    # Phase 3: Output results
    if not args.json:
        print(f"\n[3/3] Generating Risk Summary...\n")

    if args.json:
        import json
        output = {
            "parse": {
                "raw_rows": parse_result.raw_row_count,
                "clean_rows": parse_result.clean_row_count,
                "unmapped_codes": list(parse_result.validation.unmapped_codes),
                "noise_rows": len(parse_result.validation.noise_rows),
            },
            "audit": {
                "employees_audited": audit_result.employees_audited,
                "shifts_analyzed": audit_result.shifts_analyzed,
                "critical_violations": audit_result.critical_count,
                "warning_violations": audit_result.warning_count,
                "violations": [v.to_dict() for v in audit_result.violations],
                "fatigue_scores": audit_result.fatigue_scores,
                "compensatory_rest_debt": audit_result.compensatory_rest_debt,
            },
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        print(audit_result.summary())

        # Final status
        if audit_result.critical_count > 0:
            print("\n[!!] CRITICAL: Immediate action required - AML violations detected")
            return 2
        elif audit_result.warning_count > 0:
            print("\n[!] WARNING: Review recommended - potential compliance issues")
            return 1
        else:
            print("\n[OK] No violations detected in analyzed data")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
