#!/usr/bin/env python3
"""
ETF Intraday and Daily Statistics Analyzer for SSE 50, CSI 300, CSI 500, ChiNext, and STAR 50.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis

# Set seaborn theme for beautiful modern charts
sns.set_theme(style='whitegrid', context='notebook')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.titlesize': 16,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight'
})

ETFS = {
    'sse50': {
        'name': 'SSE 50 ETF (510050)',
        'file': 'data/50ETF_5m.parquet'
    },
    'csi300': {
        'name': 'CSI 300 ETF (510300)',
        'file': 'data/510300_5m.parquet'
    },
    'csi500': {
        'name': 'CSI 500 ETF (500ETF)',
        'file': 'data/500ETF_5m.parquet'
    },
    'chinext': {
        'name': 'ChiNext ETF (159915)',
        'file': 'data/159915ETF_5m.parquet'
    },
    'star50': {
        'name': 'STAR 50 ETF (588000)',
        'file': 'data/588000ETF_5m.parquet'
    }
}

OUT_BASE_DIR = 'public/data/daystata'

# Chinese market standard trading time labels (48 bars of 5m)
BAR_LABELS = [
    "09:35", "09:40", "09:45", "09:50", "09:55", "10:00",
    "10:05", "10:10", "10:15", "10:20", "10:25", "10:30",
    "10:35", "10:40", "10:45", "10:50", "10:55", "11:00",
    "11:05", "11:10", "11:15", "11:20", "11:25", "11:30",
    "13:05", "13:10", "13:15", "13:20", "13:25", "13:30",
    "13:35", "13:40", "13:45", "13:50", "13:55", "14:00",
    "14:05", "14:10", "14:15", "14:20", "14:25", "14:30",
    "14:35", "14:40", "14:45", "14:50", "14:55", "15:00"
]

# Keep only key labels to avoid x-axis clutter
TICK_INDICES = [0, 5, 11, 17, 23, 24, 29, 35, 41, 47]
TICK_LABELS = [BAR_LABELS[i] for i in TICK_INDICES]

def analyze_etf(etf_key, etf_info):
    name = etf_info['name']
    filepath = etf_info['file']
    print(f"\nProcessing {name} ({filepath})...")
    
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found. Skipping.")
        return
        
    # Read Parquet
    df = pd.read_parquet(filepath)
    df = df.sort_values('datetime')
    df['date'] = df['datetime'].dt.date
    
    # Filter for standard days (48 bars)
    counts = df.groupby('date').size()
    valid_dates = counts[counts == 48].index
    df = df[df['date'].isin(valid_dates)].copy()
    
    print(f"Loaded {len(valid_dates)} trading days.")
    
    # Pre-calculate daily statistics
    daily_stats = []
    prev_close = None
    
    # For gap effect intraday paths
    large_up_paths = []
    small_up_paths = []
    flat_paths = []
    small_dn_paths = []
    large_dn_paths = []
    
    # Gap fill times
    gap_fill_bars = []
    
    for date, group in df.groupby('date'):
        group = group.sort_values('datetime')
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        day_high = group['high'].max()
        day_low = group['low'].min()
        
        # Calculate gap metrics
        gap = (day_open - prev_close) if prev_close is not None else None
        gap_pct = (gap / prev_close * 100) if prev_close is not None else None
        
        # Calculate intraday returns
        intraday_ret = (day_close - day_open) / day_open * 100
        cc_ret = (day_close - prev_close) / prev_close * 100 if prev_close is not None else None
        
        day_range = day_high - day_low
        close_in_range = (day_close - day_low) / day_range if day_range > 0 else 0.5
        
        # Find high and low bar numbers (1 to 48)
        group['bar_number'] = np.arange(1, 49)
        high_bar = group.loc[group['high'].idxmax()]['bar_number']
        low_bar = group.loc[group['low'].idxmin()]['bar_number']
        
        # Intraday cumulative path (open to close of each bar)
        path = (group['close'].values - day_open) / day_open * 100
        
        # Check gap fill
        filled = False
        fill_bar = None
        
        if prev_close is not None:
            # Significant gap is > 0.05% or < -0.05%
            if gap_pct > 0.05:
                # Filled if low <= prev_close
                for idx, row in group.iterrows():
                    if row['low'] <= prev_close:
                        filled = True
                        fill_bar = row['bar_number']
                        break
            elif gap_pct < -0.05:
                # Filled if high >= prev_close
                for idx, row in group.iterrows():
                    if row['high'] >= prev_close:
                        filled = True
                        fill_bar = row['bar_number']
                        break
            
            # Categorize path for gap effect
            if gap_pct > 0.8:
                large_up_paths.append(path)
            elif gap_pct > 0.1:
                small_up_paths.append(path)
            elif gap_pct >= -0.1:
                flat_paths.append(path)
            elif gap_pct >= -0.8:
                small_dn_paths.append(path)
            else:
                large_dn_paths.append(path)
                
            if abs(gap_pct) > 0.05:
                gap_fill_bars.append({
                    'gap_pct': gap_pct,
                    'filled': filled,
                    'fill_bar': fill_bar
                })
        
        daily_stats.append({
            'date': date,
            'year': date.year,
            'month': date.month,
            'day_of_week': date.weekday(),
            'open': day_open,
            'close': day_close,
            'high': day_high,
            'low': day_low,
            'gap_pct': gap_pct,
            'intraday_ret': intraday_ret,
            'cc_ret': cc_ret,
            'close_in_range': close_in_range,
            'high_bar': high_bar,
            'low_bar': low_bar,
            'same_bar': high_bar == low_bar
        })
        
        prev_close = day_close
        
    daily_df = pd.DataFrame(daily_stats)
    gap_fill_df = pd.DataFrame(gap_fill_bars)
    
    # Create directory for output
    out_dir = os.path.join(OUT_BASE_DIR, etf_key)
    os.makedirs(out_dir, exist_ok=True)
    
    # ------------------ PLOTS GENERATION ------------------
    
    # Helper for CDF overlay on histograms
    def plot_hist_cdf(data, bins, r_min, r_max, color, title, xlabel, filename, is_time=False):
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Hist
        counts, edges, _ = ax1.hist(data, bins=bins, range=(r_min, r_max), edgecolor='black', alpha=0.6, color=color)
        ax1.set_ylabel('Frequency', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        
        if is_time:
            ax1.set_xticks(TICK_INDICES)
            ax1.set_xticklabels(TICK_LABELS, rotation=45)
            ax1.set_xlabel('Time of Day')
        else:
            ax1.set_xlabel(xlabel)
            
        ax1.grid(True, alpha=0.3)
        
        # CDF
        ax2 = ax1.twinx()
        sorted_data = np.sort(data)
        yvals = np.arange(len(sorted_data)) / float(len(sorted_data) - 1) * 100
        ax2.plot(sorted_data, yvals, color='black', linewidth=2, label='Cumulative %')
        ax2.set_ylabel('Cumulative %', color='black')
        ax2.set_ylim(0, 105)
        
        for pct in [50, 80, 95]:
            ax2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)
            
        plt.title(f"{name}\n{title}", fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, filename))
        plt.close()

    # 1. High Bar Distribution
    plot_hist_cdf(daily_df['high_bar'], 48, 1, 48.5, 'green', 
                  'Distribution of Daily High Bar Occurrence', 
                  'Bar Number', 'high_dist.png', is_time=True)

    # 2. Low Bar Distribution
    plot_hist_cdf(daily_df['low_bar'], 48, 1, 48.5, 'red', 
                  'Distribution of Daily Low Bar Occurrence', 
                  'Bar Number', 'low_dist.png', is_time=True)

    # 3. Extremes Distribution
    fig, ax1 = plt.subplots(figsize=(10, 6))
    first_ext = daily_df[['high_bar', 'low_bar']].min(axis=1)
    second_ext = daily_df[['high_bar', 'low_bar']].max(axis=1)
    
    ax1.hist(first_ext, bins=48, range=(1, 49), edgecolor='black', alpha=0.4, color='blue', label='First Extreme')
    ax1.hist(second_ext, bins=48, range=(1, 49), edgecolor='black', alpha=0.4, color='orange', label='Second Extreme')
    ax1.set_ylabel('Frequency')
    ax1.set_xticks(TICK_INDICES)
    ax1.set_xticklabels(TICK_LABELS, rotation=45)
    ax1.set_xlabel('Time of Day')
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    sorted_first = np.sort(first_ext)
    y_first = np.arange(len(sorted_first)) / float(len(sorted_first) - 1) * 100
    ax2.plot(sorted_first, y_first, color='blue', linewidth=2, label='First Cumulative %')
    
    sorted_second = np.sort(second_ext)
    y_second = np.arange(len(sorted_second)) / float(len(sorted_second) - 1) * 100
    ax2.plot(sorted_second, y_second, color='chocolate', linewidth=2, label='Second Cumulative %')
    
    ax2.set_ylabel('Cumulative %')
    ax2.set_ylim(0, 105)
    for pct in [50, 80, 95]:
        ax2.axhline(y=pct, color='gray', linestyle=':', alpha=0.5)
        
    plt.title(f"{name}\nTime to Form Daily Extremes", fontweight='bold')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=4)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'extremes_dist.png'), bbox_inches='tight')
    plt.close()

    # 4. High/Low Sequence
    plt.figure(figsize=(6, 6))
    low_first = (daily_df['low_bar'] < daily_df['high_bar']).sum()
    high_first = (daily_df['high_bar'] < daily_df['low_bar']).sum()
    same_bar = daily_df['same_bar'].sum()
    plt.pie([low_first, high_first, same_bar], labels=['Low First', 'High First', 'Same Bar'], 
            autopct='%1.1f%%', colors=['#ff6b6b', '#51cf66', '#ffd43b'], startangle=90,
            wedgeprops={'edgecolor': 'black', 'linewidth': 1, 'antialiased': True})
    plt.title(f"{name}\nHigh/Low Bar Sequence", fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'high_low_sequence.png'))
    plt.close()

    # 5. Gap Distribution (High Precision)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    gaps = daily_df['gap_pct'].dropna()
    
    # We focus on the high precision range [-2.0%, +2.0%]
    zoom_gaps = gaps[(gaps >= -2.0) & (gaps <= 2.0)]
    sns.histplot(zoom_gaps, bins=80, kde=True, ax=ax1, color='purple', edgecolor='black', alpha=0.6, label='Gap % Density')
    ax1.set_xlabel('Opening Gap %')
    ax1.set_ylabel('Count / Density')
    ax1.set_xlim(-2.0, 2.0)
    ax1.grid(True, alpha=0.3)
    
    # Stat text box
    stats_text = (
        f"Total Days: {len(gaps)}\n"
        f"Mean Gap: {gaps.mean():.3f}%\n"
        f"Median: {gaps.median():.3f}%\n"
        f"Std Dev: {gaps.std():.3f}%\n"
        f"Skewness: {skew(gaps):.3f}\n"
        f"Kurtosis: {kurtosis(gaps):.3f}\n"
        f"Gap Up (>0%): {(gaps > 0).mean()*100:.1f}%\n"
        f"Gap Down (<0%): {(gaps < 0).mean()*100:.1f}%"
    )
    ax1.text(0.03, 0.95, stats_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
             
    plt.title(f"{name}\nOpening Gap Distribution (High Precision)", fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'gap_dist.png'))
    plt.close()

    # 6. Gap Effect on Intraday Cumulative Path
    plt.figure(figsize=(10, 6))
    categories = [
        ('Large Gap Up (>0.8%)', large_up_paths, 'darkgreen'),
        ('Small Gap Up (0.1% to 0.8%)', small_up_paths, 'limegreen'),
        ('Flat / No Gap (-0.1% to 0.1%)', flat_paths, 'gray'),
        ('Small Gap Down (-0.8% to -0.1%)', small_dn_paths, 'salmon'),
        ('Large Gap Down (<-0.8%)', large_dn_paths, 'darkred')
    ]
    
    for label, paths, color in categories:
        if len(paths) > 0:
            avg_path = np.mean(paths, axis=0)
            plt.plot(avg_path, label=f"{label} (n={len(paths)})", color=color, linewidth=2)
            
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)
    plt.xticks(TICK_INDICES, TICK_LABELS, rotation=45)
    plt.xlabel('Time of Day')
    plt.ylabel('Average Cumulative Return from Open (%)')
    plt.title(f"{name}\nIntraday Price Trajectory by Opening Gap Size", fontweight='bold')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'gap_effect_intraday.png'))
    plt.close()

    # 7. Gap vs Intraday Return Scatter
    plt.figure(figsize=(10, 6))
    clean_df = daily_df[['gap_pct', 'intraday_ret']].dropna()
    # Filter outliers for visualization
    vis_df = clean_df[(clean_df['gap_pct'] >= -3) & (clean_df['gap_pct'] <= 3) & 
                      (clean_df['intraday_ret'] >= -4) & (clean_df['intraday_ret'] <= 4)]
                      
    sns.regplot(data=vis_df, x='gap_pct', y='intraday_ret', 
                scatter_kws={'alpha': 0.3, 'color': 'royalblue', 's': 15},
                line_kws={'color': 'darkorange', 'linewidth': 2})
    
    corr_coef = clean_df['gap_pct'].corr(clean_df['intraday_ret'])
    plt.text(0.05, 0.95, f"Correlation: {corr_coef:.3f}", transform=plt.gca().transAxes,
             fontsize=12, fontweight='bold', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
             
    plt.xlabel('Opening Gap %')
    plt.ylabel('Intraday Return % (Close/Open - 1)')
    plt.title(f"{name}\nOpening Gap vs. Intraday Return", fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'gap_vs_return_scatter.png'))
    plt.close()

    # 8. Gap Fill Analysis
    if len(gap_fill_df) > 0:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Buckets for fill rate
        gap_fill_df['gap_bucket'] = pd.cut(gap_fill_df['gap_pct'], 
                                           bins=[-np.inf, -1.0, -0.5, -0.05, 0.05, 0.5, 1.0, np.inf],
                                           labels=['<-1.0%', '-1.0% to -0.5%', '-0.5% to -0.05%', 'Flat', '0.05% to 0.5%', '0.5% to 1.0%', '>1.0%'])
                                           
        fill_rates = gap_fill_df.groupby('gap_bucket', observed=False)['filled'].mean() * 100
        counts_bucket = gap_fill_df.groupby('gap_bucket', observed=False).size()
        
        # Plot fill rates
        colors_bucket = ['darkred', 'crimson', 'salmon', 'lightgray', 'limegreen', 'green', 'darkgreen']
        bars = ax1.bar(fill_rates.index, fill_rates.values, color=colors_bucket, edgecolor='black', alpha=0.7)
        ax1.set_ylabel('Gap Fill Rate (%)')
        ax1.set_ylim(0, 110)
        ax1.set_title('Gap Fill Rate by Opening Gap Size')
        ax1.set_xticklabels(fill_rates.index, rotation=30, ha='right')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add labels on top of bars
        for bar, count in zip(bars, counts_bucket):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 2, f"{height:.1f}%\n(n={count})",
                     ha='center', va='bottom', fontsize=8)
                     
        # Time to fill distribution
        fill_times = gap_fill_df[gap_fill_df['filled'] & gap_fill_df['fill_bar'].notna()]['fill_bar'].values
        ax2.hist(fill_times, bins=48, range=(1, 49), color='indigo', edgecolor='black', alpha=0.6)
        ax2.set_xlabel('Time Gap First Filled')
        ax2.set_ylabel('Frequency')
        ax2.set_xticks(TICK_INDICES)
        ax2.set_xticklabels(TICK_LABELS, rotation=45)
        ax2.set_title('Distribution of Time to Fill Gaps')
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(f"{name}\nOpening Gap Fill Analysis", fontweight='bold', fontsize=16)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'gap_fill_analysis.png'))
        plt.close()

    # 9. Close Location in Range
    plot_hist_cdf(daily_df['close_in_range'] * 100, 50, 0, 100, 'blue',
                  'Daily Close Location in Range',
                  'Location (% of Range: 0=Low, 100=High)', 'close_loc.png')

    # 10. Yearly Return Distribution
    plt.figure(figsize=(10, 6))
    clean_cc = daily_df.dropna(subset=['cc_ret'])
    # Filter extreme returns for boxplot readability
    q_low, q_high = clean_cc['cc_ret'].quantile(0.005), clean_cc['cc_ret'].quantile(0.995)
    vis_cc = clean_cc[(clean_cc['cc_ret'] >= q_low) & (clean_cc['cc_ret'] <= q_high)]
    
    sns.boxplot(data=vis_cc, x='year', y='cc_ret', palette='viridis', hue='year', legend=False)
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)
    plt.xlabel('Year')
    plt.ylabel('Daily Close-to-Close Return (%)')
    plt.title(f"{name}\nDaily Return Distribution by Year", fontweight='bold')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'yearly_return_dist.png'))
    plt.close()

    # 11. Monthly Return Heatmap
    # Group by year and month and compute compound return or sum return
    # Here, let's compute monthly cumulative return from daily returns:
    # return = (product of (1 + r/100) - 1) * 100
    daily_df['cc_ret_raw'] = daily_df['cc_ret'] / 100
    monthly_perf = daily_df.groupby(['year', 'month'])['cc_ret_raw'].apply(lambda x: (np.prod(1 + x.dropna()) - 1) * 100).reset_index()
    
    heatmap_data = monthly_perf.pivot(index='year', columns='month', values='cc_ret_raw')
    # Column mapping to month names
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    heatmap_data.columns = [month_names[m-1] for m in heatmap_data.columns]
    
    plt.figure(figsize=(12, 8))
    # Diverging color palette: RdYlGn (Red - Yellow - Green) centered at 0
    sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="RdYlGn", center=0, cbar_kws={'label': 'Monthly Return (%)'},
                linewidths=.5, annot_kws={"size": 9})
    plt.xlabel('Month')
    plt.ylabel('Year')
    plt.title(f"{name}\nMonthly Returns Heatmap (%)", fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'monthly_return_heatmap.png'))
    plt.close()

    # 12. Seasonality (Day of Week and Month of Year)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Day of week
    dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    dow_stats = daily_df.groupby('day_of_week')['cc_ret'].agg(['mean', 'std', 'count']).loc[0:4]
    
    ax1.bar([dow_names[i] for i in dow_stats.index], dow_stats['mean'], yerr=dow_stats['std']/np.sqrt(dow_stats['count']),
            color='skyblue', edgecolor='black', alpha=0.8, capsize=5)
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Average Daily Return (%)')
    ax1.set_title('Average Return by Day of Week')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Month of year
    month_stats = daily_df.groupby('month')['cc_ret'].agg(['mean', 'std', 'count'])
    ax2.bar([month_names[i-1] for i in month_stats.index], month_stats['mean'], yerr=month_stats['std']/np.sqrt(month_stats['count']),
            color='lightcoral', edgecolor='black', alpha=0.8, capsize=5)
    ax2.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Average Daily Return (%)')
    ax2.set_title('Average Return by Month of Year')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle(f"{name}\nSeasonality Analysis (with Standard Error bars)", fontweight='bold', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'seasonality_analysis.png'))
    plt.close()
    
    print(f"Finished generating plots for {name}.")

def main():
    print("Starting ETF intraday and daily statistics calculations...")
    for key, info in ETFS.items():
        analyze_etf(key, info)
    print("\nAll ETF statistics plots generated successfully.")

if __name__ == "__main__":
    main()
