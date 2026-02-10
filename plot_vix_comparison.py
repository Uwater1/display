#!/usr/bin/env python3
"""
VIX / Implied Volatility vs Historical Volatility Comparison Charts

Generates 3 PNG figures:
  1. VIX  vs  S&P 500 (^GSPC) 20-day Historical Volatility
  2. VXN  vs  Nasdaq-100 (^NDX) 20-day Historical Volatility
  3. VXST (^VIX9D)  vs  S&P 500 (^GSPC) 9-day Historical Volatility

Historical volatility = annualised rolling std-dev of log returns.

Usage:
    python plot_vix_comparison.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "chart")


# ── helpers ─────────────────────────────────────────────────────────────────

def load_csv(filename: str) -> pd.Series:
    """Load a yfinance-style CSV and return the Close price series."""
    path = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    # The multi-level header has ('Close', ticker) – just grab Close
    close = df.iloc[:, 0]  # First column is Close
    close = pd.to_numeric(close, errors="coerce")
    close.name = "Close"
    return close.dropna()


def historical_vol(close: pd.Series, window: int = 20) -> pd.Series:
    """
    Compute annualised historical volatility (%).
    HV = std(log returns) over `window` trading days × sqrt(252) × 100
    """
    log_ret = np.log(close / close.shift(1))
    hv = log_ret.rolling(window=window).std() * np.sqrt(252) * 100
    hv.name = f"HV{window}"
    return hv


# ── plotting ────────────────────────────────────────────────────────────────

def plot_comparison(
    iv_series: pd.Series,
    hv_series: pd.Series,
    iv_label: str,
    hv_label: str,
    title: str,
    start_date: str,
    filename: str,
):
    """Create a dual-axis chart comparing implied vol index vs historical vol."""

    # Align date ranges
    iv = iv_series.loc[start_date:]
    hv = hv_series.loc[start_date:]

    # Inner-join on dates
    combined = pd.DataFrame({"IV": iv, "HV": hv}).dropna()

    fig, ax1 = plt.subplots(figsize=(16, 6))

    # Style
    fig.patch.set_facecolor("#0e1117")
    ax1.set_facecolor("#0e1117")

    # Implied vol (left axis)
    color_iv = "#ff6b6b"
    ax1.plot(combined.index, combined["IV"], color=color_iv, linewidth=0.4,
             alpha=0.9, label=iv_label)
    ax1.set_ylabel(iv_label, color=color_iv, fontsize=12)
    ax1.tick_params(axis="y", labelcolor=color_iv)

    # Historical vol (right axis)
    ax2 = ax1.twinx()
    color_hv = "#4ecdc4"
    ax2.plot(combined.index, combined["HV"], color=color_hv, linewidth=0.4,
             alpha=0.9, label=hv_label)
    ax2.set_ylabel(hv_label, color=color_hv, fontsize=12)
    ax2.tick_params(axis="y", labelcolor=color_hv)

    # Spread shading (IV − HV)
    spread = combined["IV"] - combined["HV"]
    ax1.fill_between(
        combined.index,
        combined["IV"],
        combined["HV"],
        where=(spread >= 0),
        color=color_iv, alpha=0.08, interpolate=True,
    )
    ax1.fill_between(
        combined.index,
        combined["IV"],
        combined["HV"],
        where=(spread < 0),
        color=color_hv, alpha=0.08, interpolate=True,
    )

    # Formatting
    ax1.set_title(title, fontsize=15, fontweight="bold", color="white", pad=12)
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.tick_params(axis="x", colors="white")
    ax1.grid(axis="both", color="#333", linewidth=0.3, alpha=0.6)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               facecolor="#1a1a2e", edgecolor="#333", labelcolor="white",
               fontsize=10)

    # Summary stats annotation
    corr = combined["IV"].corr(combined["HV"])
    mean_spread = spread.mean()
    stats_text = (
        f"Correlation: {corr:.3f}\n"
        f"Mean Spread (IV−HV): {mean_spread:+.1f}%\n"
        f"IV Mean: {combined['IV'].mean():.1f}%   HV Mean: {combined['HV'].mean():.1f}%"
    )
    ax1.text(
        0.98, 0.97, stats_text,
        transform=ax1.transAxes, fontsize=9,
        verticalalignment="top", horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1a2e",
                  edgecolor="#555", alpha=0.85),
        color="white", family="monospace",
    )

    fig.tight_layout()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save SVG (vector – perfect at any zoom)
    svg_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '') + '.svg')
    fig.savefig(svg_path, format='svg', facecolor=fig.get_facecolor())
    print(f"✅  Saved → {svg_path}")

    # Save high-DPI PNG as well
    png_path = os.path.join(OUTPUT_DIR, filename.replace('.png', '') + '.png')
    fig.savefig(png_path, dpi=300, facecolor=fig.get_facecolor())
    print(f"✅  Saved → {png_path}")

    plt.close(fig)


# ── main ────────────────────────────────────────────────────────────────────

def main():
    print("Loading data …")

    # Load price / index series
    vix = load_csv("^VIX_1d.csv")
    gspc = load_csv("^GSPC_1d.csv")
    vxn = load_csv("^VXN_1d.csv")
    ndx = load_csv("^NDX_1d.csv")
    vix9d = load_csv("^VIX9D_1d.csv")

    # Compute historical volatilities
    hv_gspc_20 = historical_vol(gspc, window=20)
    hv_ndx_20 = historical_vol(ndx, window=20)
    hv_gspc_9 = historical_vol(gspc, window=9)   # 9-day for VXST comparison

    print("Generating charts …\n")

    # Chart 1: VIX vs S&P 500 HV20
    plot_comparison(
        iv_series=vix,
        hv_series=hv_gspc_20,
        iv_label="VIX (Implied Vol)",
        hv_label="S&P 500 HV20 (Historical Vol)",
        title="VIX  vs  S&P 500 Historical Volatility (20-day)",
        start_date="2003-01-01",
        filename="vix_vs_gspc_hv.png",
    )

    # Chart 2: VXN vs Nasdaq-100 HV20
    plot_comparison(
        iv_series=vxn,
        hv_series=hv_ndx_20,
        iv_label="VXN (Implied Vol)",
        hv_label="Nasdaq-100 HV20 (Historical Vol)",
        title="VXN  vs  Nasdaq-100 Historical Volatility (20-day)",
        start_date="2003-01-01",
        filename="vxn_vs_ndx_hv.png",
    )

    # Chart 3: VXST (VIX9D) vs S&P 500 HV9
    plot_comparison(
        iv_series=vix9d,
        hv_series=hv_gspc_9,
        iv_label="VXST / VIX9D (Implied Vol)",
        hv_label="S&P 500 HV9 (Historical Vol)",
        title="VXST (VIX9D)  vs  S&P 500 Historical Volatility (9-day)",
        start_date="2011-01-01",
        filename="vxst_vs_gspc_hv.png",
    )

    print("\n🎉  All 3 charts generated!")


if __name__ == "__main__":
    main()
