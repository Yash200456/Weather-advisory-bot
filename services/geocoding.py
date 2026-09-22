import requests

class LocationNotFoundError(Exception):
    pass

def resolve_city(city_name: str) -> tuple[float, float]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name}
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        raise LocationNotFoundError(f"Could not reach geocoding API for '{city_name}'")
    
    data = response.json()
    results = data.get("results")
    
    if not results:
        raise LocationNotFoundError(f"No location found for '{city_name}'")
    
    first = results[0]
    return first["latitude"], first["longitude"]