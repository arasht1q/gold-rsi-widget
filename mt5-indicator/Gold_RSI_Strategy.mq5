//+------------------------------------------------------------------+
//|                                         Gold_RSI_Strategy.mq5    |
//|        RSI(30)+RSI(14) | Movable Panel | Doji Zones | Signals    |
//+------------------------------------------------------------------+
#property copyright "Z.ai - Gold RSI Widget"
#property link      "https://github.com/arasht1q/gold-rsi-widget"
#property version   "1.40"
#property description "RSI(30)+RSI(14) M30 - Movable Persian Panel - Doji Zones - Entry Signals"
#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots   2

#property indicator_label1  "RSI(30)"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrSteelBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

#property indicator_label2  "RSI(14)"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrLightSkyBlue
#property indicator_style2  STYLE_DOT
#property indicator_width2  1

#property indicator_level1  40.0
#property indicator_level2  60.0
#property indicator_levelcolor clrSilver
#property indicator_levelstyle STYLE_DASH
#property indicator_levelwidth 1

//--- Input Parameters
input int      InpRSIPeriod        = 30;
input int      InpRSI14Period      = 14;
input double   InpLevelOversold    = 40.0;
input double   InpLevelOverbought  = 60.0;
input double   InpZoneTolerance    = 1.0;
input double   InpDojiThreshold    = 0.10;
input int      InpLookbackDays     = 180;
input int      InpLookbackWeeks    = 52;
input double   InpZoneFilter       = 25.0;     // Zone filter % (show zones within this % of price)
input int      InpMaxZonesToShow   = 12;        // Max zones to draw on chart
input int      InpSignalCount      = 50;
input bool     InpShowZones        = true;
input bool     InpShowDailyZones   = true;
input bool     InpShowWeeklyZones  = true;
input color    InpWeeklyZoneColor  = C'230,160,80';
input color    InpDailyZoneColor   = C'170,170,175';
input color    InpPanelBgColor     = C'245,243,238';  // Panel background (works on any theme)
input color    InpPanelTextColor   = C'40,38,35';      // Panel text color
input bool     InpShowPanel        = true;
input bool     InpShowSignals      = true;
input bool     InpEnableAlerts     = true;
input bool     InpAlertOnRSI       = true;
input bool     InpAlertOnZone      = true;
input bool     InpAlertOnPattern   = true;

//--- Buffers
double RSI30_Buffer[];
double RSI14_Buffer[];

//--- Globals
int rsi30_handle = INVALID_HANDLE;
int rsi14_handle = INVALID_HANDLE;
double g_rsi = 0;
double g_rsi14 = 0;
double g_rsi_vel_10 = 0;
int g_candles_in_zone = 0;
int g_current_zone = 0;
datetime g_last_alert_rsi = 0;
datetime g_last_alert_zone = 0;

//--- Panel position (user can drag to change)
int g_panel_x = 10;
int g_panel_y = 25;
ENUM_BASE_CORNER g_panel_corner = CORNER_LEFT_UPPER;
bool g_panel_exists = false;

//--- Zones
struct DojiZone {
   datetime time; double open; double close; double midpoint;
   double range_high; double range_low; int type; bool active;
};
DojiZone g_zones[];
int g_zone_count = 0;

//--- Signals
struct EntrySignal { datetime time; double price; int level; int direction; };
EntrySignal g_signals[];
int g_signal_count = 0;

//--- Prediction
struct CatMeans { double cz; double vel; double vol; };
CatMeans means_40[3]; CatMeans means_60[3];
double base_rates[3] = {0.329, 0.210, 0.461};

#define PANEL_W 255
#define PANEL_H 420
#define LH 16

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, RSI30_Buffer, INDICATOR_DATA);
   SetIndexBuffer(1, RSI14_Buffer, INDICATOR_DATA);
   PlotIndexSetString(0, PLOT_LABEL, "RSI(30)");
   PlotIndexSetString(1, PLOT_LABEL, "RSI(14)");
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 0, InpLevelOversold);
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 1, InpLevelOverbought);
   IndicatorSetString(INDICATOR_SHORTNAME, "RSI(30)+RSI(14) M30 Strategy");
   
   rsi30_handle = iRSI(_Symbol, PERIOD_M30, InpRSIPeriod, PRICE_CLOSE);
   rsi14_handle = iRSI(_Symbol, PERIOD_M30, InpRSI14Period, PRICE_CLOSE);
   if(rsi30_handle == INVALID_HANDLE || rsi14_handle == INVALID_HANDLE)
      return(INIT_FAILED);
   
   means_40[0].cz=1.61; means_40[0].vel=-2.03; means_40[0].vol=1.07;
   means_40[1].cz=2.78; means_40[1].vel=-3.45; means_40[1].vol=1.02;
   means_40[2].cz=1.78; means_40[2].vel=-3.40; means_40[2].vol=1.10;
   means_60[0].cz=1.54; means_60[0].vel=1.67; means_60[0].vol=1.07;
   means_60[1].cz=2.17; means_60[1].vel=3.05; means_60[1].vol=1.02;
   means_60[2].cz=1.83; means_60[2].vel=2.16; means_60[2].vol=1.10;
   
   EventSetTimer(30);
   ScanDojiZones();
   ScanHistoricalSignals();
   
   // Make sure objects show on chart
   ChartSetInteger(0, CHART_EVENT_OBJECT_CREATE, true);
   ChartSetInteger(0, CHART_EVENT_OBJECT_DELETE, true);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, "RSI_ZONE_");
   ObjectsDeleteAll(0, "RSI_PNL_");
   ObjectsDeleteAll(0, "RSI_SIG_");
   Comment("");
   if(rsi30_handle != INVALID_HANDLE) IndicatorRelease(rsi30_handle);
   if(rsi14_handle != INVALID_HANDLE) IndicatorRelease(rsi14_handle);
}

//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   // Handle panel drag
   if(id == CHARTEVENT_OBJECT_DRAG)
   {
      if(sparam == "RSI_PNL_BG")
      {
         // Read new position from dragged background
         g_panel_x = (int)ObjectGetInteger(0, "RSI_PNL_BG", OBJPROP_XDISTANCE);
         g_panel_y = (int)ObjectGetInteger(0, "RSI_PNL_BG", OBJPROP_YDISTANCE);
         g_panel_corner = (ENUM_BASE_CORNER)ObjectGetInteger(0, "RSI_PNL_BG", OBJPROP_CORNER);
         // Redraw panel text at new position
         DrawPanel();
         ChartRedraw(0);
      }
   }
}

//+------------------------------------------------------------------+
void OnTimer()
{
   ScanDojiZones();
   if(InpShowPanel) DrawPanel();
   CheckAlerts();
}

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[])
{
   int c30 = CopyBuffer(rsi30_handle, 0, 0, rates_total, RSI30_Buffer);
   int c14 = CopyBuffer(rsi14_handle, 0, 0, rates_total, RSI14_Buffer);
   if(c30 <= 0 || c14 <= 0) return(0);
   
   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(rsi30_handle, 0, 0, 15, rsi) > 0)
   {
      g_rsi = rsi[0];
      if(ArraySize(rsi) >= 11) g_rsi_vel_10 = rsi[0] - rsi[10];
      UpdateCandlesInZone(rsi);
   }
   
   double r14[];
   ArraySetAsSeries(r14, true);
   if(CopyBuffer(rsi14_handle, 0, 0, 3, r14) > 0)
      g_rsi14 = r14[0];
   
   if(InpShowZones) DrawZonesOnChart();
   if(InpShowSignals) DrawSignals();
   if(InpShowPanel) DrawPanel();
   
   // Debug info on chart
   double cp = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   Comment(StringFormat("RSI(30)=%.2f | RSI(14)=%.2f | Zones: %d found, %d shown | Signals: %d | Price: %.2f",
                        g_rsi, g_rsi14, g_zone_count, MathMin(g_zone_count, InpMaxZonesToShow), g_signal_count, cp));
   
   return(rates_total);
}

//+------------------------------------------------------------------+
void UpdateCandlesInZone(double &rsi[])
{
   g_candles_in_zone = 0;
   g_current_zone = 0;
   double lo40 = InpLevelOversold - InpZoneTolerance;
   double hi40 = InpLevelOversold + InpZoneTolerance;
   double lo60 = InpLevelOverbought - InpZoneTolerance;
   double hi60 = InpLevelOverbought + InpZoneTolerance;
   
   if(g_rsi >= lo40 && g_rsi <= hi40)
   {
      g_current_zone = 40;
      for(int i = 0; i < ArraySize(rsi) && i < 50; i++)
      {
         if(rsi[i] >= lo40 && rsi[i] <= hi40) g_candles_in_zone++;
         else break;
      }
   }
   else if(g_rsi >= lo60 && g_rsi <= hi60)
   {
      g_current_zone = 60;
      for(int i = 0; i < ArraySize(rsi) && i < 50; i++)
      {
         if(rsi[i] >= lo60 && rsi[i] <= hi60) g_candles_in_zone++;
         else break;
      }
   }
}

//+------------------------------------------------------------------+
void ScanDojiZones()
{
   g_zone_count = 0;
   ArrayResize(g_zones, 0);
   
   if(InpShowDailyZones)
   {
      MqlRates d[];
      ArraySetAsSeries(d, true);
      int c = CopyRates(_Symbol, PERIOD_D1, 0, InpLookbackDays + 1, d);
      if(c > 0)
         for(int i = 1; i < c; i++)
         {
            double r = d[i].high - d[i].low;
            if(r <= 0) continue;
            if(MathAbs(d[i].close - d[i].open) <= InpDojiThreshold * r)
               AddZone(d[i].time, d[i].open, d[i].close, 0);
         }
   }
   
   if(InpShowWeeklyZones)
   {
      MqlRates w[];
      ArraySetAsSeries(w, true);
      int c = CopyRates(_Symbol, PERIOD_W1, 0, InpLookbackWeeks + 1, w);
      if(c > 0)
         for(int i = 1; i < c; i++)
         {
            double r = w[i].high - w[i].low;
            if(r <= 0) continue;
            if(MathAbs(w[i].close - w[i].open) <= InpDojiThreshold * r)
               AddZone(w[i].time, w[i].open, w[i].close, 1);
         }
   }
   
   Print("[Gold RSI] Doji zones found: ", g_zone_count, 
         " (Daily: ", CountType(0), ", Weekly: ", CountType(1), ")");
}

int CountType(int t)
{
   int n = 0;
   for(int i = 0; i < g_zone_count; i++) if(g_zones[i].type == t) n++;
   return n;
}

//+------------------------------------------------------------------+
void AddZone(datetime t, double op, double cl, int type)
{
   g_zone_count++;
   ArrayResize(g_zones, g_zone_count);
   int i = g_zone_count - 1;
   g_zones[i].time = t;
   g_zones[i].open = op;
   g_zones[i].close = cl;
   g_zones[i].midpoint = (op + cl) / 2.0;
   g_zones[i].range_high = MathMax(op, cl);
   g_zones[i].range_low = MathMin(op, cl);
   g_zones[i].type = type;
   g_zones[i].active = false;
}

//+------------------------------------------------------------------+
void ScanHistoricalSignals()
{
   g_signal_count = 0;
   ArrayResize(g_signals, 0);
   
   double rsi[];
   ArraySetAsSeries(rsi, true);
   int copied = CopyBuffer(rsi30_handle, 0, 0, 2000, rsi);
   if(copied <= 0) return;
   
   datetime times[];
   ArraySetAsSeries(times, true);
   if(CopyTime(_Symbol, PERIOD_M30, 0, copied, times) <= 0) return;
   
   double closes[];
   ArraySetAsSeries(closes, true);
   if(CopyClose(_Symbol, PERIOD_M30, 0, copied, closes) <= 0) return;
   
   double lo40 = InpLevelOversold - InpZoneTolerance;
   double hi40 = InpLevelOversold + InpZoneTolerance;
   double lo60 = InpLevelOverbought - InpZoneTolerance;
   double hi60 = InpLevelOverbought + InpZoneTolerance;
   
   for(int i = copied - 2; i >= 1; i--)
   {
      if(rsi[i] >= lo40 && rsi[i] <= hi40 && (rsi[i+1] < lo40 || rsi[i+1] > hi40))
         AddSignal(times[i], closes[i], 40, 1);
      if(rsi[i] >= lo60 && rsi[i] <= hi60 && (rsi[i+1] < lo60 || rsi[i+1] > hi60))
         AddSignal(times[i], closes[i], 60, -1);
   }
}

void AddSignal(datetime t, double price, int level, int dir)
{
   g_signal_count++;
   ArrayResize(g_signals, g_signal_count);
   int i = g_signal_count - 1;
   g_signals[i].time = t;
   g_signals[i].price = price;
   g_signals[i].level = level;
   g_signals[i].direction = dir;
}

//+------------------------------------------------------------------+
void DrawSignals()
{
   ObjectsDeleteAll(0, "RSI_SIG_");
   if(g_signal_count == 0) return;
   
   int start = MathMax(0, g_signal_count - InpSignalCount);
   for(int i = start; i < g_signal_count; i++)
   {
      string nm = "RSI_SIG_" + IntegerToString(i);
      int ac = g_signals[i].direction == 1 ? 233 : 234;
      color cl = g_signals[i].direction == 1 ? C'91,140,90' : C'181,107,107';
      double off = g_signals[i].price * 0.003;
      double pp = g_signals[i].direction == 1 ? g_signals[i].price - off : g_signals[i].price + off;
      
      if(ObjectFind(0, nm) < 0)
         ObjectCreate(0, nm, OBJ_ARROW, 0, g_signals[i].time, pp);
      ObjectSetInteger(0, nm, OBJPROP_ARROWCODE, ac);
      ObjectSetInteger(0, nm, OBJPROP_COLOR, cl);
      ObjectSetInteger(0, nm, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, nm, OBJPROP_SELECTABLE, false);
      
      string ln = "RSI_SIG_L_" + IntegerToString(i);
      if(ObjectFind(0, ln) < 0)
         ObjectCreate(0, ln, OBJ_TEXT, 0, g_signals[i].time, pp);
      ObjectSetString(0, ln, OBJPROP_TEXT, StringFormat("%s%d", g_signals[i].direction==1?"B":"S", g_signals[i].level));
      ObjectSetInteger(0, ln, OBJPROP_COLOR, cl);
      ObjectSetInteger(0, ln, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, ln, OBJPROP_SELECTABLE, false);
   }
}

//+------------------------------------------------------------------+
void DrawZonesOnChart()
{
   double cp = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(cp <= 0) return;
   
   ObjectsDeleteAll(0, "RSI_ZONE_");
   
   double fw = cp * (InpZoneFilter / 100.0);
   
   // Sort zones by proximity to current price
   // Create sorted index
   int sorted[];
   ArrayResize(sorted, g_zone_count);
   for(int i = 0; i < g_zone_count; i++) sorted[i] = i;
   
   // Simple bubble sort by distance
   for(int i = 0; i < g_zone_count - 1; i++)
   {
      for(int j = i + 1; j < g_zone_count; j++)
      {
         double di = MathAbs(g_zones[sorted[i]].midpoint - cp);
         double dj = MathAbs(g_zones[sorted[j]].midpoint - cp);
         if(dj < di)
         {
            int tmp = sorted[i]; sorted[i] = sorted[j]; sorted[j] = tmp;
         }
      }
   }
   
   int shown = 0;
   for(int s = 0; s < g_zone_count && shown < InpMaxZonesToShow; s++)
   {
      int i = sorted[s];
      if(g_zones[i].time >= TimeCurrent()) continue;
      if(MathAbs(g_zones[i].midpoint - cp) > fw) continue;
      
      double tol = cp * 0.002;
      bool inside = (cp >= g_zones[i].range_low - tol && cp <= g_zones[i].range_high + tol);
      g_zones[i].active = inside;
      
      string nm = "RSI_ZONE_" + IntegerToString(shown);
      datetime t2 = TimeCurrent() + PeriodSeconds(PERIOD_M30) * 200;
      
      if(ObjectFind(0, nm) < 0)
         ObjectCreate(0, nm, OBJ_RECTANGLE, 0, g_zones[i].time, g_zones[i].range_high, t2, g_zones[i].range_low);
      
      color zc = g_zones[i].type == 1 ? InpWeeklyZoneColor : InpDailyZoneColor;
      if(inside) zc = C'255,220,60';
      
      ObjectSetInteger(0, nm, OBJPROP_COLOR, zc);
      ObjectSetInteger(0, nm, OBJPROP_FILL, true);
      ObjectSetInteger(0, nm, OBJPROP_BACK, true);
      ObjectSetInteger(0, nm, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, nm, OBJPROP_SELECTABLE, false);
      
      // Label with date, type, O/C
      string ln = "RSI_ZONE_L_" + IntegerToString(shown);
      string lt = StringFormat("%s %s O:%.2f C:%.2f",
                               g_zones[i].type == 1 ? "W" : "D",
                               TimeToString(g_zones[i].time, TIME_DATE),
                               g_zones[i].open, g_zones[i].close);
      if(ObjectFind(0, ln) < 0)
         ObjectCreate(0, ln, OBJ_TEXT, 0, g_zones[i].time, g_zones[i].range_high + cp * 0.003);
      ObjectSetString(0, ln, OBJPROP_TEXT, lt);
      ObjectSetInteger(0, ln, OBJPROP_COLOR, zc);
      ObjectSetInteger(0, ln, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, ln, OBJPROP_SELECTABLE, false);
      
      shown++;
   }
}

//+------------------------------------------------------------------+
//| Draw panel — MOVABLE (user can drag background)                  |
//+------------------------------------------------------------------+
void DrawPanel()
{
   // Only delete text objects, NOT the background (so user can drag it)
   ObjectsDeleteAll(0, "RSI_PNL_T");
   
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(price <= 0) return;
   
   string bg = "RSI_PNL_BG";
   
   // Check if background exists (created before or dragged by user)
   if(ObjectFind(0, bg) >= 0)
   {
      // Read current position (user may have moved it)
      g_panel_x = (int)ObjectGetInteger(0, bg, OBJPROP_XDISTANCE);
      g_panel_y = (int)ObjectGetInteger(0, bg, OBJPROP_YDISTANCE);
      g_panel_corner = (ENUM_BASE_CORNER)ObjectGetInteger(0, bg, OBJPROP_CORNER);
      // Update size in case it changed
      ObjectSetInteger(0, bg, OBJPROP_XSIZE, PANEL_W);
      ObjectSetInteger(0, bg, OBJPROP_YSIZE, PANEL_H);
   }
   else
   {
      // Create new background
      ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, bg, OBJPROP_CORNER, g_panel_corner);
      ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, g_panel_x);
      ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, g_panel_y);
      ObjectSetInteger(0, bg, OBJPROP_XSIZE, PANEL_W);
      ObjectSetInteger(0, bg, OBJPROP_YSIZE, PANEL_H);
      ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, InpPanelBgColor);
      ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, bg, OBJPROP_COLOR, C'140,135,130');
      ObjectSetInteger(0, bg, OBJPROP_WIDTH, 2);
      // IMPORTANT: selectable = true so user can DRAG it
      ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, true);
      ObjectSetInteger(0, bg, OBJPROP_SELECTED, false);
      ObjectSetInteger(0, bg, OBJPROP_BACK, false);
   }
   
   // Text colors (use input colors for theme compatibility)
   color cT = InpPanelTextColor;
   color cL = C'100,95,90';
   color cV = C'60,55,50';
   color cR = C'91,140,90';   // green
   color cD = C'192,138,90';  // peach
   color cP = C'181,107,107'; // red
   color cA = C'200,80,80';
   color cB = C'91,140,90';
   color cS = C'181,107,107';
   color cM = C'150,145,140';
   color cBl = C'80,80,110';
   string f = "Tahoma";
   
   int x = g_panel_x + 10;
   int y = g_panel_y + 6;
   
   PT("t0", x, y, "استراتژی RSI طلا - M30", cT, 11, f); y += LH + 4;
   PT("t1", x, y, StringFormat("قیمت: %.2f", price), cV, 10, f); y += LH;
   
   color rc = cV;
   if(g_rsi > 60) rc = cP; else if(g_rsi < 40) rc = cR;
   PT("t2", x, y, StringFormat("RSI(30): %.2f", g_rsi), rc, 10, f); y += LH;
   PT("t3", x, y, StringFormat("RSI(14): %.2f", g_rsi14), cM, 9, f); y += LH + 4;
   
   if(g_current_zone > 0)
      PT("t4", x, y, StringFormat("در زون %d (%d کندل)", g_current_zone, g_candles_in_zone), cD, 10, f);
   else
   {
      double d40 = MathAbs(g_rsi - 40);
      double d60 = MathAbs(g_rsi - 60);
      int nr = d40 < d60 ? 40 : 60;
      PT("t4", x, y, StringFormat("نزدیک‌تر: سطح %d (%.1f)", nr, MathMin(d40, d60)), cM, 10, f);
   }
   y += LH + 4;
   
   PT("t5", x, y, "--- پیش‌بینی ---", cT, 9, f); y += LH - 2;
   
   double r40,d40_2,p40, r60,d60_2,p60;
   PredictForLevel(40, r40, d40_2, p40);
   PredictForLevel(60, r60, d60_2, p60);
   int likely = MathAbs(g_rsi - 40) < MathAbs(g_rsi - 60) ? 40 : 60;
   
   PT("t6", x, y, StringFormat("محتمل‌تر: سطح %d", likely), cBl, 10, f); y += LH - 2;
   
   double rev = likely == 40 ? r40 : r60;
   double div = likely == 40 ? d40_2 : d60_2;
   double pas = likely == 40 ? p40 : p60;
   PT("t7", x, y, StringFormat("  برگشت:     %.0f%%", rev * 100), cR, 9, f); y += LH - 4;
   PT("t8", x, y, StringFormat("  واگرایی:   %.0f%%", div * 100), cD, 9, f); y += LH - 4;
   PT("t9", x, y, StringFormat("  گذشتن:     %.0f%%", pas * 100), cP, 9, f); y += LH;
   
   PT("t10", x, y, "--- زون‌های دوجی ---", cT, 9, f); y += LH - 2;
   
   int nidx = -1; double ndist = 999999; bool inside = false;
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].active)
      {
         PT("t11", x, y, StringFormat("داخل زون %s!", g_zones[i].type==1?"هفتگی":"روزانه"), cA, 10, f);
         y += LH - 2; inside = true;
      }
      double dist = MathAbs(g_zones[i].midpoint - price);
      if(dist < ndist && !g_zones[i].active) { ndist = dist; nidx = i; }
   }
   
   if(!inside && nidx >= 0)
   {
      PT("t12", x, y, StringFormat("نزدیک‌ترین: %s @ %.2f", g_zones[nidx].type==1?"هفتگی":"روزانه", g_zones[nidx].midpoint), cL, 9, f);
      y += LH - 4;
      PT("t13", x, y, StringFormat("  فاصله: %.0f pip (%.2f%%)", ndist*10, ndist/price*100), cM, 9, f);
      y += LH - 4;
      PT("t14", x, y, StringFormat("  O:%.2f  C:%.2f", g_zones[nidx].open, g_zones[nidx].close), cM, 9, f);
      y += LH;
   }
   else if(!inside)
   {
      PT("t12", x, y, StringFormat("زون‌های یافت شده: %d", g_zone_count), cM, 9, f);
      y += LH;
   }
   
   if(g_current_zone > 0)
   {
      y += 4;
      PT("t15", x, y, "--- تیکت ورود ---", cT, 9, f); y += LH - 2;
      string dir = ""; color dc = cM; double sl = 0, tp = 0;
      if(g_current_zone == 60) { dir = "فروش (SELL)"; dc = cS; sl = price + price*0.004; tp = price - price*0.008; }
      else if(g_current_zone == 40) { dir = "خرید (BUY)"; dc = cB; sl = price - price*0.004; tp = price + price*0.008; }
      if(dir != "")
      {
         PT("t16", x, y, StringFormat("جهت: %s", dir), dc, 10, f); y += LH - 2;
         PT("t17", x, y, StringFormat("ورود: %.2f", price), cV, 9, f); y += LH - 4;
         PT("t18", x, y, StringFormat("ضرر: %.2f", sl), cS, 9, f); y += LH - 4;
         PT("t19", x, y, StringFormat("سود: %.2f", tp), cB, 9, f); y += LH - 4;
         double rr = MathAbs(tp - price) / MathAbs(price - sl);
         PT("t20", x, y, StringFormat("R:R = 1:%.2f", rr), cD, 9, f); y += LH;
      }
   }
   
   y += 4;
   PT("t21", x, y, StringFormat("سیگنال‌ها: %d", g_signal_count), cM, 8, f); y += LH - 4;
   
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   int th = (dt.hour + 3) % 24;
   string ss = "شب";
   if(th >= 6 && th < 12) ss = "صبح (آسیا)";
   else if(th >= 12 && th < 17) ss = "ظهر (اروپا)";
   else if(th >= 17 && th < 22) ss = "عصر (آمریکا)";
   PT("t22", x, y, StringFormat("سشن: %s", ss), cM, 8, f); y += LH - 4;
   PT("t23", x, y, StringFormat("بروز: %s", TimeToString(TimeCurrent(), TIME_MINUTES)), cM, 8, f);
   
   // Hint at bottom
   y += LH + 4;
   PT("t24", x, y, "» برای جابجایی پنل، آن را بکشید", cM, 7, f);
}

//--- Helper: Panel Text (uses prefix RSI_PNL_T so they get deleted on redraw)
void PT(string id, int x, int y, string text, color clr, int sz, string font)
{
   string name = "RSI_PNL_T_" + id;
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_CORNER, g_panel_corner);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, sz);
   ObjectSetString(0, name, OBJPROP_FONT, font);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
}

//+------------------------------------------------------------------+
void PredictForLevel(int level, double &rev, double &div, double &pas)
{
   CatMeans m[3];
   if(level == 40) { m[0]=means_40[0]; m[1]=means_40[1]; m[2]=means_40[2]; }
   else { m[0]=means_60[0]; m[1]=means_60[1]; m[2]=means_60[2]; }
   
   double dist[3];
   for(int i = 0; i < 3; i++)
   {
      double dc = MathPow((g_candles_in_zone - m[i].cz) / 3.0, 2);
      double dv = MathPow((g_rsi_vel_10 - m[i].vel) / 4.0, 2);
      dist[i] = MathSqrt(dc * 3.0 + dv);
   }
   double inv[3], sum = 0;
   for(int i = 0; i < 3; i++) { inv[i] = 1.0 / (dist[i] + 0.3); sum += inv[i]; }
   double p[3], sp = 0;
   for(int i = 0; i < 3; i++) { p[i] = base_rates[i] * (inv[i] / (sum / 3.0)); sp += p[i]; }
   rev = p[0] / sp; div = p[1] / sp; pas = p[2] / sp;
}

//+------------------------------------------------------------------+
void CheckAlerts()
{
   if(!InpEnableAlerts) return;
   datetime now = TimeCurrent();
   
   if(InpAlertOnRSI && g_current_zone > 0 && now - g_last_alert_rsi > 300)
   {
      double r, d, p;
      PredictForLevel(g_current_zone, r, d, p);
      Alert(StringFormat("RSI وارد زون %d شد! (RSI=%.2f, %d کندل)\nبرگشت: %.0f%% | واگرایی: %.0f%% | گذشتن: %.0f%%",
                         g_current_zone, g_rsi, g_candles_in_zone, r*100, d*100, p*100));
      g_last_alert_rsi = now;
   }
   
   if(InpAlertOnZone)
   {
      for(int i = 0; i < g_zone_count; i++)
      {
         if(g_zones[i].active && now - g_last_alert_zone > 300)
         {
            Alert(StringFormat("قیمت وارد زون دوجی %s شد!\nزون: %.2f - %.2f\nتاریخ: %s",
                               g_zones[i].type == 1 ? "هفتگی" : "روزانه",
                               g_zones[i].range_low, g_zones[i].range_high,
                               TimeToString(g_zones[i].time, TIME_DATE)));
            g_last_alert_zone = now;
            break;
         }
      }
   }
   
   if(InpAlertOnPattern && g_current_zone > 0 && now - g_last_alert_rsi > 180)
   {
      string pat = DetectM5Pattern();
      if(pat != "")
      {
         Alert(StringFormat("الگوی M5: %s\nRSI در زون %d - جهت: %s",
                            pat, g_current_zone, g_current_zone == 40 ? "خرید" : "فروش"));
         g_last_alert_rsi = now;
      }
   }
}

//+------------------------------------------------------------------+
string DetectM5Pattern()
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, PERIOD_M5, 0, 3, r) < 3) return "";
   double body = MathAbs(r[0].close - r[0].open);
   double range = r[0].high - r[0].low;
   if(range <= 0) return "";
   double uw = r[0].high - MathMax(r[0].open, r[0].close);
   double lw = MathMin(r[0].open, r[0].close) - r[0].low;
   if(body <= range * 0.10) return "Doji";
   if(lw >= range * 0.6 && body <= range * 0.35) return "Bullish Pin Bar";
   if(uw >= range * 0.6 && body <= range * 0.35) return "Bearish Pin Bar";
   if(r[1].close < r[1].open && r[0].close > r[0].open &&
      MathMax(r[0].open, r[0].close) >= MathMax(r[1].open, r[1].close) &&
      MathMin(r[0].open, r[0].close) <= MathMin(r[1].open, r[1].close))
      return "Bullish Engulfing";
   if(r[1].close > r[1].open && r[0].close < r[0].open &&
      MathMax(r[0].open, r[0].close) >= MathMax(r[1].open, r[1].close) &&
      MathMin(r[0].open, r[0].close) <= MathMin(r[1].open, r[1].close))
      return "Bearish Engulfing";
   return "";
}
//+------------------------------------------------------------------+
