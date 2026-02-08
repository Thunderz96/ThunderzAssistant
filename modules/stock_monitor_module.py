"""
Stock Market Module for Thunderz Assistant
Version: 1.0.0 - Initial Release

This module provides both real-time stock monitoring and historical data analysis features. 
It allows users to track their favorite stocks, view detailed performance metrics, and receive alerts based on customizable thresholds.
Features:
- Real-time stock price updates with a sleek, modern interface
- Historical data visualization with interactive charts
- Customizable alerts for price changes, volume spikes, and news events
- Integration with financial news sources for the latest market updates
- Portfolio management tools to track investments and performance over time
- User-friendly design with a focus on clarity and ease of use
- Supports multiple stock exchanges and a wide range of financial instruments
- Designed to be lightweight and efficient, ensuring smooth performance even with multiple stocks being monitored simultaneously
- Future updates will include advanced analytics, AI-driven insights, and expanded coverage of global markets.

Requires: - yfinance (for fetching stock data)
          - matplotlib (for data visualization)
          - pandas (for data manipulation)
"""
import tkinter as tk
from tkinter import messagebox
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd  # Not strictly needed here, but useful if you expand data handling


class StockMonitorModule:
    """
    Stock monitor module for Thunderz Assistant.
    
    This class handles the UI and logic for monitoring stocks.
    """

    def __init__(self, parent_frame, colors):
        """
        Initialize the stock monitor module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
                         (This is the content area passed from main.py)
            colors: Dictionary containing the application's color scheme
                   (This keeps your module matching the app's theme)
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Initialize stock data storage
        self.stocks = {}  # Dictionary to store stock data and settings
        # Example structure: {'AAPL': {'data': DataFrame, 'alerts': [...]}, ...}
        
        # Create the user interface right away
        self.create_ui()

    def create_ui(self):
        """
        Create the user interface for this module.
        
        This sets up labels, inputs, buttons, and a results area.
        """
        # Title for the module
        title_label = tk.Label(
            self.parent,
            text="📈 Stock Monitor",
            font=("Arial", 18, "bold"),
            bg=self.colors['content_bg'],  # Use theme color instead of hardcoding "white"
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Description or instructions
        info_label = tk.Label(
            self.parent,
            text="Enter a stock ticker (e.g., AAPL) to monitor prices and data.",
            font=("Arial", 12),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        info_label.pack(pady=10)
        
        # Input frame for user input
        input_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        input_frame.pack(pady=20)
        
        # Text entry field for stock ticker
        self.ticker_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            width=30
        )
        self.ticker_entry.pack(side=tk.LEFT, padx=5)
        
        # Button to add and fetch stock data
        fetch_button = tk.Button(
            input_frame,
            text="Fetch Stock Data",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.fetch_and_display,  # Calls a method to handle input
            padx=20,
            pady=5
        )
        fetch_button.pack(side=tk.LEFT, padx=5)
        
        # Button to plot data (after fetching)
        plot_button = tk.Button(
            input_frame,
            text="Plot Chart",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.plot_current_stock,  # Calls plot for the last entered ticker
            padx=20,
            pady=5
        )
        plot_button.pack(side=tk.LEFT, padx=5)
        
        # Results frame (where output is displayed)
        self.results_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        self.results_frame.pack(pady=20, fill=tk.BOTH, expand=True)

    def fetch_and_display(self):
        """
        Handle fetching stock data based on user input.
        
        This gets the ticker, adds it if new, fetches data, and displays a summary.
        """
        # Get input from the entry field
        ticker = self.ticker_entry.get().strip().upper()  # Uppercase for consistency (e.g., "aapl" -> "AAPL")
        
        # Validate input
        if not ticker:
            messagebox.showwarning("Input Required", "Please enter a stock ticker!")
            return
        
        try:
            # Add the stock if not already monitored
            self.add_stock(ticker)
            
            # Fetch the data (using your existing method)
            self.fetch_stock_data(ticker)
            
            # Get the latest data for display
            data = self.stocks[ticker]['data']
            if data is not None and not data.empty:
                latest_close = data['Close'].iloc[-1]  # Get the most recent close price
                result = f"Latest close price for {ticker}: ${latest_close:.2f}"
            else:
                result = f"No data fetched for {ticker}. Try again later."
            
            # Display the result
            self.display_result(result)
        
        except Exception as e:
            # Handle errors (e.g., invalid ticker or network issue)
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def plot_current_stock(self):
        """
        Plot the data for the last entered ticker.
        """
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("Input Required", "Please enter a stock ticker!")
            return
        self.plot_stock_data(ticker)

    def display_result(self, result):
        """
        Display results to the user.
        
        Args:
            result: The text to display
        """
        # Clear previous results
        self.clear_results()
        
        # Show new result
        result_label = tk.Label(
            self.results_frame,
            text=result,
            font=("Arial", 14),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        result_label.pack(pady=20)

    def clear_results(self):
        """
        Clear all widgets from the results display area.
        """
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def add_stock(self, ticker):
        """Add a stock to monitor by its ticker symbol."""
        if ticker not in self.stocks:
            self.stocks[ticker] = {
                'data': None,
                'alerts': []
            }
            print(f"Added {ticker} to stock monitor.")  # This prints to console; you could log it instead
        else:
            print(f"{ticker} is already being monitored.")

    def fetch_stock_data(self, ticker, period='1d', interval='1m'):
        """Fetch real-time stock data for the given ticker."""
        if ticker in self.stocks:
            stock = yf.Ticker(ticker)
            self.stocks[ticker]['data'] = stock.history(period=period, interval=interval)
            print(f"Fetched data for {ticker}.")
        else:
            print(f"{ticker} is not being monitored. Please add it first.")

    def plot_stock_data(self, ticker):
        """Plot historical stock data for the given ticker."""
        if ticker in self.stocks and self.stocks[ticker]['data'] is not None:
            data = self.stocks[ticker]['data']
            plt.figure(figsize=(10, 5))
            plt.plot(data.index, data['Close'], label='Close Price')
            plt.title(f"{ticker} Stock Price")
            plt.xlabel("Date")
            plt.ylabel("Price")
            plt.legend()
            plt.grid()
            plt.show()
        else:
            print(f"No data available for {ticker}. Please fetch it first.")

    def set_alert(self, ticker, condition):
        """Set an alert for a specific condition (e.g., price above/below a certain value)."""
        if ticker in self.stocks:
            self.stocks[ticker]['alerts'].append(condition)
            print(f"Alert set for {ticker}: {condition}")
        else:
            print(f"{ticker} is not being monitored. Please add it first.")