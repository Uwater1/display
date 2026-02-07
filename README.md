# Stock Chart Generator & Viewer

**Live Demo**: https://Uwater1.github.io/display/

A Python tool that generates 5-minute candlestick charts from OHLCV CSV data with an interactive web viewer.

## Quick Start

```bash
# Generate a chart
python generate_chart.py example.csv

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

## Usage

### Core Operations
```bash
# Generate chart
python generate_chart.py data.csv

# Custom output
python generate_chart.py data.csv --output chart.svg

## CSV Format
Required columns: `time`, `open`, `high`, `low`, `close`, `Volume`
```

### Analysis Tools
```bash
# Compare Intraday vs Overnight vs Buy & Hold
python strategy_comparison.py

# Run weekly performance analysis
python weekday_analysis.py

# Run monthly performance analysis
python monthly_analysis.py

# Show extended stats (Correlations, Seasonality, patterns)
python extended_stats.py
```

## Files
- `generate_chart.py` - Main script
- `public/` - Web viewer
- `example.csv` - Sample data

## Lisence

This project is licensed under the AGNU License - see the [LICENSE](LICENSE) file for details.
