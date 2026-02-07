import yfinance as yf
import pandas as pd
import os
import json
import numpy as np
from datetime import datetime
import warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import BDay

# Suppress FutureWarning from yfinance or pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

from generate_chart import generate_candlestick_chart

TICKERS = ["IVV", "QQQM", "VUG"]
DATA_DIR = "public/data"

# Matplotlib style
plt.style.use('dark_background')
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#36A2EB', '#FF6384', '#4BC0C0', '#FF9F40', '#9966FF', '#FFCD56'])

def ensure_dirs(ticker):
    os.makedirs(f"{DATA_DIR}/{ticker}/charts", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/{ticker}/csv", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/{ticker}/stats", exist_ok=True)

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
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = daily.columns.get_level_values(0)

            daily.reset_index(inplace=True)
            if 'Date' in daily.columns:
                daily['Date'] = pd.to_datetime(daily['Date'])

            daily_df = daily
            daily.to_csv(daily_csv, index=False)
            print(f"Saved {daily_csv}")

    except Exception as e:
        print(f"Error fetching daily data for {ticker}: {e}")
        daily_df = pd.DataFrame()

    # --- Fetch 5-minute Data (Last 60 days) ---
    try:
        five_min = yf.download(ticker, period="60d", interval="5m", progress=False)
        if five_min.empty:
             print(f"Warning: No 5m data found for {ticker}")
             five_min_df = pd.DataFrame()
        else:
            if isinstance(five_min.columns, pd.MultiIndex):
                five_min.columns = five_min.columns.get_level_values(0)

            five_min.reset_index(inplace=True)

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
            five_min.to_csv(five_min_csv, index=False)
            print(f"Saved {five_min_csv}")

    except Exception as e:
        print(f"Error fetching 5m data for {ticker}: {e}")
        five_min_df = pd.DataFrame()

    return daily_df, five_min_df

def plot_bar_chart(x, y, title, xlabel, ylabel, filename, color=None):
    fig, ax = plt.subplots()
    bars = ax.bar(x, y, color=color)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}%',
                ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def plot_multi_bar_chart(labels, data_dict, title, ylabel, filename):
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots()
    multiplier = 0

    for attribute, measurement in data_dict.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        multiplier += 1

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x + width / 2 * (len(data_dict) - 1))
    ax.set_xticklabels(labels)
    ax.set_ylabel(ylabel)
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def plot_line_chart(x, y_dict, title, xlabel, ylabel, filename):
    fig, ax = plt.subplots()

    for label, y_values in y_dict.items():
        ax.plot(x, y_values, label=label, linewidth=2)

    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Format x-axis dates if needed
    if len(x) > 0 and isinstance(x.iloc[0], datetime):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def calculate_stats(ticker, df):
    print(f"Calculating stats for {ticker}...")
    if df.empty:
        return {}

    df = df.copy()
    if 'Date' not in df.columns:
         return {}
    df.sort_values('Date', inplace=True)

    # Returns
    df['intraday_return'] = (df['Close'] - df['Open']) / df['Open']
    df['next_open'] = df['Open'].shift(-1)
    df['overnight_return'] = (df['next_open'] - df['Close']) / df['Close']
    df['daily_return'] = (df['Close'] - df['Close'].shift(1)) / df['Close'].shift(1) # Buy & Hold

    df_clean = df.dropna(subset=['intraday_return', 'overnight_return', 'daily_return']).copy()
    if df_clean.empty:
        return {}

    stats_dir = f"{DATA_DIR}/{ticker}/stats"
    manifest = []

    # 1. Strategies Total Return (Bar Chart)
    total_intra = ((1 + df_clean['intraday_return']).prod() - 1) * 100
    total_over = ((1 + df_clean['overnight_return']).prod() - 1) * 100
    total_hold = ((1 + df_clean['daily_return']).prod() - 1) * 100

    plot_bar_chart(
        ['Intraday', 'Overnight', 'Buy & Hold'],
        [total_intra, total_over, total_hold],
        f"{ticker} Total Return by Strategy",
        "Strategy", "Total Return (%)",
        f"{stats_dir}/total_return.png",
        color=['#36A2EB', '#FF6384', '#4BC0C0']
    )
    manifest.append({
        "id": "total_return",
        "title": "Total Return Comparison",
        "description": "Compares the total cumulative return of three strategies: Intraday (Open to Close), Overnight (Close to Next Open), and Buy & Hold (Close to Close) over the entire available history.",
        "image": f"data/{ticker}/stats/total_return.png"
    })

    # 2. Average Return by Day of Week (Multi-Bar)
    df_clean['weekday'] = df_clean['Date'].dt.day_name()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    avg_intra_day = []
    avg_over_day = []

    for day in days:
        day_data = df_clean[df_clean['weekday'] == day]
        avg_intra_day.append(day_data['intraday_return'].mean() * 100)
        avg_over_day.append(day_data['overnight_return'].mean() * 100)

    plot_multi_bar_chart(
        days,
        {"Intraday": avg_intra_day, "Overnight": avg_over_day},
        f"{ticker} Average Return by Day of Week",
        "Average Return (%)",
        f"{stats_dir}/avg_return_weekday.png"
    )
    manifest.append({
        "id": "avg_return_weekday",
        "title": "Average Return by Day of Week",
        "description": "Shows the average daily return for each day of the week, broken down by Intraday and Overnight sessions.",
        "image": f"data/{ticker}/stats/avg_return_weekday.png"
    })

    # 3. Win Rate by Day of Week (Multi-Bar)
    win_intra_day = []
    win_over_day = []

    for day in days:
        day_data = df_clean[df_clean['weekday'] == day]
        win_intra_day.append((day_data['intraday_return'] > 0).mean() * 100)
        win_over_day.append((day_data['overnight_return'] > 0).mean() * 100)

    plot_multi_bar_chart(
        days,
        {"Intraday": win_intra_day, "Overnight": win_over_day},
        f"{ticker} Win Rate by Day of Week",
        "Win Rate (%)",
        f"{stats_dir}/win_rate_weekday.png"
    )
    manifest.append({
        "id": "win_rate_weekday",
        "title": "Win Rate by Day of Week",
        "description": "The percentage of days where the return was positive, categorized by day of the week and session.",
        "image": f"data/{ticker}/stats/win_rate_weekday.png"
    })

    # 4. Monthly Seasonality (Bar)
    df_clean['month'] = df_clean['Date'].dt.month_name()
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    avg_monthly = []

    for month in months:
        month_data = df_clean[df_clean['month'] == month]
        avg_monthly.append(month_data['daily_return'].mean() * 100) # Using daily return for seasonality

    plot_bar_chart(
        [m[:3] for m in months], # Short names
        avg_monthly,
        f"{ticker} Average Daily Return by Month (Seasonality)",
        "Month", "Avg Daily Return (%)",
        f"{stats_dir}/monthly_seasonality.png",
        color='#9966FF'
    )
    manifest.append({
        "id": "monthly_seasonality",
        "title": "Monthly Seasonality",
        "description": "Average daily return for each month of the year, indicating potential seasonal trends.",
        "image": f"data/{ticker}/stats/monthly_seasonality.png"
    })

    # 5. Cumulative Returns (Line)
    df_clean['cum_intra'] = (1 + df_clean['intraday_return']).cumprod()
    df_clean['cum_over'] = (1 + df_clean['overnight_return']).cumprod()
    df_clean['cum_hold'] = (1 + df_clean['daily_return']).cumprod()

    plot_line_chart(
        df_clean['Date'],
        {
            "Buy & Hold": df_clean['cum_hold'],
            "Intraday": df_clean['cum_intra'],
            "Overnight": df_clean['cum_over']
        },
        f"{ticker} Cumulative Growth of $1",
        "Date", "Growth Factor",
        f"{stats_dir}/cumulative_growth.png"
    )
    manifest.append({
        "id": "cumulative_growth",
        "title": "Cumulative Growth Comparison",
        "description": "Growth of a hypothetical $1 investment over time for Buy & Hold, Intraday, and Overnight strategies.",
        "image": f"data/{ticker}/stats/cumulative_growth.png"
    })

    # 6. Rolling Volatility (Line)
    # 30-day rolling std dev annualized (approx sqrt(252))
    roll_intra = df_clean['intraday_return'].rolling(window=30).std() * np.sqrt(252) * 100
    roll_over = df_clean['overnight_return'].rolling(window=30).std() * np.sqrt(252) * 100

    plot_line_chart(
        df_clean['Date'],
        {"Intraday": roll_intra, "Overnight": roll_over},
        f"{ticker} 30-Day Rolling Volatility (Annualized)",
        "Date", "Volatility (%)",
        f"{stats_dir}/rolling_volatility.png"
    )
    manifest.append({
        "id": "rolling_volatility",
        "title": "Rolling Volatility",
        "description": "30-day rolling standard deviation of returns (annualized), showing how risk/volatility changes over time for each session.",
        "image": f"data/{ticker}/stats/rolling_volatility.png"
    })

    # Save Manifest
    with open(f"{DATA_DIR}/{ticker}/stats_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

def generate_daily_charts(ticker, df):
    print(f"Generating charts for {ticker}...")
    if df.empty:
        return

    if 'time' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])

    df['date'] = df['time'].dt.date
    unique_dates = sorted(df['date'].unique())

    charts_list = []

    for date in unique_dates:
        day_data = df[df['date'] == date].copy()
        if len(day_data) < 10:
            continue

        first_open = day_data['open'].iloc[0]
        last_close = day_data['close'].iloc[-1]
        pct_change = ((last_close - first_open) / first_open) * 100
        pct_str = f"{pct_change:+.2f}%".replace('.', ',').replace('+-', '-')
        weekday = date.strftime('%a')
        date_str = date.strftime('%Y-%m-%d')
        filename = f"{date_str};{weekday}:{pct_str}.svg"
        filepath = f"{DATA_DIR}/{ticker}/charts/{filename}"

        try:
            generate_candlestick_chart(df=day_data, output_path=filepath)
            charts_list.append({
                "filename": filename,
                "date": date_str,
                "weekday": weekday,
                "change": pct_str.replace(',', '.')
            })
        except Exception as e:
            print(f"Failed to generate chart for {date}: {e}")

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
