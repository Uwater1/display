#!/usr/bin/env python3
"""
Liquidity Study Analyzer for hs300_zz500_sum.csv
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def load_data(filepath):
    """Load data and index by time."""
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert('Asia/Shanghai')
    df['date'] = df['time'].dt.date
    df['time_of_day'] = df['time'].dt.time
    # Additional feature calculation
    df['range'] = df['high'] - df['low']
    df['returns'] = df['close'].pct_change()
    df['abs_returns'] = df['returns'].abs()
    df['volatility_per_vol'] = df['abs_returns'] / (df['Volume'] + 1e-9) 
    return df

def generate_liquidity_charts(df, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # Helper to clean up the index labels
    def format_time_labels(index_obj):
        labels = []
        for t in index_obj:
            # Assuming 5 min intervals
            start_m = t.hour * 60 + t.minute
            end_m = start_m + 30 # Grouping to 30 min intervals, wait 30 min? User said 9:30 ~ 10:00 etc. 
            # actually time is 5min bars so we probably should just do t + 30 min, actually user said "replace the 9:30:00 with 9:30 ~ 10:00 etc."
            # Since the data is already grouped by time_of_day (every 5 min)
            # wait, if the original labels are 9:30:00, 9:35:00 etc., it's 5 min bins. 
            # I will just format the label to '{t.hour}:{t.minute:02d} ~ {later}' where later is +30min? Or +5min? Since data is 5 min bins 
            # Ah user said "replace the 9:30:00 with 9:30 ~ 10:00 etc", which implies aggregating by 30 mins to make it 9:30~10:00! Let's resample by 30min? No, just formatting the labels from the 30M resample. Let's group by 30m!
            pass # wait, I need to group by 30m first, otherwise there are 78 bars. 
            
    # Group by 30 minute intervals of time_of_day
    # To do this correctly, let's map time_of_day to 30 min buckets
    def to_30m_bucket(t):
        minute = t.hour * 60 + t.minute
        # 9:30 is 570.
        if minute < 570: return "Pre-mkt"
        bucket_idx = (minute - 570) // 30
        start_min = 570 + bucket_idx * 30
        end_min = start_min + 30
        return f"{start_min//60:02d}:{start_min%60:02d} ~ {end_min//60:02d}:{end_min%60:02d}"

    df['time_bucket'] = df['time_of_day'].apply(to_30m_bucket)
    # Remove pre-market if any
    df_filtered = df[df['time_bucket'] != "Pre-mkt"]
    time_group = df_filtered.groupby('time_bucket')
    
    # 1. Average Volume by Time of Day
    avg_vol = time_group['Volume'].mean()
    plt.figure(figsize=(12, 6))
    avg_vol.plot(kind='bar', color='steelblue')
    plt.title('Average Volume by Time of Day', fontweight='bold')
    plt.xlabel('Time of Day')
    plt.ylabel('Average Volume')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'avg_volume_time.png'), dpi=150)
    plt.close()
    
    # 2. Average Range by Time of Day
    avg_range = time_group['range'].mean()
    plt.figure(figsize=(12, 6))
    avg_range.plot(kind='bar', color='darkorange')
    plt.title('Average Price Range (High-Low) by Time of Day', fontweight='bold')
    plt.xlabel('Time of Day')
    plt.ylabel('Average Range')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'avg_range_time.png'), dpi=150)
    plt.close()
    
    # 3. Volatility over Volume by Time of Day
    # This measures how much price moves per unit of volume (slippage/liquidity proxy)
    avg_vol_per_vol = time_group['volatility_per_vol'].mean()
    plt.figure(figsize=(12, 6))
    avg_vol_per_vol.plot(kind='bar', color='purple')
    plt.title('Price Impact per Volume Unit (Liquidity Proxy)', fontweight='bold')
    plt.xlabel('Time of Day')
    plt.ylabel('Abs Return / Volume')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'price_impact_time.png'), dpi=150)
    plt.close()
    
    # 4. Total Volume Distribution over the Day
    total_vol = time_group['Volume'].sum()
    total_vol_pct = total_vol / total_vol.sum() * 100
    plt.figure(figsize=(12, 6))
    total_vol_pct.plot(kind='bar', color='teal')
    plt.title('Percentage of Daily Volume by Time of Day', fontweight='bold')
    plt.xlabel('Time of Day')
    plt.ylabel('% of Daily Volume')
    plt.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'vol_pct_time.png'), dpi=150)
    plt.close()

def main():
    filepath = '/home/hallo/Documents/display/data/hs300_zz500_sum.csv'
    out_dir = '/home/hallo/Documents/display/public/data/liquidity'
    
    print("Loading data...")
    df = load_data(filepath)
    print("Generating charts...")
    generate_liquidity_charts(df, out_dir)
    print(f"Charts saved to {out_dir}")

if __name__ == "__main__":
    main()
