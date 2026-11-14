"""Try TradingView chart history and other endpoints, also test stooq."""
import urllib.request, urllib.parse, json
from datetime import datetime, timezone

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Origin': 'https://www.tradingview.com',
    'Referer': 'https://www.tradingview.com/',
}

def fetch(url, headers=HEADERS):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read(), r.status
    except urllib.error.HTTPError as e:
        return e.read() if hasattr(e, 'read') else b'', e.code
    except Exception as e:
        return str(e).encode(), 0

# ===========================================================
# Test 1: TradingView history URL with full referer
# ===========================================================
print("="*70)
print("TEST 1: TV symbol_history with proper headers")
print("="*70)
now = int(datetime.now(timezone.utc).timestamp())
frm = now - 10 * 86400

# Try various TV history endpoints
urls = [
    f"https://scanner.tradingview.com/history?symbol=TVC:GOLD&from={frm}&to={now}&resolution=30",
    f"https://history.tradingview.com/symbol_history?symbol=TVC:GOLD&from={frm}&to={now}&resolution=30",
    f"https://scanner.tradingview.com/symbol_history?symbol=TVC:GOLD&from={frm}&to={now}&resolution=30",
    # The actual chart-data endpoint used by TV widget:
    f"https://chartdata.tradingview.com/symbol_history?symbol=TVC:GOLD&from={frm}&to={now}&resolution=30",
    f"https://chart-data.tradingview.com/symbol_history?symbol=TVC:GOLD&from={frm}&to={now}&resolution=30",
]
for url in urls:
    body, status = fetch(url)
    print(f"  status={status}  url={url[:120]}")
    if status == 200:
        print(f"    body[:300]: {body[:300]}")

# ===========================================================
# Test 2: Stooq for XAUUSD intraday
# ===========================================================
print("\n" + "="*70)
print("TEST 2: Stooq XAUUSD intraday")
print("="*70)
# Stooq URL formats
urls = [
    "https://stooq.com/q/d/l/?s=xauusd&i=5",  # 5min
    "https://stooq.com/q/d/l/?s=xauusd&i=15", # 15min
    "https://stooq.com/q/d/l/?s=xauusd&i=30", # 30min
    "https://stooq.com/q/d/l/?s=xauusd&i=h",  # hourly
    "https://stooq.com/q/d/l/?s=xauusd&i=d",  # daily
]
for url in urls:
    body, status = fetch(url)
    print(f"  status={status}  url={url}")
    if status == 200 and len(body) < 5000:
        # CSV — show first lines
        print(f"    content[:300]: {body[:300]}")
    elif status == 200:
        print(f"    size: {len(body)} bytes")

# ===========================================================
# Test 3: Try TradingView chart-data with WS endpoint test
# ===========================================================
print("\n" + "="*70)
print("TEST 3: TV quote widget data")
print("="*70)
# The TradingView widget embed might give us data
urls = [
    "https://www.tradingview.com/chart-api/v1/symbol-history?symbol=TVC:GOLD&resolution=30&from=1700000000&to=1700100000",
    "https://api.tradingview.com/v1.1/history_candles/TVC/GOLD/30?from=1700000000&to=1700100000",
    # Real endpoint that works:
    "https://scanner.tradingview.com/symbol?symbol=TVC%3AGOLD&fields=close,change,change_abs,name,high,low,open,volume",
]
for url in urls:
    body, status = fetch(url)
    print(f"  status={status}  url={url[:120]}")
    if status == 200:
        print(f"    body[:400]: {body[:400]}")

# ===========================================================
# Test 4: TV websocket.io endpoint (probe only)
# ===========================================================
print("\n" + "="*70)
print("TEST 4: TV socket.io probe")
print("="*70)
try:
    import socket
    s = socket.create_connection(("data.tradingview.com", 443), timeout=5)
    print(f"  data.tradingview.com:443 → reachable")
    s.close()
except Exception as e:
    print(f"  data.tradingview.com:443 → {e}")

try:
    s = socket.create_connection(("socket.tradingview.com", 443), timeout=5)
    print(f"  socket.tradingview.com:443 → reachable")
    s.close()
except Exception as e:
    print(f"  socket.tradingview.com:443 → {e}")

# ===========================================================
# Test 5: Repeated TV scanner calls to test rate limit
# ===========================================================
print("\n" + "="*70)
print("TEST 5: TV scanner repeated calls")
print("="*70)
import time
for i in range(5):
    body, status = fetch("https://scanner.tradingview.com/symbol?symbol=TVC%3AGOLD&fields=close,change,change_abs,name")
    print(f"  call {i+1}: status={status}  body={body[:120]}")
    time.sleep(1)
