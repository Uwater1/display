# Stock Chart Generator & Viewer

A Python tool that generates 5-minute candlestick charts from OHLCV (Open, High, Low, Close, Volume) CSV data. Charts are saved as optimized SVG files. Includes a web viewer for browsing generated charts.

## Web Viewer Features

The included web viewer (`public/`) provides an interactive interface for browsing generated stock charts:

- **SVG Chart Viewer with Pagination**: Browse through all generated charts with easy navigation
- **Keyboard Navigation**: Use `A`/`D` keys or arrow keys (←/→) to navigate between charts
- **URL State for Sharing**: URL updates automatically to include the current chart index, allowing you to share direct links to specific charts
- **Responsive Design**: Works seamlessly on desktop and mobile devices

**Live Demo**: Replace `https://<username>.github.io/<repo>` with your actual GitHub Pages URL

## Deployment

### Deploy to GitHub Pages

1. Fork or clone this repository
2. Go to **Settings** → **Pages**
3. Under **Source**, select "GitHub Actions"
4. Run the **Deploy to GitHub Pages** workflow:
   - Navigate to **Actions** → **Deploy to GitHub Pages**
   - Click **Run workflow** → **Run workflow**
5. Once deployed, access your charts at:
   `https://<username>.github.io/<repo>/`

### Local Development

```bash
# Generate charts.json from existing SVG files
python scripts/generate_index.py

# Serve the public directory locally
cd public && python -m http.server 8000
```

## Features

### Chart Generation

- **Candlestick Charts**: Displays 5-minute candlestick bars with wicks and bodies
- **Volume Bars**: Shows trading volume below the price chart
- **EMA20 Line**: Plots the 20-period Exponential Moving Average
- **Gap Markers**: Highlights overnight gaps between trading sessions
- **Smart Output Naming**: Files are saved with date and percentage change (e.g., `2024-02-13:-0.13%.svg`)
- **Percentage Display**: Shows grow/fall indicator (▲/▼) with percentage change directly on the chart

## Usage

### Generate Charts

Specify input file:

```bash
python generate_chart.py example.csv
```

Specify output file:

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

- `generate_chart.py` - Main chart generation script
- `spilt.py` - Utility script
- `qqq5m.csv` - Sample data (QQQ 5-minute data)
- `example.csv` - Example input file
- `public/` - Web viewer files
  - `index.html` - Main viewer page
  - `app.js` - Viewer application logic
  - `styles.css` - Viewer styles
