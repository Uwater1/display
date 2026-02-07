# Stock Chart Generator & Viewer

**Live Demo**: https://Uwater1.github.io/display/

A Python tool that generates 5-minute candlestick charts from OHLCV CSV data with an interactive web viewer.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch data and generate charts
python fetch_and_process.py

# View locally
cd public && python -m http.server 8000
```

## Features

### Chart Generation
- 5-minute candlestick charts with volume bars
- EMA20 line and gap markers
- Smart naming with date and percentage change
- Green/red candlesticks with ▲/▼ indicators

### Web Viewer
- Interactive SVG chart browser with pagination
- Keyboard navigation (A/D or arrow keys)
- URL sharing for specific charts
- Responsive design
- **New**: Statistics dashboard for Intraday vs Overnight returns
- **New**: Day of Week and Monthly performance analysis
- **New**: Ticker selection (IVV, QQQM, VUG)

## Usage

```bash
# Fetch data for configured tickers (IVV, QQQM, VUG)
python fetch_and_process.py

# Generate single chart manually
python generate_chart.py data.csv --output chart.svg
```

## CSV Format (for manual chart generation)
Required columns: `time`, `open`, `high`, `low`, `close`, `Volume`

## Files
- `fetch_and_process.py` - Main data fetching and processing script
- `generate_chart.py` - Chart generation module
- `public/` - Web viewer frontend
- `example.csv` - Sample data

## License

This project is licensed under the AGNU License - see the [LICENSE](LICENSE) file for details.
