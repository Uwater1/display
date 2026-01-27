#!/usr/bin/env python3
"""
Generate charts.json from SVG files in data/chart/ directory.

Scans for .svg files, extracts date and percentage change from filenames,
and outputs a JSON file for the GitHub Pages frontend.
"""

import json
import os
import re
from pathlib import Path


def extract_chart_info(filename: str) -> dict | None:
    """
    Extract chart information from filename.

    Expected format: YYYY-MM-DD;DayName:+X,XX%.svg
    Example: 2024-02-13;Tue:+0,29%.svg

    Returns:
        dict with 'filename', 'date', 'weekday', and 'change' keys, or None if parsing fails.
    """
    # Remove .svg extension
    name_without_ext = filename.rsplit('.svg', 1)[0]

    # Pattern to match: YYYY-MM-DD;DayName:+X,XX%
    pattern = r'^(\d{4}-\d{2}-\d{2});([A-Za-z]{3}):([+-]?\d+,\d{2}%)$'
    match = re.match(pattern, name_without_ext)

    if not match:
        # Try alternative pattern without day name
        pattern_alt = r'^(\d{4}-\d{2}-\d{2}):([+-]?\d+,\d{2}%)$'
        match = re.match(pattern_alt, name_without_ext)
        if match:
            return {
                'filename': filename,
                'date': match.group(1),
                'weekday': None,
                'change': match.group(2)
            }
        return None

    return {
        'filename': filename,
        'date': match.group(1),
        'weekday': match.group(2),
        'change': match.group(3)
    }


def generate_charts_index(
    chart_dir: str = 'data/chart/',
    output_file: str = 'public/charts.json'
) -> list[dict]:
    """
    Generate charts.json index file.
    
    Args:
        chart_dir: Directory containing SVG chart files.
        output_file: Path for the output JSON file.
    
    Returns:
        List of chart info dictionaries.
    """
    chart_path = Path(chart_dir)
    
    if not chart_path.exists():
        print(f"Warning: Chart directory '{chart_dir}' does not exist.")
        return []
    
    if not chart_path.is_dir():
        print(f"Warning: '{chart_dir}' is not a directory.")
        return []
    
    # Find all .svg files
    svg_files = sorted(chart_path.glob('*.svg'))
    
    if not svg_files:
        print(f"No SVG files found in '{chart_dir}'.")
        return []
    
    # Extract chart info from filenames
    charts = []
    for svg_file in svg_files:
        filename = svg_file.name
        chart_info = extract_chart_info(filename)
        
        if chart_info:
            charts.append(chart_info)
        else:
            print(f"Warning: Could not parse filename '{filename}'")
    
    # Sort by date
    charts.sort(key=lambda x: x['date'])
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(charts, f, indent=2, ensure_ascii=False)
    
    print(f"Generated '{output_file}' with {len(charts)} charts.")
    
    return charts


def main():
    """Main entry point."""
    chart_dir = os.environ.get('CHART_DIR', 'data/chart/')
    output_file = os.environ.get('OUTPUT_FILE', 'public/charts.json')
    
    charts = generate_charts_index(chart_dir, output_file)
    
    if charts:
        print(f"First chart: {charts[0]['date']} ({charts[0]['change']})")
        print(f"Last chart: {charts[-1]['date']} ({charts[-1]['change']})")


if __name__ == '__main__':
    main()
