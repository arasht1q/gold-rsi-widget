//+------------------------------------------------------------------+
//|                                         Gold_RSI_Strategy.mq5    |
//|                  RSI(30) M30 Strategy with Doji Zones for MT5    |
//|                                                                  |
//|  Features:                                                       |
//|  - RSI(30) on M30 with 40/60 levels                              |
//|  - Daily & Weekly Doji zone detection and drawing               |
//|  - Prediction panel (reversal/divergence/pass-through %)        |
//|  - Entry ticket with SL/TP                                       |
//|  - M5 candle pattern detection                                   |
//|  - Alerts when RSI enters zone or price enters Doji zone        |
//|                                                                  |
//|  Based on 2-year statistical backtest (1328 events)              |
//+------------------------------------------------------------------+
#property copyright "Z.ai - Gold RSI Widget"
#property link      "https://github.com/arasht1q/gold-rsi-widget"
#property version   "1.00"
#property description "RSI(30) M30 strategy with Doji zones - based on 2-year backtest"
#property indicator_separate_window
#property indicator_buffers 1
#property indicator_plots   1

#property indicator_label1  "RSI(30)"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDarkSlateGray
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

#property indicator_level1  40.0
#property indicator_level2  60.0
#property indicator_levelcolor clrLightGray
#property indicator_levelstyle STYLE_DASH

//--- Input Parameters
input group "=== RSI Settings ==="
input int      InpRSIPeriod        = 30;       // RSI period
input double   InpLevelOversold    = 40.0;     // Oversold level
input double   InpLevelOverbought  = 60.0;     // Overbought level
input double   InpZoneTolerance    = 1.0;      // Zone tolerance (±units)

input group "=== Doji Zone Settings ==="
input double   InpDojiThreshold    = 0.10;     // Doji body/range threshold (10%)
input int      InpLookbackDays     = 90;       // Days to scan for daily Dojis
input int      InpLookbackWeeks    = 26;       // Weeks to scan for weekly Dojis
input bool     InpShowZones        = true;     // Draw Doji zones on chart
input bool     InpShowDailyZones   = true;     // Show daily Doji zones
input bool     InpShowWeeklyZones  = true;     // Show weekly Doji zones
input color    InpWeeklyZoneColor  = clrOrange; // Weekly zone color
input color    InpDailyZoneColor   = clrGray;  // Daily zone color

input group "=== Panel & Alerts ==="
input bool     InpShowPanel        = true;     // Show info panel
input bool     InpEnableAlerts     = true;     // Enable alerts
input bool     InpAlertOnRSI       = true;     // Alert when RSI enters zone
input bool     InpAlertOnZone      = true;     // Alert when price enters Doji zone
input bool     InpAlertOnPattern   = true;     // Alert on M5 pattern when RSI in zone

//--- Indicator buffer
double RSI_Buffer[];

//--- Global variables
int rsi_handle = INVALID_HANDLE;
double g_rsi = 0;
double g_rsi_vel_10 = 0;
double g_rsi_vel_5 = 0;
int g_candles_in_zone = 0;
int g_current_zone = 0; // 0 = none, 40, 60
datetime g_last_alert_rsi = 0;
datetime g_last_alert_zone = 0;

//--- Zone structure
struct DojiZone
{
   datetime time;
   double   open;
   double   close;
   double   high;
   double   low;
   double   midpoint;
   double   range_high;
   double   range_low;
   int      type; // 0 = daily, 1 = weekly
   bool     active; // is price currently inside this zone?
};

DojiZone g_zones[];
int g_zone_count = 0;

//--- Prediction means (from 2-year backtest)
struct CategoryMeans
{
   double candles_in_zone;
   double rsi_vel_10;
   double vol_ratio;
};

CategoryMeans means_40[3]; // 0=REVERSAL, 1=DIVERGENCE, 2=PASS_THROUGH
CategoryMeans means_60[3];

// Base rates
double base_rates[3] = {0.329, 0.210, 0.461}; // REVERSAL, DIVERGENCE, PASS_THROUGH

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- Set up indicator buffer
   SetIndexBuffer(0, RSI_Buffer, INDICATOR_DATA);
   PlotIndexSetString(0, PLOT_LABEL, "RSI(" + IntegerToString(InpRSIPeriod) + ")");
   
   //--- Set indicator levels
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 0, InpLevelOversold);
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 1, InpLevelOverbought);
   IndicatorSetString(INDICATOR_SHORTNAME, "RSI(30) M30 - Gold Strategy");
   
   //--- Get RSI handle
   rsi_handle = iRSI(_Symbol, PERIOD_M30, InpRSIPeriod, PRICE_CLOSE);
   if(rsi_handle == INVALID_HANDLE)
   {
      Print("Failed to create RSI handle");
      return(INIT_FAILED);
   }
   
   //--- Initialize prediction means from backtest
   // Level 40 (approaching from above)
   means_40[0].candles_in_zone = 1.61; means_40[0].rsi_vel_10 = -2.03; means_40[0].vol_ratio = 1.07; // REVERSAL
   means_40[1].candles_in_zone = 2.78; means_40[1].rsi_vel_10 = -3.45; means_40[1].vol_ratio = 1.02; // DIVERGENCE
   means_40[2].candles_in_zone = 1.78; means_40[2].rsi_vel_10 = -3.40; means_40[2].vol_ratio = 1.10; // PASS_THROUGH
   
   // Level 60 (approaching from below)
   means_60[0].candles_in_zone = 1.54; means_60[0].rsi_vel_10 = 1.67; means_60[0].vol_ratio = 1.07; // REVERSAL
   means_60[1].candles_in_zone = 2.17; means_60[1].rsi_vel_10 = 3.05; means_60[1].vol_ratio = 1.02; // DIVERGENCE
   means_60[2].candles_in_zone = 1.83; means_60[2].rsi_vel_10 = 2.16; means_60[2].vol_ratio = 1.10; // PASS_THROUGH
   
   //--- Set timer for periodic updates (every 30 seconds)
   EventSetTimer(30);
   
   //--- Scan for Doji zones
   ScanDojiZones();
   
   Print("Gold RSI Strategy indicator initialized");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   //--- Clean up all drawn objects
   ObjectsDeleteAll(0, "RSI_ZONE_");
   ObjectsDeleteAll(0, "RSI_PANEL_");
   ObjectsDeleteAll(0, "RSI_LINE_");
   
   if(rsi_handle != INVALID_HANDLE)
      IndicatorRelease(rsi_handle);
   
   Print("Gold RSI Strategy indicator removed");
}

//+------------------------------------------------------------------+
//| Timer function - periodic updates                                |
//+------------------------------------------------------------------+
void OnTimer()
{
   //--- Update Doji zones (in case new daily/weekly candle formed)
   ScanDojiZones();
   
   //--- Update panel
   if(InpShowPanel)
      DrawPanel();
   
   //--- Check for alerts
   CheckAlerts();
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   //--- Copy RSI data
   int copied = CopyBuffer(rsi_handle, 0, 0, rates_total, RSI_Buffer);
   if(copied <= 0)
      return(0);
   
   //--- Get current RSI value
   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(rsi_handle, 0, 0, 15, rsi) > 0)
   {
      g_rsi = rsi[0];
      if(ArraySize(rsi) >= 11)
         g_rsi_vel_10 = rsi[0] - rsi[10];
      if(ArraySize(rsi) >= 6)
         g_rsi_vel_5 = rsi[0] - rsi[5];
      
      //--- Count candles in zone
      UpdateCandlesInZone(rsi);
   }
   
   //--- Draw zones on main chart
   if(InpShowZones)
      DrawZonesOnChart();
   
   //--- Draw info panel
   if(InpShowPanel)
      DrawPanel();
   
   return(rates_total);
}

//+------------------------------------------------------------------+
//| Update candles in zone count                                     |
//+------------------------------------------------------------------+
void UpdateCandlesInZone(double &rsi[])
{
   g_candles_in_zone = 0;
   g_current_zone = 0;
   
   double lo40 = InpLevelOversold - InpZoneTolerance;
   double hi40 = InpLevelOversold + InpZoneTolerance;
   double lo60 = InpLevelOverbought - InpZoneTolerance;
   double hi60 = InpLevelOverbought + InpZoneTolerance;
   
   //--- Check if currently in zone 40
   if(rsi[0] >= lo40 && rsi[0] <= hi40)
   {
      g_current_zone = 40;
      for(int i = 0; i < ArraySize(rsi) && i < 50; i++)
      {
         if(rsi[i] >= lo40 && rsi[i] <= hi40)
            g_candles_in_zone++;
         else
            break;
      }
   }
   //--- Check if currently in zone 60
   else if(rsi[0] >= lo60 && rsi[0] <= hi60)
   {
      g_current_zone = 60;
      for(int i = 0; i < ArraySize(rsi) && i < 50; i++)
      {
         if(rsi[i] >= lo60 && rsi[i] <= hi60)
            g_candles_in_zone++;
         else
            break;
      }
   }
}

//+------------------------------------------------------------------+
//| Scan for Doji candles on daily and weekly timeframes             |
//+------------------------------------------------------------------+
void ScanDojiZones()
{
   g_zone_count = 0;
   ArrayResize(g_zones, 0);
   
   //--- Scan daily Dojis
   if(InpShowDailyZones)
   {
      MqlRates daily[];
      ArraySetAsSeries(daily, true);
      int copied = CopyRates(_Symbol, PERIOD_D1, 0, InpLookbackDays + 1, daily);
      if(copied > 0)
      {
         // Skip the last (current/incomplete) day
         for(int i = 1; i < copied; i++)
         {
            double range = daily[i].high - daily[i].low;
            if(range <= 0) continue;
            double body = MathAbs(daily[i].close - daily[i].open);
            if(body <= InpDojiThreshold * range)
            {
               AddZone(daily[i].time, daily[i].open, daily[i].close, 
                       daily[i].high, daily[i].low, 0); // 0 = daily
            }
         }
      }
   }
   
   //--- Scan weekly Dojis
   if(InpShowWeeklyZones)
   {
      MqlRates weekly[];
      ArraySetAsSeries(weekly, true);
      int copied = CopyRates(_Symbol, PERIOD_W1, 0, InpLookbackWeeks + 1, weekly);
      if(copied > 0)
      {
         for(int i = 1; i < copied; i++)
         {
            double range = weekly[i].high - weekly[i].low;
            if(range <= 0) continue;
            double body = MathAbs(weekly[i].close - weekly[i].open);
            if(body <= InpDojiThreshold * range)
            {
               AddZone(weekly[i].time, weekly[i].open, weekly[i].close,
                       weekly[i].high, weekly[i].low, 1); // 1 = weekly
            }
         }
      }
   }
   
   Print("Found ", g_zone_count, " Doji zones (", 
         CountZonesByType(0), " daily, ", CountZonesByType(1), " weekly)");
}

//+------------------------------------------------------------------+
//| Add a zone to the zones array                                    |
//+------------------------------------------------------------------+
void AddZone(datetime time, double op, double cl, double hi, double lo, int type)
{
   g_zone_count++;
   ArrayResize(g_zones, g_zone_count);
   
   int idx = g_zone_count - 1;
   g_zones[idx].time = time;
   g_zones[idx].open = op;
   g_zones[idx].close = cl;
   g_zones[idx].high = hi;
   g_zones[idx].low = lo;
   g_zones[idx].midpoint = (op + cl) / 2.0;
   g_zones[idx].range_high = MathMax(op, cl);
   g_zones[idx].range_low = MathMin(op, cl);
   g_zones[idx].type = type;
   g_zones[idx].active = false;
}

//+------------------------------------------------------------------+
//| Count zones by type                                              |
//+------------------------------------------------------------------+
int CountZonesByType(int type)
{
   int count = 0;
   for(int i = 0; i < g_zone_count; i++)
      if(g_zones[i].type == type) count++;
   return count;
}

//+------------------------------------------------------------------+
//| Draw Doji zones on the main chart                                |
//+------------------------------------------------------------------+
void DrawZonesOnChart()
{
   //--- Get current price
   double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(current_price <= 0) return;
   
   //--- Remove old zone objects
   ObjectsDeleteAll(0, "RSI_ZONE_");
   
   //--- Filter: only draw zones within ±10% of current price
   double filter_window = current_price * 0.10;
   
   for(int i = 0; i < g_zone_count; i++)
   {
      //--- Only show zones that existed before now (causality)
      if(g_zones[i].time >= TimeCurrent()) continue;
      
      //--- Filter by proximity
      if(MathAbs(g_zones[i].midpoint - current_price) > filter_window) continue;
      
      //--- Check if price is inside this zone
      double tolerance = current_price * 0.0015;
      bool is_inside = (current_price >= g_zones[i].range_low - tolerance &&
                       current_price <= g_zones[i].range_high + tolerance);
      g_zones[i].active = is_inside;
      
      //--- Draw rectangle on main chart
      string name = "RSI_ZONE_" + IntegerToString(i);
      datetime time1 = g_zones[i].time;
      datetime time2 = TimeCurrent() + PeriodSeconds(PERIOD_M30) * 100; // extend 100 candles into future
      
      //--- Create rectangle
      if(ObjectFind(0, name) < 0)
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, time1, g_zones[i].range_high, time2, g_zones[i].range_low);
      
      //--- Set properties
      color zoneColor = g_zones[i].type == 1 ? InpWeeklyZoneColor : InpDailyZoneColor;
      if(is_inside) zoneColor = clrYellow; // highlight active zones
      
      ObjectSetInteger(0, name, OBJPROP_COLOR, zoneColor);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      
      //--- Add text label
      string label_name = "RSI_ZONE_LBL_" + IntegerToString(i);
      string label_text = StringFormat("%s %s | O:%.2f C:%.2f",
                                       g_zones[i].type == 1 ? "W" : "D",
                                       TimeToString(g_zones[i].time, TIME_DATE),
                                       g_zones[i].open, g_zones[i].close);
      
      if(ObjectFind(0, label_name) < 0)
         ObjectCreate(0, label_name, OBJ_TEXT, 0, time1, g_zones[i].range_high);
      
      ObjectSetString(0, label_name, OBJPROP_TEXT, label_text);
      ObjectSetInteger(0, label_name, OBJPROP_COLOR, zoneColor);
      ObjectSetInteger(0, label_name, OBJPROP_FONTSIZE, 8);
      ObjectSetDouble(0, label_name, OBJPROP_PRICE, g_zones[i].range_high + current_price * 0.001);
   }
}

//+------------------------------------------------------------------+
//| Draw info panel on the chart                                     |
//+------------------------------------------------------------------+
void DrawPanel()
{
   //--- Remove old panel objects
   ObjectsDeleteAll(0, "RSI_PANEL_");
   
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(price <= 0) return;
   
   //--- Panel position (top-right of chart)
   long chart_width = ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
   int x = (int)(chart_width - 280);
   int y = 20;
   int line_height = 18;
   
   //--- Draw panel background
   DrawPanelLabel("RSI_PANEL_BG", x - 10, y - 5, 270, 320, " ", clrWhiteSmoke, clrDarkGray);
   
   //--- Title
   DrawPanelText("RSI_PANEL_TITLE", x, y, "Gold RSI Strategy — M30", clrDarkSlateGray, 11, "Arial Bold");
   y += line_height + 5;
   
   //--- Price
   DrawPanelText("RSI_PANEL_PRICE", x, y, StringFormat("Price: %.2f", price), clrBlack, 10, "Arial");
   y += line_height;
   
   //--- RSI value
   string rsi_str = StringFormat("RSI(30): %.2f", g_rsi);
   color rsi_color = clrDarkGray;
   if(g_rsi > 60) rsi_color = clrFireBrick;
   else if(g_rsi < 40) rsi_color = clrForestGreen;
   DrawPanelText("RSI_PANEL_RSI", x, y, rsi_str, rsi_color, 10, "Arial Bold");
   y += line_height + 5;
   
   //--- Zone status
   if(g_current_zone > 0)
   {
      DrawPanelText("RSI_PANEL_ZONE", x, y, 
         StringFormat("IN ZONE %d (%d candles)", g_current_zone, g_candles_in_zone),
         clrDarkOrange, 10, "Arial Bold");
   }
   else
   {
      double d40 = MathAbs(g_rsi - 40);
      double d60 = MathAbs(g_rsi - 60);
      int nearest = d40 < d60 ? 40 : 60;
      double dist = MathMin(d40, d60);
      DrawPanelText("RSI_PANEL_ZONE", x, y, 
         StringFormat("Nearest: level %d (%.1f units)", nearest, dist),
         clrGray, 10, "Arial");
   }
   y += line_height + 5;
   
   //--- Prediction section
   DrawPanelText("RSI_PANEL_PRED_HDR", x, y, "--- Prediction ---", clrDarkSlateGray, 9, "Arial Bold");
   y += line_height;
   
   //--- Compute predictions for both levels
   double rev40, div40, pass40;
   double rev60, div60, pass60;
   PredictForLevel(40, rev40, div40, pass40);
   PredictForLevel(60, rev60, div60, pass60);
   
   //--- Which level is more likely to be touched first?
   double d40 = MathAbs(g_rsi - 40);
   double d60 = MathAbs(g_rsi - 60);
   int likely_level = d40 < d60 ? 40 : 60;
   
   DrawPanelText("RSI_PANEL_LIKELY", x, y, 
      StringFormat("Likely touch: level %d", likely_level),
      clrDarkBlue, 10, "Arial Bold");
   y += line_height;
   
   //--- Show prediction for likely level
   double rev = likely_level == 40 ? rev40 : rev60;
   double div = likely_level == 40 ? div40 : div60;
   double pas = likely_level == 40 ? pass40 : pass60;
   
   DrawPanelText("RSI_PANEL_REV", x, y, 
      StringFormat("  Reversal:    %.0f%%", rev * 100),
      clrForestGreen, 9, "Arial");
   y += line_height - 2;
   
   DrawPanelText("RSI_PANEL_DIV", x, y, 
      StringFormat("  Divergence:  %.0f%%", div * 100),
      clrDarkOrange, 9, "Arial");
   y += line_height - 2;
   
   DrawPanelText("RSI_PANEL_PASS", x, y, 
      StringFormat("  Pass-through:%.0f%%", pas * 100),
      clrFireBrick, 9, "Arial");
   y += line_height + 3;
   
   //--- Zone section
   DrawPanelText("RSI_PANEL_ZONE_HDR", x, y, "--- Doji Zones ---", clrDarkSlateGray, 9, "Arial Bold");
   y += line_height;
   
   //--- Find nearest zone
   int nearest_zone_idx = -1;
   double nearest_dist = 999999;
   bool any_inside = false;
   
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].active)
      {
         any_inside = true;
         DrawPanelText("RSI_PANEL_INSIDE", x, y, 
            StringFormat("INSIDE %s zone!", g_zones[i].type == 1 ? "Weekly" : "Daily"),
            clrRed, 10, "Arial Bold");
         y += line_height;
      }
      
      double dist = MathAbs(g_zones[i].midpoint - price);
      if(dist < nearest_dist && !g_zones[i].active)
      {
         nearest_dist = dist;
         nearest_zone_idx = i;
      }
   }
   
   if(!any_inside && nearest_zone_idx >= 0)
   {
      DojiZone z = g_zones[nearest_zone_idx];
      double dist_pct = nearest_dist / price * 100;
      double dist_pips = nearest_dist * 10;
      
      DrawPanelText("RSI_PANEL_NZONE", x, y, 
         StringFormat("Nearest zone: %s @ %.2f", 
            z.type == 1 ? "Weekly" : "Daily", z.midpoint),
         clrDarkSlateGray, 9, "Arial");
      y += line_height - 2;
      
      DrawPanelText("RSI_PANEL_NDIST", x, y, 
         StringFormat("  Dist: %.1f pips (%.2f%%)", dist_pips, dist_pct),
         clrGray, 9, "Arial");
      y += line_height - 2;
      
      DrawPanelText("RSI_PANEL_NOHLC", x, y, 
         StringFormat("  O:%.2f C:%.2f", z.open, z.close),
         clrGray, 9, "Arial");
      y += line_height;
   }
   
   y += 5;
   
   //--- Entry ticket (if applicable)
   if(g_current_zone > 0)
   {
      DrawPanelText("RSI_PANEL_TICKET_HDR", x, y, "--- Entry Ticket ---", clrDarkSlateGray, 9, "Arial Bold");
      y += line_height;
      
      string direction = "";
      color dir_color = clrGray;
      double sl = 0, tp = 0;
      
      if(g_current_zone == 60)
      {
         direction = "SELL";
         dir_color = clrFireBrick;
         sl = price + price * 0.004;
         tp = price - price * 0.008;
      }
      else if(g_current_zone == 40)
      {
         direction = "BUY";
         dir_color = clrForestGreen;
         sl = price - price * 0.004;
         tp = price + price * 0.008;
      }
      
      if(direction != "")
      {
         DrawPanelText("RSI_PANEL_DIR", x, y, StringFormat("Direction: %s", direction), dir_color, 10, "Arial Bold");
         y += line_height - 2;
         DrawPanelText("RSI_PANEL_ENTRY", x, y, StringFormat("Entry: %.2f", price), clrBlack, 9, "Arial");
         y += line_height - 2;
         DrawPanelText("RSI_PANEL_SL", x, y, StringFormat("SL: %.2f", sl), clrFireBrick, 9, "Arial");
         y += line_height - 2;
         DrawPanelText("RSI_PANEL_TP", x, y, StringFormat("TP: %.2f", tp), clrForestGreen, 9, "Arial");
         y += line_height - 2;
         double rr = MathAbs(tp - price) / MathAbs(price - sl);
         DrawPanelText("RSI_PANEL_RR", x, y, StringFormat("R:R = 1:%.2f", rr), clrDarkOrange, 9, "Arial");
         y += line_height;
      }
   }
   
   //--- Session info
   y += 5;
   int hour = TimeHour(TimeCurrent());
   int tehran_hour = (hour + 3) % 24; // Approximate Tehran time (UTC+3:30)
   string session = "Night";
   if(tehran_hour >= 6 && tehran_hour < 12) session = "Morning (Asia)";
   else if(tehran_hour >= 12 && tehran_hour < 17) session = "Noon (Europe)";
   else if(tehran_hour >= 17 && tehran_hour < 22) session = "Evening (US)";
   
   DrawPanelText("RSI_PANEL_SESSION", x, y, StringFormat("Session: %s", session), clrGray, 8, "Arial");
   y += line_height - 4;
   DrawPanelText("RSI_PANEL_UPDATE", x, y, StringFormat("Updated: %s", TimeToString(TimeCurrent(), TIME_MINUTES)), clrLightGray, 8, "Arial");
}

//+------------------------------------------------------------------+
//| Draw a panel label (background rectangle)                        |
//+------------------------------------------------------------------+
void DrawPanelLabel(string name, int x, int y, int width, int height, string text, color bg, color border)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_COLOR, bg);
   ObjectSetInteger(0, name, OBJPROP_BACKGROUND, false);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
}

//+------------------------------------------------------------------+
//| Draw panel text                                                  |
//+------------------------------------------------------------------+
void DrawPanelText(string name, int x, int y, string text, color clr, int size, string font)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, name, OBJPROP_FONT, font);
}

//+------------------------------------------------------------------+
//| Predict for a specific level                                     |
//+------------------------------------------------------------------+
void PredictForLevel(int level, double &reversal, double &divergence, double &pass_through)
{
   CategoryMeans means[3];
   if(level == 40)
   {
      for(int i = 0; i < 3; i++) means[i] = means_40[i];
   }
   else
   {
      for(int i = 0; i < 3; i++) means[i] = means_60[i];
   }
   
   //--- Compute distances to each category's mean profile
   double distances[3];
   for(int i = 0; i < 3; i++)
   {
      double dCandles = MathPow((g_candles_in_zone - means[i].candles_in_zone) / 3.0, 2);
      double dVel = MathPow((g_rsi_vel_10 - means[i].rsi_vel_10) / 4.0, 2);
      distances[i] = MathSqrt(dCandles * 3.0 + dVel);
   }
   
   //--- Convert to weights (closer = higher)
   double invD[3];
   double sumInv = 0;
   for(int i = 0; i < 3; i++)
   {
      invD[i] = 1.0 / (distances[i] + 0.3);
      sumInv += invD[i];
   }
   
   //--- Compute probabilities
   double probs[3];
   double sumP = 0;
   for(int i = 0; i < 3; i++)
   {
      probs[i] = base_rates[i] * (invD[i] / (sumInv / 3.0));
      sumP += probs[i];
   }
   
   //--- Normalize
   reversal = probs[0] / sumP;
   divergence = probs[1] / sumP;
   pass_through = probs[2] / sumP;
}

//+------------------------------------------------------------------+
//| Check and trigger alerts                                         |
//+------------------------------------------------------------------+
void CheckAlerts()
{
   if(!InpEnableAlerts) return;
   
   datetime now = TimeCurrent();
   
   //--- Alert when RSI enters zone
   if(InpAlertOnRSI && g_current_zone > 0)
   {
      // Only alert once per zone entry (not every tick)
      if(now - g_last_alert_rsi > 300) // 5 minutes cooldown
      {
         double rev, div, pas;
         PredictForLevel(g_current_zone, rev, div, pas);
         
         string msg = StringFormat("RSI entered ZONE %d! (RSI=%.2f, %d candles in zone)\n"+
                                   "Reversal: %.0f%% | Divergence: %.0f%% | Pass-through: %.0f%%",
                                   g_current_zone, g_rsi, g_candles_in_zone,
                                   rev*100, div*100, pas*100);
         Alert(msg);
         g_last_alert_rsi = now;
      }
   }
   
   //--- Alert when price enters a Doji zone
   if(InpAlertOnZone)
   {
      for(int i = 0; i < g_zone_count; i++)
      {
         if(g_zones[i].active && now - g_last_alert_zone > 300)
         {
            string msg = StringFormat("Price entered %s Doji zone!\n"+
                                      "Zone: %.2f - %.2f (Open: %.2f, Close: %.2f)\n"+
                                      "Date: %s",
                                      g_zones[i].type == 1 ? "WEEKLY" : "DAILY",
                                      g_zones[i].range_low, g_zones[i].range_high,
                                      g_zones[i].open, g_zones[i].close,
                                      TimeToString(g_zones[i].time, TIME_DATE));
            Alert(msg);
            g_last_alert_zone = now;
            break;
         }
      }
   }
   
   //--- Alert on M5 pattern when RSI in zone
   if(InpAlertOnPattern && g_current_zone > 0)
   {
      string pattern = DetectM5Pattern();
      if(pattern != "" && now - g_last_alert_rsi > 180)
      {
         string msg = StringFormat("M5 Pattern detected: %s\n"+
                                   "RSI in zone %d — Consider entry!\n"+
                                   "Direction: %s",
                                   pattern, g_current_zone,
                                   g_current_zone == 40 ? "BUY" : "SELL");
         Alert(msg);
         g_last_alert_rsi = now;
      }
   }
}

//+------------------------------------------------------------------+
//| Detect M5 candle pattern                                         |
//+------------------------------------------------------------------+
string DetectM5Pattern()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_M5, 0, 3, rates) < 3) return "";
   
   MqlRates cur = rates[0];
   MqlRates prev = rates[1];
   
   double body = MathAbs(cur.close - cur.open);
   double range = cur.high - cur.low;
   if(range <= 0) return "";
   
   double upper_wick = cur.high - MathMax(cur.open, cur.close);
   double lower_wick = MathMin(cur.open, cur.close) - cur.low;
   
   //--- Doji
   if(body <= range * 0.10)
      return "Doji";
   
   //--- Bullish pin bar / hammer
   if(lower_wick >= range * 0.6 && body <= range * 0.35)
      return "Bullish Pin Bar";
   
   //--- Bearish pin bar
   if(upper_wick >= range * 0.6 && body <= range * 0.35)
      return "Bearish Pin Bar";
   
   //--- Bullish engulfing
   if(prev.close < prev.open && cur.close > cur.open &&
      MathMax(cur.open, cur.close) >= MathMax(prev.open, prev.close) &&
      MathMin(cur.open, cur.close) <= MathMin(prev.open, prev.close))
      return "Bullish Engulfing";
   
   //--- Bearish engulfing
   if(prev.close > prev.open && cur.close < cur.open &&
      MathMax(cur.open, cur.close) >= MathMax(prev.open, prev.close) &&
      MathMin(cur.open, cur.close) <= MathMin(prev.open, prev.close))
      return "Bearish Engulfing";
   
   return "";
}

//+------------------------------------------------------------------+
//| Get session name                                                 |
//+------------------------------------------------------------------+
string GetSession()
{
   int hour = TimeHour(TimeCurrent());
   if(hour >= 0 && hour < 7) return "Asia";
   if(hour >= 7 && hour < 13) return "Europe";
   if(hour >= 13 && hour < 21) return "US";
   return "Asia2";
}
//+------------------------------------------------------------------+
