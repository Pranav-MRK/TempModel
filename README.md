# Model 2 – Weather Intelligence API

## 1. Project Overview

Model 2 is an independent Weather Intelligence API developed for our agricultural weather monitoring project.

Its purpose is to collect, process, validate and provide weather information for the configured farm location.

Model 2 uses the **Open-Meteo Weather API** as its weather data provider.

It provides:

- Current weather conditions
- Weather forecasts
- Historical weather information
- Rainfall measurements
- Temperature and humidity
- Wind speed and direction
- Soil temperature and soil moisture
- Evapotranspiration (ET0)
- Weather data quality validation
- Weather data freshness information

Model 2 does not make irrigation recommendations. It only provides weather intelligence.

---

## 2. Overall Project Architecture

Our project consists of three independent models.

### Model 1 – Prediction ML Model

Model 1 is responsible for its own machine learning predictions.

It is developed independently from Model 2.

### Model 2 – Weather Intelligence API

Model 2 collects and provides weather information through a REST API.

It provides current, forecast and historical weather data, along with data quality and freshness information.

### Model 3 – Integration and Decision Model

Model 3 is responsible for combining the outputs of Model 1 and Model 2.

It will use:

- Predictions received from Model 1
- Weather information received from Model 2

Model 3 will process both inputs and generate the final output of the overall project.

### Architecture flow

```text
                MODEL 1
           Prediction ML Model
                   |
                   |
                   v
             Model 1 Output
                   |
                   |
                   v
             +-----------+
             |           |
             |  MODEL 3  |
             |           |
             +-----------+
                   ^
                   |
                   |
             Model 2 Output
                   |
                   |
                   v
                MODEL 2
         Weather Intelligence API
                   |
                   v
              Open-Meteo
            Weather Provider
```

**Important:** Model 1 and Model 2 operate independently. Model 3 is responsible for combining their outputs.

---

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Main programming language |
| FastAPI | REST API framework |
| Uvicorn | API server |
| Open-Meteo | Weather data provider |
| HTTPX | HTTP requests |
| Pydantic Settings | Environment configuration |
| Pytest | Automated testing |
| uv | Python dependency and project management |

---

## 4. Project Folder Structure

```text
model2-irrigation-api/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── tests/
│   └── test_main.py
│
├── .env
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

### Important files

**app/main.py**

Contains the FastAPI application, weather endpoints, data validation functions and freshness calculations.

**tests/test_main.py**

Contains automated tests for the health endpoint and weather data validation.

**.env**

Stores the farm configuration, including latitude and longitude.

**pyproject.toml**

Stores project dependencies and pytest configuration.

---

## 5. Installation and Setup

### Requirements

- Python 3.12
- uv
- VS Code or another Python IDE

### Step 1 – Clone the project

```bash
git clone YOUR_REPOSITORY_URL
```

Replace `YOUR_REPOSITORY_URL` with the actual Git repository URL.

Move into the project folder:

```bash
cd model2-irrigation-api
```

### Step 2 – Install dependencies

```bash
uv sync
```

### Step 3 – Configure environment variables

Create a `.env` file in the project root.

Example:

```env
MODEL2_FARM_NAME=Pilot Farm
MODEL2_LATITUDE=18.523726
MODEL2_LONGITUDE=73.86876
MODEL2_TIMEZONE=Asia/Kolkata
```

These are the coordinates currently used in the project configuration. Update them if the actual farm location is different.

Do not upload `.env` or private credentials to GitHub.

### Step 4 – Start the API

```bash
uv run uvicorn app.main:app --reload
```

The local API will run at:

```text
http://127.0.0.1:8000
```

### Step 5 – Open API documentation

```text
http://127.0.0.1:8000/docs
```

FastAPI provides interactive API documentation where endpoints can be tested.

---

## 6. API Endpoints

All endpoints are provided by Model 2.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API status |
| GET | `/monitoring/weather` | Current weather and 7-day forecast |
| GET | `/monitoring/weather/history` | Historical weather data |
| GET | `/monitoring/weather/quality` | Forecast data quality |
| GET | `/monitoring/weather/history/quality` | Historical data quality |
| GET | `/monitoring/weather/combined` | Combined historical and forecast data |
| GET | `/monitoring/weather/summary` | Important weather information in one response |

### 6.1 Health Check

```http
GET /health
```

Checks whether the API is running.

Example response:

```json
{
  "status": "ok",
  "service": "model2-weather-api"
}
```

### 6.2 Current Weather and Forecast

```http
GET /monitoring/weather
```

Provides:

- Current temperature
- Relative humidity
- Apparent temperature
- Rainfall and precipitation
- Weather code
- Cloud cover
- Wind speed and direction
- Wind gusts
- Hourly weather information
- Seven-day daily forecast
- Soil moisture
- Soil temperature
- ET0
- Solar radiation
- Vapour pressure deficit

### 6.3 Historical Weather

```http
GET /monitoring/weather/history?start_date=2026-10-01&end_date=2026-10-07
```

Provides historical weather data for the requested date range.

Historical information includes:

- Mean, maximum and minimum temperature
- Daily rainfall and precipitation
- Relative humidity
- Soil temperature
- Soil moisture
- Evapotranspiration
- Solar radiation
- Wind speed

The maximum requested period is 31 calendar days.

### 6.4 Forecast Data Quality

```http
GET /monitoring/weather/quality
```

Checks forecast data for:

- Missing weather sections
- Missing required variables
- Missing values
- Incorrect array lengths
- Invalid physical ranges
- Missing units

Example response structure:

```json
{
  "service": "model2-weather-api",
  "source": "Open-Meteo",
  "quality_check": {
    "valid": true,
    "issue_count": 0,
    "issues": []
  }
}
```

### 6.5 Historical Data Quality

```http
GET /monitoring/weather/history/quality?start_date=2026-10-01&end_date=2026-10-07
```

Validates historical weather data using similar quality checks.

### 6.6 Combined Weather Data

```http
GET /monitoring/weather/combined?start_date=2026-10-01&end_date=2026-10-07
```

Combines forecast and historical weather information into one response.

The response includes:

- Schema version
- Location
- Forecast information
- Historical information
- Source information
- Retrieval timestamps
- Data freshness information for the forecast

This endpoint is particularly useful for Model 3 integration.

### 6.7 Weather Summary

```http
GET /monitoring/weather/summary
```

This is the simplified endpoint for retrieving the most important weather information.

It provides:

| Parameter | Description | Unit |
|---|---|---|
| Temperature | Current temperature | °C |
| Humidity | Relative humidity | % |
| Wind speed | Current wind speed | km/h |
| Wind direction | Wind direction | Degrees |
| Rainfall | Current rain measurement | mm |
| Precipitation | Current precipitation | mm |
| Soil temperature | Surface soil temperature | °C |
| Soil moisture | Soil moisture at 0–7 cm | m³/m³ |
| Yesterday's rainfall | Previous day's rain total | mm |
| Today's rainfall | Today's rain total | mm |
| Maximum temperature | Today's forecast maximum | °C |
| Minimum temperature | Today's forecast minimum | °C |
| Maximum wind speed | Today's forecast maximum | km/h |

The summary also includes the location, retrieval timestamp and data freshness.

---

## 7. Data Freshness Monitoring

Model 2 includes a data freshness function to help identify how recent the weather information is.

It compares the weather timestamp supplied by Open-Meteo against the current UTC time.

The configured threshold is 120 minutes.

| Status | Meaning |
|---|---|
| `fresh` | Weather timestamp is within the 120-minute threshold |
| `stale` | Weather timestamp is older than the threshold |
| `unknown` | Timestamp is missing, invalid or unexpectedly in the future |

Example:

```json
{
  "data_freshness": {
    "status": "fresh",
    "data_timestamp_local": "2026-10-30T20:00",
    "data_timestamp_utc": "2026-10-30T14:30:00+00:00",
    "age_minutes": 25.0,
    "threshold_minutes": 120
  }
}
```

The example values are illustrative.

**Important distinction:**

- `retrieved_at_utc` indicates when Model 2 retrieved the response.
- `data_timestamp_utc` indicates the timestamp of the weather data.

These timestamps are not necessarily the same.

---

## 8. How Model 3 Can Integrate Model 2

Model 3 can retrieve weather information by sending an HTTP GET request to Model 2.

For example, if Model 2 is running locally:

```text
http://127.0.0.1:8000/monitoring/weather/summary
```

When the models run on separate computers or servers, Model 3 must use the reachable host address of Model 2 instead.

### Example Python integration

```python
import httpx

MODEL2_URL = "http://127.0.0.1:8000"

async def get_model2_weather():

    endpoint = f"{MODEL2_URL}/monitoring/weather/summary"

    async with httpx.AsyncClient(timeout=20.0) as client:

        response = await client.get(endpoint)

        response.raise_for_status()

        weather_data = response.json()

        return weather_data
```

### Example: Accessing weather information

```python
weather = await get_model2_weather()

temperature = weather["current_weather"]["temperature_c"]

humidity = weather["current_weather"]["humidity_percent"]

wind_speed = weather["current_weather"]["wind_speed_kmh"]

yesterday_rainfall = weather["rainfall"]["yesterday_mm"]

freshness = weather["data_freshness"]["status"]
```

Model 3 can use these values alongside the output it receives from Model 1.

### Recommended integration checks

Before using weather data in its processing, Model 3 should:

1. Check that the Model 2 API request succeeds.
2. Check whether required weather fields are available.
3. Inspect the `data_freshness.status` value.
4. Handle missing or unavailable measurements.
5. Preserve the source and units of weather information.

Model 3 should decide how to combine Model 1 and Model 2 outputs. Model 2 does not perform that decision-making process.

---

## 9. Automated Testing

Model 2 uses Pytest for automated testing.

Run:

```bash
uv run python -m pytest -v
```

Current test coverage includes:

- Health endpoint
- Valid forecast data
- Invalid forecast values
- Missing forecast variables
- Valid historical data
- Invalid historical values
- Missing historical variables

**Current test result: 15 passed.**

These tests use sample data and do not require live Open-Meteo requests.

Freshness-specific automated tests and endpoint integration tests are future testing improvements.

---

## 10. Error Handling

Model 2 handles common provider errors.

| HTTP status | Meaning |
|---|---|
| 200 | Successful request |
| 400 | Invalid date parameters |
| 502 | Weather provider error or unavailable response |

The API uses HTTPX timeouts to prevent requests from waiting indefinitely.

---

## 11. Data Source

**Open-Meteo**

Weather forecast API:

https://open-meteo.com/en/docs

Historical weather API:

https://open-meteo.com/en/docs/historical-weather-api

Model 2 currently uses Open-Meteo as its weather data provider.

---

## 12. Current Development Status

| Feature | Status |
|---|---|
| FastAPI application | Completed |
| Open-Meteo integration | Working |
| Current weather endpoint | Working |
| Seven-day forecast | Working |
| Historical weather endpoint | Working |
| Weather data validation | Working |
| Historical data validation | Working |
| Combined weather endpoint | Working |
| Weather summary endpoint | Working |
| Data freshness calculation | Implemented |
| Existing automated tests | 15 passing |
| Freshness-specific tests | Pending |
| Model 3 integration | Pending |

---

## 13. Team Responsibilities and Integration Boundary

### Model 2 team

Responsible for:

- Weather API
- Weather data collection
- Historical weather
- Forecast information
- Data quality validation
- Data freshness monitoring
- Providing a consistent API response

### Model 3 team

Responsible for:

- Connecting to Model 1
- Connecting to Model 2
- Receiving and validating both model outputs
- Combining the two independent inputs
- Implementing the final project logic
- Producing the final project output

### Important architecture rule

Model 2 must remain an independent weather intelligence service.

It must not depend on Model 1 and must not generate irrigation recommendations.

Model 3 is the integration layer responsible for combining the outputs of both models.

---

## 14. Contact and Project Notes

Project component: Model 2 – Weather Intelligence API

Framework: FastAPI

Language: Python 3.12

Weather provider: Open-Meteo

API documentation: `/docs`

Health endpoint: `/health`

Main integration endpoint: `/monitoring/weather/summary`

Combined integration endpoint: `/monitoring/weather/combined`

**Development principle:** Keep Model 1 and Model 2 independent, maintain consistent data formats, and let Model 3 handle the integration of their outputs.
