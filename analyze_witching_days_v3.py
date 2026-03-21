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

START_DATE = '2006-09-08'

def get_target_dates(start_year, end_year):
    """Calculates 4th Wednesdays and 3rd Fridays for each month."""
    dates = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # 4th Wednesday (Option Clearing)
            count = 0
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day)
                    if dt.weekday() == 2: # Wednesday
                        count += 1
                        if count == 4:
                            dates.append(('4th_Wed (Option)', dt))
                            break
                except ValueError: break
            
            # 3rd Friday (Future Clearing)
            count = 0
            for day in range(1, 32):
                try:
                    dt = datetime(year, month, day)
                    if dt.weekday() == 4: # Friday
                        count += 1
                        if count == 3:
                            dates.append(('3rd_Fri (Future)', dt))
                            break
                except ValueError: break
    return dates

def load_data(file_path):
    """Robustly loads CSV files with different header formats."""
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
    df = df[df['Date'] >= START_DATE] # Filter after CFFEX opening
    df = df.sort_values('Date').reset_index(drop=True)
    df['Return'] = df['Close'].pct_change()
    return df

def analyze():
    dist_stats = []
    
    for name, path in FILES.items():
        if not os.path.exists(path): continue
        df = load_data(path)
        trading_dates = sorted(df['Date'].unique())
        trading_dates_set = set(trading_dates)
        
        start_year, end_year = df['Date'].dt.year.min(), df['Date'].dt.year.max()
        target_dates = get_target_dates(start_year, end_year)
        
        # Collect baseline all days
        all_rets = df['Return'].dropna()
        
        # Collect witching days
        witching_rets = []
        for type_name, dt in target_dates:
            actual_dt = dt
            while actual_dt not in trading_dates_set and actual_dt <= trading_dates[-1]:
                actual_dt += timedelta(days=1)
            
            if actual_dt in trading_dates_set:
                ret = df[df['Date'] == actual_dt]['Return'].values[0]
                if not np.isnan(ret):
                    witching_rets.append({'Type': type_name, 'Return': ret})
        
        w_df = pd.DataFrame(witching_rets)
        
        # Statistics compilation
        # All Days
        all_stats = all_rets.describe()
        dist_stats.append({
            'Index': name, 'Period': 'All Trading Days',
            'Mean (%)': all_stats['mean'] * 100,
            'Std (%)': all_stats['std'] * 100,
            'Min (%)': all_stats['min'] * 100,
            '25% (%)': all_stats['25%'] * 100,
            '50% (%)': all_stats['50%'] * 100,
            '75% (%)': all_stats['75%'] * 100,
            'Max (%)': all_stats['max'] * 100,
            'WinRate (%)': (all_rets > 0).mean() * 100,
            'Count': int(all_stats['count'])
        })
        
        # Specific Witching Days
        for t in w_df['Type'].unique():
            t_rets = w_df[w_df['Type'] == t]['Return']
            t_stats = t_rets.describe()
            dist_stats.append({
                'Index': name, 'Period': t,
                'Mean (%)': t_stats['mean'] * 100,
                'Std (%)': t_stats['std'] * 100,
                'Min (%)': t_stats['min'] * 100,
                '25% (%)': t_stats['25%'] * 100,
                '50% (%)': t_stats['50%'] * 100,
                '75% (%)': t_stats['75%'] * 100,
                'Max (%)': t_stats['max'] * 100,
                'WinRate (%)': (t_rets > 0).mean() * 100,
                'Count': int(t_stats['count'])
            })
            
    return pd.DataFrame(dist_stats)

if __name__ == "__main__":
    results = analyze()
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print("\n=== Performance Distribution Analysis (Post 2006-09-08) ===")
    print(results.round(4))
    
    # Save to CSV for the user
    results.to_csv('/home/hallo/Documents/display/witching_day_distribution.csv', index=False)
    print(f"\nDistribution analysis saved to: /home/hallo/Documents/display/witching_day_distribution.csv")
