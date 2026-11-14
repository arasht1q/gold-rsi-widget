"""Compare PAXG vs XAUUSD data sources to diagnose the discrepancy."""
import urllib.request, json, time
from datetime import datetime, timezone

print(f"Current UTC: {datetime.now(timezone.utc)}")
print(f"Current Tehran: {datetime.utcnow()} + 3:30")

# 1. Current PAXG price (Binance)
print("\n=== Source 1: Binance PAXG/USDT (current widget source) ===")
try:
    req = urllib.request.Request("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT",
                                  headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        print(f"  PAXG/USDT price: ${float(d['price']):.2f}")
except Exception as e:
    print(f"  ERROR: {e}")

# 2. Try Binance PAXG recent klines to see what the trend has been
print("\n=== PAXG recent M30 candles (last 10) ===")
try:
    req = urllib.request.Request(
        "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=30m&limit=10",
        headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        klines = json.loads(r.read())
        for k in klines:
            t = datetime.fromtimestamp(k[0]/1000, tz=timezone.utc)
            print(f"  {t.strftime('%a %H:%M UTC')}  O={float(k[1]):.2f}  H={float(k[2]):.2f}  L={float(k[3]):.2f}  C={float(k[4]):.2f}")
except Exception as e:
    print(f"  ERROR: {e}")

# 3. Try Yahoo Finance for GC=F (Gold futures, COMEX)
print("\n=== Source 2: Yahoo Finance GC=F (gold futures) ===")
try:
    # Use the chart endpoint
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=30m&range=1d"
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        meta = d['chart']['result'][0]['meta']
        print(f"  GC=F regularMarketPrice: ${meta.get('regularMarketPrice')}")
        print(f"  GC=F previousClose: ${meta.get('chartPreviousClose')}")
        print(f"  GC=F symbol: {meta.get('symbol')}")
        print(f"  Current trading period: {meta.get('currentTradingPeriod', 'n/a')}")
        # Try to get last few candles
        ts = d['chart']['result'][0]['timestamp']
        closes = d['chart']['result'][0]['indicators']['quote'][0]['close']
        valid = [(datetime.fromtimestamp(t, tz=timezone.utc), c) for t, c in zip(ts, closes) if c is not None]
        print(f"  Got {len(valid)} candles")
        if valid:
            print(f"  Last candle: {valid[-1][0].strftime('%a %H:%M UTC')}  close=${valid[-1][1]:.2f}")
            print(f"  First candle: {valid[0][0].strftime('%a %H:%M UTC')}  close=${valid[0][1]:.2f}")
except urllib.error.HTTPError as e:
    print(f"  HTTP ERROR: {e.code} {e.reason}")
except Exception as e:
    print(f"  ERROR: {e}")

# 4. Try TwelveData with demo API key (limited but no registration)
print("\n=== Source 3: TwelveData XAU/USD (demo apikey) ===")
try:
    url = "https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=30min&outputsize=10&apikey=demo"
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        if d.get('status') == 'ok':
            print(f"  XAU/USD last price: ${float(d['values'][0]['close']):.2f}")
            for v in d['values'][:5]:
                print(f"    {v['datetime']}  close=${float(v['close']):.2f}")
        else:
            print(f"  Response: {d}")
except Exception as e:
    print(f"  ERROR: {e}")

# 5. Try Alpha Vantage with demo key
print("\n=== Source 4: Alpha Vantage (demo) ===")
try:
    url = "https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=XAU&to_symbol=USD&interval=30min&apikey=demo"
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        if 'Time Series FX (30min)' in d:
            ts = d['Time Series FX (30min)']
            keys = list(ts.keys())[:5]
            for k in keys:
                print(f"    {k}  close={ts[k]['4. close']}")
        else:
            print(f"  Response keys: {list(d.keys())[:5]}")
            if 'Information' in d:
                print(f"  Info: {d['Information'][:200]}")
            if 'Error' in d:
                print(f"  Error: {d['Error']}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== Summary ===")
print("User's broker (Aron Group, XAUUSD): $3880.15, RSI(30) M30 = 54.75")
