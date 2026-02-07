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

def extended_stats(dfs, plot=False):
    print(f"\n{'='*60}")
    print(f" Extended Statistics & Creative Insights")
    print(f"{'='*60}")

    print("\n1. 'Sell in May and Go Away' Analysis (Annualized Returns)")
    print(f"{'Ticker':<10} | {'Nov-Apr':<12} | {'May-Oct':<12} | {'Difference':<10}")
    print(f"{'-'*55}")
    sell_may_data = []
    for ticker, df in dfs.items():
        df['Return'] = df['Close'].pct_change()
        nov_apr = df[df.index.month.isin([11, 12, 1, 2, 3, 4])]['Return'].mean() * 252
        may_oct = df[df.index.month.isin([5, 6, 7, 8, 9, 10])]['Return'].mean() * 252
        diff = nov_apr - may_oct
        print(f"{ticker:<10} | {nov_apr:>11.2%} | {may_oct:>11.2%} | {diff:>10.2%}")
        sell_may_data.append({'Ticker': ticker, 'Nov-Apr': nov_apr, 'May-Oct': may_oct})

    if plot:
        sm_df = pd.DataFrame(sell_may_data).set_index('Ticker')
        sm_df.plot(kind='bar', figsize=(10, 6))
        plt.title('Sell in May Analysis (Annualized Returns)')
        plt.ylabel('Annualized Return')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        filename = 'extended_stats_sell_in_may.png'
        plt.savefig(filename)
        plt.close()
        print(f"save the plot as {filename}")

    print("\n2. Volatility Comparison (Daily Std Dev)")
    print(f"{'Ticker':<10} | {'Intraday Std':<12} | {'Overnight Std':<12}")
    print(f"{'-'*55}")
    vol_data = []
    for ticker, df in dfs.items():
        df['Intraday_Ret'] = (df['Close'] - df['Open']) / df['Open']
        df['Overnight_Ret'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
        v_intra = df['Intraday_Ret'].std()
        v_over = df['Overnight_Ret'].std()
        print(f"{ticker:<10} | {v_intra:>12.4%} | {v_over:>13.4%}")
        vol_data.append({'Ticker': ticker, 'Intraday Std': v_intra, 'Overnight Std': v_over})

    if plot:
        v_df = pd.DataFrame(vol_data).set_index('Ticker')
        v_df.plot(kind='bar', figsize=(10, 6))
        plt.title('Volatility Comparison (Daily Std Dev)')
        plt.ylabel('Standard Deviation')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        filename = 'extended_stats_volatility.png'
        plt.savefig(filename)
        plt.close()
        print(f"save the plot as {filename}")

    print("\n3. ETF Correlation Matrix (based on Daily Returns)")
    returns_df = pd.DataFrame({ticker: df['Close'].pct_change() for ticker, df in dfs.items()}).dropna()
    corr_matrix = returns_df.corr()
    print(corr_matrix.to_string())

    if plot:
        plt.figure(figsize=(8, 6))
        plt.imshow(corr_matrix, cmap='RdYlGn', interpolation='none', aspect='auto')
        plt.colorbar()
        plt.xticks(range(len(corr_matrix)), corr_matrix.columns)
        plt.yticks(range(len(corr_matrix)), corr_matrix.index)
        plt.title('ETF Correlation Matrix')
        for i in range(len(corr_matrix)):
            for j in range(len(corr_matrix)):
                plt.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}', ha='center', va='center')
        filename = 'extended_stats_correlation.png'
        plt.savefig(filename)
        plt.close()
        print(f"save the plot as {filename}")

    try:
        qqq5m = pd.read_csv('data/QQQ5m.csv')
        qqq5m['time'] = pd.to_datetime(qqq5m['time'])
        qqq5m['time_only'] = qqq5m['time'].dt.time
        qqq5m['ret'] = qqq5m['close'].pct_change()
        time_stats = qqq5m.groupby('time_only')['ret'].mean()
        print("\n4. QQQ 5-Minute Intraday Pattern (Top 5 most positive/negative 5m intervals)")
        print("Top 5 Positive Intervals:")
        print(time_stats.sort_values(ascending=False).head(5).to_string(header=False))
        print("\nTop 5 Negative Intervals:")
        print(time_stats.sort_values().head(5).to_string(header=False))

        if plot:
            plt.figure(figsize=(12, 6))
            time_stats.plot()
            plt.title('QQQ 5-Minute Average Returns Pattern')
            plt.axhline(0, color='black', linewidth=0.8)
            plt.ylabel('Average 5m Return')
            plt.grid(True, alpha=0.3)
            filename = 'extended_stats_qqq_pattern.png'
            plt.savefig(filename)
            plt.close()
            print(f"save the plot as {filename}")

    except Exception as e:
        print(f"\nCould not analyze 5m data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plot', action='store_true', help='Generate plots')
    args = parser.parse_args()

    etfs = {'IVV': 'data/IVV_1d.csv', 'QQQM': 'data/QQQM_1d.csv', 'VUG': 'data/VUG_1d.csv'}
    dfs = {}
    for ticker, path in etfs.items():
        try:
            dfs[ticker] = load_data(path)
        except Exception as e:
            print(f"Error loading {ticker}: {e}")
    
    if dfs:
        extended_stats(dfs, plot=args.plot)