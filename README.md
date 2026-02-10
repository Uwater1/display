# Stock Chart Generator & Viewer

**Live Demo**: https://Uwater1.github.io/display/

A toolkit for generating 5-minute candlestick charts from OHLCV CSV data, downloading stock & options data, running market analysis, and browsing results in an interactive web viewer.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate a chart
python generate_chart.py example.csv

# View locally
cd public && python -m http.server 8000
```

## Features

### Chart Generation (`generate_chart.py`)
- 5-minute candlestick charts saved as SVG
- EMA20 overlay and gap markers
- Smart file naming with date and percentage change
- Green/red candlesticks with ▲/▼ indicators

### Web Viewer (`public/`)
- Interactive SVG chart browser with pagination
- Keyboard navigation (A/D or arrow keys)
- URL sharing for specific charts
- Statistics page with analysis plots
- Day-trading statistics page
- Responsive design

### Data Download
- **`data_downloader.py`** — Downloads stock OHLCV data via `yfinance` at various intervals (1m, 5m, 15m, 1h, 1d). Supports multiple tickers, custom date ranges, and max-range daily data.
- **`download_options_improved.py`** — Downloads option chains (calls & puts) for major ETFs (QQQ, SPY, IWM, DIA, GLD, TLT). Computes Black-Scholes implied volatility using a vectorized Newton-Raphson + bisection solver. Caches intraday price data and stores values as float32 for efficiency.
- **`download_options.yml`** — GitHub Actions workflow config for scheduled daily options downloads.

### Analysis Tools
- **`day-vs-night.py`** — Intraday vs overnight vs buy-and-hold strategy comparison (IVV, QQQM, VUG).
- **`weekday_analysis.py`** — Day-of-week return patterns.
- **`monthly_analysis.py`** — Month-of-year return patterns.
- **`extended_stats.py`** — Sell-in-May analysis, volatility comparison, ETF correlation matrix, QQQ 5-min intraday patterns.
- **`qqq_daytrading_stats.py`** — Day-trading statistics analyzer: high/low bar timing, opening gap distribution, range location, first-hour performance, high-low sequencing. Generates detailed PNG plots with `-p` flag.

### Utilities
- **`spilt.py`** — Splits 5-minute CSV data into 2-trading-day chunks with date-based filenames.
- **`scripts/generate_index.py`** — Builds `charts.json` index for the web viewer.

## Usage

### Generate Charts
```bash
python generate_chart.py data.csv
python generate_chart.py data.csv --output chart.svg
```

### Download Data
```bash
# Download 5-minute data for tickers (default: 59 days)
python data_downloader.py QQQ SPY AAPL

# Download daily data (max range)
python data_downloader.py QQQ --interval 1d

# Custom date range
python data_downloader.py QQQ --interval 5m --start 2026-01-01 --end 2026-02-01
```

### Download Options
```bash
python download_options_improved.py
```

### Run Analysis
```bash
# Intraday vs overnight vs buy & hold
python day-vs-night.py         # text only
python day-vs-night.py -p      # with plots

# Weekly / monthly patterns
python weekday_analysis.py -p
python monthly_analysis.py -p

# Extended stats (sell-in-may, volatility, correlation, intraday pattern)
python extended_stats.py -p

# Day-trading statistics
python qqq_daytrading_stats.py qqq5m.csv -p
```

### Split CSV
```bash
python spilt.py qqq5m.csv --output-dir public/data
```

### Rebuild Chart Index
```bash
python scripts/generate_index.py
```

## CSV Format

Required columns for chart generation: `time`, `open`, `high`, `low`, `close`, `Volume`

## Project Structure

```
display/
├── README.md
├── requirements.txt
├── LICENSE
│
├── generate_chart.py            # SVG candlestick chart generator
├── data_downloader.py           # Stock OHLCV data downloader (yfinance)
├── download_options_improved.py # Options chain downloader with BS IV
├── download_options.yml         # GitHub Actions workflow for options
│
├── day-vs-night.py              # Intraday vs overnight strategy comparison
├── weekday_analysis.py          # Day-of-week return analysis
├── monthly_analysis.py          # Month-of-year return analysis
├── extended_stats.py            # Extended stats & correlations 
├── qqq_daytrading_stats.py      # Day-trading statistics analyzer
│
├── spilt.py                     # CSV splitter (2-day chunks)
├── test_read.py                 # Quick CSV read test
│
├── data/                        # Downloaded stock data (CSVs)
├── options_data/                # Downloaded options data (by date)
├── example.csv                  # Sample 5-minute OHLCV data
├── qqq5m.csv                    # QQQ 5-minute bar data
│
├── public/                      # Web viewer (GitHub Pages)
│   ├── index.html               # Landing page
│   ├── chart.html               # Chart viewer page
│   ├── statistic.html           # Statistics page
│   ├── daystat.html             # Day-trading stats page
│   ├── app.js                   # Chart viewer logic
│   ├── statistic.js             # Statistics page logic
│   ├── daystat.js               # Day-stat page logic
│   ├── styles.css               # Shared stylesheet
│   ├── charts.json              # Chart index (auto-generated)
│   └── data/                    # SVG charts & stat images
│
├── scripts/
│   └── generate_index.py        # Builds charts.json
│
└── .github/
    └── workflows/
        └── deploy.yml           # GitHub Pages deployment
```

## Dependencies

- `pandas` ≥ 1.5.0
- `pandas-ta` ≥ 0.3.14b
- `yfinance` (data download)
- `numpy`, `scipy` (options IV calculation)
- `matplotlib` (analysis plots)

## License

This project is licensed under the AGPL License — see the [LICENSE](LICENSE) file for details.
