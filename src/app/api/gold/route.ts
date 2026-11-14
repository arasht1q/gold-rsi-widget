import { NextResponse } from 'next/server';
import {
  Candle,
  calcRSI,
  calcSMA,
  detectPattern,
  extractFeatures,
  predict,
  predictApproaching,
  buildEntryTicket,
} from '@/lib/gold-analysis';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

// TradingView scanner — gives live price + today's OHLC for TVC:GOLD (spot gold)
const TV_SCANNER = 'https://scanner.tradingview.com/symbol?symbol=TVC%3AGOLD&fields=close,change,change_abs,name,description,high,low,open,volume,type,currency_code';
// Yahoo Finance — historical M30 candles for GC=F (gold futures, for RSI calc)
const YAHOO_GC_M30 = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=30m&range=10d';
const YAHOO_GC_M5  = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=5m&range=5d';
const YAHOO_GC_D1  = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=6mo';
const YAHOO_GC_W1  = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1wk&range=2y';
// Fallback
const BINANCE_PAXG_M30 = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=30m&limit=300';
const BINANCE_PAXG_M5  = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=288';

type RawKline = [number, string, string, string, string, string, number, string, number, string, string, string];

type TVQuote = {
  close: number;
  change: number | null;
  change_abs: number | null;
  name: string;
  description: string;
  high: number;
  low: number;
  open: number;
  volume: number;
  type: string;
  currency_code: string;
};

// ============================================================
// Helpers for previous-day analysis
// ============================================================

// Get UTC date string (YYYY-MM-DD) from a timestamp
function utcDateString(ms: number): string {
  const d = new Date(ms);
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`;
}

// Group candles by UTC day
function groupByDay(candles: Candle[]): Map<string, Candle[]> {
  const map = new Map<string, Candle[]>();
  for (const c of candles) {
    const key = utcDateString(c.openTime);
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(c);
  }
  return map;
}

// Session boundaries in UTC hour
// Asia: 00:00-07:00 UTC (Tokyo)
// Europe: 07:00-13:00 UTC (London)
// US: 13:00-21:00 UTC (New York)
const SESSIONS = [
  { key: 'asia',   label: 'آسیا (توکیو)',   startHour: 0,  endHour: 7  },
  { key: 'europe', label: 'اروپا (لندن)',   startHour: 7,  endHour: 13 },
  { key: 'us',     label: 'آمریکا (نیویورک)', startHour: 13, endHour: 21 },
];

type SessionData = {
  key: string;
  label: string;
  startHourUTC: number;
  endHourUTC: number;
  open: number | null;   // open of first candle in session
  close: number | null;  // close of last candle in session
  high: number | null;
  low: number | null;
  candleCount: number;
  changePct: number | null;  // (close - open) / open * 100
};

function computeSessionsForDay(dayCandles: Candle[]): SessionData[] {
  return SESSIONS.map(s => {
    const sessionCandles = dayCandles.filter(c => {
      const h = new Date(c.openTime).getUTCHours();
      return h >= s.startHour && h < s.endHour;
    });
    if (sessionCandles.length === 0) {
      return {
        key: s.key,
        label: s.label,
        startHourUTC: s.startHour,
        endHourUTC: s.endHour,
        open: null, close: null, high: null, low: null,
        candleCount: 0, changePct: null,
      };
    }
    const open = sessionCandles[0].open;
    const close = sessionCandles[sessionCandles.length - 1].close;
    const high = Math.max(...sessionCandles.map(c => c.high));
    const low = Math.min(...sessionCandles.map(c => c.low));
    return {
      key: s.key,
      label: s.label,
      startHourUTC: s.startHour,
      endHourUTC: s.endHour,
      open, close, high, low,
      candleCount: sessionCandles.length,
      changePct: open !== 0 ? ((close - open) / open) * 100 : 0,
    };
  });
}

type PreviousDayAnalysis = {
  date: string;            // YYYY-MM-DD
  sessions: SessionData[];
  dayHigh: number;
  dayLow: number;
  dayOpen: number;
  dayClose: number;
  lastM5Candle: { time: number; open: number; close: number; high: number; low: number } | null;
};

type TodayFirstM5 = {
  time: number;
  open: number;
  close: number;
  high: number;
  low: number;
} | null;

function analyzePreviousDay(
  m30Candles: Candle[],
  m5Candles: Candle[],
): { prevDay: PreviousDayAnalysis | null; todayFirstM5: TodayFirstM5 } {
  // Get all unique trading days from M30 candles, sorted descending (most recent first)
  const m30ByDay = groupByDay(m30Candles);
  const allDays = Array.from(m30ByDay.keys()).sort().reverse();

  if (allDays.length < 1) {
    return { prevDay: null, todayFirstM5: null };
  }

  // "Today" = the most recent day (which is the current/most recent trading day)
  const todayDate = allDays[0];
  // "Previous day" = the day before today (most recent complete day)
  const prevDate = allDays.length > 1 ? allDays[1] : allDays[0];

  const prevDayCandles = m30ByDay.get(prevDate) || [];
  if (prevDayCandles.length === 0) {
    return { prevDay: null, todayFirstM5: null };
  }

  // Compute previous day stats
  const dayHigh = Math.max(...prevDayCandles.map(c => c.high));
  const dayLow = Math.min(...prevDayCandles.map(c => c.low));
  const dayOpen = prevDayCandles[0].open;
  const dayClose = prevDayCandles[prevDayCandles.length - 1].close;
  const sessions = computeSessionsForDay(prevDayCandles);

  // Find last M5 candle of previous day
  const prevDayM5 = m5Candles.filter(c => utcDateString(c.openTime) === prevDate);
  const lastM5OfPrevDay = prevDayM5.length > 0 ? prevDayM5[prevDayM5.length - 1] : null;

  // Find first M5 candle of today
  const todayM5 = m5Candles.filter(c => utcDateString(c.openTime) === todayDate);
  const firstM5OfToday = todayM5.length > 0 ? todayM5[0] : null;

  return {
    prevDay: {
      date: prevDate,
      sessions,
      dayHigh,
      dayLow,
      dayOpen,
      dayClose,
      lastM5Candle: lastM5OfPrevDay ? {
        time: lastM5OfPrevDay.openTime,
        open: lastM5OfPrevDay.open,
        close: lastM5OfPrevDay.close,
        high: lastM5OfPrevDay.high,
        low: lastM5OfPrevDay.low,
      } : null,
    },
    todayFirstM5: firstM5OfToday ? {
      time: firstM5OfToday.openTime,
      open: firstM5OfToday.open,
      close: firstM5OfToday.close,
      high: firstM5OfToday.high,
      low: firstM5OfToday.low,
    } : null,
  };
}

// ============================================================
// Compute which RSI level (40 or 60) is more likely to be touched first
// Based on: current RSI position, distance to each level, and RSI velocity
// ============================================================
function computeTouchFirst(
  features: any,
  currentRsi: number,
): {
  likelyLevel: 40 | 60;
  probability40: number;
  probability60: number;
  distance40: number;
  distance60: number;
  direction: 'up' | 'down' | 'flat';
  reasoning: string;
} {
  if (!features) {
    return {
      likelyLevel: 60,
      probability40: 0.5,
      probability60: 0.5,
      distance40: Math.abs(currentRsi - 40),
      distance60: Math.abs(currentRsi - 60),
      direction: 'flat',
      reasoning: 'داده کافی نیست',
    };
  }

  const d40 = Math.abs(currentRsi - 40);
  const d60 = Math.abs(currentRsi - 60);
  const velocity = features.rsiVelocity10 ?? 0;

  // If currently in a zone, that zone is "touched"
  if (features.inZone && features.zoneLevel === 40) {
    return {
      likelyLevel: 40, probability40: 1, probability60: 0,
      distance40: 0, distance60: d60,
      direction: velocity > 0.5 ? 'up' : velocity < -0.5 ? 'down' : 'flat',
      reasoning: 'همین الان داخل زون ۴۰ هستیم',
    };
  }
  if (features.inZone && features.zoneLevel === 60) {
    return {
      likelyLevel: 60, probability40: 0, probability60: 1,
      distance40: d40, distance60: 0,
      direction: velocity > 0.5 ? 'up' : velocity < -0.5 ? 'down' : 'flat',
      reasoning: 'همین الان داخل زون ۶۰ هستیم',
    };
  }

  // Probability based on distance + velocity
  // Base score: closer level = higher probability
  // Velocity bias: if rising, more likely to hit 60; if falling, more likely to hit 40
  const totalDist = d40 + d60;
  const base40 = totalDist > 0 ? (1 - d40 / totalDist) : 0.5;  // closer = higher
  const base60 = totalDist > 0 ? (1 - d60 / totalDist) : 0.5;

  // Velocity adjustment: each unit of velocity shifts 5% probability
  // velocity > 0 = rising → favors 60
  // velocity < 0 = falling → favors 40
  const velocityAdj = velocity * 0.05;
  let p60 = base60 + velocityAdj;
  let p40 = base40 - velocityAdj;

  // Normalize to 0..1
  p60 = Math.max(0.05, Math.min(0.95, p60));
  p40 = Math.max(0.05, Math.min(0.95, p40));
  const sum = p40 + p60;
  p40 /= sum;
  p60 /= sum;

  const likelyLevel = p60 > p40 ? 60 : 40;
  const direction = velocity > 0.5 ? 'up' : velocity < -0.5 ? 'down' : 'flat';

  let reasoning = '';
  if (Math.abs(p60 - p40) < 0.1) {
    reasoning = 'احتمال هر دو سطح تقریباً برابر است';
  } else if (likelyLevel === 60) {
    reasoning = `RSI به سطح ۶۰ نزدیک‌تر است (${d60.toFixed(1)} واحد)`;
    if (direction === 'up') reasoning += ' و در حال صعود';
    else if (direction === 'down') reasoning += ' ولی در حال نزول';
  } else {
    reasoning = `RSI به سطح ۴۰ نزدیک‌تر است (${d40.toFixed(1)} واحد)`;
    if (direction === 'down') reasoning += ' و در حال نزول';
    else if (direction === 'up') reasoning += ' ولی در حال صعود';
  }

  return {
    likelyLevel: likelyLevel as 40 | 60,
    probability40: p40,
    probability60: p60,
    distance40: d40,
    distance60: d60,
    direction,
    reasoning,
  };
}

// ============================================================
// Important zones from Doji candles (daily + weekly)
// ============================================================

type ImportantZone = {
  type: 'daily' | 'weekly';
  date: string;             // YYYY-MM-DD of the Doji candle
  open: number;
  close: number;
  midpoint: number;         // (open + close) / 2 — the zone center
  rangeHigh: number;        // max(open, close)
  rangeLow: number;         // min(open, close)
  candleRange: number;      // high - low of the Doji candle
  bodySize: number;         // |close - open|
  bodyRatio: number;        // bodySize / candleRange (Doji threshold: < 0.1)
};

type ZoneAnalysis = {
  zones: ImportantZone[];         // sorted by proximity to current price
  insideZones: ImportantZone[];   // zones the current price is inside
  nearestZone: ImportantZone | null;
  nearestDistance: number | null;  // % distance to nearest zone
  nearestDirection: 'above' | 'below' | 'inside' | null;
  // Direction-aware targets (based on RSI velocity / price trend)
  nearestAbove: ImportantZone | null;   // closest zone ABOVE current price
  nearestBelow: ImportantZone | null;   // closest zone BELOW current price
  nextTarget: ImportantZone | null;     // zone in direction of movement
  nextTargetDistance: number | null;    // % distance to next target
  nextTargetDirection: 'up' | 'down' | 'flat' | null;
};

// Detect Doji candles in a list of candles
// Doji = body <= bodyThreshold * range (default 10%)
function detectDojis(candles: Candle[], bodyThreshold = 0.10): Candle[] {
  return candles.filter(c => {
    const range = c.high - c.low;
    if (range <= 0) return false;
    const body = Math.abs(c.close - c.open);
    return body <= bodyThreshold * range;
  });
}

// Build ImportantZone from a Doji candle
function buildZone(candle: Candle, type: 'daily' | 'weekly'): ImportantZone {
  const range = candle.high - candle.low;
  const body = Math.abs(candle.close - candle.open);
  return {
    type,
    date: utcDateString(candle.openTime),
    open: candle.open,
    close: candle.close,
    midpoint: (candle.open + candle.close) / 2,
    rangeHigh: Math.max(candle.open, candle.close),
    rangeLow: Math.min(candle.open, candle.close),
    candleRange: range,
    bodySize: body,
    bodyRatio: range > 0 ? body / range : 0,
  };
}

function analyzeImportantZones(
  dailyCandles: Candle[],
  weeklyCandles: Candle[],
  currentPrice: number,
  rsiVelocity: number = 0,
): ZoneAnalysis {
  // Detect Dojis
  const dailyDojis = detectDojis(dailyCandles.slice(0, -1));   // exclude current incomplete day
  const weeklyDojis = detectDojis(weeklyCandles.slice(0, -1)); // exclude current incomplete week

  const dailyZones = dailyDojis.map(c => buildZone(c, 'daily'));
  const weeklyZones = weeklyDojis.map(c => buildZone(c, 'weekly'));
  const allZones = [...dailyZones, ...weeklyZones];

  if (allZones.length === 0) {
    return {
      zones: [], insideZones: [], nearestZone: null,
      nearestDistance: null, nearestDirection: null,
      nearestAbove: null, nearestBelow: null,
      nextTarget: null, nextTargetDistance: null, nextTargetDirection: null,
    };
  }

  // Only keep zones within ±10% of current price
  const filterWindow = currentPrice * 0.10;
  const relevantZones = allZones.filter(z =>
    Math.abs(z.midpoint - currentPrice) <= filterWindow
  );

  // Find zones we're inside (price within [rangeLow, rangeHigh] + tolerance)
  const insideTolerance = currentPrice * 0.0015;
  const insideZones = relevantZones.filter(z =>
    currentPrice >= z.rangeLow - insideTolerance &&
    currentPrice <= z.rangeHigh + insideTolerance
  );

  // Sort by proximity (closest first)
  const sortedZones = relevantZones.sort((a, b) => {
    const distA = Math.abs(a.midpoint - currentPrice);
    const distB = Math.abs(b.midpoint - currentPrice);
    return distA - distB;
  });

  // Find nearest zone above and below (excluding inside zones)
  const zonesAbove = sortedZones.filter(z =>
    z.midpoint > currentPrice && !insideZones.includes(z)
  );
  const zonesBelow = sortedZones.filter(z =>
    z.midpoint < currentPrice && !insideZones.includes(z)
  );
  const nearestAbove = zonesAbove.length > 0 ? zonesAbove[0] : null;
  const nearestBelow = zonesBelow.length > 0 ? zonesBelow[0] : null;

  // Determine next target based on RSI velocity (or price trend)
  // velocity > 0.5 → up trend → target is nearestAbove
  // velocity < -0.5 → down trend → target is nearestBelow
  // flat → target is nearest overall
  let nextTarget: ImportantZone | null = null;
  let nextTargetDirection: 'up' | 'down' | 'flat' | null = null;
  if (rsiVelocity > 0.5 && nearestAbove) {
    nextTarget = nearestAbove;
    nextTargetDirection = 'up';
  } else if (rsiVelocity < -0.5 && nearestBelow) {
    nextTarget = nearestBelow;
    nextTargetDirection = 'down';
  } else {
    // flat — pick whichever is closer
    nextTarget = sortedZones.find(z => !insideZones.includes(z)) || null;
    nextTargetDirection = nextTarget
      ? (nextTarget.midpoint > currentPrice ? 'up' : 'down')
      : null;
  }

  const nextTargetDistance = nextTarget
    ? (Math.abs(nextTarget.midpoint - currentPrice) / currentPrice) * 100
    : null;

  // Nearest zone (any direction)
  const nearestNonInside = sortedZones.find(z => !insideZones.includes(z));
  let nearestDistance: number | null = null;
  let nearestDirection: 'above' | 'below' | 'inside' | null = null;
  if (nearestNonInside) {
    nearestDistance = (Math.abs(nearestNonInside.midpoint - currentPrice) / currentPrice) * 100;
    nearestDirection = nearestNonInside.midpoint > currentPrice ? 'above' : 'below';
  } else if (insideZones.length > 0) {
    nearestDirection = 'inside';
  }

  return {
    zones: sortedZones.slice(0, 10),  // top 10 nearest
    insideZones,
    nearestZone: nearestNonInside || (insideZones.length > 0 ? insideZones[0] : null),
    nearestDistance,
    nearestDirection,
    nearestAbove,
    nearestBelow,
    nextTarget,
    nextTargetDistance,
    nextTargetDirection,
  };
}

async function fetchTradingView(): Promise<TVQuote | null> {
  // Retry up to 3 times to handle 429 rate limiting
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(TV_SCANNER, {
        cache: 'no-store',
        headers: {
          'User-Agent': 'Mozilla/5.0',
          'Origin': 'https://www.tradingview.com',
          'Referer': 'https://www.tradingview.com/',
        },
      });
      if (res.status === 429) {
        await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
        continue;
      }
      if (!res.ok) return null;
      const d = (await res.json()) as Partial<TVQuote>;
      if (d && typeof d.close === 'number') {
        return {
          close: d.close,
          change: d.change ?? null,
          change_abs: d.change_abs ?? null,
          name: d.name ?? 'GOLD',
          description: d.description ?? 'Gold',
          high: d.high ?? d.close,
          low: d.low ?? d.close,
          open: d.open ?? d.close,
          volume: d.volume ?? 0,
          type: d.type ?? 'spot',
          currency_code: d.currency_code ?? 'USD',
        };
      }
      return null;
    } catch {
      if (attempt < 2) {
        await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
        continue;
      }
      return null;
    }
  }
  return null;
}

async function fetchBinance(url: string): Promise<Candle[]> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Binance API ${res.status}`);
  const raw = (await res.json()) as RawKline[];
  return raw.map(k => ({
    openTime: k[0],
    open: parseFloat(k[1]),
    high: parseFloat(k[2]),
    low: parseFloat(k[3]),
    close: parseFloat(k[4]),
    volume: parseFloat(k[5]),
  }));
}

type YahooChart = {
  chart: {
    result: Array<{
      timestamp: number[];
      indicators: {
        quote: Array<{
          open: (number | null)[];
          high: (number | null)[];
          low: (number | null)[];
          close: (number | null)[];
          volume: (number | null)[];
        }>;
      };
      meta?: { regularMarketPrice?: number; chartPreviousClose?: number; symbol?: string };
    }>;
    error?: any;
  };
};

async function fetchYahoo(url: string): Promise<{ candles: Candle[]; marketPrice: number | null }> {
  const res = await fetch(url, {
    cache: 'no-store',
    headers: { 'User-Agent': 'Mozilla/5.0' },
  });
  if (!res.ok) throw new Error(`Yahoo API ${res.status}`);
  const data = (await res.json()) as YahooChart;
  if (data.chart.error || !data.chart.result || !data.chart.result[0]) {
    throw new Error('Yahoo chart returned no data');
  }
  const result = data.chart.result[0];
  const ts = result.timestamp;
  const q = result.indicators.quote[0];
  const candles: Candle[] = [];
  for (let i = 0; i < ts.length; i++) {
    if (q.open[i] !== null && q.close[i] !== null) {
      candles.push({
        openTime: ts[i] * 1000,
        open: q.open[i]!,
        high: q.high[i] ?? q.close[i]!,
        low: q.low[i] ?? q.close[i]!,
        close: q.close[i]!,
        volume: q.volume[i] ?? 0,
      });
    }
  }
  return { candles, marketPrice: result.meta?.regularMarketPrice ?? null };
}

export async function GET() {
  let priceSource = 'TradingView TVC:GOLD';
  let candleSource = 'Yahoo GC=F (historical)';
  let tvQuote: TVQuote | null = null;
  let candles30m: Candle[] = [];
  let candles5m: Candle[] = [];

  // 1. Always try TradingView first for live price
  tvQuote = await fetchTradingView();
  if (!tvQuote) {
    priceSource = 'Yahoo GC=F (TV unavailable)';
  }

  // 2. Get historical candles from Yahoo for RSI computation
  // Also fetch daily and weekly candles for Doji zone detection
  let dailyCandles: Candle[] = [];
  let weeklyCandles: Candle[] = [];
  try {
    const [m30, m5, d1, w1] = await Promise.all([
      fetchYahoo(YAHOO_GC_M30),
      fetchYahoo(YAHOO_GC_M5),
      fetchYahoo(YAHOO_GC_D1).catch(() => ({ candles: [] as Candle[], marketPrice: null })),
      fetchYahoo(YAHOO_GC_W1).catch(() => ({ candles: [] as Candle[], marketPrice: null })),
    ]);
    candles30m = m30.candles;
    candles5m = m5.candles;
    dailyCandles = d1.candles;
    weeklyCandles = w1.candles;
  } catch {
    candleSource = 'Binance PAXG (Yahoo unavailable)';
    try {
      const [m30, m5] = await Promise.all([
        fetchBinance(BINANCE_PAXG_M30),
        fetchBinance(BINANCE_PAXG_M5),
      ]);
      candles30m = m30;
      candles5m = m5;
    } catch (e2: any) {
      return NextResponse.json({ ok: false, error: `All sources failed: ${e2?.message}` }, { status: 500 });
    }
  }

  if (candles30m.length < 200) {
    return NextResponse.json({ ok: false, error: `Insufficient candles: ${candles30m.length}` }, { status: 500 });
  }

  // 3. If we have TradingView live price, override the last candle's close with it
  // This ensures RSI is computed on data ending at the live (broker-accurate) price
  if (tvQuote && candles30m.length > 0) {
    const lastIdx = candles30m.length - 1;
    const tvLive = tvQuote.close;
    const oldClose = candles30m[lastIdx].close;
    // Adjust last candle: use TradingView price as the new close
    // Also adjust high/low to include the new price
    candles30m[lastIdx] = {
      ...candles30m[lastIdx],
      close: tvLive,
      high: Math.max(candles30m[lastIdx].high, tvLive),
      low: Math.min(candles30m[lastIdx].low, tvLive),
    };
  }

  // Compute RSI on (possibly adjusted) candle data
  const closes = candles30m.map(c => c.close);
  const rsi = calcRSI(closes, 30);
  const sma50 = calcSMA(closes, 50);
  const sma200 = calcSMA(closes, 200);

  const features = extractFeatures(candles30m, rsi, sma50);
  const prediction = features ? predict(features) : null;

  // Previous day analysis (sessions, high/low, last M5 candle, today's first M5)
  const { prevDay, todayFirstM5 } = analyzePreviousDay(candles30m, candles5m);

  // Always compute approach/simulation predictions for BOTH levels
  // (so user always sees the probabilities for what would happen at 40 and 60)
  let approach40: any = null;
  let approach60: any = null;
  if (features) {
    // For level 40: if RSI is in zone 40, this is the actual prediction; otherwise simulation
    if (features.inZone && features.zoneLevel === 40) {
      // actual already in `prediction`
    } else {
      const ap = predictApproaching(features, 40);
      approach40 = {
        reversal: ap.reversal,
        divergence: ap.divergence,
        passThrough: ap.passThrough,
        topCategory: ap.topCategory,
        topFa: ap.topFa,
        reasons: ap.reasons,
        targetLevel: 40,
        currentRsi: features.rsi,
        distanceToLevel: Math.abs(features.rsi - 40),
        isSimulation: true,
      };
    }
    // Same for level 60
    if (features.inZone && features.zoneLevel === 60) {
      // actual already in `prediction`
    } else {
      const ap = predictApproaching(features, 60);
      approach60 = {
        reversal: ap.reversal,
        divergence: ap.divergence,
        passThrough: ap.passThrough,
        topCategory: ap.topCategory,
        topFa: ap.topFa,
        reasons: ap.reasons,
        targetLevel: 60,
        currentRsi: features.rsi,
        distanceToLevel: Math.abs(features.rsi - 60),
        isSimulation: true,
      };
    }
  }

  const pattern = detectPattern(candles5m);
  const ticket = buildEntryTicket(prediction, pattern, candles30m, features);

  const lastCandle = candles30m[candles30m.length - 1];
  const lastRsi = rsi[rsi.length - 1];
  // Prefer TradingView live price; fall back to last candle close
  const lastPrice = tvQuote?.close ?? lastCandle.close;

  // Compute proximity of live price to previous day's high/low
  let proximityToPrevHigh: number | null = null;
  let proximityToPrevLow: number | null = null;
  let positionInRange: number | null = null;  // 0 = at low, 1 = at high, 0.5 = middle
  if (prevDay && lastPrice > 0) {
    const range = prevDay.dayHigh - prevDay.dayLow;
    if (range > 0) {
      proximityToPrevHigh = ((prevDay.dayHigh - lastPrice) / prevDay.dayHigh) * 100;
      proximityToPrevLow = ((lastPrice - prevDay.dayLow) / prevDay.dayLow) * 100;
      positionInRange = (lastPrice - prevDay.dayLow) / range;
      positionInRange = Math.max(0, Math.min(1, positionInRange));
    }
  }

  // Analyze important zones from daily + weekly Doji candles
  // Pass RSI velocity to determine direction of movement
  const rsiVelocity = features?.rsiVelocity10 ?? 0;
  const zoneAnalysis = analyzeImportantZones(dailyCandles, weeklyCandles, lastPrice, rsiVelocity);

  // Detect if market is currently closed (no recent candle in last 2 hours)
  const now = Date.now();
  const lastCandleAgeMin = (now - lastCandle.openTime) / 60000;
  // TradingView's "change" tells us if today's session is current; if change is 0 and last candle is old, market is closed
  const marketOpen = lastCandleAgeMin < 120 && (tvQuote?.change ?? 0) !== 0
    ? true
    : lastCandleAgeMin < 30; // very recent candle

  const distTo60 = Math.abs(lastRsi - 60);
  const distTo40 = Math.abs(lastRsi - 40);
  const nearestLevel = distTo60 < distTo40 ? 60 : 40;
  const nearestDist = Math.min(distTo60, distTo40);
  const proximity = Math.max(0, 1 - nearestDist / 10);

  let status = 'NORMAL';
  let statusFa = marketOpen ? 'عادی' : 'بازار بسته — آخرین قیمت';
  if (!marketOpen) {
    status = 'CLOSED';
    if (features?.inZone) {
      statusFa = `بازار بسته — آخرین وضعیت: زون ${features.zoneLevel}`;
    } else if (nearestDist < 2) {
      statusFa = `بازار بسته — نزدیک سطح ${nearestLevel} بود`;
    }
  } else if (features?.inZone) {
    status = 'IN_ZONE';
    statusFa = `در زون ${features.zoneLevel}`;
  } else if (nearestDist < 2) {
    status = 'APPROACHING';
    statusFa = `نزدیک سطح ${nearestLevel}`;
  } else if (nearestDist < 5) {
    status = 'WATCH';
    statusFa = `تحت نظارت (${nearestLevel})`;
  }

  const recentCandles = candles30m.slice(-48).map((c, i) => ({
    time: c.openTime,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
    rsi: rsi[rsi.length - 48 + i] ?? null,
  }));

  const recentM5 = candles5m.slice(-6).map(c => ({
    time: c.openTime,
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
    isUp: c.close >= c.open,
  }));

  return NextResponse.json({
    ok: true,
    priceSource,
    candleSource,
    priceSourceDescription: tvQuote
      ? `TradingView TVC:GOLD (طلای اسپات) — تطبیق بسیار نزدیک با XAUUSD بروکر شما`
      : 'Yahoo GC=F (fallback)',
    marketOpen,
    timestamp: Date.now(),
    lastPrice,
    lastPriceSource: tvQuote ? 'TradingView live ticker' : 'last candle close',
    tvQuote: tvQuote ? {
      name: tvQuote.name,
      description: tvQuote.description,
      close: tvQuote.close,
      change: tvQuote.change,
      change_abs: tvQuote.change_abs,
      open: tvQuote.open,
      high: tvQuote.high,
      low: tvQuote.low,
      type: tvQuote.type,
      currency: tvQuote.currency_code,
    } : null,
    lastCandleTime: lastCandle.openTime,
    lastCandleAgeMin: Math.round(lastCandleAgeMin),
    lastRsi,
    rsiPeriod: 30,
    timeframe: 'M30',
    level: nearestLevel,
    nearestDist,
    proximity,
    status,
    statusFa,
    features: features ? {
      rsi: features.rsi,
      rsiVelocity10: features.rsiVelocity10,
      rsiVelocity5: features.rsiVelocity5,
      candlesInZone: features.candlesInZone,
      inZone: features.inZone,
      zoneLevel: features.zoneLevel,
      distSMA50: features.distSMA50,
      volRatio5_20: features.volRatio5_20,
      session: features.session,
      sessionFa: features.sessionFa,
      trend50Pct: features.trend50Pct,
    } : null,
    prediction: prediction ? {
      reversal: prediction.reversal,
      divergence: prediction.divergence,
      passThrough: prediction.passThrough,
      topCategory: prediction.topCategory,
      topFa: prediction.topFa,
      reasons: prediction.reasons,
    } : null,
    approach40,
    approach60,
    // Combined prediction: which level likely to be touched first
    touchFirst: computeTouchFirst(features, lastRsi),
    // Important zones from Doji candles
    importantZones: {
      zones: zoneAnalysis.zones,
      insideZones: zoneAnalysis.insideZones,
      nearestZone: zoneAnalysis.nearestZone,
      nearestDistance: zoneAnalysis.nearestDistance,
      nearestDirection: zoneAnalysis.nearestDirection,
      nearestAbove: zoneAnalysis.nearestAbove,
      nearestBelow: zoneAnalysis.nearestBelow,
      nextTarget: zoneAnalysis.nextTarget,
      nextTargetDistance: zoneAnalysis.nextTargetDistance,
      nextTargetDirection: zoneAnalysis.nextTargetDirection,
      currentPrice: lastPrice,
    },
    // Previous day analysis
    prevDay: prevDay ? {
      date: prevDay.date,
      sessions: prevDay.sessions,
      dayHigh: prevDay.dayHigh,
      dayLow: prevDay.dayLow,
      dayOpen: prevDay.dayOpen,
      dayClose: prevDay.dayClose,
      lastM5Candle: prevDay.lastM5Candle,
    } : null,
    todayFirstM5,
    proximityToPrevHigh,
    proximityToPrevLow,
    positionInRange,
    pattern: {
      pattern: pattern.pattern,
      label: pattern.label,
      labelFa: pattern.labelFa,
      bias: pattern.bias,
      strength: pattern.strength,
    },
    ticket: {
      valid: ticket.valid,
      direction: ticket.direction,
      directionFa: ticket.directionFa,
      entryPrice: ticket.entryPrice,
      stopLoss: ticket.stopLoss,
      takeProfit: ticket.takeProfit,
      riskRewardRatio: ticket.riskRewardRatio,
      confidence: ticket.confidence,
      notes: ticket.notes,
    },
    recentCandles,
    recentM5,
    sma50Last: sma50[sma50.length - 1] ?? null,
    sma200Last: sma200[sma200.length - 1] ?? null,
  });
}
