"""Fetch Dukascopy XAUUSD tick data, parallel, then aggregate to M30."""
import sys, os, time, struct, lzma
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

DATA_DIR = "/home/z/my-project/data"
os.makedirs(DATA_DIR, exist_ok=True)

END = datetime(2026, 11, 14, tzinfo=timezone.utc)
START = END - timedelta(days=730)
print(f"Target: {START.date()} → {END.date()}  ({(END-START).days+1} days)")

def fetch_bi5(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(0.5)
                continue
            return None

def parse_bi5(blob, base_ts, price_factor=1000.0):
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
        if ask_int <= 0 or bid_int <= 0:
            continue
        ts = base_ts + timedelta(milliseconds=delta_ms)
        ask = ask_int / price_factor
        bid = bid_int / price_factor
        ticks.append((ts, ask, bid))
    return ticks

def fetch_one_hour(symbol, cur, h):
    y, m_zero, d = cur.year, cur.month - 1, cur.day
    url = f"https://datafeed.dukascopy.com/datafeed/{symbol}/{y}/{m_zero:02d}/{d:02d}/{h}h_ticks.bi5"
    blob = fetch_bi5(url)
    if not blob:
        return []
    base_ts = cur.replace(hour=h, tzinfo=timezone.utc)
    return parse_bi5(blob, base_ts)

# Build all (day, hour) tasks
tasks = []
cur = START.replace(hour=0, minute=0, second=0, microsecond=0)
while cur <= END:
    for h in range(24):
        tasks.append((cur, h))
    cur += timedelta(days=1)
print(f"Total fetch tasks: {len(tasks)}")

# Fetch with thread pool
all_ticks = []
done = 0
with ThreadPoolExecutor(max_workers=32) as ex:
    futures = {ex.submit(fetch_one_hour, "XAUUSD", t[0], t[1]): t for t in tasks}
    for fut in as_completed(futures):
        done += 1
        try:
            ticks = fut.result()
            if ticks:
                all_ticks.extend(ticks)
        except Exception as e:
            pass
        if done % 500 == 0:
            print(f"  progress: {done}/{len(tasks)}  ticks so far: {len(all_ticks):,}")

print(f"\nTotal ticks: {len(all_ticks):,}")
if len(all_ticks) < 10000:
    print("✗ Too few ticks — aborting")
    sys.exit(1)

# Aggregate to M30
df = pd.DataFrame(all_ticks, columns=['ts','ask','bid'])
df['mid'] = (df['ask'] + df['bid']) / 2.0
df['ts'] = pd.to_datetime(df['ts'], utc=True)
df = df.set_index('ts').sort_index()

ohlc = df['mid'].resample('30min').ohlc().dropna()
ohlc.columns = ['open','high','low','close']
ohlc['volume'] = df['mid'].resample('30min').size().reindex(ohlc.index).fillna(0).astype('int64')

print(f"\n30-min candles: {len(ohlc)}")
print(f"Date range: {ohlc.index.min()} → {ohlc.index.max()}")
print(f"Price range: {ohlc['low'].min():.2f} → {ohlc['high'].max():.2f}")
print(ohlc.head(3))
print("...")
print(ohlc.tail(3))

out = f"{DATA_DIR}/xauusd_30m_dukascopy.csv"
ohlc.to_csv(out)
print(f"\n✓ Saved: {out}  ({len(ohlc)} rows)")
