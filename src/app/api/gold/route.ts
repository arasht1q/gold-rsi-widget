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

const BINANCE_M30 = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=30m&limit=300';
const BINANCE_M5  = 'https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=20';

type RawKline = [
  number, string, string, string, string, string, number, string, number, string, string, string
];

async function fetchKlines(url: string): Promise<Candle[]> {
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

export async function GET() {
  try {
    const [candles30m, candles5m] = await Promise.all([
      fetchKlines(BINANCE_M30),
      fetchKlines(BINANCE_M5),
    ]);

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

    const distTo60 = Math.abs(lastRsi - 60);
    const distTo40 = Math.abs(lastRsi - 40);
    const nearestLevel = distTo60 < distTo40 ? 60 : 40;
    const nearestDist = Math.min(distTo60, distTo40);
    const proximity = Math.max(0, 1 - nearestDist / 10);

    let status = 'NORMAL';
    let statusFa = 'عادی';
    if (features?.inZone) {
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
      timestamp: Date.now(),
      lastPrice: lastCandle.close,
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
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e?.message ?? 'unknown' }, { status: 500 });
  }
}
