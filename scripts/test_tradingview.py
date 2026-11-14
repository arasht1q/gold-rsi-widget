"""Test TradingView public APIs for XAUUSD data."""
import urllib.request, urllib.parse, json
from datetime import datetime, timezone, timedelta

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.tradingview.com',
    'Referer': 'https://www.tradingview.com/',
}

# TradingView ticker candidates for gold
TICKERS = [
    'TVC:GOLD',        # TradingView spot gold
    'OANDA:XAUUSD',    # OANDA XAUUSD spot
    'FX_IDC:XAUUSD',   # FXCM
    'TVC:GOLD',        
    'COMEX:GC1!',      # Gold futures continuous
    'TVC:XAUUSD',
]

def fetch(url, headers=HEADERS):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read(), r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.read() if hasattr(e, 'read') else b'', e.code, dict(e.headers) if hasattr(e, 'headers') else {}
    except Exception as e:
        return str(e).encode(), 0, {}

# ===========================================================
# Test 1: Scanner API (current price)
# ===========================================================
print("="*70)
print("TEST 1: TradingView Scanner API (current quote)")
print("="*70)
for ticker in TICKERS:
    url = f"https://scanner.tradingview.com/symbol?symbol={urllib.parse.quote(ticker)}"
    body, status, _ = fetch(url)
    if status == 200:
        try:
            d = json.loads(body)
            if isinstance(d, dict) and d:
                price = d.get('close') or d.get('last_price') or d.get('current_price')
                change = d.get('change')
                print(f"  {ticker:25s} → status=200  price=${price}  change={change}")
            else:
                print(f"  {ticker:25s} → status=200  body={body[:100]}")
        except Exception as e:
            print(f"  {ticker:25s} → status=200  parse_error: {e}  body={body[:100]}")
    else:
        print(f"  {ticker:25s} → status={status}  body={body[:100]}")

# ===========================================================
# Test 2: Quote search API
# ===========================================================
print("\n" + "="*70)
print("TEST 2: Quote search API")
print("="*70)
url = "https://symbol-search.tradingview.com/v2/symbol/search?text=GOLD%20SPOT&hl=true&lang=en&domain=production&currency=USD&exchange=&type="
body, status, _ = fetch(url)
print(f"  status={status}")
if status == 200:
    try:
        d = json.loads(body)
        symbols = d.get('symbols', [])
        print(f"  Found {len(symbols)} symbols:")
        for s in symbols[:10]:
            print(f"    {s.get('symbol', '')}  exchange={s.get('exchange', '')}  ticker={s.get('ticker', '')}  type={s.get('type', '')}")
    except Exception as e:
        print(f"  parse error: {e}")

# ===========================================================
# Test 3: Chart history API (candle data)
# ===========================================================
print("\n" + "="*70)
print("TEST 3: Chart history API (OHLC candles)")
print("="*70)

now = int(datetime.now(timezone.utc).timestamp())
to = now
frm = now - 10 * 86400  # 10 days back

for ticker in TICKERS:
    # TradingView's chart history endpoint
    params = urllib.parse.urlencode({
        'symbol': ticker,
        'from': frm,
        'to': to,
        'resolution': '30',  # 30 minute
        'currency': 'USD',
    })
    url = f"https://chart-api.tradingview.com/symbol_history?{params}"
    body, status, _ = fetch(url)
    if status == 200:
        try:
            d = json.loads(body)
            # Find the result entries
            if 'result' in d:
                results = d['result']
                if isinstance(results, list) and results:
                    first = results[0]
                    if isinstance(first, dict):
                        ts_data = first.get('s') or first.get('t')
                        c_data = first.get('c')
                        h_data = first.get('h')
                        l_data = first.get('l')
                        o_data = first.get('o')
                        if c_data and len(c_data) > 0:
                            print(f"  {ticker:25s} → status=200  candles={len(c_data)}  last_close=${c_data[-1]:.2f}")
                            # Show last 3 candles
                            for i in range(-min(3, len(c_data)), 0):
                                t = datetime.fromtimestamp(first['t'][i] if 't' in first else 0, tz=timezone.utc)
                                print(f"    {t.strftime('%a %H:%M UTC')}  O={o_data[i]:.2f}  H={h_data[i]:.2f}  L={l_data[i]:.2f}  C={c_data[i]:.2f}")
                        else:
                            print(f"  {ticker:25s} → status=200  no OHLC data  keys={list(first.keys())[:8]}")
                    else:
                        print(f"  {ticker:25s} → status=200  result is not dict  type={type(first).__name__}  value={str(first)[:80]}")
                else:
                    print(f"  {ticker:25s} → status=200  result is empty or not list")
            else:
                print(f"  {ticker:25s} → status=200  keys={list(d.keys())[:8]}")
        except Exception as e:
            print(f"  {ticker:25s} → status=200  parse error: {e}  body={body[:200]}")
    else:
        print(f"  {ticker:25s} → status={status}  body={body[:200]}")

# ===========================================================
# Test 4: History API v1 (older format)
# ===========================================================
print("\n" + "="*70)
print("TEST 4: tvdb history API")
print("="*70)
url = f"https://history.tradingview.com/tv/history?symbol=TVC:GOLD&resolution=30&from={frm}&to={to}"
body, status, _ = fetch(url)
print(f"  status={status}  body={body[:300]}")

# ===========================================================
# Test 5: chart-api with different format
# ===========================================================
print("\n" + "="*70)
print("TEST 5: chart-api with different params")
print("="*70)
url = "https://chart-api.tradingview.com/symbol_history?symbol=TVC:GOLD&resolution=30&currency=USD&from=" + str(frm) + "&to=" + str(to)
body, status, _ = fetch(url)
print(f"  status={status}")
if status == 200:
    print(f"  body[:500]: {body[:500]}")
