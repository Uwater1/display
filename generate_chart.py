#!/usr/bin/env python3
"""
Generate a 5-minute bar (candlestick) chart from CSV data and save as SVG.
Optimized for minimal file size using direct SVG generation.
"""

import argparse
import pandas as pd
import pandas_ta as ta


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average using pandas-ta"""
    return ta.ema(prices, length=period)


def generate_candlestick_chart(csv_path: str, output_path: str = None):
    """
    Generate a candlestick chart from OHLCV data and save as SVG.
    Removes gaps between trading sessions (only shows active trading periods).
    
    Args:
        csv_path: Path to the CSV file with OHLCV data
        output_path: Optional output path. If None, uses last candle date and percentage change.
    
    Returns:
        tuple: (path to the saved SVG file, percentage_change)
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Parse the datetime column
    df['time'] = pd.to_datetime(df['time'], utc=True)
    
    # Calculate percentage change for the last trading day
    df['date'] = df['time'].dt.date
    last_date = df['date'].iloc[-1]
    last_day_data = df[df['date'] == last_date]
    first_open = last_day_data['open'].iloc[0]
    last_close = last_day_data['close'].iloc[-1]
    pct_change = ((last_close - first_open) / first_open) * 100
    
    # Format percentage with sign
    pct_str = f"{pct_change:+.2f}%".replace('.', ',').replace('+-', '-')
    
    # Determine output path from last candle date and percentage change if not provided
    if output_path is None:
        last_date_str = last_date.strftime('%Y-%m-%d')
        weekday = last_date.strftime('%a')
        output_path = f"{last_date_str};{weekday}:{pct_str}.svg"
    
    # Print percentage info
    direction = "↑" if pct_change >= 0 else "↓"
    print(f"Last trading day: {last_date} | Change: {direction} {pct_change:+.2f}%")
    
    # Calculate dimensions
    n_bars = len(df)
    bar_width = 10  # Wider candles
    bar_spacing = 12  # More spacing for longer appearance
    chart_width = n_bars * bar_spacing + 120
    price_height = 800
    volume_height = 150
    margin = 50
    total_height = price_height + volume_height + margin * 2
    
    # Calculate price range
    price_min = int(df['low'].min()) + 1
    price_max = int(df['high'].max()) + 1
    price_range = price_max - price_min
    
    # Calculate volume range
    volume_max = df['Volume'].max()
    
    def price_to_y(price):
        return margin + price_height - ((price - price_min) / price_range) * price_height
    
    def volume_to_y(volume):
        return margin + price_height + 10 + volume_height - (volume / volume_max) * volume_height
    
    # Generate SVG
    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}" height="{total_height}">')
    svg_parts.append(f'<rect width="100%" height="100%" fill="white"/>')
    
    # Price grid lines (integers only)
    for i in range(price_range + 1):
        price = price_min + i
        y = price_to_y(price)
        #svg_parts.append(f'<line x1="{margin}" y1="{y}" x2="{chart_width-margin}" y2="{y}" stroke="#e0e0e0" stroke-width="0.5"/>')
        svg_parts.append(f'<text x="{margin-8}" y="{y+4}" text-anchor="end" font-size="20" fill="black">{price}</text>')
    
    # Candlesticks (longer/wider)
    for idx, row in df.iterrows():
        x = margin + 30 + idx * bar_spacing
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        
        # Wick (high to low)
        y_high = price_to_y(row['high'])
        y_low = price_to_y(row['low'])
        svg_parts.append(f'<line x1="{x}" y1="{y_high}" x2="{x}" y2="{y_low}" stroke="{color}" stroke-width="2"/>')
        
        # Body (open to close) - wider
        y_open = price_to_y(row['open'])
        y_close = price_to_y(row['close'])
        body_top = min(y_open, y_close)
        body_height = abs(y_open - y_close)
        if body_height < 2:
            body_height = 2
        svg_parts.append(f'<rect x="{x-4}" y="{body_top}" width="8" height="{body_height}" fill="{color}"/>')
    
    # Volume bars
    for idx, row in df.iterrows():
        x = margin + 30 + idx * bar_spacing
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        
        y_vol_top = volume_to_y(row['Volume'])
        y_vol_bottom = margin + price_height + 20 + volume_height
        vol_height = y_vol_bottom - y_vol_top
        svg_parts.append(f'<rect x="{x-5}" y="{y_vol_top}" width="10" height="{vol_height}" fill="{color}" opacity="0.9"/>')
    
    # Gap markers between days (brighter red/green with opacity 0.50)
    # Wider gap indicator spanning both yesterday's last bar and today's first bar
    df['date'] = df['time'].dt.date
    for idx in range(1, n_bars):
        prev_row = df.iloc[idx - 1]
        curr_row = df.iloc[idx]
        # Check if this is a new day
        if prev_row['date'] != curr_row['date']:
            x_prev = margin + 30 + (idx - 1) * bar_spacing
            x_curr = margin + 30 + idx * bar_spacing
            gap_color = '#00ff00' if curr_row['open'] > prev_row['close'] else '#ff2400'
            y_prev_close = price_to_y(prev_row['close'])
            y_curr_open = price_to_y(curr_row['open'])
            y_top = min(y_prev_close, y_curr_open)
            y_bottom = max(y_prev_close, y_curr_open)
            gap_height = y_bottom - y_top
            # Draw wider rectangle spanning both bars
            svg_parts.append(f'<rect x="{x_prev}" y="{y_top}" width="{bar_spacing}" height="{gap_height}" fill="{gap_color}" opacity="0.60"/>')
    
    # EMA20 line (blue, starting from 21st bar)
    df['ema20'] = ta.ema(df['close'], length=20)
    ema_points = []
    for idx in range(20, n_bars):  # Start from 21st bar (index 20)
        ema_value = df['ema20'].iloc[idx]
        if pd.notna(ema_value):  # Skip NaN values
            x = margin + 30 + idx * bar_spacing
            y_ema = price_to_y(ema_value)
            ema_points.append(f'{x},{y_ema}')
    if ema_points:
        ema_polyline = ','.join(ema_points)
        svg_parts.append(f'<polyline points="{ema_polyline}" fill="none" stroke="#0090ff" stroke-width="2"/>')
    
    # 30-minute interval vertical dotted lines (9:30, 10:00, 10:30, etc.)
    for idx in range(n_bars):
        bar_time = df['time'].iloc[idx]
        minutes = bar_time.minute
        hour = bar_time.hour
        if minutes % 30 == 0:  # 00 or 30 minutes
            x = margin + 30 + idx * bar_spacing
            svg_parts.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{margin * 2 + price_height}" stroke="#666666" stroke-width="0.5" stroke-dasharray="4,4" opacity="0.90"/>')
        if hour == 15 and minutes == 55:  
            x = margin + 30 + idx * bar_spacing
            svg_parts.append(f'<line x1="{x+6}" y1="{30}" x2="{x+6}" y2="{margin * 3 + price_height}" stroke="black" stroke-width="0.7"/>')
    
    # X-axis labels (fewer for smaller file size)
    for idx in range(0, n_bars, 6):
        x = margin + 30 + idx * bar_spacing
        time_str = df['time'].iloc[idx].strftime('%H:%M')
        svg_parts.append(f'<text x="{x}" y="{total_height-10}" text-anchor="middle" font-size="20" fill="black">{time_str}</text>')
    
    # Display percentage change of last trading day on chart
    pct_color = '#26a69a' if pct_change >= 0 else '#ef5350'
    pct_symbol = "▲" if pct_change >= 0 else "▼"
    weekday = last_date.strftime('%a')
    svg_parts.append(f'<text x="{chart_width-margin}" y="{margin}" text-anchor="end" font-size="40" fill="{pct_color}" font-weight="bold">{pct_symbol} {pct_change:+.2f}% ({weekday})</text>')
    
    svg_parts.append('</svg>')
    
    # Write SVG file
    with open(output_path, 'w') as f:
        f.write(''.join(svg_parts))
    
    print(f"Chart saved to: {output_path}")
    return output_path, pct_change


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a candlestick chart from CSV trading data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python generate_chart.py
    python generate_chart.py example.csv
    python generate_chart.py data.csv --output chart.svg
        """
    )
    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        default="qqq5m.csv",
        help="Input CSV file path (default: qqq5m.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output SVG file path (default: derived from last candle date and percentage change)"
    )
    args = parser.parse_args()
    
    # Generate the chart - output name derived from last candle date and percentage change
    result = generate_candlestick_chart(csv_path=args.input, output_path=args.output)
