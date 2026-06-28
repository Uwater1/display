#!/usr/bin/env python3
"""
ETF and Index Intraday and Daily Statistics Analyzer
Computes standard daytrading and liquidity statistics for SSE 50, CSI 300, CSI 500, ChiNext, STAR 50, and CSI 800.
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
    },
    'csi800': {
        'name': 'CSI 800 Index',
        'file': 'data/800.csv',
        'volume_file': 'data/hs300_zz500_sum.csv'
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

TICK_INDICES = [0, 5, 11, 17, 23, 24, 29, 35, 41, 47]
TICK_LABELS = [BAR_LABELS[i] for i in TICK_INDICES]

def analyze_etf(etf_key, etf_info):
    name = etf_info['name']
    filepath = etf_info['file']
    print(f"\nProcessing {name} ({filepath})...")
    
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found. Skipping.")
        return
        
    # Read and standardize data
    if filepath.endswith('.parquet'):
        df = pd.read_parquet(filepath)
        df = df.sort_values('datetime')
        df['date'] = df['datetime'].dt.date
    else:  # CSV format (csi800)
        df = pd.read_csv(filepath)
        # Parse time column and convert to Asia/Shanghai, then localize to naive datetime
        df['datetime'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
        df = df.sort_values('datetime')
        df['date'] = df['datetime'].dt.date
        # Exclude the 09:30 and 13:00 bars to align with standard 48 ETF bars
        df['time_of_day'] = df['datetime'].dt.time
        df = df[~df['time_of_day'].isin([pd.to_datetime('09:30:00').time(), pd.to_datetime('13:00:00').time()])]
        df = df.drop(columns=['time_of_day'])
    
    # Filter for standard days (exactly 48 bars)
    counts = df.groupby('date').size()
    valid_dates = counts[counts == 48].index
    df = df[df['date'].isin(valid_dates)].copy()
    
    print(f"Loaded {len(valid_dates)} trading days.")
    if len(valid_dates) == 0:
        return

    # Add bar number (1 to 48)
    df['bar_number'] = df.groupby('date').cumcount() + 1
    
    # Pre-calculate daily statistics
    daily_stats = []
    prev_close = None
    
    large_up_paths = []
    small_up_paths = []
    flat_paths = []
    small_dn_paths = []
    large_dn_paths = []
    
    gap_fill_bars = []
    first_hour_stats = []
    
    for date, group in df.groupby('date'):
        group = group.sort_values('datetime')
        day_open = group.iloc[0]['open']
        day_close = group.iloc[-1]['close']
        day_high = group['high'].max()
        day_low = group['low'].min()
        
        # Gap metrics
        gap = (day_open - prev_close) if prev_close is not None else None
        gap_pct = (gap / prev_close * 100) if prev_close is not None else None
        
        # Intraday returns
        intraday_ret = (day_close - day_open) / day_open * 100
        cc_ret = (day_close - prev_close) / prev_close * 100 if prev_close is not None else None
        
        day_range = day_high - day_low
        close_in_range = (day_close - day_low) / day_range if day_range > 0 else 0.5
        
        # Find high and low bar numbers (1 to 48)
        high_bar = group.loc[group['high'].idxmax()]['bar_number']
        low_bar = group.loc[group['low'].idxmin()]['bar_number']
        
        # Intraday cumulative path (open to close of each bar)
        path = (group['close'].values - day_open) / day_open * 100
        
        # First Hour (first 12 bars, 9:30 - 10:30) range contribution
        first_hour_df = group[group['bar_number'] <= 12]
        first_hour_range = first_hour_df['high'].max() - first_hour_df['low'].min()
        first_hour_pct = (first_hour_range / day_range * 100) if day_range > 0 else 0
        first_hour_stats.append(first_hour_pct)
        
        # Check gap fill
        filled = False
        fill_bar = None
        
        if prev_close is not None:
            if gap_pct > 0.05:
                for idx, row in group.iterrows():
                    if row['low'] <= prev_close:
                        filled = True
                        fill_bar = row['bar_number']
                        break
            elif gap_pct < -0.05:
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
            'same_bar': high_bar == low_bar,
            'first_hour_pct': first_hour_pct
        })
        
        prev_close = day_close
        
    daily_df = pd.DataFrame(daily_stats)
    gap_fill_df = pd.DataFrame(gap_fill_bars)
    
    # Calculate consecutive growing (up) and falling (down) streaks prior to each day
    up_streaks = []
    down_streaks = []
    for i in range(len(daily_df)):
        if i == 0:
            up_streaks.append(0)
            down_streaks.append(0)
            continue
            
        u_count = 0
        j = i - 1
        while j >= 0 and daily_df.iloc[j]['cc_ret'] is not None and daily_df.iloc[j]['cc_ret'] > 0:
            u_count += 1
            j -= 1
        up_streaks.append(u_count)
        
        d_count = 0
        j = i - 1
        while j >= 0 and daily_df.iloc[j]['cc_ret'] is not None and daily_df.iloc[j]['cc_ret'] < 0:
            d_count += 1
            j -= 1
        down_streaks.append(d_count)
        
    daily_df['up_streak'] = up_streaks
    daily_df['down_streak'] = down_streaks
    
    
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
    zoom_gaps = gaps[(gaps >= -2.0) & (gaps <= 2.0)]
    sns.histplot(zoom_gaps, bins=80, kde=True, ax=ax1, color='purple', edgecolor='black', alpha=0.6, label='Gap % Density')
    ax1.set_xlabel('Opening Gap %')
    ax1.set_ylabel('Count / Density')
    ax1.set_xlim(-2.0, 2.0)
    ax1.grid(True, alpha=0.3)
    
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
        
        gap_fill_df['gap_bucket'] = pd.cut(gap_fill_df['gap_pct'], 
                                           bins=[-np.inf, -1.0, -0.5, -0.05, 0.05, 0.5, 1.0, np.inf],
                                           labels=['<-1.0%', '-1.0% to -0.5%', '-0.5% to -0.05%', 'Flat', '0.05% to 0.5%', '0.5% to 1.0%', '>1.0%'])
                                           
        fill_rates = gap_fill_df.groupby('gap_bucket', observed=False)['filled'].mean() * 100
        counts_bucket = gap_fill_df.groupby('gap_bucket', observed=False).size()
        
        colors_bucket = ['darkred', 'crimson', 'salmon', 'lightgray', 'limegreen', 'green', 'darkgreen']
        bars = ax1.bar(fill_rates.index, fill_rates.values, color=colors_bucket, edgecolor='black', alpha=0.7)
        ax1.set_ylabel('Gap Fill Rate (%)')
        ax1.set_ylim(0, 110)
        ax1.set_title('Gap Fill Rate by Opening Gap Size')
        ax1.set_xticklabels(fill_rates.index, rotation=30, ha='right')
        ax1.grid(True, alpha=0.3, axis='y')
        
        for bar, count in zip(bars, counts_bucket):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 2, f"{height:.1f}%\n(n={count})",
                     ha='center', va='bottom', fontsize=8)
                     
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
    daily_df['cc_ret_raw'] = daily_df['cc_ret'] / 100
    monthly_perf = daily_df.groupby(['year', 'month'])['cc_ret_raw'].apply(lambda x: (np.prod(1 + x.dropna()) - 1) * 100).reset_index()
    
    heatmap_data = monthly_perf.pivot(index='year', columns='month', values='cc_ret_raw')
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # Filter out columns that are not integers between 1 and 12
    valid_cols = [col for col in heatmap_data.columns if isinstance(col, (int, np.integer)) and 1 <= col <= 12]
    heatmap_data = heatmap_data[valid_cols]
    heatmap_data.columns = [month_names[int(m)-1] for m in heatmap_data.columns]
    
    plt.figure(figsize=(12, 8))
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
    
    dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    dow_stats = daily_df.groupby('day_of_week')['cc_ret'].agg(['mean', 'std', 'count']).loc[0:4]
    
    ax1.bar([dow_names[i] for i in dow_stats.index], dow_stats['mean'], yerr=dow_stats['std']/np.sqrt(dow_stats['count']),
            color='skyblue', edgecolor='black', alpha=0.8, capsize=5)
    ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Average Daily Return (%)')
    ax1.set_title('Average Return by Day of Week')
    ax1.grid(True, alpha=0.3, axis='y')
    
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

    # 13. Top Bars for High/Low (common_bars)
    plt.figure(figsize=(12, 6))
    high_bar_counts = daily_df['high_bar'].value_counts().head(10).sort_index()
    low_bar_counts = daily_df['low_bar'].value_counts().head(10).sort_index()
    all_top_bars = sorted(set(list(high_bar_counts.index) + list(low_bar_counts.index)))
    high_vals = [high_bar_counts.get(b, 0) for b in all_top_bars]
    low_vals = [low_bar_counts.get(b, 0) for b in all_top_bars]
    x = np.arange(len(all_top_bars))
    width = 0.35
    plt.bar(x - width/2, high_vals, width, label='High', color='green', alpha=0.7)
    plt.bar(x + width/2, low_vals, width, label='Low', color='red', alpha=0.7)
    plt.xlabel('Bar Time')
    plt.ylabel('Frequency')
    plt.title(f"{name}\nMost Common 5m Bars for Day High/Low", fontweight='bold')
    plt.xticks(x, [BAR_LABELS[b-1] for b in all_top_bars], rotation=45)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'common_bars.png'))
    plt.close()

    # 14. First Hour Range Contribution
    plot_hist_cdf(first_hour_stats, 50, 0, 100, 'orange',
                  'First Hour (9:30 - 10:30) Range Contribution',
                  'First Hour Range as % of Day Range', 'first_hour.png')

    # 15. Time-based High/Low Buckets (time_buckets)
    plt.figure(figsize=(10, 6))
    bucket_labels = ['09:30-10:00', '10:00-10:30', '10:30-11:00', '11:00-11:30', 
                     '13:00-13:30', '13:30-14:00', '14:00-14:30', '14:30-15:00']
    bucket_ranges = [(1, 6), (7, 12), (13, 18), (19, 24), 
                     (25, 30), (31, 36), (37, 42), (43, 48)]
    high_buckets = [len(daily_df[(daily_df['high_bar'] >= r[0]) & (daily_df['high_bar'] <= r[1])]) for r in bucket_ranges]
    low_buckets = [len(daily_df[(daily_df['low_bar'] >= r[0]) & (daily_df['low_bar'] <= r[1])]) for r in bucket_ranges]
    
    x = np.arange(len(bucket_labels))
    width = 0.35
    plt.bar(x - width/2, high_buckets, width, label='High', color='green', alpha=0.7)
    plt.bar(x + width/2, low_buckets, width, label='Low', color='red', alpha=0.7)
    plt.ylabel('Number of Days')
    plt.title(f"{name}\nDay High/Low Occurrences by Time Period", fontweight='bold')
    plt.xticks(x, bucket_labels, rotation=30)
    plt.legend()
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'time_buckets.png'))
    plt.close()

    # 16. Gap Size Categories
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
    plt.title(f"{name}\nGap Size Categories", fontweight='bold')
    plt.grid(alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'gap_categories.png'))
    plt.close()

    # 21. Growing Streak Trend Following
    win_rates_up, counts_up, avg_rets_up = [], [], []
    win_rates_down, counts_down, avg_rets_down = [], [], []
    streak_labels = ['1 Day', '2 Days', '3 Days', '4 Days', '5 Days', '6 Days', '7+ Days']

    for n in range(1, 8):
        # Up streak
        sub_up = daily_df[daily_df['up_streak'] == n] if n < 7 else daily_df[daily_df['up_streak'] >= 7]
        cnt_u = len(sub_up)
        counts_up.append(cnt_u)
        win_rates_up.append((sub_up['cc_ret'] > 0).mean() * 100 if cnt_u > 0 else 0)
        avg_rets_up.append(sub_up['cc_ret'].mean() if cnt_u > 0 else 0)

        # Down streak
        sub_dn = daily_df[daily_df['down_streak'] == n] if n < 7 else daily_df[daily_df['down_streak'] >= 7]
        cnt_d = len(sub_dn)
        counts_down.append(cnt_d)
        win_rates_down.append((sub_dn['cc_ret'] < 0).mean() * 100 if cnt_d > 0 else 0)
        avg_rets_down.append(sub_dn['cc_ret'].mean() if cnt_d > 0 else 0)

    fig, ax1 = plt.subplots(figsize=(10, 6))
    x = np.arange(len(streak_labels))
    width = 0.5
    bars = ax1.bar(x, win_rates_up, width, color='#2ecc71', edgecolor='black', alpha=0.8, label='Trend Following Chance (%)')
    ax1.set_ylabel('Trend Continuation Probability (%)', color='#1e8449')
    ax1.tick_params(axis='y', labelcolor='#1e8449')
    ax1.set_ylim(0, 105)
    ax1.set_xlabel('Prior Growing (Up) Streak Length')
    ax1.set_xticks(x)
    ax1.set_xticklabels(streak_labels)
    ax1.axhline(50, color='gray', linestyle='--', alpha=0.7, label='50% Baseline')
    ax1.grid(True, alpha=0.3, axis='y')

    for bar, wr, count in zip(bars, win_rates_up, counts_up):
        if count > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                     f"{wr:.1f}%\n(n={count})", ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax2 = ax1.twinx()
    ax2.plot(x, avg_rets_up, color='#e67e22', marker='o', linewidth=2.5, markersize=8, label='Avg Next-Day Return (%)')
    ax2.set_ylabel('Avg Next-Day Return (%)', color='#d35400')
    ax2.tick_params(axis='y', labelcolor='#d35400')
    ax2.axhline(0, color='black', linestyle=':', alpha=0.5)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.title(f"{name}\nChance of Trend Following after Growing for N Days", fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'trend_growing.png'), bbox_inches='tight')
    plt.close()

    # 22. Falling Streak Trend Following
    fig, ax1 = plt.subplots(figsize=(10, 6))
    bars = ax1.bar(x, win_rates_down, width, color='#e74c3c', edgecolor='black', alpha=0.8, label='Trend Following Chance (%)')
    ax1.set_ylabel('Trend Continuation Probability (%)', color='#922b21')
    ax1.tick_params(axis='y', labelcolor='#922b21')
    ax1.set_ylim(0, 105)
    ax1.set_xlabel('Prior Falling (Down) Streak Length')
    ax1.set_xticks(x)
    ax1.set_xticklabels(streak_labels)
    ax1.axhline(50, color='gray', linestyle='--', alpha=0.7, label='50% Baseline')
    ax1.grid(True, alpha=0.3, axis='y')

    for bar, wr, count in zip(bars, win_rates_down, counts_down):
        if count > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                     f"{wr:.1f}%\n(n={count})", ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax2 = ax1.twinx()
    ax2.plot(x, avg_rets_down, color='#2980b9', marker='s', linewidth=2.5, markersize=8, label='Avg Next-Day Return (%)')
    ax2.set_ylabel('Avg Next-Day Return (%)', color='#1b4f72')
    ax2.tick_params(axis='y', labelcolor='#1b4f72')
    ax2.axhline(0, color='black', linestyle=':', alpha=0.5)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.title(f"{name}\nChance of Trend Following after Falling for N Days", fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'trend_falling.png'), bbox_inches='tight')
    plt.close()


    # ------------------ LIQUIDITY CHARTS GENERATION ------------------
    # Now generate the 4 liquidity plots (vol, vol_pct, range, impact)
    print("Generating liquidity plots...")
    if etf_key != 'csi800':
        # For standard ETFs, calculate from Parquet data (5-minute resolution, 48 bars)
        df['turnover_million'] = df['total_turnover'] / 1e6
        df['range_pct'] = (df['high'] - df['low']) / df['open'] * 100
        df['impact'] = ((df['close'] - df['open']).abs() / df['open'] * 100) / (df['turnover_million'] + 1e-9)
        
        daily_total_turnover = df.groupby('date')['total_turnover'].transform('sum')
        df['turnover_pct_day'] = df['total_turnover'] / (daily_total_turnover + 1e-9) * 100
        
        bar_group = df.groupby('bar_number')
        
        # 17. Average Turnover (Volume)
        plt.figure(figsize=(12, 6))
        bar_group['turnover_million'].mean().plot(kind='bar', color='steelblue', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nAverage Intraday Turnover (RMB Millions)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('RMB Millions')
        plt.xticks(TICK_INDICES, TICK_LABELS, rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_vol.png'))
        plt.close()
        
        # 18. Volume % of Day
        plt.figure(figsize=(12, 6))
        bar_group['turnover_pct_day'].mean().plot(kind='bar', color='teal', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nIntraday Turnover % of Total Day", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('% of Daily Turnover')
        plt.xticks(TICK_INDICES, TICK_LABELS, rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_vol_pct.png'))
        plt.close()
        
        # 19. Average Range %
        plt.figure(figsize=(12, 6))
        bar_group['range_pct'].mean().plot(kind='bar', color='darkorange', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nAverage Intraday Price Range % (High-Low / Open)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('Range %')
        plt.xticks(TICK_INDICES, TICK_LABELS, rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_range.png'))
        plt.close()
        
        # 20. Price Impact (Illiquidity Proxy)
        plt.figure(figsize=(12, 6))
        # Filter extreme outliers from impact plotting
        impacts = bar_group['impact'].mean()
        impacts.plot(kind='bar', color='purple', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nPrice Impact per RMB Million Traded (Amihud Illiquidity)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('Return % per RMB Million')
        plt.xticks(TICK_INDICES, TICK_LABELS, rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_impact.png'))
        plt.close()
    
    else:
        # For csi800, load the external hs300_zz500_sum.csv (30-minute resolution, 8 buckets)
        vol_file = etf_info['volume_file']
        if not os.path.exists(vol_file):
            print(f"Error: {vol_file} not found. Skipping liquidity plots for {name}.")
            return
            
        vol_df = pd.read_csv(vol_file)
        vol_df['datetime'] = pd.to_datetime(vol_df['time'], utc=True).dt.tz_convert('Asia/Shanghai').dt.tz_localize(None)
        vol_df = vol_df.sort_values('datetime')
        vol_df['date'] = vol_df['datetime'].dt.date
        vol_df['time_of_day'] = vol_df['datetime'].dt.time
        
        def to_30m_bucket(t):
            minute = t.hour * 60 + t.minute
            if minute < 570: return "Pre-mkt"
            bucket_idx = (minute - 570) // 30
            start_min = 570 + bucket_idx * 30
            end_min = start_min + 30
            return f"{start_min//60:02d}:{start_min%60:02d} ~ {end_min//60:02d}:{end_min%60:02d}"
            
        vol_df['time_bucket'] = vol_df['time_of_day'].apply(to_30m_bucket)
        vol_df = vol_df[vol_df['time_bucket'] != "Pre-mkt"].copy()
        
        # Calculate standard 30m liquidity features
        vol_df['volume_million'] = vol_df['Volume'] / 1e6
        vol_df['range_pct'] = (vol_df['high'] - vol_df['low']) / vol_df['open'] * 100
        vol_df['impact'] = ((vol_df['close'] - vol_df['open']).abs() / vol_df['open'] * 100) / (vol_df['volume_million'] + 1e-9)
        
        daily_total_vol = vol_df.groupby('date')['Volume'].transform('sum')
        vol_df['volume_pct_day'] = vol_df['Volume'] / (daily_total_vol + 1e-9) * 100
        
        # Sort buckets chronologically
        bucket_order = sorted(vol_df['time_bucket'].unique())
        vol_df['time_bucket'] = pd.Categorical(vol_df['time_bucket'], categories=bucket_order, ordered=True)
        bucket_group = vol_df.groupby('time_bucket', observed=False)
        
        # 17. Average Volume
        plt.figure(figsize=(12, 6))
        bucket_group['volume_million'].mean().plot(kind='bar', color='steelblue', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nAverage Volume by Time of Day (HS300+ZZ500 Sum)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('Volume (Millions of Shares)')
        plt.xticks(rotation=30, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_vol.png'))
        plt.close()
        
        # 18. Volume % of Day
        plt.figure(figsize=(12, 6))
        bucket_group['volume_pct_day'].mean().plot(kind='bar', color='teal', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nPercentage of Daily Volume by Time of Day (HS300+ZZ500 Sum)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('% of Daily Volume')
        plt.xticks(rotation=30, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_vol_pct.png'))
        plt.close()
        
        # 19. Average Range %
        plt.figure(figsize=(12, 6))
        bucket_group['range_pct'].mean().plot(kind='bar', color='darkorange', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nAverage Price Range % by Time of Day (HS300+ZZ500 Sum)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('Range %')
        plt.xticks(rotation=30, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_range.png'))
        plt.close()
        
        # 20. Price Impact
        plt.figure(figsize=(12, 6))
        bucket_group['impact'].mean().plot(kind='bar', color='purple', edgecolor='black', alpha=0.8)
        plt.title(f"{name}\nPrice Impact per Million Shares (HS300+ZZ500 Sum)", fontweight='bold')
        plt.xlabel('Time of Day')
        plt.ylabel('Return % per Million Shares')
        plt.xticks(rotation=30, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'liquidity_impact.png'))
        plt.close()

    print(f"Finished generating all 22 plots for {name}.")

def main():
    print("Starting ETF intraday and daily statistics calculations...")
    for key, info in ETFS.items():
        analyze_etf(key, info)
    print("\nAll statistics plots generated successfully.")

if __name__ == "__main__":
    main()
