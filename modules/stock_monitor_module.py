"""
Stock Market Module for Thunderz Assistant
Version: 2.0.0 - Watchlist Edition

Enhanced stock monitoring with persistent watchlist tracking.

Features:
- 📊 Watchlist: Track multiple stocks persistently
- 🔄 Auto-refresh: Automatic updates when opening module
- 📈 Price tracking: See current price, change %, and change $
- 🎨 Visual indicators: Green (up), Red (down)
- ⭐ Quick actions: Add, Remove, Refresh, Plot
- 💾 Persistent: Watchlist saved between sessions
- 🔔 Notifications: Optional alerts (integration ready)

Requires:
- yfinance (for fetching stock data)
- matplotlib (for data visualization)
"""
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext # Standard PyInstaller hook target
import yfinance as yf
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
import threading


class StockMonitorModule:
    """
    Enhanced Stock Monitor with Watchlist feature.
    
    Track stocks over time without fetching manually every time!
    """
    ICON = "📈"
    PRIORITY = 4  

    def __init__(self, parent_frame, colors):
        """
        Initialize the stock monitor module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
            colors: Dictionary containing the application's color scheme
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Watchlist storage
        self.watchlist = {}  # {ticker: {price, change, change_pct, last_updated, data}}
        self.watchlist_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "stock_watchlist.json"
        )
        # Alerts storage  {ticker: [{type, threshold, triggered, created_at}, ...]}
        self.alerts_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "stock_alerts.json"
        )
        self.alerts = {}

        # Load saved watchlist and alerts
        self.load_watchlist()
        self.load_alerts()
        
        # Create the user interface
        self.create_ui()
        
        # Auto-refresh watchlist on load
        if self.watchlist:
            self.refresh_all_stocks()

    def create_ui(self):
        """Create the user interface"""
        # Title
        title_label = tk.Label(
            self.parent,
            text="📈 Stock Monitor",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Description
        info_label = tk.Label(
            self.parent,
            text="Track stocks in your watchlist. Add VTI, AAPL, or any ticker!",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        info_label.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        input_frame.pack(pady=20)
        
        # Ticker entry
        tk.Label(
            input_frame,
            text="Ticker:",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT, padx=5)
        
        self.ticker_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 12),
            width=15
        )
        self.ticker_entry.pack(side=tk.LEFT, padx=5)
        self.ticker_entry.bind("<Return>", lambda e: self.add_to_watchlist())
        
        # Add button
        tk.Button(
            input_frame,
            text="⭐ Add to Watchlist",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['accent'],
            fg="white",
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            cursor="hand2",
            command=self.add_to_watchlist,
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Refresh all button
        tk.Button(
            input_frame,
            text="🔄 Refresh All",
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            cursor="hand2",
            command=self.refresh_all_stocks,
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Watchlist section
        watchlist_header = tk.Frame(self.parent, bg=self.colors['content_bg'])
        watchlist_header.pack(pady=(20, 10), padx=40, fill=tk.X)
        
        tk.Label(
            watchlist_header,
            text="📊 Your Watchlist",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        self.watchlist_count = tk.Label(
            watchlist_header,
            text=f"({len(self.watchlist)} stocks)",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        self.watchlist_count.pack(side=tk.LEFT, padx=10)
        
        # Scrollable watchlist container
        self.watchlist_frame = tk.Frame(
            self.parent,
            bg=self.colors['content_bg']
        )
        self.watchlist_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self.watchlist_frame,
            bg=self.colors['content_bg'],
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            self.watchlist_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['content_bg'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Display watchlist
        self.display_watchlist()
        
        # Status label
        self.status_label = tk.Label(
            self.parent,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        self.status_label.pack(pady=10)
    
    def _on_mousewheel(self, event):
        try:
            # Check if canvas still exists before scrolling
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass # Ignore errors if the window is closed
    
    def add_to_watchlist(self):
        """Add a stock to the watchlist"""
        ticker = self.ticker_entry.get().strip().upper()
        
        if not ticker:
            messagebox.showwarning("Input Required", "Please enter a stock ticker!")
            return
        
        if ticker in self.watchlist:
            messagebox.showinfo("Already Tracked", f"{ticker} is already in your watchlist!")
            return
        
        # Show loading
        self.status_label.config(text=f"Adding {ticker}...", fg=self.colors['accent'])
        self.parent.update()
        
        # Fetch initial data
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='2d')  # Get 2 days to calculate change
            
            if hist.empty:
                messagebox.showerror("Invalid Ticker", f"Could not find stock: {ticker}")
                self.status_label.config(text="")
                return
            
            # Get current price and calculate change
            current_price = hist['Close'].iloc[-1]
            
            # Calculate change
            if len(hist) > 1:
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
            else:
                change = 0
                change_pct = 0
            
            # Add to watchlist
            self.watchlist[ticker] = {
                'price': float(current_price),
                'change': float(change),
                'change_pct': float(change_pct),
                'last_updated': datetime.now().isoformat(),
                'data': hist
            }
            
            # Save watchlist
            self.save_watchlist()
            
            # Clear input
            self.ticker_entry.delete(0, tk.END)
            
            # Refresh display
            self.display_watchlist()
            
            # Send notification
            self.send_notification(
                f"Added {ticker}",
                f"{ticker} added to watchlist at ${current_price:.2f}",
                notification_type="info"
            )
            
            self.status_label.config(
                text=f"✓ {ticker} added to watchlist!",
                fg=self.colors['success']
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add {ticker}: {str(e)}")
            self.status_label.config(text="")
    
    def remove_from_watchlist(self, ticker):
        """Remove a stock from the watchlist"""
        if ticker in self.watchlist:
            del self.watchlist[ticker]
            self.save_watchlist()
            self.display_watchlist()
            
            self.status_label.config(
                text=f"✓ {ticker} removed from watchlist",
                fg=self.colors['text_dim']
            )
    
    def refresh_stock(self, ticker):
        """Refresh data for a single stock"""
        if ticker not in self.watchlist:
            return
        
        self.status_label.config(text=f"Refreshing {ticker}...", fg=self.colors['accent'])
        self.parent.update()
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='2d')
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                # Calculate change
                if len(hist) > 1:
                    prev_price = hist['Close'].iloc[-2]
                    change = current_price - prev_price
                    change_pct = (change / prev_price) * 100
                else:
                    change = 0
                    change_pct = 0
                
                # Update watchlist
                self.watchlist[ticker]['price'] = float(current_price)
                self.watchlist[ticker]['change'] = float(change)
                self.watchlist[ticker]['change_pct'] = float(change_pct)
                self.watchlist[ticker]['last_updated'] = datetime.now().isoformat()
                self.watchlist[ticker]['data'] = hist
                
                self.save_watchlist()
                self.check_alerts(ticker, float(current_price))
                self.display_watchlist()

                self.status_label.config(
                    text=f"✓ {ticker} refreshed: ${current_price:.2f}",
                    fg=self.colors['success']
                )
        except Exception as e:
            self.status_label.config(
                text=f"✗ Failed to refresh {ticker}",
                fg=self.colors['danger']
            )
    
    def refresh_all_stocks(self):
        """Refresh all stocks in watchlist"""
        if not self.watchlist:
            messagebox.showinfo("Empty Watchlist", "Add some stocks to your watchlist first!")
            return
        
        self.status_label.config(text="Refreshing all stocks...", fg=self.colors['accent'])
        self.parent.update()
        
        # Refresh in background thread
        def _refresh():
            for ticker in list(self.watchlist.keys()):
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='2d')
                    
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        
                        if len(hist) > 1:
                            prev_price = hist['Close'].iloc[-2]
                            change = current_price - prev_price
                            change_pct = (change / prev_price) * 100
                        else:
                            change = 0
                            change_pct = 0
                        
                        self.watchlist[ticker]['price'] = float(current_price)
                        self.watchlist[ticker]['change'] = float(change)
                        self.watchlist[ticker]['change_pct'] = float(change_pct)
                        self.watchlist[ticker]['last_updated'] = datetime.now().isoformat()
                        self.watchlist[ticker]['data'] = hist
                        self.parent.after(0, lambda t=ticker, p=float(current_price): self.check_alerts(t, p))
                except:
                    pass  # Skip failed tickers

            # Update UI on main thread
            self.parent.after(0, self.save_watchlist)
            self.parent.after(0, self.display_watchlist)
            self.parent.after(0, lambda: self.status_label.config(
                text="✓ All stocks refreshed!",
                fg=self.colors['success']
            ))
        
        threading.Thread(target=_refresh, daemon=True).start()
    
    def display_watchlist(self):
        """Display all stocks in watchlist"""
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Update count
        self.watchlist_count.config(text=f"({len(self.watchlist)} stocks)")
        
        # Empty state
        if not self.watchlist:
            empty_label = tk.Label(
                self.scrollable_frame,
                text="📊 Your watchlist is empty!\n\nAdd stocks like VTI, AAPL, TSLA to track them over time.",
                font=("Segoe UI", 12),
                bg=self.colors['content_bg'],
                fg=self.colors['text_dim'],
                justify=tk.CENTER
            )
            empty_label.pack(pady=50)
            return
        
        # Display each stock
        for ticker, data in sorted(self.watchlist.items()):
            self.create_stock_card(ticker, data)
    
    def create_stock_card(self, ticker, data):
        """Create a card for a stock"""
        price = data['price']
        change = data['change']
        change_pct = data['change_pct']
        last_updated = data.get('last_updated', 'Unknown')
        
        # Determine color based on change
        if change > 0:
            change_color = self.colors['success']
            arrow = "▲"
        elif change < 0:
            change_color = self.colors['danger']
            arrow = "▼"
        else:
            change_color = self.colors['text_dim']
            arrow = "━"
        
        # Card frame
        card = tk.Frame(
            self.scrollable_frame,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=2
        )
        card.pack(fill=tk.X, padx=5, pady=5)
        
        # Header (ticker and actions)
        header = tk.Frame(card, bg=self.colors['card_bg'])
        header.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        # Ticker name (left)
        tk.Label(
            header,
            text=ticker,
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Actions (right)
        actions = tk.Frame(header, bg=self.colors['card_bg'])
        actions.pack(side=tk.RIGHT)
        
        tk.Button(
            actions,
            text="📈 Plot",
            font=("Segoe UI", 9),
            bg=self.colors['accent'],
            fg="white",
            cursor="hand2",
            command=lambda t=ticker: self.plot_stock(t),
            padx=10,
            pady=3
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            actions,
            text="🔄",
            font=("Segoe UI", 9),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            cursor="hand2",
            command=lambda t=ticker: self.refresh_stock(t),
            padx=8,
            pady=3
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            actions,
            text="🔔 Alert",
            font=("Segoe UI", 9),
            bg=self.colors['warning'],
            fg="white",
            cursor="hand2",
            command=lambda t=ticker, p=price: self.open_alert_dialog(t, p),
            padx=8,
            pady=3
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            actions,
            text="✕",
            font=("Segoe UI", 9),
            bg=self.colors['danger'],
            fg="white",
            cursor="hand2",
            command=lambda t=ticker: self.remove_from_watchlist(t),
            padx=8,
            pady=3
        ).pack(side=tk.LEFT, padx=2)
        
        # Price section
        price_frame = tk.Frame(card, bg=self.colors['card_bg'])
        price_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Current price
        tk.Label(
            price_frame,
            text=f"${price:.2f}",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Change
        tk.Label(
            price_frame,
            text=f"  {arrow} ${abs(change):.2f} ({change_pct:+.2f}%)",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=change_color
        ).pack(side=tk.LEFT, padx=10)
        
        # Last updated
        try:
            updated_time = datetime.fromisoformat(last_updated)
            time_str = updated_time.strftime("%I:%M %p")
        except:
            time_str = "Unknown"
        
        tk.Label(
            card,
            text=f"Last updated: {time_str}",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        ).pack(anchor=tk.W, padx=15, pady=(0, 15))
    
    def plot_stock(self, ticker):
        """Plot historical data for a stock"""
        if ticker not in self.watchlist:
            return
        
        data = self.watchlist[ticker].get('data')
        if data is None or data.empty:
            messagebox.showwarning("No Data", f"No data available for {ticker}")
            return
        
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, data['Close'], label='Close Price', linewidth=2)
            plt.title(f"{ticker} Stock Price", fontsize=16, fontweight='bold')
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Price ($)", fontsize=12)
            plt.legend(fontsize=11)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Plot Error", f"Failed to plot {ticker}: {str(e)}")
    
    def save_watchlist(self):
        """Save watchlist to file"""
        try:
            # Convert to serializable format
            save_data = {}
            for ticker, data in self.watchlist.items():
                save_data[ticker] = {
                    'price': data['price'],
                    'change': data['change'],
                    'change_pct': data['change_pct'],
                    'last_updated': data['last_updated']
                    # Don't save 'data' DataFrame (not JSON serializable)
                }
            
            with open(self.watchlist_file, 'w') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Error saving watchlist: {e}")
    
    def load_watchlist(self):
        """Load watchlist from file"""
        try:
            if os.path.exists(self.watchlist_file):
                with open(self.watchlist_file, 'r') as f:
                    self.watchlist = json.load(f)
                
                # Initialize 'data' key for each stock (will be populated on refresh)
                for ticker in self.watchlist:
                    self.watchlist[ticker]['data'] = None
        except Exception as e:
            print(f"Error loading watchlist: {e}")
            self.watchlist = {}
    
    # ── Alert system ──────────────────────────────────────────────────────────

    def load_alerts(self):
        """Load price alerts from file."""
        try:
            if os.path.exists(self.alerts_file):
                with open(self.alerts_file, 'r') as f:
                    self.alerts = json.load(f)
        except Exception as e:
            print(f"Error loading alerts: {e}")
            self.alerts = {}

    def save_alerts(self):
        """Persist alerts to disk."""
        try:
            os.makedirs(os.path.dirname(self.alerts_file), exist_ok=True)
            with open(self.alerts_file, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")

    def open_alert_dialog(self, ticker, current_price):
        """Open a dialog to create or view alerts for a ticker."""
        from tkinter import simpledialog
        win = tk.Toplevel(self.parent)
        win.title(f"🔔 Alerts — {ticker}")
        win.configure(bg=self.colors['background'])
        win.resizable(False, False)
        win.geometry("360x400")
        win.grab_set()

        tk.Label(win, text=f"🔔  Price Alerts for {ticker}",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']).pack(pady=(16, 4))
        tk.Label(win, text=f"Current price: ${current_price:.2f}",
                 font=("Segoe UI", 10),
                 bg=self.colors['background'], fg=self.colors['text_dim']).pack(pady=(0, 12))

        # ── Add new alert ──────────────────────────────────────────────────
        add_frame = tk.Frame(win, bg=self.colors['card_bg'], pady=10, padx=12)
        add_frame.pack(fill=tk.X, padx=14)
        tk.Label(add_frame, text="New alert:", font=("Segoe UI", 10, "bold"),
                 bg=self.colors['card_bg'], fg=self.colors['text']).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        alert_type_var = tk.StringVar(value="above")
        for i, (val, lbl) in enumerate([("above", "Price above $"), ("below", "Price below $"), ("pct_up", "Change % ≥"), ("pct_down", "Change % ≤ −")]):
            tk.Radiobutton(add_frame, text=lbl, variable=alert_type_var, value=val,
                           font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text'],
                           selectcolor=self.colors['background'],
                           activebackground=self.colors['card_bg']).grid(row=1 + i // 2, column=i % 2, sticky="w")

        threshold_entry = tk.Entry(add_frame, font=("Segoe UI", 11), width=10,
                                   bg=self.colors['background'], fg=self.colors['text'],
                                   insertbackground=self.colors['text'])
        threshold_entry.grid(row=3, column=0, columnspan=2, pady=(8, 4), sticky="w")

        def add_alert():
            try:
                val = float(threshold_entry.get().strip())
            except ValueError:
                return
            ticker_alerts = self.alerts.setdefault(ticker, [])
            ticker_alerts.append({
                'type': alert_type_var.get(),
                'threshold': val,
                'triggered': False,
                'created_at': datetime.now().isoformat()
            })
            self.save_alerts()
            refresh_list()
            threshold_entry.delete(0, tk.END)

        tk.Button(add_frame, text="➕ Add Alert", command=add_alert,
                  bg=self.colors['accent'], fg="white", font=("Segoe UI", 10),
                  relief=tk.FLAT, cursor="hand2").grid(row=3, column=2, padx=8, pady=(8, 4))

        # ── Existing alerts list ───────────────────────────────────────────
        tk.Label(win, text="Active alerts:", font=("Segoe UI", 10, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']).pack(anchor="w", padx=16, pady=(10, 2))

        list_frame = tk.Frame(win, bg=self.colors['background'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14)

        def refresh_list():
            for w in list_frame.winfo_children():
                try: w.destroy()
                except: pass
            ticker_alerts = self.alerts.get(ticker, [])
            if not ticker_alerts:
                tk.Label(list_frame, text="No alerts set.", font=("Segoe UI", 10),
                         bg=self.colors['background'], fg=self.colors['text_dim']).pack(pady=6)
                return
            labels = {'above': 'Above $', 'below': 'Below $', 'pct_up': 'Change ≥ +', 'pct_down': 'Change ≤ −'}
            for idx, alert in enumerate(ticker_alerts):
                row = tk.Frame(list_frame, bg=self.colors['card_bg'])
                row.pack(fill=tk.X, pady=2)
                status = "✅" if alert['triggered'] else "⏳"
                lbl = labels.get(alert['type'], '')
                threshold = alert['threshold']
                suffix = "%" if alert['type'] in ('pct_up', 'pct_down') else ""
                tk.Label(row, text=f"{status} {lbl}{threshold:.2f}{suffix}",
                         font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text']).pack(side=tk.LEFT, padx=8, pady=4)

                def delete_alert(i=idx):
                    self.alerts[ticker].pop(i)
                    if not self.alerts[ticker]:
                        del self.alerts[ticker]
                    self.save_alerts()
                    refresh_list()

                tk.Button(row, text="✕", command=delete_alert,
                          bg=self.colors['danger'], fg="white", font=("Segoe UI", 8),
                          relief=tk.FLAT, cursor="hand2", padx=5).pack(side=tk.RIGHT, padx=4)

        refresh_list()

    def check_alerts(self, ticker, current_price):
        """Check all active alerts for ticker against current_price and fire if triggered."""
        ticker_alerts = self.alerts.get(ticker, [])
        if not ticker_alerts:
            return
        changed = False
        for alert in ticker_alerts:
            if alert.get('triggered'):
                continue
            atype = alert['type']
            threshold = alert['threshold']
            fired = False
            if atype == 'above' and current_price >= threshold:
                fired = True
                msg = f"{ticker} hit ${current_price:.2f} (alert: above ${threshold:.2f})"
            elif atype == 'below' and current_price <= threshold:
                fired = True
                msg = f"{ticker} hit ${current_price:.2f} (alert: below ${threshold:.2f})"
            elif atype == 'pct_up':
                pct = self.watchlist.get(ticker, {}).get('change_pct', 0)
                if pct >= threshold:
                    fired = True
                    msg = f"{ticker} up {pct:.2f}% today (alert: ≥ +{threshold:.2f}%)"
            elif atype == 'pct_down':
                pct = self.watchlist.get(ticker, {}).get('change_pct', 0)
                if pct <= -threshold:
                    fired = True
                    msg = f"{ticker} down {abs(pct):.2f}% today (alert: ≤ −{threshold:.2f}%)"
            if fired:
                alert['triggered'] = True
                changed = True
                self.send_notification(f"🔔 Price Alert: {ticker}", msg, notification_type="warning")
        if changed:
            self.save_alerts()

    def send_notification(self, title, message, notification_type="info"):
        """Send notification (optional integration)"""
        try:
            from notification_manager import send_notification
            send_notification(
                title=title,
                message=message,
                module="Stock Monitor",
                notification_type=notification_type,
                play_sound=False
            )
        except:
            pass  # Notification system not available
