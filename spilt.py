#!/usr/bin/env python3
"""
Split CSV files with 5-minute trading data into chunks of exactly 2 trading days.

Each trading day contains 78 rows (5-minute intervals from 9:30 AM to 3:55 PM ET).
This script splits data into files containing exactly 2 trading days (156 data rows).

Usage:
    python split_trading_data.py [INPUT_FILE] [--output OUTPUT_DIR] [--rows-per-day ROWS]

Arguments:
    INPUT_FILE     Input CSV file path (default: qqq5m.csv)
    --output    Output directory path (default: current directory)
    --rows-per-day  Number of rows per trading day (default: 78)

Output:
    Named sequentially as output_001.csv, output_002.csv, etc.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple


# Constants
ROWS_PER_DAY = 78  # 5-minute intervals from 9:30 AM to 3:55 PM ET = 78 bars
DEFAULT_INPUT = "qqq5m.csv"
DEFAULT_OUTPUT_PREFIX = "output"


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Split CSV trading data into chunks of 2 trading days.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python split_trading_data.py data.csv
    python split_trading_data.py data.csv --output /tmp/split
    python split_trading_data.py --rows-per-day 78
        """
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default=DEFAULT_INPUT,
        help=f"Input CSV file path (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".",
        help="Output directory path (default: current directory)"
    )
    parser.add_argument(
        "--rows-per-day",
        type=int,
        default=ROWS_PER_DAY,
        help=f"Number of rows per trading day (default: {ROWS_PER_DAY})"
    )
    return parser.parse_args()


def read_csv_header(input_file: str) -> Tuple[str, List[str]]:
    """
    Read the header row from a CSV file.
    
    Args:
        input_file: Path to the input CSV file
        
    Returns:
        Tuple of (header_line, all_lines read so far)
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file is empty or has no header
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        header = f.readline().strip()
        if not header:
            raise ValueError(f"Input file '{input_file}' is empty or has no header")
        
        # Read all remaining lines
        lines = f.readlines()
        
    return header, lines


def count_total_rows(lines: List[str]) -> int:
    """
    Count the number of data rows (non-empty, non-comment lines).
    
    Args:
        lines: List of lines from the CSV file
        
    Returns:
        Number of valid data rows
    """
    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            count += 1
    return count


def write_chunk(
    output_dir: str,
    chunk_number: int,
    header: str,
    rows: List[str],
    use_date_filename: bool = True
) -> str:
    """
    Write a chunk of data to an output CSV file.
    
    Args:
        output_dir: Directory to write the output file
        chunk_number: Sequential chunk number (1-based)
        header: CSV header row
        rows: List of data rows to write
        use_date_filename: If True, name file after last trading day in chunk
        
    Returns:
        Path to the created file
    """
    if use_date_filename and rows:
        # Extract date from last row (format: 2024-02-12T09:30:00-05:00)
        last_row = rows[-1].strip()
        if last_row:
            # Split by comma and take first field (time column)
            time_field = last_row.split(',')[0]
            # Extract date portion (first 10 characters: YYYY-MM-DD)
            date_str = time_field[:10]
            filename = f"{date_str}.csv"
    else:
        # Fallback to sequential naming
        filename = f"{DEFAULT_OUTPUT_PREFIX}_{chunk_number:03d}.csv"
    
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n')
        for row in rows:
            f.write(row)
    
    return output_path


def split_csv(
    input_file: str,
    output_dir: str,
    rows_per_day: int = ROWS_PER_DAY,
    use_date_filename: bool = True
) -> Tuple[int, int, int]:
    """
    Split a CSV file into chunks of exactly 2 trading days.
    
    Args:
        input_file: Path to the input CSV file
        output_dir: Directory to write output files
        rows_per_day: Number of rows per trading day (default: 78)
        use_date_filename: If True, name files after last trading day
        
    Returns:
        Tuple of (total_chunks, complete_chunks, incomplete_rows)
    """
    # Read header and all data lines
    header, all_lines = read_csv_header(input_file)
    
    # Filter to get only valid data rows (non-empty, non-comment)
    data_rows = [line for line in all_lines if line.strip() and not line.strip().startswith('#')]
    total_data_rows = len(data_rows)
    
    # Calculate rows per chunk (2 trading days)
    rows_per_chunk = rows_per_day * 2
    
    # Calculate number of complete chunks and remaining rows
    total_chunks = (total_data_rows + rows_per_chunk - 1) // rows_per_chunk
    complete_chunks = total_data_rows // rows_per_chunk
    incomplete_rows = total_data_rows % rows_per_chunk
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process and write chunks
    chunk_number = 0
    for i in range(0, total_data_rows, rows_per_chunk):
        chunk_number += 1
        chunk_rows = data_rows[i:i + rows_per_chunk]
        
        output_path = write_chunk(output_dir, chunk_number, header, chunk_rows, use_date_filename)
        rows_written = len(chunk_rows)
        print(f"Created: {output_path} ({rows_written} rows)")
    
    return total_chunks, complete_chunks, incomplete_rows


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isfile(args.input):
        print(f"Error: '{args.input}' is not a file", file=sys.stderr)
        sys.exit(1)
    
    # Validate rows per day
    if args.rows_per_day <= 0:
        print(f"Error: rows-per-day must be positive, got {args.rows_per_day}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Splitting CSV file: {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Rows per trading day: {args.rows_per_day}")
    print(f"Rows per output file: {args.rows_per_day * 2}")
    print("-" * 50)
    
    try:
        total_chunks, complete_chunks, incomplete_rows = split_csv(
            args.input,
            args.output,
            args.rows_per_day
        )
        
        print("-" * 50)
        print(f"Summary:")
        print(f"  Total output files: {total_chunks}")
        print(f"  Complete (2-day) files: {complete_chunks}")
        
        if incomplete_rows > 0:
            print(f"  Incomplete file: {incomplete_rows} rows")
            print(f"  Note: Last file has less than 2 trading days of data")
        
        print("-" * 50)
        print(f"Files named after last trading day in each chunk (e.g., 2024-02-13.csv)")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
