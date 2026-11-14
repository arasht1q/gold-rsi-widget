"""Try TradingView scanner with proper fields parameter and alternative endpoints."""
import urllib.request, urllib.parse, json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.tradingview.com',
    'Referer': 'https://www.tradingview.com/',
}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read(), r.status
    except urllib.error.HTTPError as e:
        return e.read() if hasattr(e, 'read') else b'', e.code
    except Exception as e:
        return str(e).encode(), 0

TICKERS = ['TVC:GOLD', 'OANDA:XAUUSD', 'FX_IDC:XAUUSD', 'COMEX:GC1!', 'TVC:XAUUSD']

# ===========================================================
# Test 1: Scanner with proper fields
# ===========================================================
print("="*70)
print("TEST 1: scanner.tradingview.com/symbol with fields")
print("="*70)
fields = "name,close,change,change_abs,current_price,last_price,Recommendations,description,high,low,open"
for ticker in TICKERS:
    url = f"https://scanner.tradingview.com/symbol?symbol={urllib.parse.quote(ticker)}&fields={fields}"
    body, status = fetch(url)
    print(f"  {ticker:25s} → status={status}  body={body[:300]}")

# ===========================================================
# Test 2: Scanner scan endpoint (multiple symbols at once)
# ===========================================================
print("\n" + "="*70)
print("TEST 2: scanner scan endpoint with multiple tickers")
print("="*70)
# Format: POST with JSON body, or GET with query params
import urllib.request as ur
data = json.dumps({
    "symbols": {
        "tickers": ["TVC:GOLD", "OANDA:XAUUSD"],
        "query": {"types": []}
    },
    "fields": ["name", "close", "change", "change_abs", "Recommendations", "description", "high", "low", "open"]
}).encode()

req = ur.Request(
    "https://scanner.tradingview.com/scan",
    data=data,
    headers={**HEADERS, 'Content-Type': 'application/json'},
    method='POST'
)
try:
    with ur.urlopen(req, timeout=15) as r:
        body = r.read()
        print(f"  POST /scan status=200  body={body[:500]}")
except urllib.error.HTTPError as e:
    print(f"  POST /scan status={e.code}  body={e.read()[:300] if hasattr(e, 'read') else b''}")
except Exception as e:
    print(f"  POST /scan error: {e}")

# ===========================================================
# Test 3: Try direct chart-api hosts
# ===========================================================
print("\n" + "="*70)
print("TEST 3: Try different chart-api hosts")
print("="*70)
hosts_to_try = [
    "chart-api.tradingview.com",
    "charts.tradingview.com",
    "api.tradingview.com",
    "www.tradingview.com",
]
for host in hosts_to_try:
    url = f"https://{host}/symbol_history?symbol=TVC:GOLD&resolution=30&from=1700000000&to=1700100000"
    body, status = fetch(url)
    print(f"  {host:30s} → status={status}  body={body[:200]}")

# ===========================================================
# Test 4: Try tradingview-chart embed API
# ===========================================================
print("\n" + "="*70)
print("TEST 4: TV embed/quote widget endpoints")
print("="*70)
urls_to_try = [
    "https://www.tradingview.com/quote/TVC:GOLD/",
    "https://www.tradingview.com/symbols/XAUUSD/",
    "https://scanner.tradingview.com/tv/symbol?symbol=TVC:GOLD&fields=name,close",
    "https://scanner.tradingview.com/symbol?symbol=TVC%3AGOLD&fields=close,change,change_abs,name",
]
for url in urls_to_try:
    body, status = fetch(url)
    print(f"  status={status}  url={url}")
    print(f"    body[:200]: {body[:200]}")

# ===========================================================
# Test 5: Different scanner field lists
# ===========================================================
print("\n" + "="*70)
print("TEST 5: scanner with minimal fields")
print("="*70)
for ticker in ['TVC:GOLD']:
    for f in ['close', 'name,close', 'close,change', 'close|change', 'name|close|change']:
        url = f"https://scanner.tradingview.com/symbol?symbol={urllib.parse.quote(ticker)}&fields={urllib.parse.quote(f)}"
        body, status = fetch(url)
        print(f"  fields='{f}'  status={status}  body={body[:200]}")
