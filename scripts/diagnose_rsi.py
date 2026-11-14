"""Diagnose RSI difference between our calc and user's broker (54.75)."""
import urllib.request, json
from datetime import datetime, timezone

def fetch_yahoo(symbol, interval, range_):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def calc_rsi_wilder(closes, period):
    """MT4-compatible Wilder RSI"""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        gains.append(max(0, d))
        losses.append(max(0, -d))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rsi = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        g, l = max(0, d), max(0, -d)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        rsi = 100 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return rsi

def calc_rsi_sma(closes, period):
    """Simple RSI using SMA (some platforms use this)"""
    if len(closes) < period + 1:
        return None
    rsis = []
    for i in range(period, len(closes)):
        window = closes[i-period:i+1]
        gains = [max(0, window[j] - window[j-1]) for j in range(1, len(window))]
        losses = [max(0, window[j-1] - window[j]) for j in range(1, len(window))]
        avg_g = sum(gains) / period
        avg_l = sum(losses) / period
        if avg_l == 0:
            rsis.append(100)
        else:
            rsis.append(100 - 100 / (1 + avg_g / avg_l))
    return rsis[-1] if rsis else None

# Fetch GC=F M30 last 10 days
print("=== Fetching GC=F M30 last 10 days ===")
d = fetch_yahoo("GC=F", "30m", "10d")
result = d['chart']['result'][0]
ts = result['timestamp']
quotes = result['indicators']['quote'][0]
candles = []
for i in range(len(ts)):
    if quotes['close'][i] is not None:
        candles.append({
            'time': datetime.fromtimestamp(ts[i], tz=timezone.utc),
            'close': quotes['close'][i],
        })
print(f"Total candles: {len(candles)}")
print(f"Last candle: {candles[-1]['time'].strftime('%Y-%m-%d %a %H:%M UTC')}  close=${candles[-1]['close']:.2f}")
print(f"5 candles ago: {candles[-5]['time'].strftime('%a %H:%M UTC')}  close=${candles[-5]['close']:.2f}")
print(f"30 candles ago: {candles[-30]['time'].strftime('%a %H:%M UTC')}  close=${candles[-30]['close']:.2f}")

closes = [c['close'] for c in candles]

# Test different RSI periods
print("\n=== RSI on M30 with various periods (Wilder) ===")
for p in [14, 21, 30, 50]:
    rsi = calc_rsi_wilder(closes, p)
    print(f"  RSI({p})  Wilder  = {rsi:.2f}" if rsi else f"  RSI({p})  not enough data")

print("\n=== RSI on M30 with various periods (SMA) ===")
for p in [14, 21, 30, 50]:
    rsi = calc_rsi_sma(closes, p)
    print(f"  RSI({p})  SMA    = {rsi:.2f}" if rsi else f"  RSI({p})  not enough data")

# Also try with different number of recent candles (maybe user's broker uses different cutoff)
print("\n=== RSI(30) Wilder with different last-N candles ===")
for n in [40, 60, 100, 200, len(closes)]:
    if n > len(closes):
        continue
    sub = closes[-n:]
    rsi = calc_rsi_wilder(sub, 30)
    print(f"  Last {n} candles, RSI(30) Wilder = {rsi:.2f}")

# Try fetching XAUUSD=X (Yahoo's spot gold ticker)
print("\n=== Try Yahoo XAUUSD=X (spot gold) ===")
try:
    d = fetch_yahoo("XAUUSD=X", "30m", "10d")
    result = d['chart']['result'][0]
    ts = result['timestamp']
    quotes = result['indicators']['quote'][0]
    spot_closes = []
    for i in range(len(ts)):
        if quotes['close'][i] is not None:
            spot_closes.append(quotes['close'][i])
    print(f"  Got {len(spot_closes)} spot candles")
    if spot_closes:
        print(f"  Last spot price: ${spot_closes[-1]:.2f}")
        rsi = calc_rsi_wilder(spot_closes, 30)
        print(f"  RSI(30) Wilder on spot: {rsi:.2f}")
        rsi14 = calc_rsi_wilder(spot_closes, 14)
        print(f"  RSI(14) Wilder on spot: {rsi14:.2f}")
except Exception as e:
    print(f"  ERROR: {e}")

# Try USD/XAU = inverse
print("\n=== Try Yahoo USD/XAU (inverse) ===")
try:
    d = fetch_yahoo("USD=XAU", "30m", "5d")
    result = d['chart']['result'][0]
    print(f"  Got data: {len(result['timestamp'])} candles")
except Exception as e:
    print(f"  ERROR: {e}")
