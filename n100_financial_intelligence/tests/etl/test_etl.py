import pytest
import sys
import os

# Adjust import path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from etl.normaliser import normalize_ticker, normalize_year


# 20 tests for normalize_year
def test_normalize_year_pure_int():
    assert normalize_year(2024) == 2024


def test_normalize_year_pure_float():
    assert normalize_year(2021.0) == 2021


def test_normalize_year_string_int():
    assert normalize_year("2018") == 2018


def test_normalize_year_dec_format():
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_mar_dash_format():
    assert normalize_year("Mar-13") == 2013


def test_normalize_year_sep_dash_format():
    assert normalize_year("Sep-24") == 2024


def test_normalize_year_with_suffix():
    assert normalize_year("Mar 2023 15") == 2023


def test_normalize_year_9m_suffix():
    assert normalize_year("Mar 2016 9m") == 2016


def test_normalize_year_ttm():
    assert normalize_year("TTM") is None


def test_normalize_year_na():
    assert normalize_year(float("nan")) is None


def test_normalize_year_none():
    assert normalize_year(None) is None


def test_normalize_year_invalid_str():
    assert normalize_year("Not A Year") is None


def test_normalize_year_empty_str():
    assert normalize_year("") is None


def test_normalize_year_whitespace():
    assert normalize_year("  2020  ") == 2020


def test_normalize_year_slashed_format():
    assert normalize_year("Mar/15") == 2015


def test_normalize_year_dec_short_whitespace():
    assert normalize_year("Dec- 12") is None


def test_normalize_year_jun_format():
    assert normalize_year("Jun 2014") == 2014


def test_normalize_year_sep_format():
    assert normalize_year("Sep 2021") == 2021


def test_normalize_year_early_2000s():
    assert normalize_year("Mar-05") == 2005


def test_normalize_year_late_1900s():
    assert normalize_year("Mar-99") == 1999


# 15 tests for normalize_ticker
def test_normalize_ticker_basic():
    assert normalize_ticker("abb") == "ABB"


def test_normalize_ticker_spaces():
    assert normalize_ticker("  ADANIENSOL  ") == "ADANIENSOL"


def test_normalize_ticker_mixed():
    assert normalize_ticker("HdfcBank") == "HDFCBANK"


def test_normalize_ticker_dash():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"


def test_normalize_ticker_ampersand():
    assert normalize_ticker("M&M") == "M&M"


def test_normalize_ticker_none():
    assert normalize_ticker(None) is None


def test_normalize_ticker_nan():
    assert normalize_ticker(float("nan")) is None


def test_normalize_ticker_number():
    assert normalize_ticker(123) is None


def test_normalize_ticker_empty():
    assert normalize_ticker("") == ""


def test_normalize_ticker_only_spaces():
    assert normalize_ticker("   ") == ""


def test_normalize_ticker_already_upper():
    assert normalize_ticker("TCS") == "TCS"


def test_normalize_ticker_infosys():
    assert normalize_ticker("infy") == "INFY"


def test_normalize_ticker_ltd():
    assert normalize_ticker("LT") == "LT"


def test_normalize_ticker_tatasteel():
    assert normalize_ticker("TATASTEEL") == "TATASTEEL"


def test_normalize_ticker_reliance():
    assert normalize_ticker("RELIANCE") == "RELIANCE"
