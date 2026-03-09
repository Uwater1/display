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
    
    # Group by time of day
    time_group = df.groupby('time_of_day')
    
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
