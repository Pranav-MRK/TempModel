
import pytest
from fastapi.testclient import TestClient

from app.main import (
    app,
    validate_weather_data,
    validate_historical_weather_data,
)


# --------------------------------------------------
# Test client
# --------------------------------------------------

client = TestClient(app)


# --------------------------------------------------
# Forecast test data
# --------------------------------------------------

@pytest.fixture
def valid_forecast_data():
    return {
        "current": {
            "temperature_2m": 25,
        },
        "hourly": {
            "time": ["2026-10-30T10:00"],
            "temperature_2m": [25],
            "relative_humidity_2m": [70],
            "precipitation": [0],
            "soil_moisture_0_to_7cm": [0.25],
            "et0_fao_evapotranspiration": [0.2],
        },
        "daily": {
            "time": ["2026-10-30"],
        },
        "hourly_units": {
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "precipitation": "mm",
            "soil_moisture_0_to_7cm": "m³/m³",
            "et0_fao_evapotranspiration": "mm",
        },
    }


# --------------------------------------------------
# Historical test data
# --------------------------------------------------

@pytest.fixture
def valid_historical_data():
    return {
        "hourly": {
            "time": ["2026-10-01T10:00"],
            "relative_humidity_2m": [70],
            "soil_temperature_0_to_7cm": [25],
            "soil_moisture_0_to_7cm": [0.25],
            "vapour_pressure_deficit": [1.2],
        },
        "daily": {
            "time": ["2026-10-01"],
            "temperature_2m_mean": [25],
            "temperature_2m_max": [30],
            "temperature_2m_min": [20],
            "precipitation_sum": [2],
            "et0_fao_evapotranspiration": [4],
            "shortwave_radiation_sum": [20],
        },
        "hourly_units": {
            "relative_humidity_2m": "%",
            "soil_temperature_0_to_7cm": "°C",
            "soil_moisture_0_to_7cm": "m³/m³",
            "vapour_pressure_deficit": "kPa",
        },
        "daily_units": {
            "temperature_2m_mean": "°C",
            "temperature_2m_max": "°C",
            "temperature_2m_min": "°C",
            "precipitation_sum": "mm",
            "et0_fao_evapotranspiration": "mm",
            "shortwave_radiation_sum": "MJ/m²",
        },
    }


# --------------------------------------------------
# Health endpoint tests
# --------------------------------------------------

def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# --------------------------------------------------
# Forecast validation tests
# --------------------------------------------------

def test_valid_forecast_data(valid_forecast_data):
    result = validate_weather_data(valid_forecast_data)

    assert result["valid"] is True
    assert result["issue_count"] == 0
    assert result["issues"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("relative_humidity_2m", 150),
        ("relative_humidity_2m", -10),
        ("soil_moisture_0_to_7cm", 1.5),
        ("soil_moisture_0_to_7cm", -0.1),
        ("precipitation", -5),
    ],
)
def test_invalid_forecast_values(
    valid_forecast_data,
    field,
    value,
):
    valid_forecast_data["hourly"][field] = [value]

    result = validate_weather_data(valid_forecast_data)

    assert result["valid"] is False
    assert result["issue_count"] > 0
    assert len(result["issues"]) > 0


def test_forecast_missing_hourly_data(valid_forecast_data):
    valid_forecast_data["hourly"].pop("temperature_2m")

    result = validate_weather_data(valid_forecast_data)

    assert result["valid"] is False
    assert result["issue_count"] > 0


# --------------------------------------------------
# Historical validation tests
# --------------------------------------------------

def test_valid_historical_data(valid_historical_data):
    result = validate_historical_weather_data(
        valid_historical_data
    )

    assert result["valid"] is True
    assert result["issue_count"] == 0
    assert result["issues"] == []


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("hourly", "relative_humidity_2m", 150),
        ("hourly", "relative_humidity_2m", -10),
        ("hourly", "soil_moisture_0_to_7cm", 1.5),
        ("hourly", "soil_moisture_0_to_7cm", -0.1),
        ("daily", "precipitation_sum", -2),
    ],
)
def test_invalid_historical_values(
    valid_historical_data,
    section,
    field,
    value,
):
    valid_historical_data[section][field] = [value]

    result = validate_historical_weather_data(
        valid_historical_data
    )

    assert result["valid"] is False
    assert result["issue_count"] > 0
    assert len(result["issues"]) > 0


def test_historical_missing_data(valid_historical_data):
    valid_historical_data["daily"].pop("precipitation_sum")

    result = validate_historical_weather_data(
        valid_historical_data
    )

    assert result["valid"] is False
    assert result["issue_count"] > 0
