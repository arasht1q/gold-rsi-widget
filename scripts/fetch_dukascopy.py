"""Try multiple sources for XAUUSD M30 data."""
import sys, os, time, struct, lzma
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

DATA_DIR = "/home/z/my-project/data"
os.makedirs(DATA_DIR, exist_ok=True)

END = datetime(2026, 11, 14, tzinfo=timezone.utc)
START = END - timedelta(days=730)
print(f"Target: {START.date()} → {END.date()}  ({(END-START).days} days)")

# ===================================================================
# Source A: Dukascopy tick data → aggregate to M30
# ===================================================================
# URL: https://datafeed.dukascopy.com/datafeed/XAUUSD/{YYYY}/{MM-1}/{DD}/{HH}h_ticks.bi5
# Each .bi5 = LZMA-compressed bytes; each tick = 20 bytes:
#   int32 delta_ms, int32 ask, int32 bid, int32 ask_vol, int32 bid_vol
# Prices are scaled by 1e3 for XAUUSD (3 decimals).
# ===================================================================

def fetch_bi5(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None  # weekend/holiday — no data
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            return None

def parse_bi5(blob, base_ts, price_factor=1000.0):
    """Decompress and parse Dukascopy bi5 tick blob."""
    try:
        raw = lzma.decompress(blob)
    except Exception:
        return []
    n = len(raw) // 20
    ticks = []
    for i in range(n):
        off = i * 20
        try:
            delta_ms, ask_int, bid_int, _av, _bv = struct.unpack(">iiiii", raw[off:off+20])
        except struct.error:
            break
        # Skip zero prices (rarely happens)
        if ask_int <= 0 or bid_int <= 0:
            continue
        ts = base_ts + timedelta(milliseconds=delta_ms)
        ask = ask_int / price_factor
        bid = bid_int / price_factor
        ticks.append((ts, ask, bid))
    return ticks

def dukascopy_fetch(symbol, start, end):
    """Fetch tick data day-by-day, aggregate to M30 OHLC."""
    all_ticks = []
    days = (end - start).days + 1
    cur = start.replace(hour=0, minute=0, second=0, microsecond=0)
    fetched_days = 0
    while cur <= end:
        y, m_zero, d = cur.year, cur.month - 1, cur.day
        day_ticks = []
        for h in range(24):
            url = f"https://datafeed.dukascopy.com/datafeed/{symbol}/{y}/{m_zero:02d}/{d:02d}/{h}h_ticks.bi5"
            blob = fetch_bi5(url)
            if blob is None or len(blob) == 0:
                continue
            base_ts = cur.replace(hour=h, tzinfo=timezone.utc)
            ticks = parse_bi5(blob, base_ts)
            day_ticks.extend(ticks)
        if day_ticks:
            all_ticks.extend(day_ticks)
            fetched_days += 1
        cur += timedelta(days=1)
        if (cur - start).days % 30 == 0:
            print(f"  ... {cur.date()}  ticks={len(all_ticks):,}  days_with_data={fetched_days}")
    return all_ticks

print("\n=== Trying Dukascopy XAUUSD ===")
# Probe one day first to confirm endpoint works
probe_url = "https://datafeed.dukascopy.com/datafeed/XAUUSD/2026/10/13/00h_ticks.bi5"
probe = fetch_bi5(probe_url)
print(f"Probe 2026-10-13 hour 0: {'OK' if probe and len(probe)>0 else 'FAIL'}  bytes={len(probe) if probe else 0}")

if probe:
    print(f"Fetching Dukascopy tick data ({(END-START).days+1} days)...")
    # Limit to last 730 days = 2 years
    ticks = dukascopy_fetch("XAUUSD", START, END)
    print(f"\nTotal ticks: {len(ticks):,}")
    if len(ticks) > 1000:
        df = pd.DataFrame(ticks, columns=['ts','ask','bid'])
        df['mid'] = (df['ask'] + df['bid']) / 2.0
        df['ts'] = pd.to_datetime(df['ts'])
        df = df.set_index('ts').sort_index()
        # Aggregate to 30-minute OHLC on mid price
        ohlc = df['mid'].resample('30min').ohlc().dropna()
        ohlc['volume'] = df['mid'].resample('30min').size().reindex(ohlc.index).fillna(0)
        print(f"30-min candles: {len(ohlc)}")
        print(ohlc.head())
        print("...")
        print(ohlc.tail())
        ohlc.to_csv(f"{DATA_DIR}/xauusd_30m_dukascopy.csv")
        print(f"✓ Saved to {DATA_DIR}/xauusd_30m_dukascopy.csv")
