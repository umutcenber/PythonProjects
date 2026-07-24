import requests

def get_coordinates(city):
    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    data = response.json()

    if "results" not in data:
        return None

    place = data["results"][0]

    return (
        place["latitude"],
        place["longitude"],
        place["name"],
        place["country"]
    )


def get_weather(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code"
        ]
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None

    return response.json()["current"]


def weather_description(code):
    descriptions = {
        0: "Clear Sky ",
        1: "Mostly Clear ",
        2: "Partly Cloudy ",
        3: "Cloudy ",
        45: "Fog ",
        48: "Fog ",
        51: "Light Drizzle ",
        53: "Drizzle",
        55: "Heavy Drizzle ",
        61: "Light Rain ",
        63: "Rain ",
        65: "Heavy Rain ",
        71: "Snow ",
        73: "Snow ",
        75: "Heavy Snow ",
        80: "Rain Showers ",
        81: "Rain Showers ",
        82: "Heavy Showers ",
        95: "Thunderstorm "
    }

    return descriptions.get(code, "Unknown")


def main():
    print("=" * 40)
    print("        WEATHER APP")
    print("=" * 40)

    city = input("Enter city: ").strip()

    coordinates = get_coordinates(city)

    if coordinates is None:
        print("\n❌ City not found.")
        return

    latitude, longitude, city_name, country = coordinates

    weather = get_weather(latitude, longitude)

    if weather is None:
        print("\n❌ Could not retrieve weather.")
        return

    print("\n========== WEATHER ==========")
    print(f"📍 City: {city_name}, {country}")
    print(f"🌡️ Temperature: {weather['temperature_2m']} °C")
    print(f"💧 Humidity: {weather['relative_humidity_2m']}%")
    print(f"🌬️ Wind Speed: {weather['wind_speed_10m']} km/h")
    print(f"☁️ Weather: {weather_description(weather['weather_code'])}")


if __name__ == "__main__":
    main()