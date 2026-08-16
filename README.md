# weather_report_app

A command-line weather app that reports real-time conditions for any city in the US,
powered by the [OpenWeatherMap API](https://openweathermap.org/api).

Give it a city, and it prints the temperature (Celsius), humidity, and a description
of the current conditions.

```
==============================================
 WEATHER REPORT  |  Nashville, Tennessee
==============================================
  ☁  Description : Broken Clouds
     Temperature : 24.4 C  (75.9 F)
     Feels Like  : 25.1 C  (77.2 F)
     Humidity    : 68%
     Wind        : 3.6 m/s
==============================================
```

## Features

- Accepts the city as a CLI argument, or prompts for one if you don't pass any
- Handles state codes (`"Springfield, IL"`) so same-named cities aren't ambiguous
- Forgiving input parsing — `nashville tn`, `Nashville, TN`, and `Nashville,tn` all work
- Uses the Geocoding API restricted to `US` so results are always American cities
- Shows both Celsius and Fahrenheit, plus feels-like temperature and wind speed
- Condition icon (☀ ☁ ☂ ⚡ ❄) matched to the current weather
- Clear error messages for a bad city name, a missing/invalid API key, or no network

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/<your-username>/weather_report_app.git
cd weather_report_app
```

**2. Install the dependencies** (Python 3.8+)

```bash
pip install -r requirements.txt
```

**3. Get a free API key**

Sign up at [openweathermap.org](https://home.openweathermap.org/users/sign_up) and copy
your key from the **API keys** tab. New keys can take up to a couple of hours to activate.

**4. Add your key**

Copy the example env file and paste your key into it:

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Then edit `.env`:

```
OPENWEATHER_API_KEY=your_actual_key_here
```

`.env` is listed in `.gitignore`, so your key never gets committed.

## Usage

Pass the city as an argument:

```bash
python weather.py "Nashville, TN"
python weather.py Denver
python weather.py "New York, NY"
```

Or run it with no arguments and it will ask:

```bash
python weather.py
Enter a US city: Seattle
```

### Options

| Flag | Description |
| --- | --- |
| `-u`, `--units` | `metric` (default) or `imperial` — the units requested from the API. Celsius and Fahrenheit are both printed either way. |
| `-h`, `--help` | Show usage and exit. |

```bash
python weather.py Miami --units imperial
```

## How it works

1. **Parse** — the raw input is normalized with a regex and split into a city and an
   optional state code.
2. **Geocode** — `GET /geo/1.0/direct` converts `city,state,US` into latitude/longitude.
3. **Fetch** — `GET /data/2.5/weather` returns the current conditions for those coordinates.
4. **Format** — temperature, humidity, and description are pulled out of the JSON, the
   description is title-cased with a regex, and the report is printed to the terminal.

## Troubleshooting

| Message | Fix |
| --- | --- |
| `OPENWEATHER_API_KEY is not set` | Create a `.env` file from `.env.example` and add your key. |
| `API key was rejected` | Double-check the key. Brand-new keys take a little while to activate. |
| `No US city found matching '…'` | Check the spelling, or add a state code: `"Portland, ME"`. |
| `Could not reach OpenWeatherMap` | Check your internet connection. |
