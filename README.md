# weather_report_app ⛅

A weather app that reports real-time conditions for any city in the US, powered by the
[OpenWeatherMap API](https://openweathermap.org/api).

It comes in two flavors:

- **A Streamlit web app** (`app.py`) — type a city, get current conditions plus a 5-day forecast with charts
- **A command-line tool** (`weather.py`) — same data, printed to your terminal

## The Streamlit app

Enter a US city and the app shows:

- 🌤️ Current conditions with a matching emoji, in both Fahrenheit and Celsius
- 📊 Metric cards for temperature, feels-like, humidity, wind (with compass direction), pressure, and cloud cover
- 📈 A 5-day temperature line chart (actual vs. feels-like)
- 💧 A humidity area chart over the same window
- 🌡️ A grouped bar chart of daily highs and lows
- 🗂️ An expander with the raw forecast table

A **Fahrenheit / Celsius** toggle lives in the sidebar, and results are cached for 10 minutes
so repeated lookups don't burn through API calls.

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

Create a file named `.env` in the project root:

```
OPENWEATHER_API_KEY=your_actual_key_here
```

```bash
# macOS / Linux
echo "OPENWEATHER_API_KEY=your_actual_key_here" > .env

# Windows (PowerShell)
"OPENWEATHER_API_KEY=your_actual_key_here" | Out-File -Encoding utf8 .env
```

`.env` is listed in `.gitignore`, so your key never gets committed.

> Deploying to Streamlit Community Cloud instead? Skip the `.env` file and add
> `OPENWEATHER_API_KEY` under **Settings → Secrets**. The app reads `st.secrets` first and
> falls back to `.env`.

## Running the Streamlit app

```bash
streamlit run app.py
```

Streamlit prints a local URL (usually <http://localhost:8501>) and opens it in your browser.
Type a city into the **City** box — for example `Nashville, TN`, `Denver`, or `Portland, ME` —
and press **Get weather**.

Press `Ctrl+C` in the terminal to stop the server.

## Running the CLI

Pass the city as an argument:

```bash
python weather.py "Nashville, TN"
python weather.py Denver
python weather.py Miami --units imperial
```

Or run it with no arguments and it will ask:

```bash
python weather.py
Enter a US city: Seattle
```

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

### CLI options

| Flag | Description |
| --- | --- |
| `-u`, `--units` | `metric` (default) or `imperial` — the units requested from the API. Celsius and Fahrenheit are both printed either way. |
| `-h`, `--help` | Show usage and exit. |

## Entering a city

Both interfaces use the same forgiving parser:

- A state code is optional but disambiguates same-named cities — `Springfield, IL` vs. `Springfield, MO`
- Spacing and commas are normalized by a regex, so `nashville tn`, `Nashville, TN`, and `Nashville,tn` all work
- Geocoding is restricted to `US`, so results are always American cities

## How it works

1. **Parse** — `parse_location()` normalizes the raw input with a regex and splits it into a
   city and an optional state code.
2. **Geocode** — `GET /geo/1.0/direct` converts `city,state,US` into latitude/longitude.
3. **Fetch** — `GET /data/2.5/weather` returns current conditions and
   `GET /data/2.5/forecast` returns the 5-day / 3-hour forecast for those coordinates.
4. **Display** — the JSON is reshaped into a pandas DataFrame, descriptions are title-cased
   with a regex, and the results are rendered as Streamlit metrics and charts (or printed
   as a text report by the CLI).

## Project layout

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit web app — input, metrics, and charts |
| `weather.py` | API calls, input parsing, and the CLI |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Keeps `.env` and caches out of git |

## Troubleshooting

| Message | Fix |
| --- | --- |
| `OPENWEATHER_API_KEY is not set` | Create a `.env` file in the project root and add your key. |
| `API key was rejected` | Double-check the key. Brand-new keys take a little while to activate. |
| `No US city found matching '…'` | Check the spelling, or add a state code: `"Portland, ME"`. |
| `Could not reach OpenWeatherMap` | Check your internet connection. |
| `streamlit: command not found` | Run `pip install -r requirements.txt`, or use `python -m streamlit run app.py`. |
| Port 8501 already in use | Run on another port: `streamlit run app.py --server.port 8502`. |
