import pandas as pd
import numpy as np
from datetime import time

def get_session(t):
    if t < time(10, 30):
        return "Morning (09:30-10:30)"
    elif t < time(14, 30):
        return "Mid-day (10:30-14:30)"
    else:
        return "Afternoon (14:30-16:00)"

def get_bucket(gap):
    abs_gap = abs(gap)
    if abs_gap < 0.1:
        return "Tiny (0.05-0.1)"
    elif abs_gap < 0.2:
        return "Small (0.1-0.2)"
    else:
        return "Large (>0.2)"

def analyze_advanced_gaps(file_path):
    df = pd.read_csv(file_path)
    # Convert to datetime and then to US/Eastern to handle sessions correctly
    df['time_dt'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert('US/Eastern')
    df['date'] = df['time_dt'].dt.date
    df['time_only'] = df['time_dt'].dt.time
    
    # Intraday gap
    df['prev_close'] = df.groupby('date')['close'].shift(1)
    df['gap'] = df['open'] - df['prev_close']
    
    # Filter for significant gaps (>= 0.05)
    sig_gaps = df[df['gap'].abs() >= 0.05].copy()
    
    horizons = [1, 3, 5, 10]
    trades = []

    for idx, row in sig_gaps.iterrows():
        current_date = row['date']
        gap_val = row['gap']
        session = get_session(row['time_only'])
        bucket = get_bucket(gap_val)
        direction = "Long" if gap_val > 0 else "Short"
        
        for h in horizons:
            if idx + h < len(df) and df.iloc[idx + h]['date'] == current_date:
                # Entry: Open of next bar
                entry_price = df.iloc[idx + 1]['open']
                exit_price = df.iloc[idx + h]['close']
                
                # Window for MAE/MFE
                window = df.iloc[idx + 1 : idx + h + 1]
                highs = window['high']
                lows = window['low']
                
                if direction == "Long":
                    trade_ret = exit_price - entry_price
                    mfe = lows.max() - entry_price # Max profit reached
                    mae = entry_price - lows.min() # Max drawdown
                    # Correcting MFE logic: it should be high for long
                    mfe = highs.max() - entry_price
                else:
                    trade_ret = entry_price - exit_price
                    mfe = entry_price - lows.min()
                    mae = highs.max() - entry_price

                trades.append({
                    'Session': session,
                    'Bucket': bucket,
                    'Dir': direction,
                    'Horizon': h,
                    'Return': trade_ret,
                    'MAE': mae,
                    'MFE': mfe
                })

    trades_df = pd.DataFrame(trades)
    
    if trades_df.empty:
        print("No trades found matching criteria.")
        return

    # Aggregate by Session, Bucket, Horizon
    summary = trades_df.groupby(['Session', 'Bucket', 'Horizon']).agg(
        Count=('Return', 'count'),
        WinRate=('Return', lambda x: (x > 0).mean() * 100),
        MeanRet=('Return', 'mean'),
        AvgMAE=('MAE', 'mean'),
        AvgMFE=('MFE', 'mean'),
        ProfitFactor=('Return', lambda x: x[x > 0].sum() / abs(x[x < 0].sum()) if len(x[x < 0]) > 0 and x[x < 0].sum() != 0 else np.nan)
    ).reset_index()

    print("\nAdvanced Day Trading Gap Analysis")
    print("=" * 110)
    
    # Sort for better readability
    summary['Session_Rank'] = summary['Session'].map({
        "Morning (09:30-10:30)": 1,
        "Mid-day (10:30-14:30)": 2,
        "Afternoon (14:30-16:00)": 3
    })
    summary = summary.sort_values(['Session_Rank', 'Bucket', 'Horizon'])

    for session in summary['Session'].unique():
        print(f"\n>>> SESSION: {session}")
        sess_data = summary[summary['Session'] == session]
        
        print(f"{'Bucket':<15} | {'H':<3} | {'Count':<5} | {'Win%':<6} | {'MeanRet':<8} | {'MAE':<7} | {'MFE':<7} | {'PF':<5}")
        print("-" * 80)
        
        for _, r in sess_data.iterrows():
            print(f"{r['Bucket']:<15} | {r['Horizon']:<3} | {int(r['Count']):<5} | {r['WinRate']:<6.1f} | {r['MeanRet']:<8.4f} | {r['AvgMAE']:<7.3f} | {r['AvgMFE']:<7.3f} | {r['ProfitFactor']:<5.2f}")

if __name__ == "__main__":
    analyze_advanced_gaps('/home/hallo/Documents/display/qqq5m.csv')
