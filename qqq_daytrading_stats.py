#!/usr/bin/env python3
"""
QQQ 5-Minute Bar Day-Trading Statistics Analyzer

This script analyzes intraday patterns in QQQ 5-minute data to identify:
- At which bar the day's high/low typically occurs
- Opening gap statistics
- Range characteristics
- First hour performance
- And other useful day-trading insights
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import argparse
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def load_data(filepath):
    """Load and prepare the 5-minute bar data."""
    df = pd.read_csv(filepath)
    df['time'] = pd.to_datetime(df['time'])
    df['date'] = df['time'].dt.date
    df['time_of_day'] = df['time'].dt.time
    return df


def calculate_bar_number(df):
    """Calculate the bar number within each trading day (1-78 for regular hours)."""
    df['bar_number'] = df.groupby('date').cumcount() + 1
    return df


def analyze_high_low_bars(df):
    """Analyze at which bar the day's high and low occur."""
    results = defaultdict(lambda: {'high_bars': [], 'low_bars': [], 
                                   'both_same_bar': 0, 'total_days': 0})
    
    daily_stats = []
    prev_close = None
    
    for date, day_data in df.groupby('date'):
        if len(day_data) < 10:  # Skip partial days
            continue
            
        day_high = day_data['high'].max()
        day_low = day_data['low'].min()
        day_open = day_data.iloc[0]['open']
        day_close = day_data.iloc[-1]['close']
        
        # Find bar(s) where high occurred
        high_bars = day_data[day_data['high'] == day_high]['bar_number'].values
        # Find bar(s) where low occurred
        low_bars = day_data[day_data['low'] == day_low]['bar_number'].values
        
        # Take the first occurrence
        first_high_bar = high_bars[0]
        first_low_bar = low_bars[0]
        
        results['all']['high_bars'].append(first_high_bar)
        results['all']['low_bars'].append(first_low_bar)
        results['all']['total_days'] += 1
        
        if first_high_bar == first_low_bar:
            results['all']['both_same_bar'] += 1
        
        # Calculate gap
        gap = (day_open - prev_close) if prev_close is not None else None
        gap_pct = (gap / prev_close * 100) if prev_close is not None and prev_close > 0 else None
        
        # Calculate range metrics
        day_range = day_high - day_low
        close_in_range = ((day_close - day_low) / day_range) if day_range > 0 else None
            
        daily_stats.append({
            'date': date,
            'high_bar': first_high_bar,
            'low_bar': first_low_bar,
            'same_bar': first_high_bar == first_low_bar,
            'high': day_high,
            'low': day_low,
            'open': day_open,
            'close': day_close,
            'gap': gap,
            'gap_pct': gap_pct,
            'day_range': day_range,
            'close_in_range': close_in_range
        })
        
        prev_close = day_close
    
    return results, pd.DataFrame(daily_stats)


def print_bar_distribution(bars, label, total_days):
    """Print distribution of when highs/lows occur."""
    print(f"\n{label} Distribution:")
    print("=" * 60)
    
    # Create buckets
    buckets = {
        'Morning (1-12)': [b for b in bars if 1 <= b <= 12],    # First hour
        'Mid-Morning (13-24)': [b for b in bars if 13 <= b <= 24],
        'Midday (25-48)': [b for b in bars if 25 <= b <= 48],
        'Afternoon (49-66)': [b for b in bars if 49 <= b <= 66],
        'Last Hour (67-78)': [b for b in bars if 67 <= b <= 78]
    }
    
    for bucket_name, bucket_bars in buckets.items():
        pct = (len(bucket_bars) / total_days * 100) if total_days > 0 else 0
        print(f"  {bucket_name:20s}: {len(bucket_bars):4d} days ({pct:5.1f}%)")
    
    # Top 5 specific bars
    bar_counts = pd.Series(bars).value_counts().head(10)
    print(f"\n  Top 10 Most Common Bars:")
    for bar, count in bar_counts.items():
        pct = (count / total_days * 100) if total_days > 0 else 0
        time_est = f"~{9 + (bar-1)//12:02d}:{((bar-1)%12)*5:02d}"
        print(f"    Bar {bar:2d} ({time_est}): {count:4d} times ({pct:5.1f}%)")


def analyze_gaps(daily_stats_df):
    """Analyze opening gaps."""
    gaps = daily_stats_df['gap_pct'].dropna()
    
    print("\nOpening Gap Statistics:")
    print("=" * 60)
    print(f"  Average Gap:        {gaps.mean():+6.2f}%")
    print(f"  Median Gap:         {gaps.median():+6.2f}%")
    print(f"  Gap Up Days:        {(gaps > 0).sum():4d} ({(gaps > 0).sum()/len(gaps)*100:5.1f}%)")
    print(f"  Gap Down Days:      {(gaps < 0).sum():4d} ({(gaps < 0).sum()/len(gaps)*100:5.1f}%)")
    print(f"  Gap > +0.5%:        {(gaps > 0.5).sum():4d} ({(gaps > 0.5).sum()/len(gaps)*100:5.1f}%)")
    print(f"  Gap < -0.5%:        {(gaps < -0.5).sum():4d} ({(gaps < -0.5).sum()/len(gaps)*100:5.1f}%)")


def analyze_range_location(daily_stats_df):
    """Analyze where price closes relative to the day's range."""
    close_loc = daily_stats_df['close_in_range'].dropna()
    
    print("\nClose Location in Day's Range:")
    print("=" * 60)
    print(f"  Average Close Location: {close_loc.mean()*100:5.1f}% of range")
    print(f"  Median Close Location:  {close_loc.median()*100:5.1f}% of range")
    print(f"  Upper 25% (75-100%):    {(close_loc >= 0.75).sum():4d} days ({(close_loc >= 0.75).sum()/len(close_loc)*100:5.1f}%)")
    print(f"  Middle 50% (25-75%):    {((close_loc >= 0.25) & (close_loc < 0.75)).sum():4d} days ({((close_loc >= 0.25) & (close_loc < 0.75)).sum()/len(close_loc)*100:5.1f}%)")
    print(f"  Lower 25% (0-25%):      {(close_loc < 0.25).sum():4d} days ({(close_loc < 0.25).sum()/len(close_loc)*100:5.1f}%)")


def analyze_first_hour(df):
    """Analyze first hour (12 bars) vs rest of day performance."""
    first_hour_stats = []
    
    for date, day_data in df.groupby('date'):
        if len(day_data) < 12:
            continue
            
        first_hour = day_data.iloc[:12]
        rest_of_day = day_data.iloc[12:]
        
        if len(rest_of_day) == 0:
            continue
            
        first_hour_range = first_hour['high'].max() - first_hour['low'].min()
        rest_range = rest_of_day['high'].max() - rest_of_day['low'].min()
        day_range = day_data['high'].max() - day_data['low'].min()
        
        first_hour_stats.append({
            'first_hour_range': first_hour_range,
            'rest_range': rest_range,
            'total_range': day_range,
            'first_hour_pct': first_hour_range / day_range if day_range > 0 else 0
        })
    
    fh_df = pd.DataFrame(first_hour_stats)
    
    print("\nFirst Hour (9:30-10:30) Statistics:")
    print("=" * 60)
    print(f"  Avg First Hour Range:     {fh_df['first_hour_range'].mean():.2f}")
    print(f"  Avg Rest of Day Range:    {fh_df['rest_range'].mean():.2f}")
    print(f"  First Hour as % of Total: {fh_df['first_hour_pct'].mean()*100:.1f}%")
    print(f"  Days where first hour > 50% of range: {(fh_df['first_hour_pct'] > 0.5).sum()} ({(fh_df['first_hour_pct'] > 0.5).sum()/len(fh_df)*100:.1f}%)")


def analyze_high_low_sequence(daily_stats_df):
    """Analyze whether high or low comes first."""
    print("\nHigh/Low Sequence:")
    print("=" * 60)
    
    high_first = (daily_stats_df['high_bar'] < daily_stats_df['low_bar']).sum()
    low_first = (daily_stats_df['low_bar'] < daily_stats_df['high_bar']).sum()
    same_bar = daily_stats_df['same_bar'].sum()
    total = len(daily_stats_df)
    
    print(f"  High Before Low:  {high_first:4d} days ({high_first/total*100:5.1f}%)")
    print(f"  Low Before High:  {low_first:4d} days ({low_first/total*100:5.1f}%)")
    print(f"  Same Bar:         {same_bar:4d} days ({same_bar/total*100:5.1f}%)")


def plot_histogram_with_cdf(data, bins, range_min, range_max, color, title, xlabel, filename, label=None):
    """Helper to plot histogram with cumulative distribution line."""
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # Histogram
    counts, _, _ = ax1.hist(data, bins=bins, range=(range_min, range_max), 
                           edgecolor='black', alpha=0.6, color=color, label='Frequency')
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel('Frequency', color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(alpha=0.3)
    
    # CDF
    ax2 = ax1.twinx()
    
    # Calculate CDF
    sorted_data = np.sort(data)
    yvals = np.arange(len(sorted_data)) / float(len(sorted_data) - 1) * 100
    
    ax2.plot(sorted_data, yvals, color='black', linewidth=2, label='Cumulative %')
    ax2.set_ylabel('Cumulative %', color='black')
    ax2.set_ylim(0, 105)
    
    # Add key percentile lines
    for pct in [50, 80, 95]:
        ax2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)
        
    plt.title(title, fontweight='bold')
    
    # Legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"📊 Plot saved as '{filename}'")
    plt.close()


def plot_results(results, daily_stats_df, df):
    """Create separate visualizations for all statistics."""
    
    # 1. High Bar Distribution with CDF
    high_bars = results['all']['high_bars']
    plot_histogram_with_cdf(high_bars, 78, 1, 79, 'green', 
                          'Distribution of Day High Occurrence', 
                          'Bar Number', 'high_dist.png')
    
    # 2. Low Bar Distribution with CDF
    low_bars = results['all']['low_bars']
    plot_histogram_with_cdf(low_bars, 78, 1, 79, 'red', 
                          'Distribution of Day Low Occurrence', 
                          'Bar Number', 'low_dist.png')
    
    # 3. First Extreme (Either High or Low) and Second Extreme (Both)
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    # Calculate first and second extremes
    first_extreme = daily_stats_df[['high_bar', 'low_bar']].min(axis=1)
    second_extreme = daily_stats_df[['high_bar', 'low_bar']].max(axis=1)
    
    # Plot Histograms
    ax1.hist(first_extreme, bins=78, range=(1, 79), edgecolor='black', alpha=0.4, 
             color='blue', label='First Extreme (Computed High OR Low)')
    ax1.hist(second_extreme, bins=78, range=(1, 79), edgecolor='black', alpha=0.4, 
             color='orange', label='Second Extreme (Computed Both)')
    
    ax1.set_xlabel('Bar Number')
    ax1.set_ylabel('Frequency')
    ax1.grid(alpha=0.3)
    
    # Plot CDFs
    ax2 = ax1.twinx()
    
    # First Extreme CDF
    sorted_first = np.sort(first_extreme)
    y_first = np.arange(len(sorted_first)) / float(len(sorted_first) - 1) * 100
    ax2.plot(sorted_first, y_first, color='blue', linewidth=2, linestyle='-', 
             label='First Extreme Cumulative %')
    
    # Second Extreme CDF
    sorted_second = np.sort(second_extreme)
    y_second = np.arange(len(sorted_second)) / float(len(sorted_second) - 1) * 100
    ax2.plot(sorted_second, y_second, color='chocolate', linewidth=2, linestyle='-', 
             label='Second Extreme Cumulative %')
    
    ax2.set_ylabel('Cumulative %')
    ax2.set_ylim(0, 105)
    
    # Add key percentile lines
    for pct in [50, 80, 95]:
        ax2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)
        ax2.text(1, pct+1, f'{pct}%', color='gray', fontsize=8)

    plt.title('Distribution of Time to Form Extremes (Either/Both)', fontweight='bold')
    
    # Legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    
    plt.tight_layout()
    plt.savefig('extremes_dist.png', dpi=150)
    print(f"📊 Plot saved as 'extremes_dist.png'")
    plt.close()
    
    # 4. High/Low Sequence Pie Chart
    plt.figure(figsize=(8, 8))
    high_first = (daily_stats_df['high_bar'] < daily_stats_df['low_bar']).sum()
    low_first = (daily_stats_df['low_bar'] < daily_stats_df['high_bar']).sum()
    same_bar = daily_stats_df['same_bar'].sum()
    
    labels = ['Low First', 'High First', 'Same Bar']
    sizes = [low_first, high_first, same_bar]
    colors = ['#ff6b6b', '#51cf66', '#ffd43b']
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    plt.title('High/Low Sequence', fontweight='bold')
    plt.tight_layout()
    plt.savefig('high_low_sequence.png', dpi=150)
    print(f"📊 Plot saved as 'high_low_sequence.png'")
    plt.close()
    
    # 5. Opening Gap Distribution
    gaps = daily_stats_df['gap_pct'].dropna()
    plot_histogram_with_cdf(gaps, 50, -3, 3, 'purple', 
                          'Opening Gap Distribution', 
                          'Gap %', 'gap_dist.png')
    
    # 6. Close Location in Range
    close_loc = daily_stats_df['close_in_range'].dropna() * 100
    plot_histogram_with_cdf(close_loc, 50, 0, 100, 'blue', 
                          'Close Location in Day Range', 
                          'Close Location (% of Range)', 'close_loc.png')
    
    # 7. Top Bars for High/Low (Bar Chart)
    plt.figure(figsize=(12, 6))
    high_bar_counts = pd.Series(high_bars).value_counts().head(10).sort_index()
    low_bar_counts = pd.Series(low_bars).value_counts().head(10).sort_index()
    
    all_top_bars = sorted(set(list(high_bar_counts.index) + list(low_bar_counts.index)))
    high_vals = [high_bar_counts.get(b, 0) for b in all_top_bars]
    low_vals = [low_bar_counts.get(b, 0) for b in all_top_bars]
    
    x = np.arange(len(all_top_bars))
    width = 0.35
    plt.bar(x - width/2, high_vals, width, label='High', color='green', alpha=0.7)
    plt.bar(x + width/2, low_vals, width, label='Low', color='red', alpha=0.7)
    plt.xlabel('Bar Number')
    plt.ylabel('Frequency')
    plt.title('Most Common Bars for High/Low', fontweight='bold')
    plt.xticks(x, all_top_bars, rotation=45)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('common_bars.png', dpi=150)
    print(f"📊 Plot saved as 'common_bars.png'")
    plt.close()
    
    # 8. First Hour Range Analysis
    first_hour_stats = []
    for date, day_data in df.groupby('date'):
        if len(day_data) < 12:
            continue
        first_hour = day_data.iloc[:12]
        rest_of_day = day_data.iloc[12:]
        if len(rest_of_day) == 0:
            continue
        first_hour_range = first_hour['high'].max() - first_hour['low'].min()
        day_range = day_data['high'].max() - day_data['low'].min()
        first_hour_stats.append(first_hour_range / day_range * 100 if day_range > 0 else 0)
    
    plot_histogram_with_cdf(first_hour_stats, 50, 0, 100, 'orange',
                          'First Hour Range Contribution',
                          'First Hour Range as % of Day Range', 'first_hour.png')
    
    # 9. Time-based High/Low Buckets
    plt.figure(figsize=(10, 6))
    bucket_labels = ['Morning\n(1-12)', 'Mid-Morn\n(13-24)', 'Midday\n(25-48)', 
                     'Afternoon\n(49-66)', 'Last Hour\n(67-78)']
    bucket_ranges = [(1, 12), (13, 24), (25, 48), (49, 66), (67, 78)]
    
    high_buckets = [len([b for b in high_bars if r[0] <= b <= r[1]]) for r in bucket_ranges]
    low_buckets = [len([b for b in low_bars if r[0] <= b <= r[1]]) for r in bucket_ranges]
    
    x = np.arange(len(bucket_labels))
    width = 0.35
    plt.bar(x - width/2, high_buckets, width, label='High', color='green', alpha=0.7)
    plt.bar(x + width/2, low_buckets, width, label='Low', color='red', alpha=0.7)
    plt.ylabel('Number of Days')
    plt.title('High/Low by Time Period', fontweight='bold')
    plt.xticks(x, bucket_labels)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('time_buckets.png', dpi=150)
    print(f"📊 Plot saved as 'time_buckets.png'")
    plt.close()
    
    # 10. Gap Size Categories
    plt.figure(figsize=(8, 6))
    # gaps already calculated
    gap_categories = [
        'Large Down\n(< -0.5%)',
        'Small Down\n(-0.5 to 0%)',
        'Small Up\n(0 to 0.5%)',
        'Large Up\n(> 0.5%)'
    ]
    gap_counts = [
        (gaps < -0.5).sum(),
        ((gaps >= -0.5) & (gaps < 0)).sum(),
        ((gaps >= 0) & (gaps <= 0.5)).sum(),
        (gaps > 0.5).sum()
    ]
    
    colors_gap = ['darkred', 'lightcoral', 'lightgreen', 'darkgreen']
    plt.bar(gap_categories, gap_counts, color=colors_gap, alpha=0.7, edgecolor='black')
    plt.ylabel('Number of Days')
    plt.title('Gap Size Categories', fontweight='bold')
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('gap_categories.png', dpi=150)
    print(f"📊 Plot saved as 'gap_categories.png'")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Analyze QQQ 5-minute day-trading statistics')
    parser.add_argument('-p', '--plot', action='store_true', help='Generate and display plots')
    args = parser.parse_args()
    
    filepath = 'data/QQQ5m.csv'
    
    print("=" * 60)
    print("QQQ 5-Minute Day-Trading Statistics")
    print("=" * 60)
    
    # Load and prepare data
    df = load_data(filepath)
    df = calculate_bar_number(df)
    
    print(f"\nDataset: {df['date'].min()} to {df['date'].max()}")
    print(f"Total bars: {len(df):,}")
    print(f"Trading days: {df['date'].nunique():,}")
    
    # Analyze high/low bar occurrences
    results, daily_stats_df = analyze_high_low_bars(df)
    
    total_days = results['all']['total_days']
    print(f"\nAnalyzed {total_days} complete trading days")
    
    # Print distributions
    print_bar_distribution(results['all']['high_bars'], "Day High", total_days)
    print_bar_distribution(results['all']['low_bars'], "Day Low", total_days)
    
    # High/Low sequence
    analyze_high_low_sequence(daily_stats_df)
    
    # Gap analysis
    analyze_gaps(daily_stats_df)
    
    # Range location analysis
    analyze_range_location(daily_stats_df)
    
    # First hour analysis
    analyze_first_hour(df)
    
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    
    # Generate plots if requested
    if args.plot:
        print("\nGenerating plots...")
        plot_results(results, daily_stats_df, df)


if __name__ == "__main__":
    main()
