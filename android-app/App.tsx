/**
 * Gold RSI Widget — React Native (Expo) Android App
 *
 * Reads data from the Next.js API (deploy the web app separately)
 * or directly from Yahoo Finance / TradingView.
 *
 * For self-contained operation, set API_BASE to your deployed API URL.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  RefreshControl,
  StyleSheet,
  StatusBar,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

// Configuration: set this to your deployed API URL
// For local dev: http://10.0.2.2:3000 (Android emulator) or your PC's IP
// For production: https://your-app.vercel.app or https://your-app.workers.dev
const API_BASE = 'https://preview-chat-43ca7d06-8757-4f60-9c2b-6b4eae683f37.space-z.ai';
const API_URL = `${API_BASE}/api/gold`;

// Colors (matching web widget palette)
const COLORS = {
  bg: '#fafaf9',
  bgGradient: '#f5f5f4',
  card: '#ffffff',
  border: '#e7e5e4',
  text: '#1f2937',
  textSecondary: '#57534e',
  textMuted: '#a8a29e',
  // Category colors (pastel)
  reversal: { text: '#5b8c5a', bg: '#e8f4e8', bar: '#9ec99e', border: '#c3e6c3' },
  divergence: { text: '#c08a5a', bg: '#fdf3e7', bar: '#f0b870', border: '#f0d8b5' },
  passThrough: { text: '#b56b6b', bg: '#fce8e8', bar: '#e89090', border: '#f0c8c8' },
  level40: { text: '#5a7d9c', bg: '#e8f0f8', border: '#c8dcef' },
  level60: { text: '#9c7a5a', bg: '#f8ede0', border: '#e8d5b8' },
  // Zone type colors
  weeklyColor: '#f5b87a',
  weeklyBg: '#fef3e7',
  weeklyBorder: '#f0d8b5',
  dailyColor: '#c8c8c8',
  dailyBg: '#f5f5f4',
  dailyBorder: '#e0e0e0',
  // Candle colors (standard)
  candleUp: '#26a69a',
  candleDown: '#ef5350',
};

type ApiResponse = {
  ok: boolean;
  lastPrice: number;
  lastRsi: number;
  status: string;
  statusFa: string;
  marketOpen: boolean;
  tvQuote: any;
  touchFirst: any;
  approach40: any;
  approach60: any;
  importantZones: any;
  pattern: any;
  ticket: any;
  features: any;
  lastCandleAgeMin: number;
};

export default function App() {
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(API_URL, { cache: 'no-store' });
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

  if (loading && !data) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: COLORS.textSecondary }}>در حال بارگذاری...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar backgroundColor={COLORS.bg} barStyle="dark-content" />
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl refreshing={loading} onRefresh={fetchData} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <View style={styles.headerIcon}>
              <Ionicons name="pulse" size={20} color={COLORS.level60.text} />
            </View>
            <View>
              <Text style={styles.headerTitle}>ویجت RSI طلا</Text>
              <Text style={styles.headerSubtitle}>M30 · RSI(30) · سطوح ۴۰/۶۰</Text>
            </View>
          </View>
          {lastUpdate && (
            <Text style={styles.updateTime}>
              {lastUpdate.toLocaleTimeString('fa-IR')}
            </Text>
          )}
        </View>

        {error && (
          <View style={[styles.errorBox, { borderColor: COLORS.passThrough.border }]}>
            <Text style={{ color: COLORS.passThrough.text }}>{error}</Text>
          </View>
        )}

        {data && (
          <>
            {/* Price Widget Card */}
            <PriceWidget data={data} />

            {/* Combined Prediction */}
            {data.touchFirst && data.approach40 && data.approach60 && (
              <PredictionCard
                touchFirst={data.touchFirst}
                approach40={data.approach40}
                approach60={data.approach60}
              />
            )}

            {/* Important Zones */}
            {data.importantZones && data.importantZones.zones.length > 0 && (
              <ZonesCard importantZones={data.importantZones} />
            )}

            {/* Pattern Detection */}
            <PatternCard pattern={data.pattern} recentM5={data.recentM5 || []} />

            {/* Entry Ticket */}
            {data.ticket && <TicketCard ticket={data.ticket} />}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ============================================================
// Price Widget Card
// ============================================================
function PriceWidget({ data }: { data: ApiResponse }) {
  const alertLevel =
    data.status === 'IN_ZONE' ? 'critical' :
    data.status === 'APPROACHING' ? 'high' :
    data.status === 'WATCH' ? 'medium' : 'low';

  const statusColor =
    alertLevel === 'critical' ? COLORS.passThrough :
    alertLevel === 'high' ? COLORS.divergence :
    alertLevel === 'medium' ? COLORS.level40 :
    { text: '#78716c', bg: COLORS.bgGradient, border: COLORS.border };

  const rsiColor = data.lastRsi > 60 ? COLORS.level60.text :
                   data.lastRsi < 40 ? COLORS.level40.text :
                   '#d6d3d1';

  return (
    <View style={styles.card}>
      {/* Top row: price + status */}
      <View style={styles.rowSpaceBetween}>
        <View>
          <Text style={styles.label}>طلا / اونس (XAUUSD)</Text>
          <Text style={styles.priceText}>${data.lastPrice?.toFixed(2)}</Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <View style={[styles.badge, { backgroundColor: statusColor.bg, borderColor: statusColor.border }]}>
            <Text style={[styles.badgeText, { color: statusColor.text }]}>
              {data.statusFa}
            </Text>
          </View>
          {data.features && (
            <Text style={styles.sessionText}>{data.features.sessionFa}</Text>
          )}
        </View>
      </View>

      {/* Market status */}
      <View style={[styles.rowSpaceBetween, { marginTop: 8 }]}>
        <View style={[styles.badge, {
          backgroundColor: data.marketOpen ? COLORS.reversal.bg : COLORS.bgGradient,
          borderColor: data.marketOpen ? COLORS.reversal.border : COLORS.border,
        }]}>
          <View style={[styles.dot, {
            backgroundColor: data.marketOpen ? COLORS.reversal.text : COLORS.textMuted,
          }]} />
          <Text style={[styles.badgeText, {
            color: data.marketOpen ? COLORS.reversal.text : COLORS.textMuted,
          }]}>
            {data.marketOpen ? 'بازار باز' : 'بازار بسته'}
          </Text>
        </View>
        <Text style={styles.sourceText}>
          منبع: {data.tvQuote ? 'TradingView' : 'Yahoo GC=F'}
        </Text>
      </View>

      {/* RSI Gauge */}
      <View style={{ marginTop: 12 }}>
        <View style={styles.rowSpaceBetween}>
          <Text style={styles.label}>RSI(30)</Text>
          <Text style={[styles.rsiValue, { color: COLORS.text }]}>
            {data.lastRsi?.toFixed(2)}
          </Text>
        </View>
        <View style={styles.rsiBar}>
          {/* Zone bands */}
          <View style={[styles.rsiZoneBand, { left: '39%', width: '2%', backgroundColor: COLORS.level40.bg }]} />
          <View style={[styles.rsiZoneBand, { left: '59%', width: '2%', backgroundColor: COLORS.level60.bg }]} />
          {/* Fill */}
          <View style={[styles.rsiFill, {
            width: `${Math.min(100, Math.max(0, data.lastRsi || 0))}%`,
            backgroundColor: COLORS.textSecondary,
          }]} />
        </View>
        <View style={[styles.rowSpaceBetween, { marginTop: 4 }]}>
          <Text style={styles.scaleText}>۰</Text>
          <Text style={[styles.scaleText, { color: COLORS.level40.text }]}>۴۰</Text>
          <Text style={styles.scaleText}>۵۰</Text>
          <Text style={[styles.scaleText, { color: COLORS.level60.text }]}>۶۰</Text>
          <Text style={styles.scaleText}>۱۰۰</Text>
        </View>
      </View>

      {/* Market closed note */}
      {!data.marketOpen && (
        <View style={[styles.noteBox, { marginTop: 8 }]}>
          <Text style={styles.noteText}>
            بازار طلا شنبه‌ها تعطیل است. آخرین کندل: {Math.floor(data.lastCandleAgeMin / 60)} ساعت پیش
          </Text>
        </View>
      )}
    </View>
  );
}

// ============================================================
// Prediction Card
// ============================================================
function PredictionCard({ touchFirst, approach40, approach60 }: any) {
  const likelyPalette = touchFirst.likelyLevel === 60 ? COLORS.level60 : COLORS.level40;
  const likelyPrediction = touchFirst.likelyLevel === 40 ? approach40 : approach60;

  return (
    <View style={[styles.card, { borderColor: likelyPalette.border }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <View style={[styles.iconBox, { backgroundColor: likelyPalette.bg, borderColor: likelyPalette.border }]}>
          <Ionicons name="flash" size={16} color={likelyPalette.text} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>پیش‌بینی واکنش بازار</Text>
          <Text style={styles.cardSubtitle}>بر اساس آمار ۲ سال گذشته</Text>
        </View>
      </View>

      {/* Which level is more likely */}
      <View style={[styles.innerBox, { backgroundColor: likelyPalette.bg, borderColor: likelyPalette.border }]}>
        <View style={[styles.rowSpaceBetween, { marginBottom: 8 }]}>
          <Text style={styles.label}>سطح محتمل‌تر:</Text>
          <View style={[styles.badge, { backgroundColor: likelyPalette.text }]}>
            <Text style={[styles.badgeText, { color: '#fff' }]}>
              سطح {touchFirst.likelyLevel}
            </Text>
          </View>
        </View>
        <ProbBar label="برخورد به ۴۰ اول" value={touchFirst.probability40} color={COLORS.level40.text} />
        <ProbBar label="برخورد به ۶۰ اول" value={touchFirst.probability60} color={COLORS.level60.text} />
        <Text style={[styles.reasoning, { marginTop: 8 }]}>{touchFirst.reasoning}</Text>
      </View>

      {/* Prediction for likely level */}
      <Text style={[styles.label, { marginTop: 12, marginBottom: 6 }]}>
        وقتی به سطح {touchFirst.likelyLevel} برسد:
      </Text>
      <ProbBar label="برگشت" value={likelyPrediction.reversal} color={COLORS.reversal.bar} />
      <ProbBar label="واگرایی" value={likelyPrediction.divergence} color={COLORS.divergence.bar} />
      <ProbBar label="گذشتن" value={likelyPrediction.passThrough} color={COLORS.passThrough.bar} />
    </View>
  );
}

function ProbBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={{ marginVertical: 3 }}>
      <View style={[styles.rowSpaceBetween, { marginBottom: 2 }]}>
        <Text style={styles.barLabel}>{label}</Text>
        <Text style={styles.barValue}>{(value * 100).toFixed(0)}٪</Text>
      </View>
      <View style={styles.barBg}>
        <View style={[styles.barFill, { width: `${value * 100}%`, backgroundColor: color }]} />
      </View>
    </View>
  );
}

// ============================================================
// Zones Card
// ============================================================
function ZonesCard({ importantZones }: any) {
  const insideCount = importantZones.insideZones.length;
  const NEAR_THRESHOLD = 2.0;
  const nearZones = importantZones.zones.filter((z: any) => {
    const d = Math.abs(z.midpoint - importantZones.currentPrice) / importantZones.currentPrice * 100;
    return d <= NEAR_THRESHOLD && !importantZones.insideZones.some((i: any) => i.date === z.date && i.type === z.type);
  });
  const farZones = importantZones.zones.filter((z: any) => {
    const d = Math.abs(z.midpoint - importantZones.currentPrice) / importantZones.currentPrice * 100;
    return d > NEAR_THRESHOLD && !importantZones.insideZones.some((i: any) => i.date === z.date && i.type === z.type);
  });

  return (
    <View style={[styles.card, insideCount > 0 ? { borderColor: COLORS.divergence.border } : null]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <View style={[styles.iconBox, {
          backgroundColor: insideCount > 0 ? COLORS.divergence.bg : COLORS.level60.bg,
          borderColor: insideCount > 0 ? COLORS.divergence.border : COLORS.level60.border,
        }]}>
          <Ionicons name="locate" size={16} color={insideCount > 0 ? COLORS.divergence.text : COLORS.level60.text} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle}>زون‌های مهم (دوجی)</Text>
          <Text style={styles.cardSubtitle}>روزانه و هفتگی — Open/Close</Text>
        </View>
      </View>

      {/* Legend */}
      <View style={[styles.rowSpaceBetween, { marginBottom: 8 }]}>
        <View style={{ flexDirection: 'row', gap: 12 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.weeklyColor }]} />
            <Text style={styles.legendText}>هفتگی</Text>
          </View>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <View style={[styles.legendDot, { backgroundColor: COLORS.dailyColor }]} />
            <Text style={styles.legendText}>روزانه</Text>
          </View>
        </View>
        <Text style={styles.sourceText}>۱ pip = $۰.۱۰</Text>
      </View>

      {/* Inside zone alert */}
      {insideCount > 0 && (
        <View style={[styles.innerBox, {
          backgroundColor: COLORS.divergence.bg,
          borderColor: COLORS.divergence.border,
          marginBottom: 8,
        }]}>
          <Text style={[styles.cardTitle, { color: COLORS.divergence.text, fontSize: 12 }]}>
            داخل زون مهم هستیم!
          </Text>
          {importantZones.insideZones.map((z: any, i: number) => (
            <ZoneMiniRow key={`in-${i}`} z={z} currentPrice={importantZones.currentPrice} isInside />
          ))}
        </View>
      )}

      {/* Next target */}
      {importantZones.nextTarget && (
        <View style={[styles.innerBox, {
          backgroundColor: importantZones.nextTargetDirection === 'up' ? COLORS.reversal.bg : COLORS.passThrough.bg,
          borderColor: importantZones.nextTargetDirection === 'up' ? COLORS.reversal.border : COLORS.passThrough.border,
          marginBottom: 8,
        }]}>
          <Text style={[styles.label, {
            color: importantZones.nextTargetDirection === 'up' ? COLORS.reversal.text : COLORS.passThrough.text,
          }]}>
            زون هدف ({importantZones.nextTargetDirection === 'up' ? '↑ صعودی' : '↓ نزولی'}):
          </Text>
          <ZoneMiniRow z={importantZones.nextTarget} currentPrice={importantZones.currentPrice} isTarget />
        </View>
      )}

      {/* Near zones */}
      {nearZones.length > 0 && (
        <View style={{ marginBottom: 8 }}>
          <Text style={[styles.label, { marginBottom: 4 }]}>زون‌های نزدیک (≤ ۲٪):</Text>
          {nearZones.map((z: any, i: number) => (
            <ZoneMiniRow key={`n-${i}`} z={z} currentPrice={importantZones.currentPrice} />
          ))}
        </View>
      )}

      {/* Far zones */}
      {farZones.length > 0 && (
        <View>
          <Text style={[styles.label, { marginBottom: 4, color: COLORS.textMuted }]}>
            زون‌های بعدی ({'> ۲٪'}):
          </Text>
          {farZones.map((z: any, i: number) => (
            <ZoneMiniRow key={`f-${i}`} z={z} currentPrice={importantZones.currentPrice} />
          ))}
        </View>
      )}
    </View>
  );
}

function ZoneMiniRow({ z, currentPrice, isInside, isTarget }: any) {
  const isWeekly = z.type === 'weekly';
  const zoneColor = isWeekly ? COLORS.weeklyColor : COLORS.dailyColor;
  const zoneBg = isWeekly ? COLORS.weeklyBg : COLORS.dailyBg;
  const zoneBorder = isWeekly ? COLORS.weeklyBorder : COLORS.dailyBorder;
  const diff = Math.abs(z.midpoint - currentPrice);
  const pips = diff * 10;
  const points = diff;
  const distPct = (diff / currentPrice) * 100;
  const isAbove = z.midpoint > currentPrice;

  return (
    <View style={[styles.zoneRow, { backgroundColor: zoneBg, borderColor: zoneBorder, borderRightColor: zoneColor }]}>
      {/* Row 1: type + date + direction + distance */}
      <View style={[styles.rowSpaceBetween, { marginBottom: 4 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
          <View style={[styles.legendDot, { backgroundColor: zoneColor }]} />
          <Text style={styles.zoneType}>{isWeekly ? 'هفتگی' : 'روزانه'}</Text>
          <Text style={styles.zoneDate}>{z.date}</Text>
        </View>
        <Text style={{ color: isAbove ? COLORS.reversal.text : COLORS.passThrough.text, fontSize: 10, fontWeight: 'bold' }}>
          {isInside ? '✓ داخل' : isAbove ? '↑ بالا' : '↓ پایین'}
        </Text>
      </View>
      {/* Row 2: open / close / midpoint */}
      <View style={{ flexDirection: 'row', gap: 4, marginBottom: 4 }}>
        <View style={[styles.zonePriceBox, { flex: 1 }]}>
          <Text style={styles.zonePriceLabel}>شروع (Open)</Text>
          <Text style={styles.zonePriceValue}>${z.open?.toFixed(2)}</Text>
        </View>
        <View style={[styles.zonePriceBox, { flex: 1 }]}>
          <Text style={styles.zonePriceLabel}>پایان (Close)</Text>
          <Text style={styles.zonePriceValue}>${z.close?.toFixed(2)}</Text>
        </View>
        <View style={[styles.zonePriceBox, { flex: 1 }]}>
          <Text style={styles.zonePriceLabel}>وسط زون</Text>
          <Text style={styles.zonePriceValue}>${z.midpoint?.toFixed(2)}</Text>
        </View>
      </View>
      {/* Row 3: distance */}
      {!isInside && (
        <View style={{ flexDirection: 'row', justifyContent: 'flex-end', gap: 8 }}>
          <Text style={styles.distText}>پوینت: <Text style={styles.distValue}>{points.toFixed(1)}</Text></Text>
          <Text style={styles.distText}>pip: <Text style={styles.distValue}>{pips.toFixed(0)}</Text></Text>
          <Text style={styles.distText}>٪: <Text style={[styles.distValue, {
            color: isAbove ? COLORS.reversal.text : COLORS.passThrough.text,
          }]}>{distPct.toFixed(2)}</Text></Text>
        </View>
      )}
    </View>
  );
}

// ============================================================
// Pattern Card
// ============================================================
function PatternCard({ pattern, recentM5 }: any) {
  const biasColor = pattern.bias === 'bullish' ? COLORS.candleUp :
                    pattern.bias === 'bearish' ? COLORS.candleDown :
                    COLORS.textMuted;

  return (
    <View style={styles.card}>
      <View style={[styles.rowSpaceBetween, { marginBottom: 8 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View style={[styles.iconBox, { backgroundColor: '#ede9fe' }]}>
            <Ionicons name="candle" size={16} color="#7c6fc4" />
          </View>
          <View>
            <Text style={styles.cardTitle}>الگوی کندلی M5</Text>
            <Text style={styles.cardSubtitle}>آخرین کندل‌های ۵ دقیقه</Text>
          </View>
        </View>
        <View style={[styles.badge, { backgroundColor: biasColor, borderColor: biasColor }]}>
          <Text style={[styles.badgeText, { color: '#fff' }]}>{pattern.labelFa}</Text>
        </View>
      </View>
      <Text style={[styles.noteText, { textAlign: 'center' }]}>
        {pattern.bias === 'bullish' && 'الگوی صعودی — مناسب ورود خرید در سطح ۴۰'}
        {pattern.bias === 'bearish' && 'الگوی نزولی — مناسب ورود فروش در سطح ۶۰'}
        {pattern.bias === 'neutral' && 'الگوی خنثی — منتظر الگوی قطعی'}
      </Text>
    </View>
  );
}

// ============================================================
// Ticket Card
// ============================================================
function TicketCard({ ticket }: any) {
  return (
    <View style={[styles.card, ticket.valid ? { borderColor: COLORS.reversal.border } : null]}>
      <View style={[styles.rowSpaceBetween, { marginBottom: 8 }]}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <View style={[styles.iconBox, { backgroundColor: ticket.valid ? COLORS.reversal.bg : COLORS.bgGradient }]}>
            <Ionicons name="create" size={16} color={ticket.valid ? COLORS.reversal.text : COLORS.textMuted} />
          </View>
          <View>
            <Text style={styles.cardTitle}>تیکت ورود</Text>
            <Text style={styles.cardSubtitle}>با مدیریت ریسک</Text>
          </View>
        </View>
        {ticket.valid && ticket.direction && (
          <View style={[styles.badge, {
            backgroundColor: ticket.direction === 'BUY' ? COLORS.reversal.text : COLORS.passThrough.text,
          }]}>
            <Text style={[styles.badgeText, { color: '#fff' }]}>{ticket.directionFa}</Text>
          </View>
        )}
      </View>

      {ticket.valid ? (
        <>
          <View style={{ flexDirection: 'row', gap: 4, marginBottom: 8 }}>
            <View style={[styles.zonePriceBox, { flex: 1 }]}>
              <Text style={styles.zonePriceLabel}>قیمت ورود</Text>
              <Text style={styles.zonePriceValue}>${ticket.entryPrice.toFixed(2)}</Text>
            </View>
            <View style={[styles.zonePriceBox, { flex: 1, backgroundColor: COLORS.passThrough.bg }]}>
              <Text style={styles.zonePriceLabel}>حد ضرر</Text>
              <Text style={[styles.zonePriceValue, { color: COLORS.passThrough.text }]}>${ticket.stopLoss.toFixed(2)}</Text>
            </View>
            <View style={[styles.zonePriceBox, { flex: 1, backgroundColor: COLORS.reversal.bg }]}>
              <Text style={styles.zonePriceLabel}>حد سود</Text>
              <Text style={[styles.zonePriceValue, { color: COLORS.reversal.text }]}>${ticket.takeProfit.toFixed(2)}</Text>
            </View>
          </View>
          <View style={[styles.rowSpaceBetween, { marginBottom: 4 }]}>
            <Text style={styles.barLabel}>نسبت ریسک/سود</Text>
            <Text style={[styles.barValue, { color: COLORS.divergence.text }]}>
              1:{ticket.riskRewardRatio.toFixed(2)}
            </Text>
          </View>
          <View style={[styles.rowSpaceBetween, { marginBottom: 4 }]}>
            <Text style={styles.barLabel}>اطمینان</Text>
            <Text style={[styles.barValue, { color: COLORS.divergence.text }]}>
              {(ticket.confidence * 100).toFixed(0)}٪
            </Text>
          </View>
        </>
      ) : (
        <Text style={styles.noteText}>{ticket.notes[0]}</Text>
      )}
    </View>
  );
}

// ============================================================
// Styles
// ============================================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: COLORS.level60.bg,
    borderWidth: 1,
    borderColor: COLORS.level60.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  headerSubtitle: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  updateTime: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  rowSpaceBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  priceText: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    fontVariant: ['tabular-nums'],
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
    gap: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  sessionText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  sourceText: {
    fontSize: 9,
    color: COLORS.textMuted,
  },
  rsiValue: {
    fontSize: 16,
    fontWeight: 'bold',
    fontVariant: ['tabular-nums'],
  },
  rsiBar: {
    height: 12,
    backgroundColor: COLORS.bgGradient,
    borderRadius: 6,
    overflow: 'hidden',
    marginTop: 4,
  },
  rsiZoneBand: {
    position: 'absolute',
    top: 0,
    bottom: 0,
  },
  rsiFill: {
    height: '100%',
  },
  scaleText: {
    fontSize: 9,
    color: COLORS.textMuted,
  },
  noteBox: {
    backgroundColor: COLORS.bgGradient,
    borderRadius: 6,
    padding: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  noteText: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  errorBox: {
    backgroundColor: COLORS.passThrough.bg,
    borderRadius: 6,
    padding: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  iconBox: {
    width: 28,
    height: 28,
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  cardSubtitle: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  innerBox: {
    borderRadius: 6,
    padding: 10,
    borderWidth: 1,
  },
  reasoning: {
    fontSize: 10,
    color: COLORS.text,
  },
  barLabel: {
    fontSize: 11,
    color: COLORS.text,
  },
  barValue: {
    fontSize: 11,
    fontWeight: 'bold',
    color: COLORS.text,
    fontVariant: ['tabular-nums'],
  },
  barBg: {
    height: 8,
    backgroundColor: COLORS.border,
    borderRadius: 4,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 2,
  },
  legendText: {
    fontSize: 9,
    color: COLORS.textSecondary,
  },
  zoneRow: {
    borderRadius: 4,
    padding: 8,
    borderWidth: 1,
    marginBottom: 4,
    borderRightWidth: 3,
  },
  zoneType: {
    fontSize: 9,
    fontWeight: 'bold',
    color: COLORS.textSecondary,
  },
  zoneDate: {
    fontSize: 10,
    color: COLORS.text,
    fontFamily: 'monospace',
    fontVariant: ['tabular-nums'],
  },
  zonePriceBox: {
    backgroundColor: COLORS.card,
    borderRadius: 4,
    padding: 4,
    alignItems: 'center',
  },
  zonePriceLabel: {
    fontSize: 8,
    color: COLORS.textMuted,
  },
  zonePriceValue: {
    fontSize: 10,
    fontWeight: 'bold',
    color: COLORS.text,
    fontVariant: ['tabular-nums'],
  },
  distText: {
    fontSize: 9,
    color: COLORS.textMuted,
  },
  distValue: {
    fontWeight: 'bold',
    color: COLORS.text,
    fontVariant: ['tabular-nums'],
  },
});
