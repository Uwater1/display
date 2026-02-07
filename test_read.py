import pandas as pd

def load_data(file_path):
    df = pd.read_csv(file_path, skiprows=[1, 2])
    df.rename(columns={'Price': 'Date'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

try:
    ivv = load_data('data/IVV_1d.csv')
    print("IVV Data Head:")
    print(ivv.head())
    print("\nColumns:", ivv.columns)
except Exception as e:
    print(f"Error: {e}")