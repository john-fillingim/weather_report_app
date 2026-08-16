"""
weather_report_app — CLI weather lookup for any city in the US.

Sources current conditions from the OpenWeatherMap API and prints
temperature (Celsius), humidity, and a description to the terminal.

Usage:
    python weather.py "Nashville, TN"
    python weather.py Austin --units imperial
    python weather.py                 # prompts for a city
"""

import argparse
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT = 10

# Small map so the report can print a matching icon for the conditions.
CONDITION_ICONS = {
    "Clear": "☀",
    "Clouds": "☁",
    "Rain": "☂",
    "Drizzle": "☂",
    "Thunderstorm": "⚡",
    "Snow": "❄",
    "Mist": "≈",
    "Fog": "≈",
    "Haze": "≈",
    "Smoke": "≈",
}

# Older Windows terminals default to cp1252 and cannot print the symbols above.
ASCII_ICONS = {
    "Clear": "(*)",
    "Clouds": "(~)",
    "Rain": "(//)",
    "Drizzle": "(')",
    "Thunderstorm": "(!)",
    "Snow": "(**)",
    "Mist": "(=)",
    "Fog": "(=)",
    "Haze": "(=)",
    "Smoke": "(=)",
}


def pick_icon(condition):
    """Return an icon the current terminal can actually render."""
    icon = CONDITION_ICONS.get(condition, "*")
    encoding = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        icon.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return ASCII_ICONS.get(condition, "*")
    return icon

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}


class WeatherError(Exception):
    """Raised for any user-facing failure (bad city, bad key, network down)."""


def parse_location(raw):
    """Split free-form user input into (city, state_code_or_None).

    Accepts "Nashville, TN", "nashville tn", "New York", "  Saint Louis,mo  ".
    Regex normalizes whitespace/commas so sloppy input still works.
    """
    text = re.sub(r"[\s,]+", " ", raw).strip()
    if not text:
        raise WeatherError("No city provided.")

    if not re.search(r"[A-Za-z]", text):
        raise WeatherError(f"'{raw}' does not look like a city name.")

    parts = text.split(" ")
    if len(parts) > 1 and parts[-1].upper() in US_STATES:
        return " ".join(parts[:-1]).title(), parts[-1].upper()
    return text.title(), None


def geocode(city, state, api_key):
    """Resolve a US city (optionally city+state) to lat/lon via the Geocoding API."""
    query = ",".join(part for part in (city, state, "US") if part)
    params = {"q": query, "limit": 5, "appid": api_key}

    try:
        response = requests.get(GEO_URL, params=params, timeout=TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise WeatherError(f"Could not reach OpenWeatherMap: {exc}") from exc

    if response.status_code == 401:
        raise WeatherError("API key was rejected. Check OPENWEATHER_API_KEY in your .env file.")
    response.raise_for_status()

    matches = [m for m in response.json() if m.get("country") == "US"]
    if not matches:
        hint = f"{city}, {state}" if state else city
        raise WeatherError(
            f"No US city found matching '{hint}'. "
            "Try adding a state code, e.g. \"Springfield, IL\"."
        )
    return matches[0]


def fetch_weather(lat, lon, api_key, units="metric"):
    """Pull current conditions for a coordinate pair."""
    params = {"lat": lat, "lon": lon, "units": units, "appid": api_key}

    try:
        response = requests.get(WEATHER_URL, params=params, timeout=TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise WeatherError(f"Could not reach OpenWeatherMap: {exc}") from exc

    if response.status_code == 401:
        raise WeatherError("API key was rejected. Check OPENWEATHER_API_KEY in your .env file.")
    response.raise_for_status()
    return response.json()


def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32


def build_report(place, data, units):
    """Format the API payload into the block of text printed to the CLI."""
    weather = data["weather"][0]
    main = data["main"]

    # The API returns lowercase text like "broken clouds" — title-case each word.
    description = re.sub(r"\b[a-z]", lambda m: m.group().upper(), weather["description"])
    icon = pick_icon(weather["main"])

    temp = main["temp"]
    feels_like = main["feels_like"]
    if units == "imperial":
        temp_c, feels_c = (temp - 32) * 5 / 9, (feels_like - 32) * 5 / 9
        temp_f, feels_f = temp, feels_like
    else:
        temp_c, feels_c = temp, feels_like
        temp_f, feels_f = celsius_to_fahrenheit(temp), celsius_to_fahrenheit(feels_like)

    location = place.get("name", "")
    if place.get("state"):
        location += f", {place['state']}"

    wind_unit = "mph" if units == "imperial" else "m/s"
    wind = data.get("wind", {}).get("speed")

    width = 46
    lines = [
        "=" * width,
        f" WEATHER REPORT  |  {location}".rstrip(),
        "=" * width,
        f"  {icon}  Description : {description}",
        f"     Temperature : {temp_c:.1f} C  ({temp_f:.1f} F)",
        f"     Feels Like  : {feels_c:.1f} C  ({feels_f:.1f} F)",
        f"     Humidity    : {main['humidity']}%",
    ]
    if wind is not None:
        lines.append(f"     Wind        : {wind:.1f} {wind_unit}")
    lines.append("=" * width)
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Get the current weather for any city in the US.",
        epilog='Example: python weather.py "Nashville, TN"',
    )
    parser.add_argument(
        "city",
        nargs="*",
        help='City name, optionally with a state code (e.g. "Springfield, IL")',
    )
    parser.add_argument(
        "-u",
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Units used by the API (both C and F are always shown). Default: metric",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print(
            "Error: OPENWEATHER_API_KEY is not set.\n"
            "Copy .env.example to .env and add your OpenWeatherMap API key.",
            file=sys.stderr,
        )
        return 1

    raw_city = " ".join(args.city) if args.city else input("Enter a US city: ")

    try:
        city, state = parse_location(raw_city)
        place = geocode(city, state, api_key)
        data = fetch_weather(place["lat"], place["lon"], api_key, args.units)
        print()
        print(build_report(place, data, args.units))
        print()
    except WeatherError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as exc:
        print(f"Error: the weather service returned an error ({exc}).", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
