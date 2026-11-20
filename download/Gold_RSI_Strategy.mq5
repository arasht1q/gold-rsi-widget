//+------------------------------------------------------------------+
//|                                         Gold_RSI_Strategy.mq5    |
//|                  RSI(30) M30 Strategy with Doji Zones for MT5    |
//+------------------------------------------------------------------+
#property copyright "Z.ai - Gold RSI Widget"
#property link      "https://github.com/arasht1q/gold-rsi-widget"
#property version   "1.00"
#property description "RSI(30) M30 strategy with Doji zones"
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

//--- Input Parameters (NO 'group' keyword for compatibility)
input int      InpRSIPeriod        = 30;       // RSI period
input double   InpLevelOversold    = 40.0;     // Oversold level
input double   InpLevelOverbought  = 60.0;     // Overbought level
input double   InpZoneTolerance    = 1.0;      // Zone tolerance (+/- units)
input double   InpDojiThreshold    = 0.10;     // Doji body/range threshold (0.10 = 10%)
input int      InpLookbackDays     = 90;       // Days to scan for daily Dojis
input int      InpLookbackWeeks    = 26;       // Weeks to scan for weekly Dojis
input bool     InpShowZones        = true;     // Draw Doji zones on chart
input bool     InpShowDailyZones   = true;     // Show daily Doji zones
input bool     InpShowWeeklyZones  = true;     // Show weekly Doji zones
input color    InpWeeklyZoneColor  = clrOrange; // Weekly zone color
input color    InpDailyZoneColor   = clrGray;  // Daily zone color
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
int g_current_zone = 0;
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
   int      type;
   bool     active;
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

CategoryMeans means_40[3];
CategoryMeans means_60[3];
double base_rates[3] = {0.329, 0.210, 0.461};

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0, RSI_Buffer, INDICATOR_DATA);
   PlotIndexSetString(0, PLOT_LABEL, "RSI(30)");
   
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 0, InpLevelOversold);
   IndicatorSetDouble(INDICATOR_LEVELVALUE, 1, InpLevelOverbought);
   IndicatorSetString(INDICATOR_SHORTNAME, "RSI(30) M30 - Gold Strategy");
   
   rsi_handle = iRSI(_Symbol, PERIOD_M30, InpRSIPeriod, PRICE_CLOSE);
   if(rsi_handle == INVALID_HANDLE)
   {
      Print("Failed to create RSI handle");
      return(INIT_FAILED);
   }
   
   // Initialize prediction means
   means_40[0].candles_in_zone = 1.61; means_40[0].rsi_vel_10 = -2.03; means_40[0].vol_ratio = 1.07;
   means_40[1].candles_in_zone = 2.78; means_40[1].rsi_vel_10 = -3.45; means_40[1].vol_ratio = 1.02;
   means_40[2].candles_in_zone = 1.78; means_40[2].rsi_vel_10 = -3.40; means_40[2].vol_ratio = 1.10;
   
   means_60[0].candles_in_zone = 1.54; means_60[0].rsi_vel_10 = 1.67; means_60[0].vol_ratio = 1.07;
   means_60[1].candles_in_zone = 2.17; means_60[1].rsi_vel_10 = 3.05; means_60[1].vol_ratio = 1.02;
   means_60[2].candles_in_zone = 1.83; means_60[2].rsi_vel_10 = 2.16; means_60[2].vol_ratio = 1.10;
   
   EventSetTimer(30);
   ScanDojiZones();
   
   Print("Gold RSI Strategy indicator initialized - ", g_zone_count, " zones found");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| OnDeinit                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, "RSI_ZONE_");
   ObjectsDeleteAll(0, "RSI_PANEL_");
   
   if(rsi_handle != INVALID_HANDLE)
      IndicatorRelease(rsi_handle);
}

//+------------------------------------------------------------------+
//| OnTimer                                                           |
//+------------------------------------------------------------------+
void OnTimer()
{
   ScanDojiZones();
   if(InpShowPanel)
      DrawPanel();
   CheckAlerts();
}

//+------------------------------------------------------------------+
//| OnCalculate                                                       |
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
   int copied = CopyBuffer(rsi_handle, 0, 0, rates_total, RSI_Buffer);
   if(copied <= 0)
      return(0);
   
   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(rsi_handle, 0, 0, 15, rsi) > 0)
   {
      g_rsi = rsi[0];
      if(ArraySize(rsi) >= 11)
         g_rsi_vel_10 = rsi[0] - rsi[10];
      if(ArraySize(rsi) >= 6)
         g_rsi_vel_5 = rsi[0] - rsi[5];
      
      UpdateCandlesInZone(rsi);
   }
   
   if(InpShowZones)
      DrawZonesOnChart();
   
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
   
   if(g_rsi >= lo40 && g_rsi <= hi40)
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
   else if(g_rsi >= lo60 && g_rsi <= hi60)
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
//| Scan for Doji candles                                            |
//+------------------------------------------------------------------+
void ScanDojiZones()
{
   g_zone_count = 0;
   ArrayResize(g_zones, 0);
   
   if(InpShowDailyZones)
   {
      MqlRates daily[];
      ArraySetAsSeries(daily, true);
      int copied = CopyRates(_Symbol, PERIOD_D1, 0, InpLookbackDays + 1, daily);
      if(copied > 0)
      {
         for(int i = 1; i < copied; i++)
         {
            double range = daily[i].high - daily[i].low;
            if(range <= 0) continue;
            double body = MathAbs(daily[i].close - daily[i].open);
            if(body <= InpDojiThreshold * range)
            {
               AddZone(daily[i].time, daily[i].open, daily[i].close, 
                       daily[i].high, daily[i].low, 0);
            }
         }
      }
   }
   
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
                       weekly[i].high, weekly[i].low, 1);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Add zone to array                                                |
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
//| Draw Doji zones on main chart                                    |
//+------------------------------------------------------------------+
void DrawZonesOnChart()
{
   double current_price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(current_price <= 0) return;
   
   ObjectsDeleteAll(0, "RSI_ZONE_");
   
   double filter_window = current_price * 0.10;
   
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].time >= TimeCurrent()) continue;
      if(MathAbs(g_zones[i].midpoint - current_price) > filter_window) continue;
      
      double tolerance = current_price * 0.0015;
      bool is_inside = (current_price >= g_zones[i].range_low - tolerance &&
                       current_price <= g_zones[i].range_high + tolerance);
      g_zones[i].active = is_inside;
      
      string name = "RSI_ZONE_" + IntegerToString(i);
      datetime time1 = g_zones[i].time;
      datetime time2 = TimeCurrent() + PeriodSeconds(PERIOD_M30) * 100;
      
      if(ObjectFind(0, name) < 0)
         ObjectCreate(0, name, OBJ_RECTANGLE, 0, time1, g_zones[i].range_high, time2, g_zones[i].range_low);
      
      color zoneColor = g_zones[i].type == 1 ? InpWeeklyZoneColor : InpDailyZoneColor;
      if(is_inside) zoneColor = clrYellow;
      
      ObjectSetInteger(0, name, OBJPROP_COLOR, zoneColor);
      ObjectSetInteger(0, name, OBJPROP_FILL, true);
      ObjectSetInteger(0, name, OBJPROP_BACK, true);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, 1);
      
      // Label
      string lbl_name = "RSI_ZONE_LBL_" + IntegerToString(i);
      string lbl_text = StringFormat("%s %s | O:%.2f C:%.2f",
                                     g_zones[i].type == 1 ? "W" : "D",
                                     TimeToString(g_zones[i].time, TIME_DATE),
                                     g_zones[i].open, g_zones[i].close);
      
      if(ObjectFind(0, lbl_name) < 0)
         ObjectCreate(0, lbl_name, OBJ_TEXT, 0, time1, g_zones[i].range_high);
      
      ObjectSetString(0, lbl_name, OBJPROP_TEXT, lbl_text);
      ObjectSetInteger(0, lbl_name, OBJPROP_COLOR, zoneColor);
      ObjectSetInteger(0, lbl_name, OBJPROP_FONTSIZE, 8);
   }
}

//+------------------------------------------------------------------+
//| Draw info panel                                                  |
//+------------------------------------------------------------------+
void DrawPanel()
{
   ObjectsDeleteAll(0, "RSI_PANEL_");
   
   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(price <= 0) return;
   
   int x = 10;
   int y = 20;
   int line_h = 18;
   
   // Title
   DrawText("RSI_PANEL_0", x, y, "Gold RSI Strategy - M30", clrDarkSlateGray, 11, "Arial Bold");
   y += line_h + 4;
   
   // Price
   DrawText("RSI_PANEL_1", x, y, StringFormat("Price: %.2f", price), clrBlack, 10, "Arial");
   y += line_h;
   
   // RSI
   color rsi_clr = clrDarkGray;
   if(g_rsi > 60) rsi_clr = clrFireBrick;
   else if(g_rsi < 40) rsi_clr = clrForestGreen;
   DrawText("RSI_PANEL_2", x, y, StringFormat("RSI(30): %.2f", g_rsi), rsi_clr, 10, "Arial Bold");
   y += line_h + 4;
   
   // Zone status
   if(g_current_zone > 0)
   {
      DrawText("RSI_PANEL_3", x, y, 
         StringFormat("IN ZONE %d (%d candles)", g_current_zone, g_candles_in_zone),
         clrDarkOrange, 10, "Arial Bold");
   }
   else
   {
      double d40 = MathAbs(g_rsi - 40);
      double d60 = MathAbs(g_rsi - 60);
      int nearest = d40 < d60 ? 40 : 60;
      double dist = MathMin(d40, d60);
      DrawText("RSI_PANEL_3", x, y, 
         StringFormat("Nearest: level %d (%.1f units)", nearest, dist),
         clrGray, 10, "Arial");
   }
   y += line_h + 4;
   
   // Prediction header
   DrawText("RSI_PANEL_4", x, y, "--- Prediction ---", clrDarkSlateGray, 9, "Arial Bold");
   y += line_h - 2;
   
   double rev40, div40, pass40;
   double rev60, div60, pass60;
   PredictForLevel(40, rev40, div40, pass40);
   PredictForLevel(60, rev60, div60, pass60);
   
   double d40 = MathAbs(g_rsi - 40);
   double d60 = MathAbs(g_rsi - 60);
   int likely = d40 < d60 ? 40 : 60;
   
   DrawText("RSI_PANEL_5", x, y, StringFormat("Likely touch: level %d", likely), clrDarkBlue, 10, "Arial Bold");
   y += line_h - 2;
   
   double rev = likely == 40 ? rev40 : rev60;
   double div = likely == 40 ? div40 : div60;
   double pas = likely == 40 ? pass40 : pass60;
   
   DrawText("RSI_PANEL_6", x, y, StringFormat("  Reversal:     %.0f%%", rev * 100), clrForestGreen, 9, "Arial");
   y += line_h - 4;
   DrawText("RSI_PANEL_7", x, y, StringFormat("  Divergence:   %.0f%%", div * 100), clrDarkOrange, 9, "Arial");
   y += line_h - 4;
   DrawText("RSI_PANEL_8", x, y, StringFormat("  Pass-through: %.0f%%", pas * 100), clrFireBrick, 9, "Arial");
   y += line_h;
   
   // Zones section
   DrawText("RSI_PANEL_9", x, y, "--- Doji Zones ---", clrDarkSlateGray, 9, "Arial Bold");
   y += line_h - 2;
   
   int nearest_idx = -1;
   double nearest_dist = 999999;
   bool any_inside = false;
   
   for(int i = 0; i < g_zone_count; i++)
   {
      if(g_zones[i].active)
      {
         DrawText("RSI_PANEL_10", x, y, 
            StringFormat("INSIDE %s zone!", g_zones[i].type == 1 ? "Weekly" : "Daily"),
            clrRed, 10, "Arial Bold");
         y += line_h - 2;
         any_inside = true;
      }
      
      double dist = MathAbs(g_zones[i].midpoint - price);
      if(dist < nearest_dist && !g_zones[i].active)
      {
         nearest_dist = dist;
         nearest_idx = i;
      }
   }
   
   if(!any_inside && nearest_idx >= 0)
   {
      DrawText("RSI_PANEL_11", x, y, 
         StringFormat("Nearest: %s @ %.2f", 
            g_zones[nearest_idx].type == 1 ? "Weekly" : "Daily", 
            g_zones[nearest_idx].midpoint),
         clrDarkSlateGray, 9, "Arial");
      y += line_h - 4;
      
      double dist_pips = nearest_dist * 10;
      double dist_pct = nearest_dist / price * 100;
      DrawText("RSI_PANEL_12", x, y, 
         StringFormat("  Dist: %.0f pips (%.2f%%)", dist_pips, dist_pct),
         clrGray, 9, "Arial");
      y += line_h - 4;
      
      DrawText("RSI_PANEL_13", x, y, 
         StringFormat("  O:%.2f  C:%.2f", g_zones[nearest_idx].open, g_zones[nearest_idx].close),
         clrGray, 9, "Arial");
      y += line_h;
   }
   else if(!any_inside)
   {
      DrawText("RSI_PANEL_11", x, y, "No zones nearby", clrGray, 9, "Arial");
      y += line_h;
   }
   
   // Entry ticket
   if(g_current_zone > 0)
   {
      y += 4;
      DrawText("RSI_PANEL_14", x, y, "--- Entry Ticket ---", clrDarkSlateGray, 9, "Arial Bold");
      y += line_h - 2;
      
      string dir = "";
      color dir_clr = clrGray;
      double sl = 0, tp = 0;
      
      if(g_current_zone == 60)
      {
         dir = "SELL";
         dir_clr = clrFireBrick;
         sl = price + price * 0.004;
         tp = price - price * 0.008;
      }
      else if(g_current_zone == 40)
      {
         dir = "BUY";
         dir_clr = clrForestGreen;
         sl = price - price * 0.004;
         tp = price + price * 0.008;
      }
      
      if(dir != "")
      {
         DrawText("RSI_PANEL_15", x, y, StringFormat("Direction: %s", dir), dir_clr, 10, "Arial Bold");
         y += line_h - 2;
         DrawText("RSI_PANEL_16", x, y, StringFormat("Entry: %.2f", price), clrBlack, 9, "Arial");
         y += line_h - 4;
         DrawText("RSI_PANEL_17", x, y, StringFormat("SL: %.2f", sl), clrFireBrick, 9, "Arial");
         y += line_h - 4;
         DrawText("RSI_PANEL_18", x, y, StringFormat("TP: %.2f", tp), clrForestGreen, 9, "Arial");
         y += line_h - 4;
         double rr = MathAbs(tp - price) / MathAbs(price - sl);
         DrawText("RSI_PANEL_19", x, y, StringFormat("R:R = 1:%.2f", rr), clrDarkOrange, 9, "Arial");
         y += line_h;
      }
   }
   
   // Session
   y += 4;
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   int tehran_hour = (hour + 3) % 24;
   string sess = "Night";
   if(tehran_hour >= 6 && tehran_hour < 12) sess = "Morning (Asia)";
   else if(tehran_hour >= 12 && tehran_hour < 17) sess = "Noon (Europe)";
   else if(tehran_hour >= 17 && tehran_hour < 22) sess = "Evening (US)";
   
   DrawText("RSI_PANEL_20", x, y, StringFormat("Session: %s", sess), clrGray, 8, "Arial");
   y += line_h - 4;
   DrawText("RSI_PANEL_21", x, y, StringFormat("Updated: %s", TimeToString(TimeCurrent(), TIME_MINUTES)), clrLightGray, 8, "Arial");
}

//+------------------------------------------------------------------+
//| Draw text label on chart                                         |
//+------------------------------------------------------------------+
void DrawText(string name, int x, int y, string text, color clr, int size, string font)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, name, OBJPROP_FONT, font);
}

//+------------------------------------------------------------------+
//| Predict for a level                                              |
//+------------------------------------------------------------------+
void PredictForLevel(int level, double &reversal, double &divergence, double &pass_through)
{
   CategoryMeans m[3];
   if(level == 40)
   {
      m[0] = means_40[0]; m[1] = means_40[1]; m[2] = means_40[2];
   }
   else
   {
      m[0] = means_60[0]; m[1] = means_60[1]; m[2] = means_60[2];
   }
   
   double distances[3];
   for(int i = 0; i < 3; i++)
   {
      double dCandles = MathPow((g_candles_in_zone - m[i].candles_in_zone) / 3.0, 2);
      double dVel = MathPow((g_rsi_vel_10 - m[i].rsi_vel_10) / 4.0, 2);
      distances[i] = MathSqrt(dCandles * 3.0 + dVel);
   }
   
   double invD[3];
   double sumInv = 0;
   for(int i = 0; i < 3; i++)
   {
      invD[i] = 1.0 / (distances[i] + 0.3);
      sumInv += invD[i];
   }
   
   double probs[3];
   double sumP = 0;
   for(int i = 0; i < 3; i++)
   {
      probs[i] = base_rates[i] * (invD[i] / (sumInv / 3.0));
      sumP += probs[i];
   }
   
   reversal = probs[0] / sumP;
   divergence = probs[1] / sumP;
   pass_through = probs[2] / sumP;
}

//+------------------------------------------------------------------+
//| Check alerts                                                     |
//+------------------------------------------------------------------+
void CheckAlerts()
{
   if(!InpEnableAlerts) return;
   
   datetime now = TimeCurrent();
   
   if(InpAlertOnRSI && g_current_zone > 0 && now - g_last_alert_rsi > 300)
   {
      double rev, div, pas;
      PredictForLevel(g_current_zone, rev, div, pas);
      
      string msg = StringFormat("RSI entered ZONE %d! (RSI=%.2f, %d candles)\nReversal: %.0f%% | Divergence: %.0f%% | Pass: %.0f%%",
                                g_current_zone, g_rsi, g_candles_in_zone, rev*100, div*100, pas*100);
      Alert(msg);
      g_last_alert_rsi = now;
   }
   
   if(InpAlertOnZone)
   {
      for(int i = 0; i < g_zone_count; i++)
      {
         if(g_zones[i].active && now - g_last_alert_zone > 300)
         {
            string msg = StringFormat("Price entered %s Doji zone!\nZone: %.2f - %.2f\nDate: %s",
                                      g_zones[i].type == 1 ? "WEEKLY" : "DAILY",
                                      g_zones[i].range_low, g_zones[i].range_high,
                                      TimeToString(g_zones[i].time, TIME_DATE));
            Alert(msg);
            g_last_alert_zone = now;
            break;
         }
      }
   }
   
   if(InpAlertOnPattern && g_current_zone > 0 && now - g_last_alert_rsi > 180)
   {
      string pattern = DetectM5Pattern();
      if(pattern != "")
      {
         string msg = StringFormat("M5 Pattern: %s\nRSI in zone %d - Direction: %s",
                                   pattern, g_current_zone, g_current_zone == 40 ? "BUY" : "SELL");
         Alert(msg);
         g_last_alert_rsi = now;
      }
   }
}

//+------------------------------------------------------------------+
//| Detect M5 pattern                                                |
//+------------------------------------------------------------------+
string DetectM5Pattern()
{
   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, PERIOD_M5, 0, 3, rates) < 3) return "";
   
   double body = MathAbs(rates[0].close - rates[0].open);
   double range = rates[0].high - rates[0].low;
   if(range <= 0) return "";
   
   double upper_wick = rates[0].high - MathMax(rates[0].open, rates[0].close);
   double lower_wick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
   
   if(body <= range * 0.10)
      return "Doji";
   
   if(lower_wick >= range * 0.6 && body <= range * 0.35)
      return "Bullish Pin Bar";
   
   if(upper_wick >= range * 0.6 && body <= range * 0.35)
      return "Bearish Pin Bar";
   
   if(rates[1].close < rates[1].open && rates[0].close > rates[0].open &&
      MathMax(rates[0].open, rates[0].close) >= MathMax(rates[1].open, rates[1].close) &&
      MathMin(rates[0].open, rates[0].close) <= MathMin(rates[1].open, rates[1].close))
      return "Bullish Engulfing";
   
   if(rates[1].close > rates[1].open && rates[0].close < rates[0].open &&
      MathMax(rates[0].open, rates[0].close) >= MathMax(rates[1].open, rates[1].close) &&
      MathMin(rates[0].open, rates[0].close) <= MathMin(rates[1].open, rates[1].close))
      return "Bearish Engulfing";
   
   return "";
}
//+------------------------------------------------------------------+
