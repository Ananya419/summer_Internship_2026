import pytest
from fastapi.testclient import TestClient
import sys
import os

# Adjust import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/api')))

from main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "ok"
    assert "companies" in json_data["db_row_counts"]

def test_api_companies_list():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()) == 92

def test_api_company_details():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    assert response.json()["company_name"] == "Tata Consultancy Services Ltd"

def test_api_company_details_invalid():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404

def test_api_screener():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    for r in response.json():
        assert r["return_on_equity_pct"] >= 15.0

def test_api_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    assert len(response.json()) == 10
