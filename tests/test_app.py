import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def clean_db():
    if os.path.exists('mock_cbr.db'):
        os.remove('mock_cbr.db')
    yield

def test_successful_response(client):
    response = client.get("/scripts/XML_daily.asp?date_req=02/03/2002")
    assert response.status_code == 200
    assert b"ValCurs" in response.data
    assert b"02.03.2002" in response.data
    assert b"USD" in response.data
    assert b"EUR" in response.data

def test_missing_date(client):
    response = client.get("/scripts/XML_daily.asp")
    assert response.status_code == 200
    assert b"ValCurs" in response.data

def test_invalid_date(client):
    response = client.get("/scripts/XML_daily.asp?date_req=32/13/2024")
    assert response.status_code == 400
    assert b"Invalid date format" in response.data

def test_error_response(client, monkeypatch):
    # Принудительно вызвать ошибку 500
    monkeypatch.setattr('random.random', lambda: 0.1)  # < 0.2 → ошибка
    response = client.get("/scripts/XML_daily.asp?date_req=01/01/2023")
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data
