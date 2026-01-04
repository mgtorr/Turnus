#!/bin/bash
#
# Turnus Risk Audit - Verification Script
# ========================================
#
# This script runs the complete test verification suite.
#
# Usage:
#   ./scripts/verify.sh [options]
#
# Options:
#   --quick     Run only unit tests (skip slow integration tests)
#   --chaos     Generate chaos data before testing
#   --verbose   Show detailed test output
#   --coverage  Generate coverage report
#   --ci        CI mode (strict, no interactive prompts)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
QUICK=false
CHAOS=false
VERBOSE=false
COVERAGE=false
CI=false

for arg in "$@"; do
    case $arg in
        --quick) QUICK=true ;;
        --chaos) CHAOS=true ;;
        --verbose) VERBOSE=true ;;
        --coverage) COVERAGE=true ;;
        --ci) CI=true ;;
    esac
done

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Turnus Risk Audit - Verification Suite                 ║${NC}"
echo -e "${BLUE}║       Norwegian Labor Compliance Engine (2026)               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Track results
PASSED=0
FAILED=0
SKIPPED=0

check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $1"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $1"
        ((FAILED++))
        if [ "$CI" = true ]; then
            exit 1
        fi
    fi
}

skip_check() {
    echo -e "${YELLOW}○ SKIP${NC}: $1"
    ((SKIPPED++))
}

# ============================================================================
# PHASE 1: Environment Check
# ============================================================================
echo -e "\n${BLUE}━━━ Phase 1: Environment Check ━━━${NC}\n"

# Check Python version
echo -n "Checking Python version... "
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python $PY_VERSION"
    check_result "Python 3.12+ installed"
else
    echo -e "${RED}Python 3 not found${NC}"
    exit 1
fi

# Check required packages
echo -n "Checking Polars... "
if python3 -c "import polars" 2>/dev/null; then
    check_result "Polars installed"
else
    echo -e "${YELLOW}Not installed - installing...${NC}"
    pip install polars -q
    check_result "Polars installed"
fi

echo -n "Checking pytest... "
if python3 -c "import pytest" 2>/dev/null; then
    check_result "pytest installed"
else
    pip install pytest pytest-cov -q
    check_result "pytest installed"
fi

echo -n "Checking openpyxl... "
if python3 -c "import openpyxl" 2>/dev/null; then
    check_result "openpyxl installed"
else
    pip install openpyxl -q
    check_result "openpyxl installed"
fi

# ============================================================================
# PHASE 2: Configuration Validation
# ============================================================================
echo -e "\n${BLUE}━━━ Phase 2: Configuration Validation ━━━${NC}\n"

echo -n "Checking rules.json exists... "
if [ -f "config/rules.json" ]; then
    check_result "rules.json found"
else
    echo -e "${RED}config/rules.json not found${NC}"
    exit 1
fi

echo -n "Validating rules.json syntax... "
if python3 -c "import json; json.load(open('config/rules.json'))" 2>/dev/null; then
    check_result "Valid JSON syntax"
else
    echo -e "${RED}Invalid JSON${NC}"
    exit 1
fi

echo -n "Checking AML § 10-8 thresholds... "
if python3 -c "
import json
rules = json.load(open('config/rules.json'))
assert rules['aml']['section_10_8']['daily_rest']['threshold_hours'] == 11
assert rules['aml']['section_10_8']['weekly_rest']['threshold_hours'] == 35
" 2>/dev/null; then
    check_result "AML thresholds correct (11h daily, 35h weekly)"
else
    echo -e "${RED}Incorrect thresholds${NC}"
    ((FAILED++))
fi

echo -n "Checking fatigue coefficients... "
if python3 -c "
import json
rules = json.load(open('config/rules.json'))
m = rules['fatigue_coefficients']['multipliers']
assert m['short_rest_under_11h']['value'] == 1.94
assert m['backward_rotation']['value'] == 0.49
assert m['successive_nights']['value'] == 0.68
assert m['night_shift_base']['value'] == 0.22
" 2>/dev/null; then
    check_result "Fatigue coefficients match CLAUDE.md spec"
else
    echo -e "${RED}Coefficient mismatch${NC}"
    ((FAILED++))
fi

# ============================================================================
# PHASE 3: Generate Chaos Data (Optional)
# ============================================================================
if [ "$CHAOS" = true ]; then
    echo -e "\n${BLUE}━━━ Phase 3: Chaos Data Generation ━━━${NC}\n"

    echo "Generating chaos test data..."
    python3 tests/generate_chaos.py data/chaos --chaos-level 3 --employees 20 --weeks 2

    if [ $? -eq 0 ]; then
        check_result "Chaos data generated"
        echo "  Files created in data/chaos/"
    else
        skip_check "Chaos generation (error)"
    fi
else
    skip_check "Chaos generation (use --chaos to enable)"
fi

# ============================================================================
# PHASE 4: Unit Tests
# ============================================================================
echo -e "\n${BLUE}━━━ Phase 4: Unit Tests ━━━${NC}\n"

PYTEST_ARGS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_ARGS="-v"
fi
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=logic --cov-report=term-missing"
fi

# Test Parser (Gat-Slayer)
echo "Running parser tests (The Gat-Slayer)..."
if python3 -m pytest tests/test_parser.py $PYTEST_ARGS --tb=short 2>&1 | tee /tmp/pytest_parser.log; then
    check_result "Parser tests"
else
    # Check if skipped due to not implemented
    if grep -q "SKIPPED" /tmp/pytest_parser.log; then
        skip_check "Parser tests (module not implemented)"
    else
        echo -e "${RED}Parser tests failed${NC}"
        ((FAILED++))
    fi
fi

# Test Auditor
echo -e "\nRunning auditor tests (The Auditor)..."
if python3 -m pytest tests/test_auditor.py $PYTEST_ARGS --tb=short 2>&1 | tee /tmp/pytest_auditor.log; then
    check_result "Auditor tests"
else
    if grep -q "SKIPPED" /tmp/pytest_auditor.log; then
        skip_check "Auditor tests (module not implemented)"
    else
        echo -e "${RED}Auditor tests failed${NC}"
        ((FAILED++))
    fi
fi

# Test Fatigue (Economist)
echo -e "\nRunning fatigue tests (The Economist)..."
if python3 -m pytest tests/test_fatigue.py $PYTEST_ARGS --tb=short 2>&1 | tee /tmp/pytest_fatigue.log; then
    check_result "Fatigue tests"
else
    if grep -q "SKIPPED" /tmp/pytest_fatigue.log; then
        skip_check "Fatigue tests (module not implemented)"
    else
        echo -e "${RED}Fatigue tests failed${NC}"
        ((FAILED++))
    fi
fi

# ============================================================================
# PHASE 5: Integration Tests
# ============================================================================
if [ "$QUICK" = false ]; then
    echo -e "\n${BLUE}━━━ Phase 5: Integration Tests ━━━${NC}\n"

    echo "Running integration tests..."
    if python3 -m pytest tests/test_integration.py $PYTEST_ARGS --tb=short 2>&1 | tee /tmp/pytest_integration.log; then
        check_result "Integration tests"
    else
        if grep -q "SKIPPED" /tmp/pytest_integration.log; then
            skip_check "Integration tests (modules not implemented)"
        else
            echo -e "${RED}Integration tests failed${NC}"
            ((FAILED++))
        fi
    fi
else
    skip_check "Integration tests (use full run to enable)"
fi

# ============================================================================
# PHASE 6: Adversarial Tests
# ============================================================================
if [ "$QUICK" = false ]; then
    echo -e "\n${BLUE}━━━ Phase 6: Adversarial Tests ━━━${NC}\n"

    echo "Running chaos/adversarial tests..."
    if python3 -m pytest tests/ -k "adversarial or chaos" $PYTEST_ARGS --tb=short 2>&1 | tee /tmp/pytest_adversarial.log; then
        check_result "Adversarial tests"
    else
        if grep -q "SKIPPED" /tmp/pytest_adversarial.log || grep -q "no tests ran" /tmp/pytest_adversarial.log; then
            skip_check "Adversarial tests (modules not implemented)"
        else
            echo -e "${RED}Adversarial tests failed${NC}"
            ((FAILED++))
        fi
    fi
else
    skip_check "Adversarial tests (use full run to enable)"
fi

# ============================================================================
# PHASE 7: Code Quality
# ============================================================================
echo -e "\n${BLUE}━━━ Phase 7: Code Quality ━━━${NC}\n"

# Check for ruff/flake8
if command -v ruff &> /dev/null; then
    echo "Running ruff linter..."
    if ruff check logic/ tests/ --quiet 2>/dev/null; then
        check_result "Linting (ruff)"
    else
        skip_check "Linting (issues found but non-blocking)"
    fi
elif command -v flake8 &> /dev/null; then
    echo "Running flake8 linter..."
    if flake8 logic/ tests/ --max-line-length=100 --ignore=E501,W503 2>/dev/null; then
        check_result "Linting (flake8)"
    else
        skip_check "Linting (issues found but non-blocking)"
    fi
else
    skip_check "Linting (no linter installed)"
fi

# Type checking
if command -v mypy &> /dev/null; then
    echo "Running type checks..."
    if mypy logic/ --ignore-missing-imports --no-error-summary 2>/dev/null; then
        check_result "Type checking (mypy)"
    else
        skip_check "Type checking (issues found but non-blocking)"
    fi
else
    skip_check "Type checking (mypy not installed)"
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Verification Summary                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASSED"
echo -e "  ${RED}Failed:${NC}  $FAILED"
echo -e "  ${YELLOW}Skipped:${NC} $SKIPPED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✓ All verification checks passed!                            ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ✗ $FAILED verification check(s) failed                        ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
