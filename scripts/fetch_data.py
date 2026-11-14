"""Fetch XAUUSD M30 data for past 2 years from multiple sources."""
import sys
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

DATA_DIR = "/home/z/my-project/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Target: 2 years back from today (2026-11-14)
END = datetime(2026, 11, 14)
START = END - timedelta(days=730)

print(f"Target window: {START.date()} → {END.date()}  ({(END-START).days} days)")

# -------------------------------------------------------------------
# Approach 1: yfinance — try multiple tickers at 30m interval
# -------------------------------------------------------------------
def try_yf_30m(ticker):
    print(f"\n--- yfinance 30m: {ticker} ---")
    try:
        df = yf.download(ticker, start=START, end=END, interval="30m",
                         progress=False, auto_adjust=False)
        if df is None or len(df) == 0:
            print("  → empty")
            return None
        df = df.reset_index()
        # flatten multi-index columns if any
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join([str(c) for c in col if c]).strip('_') for col in df.columns.values]
        print(f"  rows: {len(df)}  range: {df.iloc[0,0]}  →  {df.iloc[-1,0]}")
        print(f"  cols: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# yfinance caps 30m at 60 days. Try anyway.
df_gc = try_yf_30m("GC=F")        # Gold futures
df_xau = try_yf_30m("XAUUSD=X")   # Spot gold

# -------------------------------------------------------------------
# Approach 2: yfinance — 60m interval (730-day cap)
# -------------------------------------------------------------------
def try_yf_60m(ticker):
    print(f"\n--- yfinance 60m: {ticker} ---")
    try:
        df = yf.download(ticker, start=START, end=END, interval="60m",
                         progress=False, auto_adjust=False)
        if df is None or len(df) == 0:
            print("  → empty")
            return None
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join([str(c) for c in col if c]).strip('_') for col in df.columns.values]
        print(f"  rows: {len(df)}  range: {df.iloc[0,0]}  →  {df.iloc[-1,0]}")
        return df
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

df_60m = try_yf_60m("GC=F")

# Save whatever we got for inspection
if df_xau is not None and len(df_xau) > 1000:
    df_xau.to_csv(f"{DATA_DIR}/xauusd_30m_yf.csv", index=False)
    print(f"\n✓ Saved 30m XAUUSD: {len(df_xau)} rows")
elif df_gc is not None and len(df_gc) > 1000:
    df_gc.to_csv(f"{DATA_DIR}/gcf_30m_yf.csv", index=False)
    print(f"\n✓ Saved 30m GC=F: {len(df_gc)} rows")
else:
    print("\n✗ yfinance 30m has too few rows for 2-year backtest")

if df_60m is not None:
    df_60m.to_csv(f"{DATA_DIR}/gcf_60m_yf.csv", index=False)
    print(f"✓ Saved 60m GC=F: {len(df_60m)} rows  (fallback only)")

print("\nDone.")
