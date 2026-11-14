import { NextResponse } from 'next/server';
import {
  Candle,
  calcRSI,
  calcSMA,
  detectPattern,
  extractFeatures,
  predict,
  buildEntryTicket,
} from '@/lib/gold-analysis';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

// Yahoo Finance chart endpoints — free, no API key needed
// GC=F = Gold Futures (COMEX) — tracks XAUUSD spot very closely during market hours
const YAHOO_GC_M30 = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=30m&range=10d';
const YAHOO_GC_M5  = 'https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=5m&range=1d';
// Fallback: Binance PAXG/USDT (24/7 market — used when Yahoo is down or market closed)
const BINANCE_PAXG_M30 = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=30m&limit=300';
const BINANCE_PAXG_M5  = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=20';

type RawKline = [
  number, string, string, string, string, string, number, string, number, string, string, string
];

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
      meta?: {
        regularMarketPrice?: number;
        chartPreviousClose?: number;
        symbol?: string;
      };
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
  let source = 'GC=F (Yahoo Finance)';
  let candles30m: Candle[] = [];
  let candles5m: Candle[] = [];
  let marketPrice: number | null = null;

  // Try GC=F first
  try {
    const [m30, m5] = await Promise.all([
      fetchYahoo(YAHOO_GC_M30),
      fetchYahoo(YAHOO_GC_M5),
    ]);
    candles30m = m30.candles;
    candles5m = m5.candles;
    marketPrice = m30.marketPrice;
  } catch (e) {
    // Fallback to Binance PAXG
    source = 'PAXG/USDT (Binance) — fallback';
    try {
      const [m30, m5] = await Promise.all([
        fetchBinance(BINANCE_PAXG_M30),
        fetchBinance(BINANCE_PAXG_M5),
      ]);
      candles30m = m30;
      candles5m = m5;
    } catch (e2: any) {
      return NextResponse.json({ ok: false, error: `Both sources failed: ${e2?.message}` }, { status: 500 });
    }
  }

  if (candles30m.length < 200) {
    return NextResponse.json({
      ok: false,
      error: `Insufficient candles: ${candles30m.length}`,
      source,
    }, { status: 500 });
  }

  const closes = candles30m.map(c => c.close);
  const rsi = calcRSI(closes, 30);
  const sma50 = calcSMA(closes, 50);
  const sma200 = calcSMA(closes, 200);

  const features = extractFeatures(candles30m, rsi, sma50);
  const prediction = features ? predict(features) : null;
  const pattern = detectPattern(candles5m);
  const ticket = buildEntryTicket(prediction, pattern, candles30m, features);

  const lastCandle = candles30m[candles30m.length - 1];
  const lastRsi = rsi[rsi.length - 1];
  const lastPrice = marketPrice ?? lastCandle.close;

  // Detect if market is currently closed (no recent candle in last 2 hours)
  const now = Date.now();
  const lastCandleAgeMin = (now - lastCandle.openTime) / 60000;
  const marketOpen = lastCandleAgeMin < 120; // last candle within 2 hours

  const distTo60 = Math.abs(lastRsi - 60);
  const distTo40 = Math.abs(lastRsi - 40);
  const nearestLevel = distTo60 < distTo40 ? 60 : 40;
  const nearestDist = Math.min(distTo60, distTo40);
  const proximity = Math.max(0, 1 - nearestDist / 10);

  let status = 'NORMAL';
  let statusFa = marketOpen ? 'عادی' : 'بازار بسته — آخرین قیمت جمعه';
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
    source,
    sourceDescription: source.startsWith('GC=F')
      ? 'Yahoo Finance GC=F (Gold Futures COMEX) — نزدیک‌ترین منبع رایگان به XAUUSD اسپات'
      : 'Binance PAXG/USDT (fallback) — توکن طلای بinance که ۲۴/۷ معامله می‌شود',
    marketOpen,
    timestamp: Date.now(),
    lastPrice,
    lastPriceSource: marketPrice !== null ? 'live ticker' : 'last candle close',
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
