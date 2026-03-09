import pandas as pd
import os

def sum_indices():
    hs300_path = "/home/hallo/Documents/display/data/hs300.csv"
    zz500_path = "/home/hallo/Documents/display/data/zz500.csv"
    output_path = "/home/hallo/Documents/display/data/hs300_zz500_sum.csv"

    if not os.path.exists(hs300_path) or not os.path.exists(zz500_path):
        print("Required files missing.")
        return

    print("Loading hs300.csv...")
    df_hs = pd.read_csv(hs300_path)
    print("Loading zz500.csv...")
    df_zz = pd.read_csv(zz500_path)

    # Ensure column Volume is consistently named if needed, but they both have 'Volume'
    cols_to_sum = ['open', 'high', 'low', 'close', 'Volume']
    
    print("Merging on 'time'...")
    # Inner join to combine only rows where the time exists in both
    merged = pd.merge(df_hs, df_zz, on='time', suffixes=('_hs', '_zz'))
    
    print(f"Aliged {len(merged)} common time points.")
    
    # Create the summed dataframe
    summed_df = pd.DataFrame()
    summed_df['time'] = merged['time']
    
    for col in cols_to_sum:
        summed_df[col] = merged[f'{col}_hs'] + merged[f'{col}_zz']
        if col != 'Volume':
            summed_df[col] = summed_df[col].round(4)
        
    print(f"Summing complete. Saving to {output_path}...")
    summed_df.to_csv(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    sum_indices()
