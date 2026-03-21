import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Configuration: Index data files
FILES = {
    'SZ50 (SSE 50)': '/home/hallo/Documents/display/data/sz50_1d.csv',
    'HS300 (CSI 300)': '/home/hallo/Documents/display/data/hs300_1d.csv',
    'ZZ1000 (CSI 1000)': '/home/hallo/Documents/display/data/zz1000_1d.csv'
}

START_DATE = '2014-09-08'

def get_target_dates(start_year, end_year):
    """Calculates 4th Wednesdays and 3rd Fridays."""
    dates = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # 4th Wednesday
            count = 0
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day)
                    if dt.weekday() == 2:
                        count += 1
                        if count == 4:
                            dates.append(('4th_Wed (Option)', dt))
                            break
                except ValueError: break
            # 3rd Friday
            count = 0
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day)
                    if dt.weekday() == 4:
                        count += 1
                        if count == 3:
                            dates.append(('3rd_Fri (Future)', dt))
                            break
                except ValueError: break
    return dates

def load_data(file_path):
    with open(file_path, 'r') as f:
        first_line = f.readline()
    if first_line.startswith('Price,Close'):
        df = pd.read_csv(file_path, skiprows=3, names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
    elif first_line.startswith('time,open'):
        df = pd.read_csv(file_path)
        df = df.rename(columns={'time': 'Date', 'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'})
    else:
        df = pd.read_csv(file_path)
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower(): df = df.rename(columns={col: 'Date'})
            if 'close' in col.lower(): df = df.rename(columns={col: 'Close'})
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Date'] >= START_DATE]
    df = df.sort_values('Date').reset_index(drop=True)
    df['Return'] = df['Close'].pct_change()
    return df

def get_bucket_stats(rets):
    """Calculates custom probability buckets for returns."""
    if rets.empty:
        return {}
    return {
        'Count': int(len(rets)),
        'Mean (%)': rets.mean() * 100,
        'Std (%)': rets.std() * 100,
        'WinRate (%)': (rets > 0).mean() * 100,
        '< -2% (%)': (rets < -0.02).mean() * 100,
        '< -1% (%)': (rets < -0.01).mean() * 100,
        '> 1% (%)': (rets > 0.01).mean() * 100,
        '> 2% (%)': (rets > 0.02).mean() * 100,
        '|x| < 0.5% (%)': ((rets > -0.005) & (rets < 0.005)).mean() * 100
    }

def analyze():
    all_rows = []
    for name, path in FILES.items():
        if not os.path.exists(path): continue
        df = load_data(path)
        trading_dates = sorted(df['Date'].unique())
        trading_dates_set = set(trading_dates)
        
        target_dates = get_target_dates(df['Date'].dt.year.min(), df['Date'].dt.year.max())
        all_rets = df['Return'].dropna()
        
        # Baseline
        stats = get_bucket_stats(all_rets)
        stats['Index'] = name
        stats['Period'] = 'All Trading Days'
        all_rows.append(stats)
        
        # Target Days
        witching_data = []
        for type_name, dt in target_dates:
            actual_dt = dt
            while actual_dt not in trading_dates_set and actual_dt <= trading_dates[-1]:
                actual_dt += timedelta(days=1)
            if actual_dt in trading_dates_set:
                ret = df[df['Date'] == actual_dt]['Return'].values[0]
                if not np.isnan(ret):
                    witching_data.append({'Type': type_name, 'Return': ret})
        
        w_df = pd.DataFrame(witching_data)
        for t in w_df['Type'].unique():
            t_rets = w_df[w_df['Type'] == t]['Return']
            t_stats = get_bucket_stats(t_rets)
            t_stats['Index'] = name
            t_stats['Period'] = t
            all_rows.append(t_stats)
            
    return pd.DataFrame(all_rows)

if __name__ == "__main__":
    results = analyze()
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print("\n=== Custom Bucket Distribution Analysis (Post 2006-09-08) ===")
    cols = ['Index', 'Period', 'Count', 'Mean (%)', 'WinRate (%)', '< -2% (%)', '< -1% (%)', '> 1% (%)', '> 2% (%)', '|x| < 0.5% (%)']
    print(results[cols].round(2))
    
    results.to_csv('/home/hallo/Documents/display/witching_day_custom_buckets.csv', index=False)
