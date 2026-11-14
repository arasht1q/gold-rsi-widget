"""Fetch PAXG/USDT M30 from Binance — proxy for spot gold (1 PAXG = 1 oz LBMA gold)."""
import sys, os, json, time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
import pandas as pd

DATA_DIR = "/home/z/my-project/data"
os.makedirs(DATA_DIR, exist_ok=True)

END = int(datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp() * 1000)
START = END - 730 * 24 * 3600 * 1000
print(f"Window ms: {START} → {END}  (2 years)")

def fetch_klines(symbol, interval, start_ms, end_ms, limit=1000):
    url = (f"https://api.binance.com/api/v3/klines"
           f"?symbol={symbol}&interval={interval}"
           f"&startTime={start_ms}&endTime={end_ms}&limit={limit}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# Probe
print("\n=== Probe Binance PAXGUSDT ===")
try:
    probe = fetch_klines("PAXGUSDT", "30m", END - 4*3600*1000, END, limit=10)
    print(f"PAXGUSDT probe: {len(probe)} candles, sample price={probe[0][4]}")
    has_paxg = len(probe) > 0
except Exception as e:
    print(f"PAXGUSDT probe failed: {e}")
    has_paxg = False

if not has_paxg:
    print("✗ No PAXG data")
    sys.exit(1)

# Paginate
all_rows = []
cur = START
total = (END - START) // (1000 * 30 * 60 * 1000) + 1
i = 0
while cur < END:
    try:
        rows = fetch_klines("PAXGUSDT", "30m", cur, END, limit=1000)
    except Exception as e:
        print(f"  ERROR at {cur}: {e}  — retry in 2s")
        time.sleep(2)
        continue
    if not rows:
        break
    all_rows.extend(rows)
    # Move past the last candle's open time
    last_open = rows[-1][0]
    cur = last_open + 30*60*1000  # +30 min
    i += 1
    if i % 5 == 0:
        print(f"  fetched {len(all_rows):,} candles  (batch {i}, ~{total} total)")

print(f"\nTotal candles fetched: {len(all_rows):,}")

# Build DataFrame
df = pd.DataFrame(all_rows, columns=[
    'open_time','open','high','low','close','volume',
    'close_time','quote_vol','trades','taker_buy_base','taker_buy_quote','ignore'
])
df['open_time'] = pd.to_datetime(df['open_time'], unit='ms', utc=True)
for c in ['open','high','low','close','volume']:
    df[c] = pd.to_numeric(df[c])
df = df[['open_time','open','high','low','close','volume','trades']].set_index('open_time')
df = df[~df.index.duplicated(keep='last')].sort_index()

# Restrict to our window
df = df[(df.index >= pd.Timestamp(START, unit='ms', tz='UTC')) &
        (df.index <= pd.Timestamp(END, unit='ms', tz='UTC'))]

print(f"Final M30 candles: {len(df):,}")
print(f"Range: {df.index.min()} → {df.index.max()}")
print(f"Price: low={df['low'].min():.2f}  high={df['high'].max():.2f}  last={df['close'].iloc[-1]:.2f}")

out = f"{DATA_DIR}/xauusd_30m_binance_paxg.csv"
df.to_csv(out)
print(f"\n✓ Saved: {out}")
