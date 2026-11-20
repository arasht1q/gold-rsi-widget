//+------------------------------------------------------------------+
//|                                         Gold_RSI_Strategy.mq5    |
//|     RSI(30) M30 Strategy - Chart Window - Persian - Signals      |
//+------------------------------------------------------------------+
#property copyright "Z.ai - Gold RSI Widget"
#property link      "https://github.com/arasht1q/gold-rsi-widget"
#property version   "1.30"
#property description "RSI(30) M30 strategy - Doji zones - Entry signals - Persian"
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//--- Input Parameters
input int      InpRSIPeriod        = 30;       // RSI(30) period
input int      InpRSI14Period      = 14;       // RSI(14) period (reference)
input double   InpLevelOversold    = 40.0;     // Oversold level
input double   InpLevelOverbought  = 60.0;     // Overbought level
input double   InpZoneTolerance    = 1.0;      // Zone tolerance (+/- units)
input double   InpDojiThreshold    = 0.10;     // Doji threshold (10%)
input int      InpLookbackDays     = 180;      // Days to scan for daily Dojis
input int      InpLookbackWeeks    = 52;       // Weeks to scan for weekly Dojis
input double   InpZoneFilter       = 15.0;     // Zone filter (% from current price)
input int      InpSignalCount      = 50;       // Past entry signals to show
input bool     InpShowZones        = true;     // Draw Doji zones
input bool     InpShowDailyZones   = true;     // Show daily Doji zones
input bool     InpShowWeeklyZones  = true;     // Show weekly Doji zones
input color    InpWeeklyZoneColor  = C'245,184,122'; // Weekly zone (soft orange)
input color    InpDailyZoneColor   = C'180,180,185'; // Daily zone (soft gray)
input bool     InpShowPanel        = true;     // Show info panel
input bool     InpShowSignals      = true;     // Show entry signals
input int      InpPanelCorner      = 0;        // Panel corner: 0=top-left, 1=top-right
input bool     InpEnableAlerts     = true;     // Enable alerts
input bool     InpAlertOnRSI       = true;     // Alert on RSI zone entry
input bool     InpAlertOnZone      = true;     // Alert on price entering Doji zone
input bool     InpAlertOnPattern   = true;     // Alert on M5 pattern

//--- Global variables
int rsi30_handle = INVALID_HANDLE;
int rsi14_handle = INVALID_HANDLE;
double g_rsi = 0;
double g_rsi14 = 0;
double g_rsi_vel_10 = 0;
int g_candles_in_zone = 0;
int g_current_zone = 0;
datetime g_last_alert_rsi = 0;
datetime g_last_alert_zone = 0;

//--- Zone structure
struct DojiZone
{
   datetime time;
   double   open;
   double   close;
   double   midpoint;
   double   range_high;
   double   range_low;
   int      type;
   bool     active;
};

DojiZone g_zones[];
int g_zone_count = 0;

//--- Signal structure
struct EntrySignal
{
   datetime time;
   double   price;
   int      level;
   int      direction;
};

EntrySignal g_signals[];
int g_signal_count = 0;

//--- Prediction means
struct CatMeans { double cz; double vel; double vol; };
CatMeans means_40[3];
CatMeans means_60[3];
double base_rates[3] = {0.329, 0.210, 0.461};

//--- Panel constants
#define PANEL_W   250
#define PANEL_H   400
#define LH        16

//--- Pastel colors
color C_TITLE = C'80,75,70';
color C_LABEL = C'120,115,110';
color C_VALUE = C'50,45,40';
color C_REV   = C'91,140,90';
color C_DIV   = C'192,138,90';
color C_PASS  = C'181,107,107';
color C_ALERT = C'200,100,100';
color C_BUY   = C'91,140,90';
color C_SELL  = C'181,107,107';
color C_MUTED = C'160,155,150';
color C_BLUE  = C'90,90,120';

//+------------------------------------------------------------------+
int OnInit()
{
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
   
   // Set chart to show objects properly
   ChartSetInteger(0, CHART_SHOW_OBJECT_DESCR, true);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, "RSI_ZONE_");
   ObjectsDeleteAll(0, "RSI_PANEL_");
   ObjectsDeleteAll(0, "RSI_SIG_");
   if(rsi30_handle != INVALID_HANDLE) IndicatorRelease(rsi30_handle);
   if(rsi14_handle != INVALID_HANDLE) IndicatorRelease(rsi14_handle);
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
   
   Print("Scanned: ", g_zone_count, " Doji zones found");
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
   
   Print("Found ", g_signal_count, " historical signals");
}

//+------------------------------------------------------------------+
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
      string name = "RSI_SIG_" + IntegerToString(i);
      int arrow_code = g_signals[i].direction == 1 ? 233 : 234;
      color clr = g_signals[i].direction == 1 ? C_BUY : C_SELL;
      
      double offset = g_signals[i].price * 0.003;
      double pp = g_signals[i].direction == 1 ? 
                  g_signals[i].price - offset : 
                  g_signals[i].price + offset;
      
      if(ObjectFind(0, name) < 0)
         ObjectCreate(0, name, OBJ_ARROW, 0, g_signals[i].time, pp);
      
      ObjectSetInteger(0, name, OBJPROP_ARROWCODE, arrow_code);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      
      string ln = "RSI_SIG_L_" + IntegerToString(i);
      string lt = StringFormat("%s%d", g_signals[i].direction == 1 ? "B" : "S", g_signals[i].level);
      
      if(ObjectFind(0, ln) < 0)
         ObjectCreate(0, ln, OBJ_TEXT, 0, g_signals[i].time, pp);
      ObjectSetString(0, ln, OBJPROP_TEXT, lt);
      ObjectSetInteger(0, ln, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, ln, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, ln, OBJPROP_SELECTABLE, false);
   }
}

//+------------------------------------------------------------------+
void DrawZonesOnChart()
{
   double cp = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(cp <= 0) return;
   
   ObjectsDeleteAll(0, "RSI_ZONE_");
   
   // Use configurable filter
   double fw = cp * (InpZoneFilter / 100.0);
   
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].time >= TimeCurrent()) continue;
      if(MathAbs(g_zones[i].midpoint - cp) > fw) continue;
      
      double tol = cp * 0.002;
      bool inside = (cp >= g_zones[i].range_low - tol && cp <= g_zones[i].range_high + tol);
      g_zones[i].active = inside;
      
      string name = "RSI_ZONE_" + IntegerToString(i);
      datetime t2 = TimeCurrent() + PeriodSeconds(PERIOD_M30) * 200;
      
      if(ObjectFind(0, name) < 0)
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, g_zones[i].time, g_zones[i].range_high, t2, g_zones[i].range_low);
      
      color zc = g_zones[i].type == 1 ? InpWeeklyZoneColor : InpDailyZoneColor;
      if(inside) zc = C'255,220,80';
      
      ObjectSetInteger(0, name, OBJPROP_COLOR, zc);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
      
      // Label
      string ln = "RSI_ZONE_L_" + IntegerToString(i);
      string lt = StringFormat("%s %s | O:%.2f C:%.2f",
                               g_zones[i].type == 1 ? "W" : "D",
                               TimeToString(g_zones[i].time, TIME_DATE),
                               g_zones[i].open, g_zones[i].close);
      if(ObjectFind(0, ln) < 0)
         ObjectCreate(0, ln, OBJ_TEXT, 0, g_zones[i].time, g_zones[i].range_high + cp * 0.002);
      ObjectSetString(0, ln, OBJPROP_TEXT, lt);
      ObjectSetInteger(0, ln, OBJPROP_COLOR, zc);
      ObjectSetInteger(0, ln, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, ln, OBJPROP_SELECTABLE, false);
   }
}

//+------------------------------------------------------------------+
void DrawPanel()
{
   ObjectsDeleteAll(0, "RSI_PANEL_");
   
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(price <= 0) return;
   
   // Choose corner based on input
   ENUM_BASE_CORNER corner = InpPanelCorner == 0 ? CORNER_LEFT_UPPER : CORNER_RIGHT_UPPER;
   int bg_x = InpPanelCorner == 0 ? 5 : 5;
   int txt_x = InpPanelCorner == 0 ? 12 : 12;
   
   // Background
   string bg = "RSI_PANEL_BG";
   if(ObjectFind(0, bg) < 0)
      ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bg, OBJPROP_CORNER, corner);
   ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, bg_x);
   ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, 20);
   ObjectSetInteger(0, bg, OBJPROP_XSIZE, PANEL_W);
   ObjectSetInteger(0, bg, OBJPROP_YSIZE, PANEL_H);
   ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, C'250,250,248');
   ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bg, OBJPROP_COLOR, C'180,175,170');
   ObjectSetInteger(0, bg, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, bg, OBJPROP_BACK, false);
   
   int x = txt_x;
   int y = 26;
   string f = "Tahoma";
   
   DrawText("p0", x, y, "استراتژی RSI طلا - M30", C_TITLE, 11, f, corner);
   y += LH + 4;
   
   DrawText("p1", x, y, StringFormat("قیمت: %.2f", price), C_VALUE, 10, f, corner);
   y += LH;
   
   color rsi30_c = C_VALUE;
   if(g_rsi > 60) rsi30_c = C_PASS;
   else if(g_rsi < 40) rsi30_c = C_REV;
   DrawText("p2", x, y, StringFormat("RSI(30): %.2f", g_rsi), rsi30_c, 10, f, corner);
   y += LH;
   
   DrawText("p3", x, y, StringFormat("RSI(14): %.2f", g_rsi14), C_MUTED, 9, f, corner);
   y += LH + 4;
   
   if(g_current_zone > 0)
   {
      DrawText("p4", x, y, StringFormat("در زون %d (%d کندل)", g_current_zone, g_candles_in_zone), C_DIV, 10, f, corner);
   }
   else
   {
      double d40 = MathAbs(g_rsi - 40);
      double d60 = MathAbs(g_rsi - 60);
      int near = d40 < d60 ? 40 : 60;
      DrawText("p4", x, y, StringFormat("نزدیک‌تر: سطح %d (%.1f)", near, MathMin(d40, d60)), C_MUTED, 10, f, corner);
   }
   y += LH + 4;
   
   DrawText("p5", x, y, "--- پیش‌بینی ---", C_TITLE, 9, f, corner);
   y += LH - 2;
   
   double r40, d40_2, p40;
   double r60, d60_2, p60;
   PredictForLevel(40, r40, d40_2, p40);
   PredictForLevel(60, r60, d60_2, p60);
   
   double dd40 = MathAbs(g_rsi - 40);
   double dd60 = MathAbs(g_rsi - 60);
   int likely = dd40 < dd60 ? 40 : 60;
   
   DrawText("p6", x, y, StringFormat("محتمل‌تر: سطح %d", likely), C_BLUE, 10, f, corner);
   y += LH - 2;
   
   double rev = likely == 40 ? r40 : r60;
   double div = likely == 40 ? d40_2 : d60_2;
   double pas = likely == 40 ? p40 : p60;
   
   DrawText("p7", x, y, StringFormat("  برگشت:     %.0f%%", rev * 100), C_REV, 9, f, corner);
   y += LH - 4;
   DrawText("p8", x, y, StringFormat("  واگرایی:   %.0f%%", div * 100), C_DIV, 9, f, corner);
   y += LH - 4;
   DrawText("p9", x, y, StringFormat("  گذشتن:     %.0f%%", pas * 100), C_PASS, 9, f, corner);
   y += LH;
   
   DrawText("p10", x, y, "--- زون‌های دوجی ---", C_TITLE, 9, f, corner);
   y += LH - 2;
   
   int nidx = -1;
   double ndist = 999999;
   bool inside = false;
   
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].active)
      {
         DrawText("p11", x, y, StringFormat("داخل زون %s!", g_zones[i].type == 1 ? "هفتگی" : "روزانه"), C_ALERT, 10, f, corner);
         y += LH - 2;
         inside = true;
      }
      double dist = MathAbs(g_zones[i].midpoint - price);
      if(dist < ndist && !g_zones[i].active)
      {
         ndist = dist;
         nidx = i;
      }
   }
   
   if(!inside && nidx >= 0)
   {
      DrawText("p12", x, y, StringFormat("نزدیک‌ترین: %s @ %.2f", g_zones[nidx].type == 1 ? "هفتگی" : "روزانه", g_zones[nidx].midpoint), C_LABEL, 9, f, corner);
      y += LH - 4;
      DrawText("p13", x, y, StringFormat("  فاصله: %.0f pip (%.2f%%)", ndist * 10, ndist / price * 100), C_MUTED, 9, f, corner);
      y += LH - 4;
      DrawText("p14", x, y, StringFormat("  O:%.2f  C:%.2f", g_zones[nidx].open, g_zones[nidx].close), C_MUTED, 9, f, corner);
      y += LH;
   }
   else if(!inside)
   {
      DrawText("p12", x, y, StringFormat("زون‌های یافت شده: %d", g_zone_count), C_MUTED, 9, f, corner);
      y += LH;
   }
   
   if(g_current_zone > 0)
   {
      y += 4;
      DrawText("p15", x, y, "--- تیکت ورود ---", C_TITLE, 9, f, corner);
      y += LH - 2;
      
      string dir = "";
      color dc = C_MUTED;
      double sl = 0, tp = 0;
      
      if(g_current_zone == 60)
      {
         dir = "فروش (SELL)"; dc = C_SELL;
         sl = price + price * 0.004;
         tp = price - price * 0.008;
      }
      else if(g_current_zone == 40)
      {
         dir = "خرید (BUY)"; dc = C_BUY;
         sl = price - price * 0.004;
         tp = price + price * 0.008;
      }
      
      if(dir != "")
      {
         DrawText("p16", x, y, StringFormat("جهت: %s", dir), dc, 10, f, corner);
         y += LH - 2;
         DrawText("p17", x, y, StringFormat("ورود: %.2f", price), C_VALUE, 9, f, corner);
         y += LH - 4;
         DrawText("p18", x, y, StringFormat("ضرر: %.2f", sl), C_SELL, 9, f, corner);
         y += LH - 4;
         DrawText("p19", x, y, StringFormat("سود: %.2f", tp), C_BUY, 9, f, corner);
         y += LH - 4;
         double rr = MathAbs(tp - price) / MathAbs(price - sl);
         DrawText("p20", x, y, StringFormat("R:R = 1:%.2f", rr), C_DIV, 9, f, corner);
         y += LH;
      }
   }
   
   y += 4;
   DrawText("p21", x, y, StringFormat("سیگنال‌ها: %d", g_signal_count), C_MUTED, 8, f, corner);
   y += LH - 4;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int th = (dt.hour + 3) % 24;
   string sess = "شب";
   if(th >= 6 && th < 12) sess = "صبح (آسیا)";
   else if(th >= 12 && th < 17) sess = "ظهر (اروپا)";
   else if(th >= 17 && th < 22) sess = "عصر (آمریکا)";
   
   DrawText("p22", x, y, StringFormat("سشن: %s", sess), C_MUTED, 8, f, corner);
   y += LH - 4;
   DrawText("p23", x, y, StringFormat("بروز: %s", TimeToString(TimeCurrent(), TIME_MINUTES)), C_MUTED, 8, f, corner);
}

//+------------------------------------------------------------------+
void DrawText(string name, int x, int y, string text, color clr, int size, string font, ENUM_BASE_CORNER corner)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_CORNER, corner);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
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
   
   rev = p[0] / sp;
   div = p[1] / sp;
   pas = p[2] / sp;
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
