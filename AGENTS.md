# AGENTS.md

Compact guide for OpenCode sessions working in this repo. Repo = stock/options data toolkit + static GitHub Pages viewer (`public/`). Branch: `main`.

## Python env

- Try `source venv/bin/activate`. If missing: `rtk uv venv`, activate, `rtk uv pip install -r requirements.txt`.
- `requirements.txt` is INCOMPLETE — declares only `pandas`, `pandas-ta`. Most scripts also import `numpy`, `scipy`, `matplotlib`, `yfinance`. Install extras manually as needed; add new deps to `requirements.txt`.
- Run all scripts from repo root. Paths like `data/IVV_1d.csv` are hardcoded relative to CWD.

## No tests / lint / typecheck

- No test suite, no pytest, no lint, no formatter, no typecheck. Do not invent commands.
- `test_read.py` is a one-off CSV sanity check, not a test runner.
- Verify changes by executing the affected script directly with a real CSV input.

## Two CSV formats — do not mix

- **yfinance daily exports** (`data/*_1d.csv`, e.g. `IVV_1d.csv`, `QQQM_1d.csv`, `^VIX_1d.csv`): two junk rows after header. Must read with `pd.read_csv(path, skiprows=[1, 2])` then `rename(columns={'Price': 'Date'})`. Every analysis script (`day-vs-night.py`, `extended_stats.py`, `weekday_analysis.py`, `monthly_analysis.py`) does this. New scripts reading daily data must do the same or rows shift.
- **Intraday 5-minute CSVs** (`data/QQQ5m.csv`, root `qqq5m.csv`, `qqq2.csv`, `example.csv`): columns `time,open,high,low,close,Volume`. No skiprows.

## README command examples are WRONG in places

Trust the script's own argparse, not the README:

- `data_downloader.py`: interval is **positional and required, comes after tickers**. Correct: `python data_downloader.py QQQ 5m`. README's `python data_downloader.py QQQ --interval 5m` fails.
- `spilt.py`: flag is `--output`, NOT `--output-dir` (README wrong).
- `generate_chart.py`: default input is `qqq5m.csv` (not `example.csv`). Output SVG name auto-derived from last candle date + pct change.
- `qqq_daytrading_stats.py`: takes NO positional arg, hardcodes `data/QQQ5m.csv`. Only flag is `-p`. README's `python qqq_daytrading_stats.py qqq5m.csv -p` errors (unrecognized arg).
- `data_downloader.py`: date flags are `--start-date` / `--end-date` (with hyphen), NOT `--start` / `--end`.

## Adding a chart to the viewer

Frontend (`public/app.js`) fetches `charts.json` then `data/chart/<filename>` relative to `public/`. CI does NOT regenerate the index. Full pipeline:

1. `python generate_chart.py <csv> [--output X.svg]` → produces SVG.
2. Copy SVG into BOTH `data/chart/` AND `public/data/chart/` (frontend only reads the latter; index generator only scans the former).
3. `python scripts/generate_index.py` → rewrites `public/charts.json` from `data/chart/`.
4. Commit `public/charts.json` + both SVG copies.

**Filename format is strict**: `YYYY-MM-DD;Day:+X,XX%.svg` (semicolon separators, comma as decimal). Examples: `2024-02-13;Tue:+0,29%.svg`. `generate_index.py` regex-parses this; non-matching files are silently skipped and will never appear in viewer.

`CHART_DIR` and `OUTPUT_FILE` env vars override defaults.

## Deploy

`.github/workflows/deploy.yml` runs on push to `main`: uploads `public/` to GitHub Pages. It does NOT run `generate_index.py` — index must be committed already. Live URL: `https://Uwater1.github.io/display/`.

`download_options.yml` at repo ROOT is **inactive** (not under `.github/workflows/`). It also calls the older `download_options.py`, not `download_options_improved.py`. Only `deploy.yml` actually runs in CI.

## No .gitignore

Large CSVs, parquet, and SVGs are committed directly. `data/` and `public/data/` hold many MB of tracked data. Do not dump large new datasets without intent; do not `git add` blindly.

## Repo layout shortcuts

- `generate_chart.py` — SVG candlestick generator (entry point for new charts).
- `generate_etf_stats.py` — Runs morning gap, fill rate, return distribution, daytrading pattern, and liquidity analyses on 5 ETF Parquet files and CSI 800 CSV files. Saves PNG plots to `public/data/daystata/<asset_key>/`.
- `data_downloader.py` — yfinance OHLCV downloader.
- `download_options_improved.py` — options chains + Black-Scholes IV (preferred over `download_options.py`).
- `spilt.py` — splits 5m CSV into 2-trading-day chunks.
- `scripts/generate_index.py` — rebuilds `public/charts.json`.
- `public/` — static viewer (HTML/JS/CSS), deployed as-is to Pages. `data/chart/` mirror lives at `public/data/chart/`.
- `data/` — source datasets. `*_1d.csv` daily (skiprows), `QQQ5m.csv` intraday, `*.parquet` Chinese ETF 5m.
- `day.ipynb` — exploration notebook.

## ETF & Index Day Trading Statistics (Day-Stat-A)

- Parquet files (`data/*_5m.parquet`) contain 5-minute bar data for Chinese ETFs.
- `data/800.csv` and `data/hs300_zz500_sum.csv` contain data for the CSI 800 Index.
- `python generate_etf_stats.py` reads these datasets, calculates 22 statistics (including daytrading patterns, liquidity analysis, and trend following streaks), and outputs PNG plots to `public/data/daystata/<asset_key>/` (keys: `sse50`, `csi300`, `csi500`, `chinext`, `star50`, `csi800`).
- Frontend `public/daystata.html` and `public/daystata.js` display all 22 charts consistently for all 6 assets. URL parameter `a` tracks the active asset, `i` tracks the chart index.


## Conventions

- Shell: prefix commands with `rtk` (e.g. `rtk git status`).
- Responses: caveman-terse, technical substance intact.
- Don't commit unless explicitly asked.

