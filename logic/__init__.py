"""
Turnus Logic Module

Contains:
- parser.py: The Gat-Slayer (data ingestion)
- auditor.py: The Auditor (legal logic engine)
- fatigue.py: The Economist (predictive analysis) [future]
"""

from .parser import GatSlayer, load_parser, ParseResult, ValidationReport
from .auditor import Auditor, load_auditor, AuditResult, Violation

__all__ = [
    "GatSlayer",
    "load_parser",
    "ParseResult",
    "ValidationReport",
    "Auditor",
    "load_auditor",
    "AuditResult",
    "Violation",
]
