"""Test switching to Yahoo Finance GC=F as primary gold source."""
import urllib.request, json
from datetime import datetime, timezone

# Yahoo Finance chart endpoint — works without API key
def fetch_yahoo(symbol, interval="30m", range="10d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range}"
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def calc_rsi(closes, period=30):
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        d = closes[i] - closes[i-1]
        gains.append(max(0, d))
        losses.append(max(0, -d))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rsi = 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i-1]
        g = max(0, d)
        l = max(0, -d)
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        if avg_loss == 0:
            rsi = 100.0
        else:
            rsi = 100 - 100 / (1 + avg_gain / avg_loss)
    return rsi

# Test GC=F with different ranges
for rng in ["1d", "5d", "10d", "1mo", "3mo"]:
    print(f"\n=== GC=F interval=30m range={rng} ===")
    try:
        d = fetch_yahoo("GC=F", "30m", rng)
        result = d['chart']['result'][0]
        ts = result['timestamp']
        quotes = result['indicators']['quote'][0]
        ohlc = []
        for i in range(len(ts)):
            if quotes['open'][i] is not None:
                ohlc.append({
                    'time': datetime.fromtimestamp(ts[i], tz=timezone.utc),
                    'open': quotes['open'][i],
                    'high': quotes['high'][i],
                    'low': quotes['low'][i],
                    'close': quotes['close'][i],
                    'volume': quotes['volume'][i] or 0,
                })
        print(f"  Got {len(ohlc)} candles")
        if len(ohlc) > 0:
            print(f"  First: {ohlc[0]['time'].strftime('%Y-%m-%d %a %H:%M UTC')}  close=${ohlc[0]['close']:.2f}")
            print(f"  Last:  {ohlc[-1]['time'].strftime('%Y-%m-%d %a %H:%M UTC')}  close=${ohlc[-1]['close']:.2f}")
            closes = [c['close'] for c in ohlc]
            rsi = calc_rsi(closes, 30)
            if rsi:
                print(f"  RSI(30) on M30: {rsi:.2f}")
            # Show last 5 candles
            print("  Last 5 candles:")
            for c in ohlc[-5:]:
                print(f"    {c['time'].strftime('%a %H:%M UTC')}  O={c['open']:.2f}  H={c['high']:.2f}  L={c['low']:.2f}  C={c['close']:.2f}")
    except urllib.error.HTTPError as e:
        print(f"  HTTP ERROR: {e.code}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n=== For comparison: User's broker shows XAUUSD = $3880.15, RSI(30) M30 = 54.75 ===")
