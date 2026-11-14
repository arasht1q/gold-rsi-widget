'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Bell,
  RefreshCw,
  Target,
  Shield,
  Zap,
  Clock,
  ChevronDown,
  ChevronUp,
  Smartphone,
} from 'lucide-react';
import { InstallGuide } from '@/components/install-guide';

type Prediction = {
  reversal: number;
  divergence: number;
  passThrough: number;
  topCategory: string;
  topFa: string;
  reasons: string[];
};

type ApproachPrediction = Prediction & {
  targetLevel: number;
  currentRsi: number;
  distanceToLevel: number;
  isSimulation: boolean;
};

type ApiResponse = {
  ok: boolean;
  priceSource: string;
  candleSource: string;
  priceSourceDescription: string;
  marketOpen: boolean;
  timestamp: number;
  lastPrice: number;
  lastPriceSource: string;
  tvQuote: {
    name: string;
    description: string;
    close: number;
    change: number | null;
    change_abs: number | null;
    open: number;
    high: number;
    low: number;
    type: string;
    currency: string;
  } | null;
  lastCandleTime: number;
  lastCandleAgeMin: number;
  lastRsi: number;
  rsiPeriod: number;
  timeframe: string;
  level: number;
  nearestDist: number;
  proximity: number;
  status: string;
  statusFa: string;
  features: {
    rsi: number;
    rsiVelocity10: number;
    rsiVelocity5: number;
    candlesInZone: number;
    inZone: boolean;
    zoneLevel: number | null;
    distSMA50: number;
    volRatio5_20: number;
    session: string;
    sessionFa: string;
    trend50Pct: number;
  } | null;
  prediction: Prediction | null;
  approach40: ApproachPrediction | null;
  approach60: ApproachPrediction | null;
  touchFirst: {
    likelyLevel: 40 | 60;
    probability40: number;
    probability60: number;
    distance40: number;
    distance60: number;
    direction: 'up' | 'down' | 'flat';
    reasoning: string;
  } | null;
  importantZones: {
    zones: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
      candleRange: number;
      bodySize: number;
      bodyRatio: number;
    }[];
    insideZones: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
    }[];
    nearestZone: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
    } | null;
    nearestDistance: number | null;
    nearestDirection: 'above' | 'below' | 'inside' | null;
    nearestAbove: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
    } | null;
    nearestBelow: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
    } | null;
    nextTarget: {
      type: 'daily' | 'weekly';
      date: string;
      open: number;
      close: number;
      midpoint: number;
      rangeHigh: number;
      rangeLow: number;
    } | null;
    nextTargetDistance: number | null;
    nextTargetDirection: 'up' | 'down' | 'flat' | null;
    currentPrice: number;
  } | null;
  prevDay: {
    date: string;
    sessions: {
      key: string;
      label: string;
      startHourUTC: number;
      endHourUTC: number;
      open: number | null;
      close: number | null;
      high: number | null;
      low: number | null;
      candleCount: number;
      changePct: number | null;
    }[];
    dayHigh: number;
    dayLow: number;
    dayOpen: number;
    dayClose: number;
    lastM5Candle: {
      time: number;
      open: number;
      close: number;
      high: number;
      low: number;
    } | null;
  } | null;
  todayFirstM5: {
    time: number;
    open: number;
    close: number;
    high: number;
    low: number;
  } | null;
  proximityToPrevHigh: number | null;
  proximityToPrevLow: number | null;
  positionInRange: number | null;
  pattern: {
    pattern: string;
    label: string;
    labelFa: string;
    bias: string;
    strength: number;
  };
  ticket: {
    valid: boolean;
    direction: string | null;
    directionFa: string;
    entryPrice: number;
    stopLoss: number;
    takeProfit: number;
    riskRewardRatio: number;
    confidence: number;
    notes: string[];
  };
  recentCandles: {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    rsi: number | null;
  }[];
  recentM5: {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    isUp: boolean;
  }[];
  sma50Last: number | null;
  sma200Last: number | null;
};

// Pastel palette + dark gray bars
const PALETTE = {
  // Category accents (soft pastel colors — more colorful than gray, still gentle)
  reversal: {
    text: '#5b8c5a',
    bgSoft: '#e8f4e8',
    bgBar: '#9ec99e',  // soft sage green
    border: '#c3e6c3',
  },
  divergence: {
    text: '#c08a5a',
    bgSoft: '#fdf3e7',
    bgBar: '#f0b870',  // soft peach
    border: '#f0d8b5',
  },
  passThrough: {
    text: '#b56b6b',
    bgSoft: '#fce8e8',
    bgBar: '#e89090',  // soft coral
    border: '#f0c8c8',
  },
  // Level-specific pastel accents
  level40: {
    text: '#5a7d9c',
    bgSoft: '#e8f0f8',
    border: '#c8dcef',
  },
  level60: {
    text: '#9c7a5a',
    bgSoft: '#f8ede0',
    border: '#e8d5b8',
  },
};

const DARK_GRAY = '#44403c';      // stone-700 — for bars
const DARK_GRAY_SOFT = '#a8a29e'; // stone-400 — for soft bars
const BG_LIGHT = '#fafaf9';       // stone-50 — very light gray
const BG_LIGHTER = '#f5f5f4';     // stone-100
const CARD_BG = '#ffffff';
const BORDER_LIGHT = '#e7e5e4';   // stone-200

export default function Home() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [showInstall, setShowInstall] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch('/api/gold', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setLastUpdate(new Date());
    } catch (e: any) {
      setError(e?.message ?? 'خطا در دریافت داده');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);

  const alertLevel = data?.status === 'IN_ZONE' ? 'critical'
                    : data?.status === 'APPROACHING' ? 'high'
                    : data?.status === 'WATCH' ? 'medium'
                    : 'low';

  // For each level, get the right prediction: actual if in that zone, otherwise approach
  const level40Pred = data?.features?.inZone && data.features.zoneLevel === 40
    ? { ...(data.prediction as Prediction), targetLevel: 40, currentRsi: data.features.rsi, distanceToLevel: 0, isSimulation: false }
    : data?.approach40;
  const level60Pred = data?.features?.inZone && data.features.zoneLevel === 60
    ? { ...(data.prediction as Prediction), targetLevel: 60, currentRsi: data.features.rsi, distanceToLevel: 0, isSimulation: false }
    : data?.approach60;

  return (
    <div dir="rtl" className="min-h-screen text-stone-700"
         style={{
           fontFamily: 'system-ui, -apple-system, "Segoe UI", Tahoma, sans-serif',
           background: `linear-gradient(180deg, ${BG_LIGHT} 0%, ${BG_LIGHTER} 100%)`,
         }}>
      <div className="max-w-md mx-auto p-4 space-y-3 pb-12">

        {/* Header */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
                 style={{ background: PALETTE.level60.bgSoft, border: `1px solid ${PALETTE.level60.border}` }}>
              <Activity className="w-5 h-5" style={{ color: PALETTE.level60.text }} />
            </div>
            <div>
              <div className="text-sm font-bold text-stone-800">ویجت RSI طلا</div>
              <div className="text-[10px] text-stone-500">M30 · RSI(30) · سطوح ۴۰/۶۰</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <div className="text-[10px] text-stone-500 text-left">
                <div>{lastUpdate.toLocaleTimeString('fa-IR')}</div>
                <div className="text-stone-400">آخرین بروزرسانی</div>
              </div>
            )}
            <Button variant="ghost" size="icon" onClick={fetchData} disabled={loading}
                    className="h-9 w-9 text-stone-500 hover:text-stone-800">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setShowInstall(true)}
                    className="h-9 w-9 text-stone-500 hover:text-stone-800"
                    title="راهنمای نصب روی گوشی">
              <Smartphone className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {showInstall && <InstallGuide onClose={() => setShowInstall(false)} />}

        {/* ====== WIDGET CARD ====== */}
        <Card className="relative overflow-hidden p-4 shadow-sm"
              style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
          <div className="relative">
            {/* Top row: price + status pill */}
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-[10px] text-stone-500 mb-0.5">طلا / اونس (XAUUSD)</div>
                <div className="text-3xl font-bold tabular-nums tracking-tight text-stone-900">
                  ${data?.lastPrice?.toFixed(2) ?? '...'}
                </div>
                {data?.sma50Last && (
                  <div className="text-[10px] text-stone-400 mt-0.5">
                    SMA50: {data.sma50Last.toFixed(2)}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge style={{
                  background: alertLevel === 'critical' ? PALETTE.passThrough.bgSoft :
                              alertLevel === 'high' ? PALETTE.divergence.bgSoft :
                              alertLevel === 'medium' ? PALETTE.level40.bgSoft :
                              BG_LIGHTER,
                  color: alertLevel === 'critical' ? PALETTE.passThrough.text :
                         alertLevel === 'high' ? PALETTE.divergence.text :
                         alertLevel === 'medium' ? PALETTE.level40.text :
                         '#78716c',
                  border: `1px solid ${
                    alertLevel === 'critical' ? PALETTE.passThrough.border :
                    alertLevel === 'high' ? PALETTE.divergence.border :
                    alertLevel === 'medium' ? PALETTE.level40.border :
                    BORDER_LIGHT
                  }`,
                }}>
                  {data?.statusFa ?? '...'}
                </Badge>
                {data?.features?.sessionFa && (
                  <div className="text-[10px] text-stone-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {data.features.sessionFa}
                  </div>
                )}
              </div>
            </div>

            {/* Source badge + OHLC */}
            {data?.priceSource && (
              <div className="space-y-1.5 mb-3">
                <div className="flex items-center justify-between text-[9px]">
                  <Badge variant="outline" className="text-[9px] py-0 px-1.5"
                         style={{
                           borderColor: data.marketOpen ? PALETTE.reversal.border : BORDER_LIGHT,
                           color: data.marketOpen ? PALETTE.reversal.text : '#a8a29e',
                           background: data.marketOpen ? PALETTE.reversal.bgSoft : BG_LIGHTER,
                         }}>
                    <span className={`w-1.5 h-1.5 rounded-full ml-1 ${
                      data.marketOpen ? 'animate-pulse' : ''
                    }`} style={{
                      background: data.marketOpen ? PALETTE.reversal.text : '#a8a29e',
                    }} />
                    {data.marketOpen ? 'بازار باز' : 'بازار بسته'}
                  </Badge>
                  <span className="text-stone-400" title={data.priceSourceDescription}>
                    قیمت: {data.tvQuote ? 'TradingView TVC:GOLD' : data.priceSource.startsWith('GC=F') ? 'Yahoo GC=F' : 'Binance PAXG'}
                  </span>
                </div>
                {data?.tvQuote && (
                  <div className="grid grid-cols-4 gap-1 text-[9px]">
                    <div className="rounded p-1 text-center" style={{ background: BG_LIGHTER }}>
                      <div className="text-stone-400">Open</div>
                      <div className="font-bold text-stone-700 tabular-nums">{data.tvQuote.open.toFixed(2)}</div>
                    </div>
                    <div className="rounded p-1 text-center" style={{ background: PALETTE.reversal.bgSoft }}>
                      <div className="text-stone-400">High</div>
                      <div className="font-bold tabular-nums" style={{ color: PALETTE.reversal.text }}>{data.tvQuote.high.toFixed(2)}</div>
                    </div>
                    <div className="rounded p-1 text-center" style={{ background: PALETTE.passThrough.bgSoft }}>
                      <div className="text-stone-400">Low</div>
                      <div className="font-bold tabular-nums" style={{ color: PALETTE.passThrough.text }}>{data.tvQuote.low.toFixed(2)}</div>
                    </div>
                    <div className="rounded p-1 text-center"
                         style={{
                           background: (data.tvQuote.change ?? 0) >= 0 ? PALETTE.reversal.bgSoft : PALETTE.passThrough.bgSoft
                         }}>
                      <div className="text-stone-400">Change</div>
                      <div className="font-bold tabular-nums"
                           style={{ color: (data.tvQuote.change ?? 0) >= 0 ? PALETTE.reversal.text : PALETTE.passThrough.text }}>
                        {(data.tvQuote.change ?? 0) >= 0 ? '+' : ''}{(data.tvQuote.change ?? 0).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between text-[9px] text-stone-400 pt-0.5">
                  <span>RSI از: </span>
                  <span>{data.candleSource || 'Yahoo GC=F'}</span>
                </div>
              </div>
            )}

            {/* RSI gauge — dark gray fill, pastel zone bands */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px] text-stone-500">
                <span>RSI(30)</span>
                <span className="font-bold text-base text-stone-800 tabular-nums">
                  {data?.lastRsi?.toFixed(2) ?? '...'}
                </span>
              </div>
              <div className="relative h-3 rounded-full overflow-hidden" style={{ background: BG_LIGHTER }}>
                {/* zone bands — pastel */}
                <div className="absolute top-0 bottom-0"
                     style={{ left: '39%', width: '2%', background: PALETTE.level40.bgSoft }} />
                <div className="absolute top-0 bottom-0"
                     style={{ left: '59%', width: '2%', background: PALETTE.level60.bgSoft }} />
                {/* fill — dark gray */}
                <div
                  className="h-full transition-all"
                  style={{
                    width: `${Math.min(100, Math.max(0, data?.lastRsi ?? 0))}%`,
                    background: DARK_GRAY,
                  }}
                />
                {/* markers at 40/60 */}
                <div className="absolute top-0 bottom-0 w-px bg-stone-400" style={{ left: '40%' }} />
                <div className="absolute top-0 bottom-0 w-px bg-stone-400" style={{ left: '60%' }} />
              </div>
              <div className="flex justify-between text-[9px] text-stone-400">
                <span>۰</span>
                <span style={{ color: PALETTE.level40.text }}>۴۰</span>
                <span>۵۰</span>
                <span style={{ color: PALETTE.level60.text }}>۶۰</span>
                <span>۱۰۰</span>
              </div>
            </div>

            {/* Proximity indicator — dark gray bar */}
            {data && !data.features?.inZone && data.proximity > 0.1 && (
              <div className="mt-3 p-2 rounded-lg" style={{ background: BG_LIGHTER, border: `1px solid ${BORDER_LIGHT}` }}>
                <div className="flex items-center justify-between text-[10px] mb-1">
                  <span className="text-stone-500 flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    نزدیکی به سطح {data.level}
                  </span>
                  <span className="font-bold" style={{ color: PALETTE.divergence.text }}>
                    {data.nearestDist.toFixed(2)} واحد فاصله
                  </span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background: BORDER_LIGHT }}>
                  <div className="h-full transition-all"
                       style={{ width: `${data.proximity * 100}%`, background: DARK_GRAY }} />
                </div>
              </div>
            )}

            {/* In-zone info — pastel badge */}
            {data?.features?.inZone && data.features.zoneLevel && (
              <div className="mt-3 p-2 rounded-lg"
                   style={{
                     background: PALETTE.divergence.bgSoft,
                     border: `1px solid ${PALETTE.divergence.border}`,
                   }}>
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1 font-medium" style={{ color: PALETTE.divergence.text }}>
                    <Bell className="w-3 h-3" />
                    وارد زون {data.features.zoneLevel} شد
                  </span>
                  <span className="font-bold" style={{ color: PALETTE.divergence.text }}>
                    {data.features.candlesInZone} کندل در زون
                  </span>
                </div>
              </div>
            )}

            {/* Market closed note */}
            {data && !data.marketOpen && (
              <div className="mt-2 p-2 rounded-lg" style={{ background: BG_LIGHTER, border: `1px solid ${BORDER_LIGHT}` }}>
                <div className="text-[10px] text-stone-500 flex items-start gap-1.5">
                  <Clock className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>
                    بازار طلا شنبه‌ها تعطیل است. آخرین کندل: {data.lastCandleAgeMin > 1440
                      ? `${Math.floor(data.lastCandleAgeMin / 1440)} روز پیش`
                      : `${Math.floor(data.lastCandleAgeMin / 60)} ساعت پیش`}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* ====== COMBINED PREDICTION CARD (level 40 + 60 in one) ====== */}
        {data?.touchFirst && level40Pred && level60Pred && (
          <Card className="p-4 shadow-sm"
                style={{
                  borderColor: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.border : PALETTE.level40.border,
                  borderWidth: 1,
                  background: `linear-gradient(180deg, ${
                    data.touchFirst.likelyLevel === 60 ? PALETTE.level60.bgSoft : PALETTE.level40.bgSoft
                  } 0%, ${CARD_BG} 70%)`,
                }}>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                   style={{
                     background: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.bgSoft : PALETTE.level40.bgSoft,
                     border: `1px solid ${
                       data.touchFirst.likelyLevel === 60 ? PALETTE.level60.border : PALETTE.level40.border
                     }`,
                   }}>
                <Zap className="w-4 h-4"
                     style={{ color: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.text : PALETTE.level40.text }} />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold text-stone-800">پیش‌بینی واکنش بازار</div>
                <div className="text-[10px] text-stone-500">بر اساس آمار ۲ سال گذشته (۱۳۲۸ رویداد)</div>
              </div>
            </div>

            {/* Which level is more likely */}
            <div className="mb-3 p-2.5 rounded-lg"
                 style={{
                   background: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.bgSoft : PALETTE.level40.bgSoft,
                   border: `1px solid ${
                     data.touchFirst.likelyLevel === 60 ? PALETTE.level60.border : PALETTE.level40.border
                   }`,
                 }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold text-stone-700">سطح محتمل‌تر برای برخورد:</span>
                <Badge style={{
                  background: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.text : PALETTE.level40.text,
                  color: 'white',
                }}>
                  سطح {data.touchFirst.likelyLevel}
                </Badge>
              </div>
              {/* Probability bars for touching each level first */}
              <div className="space-y-1.5">
                <div>
                  <div className="flex items-center justify-between text-[10px] mb-0.5">
                    <span className="text-stone-600">برخورد به ۴۰ اول</span>
                    <span className="font-bold tabular-nums"
                          style={{ color: PALETTE.level40.text }}>
                      {(data.touchFirst.probability40 * 100).toFixed(0)}٪
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: BORDER_LIGHT }}>
                    <div className="h-full transition-all"
                         style={{
                           width: `${data.touchFirst.probability40 * 100}%`,
                           background: PALETTE.level40.bgBar || PALETTE.level40.text,
                         }} />
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between text-[10px] mb-0.5">
                    <span className="text-stone-600">برخورد به ۶۰ اول</span>
                    <span className="font-bold tabular-nums"
                          style={{ color: PALETTE.level60.text }}>
                      {(data.touchFirst.probability60 * 100).toFixed(0)}٪
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full overflow-hidden" style={{ background: BORDER_LIGHT }}>
                    <div className="h-full transition-all"
                         style={{
                           width: `${data.touchFirst.probability60 * 100}%`,
                           background: PALETTE.level60.bgBar || PALETTE.level60.text,
                         }} />
                  </div>
                </div>
              </div>
              <div className="text-[10px] text-stone-600 mt-2 flex items-start gap-1">
                <span style={{ color: PALETTE.divergence.text }}>→</span>
                <span>{data.touchFirst.reasoning}</span>
              </div>
              <div className="flex items-center justify-between text-[9px] text-stone-500 mt-1">
                <span>فاصله تا ۴۰: {data.touchFirst.distance40.toFixed(1)} واحد</span>
                <span>فاصله تا ۶۰: {data.touchFirst.distance60.toFixed(1)} واحد</span>
              </div>
            </div>

            {/* Prediction for likely level (prominent) */}
            <div className="mb-2">
              <div className="text-[10px] font-bold text-stone-600 mb-1.5">
                پیش‌بینی وقتی به سطح {data.touchFirst.likelyLevel} برسد:
              </div>
              <div className="space-y-2">
                <ProbBar
                  label="برگشت (تک‌برخورد)"
                  value={data.touchFirst.likelyLevel === 40 ? level40Pred.reversal : level60Pred.reversal}
                  palette={PALETTE.reversal}
                  icon={<TrendingUp className="w-3 h-3" />}
                />
                <ProbBar
                  label="واگرایی"
                  value={data.touchFirst.likelyLevel === 40 ? level40Pred.divergence : level60Pred.divergence}
                  palette={PALETTE.divergence}
                  icon={<Activity className="w-3 h-3" />}
                />
                <ProbBar
                  label="گذشتن از سطح"
                  value={data.touchFirst.likelyLevel === 40 ? level40Pred.passThrough : level60Pred.passThrough}
                  palette={PALETTE.passThrough}
                  icon={<TrendingDown className="w-3 h-3" />}
                />
              </div>
            </div>

            <Separator className="my-2" style={{ background: BORDER_LIGHT }} />

            {/* Prediction for other level (compact) */}
            <div className="text-[10px] text-stone-500 mb-1">
              پیش‌بینی سطح دیگر ({data.touchFirst.likelyLevel === 40 ? 60 : 40}):
            </div>
            <div className="grid grid-cols-3 gap-1 text-[9px]">
              <div className="rounded p-1 text-center" style={{ background: PALETTE.reversal.bgSoft }}>
                <div className="text-stone-500">برگشت</div>
                <div className="font-bold" style={{ color: PALETTE.reversal.text }}>
                  {((data.touchFirst.likelyLevel === 40 ? level60Pred.reversal : level40Pred.reversal) * 100).toFixed(0)}٪
                </div>
              </div>
              <div className="rounded p-1 text-center" style={{ background: PALETTE.divergence.bgSoft }}>
                <div className="text-stone-500">واگرایی</div>
                <div className="font-bold" style={{ color: PALETTE.divergence.text }}>
                  {((data.touchFirst.likelyLevel === 40 ? level60Pred.divergence : level40Pred.divergence) * 100).toFixed(0)}٪
                </div>
              </div>
              <div className="rounded p-1 text-center" style={{ background: PALETTE.passThrough.bgSoft }}>
                <div className="text-stone-500">گذشتن</div>
                <div className="font-bold" style={{ color: PALETTE.passThrough.text }}>
                  {((data.touchFirst.likelyLevel === 40 ? level60Pred.passThrough : level40Pred.passThrough) * 100).toFixed(0)}٪
                </div>
              </div>
            </div>

            {/* Reasons for likely level */}
            <div className="mt-3 space-y-1">
              <div className="text-[10px] font-bold text-stone-500 mb-1">
                دلایل پیش‌بینی (سطح {data.touchFirst.likelyLevel}):
              </div>
              {(data.touchFirst.likelyLevel === 40 ? level40Pred.reasons : level60Pred.reasons).slice(0, 3).map((r, i) => (
                <div key={i} className="text-[11px] text-stone-700 flex items-start gap-1.5">
                  <span className="mt-0.5"
                        style={{ color: data.touchFirst.likelyLevel === 60 ? PALETTE.level60.text : PALETTE.level40.text }}>•</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* ====== IMPORTANT ZONES (Doji-based) ====== */}
        {data?.importantZones && data.importantZones.zones.length > 0 && (() => {
          const iz = data.importantZones;
          const insideCount = iz.insideZones.length;
          // Group zones: near (<= 2%) and far (> 2%)
          const NEAR_THRESHOLD = 2.0;
          const nearZones = iz.zones.filter(z => {
            const distPct = (Math.abs(z.midpoint - iz.currentPrice) / iz.currentPrice) * 100;
            return distPct <= NEAR_THRESHOLD && !iz.insideZones.some(i => i.date === z.date && i.type === z.type);
          });
          const farZones = iz.zones.filter(z => {
            const distPct = (Math.abs(z.midpoint - iz.currentPrice) / iz.currentPrice) * 100;
            return distPct > NEAR_THRESHOLD && !iz.insideZones.some(i => i.date === z.date && i.type === z.type);
          });

          return (
            <Card className="p-4 shadow-sm"
                  style={{
                    borderColor: insideCount > 0 ? PALETTE.divergence.border : BORDER_LIGHT,
                    borderWidth: 1,
                    background: insideCount > 0
                      ? `linear-gradient(180deg, ${PALETTE.divergence.bgSoft} 0%, ${CARD_BG} 70%)`
                      : CARD_BG,
                  }}>
              {/* Header */}
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                     style={{
                       background: insideCount > 0 ? PALETTE.divergence.bgSoft : PALETTE.level60.bgSoft,
                       border: `1px solid ${insideCount > 0 ? PALETTE.divergence.border : PALETTE.level60.border}`,
                     }}>
                  <Target className="w-4 h-4"
                          style={{ color: insideCount > 0 ? PALETTE.divergence.text : PALETTE.level60.text }} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold text-stone-800">زون‌های مهم (دوجی)</div>
                  <div className="text-[10px] text-stone-500">روزانه و هفتگی — Open/Close به‌عنوان زون</div>
                </div>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-3 mb-3 text-[9px]">
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded" style={{ background: '#f5b87a' }} />
                  <span className="text-stone-600">هفتگی</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded" style={{ background: '#c8c8c8' }} />
                  <span className="text-stone-600">روزانه</span>
                </div>
                <div className="flex items-center gap-1 mr-auto">
                  <span className="text-stone-400">۱ pip = $۰.۱۰</span>
                </div>
              </div>

              {/* Inside zone alert */}
              {insideCount > 0 && (
                <div className="mb-3 p-2.5 rounded-lg"
                     style={{
                       background: PALETTE.divergence.bgSoft,
                       border: `1px solid ${PALETTE.divergence.border}`,
                     }}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <Bell className="w-3.5 h-3.5 animate-pulse" style={{ color: PALETTE.divergence.text }} />
                    <span className="font-bold text-xs" style={{ color: PALETTE.divergence.text }}>
                      داخل زون مهم هستیم!
                    </span>
                  </div>
                  {iz.insideZones.map((z, i) => {
                    const isWeekly = z.type === 'weekly';
                    return (
                      <div key={i} className="text-[10px] text-stone-700 mb-1 flex items-center gap-1">
                        <span className="w-2 h-2 rounded" style={{ background: isWeekly ? '#f5b87a' : '#c8c8c8' }} />
                        <span className="text-stone-600">{isWeekly ? 'هفتگی' : 'روزانه'}</span>
                        <span>{new Date(z.date + 'T00:00:00Z').toLocaleDateString('fa-IR', { timeZone: 'UTC' })}</span>
                        <span className="font-bold tabular-nums mr-auto">${z.midpoint.toFixed(2)}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Next target (in direction of movement) */}
              {iz.nextTarget && (
                <div className="mb-3 p-2.5 rounded-lg"
                     style={{
                       background: iz.nextTargetDirection === 'up' ? PALETTE.reversal.bgSoft : PALETTE.passThrough.bgSoft,
                       border: `1px solid ${
                         iz.nextTargetDirection === 'up' ? PALETTE.reversal.border : PALETTE.passThrough.border
                       }`,
                     }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold" style={{
                      color: iz.nextTargetDirection === 'up' ? PALETTE.reversal.text : PALETTE.passThrough.text,
                    }}>
                      زون هدف ({iz.nextTargetDirection === 'up' ? '↑ صعودی' : '↓ نزولی'}):
                    </span>
                    <span className="w-2 h-2 rounded"
                          style={{ background: iz.nextTarget.type === 'weekly' ? '#f5b87a' : '#c8c8c8' }} />
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <div>
                      <span className="text-stone-600">{iz.nextTarget.type === 'weekly' ? 'هفتگی' : 'روزانه'}</span>
                      <span className="text-stone-400 mr-1">
                        {new Date(iz.nextTarget.date + 'T00:00:00Z').toLocaleDateString('fa-IR', {
                          month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
                        })}
                      </span>
                    </div>
                    <div className="font-bold tabular-nums text-stone-800">
                      ${iz.nextTarget.midpoint.toFixed(2)}
                    </div>
                  </div>
                  {/* Distance in 3 formats */}
                  <div className="grid grid-cols-3 gap-1 mt-2 text-[9px]">
                    {(() => {
                      const diff = Math.abs(iz.nextTarget.midpoint - iz.currentPrice);
                      const pips = diff * 10;
                      const points = diff;
                      const pct = iz.nextTargetDistance ?? 0;
                      return (
                        <>
                          <div className="rounded p-1 text-center" style={{ background: CARD_BG }}>
                            <div className="text-stone-400">پوینت</div>
                            <div className="font-bold tabular-nums text-stone-700">{points.toFixed(1)}</div>
                          </div>
                          <div className="rounded p-1 text-center" style={{ background: CARD_BG }}>
                            <div className="text-stone-400">پip</div>
                            <div className="font-bold tabular-nums text-stone-700">{pips.toFixed(0)}</div>
                          </div>
                          <div className="rounded p-1 text-center" style={{ background: CARD_BG }}>
                            <div className="text-stone-400">٪</div>
                            <div className="font-bold tabular-nums" style={{
                              color: iz.nextTargetDirection === 'up' ? PALETTE.reversal.text : PALETTE.passThrough.text,
                            }}>{pct.toFixed(2)}٪</div>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Near zones group */}
              {nearZones.length > 0 && (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="text-[10px] font-bold text-stone-700 flex items-center gap-1">
                      <span className="w-1 h-3 rounded" style={{ background: PALETTE.divergence.text }} />
                      زون‌های نزدیک (≤ ۲٪)
                    </div>
                    <span className="text-[9px] text-stone-400">{nearZones.length} زون</span>
                  </div>
                  <div className="space-y-1">
                    {nearZones.map((z, i) => (
                      <ZoneRow key={`n-${i}`} z={z} iz={iz} />
                    ))}
                  </div>
                </div>
              )}

              {/* Far zones group */}
              {farZones.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="text-[10px] font-bold text-stone-500 flex items-center gap-1">
                      <span className="w-1 h-3 rounded bg-stone-300" />
                      زون‌های بعدی ({'>'} ۲٪)
                    </div>
                    <span className="text-[9px] text-stone-400">{farZones.length} زون</span>
                  </div>
                  <div className="space-y-1">
                    {farZones.map((z, i) => (
                      <ZoneRow key={`f-${i}`} z={z} iz={iz} />
                    ))}
                  </div>
                </div>
              )}
            </Card>
          );
        })()}

        {/* ====== PREVIOUS DAY ANALYSIS ====== */}
        {data?.prevDay && (
          <Card className="p-4 shadow-sm" style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                     style={{ background: PALETTE.level40.bgSoft, border: `1px solid ${PALETTE.level40.border}` }}>
                  <Clock className="w-4 h-4" style={{ color: PALETTE.level40.text }} />
                </div>
                <div>
                  <div className="text-sm font-bold text-stone-800">تحلیل روز قبل</div>
                  <div className="text-[10px] text-stone-500">
                    {new Date(data.prevDay.date + 'T00:00:00Z').toLocaleDateString('fa-IR', {
                      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                      timeZone: 'UTC',
                    })}
                  </div>
                </div>
              </div>
            </div>

            {/* Sessions table */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-bold text-stone-500 mb-1">سشن‌های معاملاتی (UTC):</div>
              {data.prevDay.sessions.map((s, i) => (
                <div key={i} className="rounded-lg p-2"
                     style={{ background: BG_LIGHTER, border: `1px solid ${BORDER_LIGHT}` }}>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="font-bold text-stone-700">{s.label}</span>
                    <span className="text-[9px] text-stone-400">
                      {String(s.startHourUTC).padStart(2,'0')}:00 - {String(s.endHourUTC).padStart(2,'0')}:00 UTC
                    </span>
                  </div>
                  {s.open !== null && s.close !== null ? (
                    <>
                      <div className="grid grid-cols-2 gap-2 text-[10px]">
                        <div className="flex items-center justify-between">
                          <span className="text-stone-500">Open:</span>
                          <span className="font-bold text-stone-700 tabular-nums">${s.open.toFixed(2)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-stone-500">Close:</span>
                          <span className="font-bold text-stone-700 tabular-nums">${s.close.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[10px]">
                        <span className="text-stone-500">تغییر سشن:</span>
                        <span className="font-bold tabular-nums"
                              style={{ color: (s.changePct ?? 0) >= 0 ? PALETTE.reversal.text : PALETTE.passThrough.text }}>
                          {(s.changePct ?? 0) >= 0 ? '+' : ''}{(s.changePct ?? 0).toFixed(2)}٪
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="text-[10px] text-stone-400 text-center py-1">داده‌ای برای این سشن موجود نیست</div>
                  )}
                </div>
              ))}
            </div>

            {/* Day High/Low with live proximity */}
            <div className="mt-3 p-2 rounded-lg"
                 style={{ background: PALETTE.divergence.bgSoft, border: `1px solid ${PALETTE.divergence.border}` }}>
              <div className="text-[10px] font-bold mb-2" style={{ color: PALETTE.divergence.text }}>
                سقف و کف روز قبل:
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] mb-2">
                <div className="rounded p-1.5 text-center"
                     style={{ background: CARD_BG, border: `1px solid ${PALETTE.reversal.border}` }}>
                  <div className="text-stone-500">سقف (High)</div>
                  <div className="font-bold tabular-nums" style={{ color: PALETTE.reversal.text }}>
                    ${data.prevDay.dayHigh.toFixed(2)}
                  </div>
                </div>
                <div className="rounded p-1.5 text-center"
                     style={{ background: CARD_BG, border: `1px solid ${PALETTE.passThrough.border}` }}>
                  <div className="text-stone-500">کف (Low)</div>
                  <div className="font-bold tabular-nums" style={{ color: PALETTE.passThrough.text }}>
                    ${data.prevDay.dayLow.toFixed(2)}
                  </div>
                </div>
              </div>
              {/* Position in range */}
              {data.positionInRange !== null && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-[10px] mb-1">
                    <span className="text-stone-600">موقعیت قیمت لایو در بازه روز قبل:</span>
                    <span className="font-bold" style={{ color: PALETTE.divergence.text }}>
                      {(data.positionInRange * 100).toFixed(0)}٪
                    </span>
                  </div>
                  {/* Position bar — from low (left) to high (right) */}
                  <div className="relative h-2.5 rounded-full overflow-hidden"
                       style={{ background: `linear-gradient(90deg, ${PALETTE.passThrough.bgBar}, ${BORDER_LIGHT}, ${PALETTE.reversal.bgBar})` }}>
                    {/* Marker for current price */}
                    <div className="absolute top-0 bottom-0 w-1 bg-stone-800"
                         style={{ left: `calc(${data.positionInRange * 100}% - 2px)` }} />
                  </div>
                  <div className="flex justify-between text-[9px] mt-0.5">
                    <span style={{ color: PALETTE.passThrough.text }}>کف</span>
                    <span className="text-stone-400">میانه</span>
                    <span style={{ color: PALETTE.reversal.text }}>سقف</span>
                  </div>
                </div>
              )}
              {/* Proximity percentages */}
              {(data.proximityToPrevHigh !== null || data.proximityToPrevLow !== null) && (
                <div className="grid grid-cols-2 gap-2 mt-2 text-[10px]">
                  {data.proximityToPrevHigh !== null && (
                    <div className="flex items-center justify-between rounded p-1"
                         style={{ background: CARD_BG }}>
                      <span className="text-stone-500">فاصله تا سقف:</span>
                      <span className="font-bold tabular-nums" style={{ color: PALETTE.reversal.text }}>
                        {data.proximityToPrevHigh.toFixed(2)}٪
                      </span>
                    </div>
                  )}
                  {data.proximityToPrevLow !== null && (
                    <div className="flex items-center justify-between rounded p-1"
                         style={{ background: CARD_BG }}>
                      <span className="text-stone-500">فاصله تا کف:</span>
                      <span className="font-bold tabular-nums" style={{ color: PALETTE.passThrough.text }}>
                        {data.proximityToPrevLow.toFixed(2)}٪
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Last M5 of previous day + First M5 of today */}
            <div className="mt-3 grid grid-cols-2 gap-2">
              {data.prevDay.lastM5Candle && (
                <div className="rounded-lg p-2"
                     style={{ background: BG_LIGHTER, border: `1px solid ${BORDER_LIGHT}` }}>
                  <div className="text-[9px] text-stone-500 mb-1">آخرین کندل M5 روز قبل</div>
                  <div className="text-[9px] text-stone-400 mb-1">
                    {new Date(data.prevDay.lastM5Candle.time).toLocaleTimeString('fa-IR', {
                      hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
                    })} UTC
                  </div>
                  <div className="space-y-0.5 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-stone-500">O:</span>
                      <span className="font-bold text-stone-700 tabular-nums">${data.prevDay.lastM5Candle.open.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">C:</span>
                      <span className="font-bold text-stone-700 tabular-nums">${data.prevDay.lastM5Candle.close.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              )}
              {data.todayFirstM5 && (
                <div className="rounded-lg p-2"
                     style={{ background: PALETTE.level40.bgSoft, border: `1px solid ${PALETTE.level40.border}` }}>
                  <div className="text-[9px] text-stone-500 mb-1">اولین کندل M5 امروز</div>
                  <div className="text-[9px] text-stone-400 mb-1">
                    {new Date(data.todayFirstM5.time).toLocaleTimeString('fa-IR', {
                      hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
                    })} UTC
                  </div>
                  <div className="space-y-0.5 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-stone-500">O:</span>
                      <span className="font-bold text-stone-700 tabular-nums">${data.todayFirstM5.open.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">C:</span>
                      <span className="font-bold text-stone-700 tabular-nums">${data.todayFirstM5.close.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* ====== PATTERN DETECTION (M5) ====== */}
        <Card className="p-4 shadow-sm" style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                   style={{ background: '#ede9fe' }}>
                <Activity className="w-4 h-4" style={{ color: '#7c6fc4' }} />
              </div>
              <div>
                <div className="text-sm font-bold text-stone-800">الگوی کندلی M5</div>
                <div className="text-[10px] text-stone-500">آخرین کندل‌های ۵ دقیقه</div>
              </div>
            </div>
            <Badge style={{
              background: data?.pattern?.bias === 'bullish' ? '#26a69a' :
                          data?.pattern?.bias === 'bearish' ? '#ef5350' :
                          BG_LIGHTER,
              color: data?.pattern?.bias === 'bullish' || data?.pattern?.bias === 'bearish'
                ? 'white'
                : '#78716c',
              border: `1px solid ${
                data?.pattern?.bias === 'bullish' ? '#26a69a' :
                data?.pattern?.bias === 'bearish' ? '#ef5350' :
                BORDER_LIGHT
              }`,
            }}>
              {data?.pattern?.labelFa ?? '...'}
            </Badge>
          </div>

          {data?.recentM5 && data.recentM5.length > 0 && (
            <div className="flex items-end gap-1.5 h-24 mb-2 px-1">
              {data.recentM5.map((c, i) => {
                const all = data.recentM5!;
                const max = Math.max(...all.map(x => x.high));
                const min = Math.min(...all.map(x => x.low));
                const range = max - min || 1;
                const color = c.isUp ? '#26a69a' : '#ef5350';

                // Wick spans from low to high
                const wickBottomPct = ((c.low - min) / range) * 100;
                const wickHeightPct = ((c.high - c.low) / range) * 100;

                // Body spans from min(open,close) to max(open,close)
                const bodyBottomPct = ((Math.min(c.open, c.close) - min) / range) * 100;
                const bodyHeightPct = (Math.abs(c.close - c.open) / range) * 100;

                return (
                  <div key={i} className="flex-1 relative" style={{ height: '100%' }}>
                    {/* Wick (thin vertical line, full high-low range) */}
                    <div className="absolute left-1/2 -translate-x-1/2"
                         style={{
                           bottom: `${wickBottomPct}%`,
                           height: `${wickHeightPct}%`,
                           width: '1.5px',
                           background: color,
                           opacity: 0.6,
                         }} />
                    {/* Body (rectangle) */}
                    <div
                      className="absolute left-1/2 -translate-x-1/2 rounded-sm"
                      style={{
                        bottom: `${bodyBottomPct}%`,
                        height: `${Math.max(3, bodyHeightPct)}%`,
                        width: '12px',
                        background: color,
                        boxShadow: `0 0 3px ${color}40`,
                      }}
                    />
                  </div>
                );
              })}
            </div>
          )}

          <div className="text-[10px] text-stone-500 text-center">
            {data?.pattern?.bias === 'bullish' && 'الگوی صعودی — مناسب ورود خرید در سطح ۴۰'}
            {data?.pattern?.bias === 'bearish' && 'الگوی نزولی — مناسب ورود فروش در سطح ۶۰'}
            {data?.pattern?.bias === 'neutral' && 'الگوی خنثی — منتظر الگوی قطعی'}
          </div>
        </Card>

        {/* ====== ENTRY TICKET ====== */}
        {data?.ticket && (
          <Card className="p-4 shadow-sm"
                style={{
                  borderColor: data.ticket.valid ? PALETTE.reversal.border : BORDER_LIGHT,
                  borderWidth: 1,
                  background: data.ticket.valid
                    ? `linear-gradient(180deg, ${PALETTE.reversal.bgSoft} 0%, ${CARD_BG} 60%)`
                    : CARD_BG,
                }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                     style={{ background: data.ticket.valid ? PALETTE.reversal.bgSoft : BG_LIGHTER }}>
                  <Target className="w-4 h-4"
                          style={{ color: data.ticket.valid ? PALETTE.reversal.text : '#a8a29e' }} />
                </div>
                <div>
                  <div className="text-sm font-bold text-stone-800">تیکت ورود</div>
                  <div className="text-[10px] text-stone-500">با مدیریت ریسک</div>
                </div>
              </div>
              {data.ticket.valid && data.ticket.direction && (
                <Badge className="text-xs px-3 py-1 text-white"
                       style={{
                         background: data.ticket.direction === 'BUY' ? PALETTE.reversal.text : PALETTE.passThrough.text,
                       }}>
                  {data.ticket.directionFa}
                </Badge>
              )}
            </div>

            {data.ticket.valid ? (
              <>
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <TicketBox label="قیمت ورود" value={`$${data.ticket.entryPrice.toFixed(2)}`} />
                  <TicketBox label="حد ضرر" value={`$${data.ticket.stopLoss.toFixed(2)}`} tone="red" />
                  <TicketBox label="حد سود" value={`$${data.ticket.takeProfit.toFixed(2)}`} tone="green" />
                </div>

                <div className="flex items-center justify-between mb-2 text-xs">
                  <span className="text-stone-500 flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    نسبت ریسک/سود
                  </span>
                  <span className="font-bold" style={{ color: PALETTE.divergence.text }}>
                    1:{data.ticket.riskRewardRatio.toFixed(2)}
                  </span>
                </div>

                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="text-stone-500 flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    اطمینان
                  </span>
                  <span className="font-bold" style={{ color: PALETTE.divergence.text }}>
                    {(data.ticket.confidence * 100).toFixed(0)}٪
                  </span>
                </div>

                {/* Confidence bar — dark gray */}
                <div className="h-1.5 rounded-full overflow-hidden mb-3" style={{ background: BORDER_LIGHT }}>
                  <div className="h-full transition-all"
                       style={{
                         width: `${data.ticket.confidence * 100}%`,
                         background: DARK_GRAY,
                       }}
                  />
                </div>
              </>
            ) : (
              <div className="flex items-start gap-2 p-2 rounded-lg text-xs text-stone-600"
                   style={{ background: BG_LIGHTER }}>
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5"
                               style={{ color: PALETTE.divergence.text }} />
                <div>{data.ticket.notes[0]}</div>
              </div>
            )}

            {data.ticket.notes.length > 0 && (
              <div className="space-y-1 mt-2">
                {data.ticket.notes.slice(data.ticket.valid ? 0 : 1).map((n, i) => (
                  <div key={i} className="text-[10px] text-stone-500 flex items-start gap-1">
                    <span style={{ color: PALETTE.level40.text }}>→</span>
                    <span>{n}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* ====== EXPAND BUTTON ====== */}
        <Button variant="ghost" onClick={() => setExpanded(!expanded)}
                className="w-full text-stone-500 hover:text-stone-800 text-xs">
          {expanded ? (
            <><ChevronUp className="w-4 h-4 ml-1" /> بستن جزئیات</>
          ) : (
            <><ChevronDown className="w-4 h-4 ml-1" /> نمایش جزئیات بیشتر</>
          )}
        </Button>

        {/* ====== EXPANDED DETAILS ====== */}
        {expanded && data && (
          <div className="space-y-3">
            {data.features && (
              <Card className="p-4 shadow-sm" style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
                <div className="text-sm font-bold mb-3 text-stone-800">ویژگی‌های فعلی بازار</div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <FeatureItem label="RSI" value={data.features.rsi.toFixed(2)} />
                  <FeatureItem label="کندل در زون" value={String(data.features.candlesInZone)} />
                  <FeatureItem label="سرعت RSI (۱۰)" value={data.features.rsiVelocity10.toFixed(2)} />
                  <FeatureItem label="سرعت RSI (۵)" value={data.features.rsiVelocity5.toFixed(2)} />
                  <FeatureItem label="نسبت حجم ۵/۲۰" value={data.features.volRatio5_20.toFixed(2)} />
                  <FeatureItem label="فاصله از SMA50٪" value={data.features.distSMA50.toFixed(2)} />
                  <FeatureItem label="روند ۵۰ کندلی" value={`${data.features.trend50Pct.toFixed(2)}٪`} />
                  <FeatureItem label="سشن" value={data.features.sessionFa} />
                </div>
              </Card>
            )}

            <Card className="p-4 shadow-sm" style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
              <div className="text-sm font-bold mb-3 text-stone-800">نمودار قیمت و RSI (۲۴ ساعت اخیر)</div>
              <MiniChart candles={data.recentCandles} />
            </Card>

            <Card className="p-4 shadow-sm" style={{ background: CARD_BG, borderColor: BORDER_LIGHT, borderWidth: 1 }}>
              <div className="text-sm font-bold mb-2 text-stone-800">درباره این ویجت</div>
              <div className="text-[11px] text-stone-600 leading-relaxed space-y-2">
                <p>این ویجت RSI(30) را روی تایم‌فریم M30 طلا پایش می‌کند. منابع داده:</p>
                <ul className="space-y-1 list-disc pr-4">
                  <li><strong className="text-stone-800">قیمت لحظه‌ای:</strong> TradingView TVC:GOLD (طلای اسپات)</li>
                  <li><strong className="text-stone-800">کندل‌های تاریخی M30:</strong> Yahoo Finance GC=F (طلای آتی COMEX)</li>
                  <li><strong className="text-stone-800">Fallback:</strong> Binance PAXG/USDT</li>
                </ul>
                <p>بازار طلای اسپات از یکشنبه ۲۳:۰۰ تا جمعه ۲۲:۰۰ UTC باز است و در شنبه تعطیل است.</p>
                <p>
                  <strong className="text-stone-800">پیش‌بینی‌ها:</strong> همیشه برای هر دو سطح ۴۰ و ۶۰ نشان داده می‌شوند.
                  اگر RSI داخل زون باشد، پیش‌بینی واقعی است؛ در غیر این صورت، پیش‌بینی فرضی است.
                </p>
              </div>
            </Card>
          </div>
        )}

        {error && (
          <Card className="p-3 shadow-sm"
                style={{ borderColor: PALETTE.passThrough.border, background: PALETTE.passThrough.bgSoft }}>
            <div className="text-xs flex items-center gap-2" style={{ color: PALETTE.passThrough.text }}>
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          </Card>
        )}

        <div className="text-center text-[10px] text-stone-400 pt-4">
          داده زنده · به‌روزرسانی هر ۳۰ ثانیه<br/>
          این ابزار سیگنال معاملاتی قطعی نیست — با مدیریت ریسک معامله کنید
        </div>
      </div>
    </div>
  );
}

// =====================================================
// Zone Row component — used for each zone in near/far groups
// =====================================================
function ZoneRow({ z, iz }: {
  z: {
    type: 'daily' | 'weekly';
    date: string;
    open: number;
    close: number;
    midpoint: number;
    rangeHigh: number;
    rangeLow: number;
  };
  iz: {
    currentPrice: number;
    insideZones: { date: string; type: string; midpoint: number }[];
  };
}) {
  const isWeekly = z.type === 'weekly';
  const zoneColor = isWeekly ? '#f5b87a' : '#c8c8c8';  // orange for weekly, gray for daily
  const zoneBg = isWeekly ? '#fef3e7' : '#f5f5f4';
  const zoneBorder = isWeekly ? '#f0d8b5' : '#e0e0e0';

  const diff = Math.abs(z.midpoint - iz.currentPrice);
  const pips = diff * 10;
  const points = diff;
  const distPct = (diff / iz.currentPrice) * 100;
  const isAbove = z.midpoint > iz.currentPrice;
  const isInside = iz.insideZones.some(i => i.date === z.date && i.type === z.type);

  return (
    <div className="rounded p-1.5 flex items-center gap-2"
         style={{
           background: zoneBg,
           border: `1px solid ${zoneBorder}`,
           borderRight: `3px solid ${zoneColor}`,
         }}>
      {/* Type indicator */}
      <div className="flex flex-col items-center" style={{ minWidth: '32px' }}>
        <span className="w-2 h-2 rounded-full" style={{ background: zoneColor }} />
        <span className="text-[8px] text-stone-500 mt-0.5">
          {isWeekly ? 'هفتگی' : 'روزانه'}
        </span>
      </div>

      {/* Date */}
      <div className="text-[9px] text-stone-500" style={{ minWidth: '60px' }}>
        {new Date(z.date + 'T00:00:00Z').toLocaleDateString('fa-IR', {
          month: 'short', day: 'numeric', timeZone: 'UTC',
        })}
      </div>

      {/* Price */}
      <div className="font-bold tabular-nums text-stone-800 text-[11px]" style={{ minWidth: '60px' }}>
        ${z.midpoint.toFixed(2)}
      </div>

      {/* Direction arrow */}
      <div className="text-[10px]" style={{ color: isAbove ? PALETTE.reversal.text : PALETTE.passThrough.text }}>
        {isInside ? '✓' : isAbove ? '↑' : '↓'}
      </div>

      {/* Distance: points/pips/pct */}
      <div className="flex flex-col items-end text-[8px] leading-tight mr-auto">
        <div className="flex items-center gap-1.5">
          <span className="text-stone-400">پوینت:</span>
          <span className="font-bold tabular-nums text-stone-700">{points.toFixed(1)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-stone-400">pip:</span>
          <span className="font-bold tabular-nums text-stone-700">{pips.toFixed(0)}</span>
          <span className="text-stone-400">|</span>
          <span className="font-bold tabular-nums" style={{
            color: isInside ? PALETTE.divergence.text :
                   isAbove ? PALETTE.reversal.text : PALETTE.passThrough.text,
          }}>{distPct.toFixed(2)}٪</span>
        </div>
      </div>
    </div>
  );
}

// =====================================================
// Prediction Card component — used for both levels
// =====================================================
function PredictionCard({ level, prediction, isActual, palette } : {
  level: 40 | 60;
  prediction: ApproachPrediction;
  isActual: boolean;
  palette: { text: string; bgSoft: string; border: string };
}) {
  return (
    <Card className="p-4 shadow-sm"
          style={{
            borderColor: palette.border,
            borderWidth: 1,
            background: `linear-gradient(180deg, ${palette.bgSoft} 0%, ${CARD_BG} 80%)`,
          }}>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
             style={{ background: palette.bgSoft, border: `1px solid ${palette.border}` }}>
          <Zap className="w-4 h-4" style={{ color: palette.text }} />
        </div>
        <div className="flex-1">
          <div className="text-sm font-bold text-stone-800">
            {isActual
              ? `پیش‌بینی واکنش بازار — سطح ${level}`
              : `پیش‌بینی فرضی — سطح ${level}`}
          </div>
          <div className="text-[10px] text-stone-500">
            {isActual
              ? 'بر اساس آمار ۲ سال گذشته (۱۳۲۸ رویداد)'
              : `اگر RSI به سطح ${level} برسد`}
          </div>
        </div>
        <Badge variant="outline" className="text-[10px]"
               style={{ borderColor: palette.border, color: palette.text, background: palette.bgSoft }}>
          محتمل: {prediction.topFa}
        </Badge>
      </div>

      {/* Distance indicator (only for simulations) */}
      {!isActual && (
        <div className="mb-3 p-2 rounded-lg" style={{ background: palette.bgSoft, border: `1px solid ${palette.border}` }}>
          <div className="flex items-center justify-between text-[10px]">
            <span className="flex items-center gap-1" style={{ color: palette.text }}>
              <Target className="w-3 h-3" />
              RSI فعلی: {prediction.currentRsi.toFixed(2)}
            </span>
            <span className="font-bold" style={{ color: palette.text }}>
              {prediction.distanceToLevel.toFixed(2)} واحد تا سطح {level}
            </span>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <ProbBar label="برگشت (تک‌برخورد)" value={prediction.reversal} palette={PALETTE.reversal}
                 icon={<TrendingUp className="w-3 h-3" />} />
        <ProbBar label="واگرایی" value={prediction.divergence} palette={PALETTE.divergence}
                 icon={<Activity className="w-3 h-3" />} />
        <ProbBar label="گذشتن از سطح" value={prediction.passThrough} palette={PALETTE.passThrough}
                 icon={<TrendingDown className="w-3 h-3" />} />
      </div>

      <Separator className="my-3" style={{ background: BORDER_LIGHT }} />

      <div className="space-y-1">
        <div className="text-[10px] font-bold text-stone-500 mb-1">دلایل پیش‌بینی:</div>
        {prediction.reasons.map((r, i) => (
          <div key={i} className="text-[11px] text-stone-700 flex items-start gap-1.5">
            <span className="mt-0.5" style={{ color: palette.text }}>•</span>
            <span>{r}</span>
          </div>
        ))}
      </div>

      {!isActual && (
        <div className="mt-3 p-2 rounded text-[10px] flex items-start gap-1.5"
             style={{ background: palette.bgSoft, color: palette.text, border: `1px solid ${palette.border}` }}>
          <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
          <span>
            این پیش‌بینی فرضی است و فرض می‌کند RSI همین الان به سطح می‌رسد. وقتی واقعاً به سطح برسد
            و چند کندل در زون بماند، احتمالات می‌تواند متفاوت باشد.
          </span>
        </div>
      )}
    </Card>
  );
}

function ProbBar({ label, value, palette, icon }: {
  label: string; value: number;
  palette: { text: string; bgBar: string };
  icon: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className="text-stone-700 flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        <span className="font-bold text-stone-800 tabular-nums">{(value * 100).toFixed(0)}٪</span>
      </div>
      {/* Bar background = light gray, fill = soft pastel color from palette */}
      <div className="h-2 rounded-full overflow-hidden" style={{ background: BORDER_LIGHT }}>
        <div className="h-full transition-all"
             style={{ width: `${value * 100}%`, background: palette.bgBar }} />
      </div>
    </div>
  );
}

function TicketBox({ label, value, tone }: {
  label: string; value: string; tone?: 'red' | 'green';
}) {
  const palette = tone === 'red' ? PALETTE.passThrough : tone === 'green' ? PALETTE.reversal : null;
  return (
    <div className="p-2 rounded-lg"
         style={{
           background: palette ? palette.bgSoft : BG_LIGHTER,
           border: `1px solid ${palette ? palette.border : BORDER_LIGHT}`,
         }}>
      <div className="text-[9px] text-stone-500 mb-0.5">{label}</div>
      <div className="text-xs font-bold tabular-nums"
           style={{ color: palette ? palette.text : '#292524' }}>{value}</div>
    </div>
  );
}

function FeatureItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between p-2 rounded" style={{ background: BG_LIGHTER }}>
      <span className="text-stone-500">{label}</span>
      <span className="font-bold text-stone-800 tabular-nums">{value}</span>
    </div>
  );
}

function MiniChart({ candles }: { candles: any[] }) {
  if (!candles || candles.length === 0) return <div className="text-xs text-stone-500">داده‌ای موجود نیست</div>;

  const prices = candles.map(c => c.close);
  const rsis = candles.map(c => c.rsi).filter((r): r is number => r !== null);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const rangeP = maxP - minP || 1;

  const w = 320;
  const hPrice = 80;
  const hRsi = 40;
  const padX = 0;

  const pricePath = prices.map((p, i) => {
    const x = padX + (i / (prices.length - 1)) * w;
    const y = hPrice - ((p - minP) / rangeP) * hPrice;
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');

  const rsiPath = rsis.length > 0 ? rsis.map((r, i) => {
    const x = padX + (i / (candles.length - 1)) * w;
    const y = hRsi - (r / 100) * hRsi;
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ') : '';

  return (
    <div className="space-y-1">
      <svg viewBox={`0 0 ${w} ${hPrice + hRsi + 10}`} className="w-full" preserveAspectRatio="none">
        {/* Price line — dark gray */}
        <path d={pricePath} stroke={DARK_GRAY} strokeWidth="1.5" fill="none" />
        <g transform={`translate(0, ${hPrice + 10})`}>
          {/* Zone bands — pastel */}
          <rect x="0" y={hRsi - (60 / 100) * hRsi} width={w} height={(2 / 100) * hRsi}
                fill={PALETTE.level60.bgSoft} opacity="0.6" />
          <rect x="0" y={hRsi - (40 / 100) * hRsi} width={w} height={(2 / 100) * hRsi}
                fill={PALETTE.level40.bgSoft} opacity="0.6" />
          <line x1="0" y1={hRsi - (60 / 100) * hRsi} x2={w} y2={hRsi - (60 / 100) * hRsi}
                stroke={PALETTE.level60.text} strokeWidth="0.3" strokeDasharray="2,2" opacity="0.5" />
          <line x1="0" y1={hRsi - (40 / 100) * hRsi} x2={w} y2={hRsi - (40 / 100) * hRsi}
                stroke={PALETTE.level40.text} strokeWidth="0.3" strokeDasharray="2,2" opacity="0.5" />
          {/* RSI line — dark gray */}
          {rsiPath && <path d={rsiPath} stroke={DARK_GRAY_SOFT} strokeWidth="1.2" fill="none" />}
        </g>
      </svg>
      <div className="flex justify-between text-[9px] text-stone-400">
        <span>{new Date(candles[0].time).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}</span>
        <span>قیمت (بالایی) + RSI (پایینی)</span>
        <span>{new Date(candles[candles.length - 1].time).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
    </div>
  );
}
