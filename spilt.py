#!/usr/bin/env python3
"""
Split CSV files with 5-minute trading data into chunks of exactly 2 trading days.

Each trading day contains 78 rows (5-minute intervals from 9:30 AM to 3:55 PM ET).
This script splits data into files containing exactly 2 trading days.

The script detects trading day boundaries by looking for rows that start at 9:30 AM.
This handles half trading days (e.g., market closes early) correctly.

Usage:
    python split_trading_data.py [INPUT_FILE] [--output OUTPUT_DIR]

Arguments:
    INPUT_FILE     Input CSV file path (default: qqq5m.csv)
    --output    Output directory path (default: current directory)

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
TRADING_DAY_START = "T09:30:00"  # Trading day starts at 9:30 AM ET


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Split CSV trading data into chunks of 2 trading days.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python split_trading_data.py data.csv
    python split_trading_data.py data.csv --output /tmp/split
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


def is_trading_day_start(line: str) -> bool:
    """
    Check if a line represents the start of a trading day (9:30 AM).
    
    Args:
        line: A CSV data line
        
    Returns:
        True if the line starts at 9:30 AM, False otherwise
    """
    stripped = line.strip()
    if not stripped:
        return False
    
    # First field is the timestamp
    first_field = stripped.split(',')[0]
    
    # Check if it contains T09:30:00 (9:30 AM start)
    # Format: 2024-02-12T09:30:00-05:00
    return TRADING_DAY_START in first_field


def group_by_trading_days(lines: List[str]) -> List[List[str]]:
    """
    Group data lines by trading day based on 9:30 AM start times.
    
    Args:
        lines: List of data lines from CSV
        
    Returns:
        List of trading days, where each trading day is a list of its rows
    """
    trading_days = []
    current_day = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
            
        if is_trading_day_start(line):
            # Start of a new trading day
            if current_day:
                trading_days.append(current_day)
            current_day = [line]
        else:
            current_day.append(line)
    
    # Don't forget the last trading day
    if current_day:
        trading_days.append(current_day)
    
    return trading_days


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
        # Extract date from LAST row (format: 2024-02-12T09:30:00-05:00)
        # This names the file after the last trading day in the chunk
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
    use_date_filename: bool = True
) -> Tuple[int, int, int]:
    """
    Split a CSV file into chunks of exactly 2 trading days.
    
    The script detects trading day boundaries by looking for rows starting at 9:30 AM.
    This handles half trading days (e.g., market closes early) correctly.
    
    Args:
        input_file: Path to the input CSV file
        output_dir: Directory to write output files
        use_date_filename: If True, name files after last trading day
        
    Returns:
        Tuple of (total_chunks, complete_chunks, incomplete_chunks)
    """
    # Read header and all data lines
    header, all_lines = read_csv_header(input_file)
    
    # Group lines by trading day
    trading_days = group_by_trading_days(all_lines)
    
    if not trading_days:
        raise ValueError("No valid trading data found in the file")
    
    # Print trading day info
    print(f"Found {len(trading_days)} trading days in the file")
    print(f"Trading day 1: {len(trading_days[0])} rows")
    if len(trading_days) > 1:
        print(f"Trading day 2: {len(trading_days[1])} rows")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Group trading days into chunks of 2 with sliding window
    # Each trading day appears in 2 consecutive files (as last day of chunk N, first day of chunk N+1)
    # This creates overlapping chunks: [Day1+Day2], [Day2+Day3], [Day3+Day4], ...
    chunks = []
    for i in range(len(trading_days) - 1):
        # Each chunk contains trading_days[i] and trading_days[i+1]
        chunk_rows = trading_days[i] + trading_days[i + 1]
        chunks.append(chunk_rows)
    
    # Process and write chunks
    chunk_number = 0
    for chunk_rows in chunks:
        chunk_number += 1
        output_path = write_chunk(output_dir, chunk_number, header, chunk_rows, use_date_filename)
        rows_written = len(chunk_rows)
        trading_days_in_chunk = len([1 for r in chunk_rows if is_trading_day_start(r)])
        if trading_days_in_chunk == 0 and chunk_rows:
            trading_days_in_chunk = 1
        print(f"Created: {output_path} ({rows_written} rows, {trading_days_in_chunk} trading day(s))")
    
    # Count complete and incomplete chunks
    # A complete chunk has at least 2 trading days (156 rows = 2 * 78)
    complete_chunks = len([c for c in chunks if len(c) >= 2 * ROWS_PER_DAY])
    incomplete_chunks = len(chunks) - complete_chunks
    
    return len(chunks), complete_chunks, incomplete_chunks


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
    
    print(f"Splitting CSV file: {args.input}")
    print(f"Output directory: {args.output}")
    print("-" * 50)
    
    try:
        total_chunks, complete_chunks, incomplete_chunks = split_csv(
            args.input,
            args.output
        )
        
        print("-" * 50)
        print(f"Summary:")
        print(f"  Total output files: {total_chunks}")
        print(f"  Complete (2-day) files: {complete_chunks}")
        
        if incomplete_chunks > 0:
            print(f"  Incomplete files: {incomplete_chunks}")
            print(f"  Note: Some files have less than 2 trading days of data")
        
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
