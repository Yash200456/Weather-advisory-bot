# services/weather.py
import requests


class WeatherFetchError(Exception):
    pass


def get_current_weather(latitude: float, longitude: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,precipitation,precipitation_probability,uv_index"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        raise WeatherFetchError("Could not reach weather API")

    data = response.json()
    current = data.get("current")

    if not current:
        raise WeatherFetchError("Weather API returned no current conditions")

    return current