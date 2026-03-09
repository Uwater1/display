import pandas as pd
import glob
import os

def combine_csvs():
    # Define the pattern for the files
    file_pattern = "/home/hallo/Documents/display/500l[1-6].csv"
    files = sorted(glob.glob(file_pattern))
    
    if not files:
        print("No files matching 500l[1-6].csv found.")
        return

    print(f"Found files: {files}")
    
    # Read and concatenate
    dfs = []
    for f in files:
        print(f"Reading {f}...")
        df = pd.read_csv(f)
        dfs.append(df)
    
    combined_df = pd.concat(dfs, ignore_index=True)
    initial_len = len(combined_df)
    
    # Remove duplicates based on 'time' (assuming time is the unique key)
    # If 'time' column doesn't exist, we'll use all columns
    if 'time' in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['time'])
    else:
        combined_df = combined_df.drop_duplicates()
        
    final_len = len(combined_df)
    removed = initial_len - final_len
    print(f"Removed {removed} duplicates.")
    
    # Sort by time if column exists
    if 'time' in combined_df.columns:
        combined_df = combined_df.sort_values(by='time')
        
    # Save output
    output_file = "/home/hallo/Documents/display/500l_combined.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"Saved combined data to {output_file} (Total rows: {final_len})")

if __name__ == "__main__":
    combine_csvs()
