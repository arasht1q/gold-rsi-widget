# Gold RSI Strategy — Complete Rules & Code Reference
# Generated: 2026-11-27
# This document will be updated with every change

## 1. Strategy Overview

**Instrument:** XAUUSD (Gold)
**Timeframe:** M30 (30-minute)
**Indicator:** RSI(30) — Wilder smoothing, applied to Close
**Levels:** 40 (oversold) and 60 (overbought) with ±1 tolerance
**RSI(14):** Also calculated as reference

## 2. Backtest Statistics (2-year: Nov 2024 - Nov 2026)

- Total touch events: 1,328 (avg 1.8/day)
- At level 40: 598 events | At level 60: 730 events

### Outcome Distribution:
| Category | Count | Percentage |
|----------|-------|-----------|
| Pass-through | 612 | 46.1% |
| Reversal | 437 | 32.9% |
| Divergence | 279 | 21.0% |

### Key Finding:
- **Candles in zone** is strongest predictor (ANOVA F=20.13, p<0.001)
- 5+ candles in zone → 50%+ reversal probability
- 1-2 candles in zone → 70% pass-through probability
- Volume ratio 5/20 > 1.3 → momentum strong (favor divergence/pass-through)
- US session has highest reversal rate (36.8%)
- Europe session has lowest reversal rate (27.8%)
- Avg time from RSI=50 to zone touch: 19.4 hours

## 3. Signal Types (8 total)

### Signal 1: First Touch
- **Condition:** RSI enters zone 40 (buy) or 60 (sell) for first time
- **Filter:** Must have candle pattern OR 2+ candles in zone
- **Label:** "First Touch" (green=buy, red=sell)
- **Strength:** Medium

### Signal 2: Turn
- **Condition:** RSI exits zone 40 upward (buy) or zone 60 downward (sell)
- **Label:** "Turn" (light green=buy, light red=sell)
- **Strength:** Medium

### Signal 3: Divergence (strong, near zone)
- **Condition:** Price lower low + RSI higher low (bullish) near zone 40
- **Condition:** Price higher high + RSI lower high (bearish) near zone 60
- **Range:** Within 50 bars after zone touch, RSI < 50 (bullish) or > 50 (bearish)
- **Label:** "Divergence" (blue=bull, orange=bear)
- **Strength:** Strong

### Signal 4: Weak Divergence (outside zone)
- **Condition:** Same as Signal 3 but detected OUTSIDE zone range
- **Label:** "Weak Div" (light blue=bull, light orange=bear)
- **Strength:** Weak

### Signal 5: Strong Reversal
- **Condition:** RSI has been in zone for exactly 5 candles
- **Backtest:** 5+ candles → 50%+ reversal probability
- **Label:** "Strong Rev" (bright green=buy, bright red=sell)
- **Strength:** Very Strong

### Signal 6: Momentum Warning
- **Condition:** Volume ratio (5-bar avg / 20-bar avg) > 1.3 when RSI enters zone
- **Backtest:** High volume → momentum strong, favor divergence/pass-through
- **Label:** "Momentum" (purple)
- **Strength:** Warning (be careful with reversal trades)

### Signal 7: Multi-Timeframe Confluence
- **Condition:** 3+ timeframes (M5/M15/M30/H1/H4) have RSI < 40 (buy) or > 60 (sell)
- **Label:** "Multi-TF" (dark blue=buy, dark orange=sell)
- **Strength:** Strong

### Signal 8: Trend Cross
- **Condition:** RSI crosses above 50 (bullish) or below 50 (bearish)
- **Purpose:** Captures momentum moves BETWEEN zones 40 and 60
- **Label:** "Trend Up" (green) / "Trend Down" (red)
- **Strength:** Medium

## 4. Prediction Model

Based on 2-year backtest means:

### Level 40 means:
- Reversal: cz=1.61, vel=-2.03
- Divergence: cz=2.78, vel=-3.45
- Pass-through: cz=1.78, vel=-3.40

### Level 60 means:
- Reversal: cz=1.54, vel=1.67
- Divergence: cz=2.17, vel=3.05
- Pass-through: cz=1.83, vel=2.16

### Base rates:
- Reversal: 32.9%
- Divergence: 21.0%
- Pass-through: 46.1%

### Session multipliers:
- US session: reversal ×1.12
- Europe session: reversal ×0.85

## 5. Entry Ticket

When RSI is in zone:
- **BUY** (zone 40): Entry=close, SL=close×0.996, TP=close×1.008, R:R=1:2
- **SELL** (zone 60): Entry=close, SL=close×1.004, TP=close×0.992, R:R=1:2

## 6. Visual Elements

### Session Backgrounds:
- Asia (UTC 00-07): teal, 93% transparency
- Europe (UTC 07-13): orange, 93% transparency
- US (UTC 13-21): red, 93% transparency

### Day Markers:
- Vertical dotted line at each new day
- Label with day number

### Panel:
- Price, RSI(30), RSI(14)
- Zone status + candles in zone
- Reversal/Divergence/Pass-through probabilities
- Pattern detection (Doji, Pin Bar, Engulfing)
- Volume ratio (red if > 1.3)
- MTF oversold/overbought count
- Entry ticket with SL/TP/R:R when in zone

## 7. Trading Rules Summary

1. Wait for RSI to reach zone 40 or 60
2. Check candles in zone: 5+ = strong reversal signal
3. Check volume ratio: > 1.3 = momentum warning
4. Check MTF confluence: 3+ TFs = stronger signal
5. Wait for pattern confirmation (Doji, Pin Bar, Engulfing)
6. US session has best reversal rate
7. Use SL beyond recent swing high/low
8. R:R target = 1:2

## 8. Pattern Detection

- **Doji:** body ≤ 10% of range
- **Bullish Pin Bar:** lower wick ≥ 60% of range, body ≤ 35%
- **Bearish Pin Bar:** upper wick ≥ 60% of range, body ≤ 35%
- **Bullish Engulfing:** prev red, current green, current engulfs prev body
- **Bearish Engulfing:** prev green, current red, current engulfs prev body

## 9. Overlap Prevention

- Counter `sigCountThisBar` tracks signals per bar
- Each label offset by `ATR × 0.5 × signalNumber` vertically
- Multiple signals on same bar stack without overlap

## 10. Alerts

All 8 signal types have alerts:
- Buy/Sell First Touch
- Turn Buy/Sell
- Bull/Bear Divergence (strong)
- Weak Bull/Bear Divergence
- Strong Reversal Buy/Sell
- Momentum Warning
- Multi-TF Buy/Sell
- Trend Up/Down

## 11. Configuration

All signals can be toggled on/off via inputs:
- showSigs, showTurn, showDiv, showWeak, showStrong, showMom, showMTF, showTrend
- showSess (session backgrounds), showDayMark (day markers)
- divRange (divergence detection range, default 50 bars)
- mtfCount (min timeframes for confluence, default 3)

## 12. Code

The complete Pine Script v5 code is below:

```pine
```

(Full code attached as separate file: Gold_RSI_Strategy.pine)
