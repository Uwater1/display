import yfinance as yf
import pandas as pd
import os
import json
import numpy as np
from datetime import datetime
import warnings

# Suppress FutureWarning from yfinance or pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

from generate_chart import generate_candlestick_chart

TICKERS = ["IVV", "QQQM", "VUG"]
DATA_DIR = "public/data"

def ensure_dirs(ticker):
    os.makedirs(f"{DATA_DIR}/{ticker}/charts", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/{ticker}/csv", exist_ok=True)

def fetch_data(ticker):
    print(f"Fetching data for {ticker}...")
    daily_csv = f"{DATA_DIR}/{ticker}/csv/{ticker}_daily.csv"
    five_min_csv = f"{DATA_DIR}/{ticker}/csv/{ticker}_5m.csv"

    # --- Fetch Daily Data (Max History) ---
    try:
        daily = yf.download(ticker, period="max", interval="1d", progress=False)
        if daily.empty:
            print(f"Warning: No daily data found for {ticker}")
            daily_df = pd.DataFrame()
        else:
            # yfinance returns MultiIndex columns in recent versions, flatten them if needed
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = daily.columns.get_level_values(0)

            daily.reset_index(inplace=True)
            # Ensure Date column exists and is datetime
            if 'Date' in daily.columns:
                daily['Date'] = pd.to_datetime(daily['Date'])

            daily_df = daily
            # Save to CSV
            daily.to_csv(daily_csv, index=False)
            print(f"Saved {daily_csv}")

    except Exception as e:
        print(f"Error fetching daily data for {ticker}: {e}")
        daily_df = pd.DataFrame()

    # --- Fetch 5-minute Data (Last 60 days - max for 5m) ---
    try:
        five_min = yf.download(ticker, period="60d", interval="5m", progress=False)
        if five_min.empty:
             print(f"Warning: No 5m data found for {ticker}")
             five_min_df = pd.DataFrame()
        else:
            if isinstance(five_min.columns, pd.MultiIndex):
                five_min.columns = five_min.columns.get_level_values(0)

            five_min.reset_index(inplace=True)

            # Handle column renaming for 5-min data
            rename_map = {
                "Datetime": "time",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "Volume"
            }
            if 'Date' in five_min.columns and 'Datetime' not in five_min.columns:
                 rename_map['Date'] = 'time'

            five_min.rename(columns=rename_map, inplace=True)
            five_min_df = five_min

            # Save to CSV
            five_min.to_csv(five_min_csv, index=False)
            print(f"Saved {five_min_csv}")

    except Exception as e:
        print(f"Error fetching 5m data for {ticker}: {e}")
        five_min_df = pd.DataFrame()

    return daily_df, five_min_df

def calculate_stats(ticker, df):
    print(f"Calculating stats for {ticker}...")
    if df.empty:
        return {}

    df = df.copy()
    # Ensure sorted by date
    if 'Date' not in df.columns:
         print(f"Error: Date column missing in daily data for {ticker}")
         return {}

    df.sort_values('Date', inplace=True)

    # Intraday Return: (Close - Open) / Open
    df['intraday_return'] = (df['Close'] - df['Open']) / df['Open']

    # Overnight Return: (Open_next - Close) / Close
    # Shift Open backwards to get next day's open on the current row
    df['next_open'] = df['Open'].shift(-1)
    df['overnight_return'] = (df['next_open'] - df['Close']) / df['Close']

    # Drop rows with NaN returns
    df_clean = df.dropna(subset=['intraday_return', 'overnight_return'])

    if df_clean.empty:
        return {}

    # --- Strategies ---

    # Cumulative Returns
    df_clean['intraday_cum'] = (1 + df_clean['intraday_return']).cumprod()
    df_clean['overnight_cum'] = (1 + df_clean['overnight_return']).cumprod()

    stats = {
        "ticker": ticker,
        "strategies": {
            "intraday": {
                "total_return": float(df_clean['intraday_cum'].iloc[-1] - 1),
                "avg_daily_return": float(df_clean['intraday_return'].mean()),
                "win_rate": float((df_clean['intraday_return'] > 0).mean())
            },
            "overnight": {
                "total_return": float(df_clean['overnight_cum'].iloc[-1] - 1),
                "avg_daily_return": float(df_clean['overnight_return'].mean()),
                "win_rate": float((df_clean['overnight_return'] > 0).mean())
            }
        },
        "day_of_week": [],
        "monthly": []
    }

    # --- Day of Week ---
    df_clean['weekday'] = df_clean['Date'].dt.day_name()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    weekday_stats = df_clean.groupby('weekday')[['intraday_return', 'overnight_return']].mean()
    weekday_win_rate = df_clean.groupby('weekday')[['intraday_return', 'overnight_return']].apply(lambda x: (x > 0).mean())

    for day in weekday_order:
        if day in weekday_stats.index:
            stats["day_of_week"].append({
                "day": day,
                "intraday_avg": float(weekday_stats.loc[day, 'intraday_return']),
                "overnight_avg": float(weekday_stats.loc[day, 'overnight_return']),
                "intraday_win_rate": float(weekday_win_rate.loc[day, 'intraday_return']),
                "overnight_win_rate": float(weekday_win_rate.loc[day, 'overnight_return'])
            })

    # --- Monthly ---
    df_clean['month'] = df_clean['Date'].dt.month_name()
    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    monthly_stats = df_clean.groupby('month')[['intraday_return', 'overnight_return']].mean()

    for month in month_order:
        if month in monthly_stats.index:
            stats["monthly"].append({
                "month": month,
                "intraday_avg": float(monthly_stats.loc[month, 'intraday_return']),
                "overnight_avg": float(monthly_stats.loc[month, 'overnight_return'])
            })

    # Save Stats
    with open(f"{DATA_DIR}/stats_{ticker}.json", "w") as f:
        json.dump(stats, f, indent=2)

    return stats

def generate_daily_charts(ticker, df):
    print(f"Generating charts for {ticker}...")
    if df.empty:
        return

    # Ensure time column is datetime
    if 'time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])

    df['date'] = df['time'].dt.date
    unique_dates = df['date'].unique()
    unique_dates = sorted(unique_dates)

    charts_list = []

    for date in unique_dates:
        day_data = df[df['date'] == date].copy()
        if len(day_data) < 10: # Skip incomplete days
            continue

        # Calculate manually for filename
        first_open = day_data['open'].iloc[0]
        last_close = day_data['close'].iloc[-1]
        pct_change = ((last_close - first_open) / first_open) * 100
        pct_str = f"{pct_change:+.2f}%".replace('.', ',').replace('+-', '-')
        weekday = date.strftime('%a')
        date_str = date.strftime('%Y-%m-%d')
        filename = f"{date_str};{weekday}:{pct_str}.svg"
        filepath = f"{DATA_DIR}/{ticker}/charts/{filename}"

        try:
            # generate_chart adds 'date' column too
            generate_candlestick_chart(df=day_data, output_path=filepath)
            charts_list.append({
                "filename": filename,
                "date": date_str,
                "weekday": weekday,
                "change": pct_str.replace(',', '.') # Keep consistent format for JSON
            })
        except Exception as e:
            print(f"Failed to generate chart for {date}: {e}")

    # Save charts.json for this ticker
    # We sort charts by date descending for the viewer
    charts_list.sort(key=lambda x: x['date'], reverse=True)

    with open(f"{DATA_DIR}/charts_{ticker}.json", "w") as f:
        json.dump(charts_list, f, indent=2)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    metadata = {
        "tickers": TICKERS,
        "last_updated": datetime.now().isoformat()
    }

    for ticker in TICKERS:
        ensure_dirs(ticker)
        daily_df, five_min_df = fetch_data(ticker)

        if not daily_df.empty:
            calculate_stats(ticker, daily_df)

        if not five_min_df.empty:
            generate_daily_charts(ticker, five_min_df)

    with open(f"{DATA_DIR}/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("All processing done!")

if __name__ == "__main__":
    main()
