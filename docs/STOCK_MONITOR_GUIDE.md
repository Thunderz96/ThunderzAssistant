# 📈 Stock Monitor v2.0 - Watchlist Edition

## 🎯 What's New

The Stock Monitor has been completely overhauled with a **Watchlist** feature! Now you can track stocks like VTI, AAPL, TSLA over time without fetching manually every time.

---

## ✨ New Features

### **Watchlist Tracking** ⭐
- Add stocks to persistent watchlist
- Track multiple stocks simultaneously
- See all tracked stocks at a glance
- Remove stocks you don't want anymore

### **Auto-Refresh** 🔄
- Automatically refreshes when you open the module
- Manual refresh for all stocks or individual stocks
- Background updates (non-blocking UI)

### **Price Display** 💰
- Current price (large, clear)
- Dollar change (± $X.XX)
- Percentage change (± X.XX%)
- Color-coded: Green (up), Red (down)
- Last updated timestamp

### **Quick Actions** ⚡
- **Plot** - View price chart
- **Refresh** - Update single stock
- **Remove** - Delete from watchlist

### **Persistent Storage** 💾
- Watchlist saved between sessions
- Never lose your tracked stocks
- Auto-loads on startup

### **Notifications** 🔔
- Integrated with Notification Center
- Get notified when stocks are added
- (Future: Price alerts)

---

## 🚀 How to Use

### **Adding Stocks to Watchlist**

1. **Enter ticker symbol** (e.g., VTI, AAPL, TSLA)
2. Click **⭐ Add to Watchlist** (or press Enter)
3. Stock appears in your watchlist instantly!

**Example Tickers:**
- `VTI` - Vanguard Total Stock Market ETF
- `AAPL` - Apple Inc.
- `TSLA` - Tesla Inc.
- `MSFT` - Microsoft Corporation
- `GOOGL` - Alphabet Inc.
- `SPY` - S&P 500 ETF

### **Viewing Your Watchlist**

Each stock card shows:
```
┌──────────────────────────────────────┐
│ AAPL                    [📈 Plot] [🔄] [✕] │
│                                      │
│ $185.50   ▲ $2.30 (+1.26%)          │
│                                      │
│ Last updated: 2:30 PM                │
└──────────────────────────────────────┘
```

**Color Coding:**
- 🟢 Green arrow (▲) = Price up
- 🔴 Red arrow (▼) = Price down
- ⚪ Flat line (━) = No change

### **Refreshing Stocks**

**Refresh All:**
- Click **🔄 Refresh All** button
- Updates all stocks in watchlist
- Runs in background (non-blocking)

**Refresh Single Stock:**
- Click **🔄** button on stock card
- Updates only that stock
- Instant feedback

### **Plotting Charts**

1. Click **📈 Plot** on any stock card
2. Opens matplotlib chart window
3. Shows historical price data
4. Interactive (zoom, pan, save)

### **Removing Stocks**

1. Click **✕** button on stock card
2. Stock removed from watchlist
3. Permanently deleted (until you add it again)

---

## 📊 Example Workflow

### **Building a Watchlist**

```
1. Open Stock Monitor module
2. Add stocks:
   - Type "VTI" → Click Add
   - Type "AAPL" → Click Add
   - Type "TSLA" → Click Add
3. See all three stocks displayed
4. Click "Refresh All" to update prices
5. Close and reopen app → Stocks still there!
```

### **Daily Monitoring**

```
Morning:
1. Open Stock Monitor
2. Module auto-refreshes all stocks
3. Check which stocks are up/down
4. Click "Plot" on VTI to see chart

Later:
1. Click "Refresh All" to get latest prices
2. Review changes throughout the day
```

### **Research Mode**

```
1. Add stock to watchlist (e.g., GOOGL)
2. Click "Plot" to see recent trend
3. Check price and change %
4. Decide if you want to keep tracking
5. Remove from watchlist if not interested
```

---

## 💡 Pro Tips

### **Tip 1: Build Your Portfolio**
Add all stocks you own to track performance at a glance!

### **Tip 2: ETF Tracking**
Track ETFs like VTI, SPY, QQQ for market overview

### **Tip 3: Refresh Timing**
- **Morning:** Check after market open (9:30 AM ET)
- **Midday:** Check around lunch
- **End of Day:** Check after market close (4:00 PM ET)

### **Tip 4: Use Plots for Trends**
Click Plot to see if stock is trending up/down over time

### **Tip 5: Color Signals**
- Mostly green in watchlist = Good day!
- Mostly red in watchlist = Market down

---

## 🔧 Technical Details

### **Data Source**
- **Library:** yfinance (Yahoo Finance)
- **Data:** Real-time delayed ~15 minutes
- **Period:** 2 days (to calculate change)
- **Refresh:** On-demand (manual)

### **Storage**
- **File:** `stock_watchlist.json`
- **Location:** App root directory
- **Format:** JSON
- **Gitignored:** Yes (won't be committed)

### **Data Stored**
```json
{
  "VTI": {
    "price": 250.45,
    "change": 2.30,
    "change_pct": 0.93,
    "last_updated": "2026-02-09T14:30:00"
  }
}
```

### **Performance**
- **Initial Add:** ~2 seconds (fetches data)
- **Refresh Single:** ~2 seconds
- **Refresh All:** ~2 seconds per stock (parallel)
- **Load Watchlist:** Instant (from cache)

---

## 🎨 UI Components

### **Main Interface**
```
┌────────────────────────────────────────┐
│  📈 Stock Monitor                      │
│  Track stocks in your watchlist       │
├────────────────────────────────────────┤
│  Ticker: [VTI    ] [⭐ Add] [🔄 Refresh]│
├────────────────────────────────────────┤
│  📊 Your Watchlist (3 stocks)          │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ VTI         [📈] [🔄] [✕]        │ │
│  │ $250.45  ▲ $2.30 (+0.93%)       │ │
│  │ Last updated: 2:30 PM            │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ AAPL        [📈] [🔄] [✕]        │ │
│  │ $185.50  ▲ $1.20 (+0.65%)       │ │
│  │ Last updated: 2:30 PM            │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ TSLA        [📈] [🔄] [✕]        │ │
│  │ $195.30  ▼ $3.20 (-1.61%)       │ │
│  │ Last updated: 2:30 PM            │ │
│  └──────────────────────────────────┘ │
│                                        │
│  ✓ All stocks refreshed!               │
└────────────────────────────────────────┘
```

### **Empty State**
```
┌────────────────────────────────────────┐
│  📈 Stock Monitor                      │
├────────────────────────────────────────┤
│  Ticker: [____    ] [⭐ Add] [🔄]      │
├────────────────────────────────────────┤
│  📊 Your Watchlist (0 stocks)          │
│                                        │
│           📊 Your watchlist is empty!  │
│                                        │
│     Add stocks like VTI, AAPL, TSLA   │
│         to track them over time.       │
│                                        │
└────────────────────────────────────────┘
```

---

## 🔔 Notification Integration

The Stock Monitor now integrates with the Notification Center!

**Current Notifications:**
- ✅ Stock added to watchlist

**Future Notifications (Planned):**
- 📈 Significant price increase (>5%)
- 📉 Significant price decrease (>5%)
- ⚠️ Volume spike detected
- 🎯 Price target reached

---

## 📚 API Reference (For Developers)

### **Add Stock to Watchlist**
```python
stock_monitor.add_to_watchlist()
# Gets ticker from entry field
# Fetches data from Yahoo Finance
# Adds to watchlist dictionary
# Saves to JSON
# Updates UI
```

### **Remove Stock**
```python
stock_monitor.remove_from_watchlist(ticker)
# Args: ticker (str) - Stock ticker symbol
# Removes from watchlist dictionary
# Saves to JSON
# Updates UI
```

### **Refresh Stock**
```python
stock_monitor.refresh_stock(ticker)
# Args: ticker (str) - Stock ticker symbol
# Fetches latest data
# Updates watchlist
# Updates UI
```

### **Refresh All Stocks**
```python
stock_monitor.refresh_all_stocks()
# Loops through all watchlist stocks
# Fetches latest data for each
# Updates all in background thread
# Updates UI when complete
```

### **Plot Stock**
```python
stock_monitor.plot_stock(ticker)
# Args: ticker (str) - Stock ticker symbol
# Opens matplotlib chart
# Shows historical price data
```

---

## 🐛 Troubleshooting

### **Stock Not Found**
**Problem:** "Could not find stock: XYZ"

**Solutions:**
- Check ticker spelling (must be exact)
- Verify ticker exists on Yahoo Finance
- Try different ticker symbol
- Some stocks may not be available

### **Data Not Updating**
**Problem:** Prices seem old

**Solutions:**
- Click "Refresh All" or individual refresh
- Check internet connection
- Market might be closed (data freezes)
- Wait a few seconds between refreshes

### **Plot Not Showing**
**Problem:** Chart doesn't appear

**Solutions:**
- Check matplotlib is installed: `pip install matplotlib`
- Make sure you fetched stock data first
- Try refreshing the stock
- Check for Python errors in console

### **Watchlist Not Saving**
**Problem:** Stocks disappear after restart

**Solutions:**
- Check `stock_watchlist.json` file exists
- Verify file permissions (can write)
- Check for errors in console
- Try manually saving: watchlist should auto-save

---

## 🔒 Privacy & Data

**What's Stored:**
- Stock ticker symbols
- Current price
- Price change data
- Last updated timestamp

**What's NOT Stored:**
- Your portfolio holdings
- Buy/sell history
- Personal financial data
- API keys or credentials

**Data Source:**
- Yahoo Finance (public data)
- 15-minute delayed quotes
- Free, no account required

**File Location:**
- `stock_watchlist.json` (gitignored)
- Safe to delete (will recreate empty)

---

## 🚀 Future Enhancements

**Planned Features:**

### **Price Alerts** 🔔
```python
# Set alerts for price targets
set_alert("AAPL", target=190.00, direction="above")
# Get notified when price hits target
```

### **Portfolio Tracking** 💼
```python
# Track actual holdings
add_holding("VTI", shares=100, cost_basis=240.00)
# See total value and gains/losses
```

### **Advanced Charts** 📊
- Multiple timeframes (1D, 1W, 1M, 1Y)
- Technical indicators (MA, RSI, MACD)
- Volume charts
- Candlestick charts

### **News Integration** 📰
- Latest news for each stock
- Earnings dates
- Dividend information

### **Performance Metrics** 📈
- YTD performance
- 52-week high/low
- P/E ratio
- Market cap

---

## 📊 Comparison: Old vs New

| Feature | v1.0 (Old) | v2.0 (Watchlist) |
|---------|-----------|------------------|
| **Track Multiple Stocks** | ❌ No | ✅ Yes |
| **Persistent Storage** | ❌ No | ✅ Yes |
| **Auto-Refresh** | ❌ No | ✅ Yes |
| **Visual Price Changes** | ❌ No | ✅ Yes (colors) |
| **Quick Actions** | ❌ No | ✅ Yes (plot, refresh, remove) |
| **Notifications** | ❌ No | ✅ Yes |
| **Manual Fetch** | ✅ Yes | ✅ Yes |
| **Plot Charts** | ✅ Yes | ✅ Yes (improved) |

---

## 💡 Best Practices

**DO:**
- ✅ Add stocks you care about
- ✅ Refresh regularly for latest prices
- ✅ Remove stocks you're no longer interested in
- ✅ Use plots to understand trends
- ✅ Check during market hours for best data

**DON'T:**
- ❌ Add hundreds of stocks (keep it manageable)
- ❌ Refresh every second (API limits)
- ❌ Use for real-time trading (15-min delay)
- ❌ Expect perfect accuracy (delayed data)
- ❌ Spam refresh button

---

## 🎯 Use Cases

### **Long-Term Investor**
Track ETFs like VTI, VOO, QQQ to monitor portfolio performance

### **Stock Researcher**
Add potential buys to watchlist, monitor for a few weeks before deciding

### **Market Watcher**
Track major indices (SPY, DIA, QQQ) to understand market direction

### **Tech Enthusiast**
Monitor FAANG stocks (AAPL, GOOGL, META, AMZN, NFLX)

### **Dividend Tracker**
Track dividend-paying stocks (VYM, SCHD, etc.)

---

## 📖 Quick Reference

### **Keyboard Shortcuts**
- `Enter` in ticker field = Add to watchlist

### **File Locations**
- **Watchlist:** `stock_watchlist.json`
- **Module:** `modules/stock_monitor_module.py`

### **Dependencies**
```bash
pip install yfinance matplotlib
```

### **Common Tickers**
**ETFs:**
- VTI (Total Market)
- SPY (S&P 500)
- QQQ (Nasdaq 100)
- VOO (S&P 500)

**Tech:**
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- TSLA (Tesla)

**Finance:**
- JPM (JPMorgan)
- BRK.B (Berkshire)
- V (Visa)

---

## ✅ Testing Checklist

- [ ] Add stock to watchlist (e.g., VTI)
- [ ] Stock appears in watchlist
- [ ] Price shows correctly
- [ ] Change shows with color
- [ ] Click Refresh (single stock)
- [ ] Click Refresh All
- [ ] Click Plot (chart appears)
- [ ] Click Remove (stock disappears)
- [ ] Close and reopen app
- [ ] Watchlist persists
- [ ] Add multiple stocks
- [ ] All stocks display correctly

---

## 🎉 Summary

**Stock Monitor v2.0 Features:**
- ✅ Persistent watchlist
- ✅ Auto-refresh on open
- ✅ Color-coded price changes
- ✅ Quick actions (plot, refresh, remove)
- ✅ Notification integration
- ✅ Clean, modern UI
- ✅ Background updates
- ✅ Saved between sessions

**Perfect for:**
- Long-term investors
- Market watchers
- Stock researchers
- Portfolio trackers

---

**Ready to track your stocks?**

```bash
python main.py
```

Click **📈 Stock Monitor** → Add **VTI** → Start tracking! 🚀
