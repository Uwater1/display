import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Configuration
DATA_PATH = '/home/hallo/Documents/display/data/qqq1d.csv'
OUTPUT_CHART = '/home/hallo/Documents/display/public/data/stats/qqq_expected_return.png'

def calculate_returns():
    print(f"Reading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Ensure time is sorted
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    # Calculate daily returns (current close relative to previous close)
    # We want to buy AFTER a grow or fall today, so R_t is today's move.
    df['daily_return'] = df['close'].pct_change()
    
    # Calculate forward returns (buy at today's close, sell N days later)
    # Forward 1d return is (Close_{t+1} / Close_t) - 1
    df['fwd_1d'] = df['close'].shift(-1) / df['close'] - 1
    df['fwd_5d'] = df['close'].shift(-5) / df['close'] - 1
    df['fwd_10d'] = df['close'].shift(-10) / df['close'] - 1
    df['fwd_20d'] = df['close'].shift(-20) / df['close'] - 1
    
    # Define 9 buckets based on the sign and value of daily_return
    # Note: pct_change returns decimal (0.01 = 1%)
    def get_bucket(r):
        if pd.isna(r):
            return None
        r_pct = r * 100
        if r_pct >= 3.0:
            return 'Grow >3%'
        elif 2.0 <= r_pct < 3.0:
            return 'Grow 2~3%'
        elif 1.0 <= r_pct < 2.0:
            return 'Grow 1~2%'
        elif 0.5 <= r_pct < 1.0:
            return 'Grow 0.5~1%'
        elif -0.5 < r_pct < 0.5:
            return 'Middle (-0.5~0.5%)'
        elif -1.0 < r_pct <= -0.5:
            return 'Fall 0.5~1%'
        elif -2.0 < r_pct <= -1.0:
            return 'Fall 1~2%'
        elif -3.0 < r_pct <= -2.0:
            return 'Fall 2~3%'
        else:
            return 'Fall >3%'

    df['bucket'] = df['daily_return'].apply(get_bucket)
    
    # Drop rows with NaN in buckets or forward returns (at the end of dataset)
    df = df.dropna(subset=['bucket', 'fwd_1d', 'fwd_5d', 'fwd_10d', 'fwd_20d'])
    
    return df

def generate_chart(df):
    horizons = ['fwd_1d', 'fwd_5d', 'fwd_10d', 'fwd_20d']
    bucket_order = [
        'Grow >3%',
        'Grow 2~3%',
        'Grow 1~2%',
        'Grow 0.5~1%',
        'Middle (-0.5~0.5%)',
        'Fall 0.5~1%',
        'Fall 1~2%',
        'Fall 2~3%',
        'Fall >3%'
    ]
    
    # Aggregate data
    stats = df.groupby('bucket')[horizons].mean() * 100  # Convert to percentage
    stats = stats.reindex(bucket_order)
    
    counts = df['bucket'].value_counts().reindex(bucket_order)
    
    print("\nSample counts per bucket:")
    print(counts)
    print("\nMean Forward Returns (%):")
    print(stats)
    
    # Plotting
    plt.style.use('default') # White background
    fig, ax = plt.subplots(figsize=(14, 8))
    
    stats.plot(kind='bar', ax=ax, width=0.8, color=['#4fc3f7', '#81c784', '#fff176', '#ff8a65'])
    
    ax.set_title('QQQ Expected Returns by Previous Day Move (9 Buckets)', fontsize=16, pad=20)
    ax.set_xlabel('Previous Day Move Bucket', fontsize=12)
    ax.set_ylabel('Average Expected Return (%)', fontsize=12)
    ax.legend(['1 Day', '5 Days', '10 Days', '20 Days'], title='Horizon')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Add count labels above buckets
    for i, count in enumerate(counts):
        if not pd.isna(count):
            ax.text(i, ax.get_ylim()[1] * 0.02, f'n={int(count)}', 
                    ha='center', va='bottom', fontsize=9, color='black', alpha=0.7)

    plt.tight_layout()
    plt.savefig(OUTPUT_CHART)
    print(f"\nChart saved to {OUTPUT_CHART}")

if __name__ == "__main__":
    data = calculate_returns()
    generate_chart(data)
