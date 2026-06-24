"""
weather.py
-----------
Fetches live weather from OpenWeatherMap's free Current Weather API.

We hit the API by lat/lon so this works for any point along the
UAV's route, not just fixed city names.

Docs: https://openweathermap.org/current
"""

import os
import httpx
from risk import WeatherSnapshot

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherAPIError(Exception):
    pass


async def fetch_weather(lat: float, lon: float) -> WeatherSnapshot:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise WeatherAPIError(
            "OPENWEATHER_API_KEY is not set. Add it to backend/.env "
            "(copy .env.example -> .env and fill in your free API key "
            "from https://openweathermap.org/api)."
        )

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(OPENWEATHER_URL, params=params)

    if resp.status_code != 200:
        raise WeatherAPIError(
            f"OpenWeatherMap request failed ({resp.status_code}): {resp.text}"
        )

    data = resp.json()

    wind_speed_ms = data.get("wind", {}).get("speed", 0.0)
    wind_speed_kmh = wind_speed_ms * 3.6

    visibility_m = data.get("visibility", 10000)
    visibility_km = visibility_m / 1000.0

    temperature_c = data.get("main", {}).get("temp", 25.0)

    condition = "Clear"
    weather_list = data.get("weather", [])
    if weather_list:
        condition = weather_list[0].get("main", "Clear")

    # OpenWeatherMap's free current-weather endpoint doesn't return a
    # direct rain probability (that's a forecast-API field). We derive
    # a reasonable proxy from condition + presence of rain volume data,
    # and say so plainly if asked -- this is an honest approximation,
    # not a fabricated precision number.
    rain_volume = data.get("rain", {}).get("1h", 0.0)
    if condition in ("Thunderstorm", "Rain"):
        rain_probability_pct = 80.0 if rain_volume > 0 else 60.0
    elif condition in ("Drizzle", "Mist", "Fog"):
        rain_probability_pct = 40.0
    else:
        rain_probability_pct = 5.0

    return WeatherSnapshot(
        wind_speed_kmh=round(wind_speed_kmh, 1),
        visibility_km=round(visibility_km, 1),
        temperature_c=round(temperature_c, 1),
        rain_probability_pct=rain_probability_pct,
        condition=condition,
    )
