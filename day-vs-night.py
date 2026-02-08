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

def analyze_strategies(df, ticker, plot=False):
    df['Intraday_Ret'] = (df['Close'] - df['Open']) / df['Open']
    df['Overnight_Ret'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
    df['Total_Ret'] = df['Close'].pct_change()

    cum_intraday = (1 + df['Intraday_Ret']).prod() - 1
    cum_overnight = (1 + df['Overnight_Ret'].dropna()).prod() - 1
    cum_total = (1 + df['Total_Ret'].dropna()).prod() - 1

    n_years = (df.index[-1] - df.index[0]).days / 365.25
    ann_intraday = (1 + cum_intraday)**(1/n_years) - 1
    ann_overnight = (1 + cum_overnight)**(1/n_years) - 1
    ann_total = (1 + cum_total)**(1/n_years) - 1

    print(f"\n{'='*40}")
    print(f" Strategy Comparison for {ticker}")
    print(f" Period: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"{'='*40}")
    print(f"{'Strategy':<20} | {'Total Return':<12} | {'Annualized':<12}")
    print(f"{'-'*40}")
    print(f"{'Intraday (9:30-16:00)':<20} | {cum_intraday:>11.2%} | {ann_intraday:>11.2%}")
    print(f"{'Overnight (16:00-9:30)':<20} | {cum_overnight:>11.2%} | {ann_overnight:>11.2%}")
    print(f"{'Buy & Hold':<20} | {cum_total:>11.2%} | {ann_total:>11.2%}")
    
    win_intra = (df['Intraday_Ret'] > 0).mean()
    win_over = (df['Overnight_Ret'] > 0).mean()
    print(f"\nWin Rate (Positive Days):")
    print(f"Intraday: {win_intra:.2%}")
    print(f"Overnight: {win_over:.2%}")

    if plot:
        plt.figure(figsize=(12, 6))
        (1 + df['Intraday_Ret']).cumprod().plot(label='Intraday')
        (1 + df['Overnight_Ret'].fillna(0)).cumprod().plot(label='Overnight')
        (1 + df['Total_Ret'].fillna(0)).cumprod().plot(label='Buy & Hold')
        plt.title(f'Cumulative Returns - {ticker}')
        plt.legend()
        plt.grid(True)
        filename = f'strategy_comparison_{ticker}.png'
        plt.savefig(filename)
        plt.close()
        print(f"save the plot as {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--plot', action='store_true', help='Generate plots')
    args = parser.parse_args()

    etfs = {
        'IVV': 'data/IVV_1d.csv',
        'QQQM': 'data/QQQM_1d.csv',
        'VUG': 'data/VUG_1d.csv'
    }
    for ticker, path in etfs.items():
        try:
            df = load_data(path)
            analyze_strategies(df, ticker, plot=args.plot)
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")