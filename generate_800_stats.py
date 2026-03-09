#!/usr/bin/env python3
"""
800.csv 5-Minute Bar Day-Trading Statistics Analyzer

This script analyzes intraday patterns in 800.csv 5-minute data.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import argparse
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

def load_data(filepath):
    """Load and prepare the 5-minute bar data."""
    df = pd.read_csv(filepath)
    # The time column contains timezone info, we might want to just parse the naive date and time
    # e.g., '2016-03-20T21:30:00-04:00'
    df['time'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert('America/New_York')
    df['date'] = df['time'].dt.date
    df['time_of_day'] = df['time'].dt.time
    return df


def calculate_bar_number(df):
    """Calculate the bar number within each trading day."""
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


def plot_histogram_with_cdf(data, bins, range_min, range_max, color, title, xlabel, filename, out_dir, is_time=False):
    """Helper to plot histogram with cumulative distribution line."""
    fig, ax1 = plt.subplots(figsize=(12, 8))
    
    if is_time:
        gap_bars = 18
        data = np.where(np.array(data) > 24, np.array(data) + gap_bars, np.array(data))
        bins += gap_bars
        range_max += gap_bars

    # Histogram
    counts, bins_edges, _ = ax1.hist(data, bins=bins, range=(range_min, range_max), 
                           edgecolor='black', alpha=0.6, color=color, label='Frequency')
    
    if is_time:
        ticks = [1, 7, 13, 19, 24, 43, 49, 55, 61, 66]
        labels = ["09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00"]
        ax1.set_xticks(ticks)
        ax1.set_xticklabels(labels, rotation=45)
        ax1.set_xlabel("Time")
    else:
        ax1.set_xlabel(xlabel)

    if 'Gap' in title:
        stats_text = (
            f"Total Days: {len(data)}\n"
            f"Mean Gap: {np.mean(data):.3f}%\n"
            f"Std Dev: {np.std(data):.3f}%\n"
            f"Gap = 0: {np.mean(np.array(data) == 0)*100:.1f}%\n"
            f"Gap > 0: {np.mean(np.array(data) > 0)*100:.1f}%\n"
            f"Gap < 0: {np.mean(np.array(data) < 0)*100:.1f}%"
        )
        up_gaps = [d for d in data if d > 0]
        dn_gaps = [d for d in data if d < 0]
        if up_gaps: stats_text += f"\nAvg Up: {np.mean(up_gaps):.3f}%"
        if dn_gaps: stats_text += f"\nAvg Down: {np.mean(dn_gaps):.3f}%"
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10,
                verticalalignment='top', bbox=props)
        
        sorted_counts = np.sort(counts)
        if len(sorted_counts) > 1 and sorted_counts[-1] > sorted_counts[-2] * 3:
            y_max = sorted_counts[-2] * 2.0
            ax1.set_ylim(0, max(y_max, 10))

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
    # Add a workaround for legend on twin axes
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    filepath = os.path.join(out_dir, filename)
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
    plt.close()


def plot_results(results, daily_stats_df, df, out_dir):
    """Create separate visualizations for all statistics."""
    os.makedirs(out_dir, exist_ok=True)
    
    # Total bars per day typically depends on the data (assume up to 78 for 6.5 hours of 5-min bars)
    max_bars = df['bar_number'].max()
    
    # 1. High Bar Distribution with CDF
    high_bars = results['all']['high_bars']
    plot_histogram_with_cdf(high_bars, max_bars, 1, max_bars+1, 'green', 
                          'Distribution of Day High Occurrence (800)', 
                          'Time', 'high_dist.png', out_dir, is_time=True)
    
    # 2. Low Bar Distribution with CDF
    low_bars = results['all']['low_bars']
    plot_histogram_with_cdf(low_bars, max_bars, 1, max_bars+1, 'red', 
                          'Distribution of Day Low Occurrence (800)', 
                          'Time', 'low_dist.png', out_dir, is_time=True)
    
    # 3. First Extreme (Either High or Low) and Second Extreme (Both)
    fig, ax1 = plt.subplots(figsize=(12, 8))
    first_extreme = daily_stats_df[['high_bar', 'low_bar']].min(axis=1)
    second_extreme = daily_stats_df[['high_bar', 'low_bar']].max(axis=1)
    
    gap_bars = 18
    first_extreme = np.where(first_extreme > 24, first_extreme + gap_bars, first_extreme)
    second_extreme = np.where(second_extreme > 24, second_extreme + gap_bars, second_extreme)
    max_bins = max_bars + gap_bars
    
    ax1.hist(first_extreme, bins=max_bins, range=(1, max_bins+1), edgecolor='black', alpha=0.4, 
             color='blue', label='First Extreme (Computed High OR Low)')
    ax1.hist(second_extreme, bins=max_bins, range=(1, max_bins+1), edgecolor='black', alpha=0.4, 
             color='orange', label='Second Extreme (Computed Both)')
    ax1.set_ylabel('Frequency')
    ax1.grid(alpha=0.3)

    # Create time labels for the x-axis
    ticks = [1, 7, 13, 19, 24, 43, 49, 55, 61, 66]
    labels = ["09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00"]
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(labels, rotation=45)
    ax1.set_xlabel("Time")
    
    ax2 = ax1.twinx()
    sorted_first = np.sort(first_extreme)
    y_first = np.arange(len(sorted_first)) / float(len(sorted_first) - 1) * 100
    ax2.plot(sorted_first, y_first, color='blue', linewidth=2, linestyle='-', 
             label='First Extreme Cumulative %')
    
    sorted_second = np.sort(second_extreme)
    y_second = np.arange(len(sorted_second)) / float(len(sorted_second) - 1) * 100
    ax2.plot(sorted_second, y_second, color='chocolate', linewidth=2, linestyle='-', 
             label='Second Extreme Cumulative %')
    
    ax2.set_ylabel('Cumulative %')
    ax2.set_ylim(0, 105)
    for pct in [50, 80, 95]:
        ax2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)
        ax2.text(1, pct+1, f'{pct}%', color='gray', fontsize=8)

    plt.title('Distribution of Time to Form Extremes (800)', fontweight='bold')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    plt.tight_layout()
    filepath = os.path.join(out_dir, 'extremes_dist.png')
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
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
    plt.title('High/Low Sequence (800)', fontweight='bold')
    plt.tight_layout()
    filepath = os.path.join(out_dir, 'high_low_sequence.png')
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
    plt.close()
    
    # 5. Opening Gap Distribution (custom: clip outliers, fine-grained bins)
    gaps = daily_stats_df['gap_pct'].dropna()
    gap_lo, gap_hi = -5.0, 5.0
    bin_size = 0.25
    bin_edges = np.arange(gap_lo, gap_hi + bin_size, bin_size)

    # Clip outliers into the boundary bins
    gaps_clipped = np.clip(gaps, gap_lo + 1e-9, gap_hi - 1e-9)

    n_below = (gaps < gap_lo).sum()
    n_above = (gaps > gap_hi).sum()

    fig_g, ax_g1 = plt.subplots(figsize=(12, 8))
    counts_g, _, patches = ax_g1.hist(gaps_clipped, bins=bin_edges,
                                       edgecolor='black', alpha=0.6, color='purple', label='Frequency')

    # Label the first and last bar as outlier bins
    if n_below > 0:
        patches[0].set_facecolor('#9b59b6')
        ax_g1.text(bin_edges[0] + bin_size/2, counts_g[0] + 1, f'< {gap_lo:.0f}%\n(n={n_below})',
                   ha='center', va='bottom', fontsize=8, color='darkviolet', fontweight='bold')
    if n_above > 0:
        patches[-1].set_facecolor('#9b59b6')
        ax_g1.text(bin_edges[-2] + bin_size/2, counts_g[-1] + 1, f'> {gap_hi:.0f}%\n(n={n_above})',
                   ha='center', va='bottom', fontsize=8, color='darkviolet', fontweight='bold')

    # Auto-trim x-axis to actual data extent with some padding
    data_min = max(gaps.quantile(0.001), gap_lo)
    data_max = min(gaps.quantile(0.999), gap_hi)
    ax_g1.set_xlim(data_min - bin_size, data_max + bin_size)

    ax_g1.set_xlabel('Gap %')
    ax_g1.set_ylabel('Frequency', color='purple')
    ax_g1.tick_params(axis='y', labelcolor='purple')
    ax_g1.grid(alpha=0.3)

    # Stats annotation
    up_gaps = gaps[gaps > 0]
    dn_gaps = gaps[gaps < 0]
    stats_text = (
        f"Total Days: {len(gaps)}\n"
        f"Mean: {gaps.mean():.3f}%\n"
        f"Std Dev: {gaps.std():.3f}%\n"
        f"Median: {gaps.median():.3f}%\n"
        f"Gap up: {(gaps > 0).mean()*100:.1f}%  Avg: {up_gaps.mean():.3f}%\n"
        f"Gap dn: {(gaps < 0).mean()*100:.1f}%  Avg: {dn_gaps.mean():.3f}%\n"
        f"Flat:   {(gaps == 0).mean()*100:.1f}%"
    )
    ax_g1.text(0.02, 0.98, stats_text, transform=ax_g1.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

    # CDF on twin axis
    ax_g2 = ax_g1.twinx()
    sorted_gaps = np.sort(gaps_clipped)
    yvals_g = np.arange(len(sorted_gaps)) / float(len(sorted_gaps) - 1) * 100
    ax_g2.plot(sorted_gaps, yvals_g, color='black', linewidth=2, label='Cumulative %')
    ax_g2.set_ylabel('Cumulative %', color='black')
    ax_g2.set_ylim(0, 105)
    for pct in [50, 80, 95]:
        ax_g2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)

    plt.title('Opening Gap Distribution (800)', fontweight='bold')
    lines1, labels1 = ax_g1.get_legend_handles_labels()
    lines2, labels2 = ax_g2.get_legend_handles_labels()
    ax_g1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    plt.tight_layout()
    filepath_g = os.path.join(out_dir, 'gap_dist.png')
    plt.savefig(filepath_g, dpi=150)
    print(f"📊 Plot saved as '{filepath_g}'")
    plt.close()
    
    # 6. Close Location in Range
    close_loc = daily_stats_df['close_in_range'].dropna() * 100
    plot_histogram_with_cdf(close_loc, 50, 0, 100, 'blue', 
                          'Close Location in Day Range (800)', 
                          'Close Location (% of Range)', 'close_loc.png', out_dir)
    
    # 7. Top Bars for High/Low
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
    plt.title('Most Common Bars for High/Low (800)', fontweight='bold')
    plt.xticks(x, all_top_bars, rotation=45)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    filepath = os.path.join(out_dir, 'common_bars.png')
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
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
                          'First Hour Range Contribution (800)',
                          'First Hour Range as % of Day Range', 'first_hour.png', out_dir)
    
    # 9. Time-based High/Low Buckets
    plt.figure(figsize=(10, 6))
    bucket_labels = ['9:30\n10:00', '10:00\n10:30', '10:30\n11:00', '11:00\n11:30', 
                     '13:00\n13:30', '13:30\n14:00', '14:00\n14:30', '14:30\n15:00']
    bucket_ranges = [(1, 6), (7, 12), (13, 18), (19, 24), 
                     (25, 30), (31, 36), (37, 42), (43, 48)]
    
    high_buckets = [len([b for b in high_bars if r[0] <= b <= r[1]]) for r in bucket_ranges]
    low_buckets = [len([b for b in low_bars if r[0] <= b <= r[1]]) for r in bucket_ranges]
    
    x = np.arange(len(bucket_labels))
    width = 0.35
    plt.bar(x - width/2, high_buckets, width, label='High', color='green', alpha=0.7)
    plt.bar(x + width/2, low_buckets, width, label='Low', color='red', alpha=0.7)
    plt.ylabel('Number of Days')
    plt.title('High/Low by Time Period (800)', fontweight='bold')
    plt.xticks(x, bucket_labels)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    filepath = os.path.join(out_dir, 'time_buckets.png')
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
    plt.close()
    
    # 10. Gap Size Categories
    plt.figure(figsize=(8, 6))
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
    plt.title('Gap Size Categories (800)', fontweight='bold')
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    filepath = os.path.join(out_dir, 'gap_categories.png')
    plt.savefig(filepath, dpi=150)
    print(f"📊 Plot saved as '{filepath}'")
    plt.close()


def main():
    filepath = '/home/hallo/Documents/display/data/800.csv'
    out_dir = '/home/hallo/Documents/display/public/data/daystata'
    
    df = load_data(filepath)
    df = calculate_bar_number(df)
    
    results, daily_stats_df = analyze_high_low_bars(df)
    plot_results(results, daily_stats_df, df, out_dir)
    print("Done generating 800.csv plots.")

if __name__ == "__main__":
    main()
    
