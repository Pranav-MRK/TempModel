
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    farm_name: str = "Pilot Farm"
    latitude: float = 18.5204
    longitude: float = 73.8567
    timezone: str = "Asia/Kolkata"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MODEL2_",
        extra="ignore",
    )

settings = Settings()

app = FastAPI(
    title="Model 2 - Weather Intelligence API",
    version="0.2.0",
    description=(
        "Independent weather monitoring service providing "
        "current conditions and forecasts for the pilot farm."
    ),
)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

def validate_weather_data(data: dict):
    issues = []

    current = data.get("current") or {}
    hourly = data.get("hourly") or {}
    daily = data.get("daily") or {}

    # Check required sections
    for section_name, section in [
        ("current", current),
        ("hourly", hourly),
        ("daily", daily),
    ]:
        if not section:
            issues.append(f"Missing {section_name} data.")

    # Check important hourly variables
    required_hourly = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "soil_moisture_0_to_7cm",
        "et0_fao_evapotranspiration",
    ]

    for variable in required_hourly:
        values = hourly.get(variable)

        if not isinstance(values, list) or not values:
            issues.append(f"Missing hourly variable: {variable}")
            continue

        if any(value is None for value in values):
            issues.append(f"Null values found in {variable}")

    # Check timestamps and array lengths
    hourly_times = hourly.get("time", [])

    for variable, values in hourly.items():
        if isinstance(values, list) and len(values) != len(hourly_times):
            issues.append(
                f"Length mismatch in hourly variable: {variable}"
            )

    # Check basic physical ranges
    for variable, minimum, maximum in [
        ("relative_humidity_2m", 0, 100),
        ("soil_moisture_0_to_7cm", 0, 1),
        ("precipitation", 0, None),
        ("et0_fao_evapotranspiration", 0, None),
    ]:
        values = hourly.get(variable, [])

        if isinstance(values, list):
            for value in values:
                if value is None:
                    continue

                if value < minimum or (
                    maximum is not None and value > maximum
                ):
                    issues.append(
                        f"Out-of-range value in {variable}"
                    )
                    break

    # Check units
    hourly_units = data.get("hourly_units") or {}

    for variable in required_hourly:
        if variable not in hourly_units:
            issues.append(f"Missing unit for {variable}")

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }


def validate_historical_weather_data(data: dict):
    issues = []

    hourly = data.get("hourly") or {}
    daily = data.get("daily") or {}

    required_hourly = [
        "relative_humidity_2m",
        "soil_temperature_0_to_7cm",
        "soil_moisture_0_to_7cm",
        "vapour_pressure_deficit",
    ]

    required_daily = [
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "et0_fao_evapotranspiration",
        "shortwave_radiation_sum",
    ]

    def check_section(section, required, section_name, units):
        timestamps = section.get("time")

        if not isinstance(timestamps, list) or not timestamps:
            issues.append(f"Missing {section_name} timestamps.")
            return

        for variable in required:
            values = section.get(variable)

            if not isinstance(values, list) or not values:
                issues.append(f"Missing {section_name} variable: {variable}")
                continue

            if len(values) != len(timestamps):
                issues.append(f"Length mismatch in {variable}")

            if any(value is None for value in values):
                issues.append(f"Null values found in {variable}")

            if variable not in units:
                issues.append(f"Missing unit for {variable}")

        # Physical range checks
        ranges = {
            "relative_humidity_2m": (0, 100),
            "soil_moisture_0_to_7cm": (0, 1),
            "precipitation_sum": (0, None),
            "et0_fao_evapotranspiration": (0, None),
            "shortwave_radiation_sum": (0, None),
        }

        for variable, (minimum, maximum) in ranges.items():
            values = section.get(variable, [])

            if not isinstance(values, list):
                continue

            for value in values:
                if value is None:
                    continue

                if not isinstance(value, (int, float)):
                    issues.append(f"Non-numeric value in {variable}")
                    break

                if value < minimum or (
                    maximum is not None and value > maximum
                ):
                    issues.append(f"Out-of-range value in {variable}")
                    break

    check_section(
        hourly,
        required_hourly,
        "hourly",
        data.get("hourly_units") or {},
    )

    check_section(
        daily,
        required_daily,
        "daily",
        data.get("daily_units") or {},
    )

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }



@app.get("/health")
async def health():
    return {"status": "ok", "service": "model2-weather-api"}


@app.get("/monitoring/weather")
async def get_weather():
    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,is_day,precipitation,"
            "rain,showers,weather_code,cloud_cover,"
            "wind_speed_10m,wind_direction_10m,"
            "wind_gusts_10m"
        ),
        "hourly": (
            "temperature_2m,relative_humidity_2m,"
            "precipitation_probability,precipitation,"
            "rain,weather_code,cloud_cover,"
            "wind_speed_10m,wind_direction_10m,"
            "soil_temperature_0_to_7cm,"
            "soil_temperature_7_to_28cm,"
            "soil_moisture_0_to_7cm,"
            "soil_moisture_7_to_28cm,"
            "et0_fao_evapotranspiration,"
            "shortwave_radiation,"
            "vapour_pressure_deficit"
        ),
        "daily": (
            "weather_code,temperature_2m_max,"
            "temperature_2m_min,precipitation_sum,"
            "precipitation_probability_max,"
            "wind_speed_10m_max,wind_gusts_10m_max,"
            "sunrise,sunset,"
            "et0_fao_evapotranspiration,"
            "shortwave_radiation_sum"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Weather provider returned an error.",
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve valid weather data.",
        ) from exc

    return {
        "service": "model2-weather-api",
        "source": "Open-Meteo",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
        },
        "current": data.get("current"),
        "hourly": data.get("hourly"),
        "daily": data.get("daily"),
        "units": {
            "current": data.get("current_units"),
            "hourly": data.get("hourly_units"),
            "daily": data.get("daily_units"),
        },
    }


    
@app.get("/monitoring/weather/history")
async def get_historical_weather(
    start_date: str,
    end_date: str,
):
    # Validate date format and order
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Dates must use YYYY-MM-DD format.",
        )

    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date.",
        )

    if (end - start).days > 30:
        raise HTTPException(
            status_code=400,
            detail="Maximum historical date range is 31 days.",
        )

    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "rain_sum,"
            "et0_fao_evapotranspiration,"
            "shortwave_radiation_sum,"
            "wind_speed_10m_max"
        ),
        "hourly": (
            "relative_humidity_2m,"
            "soil_temperature_0_to_7cm,"
            "soil_moisture_0_to_7cm,"
            "vapour_pressure_deficit"
        ),
        "timezone": settings.timezone,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                HISTORICAL_WEATHER_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Historical weather provider returned an error.",
                "provider_status": exc.response.status_code,
                "provider_response": exc.response.text[:500],
            },
        ) from exc

    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve historical weather data.",
        ) from exc

    return {
        "service": "model2-weather-api",
        "source": "Open-Meteo Historical Weather API",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
        },
        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "daily": data.get("daily"),
        "hourly": data.get("hourly"),
        "units": {
            "daily": data.get("daily_units"),
            "hourly": data.get("hourly_units"),
        },
    }


@app.get("/monitoring/weather/quality")
async def get_weather_quality():

    # Reuse the same weather provider request
    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,"
            "precipitation,weather_code"
        ),
        "hourly": (
            "temperature_2m,relative_humidity_2m,"
            "precipitation,"
            "soil_moisture_0_to_7cm,"
            "et0_fao_evapotranspiration"
        ),
        "daily": (
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_sum"
        ),
        "forecast_days": 7,
        "timezone": settings.timezone,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                OPEN_METEO_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Weather provider returned an error.",
        ) from exc

    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve weather data.",
        ) from exc

    quality = validate_weather_data(data)

    return {
        "service": "model2-weather-api",
        "source": "Open-Meteo",
        "quality_check": quality,
        "location": {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
        },
    }


@app.get("/monitoring/weather/history/quality")
async def get_historical_weather_quality(
    start_date: str,
    end_date: str,
):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Dates must use YYYY-MM-DD format.",
        )

    if start > end:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date.",
        )

    if (end - start).days > 30:
        raise HTTPException(
            status_code=400,
            detail="Maximum historical date range is 31 days.",
        )

    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "et0_fao_evapotranspiration,"
            "shortwave_radiation_sum"
        ),
        "hourly": (
            "relative_humidity_2m,"
            "soil_temperature_0_to_7cm,"
            "soil_moisture_0_to_7cm,"
            "vapour_pressure_deficit"
        ),
        "timezone": settings.timezone,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                HISTORICAL_WEATHER_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Historical weather provider returned an error.",
                "provider_status": exc.response.status_code,
                "provider_response": exc.response.text[:500],
            },
        ) from exc

    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve historical weather data.",
        ) from exc

    quality = validate_historical_weather_data(data)

    return {
        "service": "model2-weather-api",
        "source": "Open-Meteo Historical Weather API",
        "quality_check": quality,
        "period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "location": {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
        },
    }


@app.get("/monitoring/weather/combined")
async def get_combined_weather(
    start_date: str,
    end_date: str,
):
    # Retrieve forecast data using the existing function
    forecast = await get_weather()

    # Retrieve historical data using the existing function
    historical = await get_historical_weather(
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "schema_version": "1.0",
        "service": "model2-weather-api",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),

        "location": forecast["location"],

        "forecast": {
            "source": forecast["source"],
            "current": forecast["current"],
            "hourly": forecast["hourly"],
            "daily": forecast["daily"],
            "units": forecast["units"],
        },

        "historical": {
            "source": historical["source"],
            "period": historical["period"],
            "daily": historical["daily"],
            "hourly": historical["hourly"],
            "units": historical["units"],
        },
    }


@app.get("/monitoring/weather/summary")
async def get_weather_summary():
    settings = Settings()

    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "timezone": settings.timezone,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m",
            "soil_temperature_0cm",
            "soil_moisture_0_to_7cm",
        ],
        "daily": [
            "precipitation_sum",
            "rain_sum",
            "temperature_2m_max",
            "temperature_2m_min",
            "wind_speed_10m_max",
        ],
        "past_days": 1,
        "forecast_days": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                OPEN_METEO_URL,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Weather provider error: {str(exc)}",
        )

    current = data.get("current", {})
    daily = data.get("daily", {})
    daily_times = daily.get("time", [])

    yesterday_index = 0 if daily_times else None
    today_index = 1 if len(daily_times) > 1 else None

    def daily_value(field, index):
        values = daily.get(field, [])
        if index is not None and len(values) > index:
            return values[index]
        return None

    return {
        "service": "model2-weather-api",
        "location": {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "timezone": settings.timezone,
        },
        "current_weather": {
            "temperature_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_direction_degrees": current.get("wind_direction_10m"),
            "rainfall_mm": current.get("rain"),
            "precipitation_mm": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "soil_temperature_c": current.get("soil_temperature_0cm"),
            "soil_moisture": current.get("soil_moisture_0_to_7cm"),
        },
        "rainfall": {
            "yesterday_date": daily_times[yesterday_index] if yesterday_index is not None else None,
            "yesterday_mm": daily_value("rain_sum", yesterday_index),
            "today_date": daily_times[today_index] if today_index is not None else None,
            "today_mm": daily_value("rain_sum", today_index),
        },
        "daily_forecast": {
            "maximum_temperature_c": daily_value("temperature_2m_max", today_index),
            "minimum_temperature_c": daily_value("temperature_2m_min", today_index),
            "maximum_wind_speed_kmh": daily_value("wind_speed_10m_max", today_index),
            "precipitation_mm": daily_value("precipitation_sum", today_index),
        },
        "source": "Open-Meteo",
    }
