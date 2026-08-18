"""
Streamlit front end for weather_report_app.

Takes a US city from the user, calls the OpenWeatherMap API, and shows the
current conditions plus a 5-day forecast chart.

Run with:
    streamlit run app.py
"""

import os
import re

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from weather import (
    WeatherError,
    celsius_to_fahrenheit,
    fetch_forecast,
    fetch_weather,
    geocode,
    parse_location,
)

load_dotenv()

st.set_page_config(page_title="US weather report", page_icon="⛅", layout="centered")

# Emoji per OpenWeatherMap condition group — the browser renders these fine,
# unlike the CLI, so we can be more expressive than weather.py's icons.
CONDITION_EMOJI = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
    "Smoke": "🌫️",
    "Dust": "🌬️",
    "Sand": "🌬️",
    "Tornado": "🌪️",
}


def get_api_key():
    """Read the key from Streamlit secrets first, then fall back to .env."""
    try:
        key = st.secrets.get("OPENWEATHER_API_KEY")
    except FileNotFoundError:  # No secrets.toml on this machine — that's fine.
        key = None
    return key or os.getenv("OPENWEATHER_API_KEY")


def title_case(text):
    """The API returns 'broken clouds' — capitalize each word."""
    return re.sub(r"\b[a-z]", lambda m: m.group().upper(), text)


def compass(degrees):
    """Turn a wind bearing into a readable direction like 'NW'."""
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return points[round(degrees / 45) % 8]


@st.cache_data(ttl="10m", show_spinner=False)
def load_weather(raw_city, units, api_key):
    """Geocode the city, then fetch current conditions and the forecast.

    Cached for 10 minutes so re-running the same lookup doesn't burn API calls.
    """
    city, state = parse_location(raw_city)
    place = geocode(city, state, api_key)
    current = fetch_weather(place["lat"], place["lon"], api_key, units)
    forecast = fetch_forecast(place["lat"], place["lon"], api_key, units)
    return place, current, forecast


def forecast_frame(forecast, unit_label):
    """Flatten the 3-hour forecast list into a DataFrame for charting."""
    rows = [
        {
            "When": pd.to_datetime(entry["dt"], unit="s"),
            f"Temp ({unit_label})": entry["main"]["temp"],
            f"Feels like ({unit_label})": entry["main"]["feels_like"],
            "Humidity (%)": entry["main"]["humidity"],
            "Conditions": title_case(entry["weather"][0]["description"]),
        }
        for entry in forecast.get("list", [])
    ]
    return pd.DataFrame(rows)


st.title("⛅ US weather report")
st.caption("Current conditions and a 5-day forecast, powered by OpenWeatherMap.")

with st.sidebar:
    st.header("Settings")
    unit_choice = st.segmented_control(
        "Units",
        options=["Fahrenheit", "Celsius"],
        default="Fahrenheit",
        help="Both temperatures are always shown on the current conditions card.",
    )
    st.caption("Tip: add a state code for cities that share a name, e.g. `Portland, ME`.")

units = "imperial" if unit_choice == "Fahrenheit" else "metric"
unit_label = "°F" if units == "imperial" else "°C"
speed_label = "mph" if units == "imperial" else "m/s"

with st.form("city_lookup"):
    raw_city = st.text_input(
        "City",
        value="Nashville, TN",
        placeholder="Nashville, TN",
        help="Any US city. A state code is optional.",
    )
    submitted = st.form_submit_button(
        "Get weather", icon=":material/search:", type="primary"
    )

api_key = get_api_key()

if not api_key:
    st.error(
        "`OPENWEATHER_API_KEY` is not set. Add it to a `.env` file "
        "(or `.streamlit/secrets.toml`) and rerun the app.",
        icon=":material/key_off:",
    )
    st.stop()

if not submitted and not raw_city.strip():
    st.caption("Enter a city above to see its weather.")
    st.stop()

try:
    with st.spinner("Checking the sky..."):
        place, current, forecast = load_weather(raw_city, units, api_key)
except WeatherError as exc:
    st.error(str(exc), icon=":material/error:")
    st.stop()
except requests.exceptions.HTTPError as exc:
    st.error(f"The weather service returned an error ({exc}).", icon=":material/cloud_off:")
    st.stop()

condition = current["weather"][0]
main = current["main"]
emoji = CONDITION_EMOJI.get(condition["main"], "🌡️")

location = place.get("name", "")
if place.get("state"):
    location += f", {place['state']}"

# Show both scales regardless of which one the API returned.
temp = main["temp"]
feels_like = main["feels_like"]
if units == "imperial":
    temp_f, feels_f = temp, feels_like
    temp_c, feels_c = (temp - 32) * 5 / 9, (feels_like - 32) * 5 / 9
else:
    temp_c, feels_c = temp, feels_like
    temp_f, feels_f = celsius_to_fahrenheit(temp), celsius_to_fahrenheit(feels_like)

primary = f"{temp_f:.0f}°F" if units == "imperial" else f"{temp_c:.0f}°C"
secondary = f"{temp_c:.1f}°C" if units == "imperial" else f"{temp_f:.1f}°F"
feels_primary = f"{feels_f:.0f}°F" if units == "imperial" else f"{feels_c:.0f}°C"

st.subheader(f"{emoji} {location}")
st.markdown(f"**{title_case(condition['description'])}** — :gray[{secondary}]")

with st.container(horizontal=True):
    st.metric("Temperature", primary, border=True)
    st.metric(
        "Feels like",
        feels_primary,
        delta=f"{feels_like - temp:+.1f}{unit_label}",
        delta_color="off",
        border=True,
    )
    st.metric("Humidity", f"{main['humidity']}%", border=True)

wind = current.get("wind", {})
with st.container(horizontal=True):
    if wind.get("speed") is not None:
        direction = f" {compass(wind['deg'])}" if wind.get("deg") is not None else ""
        st.metric("Wind", f"{wind['speed']:.1f} {speed_label}{direction}", border=True)
    st.metric("Pressure", f"{main['pressure']} hPa", border=True)
    if current.get("clouds", {}).get("all") is not None:
        st.metric("Cloud cover", f"{current['clouds']['all']}%", border=True)

df = forecast_frame(forecast, unit_label)

if not df.empty:
    temp_col = f"Temp ({unit_label})"
    feels_col = f"Feels like ({unit_label})"

    with st.container(border=True):
        st.subheader("5-day forecast")
        st.line_chart(df, x="When", y=[temp_col, feels_col], height=280)

    with st.container(border=True):
        st.subheader("Humidity")
        st.area_chart(df, x="When", y="Humidity (%)", color="#4c9be8", height=220)

    # Daily highs and lows, derived from the 3-hour entries.
    daily = (
        df.assign(Day=df["When"].dt.strftime("%a %b %d"))
        .groupby("Day", sort=False)
        .agg(High=(temp_col, "max"), Low=(temp_col, "min"))
        .reset_index()
    )
    with st.container(border=True):
        st.subheader("Daily highs and lows")
        st.bar_chart(daily, x="Day", y=["High", "Low"], stack=False, height=260)

    with st.expander("Raw forecast data", icon=":material/table_chart:"):
        st.dataframe(df, hide_index=True, width="stretch")
else:
    st.caption("No forecast data available for this location.")

st.caption("Data from OpenWeatherMap. Results cached for 10 minutes.")
