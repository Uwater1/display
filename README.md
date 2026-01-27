# Stock Chart Generator

A Python tool that generates 5-minute candlestick charts from OHLCV (Open, High, Low, Close, Volume) CSV data. Charts are saved as optimized SVG files.

## Features

- **Candlestick Charts**: Displays 5-minute candlestick bars with wicks and bodies
- **Volume Bars**: Shows trading volume below the price chart
- **EMA20 Line**: Plots the 20-period Exponential Moving Average
- **Gap Markers**: Highlights overnight gaps between trading sessions
- **Smart Output Naming**: Files are saved with date and percentage change (e.g., `2024-02-13:-0.13%.svg`)
- **Percentage Display**: Shows grow/fall indicator (▲/▼) with percentage change directly on the chart

## Usage
### Specify input file:

```bash
python generate_chart.py example.csv
```

### Specify output file:

```bash
python generate_chart.py data.csv --output custom_chart.svg
```

## Output Format

When no output path is specified, the chart is saved with the format:
```
YYYY-MM-DD:±X.XX%.svg
```

For example:
- `2024-02-13:+0.45%.svg` - Last trading day up 0.45%
- `2024-02-13:-0.13%.svg` - Last trading day down 0.13%

## CSV Format

Input CSV files should have the following columns:
- `time` - Timestamp (e.g., "2024-02-13 09:30:00")
- `open` - Opening price
- `high` - High price
- `low` - Low price
- `close` - Closing price
- `Volume` - Trading volume

## Chart Display

The chart shows:
- **Green candlesticks** (▲) indicate price increased (close > open)
- **Red candlesticks** (▼) indicate price decreased (close < open)
- **EMA20** as a blue line
- **Percentage change** of the last trading day in the top-right corner with ▲ (up) or ▼ (down) symbol

## Files

- `generate_chart.py` - Main script
- `spilt.py` - Utility script
- `qqq5m.csv` - Sample data (QQQ 5-minute data)
- `example.csv` - Example input file
