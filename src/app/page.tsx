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
  prediction: {
    reversal: number;
    divergence: number;
    passThrough: number;
    topCategory: string;
    topFa: string;
    reasons: string[];
  } | null;
  approachPrediction: {
    reversal: number;
    divergence: number;
    passThrough: number;
    topCategory: string;
    topFa: string;
    reasons: string[];
    targetLevel: number;
    currentRsi: number;
    distanceToLevel: number;
    isSimulation: boolean;
  } | null;
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
    const interval = setInterval(fetchData, 30000); // every 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  // Register service worker for PWA
  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // ignore — PWA still works without SW
      });
    }
  }, []);

  // Determine alert level
  const alertLevel = data?.status === 'IN_ZONE' ? 'critical'
                    : data?.status === 'APPROACHING' ? 'high'
                    : data?.status === 'WATCH' ? 'medium'
                    : 'low';

  return (
    <div dir="rtl" className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100"
         style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", Tahoma, sans-serif' }}>
      <div className="max-w-md mx-auto p-4 space-y-3 pb-12">

        {/* Header */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
              <Activity className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <div className="text-sm font-bold">ویجت RSI طلا</div>
              <div className="text-[10px] text-slate-400">M30 · RSI(30) · سطوح ۴۰/۶۰</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {lastUpdate && (
              <div className="text-[10px] text-slate-400 text-left">
                <div>{lastUpdate.toLocaleTimeString('fa-IR')}</div>
                <div className="text-slate-500">آخرین بروزرسانی</div>
              </div>
            )}
            <Button variant="ghost" size="icon" onClick={fetchData} disabled={loading}
                    className="h-9 w-9 text-slate-300 hover:text-amber-400">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => setShowInstall(true)}
                    className="h-9 w-9 text-slate-300 hover:text-amber-400"
                    title="راهنمای نصب روی گوشی">
              <Smartphone className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {showInstall && <InstallGuide onClose={() => setShowInstall(false)} />}

        {/* ====== WIDGET CARD (compact, glanceable) ====== */}
        <Card className="relative overflow-hidden border-slate-800 bg-slate-900/80 backdrop-blur p-4 shadow-2xl">
          {/* Status glow */}
          <div className={`absolute inset-0 opacity-20 ${
            alertLevel === 'critical' ? 'bg-red-500' :
            alertLevel === 'high' ? 'bg-amber-500' :
            alertLevel === 'medium' ? 'bg-blue-500' : 'bg-slate-500'
          }`} />
          <div className="relative">
            {/* Top row: price + status pill */}
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-[10px] text-slate-400 mb-0.5">طلا / اونس (XAUUSD)</div>
                <div className="text-3xl font-bold tabular-nums tracking-tight">
                  ${data?.lastPrice?.toFixed(2) ?? '...'}
                </div>
                {data?.sma50Last && (
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    SMA50: {data.sma50Last.toFixed(2)}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end gap-1">
                <Badge className={`
                  ${alertLevel === 'critical' ? 'bg-red-500/90 text-white animate-pulse' :
                    alertLevel === 'high' ? 'bg-amber-500/90 text-white' :
                    alertLevel === 'medium' ? 'bg-blue-500/80 text-white' :
                    'bg-slate-700 text-slate-200'}`}>
                  {data?.statusFa ?? '...'}
                </Badge>
                {data?.features?.sessionFa && (
                  <div className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {data.features.sessionFa}
                  </div>
                )}
              </div>
            </div>

            {/* Source badge */}
            {data?.priceSource && (
              <div className="space-y-1 mb-2">
                <div className="flex items-center justify-between text-[9px]">
                  <Badge variant="outline" className={`text-[9px] py-0 px-1.5 ${
                    data.marketOpen
                      ? 'border-green-500/40 text-green-300'
                      : 'border-slate-600 text-slate-400'
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ml-1 ${
                      data.marketOpen ? 'bg-green-400 animate-pulse' : 'bg-slate-500'
                    }`} />
                    {data.marketOpen ? 'بازار باز' : 'بازار بسته'}
                  </Badge>
                  <span className="text-slate-500" title={data.priceSourceDescription}>
                    قیمت: {data.tvQuote ? 'TradingView TVC:GOLD' : data.priceSource.startsWith('GC=F') ? 'Yahoo GC=F' : 'Binance PAXG'}
                  </span>
                </div>
                {/* Today's OHLC from TradingView */}
                {data?.tvQuote && (
                  <div className="grid grid-cols-4 gap-1 text-[9px] mt-1">
                    <div className="bg-slate-800/40 rounded p-1 text-center">
                      <div className="text-slate-500">Open</div>
                      <div className="font-bold text-slate-200 tabular-nums">{data.tvQuote.open.toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-800/40 rounded p-1 text-center">
                      <div className="text-slate-500">High</div>
                      <div className="font-bold text-green-300 tabular-nums">{data.tvQuote.high.toFixed(2)}</div>
                    </div>
                    <div className="bg-slate-800/40 rounded p-1 text-center">
                      <div className="text-slate-500">Low</div>
                      <div className="font-bold text-red-300 tabular-nums">{data.tvQuote.low.toFixed(2)}</div>
                    </div>
                    <div className={`bg-slate-800/40 rounded p-1 text-center ${
                      (data.tvQuote.change ?? 0) >= 0 ? 'text-green-300' : 'text-red-300'
                    }`}>
                      <div className="text-slate-500">Change</div>
                      <div className="font-bold tabular-nums">
                        {(data.tvQuote.change ?? 0) >= 0 ? '+' : ''}{(data.tvQuote.change ?? 0).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between text-[9px] text-slate-500 pt-0.5">
                  <span>RSI محاسبه‌شده از: </span>
                  <span>{data.candleSource || 'Yahoo GC=F'}</span>
                </div>
              </div>
            )}

            {/* RSI gauge */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span>RSI(30)</span>
                <span className="font-bold text-base text-slate-100 tabular-nums">
                  {data?.lastRsi?.toFixed(2) ?? '...'}
                </span>
              </div>
              {/* RSI bar with zones */}
              <div className="relative h-3 bg-slate-800 rounded-full overflow-hidden">
                {/* zone bands */}
                <div className="absolute top-0 bottom-0 bg-green-500/30"
                     style={{ left: '39%', width: '2%' }} />
                <div className="absolute top-0 bottom-0 bg-red-500/30"
                     style={{ left: '59%', width: '2%' }} />
                {/* fill */}
                <div
                  className={`h-full transition-all ${
                    (data?.lastRsi ?? 50) > 60 ? 'bg-red-400' :
                    (data?.lastRsi ?? 50) < 40 ? 'bg-green-400' : 'bg-amber-400'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(0, data?.lastRsi ?? 0))}%` }}
                />
                {/* markers at 40/60 */}
                <div className="absolute top-0 bottom-0 w-px bg-slate-500/60" style={{ left: '40%' }} />
                <div className="absolute top-0 bottom-0 w-px bg-slate-500/60" style={{ left: '60%' }} />
              </div>
              <div className="flex justify-between text-[9px] text-slate-500">
                <span>۰</span><span className="text-green-400">۴۰</span>
                <span>۵۰</span><span className="text-red-400">۶۰</span><span>۱۰۰</span>
              </div>
            </div>

            {/* Proximity indicator (only when not in zone) */}
            {data && !data.features?.inZone && data.proximity > 0.1 && (
              <div className="mt-3 p-2 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="flex items-center justify-between text-[10px] mb-1">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Target className="w-3 h-3" />
                    نزدیکی به سطح {data.level}
                  </span>
                  <span className="font-bold text-amber-300">
                    {data.nearestDist.toFixed(2)} واحد فاصله
                  </span>
                </div>
                <Progress value={data.proximity * 100} className="h-1.5 bg-slate-700" />
              </div>
            )}

            {/* In-zone info */}
            {data?.features?.inZone && data.features.zoneLevel && (
              <div className="mt-3 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1 text-amber-300 font-medium">
                    <Bell className="w-3 h-3" />
                    وارد زون {data.features.zoneLevel} شد
                  </span>
                  <span className="text-amber-200 font-bold">
                    {data.features.candlesInZone} کندل در زون
                  </span>
                </div>
              </div>
            )}

            {/* Market closed note */}
            {data && !data.marketOpen && (
              <div className="mt-2 p-2 rounded-lg bg-slate-800/40 border border-slate-700/30">
                <div className="text-[10px] text-slate-400 flex items-start gap-1.5">
                  <Clock className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span>
                    بازار طلا شنبه‌ها تعطیل است. آخرین کندل: {data.lastCandleAgeMin > 1440
                      ? `${Math.floor(data.lastCandleAgeMin / 1440)} روز پیش`
                      : `${Math.floor(data.lastCandleAgeMin / 60)} ساعت پیش`}
                    . داده‌ها از آخرین سشن جمعه است.
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* ====== PREDICTION CARD (when in zone) ====== */}
        {data?.prediction && (
          <Card className="border-amber-500/30 bg-gradient-to-br from-slate-900 to-slate-900/60 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <Zap className="w-4 h-4 text-amber-400" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold">پیش‌بینی واکنش بازار</div>
                <div className="text-[10px] text-slate-400">بر اساس آمار ۲ سال گذشته (۱۳۲۸ رویداد)</div>
              </div>
              <Badge variant="outline" className="border-amber-500/50 text-amber-300 text-[10px]">
                محتمل: {data.prediction.topFa}
              </Badge>
            </div>

            <div className="space-y-2">
              <ProbBar
                label="برگشت (تک‌برخورد)"
                value={data.prediction.reversal}
                color="bg-green-500"
                icon={<TrendingUp className="w-3 h-3" />}
              />
              <ProbBar
                label="واگرایی"
                value={data.prediction.divergence}
                color="bg-orange-500"
                icon={<Activity className="w-3 h-3" />}
              />
              <ProbBar
                label="گذشتن از سطح"
                value={data.prediction.passThrough}
                color="bg-red-500"
                icon={<TrendingDown className="w-3 h-3" />}
              />
            </div>

            <Separator className="my-3 bg-slate-800" />

            <div className="space-y-1">
              <div className="text-[10px] font-bold text-slate-400 mb-1">دلایل پیش‌بینی:</div>
              {data.prediction.reasons.map((r, i) => (
                <div key={i} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                  <span className="text-amber-400 mt-0.5">•</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* ====== APPROACH PREDICTION CARD (when approaching but not in zone) ====== */}
        {!data?.prediction && data?.approachPrediction && (
          <Card className="border-blue-500/30 bg-gradient-to-br from-slate-900 to-slate-900/60 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold">پیش‌بینی فرضی واکنش بازار</div>
                <div className="text-[10px] text-slate-400">اگر RSI به سطح {data.approachPrediction.targetLevel} برسد</div>
              </div>
              <Badge variant="outline" className="border-blue-500/50 text-blue-300 text-[10px]">
                محتمل: {data.approachPrediction.topFa}
              </Badge>
            </div>

            {/* Distance indicator */}
            <div className="mb-3 p-2 rounded-lg bg-blue-500/10 border border-blue-500/30">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-blue-300 flex items-center gap-1">
                  <Target className="w-3 h-3" />
                  RSI فعلی: {data.approachPrediction.currentRsi.toFixed(2)}
                </span>
                <span className="text-blue-200 font-bold">
                  {data.approachPrediction.distanceToLevel.toFixed(2)} واحد تا سطح {data.approachPrediction.targetLevel}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <ProbBar
                label="برگشت (تک‌برخورد)"
                value={data.approachPrediction.reversal}
                color="bg-green-500"
                icon={<TrendingUp className="w-3 h-3" />}
              />
              <ProbBar
                label="واگرایی"
                value={data.approachPrediction.divergence}
                color="bg-orange-500"
                icon={<Activity className="w-3 h-3" />}
              />
              <ProbBar
                label="گذشتن از سطح"
                value={data.approachPrediction.passThrough}
                color="bg-red-500"
                icon={<TrendingDown className="w-3 h-3" />}
              />
            </div>

            <Separator className="my-3 bg-slate-800" />

            <div className="space-y-1">
              <div className="text-[10px] font-bold text-slate-400 mb-1">دلایل پیش‌بینی:</div>
              {data.approachPrediction.reasons.map((r, i) => (
                <div key={i} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>

            <div className="mt-3 p-2 rounded bg-blue-500/5 border border-blue-500/20 text-[10px] text-blue-300/80 flex items-start gap-1.5">
              <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>
                این پیش‌بینی بر اساس ویژگی‌های فعلی بازار (سرعت RSI، حجم، سشن) است و فرض می‌کند RSI همین الان به سطح می‌رسد.
                وقتی واقعاً به سطح برسد و چند کندل در زون بماند، احتمالات می‌تواند متفاوت باشد.
              </span>
            </div>
          </Card>
        )}

        {/* ====== PATTERN DETECTION (M5) ====== */}
        <Card className="border-slate-800 bg-slate-900/80 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Activity className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <div className="text-sm font-bold">الگوی کندلی M5</div>
                <div className="text-[10px] text-slate-400">آخرین کندل‌های ۵ دقیقه</div>
              </div>
            </div>
            <Badge className={`
              ${data?.pattern?.bias === 'bullish' ? 'bg-green-500/90' :
                data?.pattern?.bias === 'bearish' ? 'bg-red-500/90' :
                'bg-slate-700 text-slate-300'}
            `}>
              {data?.pattern?.labelFa ?? '...'}
            </Badge>
          </div>

          {/* M5 candle visualization */}
          {data?.recentM5 && data.recentM5.length > 0 && (
            <div className="flex items-end gap-1 h-20 mb-2">
              {data.recentM5.map((c, i) => {
                const all = data.recentM5!;
                const max = Math.max(...all.map(x => x.high));
                const min = Math.min(...all.map(x => x.low));
                const range = max - min || 1;
                const h = ((c.high - c.low) / range) * 100;
                const bodyTop = ((Math.max(c.open, c.close) - min) / range) * 100;
                const bodyBot = ((Math.min(c.open, c.close) - min) / range) * 100;
                return (
                  <div key={i} className="flex-1 relative" style={{ height: '100%' }}>
                    {/* wick */}
                    <div className="absolute left-1/2 -translate-x-1/2 w-px bg-slate-500"
                         style={{ bottom: `${100 - bodyTop - (bodyTop - bodyBot) - ((c.high - Math.max(c.open, c.close)) / range) * 100}%`, height: `${h}%` }} />
                    {/* body */}
                    <div
                      className={`absolute left-1/2 -translate-x-1/2 w-3 rounded-sm ${
                        c.isUp ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{
                        bottom: `${100 - bodyTop}%`,
                        height: `${Math.max(2, bodyTop - bodyBot)}%`,
                      }}
                    />
                  </div>
                );
              })}
            </div>
          )}

          <div className="text-[10px] text-slate-400 text-center">
            {data?.pattern?.bias === 'bullish' && 'الگوی صعودی — مناسب ورود خرید در سطح ۴۰'}
            {data?.pattern?.bias === 'bearish' && 'الگوی نزولی — مناسب ورود فروش در سطح ۶۰'}
            {data?.pattern?.bias === 'neutral' && 'الگوی خنثی — منتظر الگوی قطعی'}
          </div>
        </Card>

        {/* ====== ENTRY TICKET ====== */}
        {data?.ticket && (
          <Card className={`p-4 ${
            data.ticket.valid
              ? 'border-green-500/40 bg-gradient-to-br from-green-950/40 to-slate-900'
              : 'border-slate-800 bg-slate-900/60'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                  data.ticket.valid ? 'bg-green-500/20' : 'bg-slate-700'
                }`}>
                  <Target className={`w-4 h-4 ${data.ticket.valid ? 'text-green-400' : 'text-slate-400'}`} />
                </div>
                <div>
                  <div className="text-sm font-bold">تیکت ورود</div>
                  <div className="text-[10px] text-slate-400">با مدیریت ریسک</div>
                </div>
              </div>
              {data.ticket.valid && data.ticket.direction && (
                <Badge className={`
                  ${data.ticket.direction === 'BUY' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}
                  text-xs px-3 py-1
                `}>
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
                  <span className="text-slate-400 flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    نسبت ریسک/سود
                  </span>
                  <span className="font-bold text-amber-300">
                    1:{data.ticket.riskRewardRatio.toFixed(2)}
                  </span>
                </div>

                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Zap className="w-3 h-3" />
                    اطمینان
                  </span>
                  <span className="font-bold text-amber-300">
                    {(data.ticket.confidence * 100).toFixed(0)}٪
                  </span>
                </div>

                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-green-500"
                    style={{ width: `${data.ticket.confidence * 100}%` }}
                  />
                </div>
              </>
            ) : (
              <div className="flex items-start gap-2 p-2 rounded-lg bg-slate-800/40 text-xs text-slate-400">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>{data.ticket.notes[0]}</div>
              </div>
            )}

            {data.ticket.notes.length > 0 && (
              <div className="space-y-1 mt-2">
                {data.ticket.notes.slice(data.ticket.valid ? 0 : 1).map((n, i) => (
                  <div key={i} className="text-[10px] text-slate-400 flex items-start gap-1">
                    <span className="text-blue-400">→</span>
                    <span>{n}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* ====== EXPAND BUTTON ====== */}
        <Button
          variant="ghost"
          onClick={() => setExpanded(!expanded)}
          className="w-full text-slate-400 hover:text-amber-400 text-xs"
        >
          {expanded ? (
            <><ChevronUp className="w-4 h-4 ml-1" /> بستن جزئیات</>
          ) : (
            <><ChevronDown className="w-4 h-4 ml-1" /> نمایش جزئیات بیشتر</>
          )}
        </Button>

        {/* ====== EXPANDED DETAILS ====== */}
        {expanded && data && (
          <div className="space-y-3">
            {/* Features */}
            {data.features && (
              <Card className="border-slate-800 bg-slate-900/80 p-4">
                <div className="text-sm font-bold mb-3">ویژگی‌های فعلی بازار</div>
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

            {/* Mini chart */}
            <Card className="border-slate-800 bg-slate-900/80 p-4">
              <div className="text-sm font-bold mb-3">نمودار قیمت و RSI (۲۴ ساعت اخیر)</div>
              <MiniChart candles={data.recentCandles} />
            </Card>

            {/* Info */}
            <Card className="border-slate-800 bg-slate-900/60 p-4">
              <div className="text-sm font-bold mb-2">درباره این ویجت</div>
              <div className="text-[11px] text-slate-400 leading-relaxed space-y-2">
                <p>
                  این ویجت RSI(30) را روی تایم‌فریم M30 طلا پایش می‌کند. منابع داده:
                </p>
                <ul className="space-y-1 list-disc pr-4">
                  <li>
                    <strong className="text-slate-200">قیمت لحظه‌ای:</strong> TradingView TVC:GOLD (طلای اسپات) —
                    نزدیک‌ترین منبع رایگان به XAUUSD بروکر شما (معمولاً $۱-۵ اختلاف)
                  </li>
                  <li>
                    <strong className="text-slate-200">کندل‌های تاریخی M30:</strong> Yahoo Finance GC=F (طلای آتی COMEX) —
                    برای محاسبه RSI
                  </li>
                  <li>
                    <strong className="text-slate-200">Fallback:</strong> Binance PAXG/USDT در صورت در دسترس نبودن Yahoo
                  </li>
                </ul>
                <p>
                  بازار طلای اسپات (XAUUSD) از یکشنبه ۲۳:۰۰ تا جمعه ۲۲:۰۰ UTC باز است و در شنبه تعطیل است.
                  در زمان تعطیلی، آخرین قیمت جمعه نمایش داده می‌شود.
                </p>
                <p>
                  <strong>چرا RSI با بروکر شما کمی متفاوت است؟</strong> RSI روی داده تاریخی GC=F محاسبه می‌شود
                  (نه XAUUSD اسپات بروکر شما). دلایل اختلاف باقی‌مانده:
                  (۱) GC=F آتی است، XAUUSD اسپات است؛
                  (۲) زمان سرور بروکر شما معمولاً GMT+2 یا GMT+3 است و مرز کندل‌ها متفاوت است؛
                  (۳) هر بروکر دیتا فید اختصاصی خودش را دارد.
                </p>
                <p>
                  وقتی RSI وارد زون شد، بر اساس آمار ۲ سال گذشته (۱۳۲۸ رویداد)، احتمال هر یک از سه حالت
                  (برگشت، واگرایی، گذشتن) را پیش‌بینی می‌کند. قوی‌ترین پیش‌بینی‌کننده، تعداد کندل‌هایی است که
                  RSI در زون می‌ماند.
                </p>
                <p>
                  همزمان کندل‌های M5 را بررسی می‌کند و در صورت تشکیل الگوی تأییدیه (دوجی، پین بار، همر، اینگالف)
                  و هم‌جهت بودن با سطح، تیکت ورود با حد ضرر و حد سود تولید می‌کند.
                </p>
              </div>
            </Card>
          </div>
        )}

        {/* Error */}
        {error && (
          <Card className="border-red-500/40 bg-red-950/40 p-3">
            <div className="text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center text-[10px] text-slate-600 pt-4">
          داده زنده از Binance · به‌روزرسانی هر ۳۰ ثانیه<br/>
          این ابزار سیگنال معاملاتی قطعی نیست — با مدیریت ریسک معامله کنید
        </div>
      </div>
    </div>
  );
}

function ProbBar({ label, value, color, icon }: {
  label: string; value: number; color: string; icon: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] mb-1">
        <span className="text-slate-300 flex items-center gap-1.5">
          {icon}
          {label}
        </span>
        <span className="font-bold text-slate-100 tabular-nums">{(value * 100).toFixed(0)}٪</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

function TicketBox({ label, value, tone }: {
  label: string; value: string; tone?: 'red' | 'green';
}) {
  return (
    <div className={`p-2 rounded-lg border ${
      tone === 'red' ? 'bg-red-500/10 border-red-500/30' :
      tone === 'green' ? 'bg-green-500/10 border-green-500/30' :
      'bg-slate-800/60 border-slate-700/50'
    }`}>
      <div className="text-[9px] text-slate-400 mb-0.5">{label}</div>
      <div className={`text-xs font-bold tabular-nums ${
        tone === 'red' ? 'text-red-300' : tone === 'green' ? 'text-green-300' : 'text-slate-100'
      }`}>{value}</div>
    </div>
  );
}

function FeatureItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between p-2 rounded bg-slate-800/40">
      <span className="text-slate-400">{label}</span>
      <span className="font-bold text-slate-100 tabular-nums">{value}</span>
    </div>
  );
}

function MiniChart({ candles }: { candles: any[] }) {
  if (!candles || candles.length === 0) return <div className="text-xs text-slate-500">داده‌ای موجود نیست</div>;

  const prices = candles.map(c => c.close);
  const rsis = candles.map(c => c.rsi).filter((r): r is number => r !== null);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const rangeP = maxP - minP || 1;

  // Build SVG path for price
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

  // Zone shading on RSI
  return (
    <div className="space-y-1">
      <svg viewBox={`0 0 ${w} ${hPrice + hRsi + 10}`} className="w-full" preserveAspectRatio="none">
        {/* Price chart */}
        <path d={pricePath} stroke="#fbbf24" strokeWidth="1.5" fill="none" />

        {/* RSI chart */}
        <g transform={`translate(0, ${hPrice + 10})`}>
          {/* Zones */}
          <rect x="0" y={hRsi - (60 / 100) * hRsi} width={w} height={(2 / 100) * hRsi} fill="#ef4444" opacity="0.3" />
          <rect x="0" y={hRsi - (40 / 100) * hRsi} width={w} height={(2 / 100) * hRsi} fill="#22c55e" opacity="0.3" />
          {/* Lines */}
          <line x1="0" y1={hRsi - (60 / 100) * hRsi} x2={w} y2={hRsi - (60 / 100) * hRsi} stroke="#ef4444" strokeWidth="0.3" strokeDasharray="2,2" />
          <line x1="0" y1={hRsi - (40 / 100) * hRsi} x2={w} y2={hRsi - (40 / 100) * hRsi} stroke="#22c55e" strokeWidth="0.3" strokeDasharray="2,2" />
          {rsiPath && <path d={rsiPath} stroke="#3b82f6" strokeWidth="1.2" fill="none" />}
        </g>
      </svg>
      <div className="flex justify-between text-[9px] text-slate-500">
        <span>{new Date(candles[0].time).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}</span>
        <span>قیمت (زرد) + RSI (آبی)</span>
        <span>{new Date(candles[candles.length - 1].time).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
    </div>
  );
}
