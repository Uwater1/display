import pandas as pd
import numpy as np
import argparse
import matplotlib.pyplot as plt

def load_data(file_path):
    df = pd.read_csv(file_path, skiprows=[1, 2])
    df.rename(columns={'Price': 'Date'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df.sort_index()
    return df

def analyze_weekdays(df, ticker, plot=False):
    df['Return'] = df['Close'].pct_change()
    df['Weekday'] = df.index.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    stats = df.groupby('Weekday')['Return'].agg(['mean', 'std', 'count', lambda x: (x > 0).mean()])
    stats.columns = ['Mean Return', 'Volatility', 'Days', 'Win Rate']
    stats = stats.reindex(order)

    print(f"\n{'='*60}")
    print(f" Weekday Performance for {ticker}")
    print(f"{'='*60}")
    print(stats.to_string(formatters={
        'Mean Return': '{:,.4%}'.format,
        'Volatility': '{:,.4%}'.format,
        'Win Rate': '{:,.2%}'.format
    }))
    best_day = stats['Mean Return'].idxmax()
    worst_day = stats['Mean Return'].idxmin()
    low_vol = stats['Volatility'].idxmin()
    high_vol = stats['Volatility'].idxmax()
    
    print(f"\nBest Day: {best_day} ({stats.loc[best_day, 'Mean Return']:.4%})")
    print(f"Worst Day: {worst_day} ({stats.loc[worst_day, 'Mean Return']:.4%})")
    print(f"Lowest Volatility: {low_vol} ({stats.loc[low_vol, 'Volatility']:.4%})")
    print(f"Highest Volatility: {high_vol} ({stats.loc[high_vol, 'Volatility']:.4%})")

    if plot:
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Mean Return on left axis
        stats['Mean Return'].plot(kind='bar', ax=ax1, color='skyblue', alpha=0.7, label='Mean Return')
        ax1.set_ylabel('Mean Return', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1.axhline(0, color='black', linewidth=0.8)
        ax1.grid(axis='y', linestyle='--', alpha=0.3)
        
        # Volatility on right axis
        ax2 = ax1.twinx()
        ax2.plot(stats.index, stats['Volatility'], color='red', marker='*', markersize=12, linestyle='-', linewidth=1, label='Volatility')
        ax2.set_ylabel('Volatility', color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        
        plt.title(f'Mean Return and Volatility by Weekday - {ticker}')
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        filename = f'weekday_analysis_{ticker}.png'
        plt.savefig(filename)
        plt.close()
        print(f"save the plot as {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plot', action='store_true', help='Generate plots')
    args = parser.parse_args()

    etfs = {'IVV': 'data/IVV_1d.csv', 'QQQM': 'data/QQQM_1d.csv', 'VUG': 'data/VUG_1d.csv'}
    for ticker, path in etfs.items():
        try:
            df = load_data(path)
            analyze_weekdays(df, ticker, plot=args.plot)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")