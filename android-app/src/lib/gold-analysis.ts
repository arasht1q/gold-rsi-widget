/**
 * Pattern detection + prediction logic for the gold RSI widget.
 * Based on the 2-year backtest (1328 events) we ran earlier.
 */

export type Candle = {
  openTime: number; // ms
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type Pattern =
  | 'none'
  | 'doji'
  | 'bullish_pin'
  | 'bearish_pin'
  | 'hammer'
  | 'bullish_engulfing'
  | 'bearish_engulfing';

export type PatternInfo = {
  pattern: Pattern;
  label: string;
  labelFa: string;
  bias: 'bullish' | 'bearish' | 'neutral';
  strength: number; // 0..1
};

// ----------------------------- RSI (Wilder) -----------------------------
export function calcRSI(closes: number[], period = 30): number[] {
  if (closes.length < period + 1) return [];
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d >= 0) gain += d; else loss -= d;
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  const rsiArr: number[] = new Array(closes.length).fill(NaN);
  rsiArr[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = period + 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    const g = d > 0 ? d : 0;
    const l = d < 0 ? -d : 0;
    avgGain = (avgGain * (period - 1) + g) / period;
    avgLoss = (avgLoss * (period - 1) + l) / period;
    rsiArr[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return rsiArr;
}

// ----------------------------- SMA -----------------------------
export function calcSMA(values: number[], period: number): number[] {
  const out: number[] = new Array(values.length).fill(NaN);
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= period) sum -= values[i - period];
    if (i >= period - 1) out[i] = sum / period;
  }
  return out;
}

// ----------------------------- Pattern detection (single candle + context) -----------------------------
export function detectPattern(candles: Candle[]): PatternInfo {
  if (candles.length < 2) {
    return { pattern: 'none', label: 'No data', labelFa: 'بدون داده', bias: 'neutral', strength: 0 };
  }
  const cur = candles[candles.length - 1];
  const prev = candles[candles.length - 2];

  const body = Math.abs(cur.close - cur.open);
  const range = Math.max(cur.high - cur.low, 1e-6);
  const upperWick = cur.high - Math.max(cur.open, cur.close);
  const lowerWick = Math.min(cur.open, cur.close) - cur.low;

  // Doji: body <= 10% of range
  if (body <= range * 0.1) {
    return {
      pattern: 'doji',
      label: 'Doji',
      labelFa: 'دوجی',
      bias: 'neutral',
      strength: 0.5,
    };
  }

  // Bullish pin bar / hammer: long lower wick (>= 2/3 range), small body at top
  if (lowerWick >= range * 0.6 && body <= range * 0.35) {
    // Hammer if in downtrend (prev 3 candles falling)
    const last3 = candles.slice(-4, -1);
    const isHammer = last3.length === 3 && last3[2].close < last3[0].open;
    return {
      pattern: isHammer ? 'hammer' : 'bullish_pin',
      label: isHammer ? 'Hammer' : 'Bullish Pin Bar',
      labelFa: isHammer ? 'همر' : 'پین بار صعودی',
      bias: 'bullish',
      strength: lowerWick / range,
    };
  }

  // Bearish pin bar: long upper wick, small body at bottom
  if (upperWick >= range * 0.6 && body <= range * 0.35) {
    return {
      pattern: 'bearish_pin',
      label: 'Bearish Pin Bar',
      labelFa: 'پین بار نزولی',
      bias: 'bearish',
      strength: upperWick / range,
    };
  }

  // Engulfing
  const prevBody = Math.abs(prev.close - prev.open);
  const curBodyMax = Math.max(cur.open, cur.close);
  const curBodyMin = Math.min(cur.open, cur.close);
  const prevBodyMax = Math.max(prev.open, prev.close);
  const prevBodyMin = Math.min(prev.open, prev.close);

  // Bullish engulfing: prev red, cur green, cur engulfs prev body
  if (prev.close < prev.open && cur.close > cur.open &&
      curBodyMax >= prevBodyMax && curBodyMin <= prevBodyMin) {
    return {
      pattern: 'bullish_engulfing',
      label: 'Bullish Engulfing',
      labelFa: 'اینگالف صعودی',
      bias: 'bullish',
      strength: Math.min(1, curBodyMax - curBodyMin / (prevBodyMax - prevBodyMin + 1e-6)),
    };
  }

  // Bearish engulfing
  if (prev.close > prev.open && cur.close < cur.open &&
      curBodyMax >= prevBodyMax && curBodyMin <= prevBodyMin) {
    return {
      pattern: 'bearish_engulfing',
      label: 'Bearish Engulfing',
      labelFa: 'اینگالف نزولی',
      bias: 'bearish',
      strength: Math.min(1, curBodyMax - curBodyMin / (prevBodyMax - prevBodyMin + 1e-6)),
    };
  }

  return { pattern: 'none', label: 'No pattern', labelFa: 'بدون الگو', bias: 'neutral', strength: 0 };
}

// ----------------------------- Feature extraction -----------------------------
export type Features = {
  rsi: number;
  rsiVelocity10: number;
  rsiVelocity5: number;
  candlesInZone: number;       // # of consecutive candles RSI has been in the current zone
  inZone: boolean;
  zoneLevel: 40 | 60 | null;
  zoneEnterIdx: number;        // index in the candles array where zone entry began
  distSMA50: number;           // % distance from SMA50
  volRatio5_20: number;
  session: 'asia_morning' | 'europe' | 'us' | 'asia_night';
  sessionFa: string;
  trend50Pct: number;
};

export function extractFeatures(
  candles: Candle[],
  rsi: number[],
  sma50: number[],
): Features | null {
  if (candles.length < 200 || rsi.length < 10) return null;
  const i = candles.length - 1;
  const lastRsi = rsi[i];
  const lastPrice = candles[i].close;

  // Zone detection
  let inZone = false;
  let zoneLevel: 40 | 60 | null = null;
  if (lastRsi >= 59 && lastRsi <= 61) { inZone = true; zoneLevel = 60; }
  else if (lastRsi >= 39 && lastRsi <= 41) { inZone = true; zoneLevel = 40; }

  // Candles in zone: count back from i while RSI stays in zone
  let candlesInZone = 0;
  let zoneEnterIdx = i;
  if (inZone && zoneLevel !== null) {
    const lo = zoneLevel - 1;
    const hi = zoneLevel + 1;
    let j = i;
    while (j >= 0 && rsi[j] >= lo && rsi[j] <= hi) {
      candlesInZone++;
      zoneEnterIdx = j;
      j--;
    }
  }

  // RSI velocity
  const rsiVel10 = lastRsi - rsi[i - 10];
  const rsiVel5 = lastRsi - rsi[i - 5];

  // SMA50 distance
  const sma = sma50[i];
  const distSMA50 = sma && !isNaN(sma) ? ((lastPrice - sma) / sma) * 100 : 0;

  // Volume ratio
  const recent5 = candles.slice(i - 4, i + 1).map(c => c.volume);
  const recent20 = candles.slice(i - 19, i + 1).map(c => c.volume);
  const avg5 = recent5.reduce((a, b) => a + b, 0) / 5;
  const avg20 = recent20.reduce((a, b) => a + b, 0) / 20;
  const volRatio = avg20 > 0 ? avg5 / avg20 : 1;

  // Trend 50-candle %
  const trend50 = ((lastPrice - candles[i - 50].close) / candles[i - 50].close) * 100;

  // Session by Tehran time = UTC + 3:30
  const tehranHour = (candles[i].openTime / 1000 + 3.5 * 3600) % (24 * 3600) / 3600;
  let session: Features['session'] = 'asia_night';
  let sessionFa = 'شب (آسیا)';
  if (tehranHour >= 6 && tehranHour < 12) { session = 'asia_morning'; sessionFa = 'صبح (آسیا)'; }
  else if (tehranHour >= 12 && tehranHour < 17) { session = 'europe'; sessionFa = 'ظهر (اروپا)'; }
  else if (tehranHour >= 17 && tehranHour < 22) { session = 'us'; sessionFa = 'عصر (آمریکا)'; }

  return {
    rsi: lastRsi,
    rsiVelocity10: rsiVel10,
    rsiVelocity5: rsiVel5,
    candlesInZone,
    inZone,
    zoneLevel,
    zoneEnterIdx,
    distSMA50,
    volRatio5_20: volRatio,
    session,
    sessionFa,
    trend50Pct: trend50,
  };
}

// ----------------------------- Prediction -----------------------------
// Means from the 2-year backtest (level 60 / 40 split)
const MEANS = {
  60: {
    REVERSAL:     { candlesInZone: 1.54, rsiVel10: 1.67, volRatio: 1.07 },
    DIVERGENCE:   { candlesInZone: 2.17, rsiVel10: 3.05, volRatio: 1.02 },
    PASS_THROUGH: { candlesInZone: 1.83, rsiVel10: 2.16, volRatio: 1.10 },
  },
  40: {
    REVERSAL:     { candlesInZone: 1.61, rsiVel10: -2.03, volRatio: 1.07 },
    DIVERGENCE:   { candlesInZone: 2.78, rsiVel10: -3.45, volRatio: 1.02 },
    PASS_THROUGH: { candlesInZone: 1.78, rsiVel10: -3.40, volRatio: 1.10 },
  },
};

// Base rates from 2-year data
const BASE_RATES = {
  REVERSAL: 0.329,
  DIVERGENCE: 0.210,
  PASS_THROUGH: 0.461,
};

// Session multipliers (relative reversal rate)
const SESSION_MULT = {
  asia_morning: { REVERSAL: 0.97, DIVERGENCE: 1.0, PASS_THROUGH: 1.0 },
  europe:       { REVERSAL: 0.85, DIVERGENCE: 1.0, PASS_THROUGH: 1.10 },
  us:           { REVERSAL: 1.12, DIVERGENCE: 1.0, PASS_THROUGH: 0.93 },
  asia_night:   { REVERSAL: 1.05, DIVERGENCE: 1.0, PASS_THROUGH: 0.97 },
};

export type Prediction = {
  reversal: number;       // 0..1
  divergence: number;
  passThrough: number;
  topCategory: 'REVERSAL' | 'DIVERGENCE' | 'PASS_THROUGH';
  topFa: string;
  reasons: string[];
};

export function predict(f: Features): Prediction | null {
  if (!f.inZone || f.zoneLevel === null) return null;
  const level = f.zoneLevel as 40 | 60;
  return predictForLevel(f, level, false);
}

/**
 * Pre-touch prediction: simulate what would happen IF RSI touched the nearest
 * level right now. Used when RSI is approaching but not yet in zone.
 *
 * Uses current market features (velocity, volume, session, trend) but assumes
 * candles_in_zone = 0 (just touched).
 */
export function predictApproaching(f: Features, targetLevel: 40 | 60): Prediction {
  // Build a simulated features object: same as f but with inZone=true, level set, candles=0
  const simulated: Features = {
    ...f,
    inZone: true,
    zoneLevel: targetLevel,
    candlesInZone: 0,
  };
  return predictForLevel(simulated, targetLevel, true);
}

function predictForLevel(f: Features, level: 40 | 60, isSimulation: boolean): Prediction {
  const means = MEANS[level];

  // Score each category by similarity to its mean profile
  const cats = ['REVERSAL', 'DIVERGENCE', 'PASS_THROUGH'] as const;
  const distances: Record<string, number> = {};
  for (const c of cats) {
    const m = means[c];
    const dCandles = Math.pow((f.candlesInZone - m.candlesInZone) / 3, 2);
    const dVel = Math.pow((f.rsiVelocity10 - m.rsiVel10) / 4, 2);
    const dVol = Math.pow((f.volRatio5_20 - m.volRatio) / 0.4, 2);
    distances[c] = Math.sqrt(dCandles * 3 + dVel * 1 + dVol * 1);
  }
  const invD = cats.map(c => 1 / (distances[c] + 0.3));
  const sumInv = invD.reduce((a, b) => a + b, 0);

  let probs = cats.map((c, idx) => BASE_RATES[c] * SESSION_MULT[f.session][c] * (invD[idx] / (sumInv / 3)));
  const sumP = probs.reduce((a, b) => a + b, 0);
  probs = probs.map(p => p / sumP);

  // Build reasoning
  const reasons: string[] = [];
  if (isSimulation) {
    reasons.push(`پیش‌بینی فرضی: اگر RSI الان به سطح ${level} برسد`);
    reasons.push(`RSI فعلی ${f.rsi.toFixed(2)} — فاصله ${Math.abs(f.rsi - level).toFixed(2)} واحد تا سطح ${level}`);
  } else {
    reasons.push(`RSI در زون ${level} است و ${f.candlesInZone} کندل است که در زون مانده`);
  }
  if (f.candlesInZone >= 5) {
    reasons.push(`مدت طولانی در زون → احتمال برگشت بیشتر`);
  } else if (f.candlesInZone <= 2) {
    reasons.push(`مدت کوتاه در زون → احتمال گذشتن بیشتر`);
  }
  if (Math.abs(f.rsiVelocity10) > 3) {
    reasons.push(`سرعت RSI زیاد است (${f.rsiVelocity10.toFixed(1)}) → خطر واگرایی`);
  } else if (Math.abs(f.rsiVelocity10) < 1) {
    reasons.push(`سرعت RSI کم است (${f.rsiVelocity10.toFixed(1)}) → احتمال برگشت بیشتر`);
  }
  if (f.volRatio5_20 > 1.3) {
    reasons.push(`حجم اخیر جهش داشته (${f.volRatio5_20.toFixed(2)}) → مومنتوم قوی`);
  } else if (f.volRatio5_20 < 0.8) {
    reasons.push(`حجم اخیر کم است (${f.volRatio5_20.toFixed(2)}) → بازار بی‌تحرک`);
  }
  reasons.push(`سشن: ${f.sessionFa}`);

  const topIdx = probs.indexOf(Math.max(...probs));
  const topFaMap = { REVERSAL: 'برگشت', DIVERGENCE: 'واگرایی', PASS_THROUGH: 'گذشتن' };
  return {
    reversal: probs[0],
    divergence: probs[1],
    passThrough: probs[2],
    topCategory: cats[topIdx],
    topFa: topFaMap[cats[topIdx]],
    reasons,
  };
}

// ----------------------------- Entry ticket -----------------------------
export type EntryTicket = {
  valid: boolean;
  direction: 'BUY' | 'SELL' | null;
  directionFa: string;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  riskRewardRatio: number;
  confidence: number; // 0..1
  notes: string[];
};

export function buildEntryTicket(
  prediction: Prediction | null,
  pattern: PatternInfo,
  candles: Candle[],
  features: Features | null,
): EntryTicket {
  if (!prediction || !features || !features.inZone || features.zoneLevel === null) {
    return {
      valid: false, direction: null, directionFa: '—',
      entryPrice: 0, stopLoss: 0, takeProfit: 0,
      riskRewardRatio: 0, confidence: 0, notes: ['هنوز در زون 40 یا 60 نیستیم'],
    };
  }
  const lastCandle = candles[candles.length - 1];
  const entryPrice = lastCandle.close;

  // Direction:
  //   Level 60 (overbought) + bearish pattern → SELL
  //   Level 40 (oversold)   + bullish pattern → BUY
  const level = features.zoneLevel;
  let direction: 'BUY' | 'SELL' | null = null;
  let dirFa = '—';
  let valid = false;
  let confidence = 0;
  const notes: string[] = [];

  if (level === 60 && pattern.bias === 'bearish') {
    direction = 'SELL';
    dirFa = 'فروش (SELL)';
    valid = true;
    confidence = Math.min(0.9, prediction.reversal * (0.5 + pattern.strength * 0.5));
    notes.push(`الگوی ${pattern.labelFa} در سطح اشباع خرید (60) → سیگنال فروش`);
  } else if (level === 40 && pattern.bias === 'bullish') {
    direction = 'BUY';
    dirFa = 'خرید (BUY)';
    valid = true;
    confidence = Math.min(0.9, prediction.reversal * (0.5 + pattern.strength * 0.5));
    notes.push(`الگوی ${pattern.labelFa} در سطح اشباع فروش (40) → سیگنال خرید`);
  } else if (level === 60 && pattern.bias === 'bullish') {
    notes.push(`الگوی صعودی در سطح اشباع خرید — با سیگنال اصلی هم‌جهت نیست، صبر کنید`);
  } else if (level === 40 && pattern.bias === 'bearish') {
    notes.push(`الگوی نزولی در سطح اشباع فروش — با سیگنال اصلی هم‌جهت نیست، صبر کنید`);
  } else if (pattern.bias === 'neutral') {
    notes.push(`الگوی خنثی (${pattern.labelFa}) — منتظر الگوی قطعی باشید`);
  } else {
    notes.push(`منتظر الگوی تأییدیه در M5`);
  }

  // Risk management
  // Stop loss: just beyond last swing high/low (within current zone period)
  // For SELL: SL above last swing high; TP below recent swing low
  // For BUY: SL below last swing low; TP above recent swing high
  const lookback = Math.min(features.zoneEnterIdx, 30);
  const slice = candles.slice(-lookback);
  const swingHigh = Math.max(...slice.map(c => c.high));
  const swingLow = Math.min(...slice.map(c => c.low));

  let sl = entryPrice;
  let tp = entryPrice;
  const riskPct = 0.4; // 0.4% risk
  if (direction === 'SELL') {
    sl = Math.max(swingHigh, entryPrice * (1 + riskPct / 100));
    const risk = sl - entryPrice;
    tp = entryPrice - risk * 2; // R:R = 1:2
  } else if (direction === 'BUY') {
    sl = Math.min(swingLow, entryPrice * (1 - riskPct / 100));
    const risk = entryPrice - sl;
    tp = entryPrice + risk * 2;
  }

  const risk = Math.abs(entryPrice - sl);
  const reward = Math.abs(tp - entryPrice);
  const rr = risk > 0 ? reward / risk : 0;

  return {
    valid,
    direction,
    directionFa: dirFa,
    entryPrice,
    stopLoss: sl,
    takeProfit: tp,
    riskRewardRatio: rr,
    confidence,
    notes,
  };
}
