import pytest
import sys
import os

# Adjust import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from analytics.ratios import (
    compute_npm, compute_opm, compute_roe, compute_roce,
    compute_roa, compute_debt_to_equity, compute_interest_coverage, compute_asset_turnover
)
from analytics.cagr import calculate_cagr
from analytics.cashflow_kpis import (
    compute_fcf, compute_capex_intensity, compute_fcf_conversion, classify_capital_allocation
)

# Ratios Tests (10 tests)
def test_compute_npm_normal():
    assert compute_npm(10, 100) == 10.0

def test_compute_npm_zero_sales():
    assert compute_npm(10, 0) is None

def test_compute_opm_normal():
    assert compute_opm(20, 100) == 20.0

def test_compute_roe_normal():
    assert compute_roe(15, 50, 50) == 15.0

def test_compute_roe_negative_denom():
    assert compute_roe(15, -10, -5) is None

def test_compute_roce_normal():
    # EBIT = 30 - 5 = 25
    # Capital Employed = 50 + 30 + 20 = 100
    assert compute_roce(30, 5, 50, 30, 20) == 25.0

def test_compute_roce_zero_denom():
    assert compute_roce(30, 5, -10, -10, 20) is None

def test_compute_roa_normal():
    assert compute_roa(5, 100) == 5.0

def test_compute_debt_to_equity_normal():
    assert compute_debt_to_equity(50, 50, 50) == 0.5

def test_compute_debt_to_equity_zero_borrowings():
    assert compute_debt_to_equity(0, 50, 50) == 0.0

def test_compute_interest_coverage_normal():
    assert compute_interest_coverage(40, 10, 10) == 5.0

def test_compute_interest_coverage_zero():
    assert compute_interest_coverage(40, 10, 0) is None


# CAGR Tests (6 tests covering all edge cases)
def test_cagr_positive_positive():
    # ((161/100)**(1/5) - 1) * 100 = 10.0%
    val, flag = calculate_cagr(100, 161.051, 5)
    assert val is not None
    assert round(val, 1) == 10.0
    assert flag is None

def test_cagr_decline_to_loss():
    val, flag = calculate_cagr(100, -10, 5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    val, flag = calculate_cagr(-50, 100, 5)
    assert val is None
    assert flag == "TURNAROUND"

def test_cagr_both_negative():
    val, flag = calculate_cagr(-50, -10, 5)
    assert val is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    val, flag = calculate_cagr(0, 100, 5)
    assert val is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient():
    val, flag = calculate_cagr(100, 200, 0)
    assert val is None
    assert flag == "INSUFFICIENT"


# Cash Flow KPIs Tests (5 tests)
def test_compute_fcf():
    assert compute_fcf(100, -40) == 60.0

def test_compute_capex_intensity():
    val, label = compute_capex_intensity(-50, 1000)
    assert val == 5.0
    assert label == "Moderate"

def test_compute_fcf_conversion():
    assert compute_fcf_conversion(60, 100) == 60.0

def test_classify_capital_allocation_reinvestor():
    # (+, -, -)
    assert classify_capital_allocation(100, -50, -30) == "Reinvestor"

def test_classify_capital_allocation_distress():
    # (-, +, +)
    assert classify_capital_allocation(-10, 20, 30) == "Distress Signal"
