"""
The Gat-Slayer: Data Ingestion Module for Turnus Risk Audit

Handles messy Norwegian Gat/Excel exports with:
- Merged cells (forward-fill)
- Norwegian characters (AEOeAa)
- Fuzzy header matching
- Shift code mapping
- Human noise detection
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class ParserConfig:
    """Configuration loaded from rules.json"""
    shift_codes: dict[str, dict[str, Any]]
    header_aliases: dict[str, list[str]]
    noise_patterns: list[str]

    @classmethod
    def from_json(cls, path: Path | str) -> ParserConfig:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            shift_codes=data.get("shift_codes", {}),
            header_aliases=data.get("header_aliases", {}),
            noise_patterns=data.get("noise_patterns", []),
        )


@dataclass
class ValidationReport:
    """Report of data validation issues"""
    noise_rows: list[dict[str, Any]] = field(default_factory=list)
    unmapped_codes: set[str] = field(default_factory=set)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.noise_rows or self.unmapped_codes or self.parse_errors)

    def summary(self) -> str:
        lines = ["=== Data Validation Report ==="]
        if self.noise_rows:
            lines.append(f"Rows with human noise: {len(self.noise_rows)}")
            for row in self.noise_rows[:5]:
                lines.append(f"  - Row {row.get('row_index', '?')}: {row.get('noise_type', 'unknown')}")
            if len(self.noise_rows) > 5:
                lines.append(f"  ... and {len(self.noise_rows) - 5} more")
        if self.unmapped_codes:
            lines.append(f"Unmapped shift codes (MAPPING_REQUIRED): {sorted(self.unmapped_codes)}")
        if self.parse_errors:
            lines.append(f"Parse errors: {len(self.parse_errors)}")
            for err in self.parse_errors[:3]:
                lines.append(f"  - {err}")
        if not self.has_issues:
            lines.append("No issues detected.")
        return "\n".join(lines)


@dataclass
class ParseResult:
    """Result of parsing a Gat export"""
    shifts: pl.DataFrame
    validation: ValidationReport
    raw_row_count: int
    clean_row_count: int


class GatSlayer:
    """
    The Gat-Slayer: Sanitizes and maps inconsistent Norwegian Excel/Gat exports.
    """

    # Standard schema columns
    SCHEMA = [
        "employee_id",
        "employee_name",
        "date",
        "shift_code",
        "start_time",
        "end_time",
        "shift_type",
        "department",
        "has_noise",
        "noise_detail",
    ]

    def __init__(self, config: ParserConfig):
        self.config = config
        self._build_header_lookup()

    def _build_header_lookup(self) -> None:
        """Build reverse lookup: alias -> canonical name"""
        self.header_lookup: dict[str, str] = {}
        for canonical, aliases in self.config.header_aliases.items():
            for alias in aliases:
                self.header_lookup[alias.lower().strip()] = canonical

    def fuzzy_header_match(self, header: str) -> str | None:
        """
        Map a column header to canonical schema name.
        Uses exact match first, then fuzzy matching.
        """
        normalized = header.lower().strip()

        # Exact match
        if normalized in self.header_lookup:
            return self.header_lookup[normalized]

        # Fuzzy match: check if any alias is contained in the header
        for alias, canonical in self.header_lookup.items():
            if alias in normalized or normalized in alias:
                return canonical

        return None

    def _detect_noise(self, value: Any) -> tuple[bool, str | None]:
        """Detect human noise in cell values"""
        if value is None:
            return False, None

        str_val = str(value).strip()
        for pattern in self.config.noise_patterns:
            if pattern.lower() in str_val.lower():
                return True, pattern
        return False, None

    def vakt_code_mapper(self, code: str | None) -> tuple[time | None, time | None, str | None, bool]:
        """
        Translate shift code to start_time, end_time, shift_type.
        Returns: (start_time, end_time, shift_type, is_unmapped)
        """
        if code is None:
            return None, None, None, False

        code_clean = str(code).strip().upper()

        # Handle combined codes like "D1/A2"
        if "/" in code_clean:
            code_clean = code_clean.split("/")[0]

        if code_clean in self.config.shift_codes:
            shift_info = self.config.shift_codes[code_clean]
            start_str = shift_info.get("start")
            end_str = shift_info.get("end")
            shift_type = shift_info.get("type")

            start_time = self._parse_time(start_str) if start_str else None
            end_time = self._parse_time(end_str) if end_str else None

            return start_time, end_time, shift_type, False

        # Unknown code - trigger MAPPING_REQUIRED
        return None, None, None, True

    def _parse_time(self, time_str: str) -> time | None:
        """Parse time string in various formats"""
        if not time_str:
            return None
        try:
            # Handle HH:MM format
            if ":" in time_str:
                parts = time_str.split(":")
                return time(int(parts[0]), int(parts[1]))
            # Handle HHMM format
            if len(time_str) == 4 and time_str.isdigit():
                return time(int(time_str[:2]), int(time_str[2:]))
        except (ValueError, IndexError):
            pass
        return None

    def _parse_date(self, value: Any) -> datetime | None:
        """Parse fuzzy date formats common in Norwegian exports"""
        if value is None:
            return None

        # Already a datetime
        if isinstance(value, datetime):
            return value

        str_val = str(value).strip()
        if not str_val:
            return None

        # Common Norwegian date formats
        formats = [
            "%d.%m.%Y",      # 01.01.2026
            "%d.%m.%y",      # 01.01.26
            "%Y-%m-%d",      # 2026-01-01
            "%d/%m/%Y",      # 01/01/2026
            "%d-%m-%Y",      # 01-01-2026
            "%d. %B %Y",     # 01. januar 2026
            "%d %b %Y",      # 01 jan 2026
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str_val, fmt)
            except ValueError:
                continue

        # Handle Excel serial date numbers
        try:
            serial = float(str_val)
            if 40000 < serial < 50000:  # Reasonable Excel date range
                return datetime(1899, 12, 30) + timedelta(days=serial)
        except ValueError:
            pass

        return None

    def clean_gat_export(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Clean raw Gat export:
        - Forward-fill merged cells
        - Normalize Norwegian characters
        - Strip whitespace
        """
        # Forward-fill null values (handles merged cells)
        fill_cols = ["employee_id", "employee_name", "department"]
        available_fill_cols = [c for c in fill_cols if c in df.columns]

        if available_fill_cols:
            df = df.with_columns([
                pl.col(c).forward_fill() for c in available_fill_cols
            ])

        # Strip whitespace from string columns
        string_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
        if string_cols:
            df = df.with_columns([
                pl.col(c).str.strip_chars() for c in string_cols
            ])

        return df

    def parse_excel(self, path: Path | str) -> ParseResult:
        """
        Main entry point: Parse an Excel file and return structured shift data.
        """
        validation = ValidationReport()

        # Read Excel with openpyxl engine for better merged cell handling
        try:
            raw_df = pl.read_excel(path, engine="calamine")
        except Exception as e:
            validation.parse_errors.append(f"Failed to read Excel file: {e}")
            return ParseResult(
                shifts=pl.DataFrame(),
                validation=validation,
                raw_row_count=0,
                clean_row_count=0,
            )

        raw_row_count = len(raw_df)

        # Map headers to canonical names
        column_mapping = {}
        for col in raw_df.columns:
            canonical = self.fuzzy_header_match(col)
            if canonical:
                column_mapping[col] = canonical

        # Rename columns
        if column_mapping:
            raw_df = raw_df.rename(column_mapping)

        # Clean the data
        raw_df = self.clean_gat_export(raw_df)

        # Process each row
        processed_rows = []
        for row_idx, row in enumerate(raw_df.iter_rows(named=True)):
            # Detect noise in shift code or other fields
            shift_code = row.get("shift_code")
            has_noise, noise_detail = self._detect_noise(shift_code)

            # Also check employee_name for noise
            if not has_noise:
                has_noise, noise_detail = self._detect_noise(row.get("employee_name"))

            if has_noise:
                validation.noise_rows.append({
                    "row_index": row_idx + 2,  # +2 for Excel row (1-indexed + header)
                    "noise_type": noise_detail,
                    "raw_data": row,
                })

            # Map shift code
            start_time, end_time, shift_type, is_unmapped = self.vakt_code_mapper(shift_code)

            if is_unmapped and shift_code:
                code_clean = str(shift_code).strip().upper()
                if code_clean and code_clean not in ("", "NONE"):
                    validation.unmapped_codes.add(code_clean)

            # Parse date
            date_val = self._parse_date(row.get("date"))

            processed_rows.append({
                "employee_id": row.get("employee_id"),
                "employee_name": row.get("employee_name"),
                "date": date_val,
                "shift_code": shift_code,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "shift_type": shift_type,
                "department": row.get("department"),
                "has_noise": has_noise,
                "noise_detail": noise_detail,
            })

        # Create result DataFrame
        if processed_rows:
            shifts_df = pl.DataFrame(processed_rows)
            # Filter out empty rows
            shifts_df = shifts_df.filter(
                pl.col("employee_id").is_not_null() | pl.col("date").is_not_null()
            )
        else:
            shifts_df = pl.DataFrame(schema={
                "employee_id": pl.Utf8,
                "employee_name": pl.Utf8,
                "date": pl.Datetime,
                "shift_code": pl.Utf8,
                "start_time": pl.Utf8,
                "end_time": pl.Utf8,
                "shift_type": pl.Utf8,
                "department": pl.Utf8,
                "has_noise": pl.Boolean,
                "noise_detail": pl.Utf8,
            })

        return ParseResult(
            shifts=shifts_df,
            validation=validation,
            raw_row_count=raw_row_count,
            clean_row_count=len(shifts_df),
        )


def load_parser(config_path: Path | str | None = None) -> GatSlayer:
    """Factory function to create a configured GatSlayer instance"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "rules.json"
    config = ParserConfig.from_json(config_path)
    return GatSlayer(config)
