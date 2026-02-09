"""
Thunderz Assistant - Main Application
Version: 1.5.0
A modular Swiss Army knife application that starts simple and grows over time.

This is the main entry point for the application. It initializes the GUI and
loads available modules.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import config  # Import the config module for API keys


# Add the modules directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import modules
from weather_module import WeatherModule
from dashboard_module import DashboardModule
from news_module import NewsModule
from pomodoro_module import PomodoroModule
from system_monitor_module import SystemMonitorModule
from stock_monitor_module import StockMonitorModule
from file_organizer_module import FileOrganizerModule  


class ThunderzAssistant:
    """
    Main application class for Thunderz Assistant.
    
    This class creates the main window and manages the different modules/features
    that can be added to the application.
    """
    
    def __init__(self, root):
        """
        Initialize the main application window.
        
        Args:
            root: The main tkinter window object
        """
        self.root = root
        self.root.title("Thunderz Assistant v1.5.0")
        self.root.geometry("900x650")
        
        # Load API keys from config
        self.api_key = config.NEWS_API_KEY  # News API key
        
        # Error Handling if API key is missing or not set
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            messagebox.showwarning(
                "News API Key Missing", 
                "News API key not configured.\n\n"
                "To enable the News feature:\n"
                "1. Get a free API key from https://newsapi.org/register\n"
                "2. Open config.py\n"
                "3. Replace 'YOUR_API_KEY_HERE' with your actual key\n\n"
                "Dashboard and Weather will still work!"
            )
            # Don't destroy the app, just disable news feature
            self.api_key = None
            
        

        


     
        # Dark Blue color scheme
        self.colors = {
            'primary': '#1E40AF',      # Rich blue
            'secondary': '#1E293B',    # Dark slate
            'accent': '#3B82F6',       # Bright blue
            'background': '#0F172A',   # Very dark blue-gray
            'content_bg': '#1E293B',   # Dark gray-blue content area
            'card_bg': '#334155',      # Medium dark gray cards
            'text': '#E2E8F0',         # Light gray text
            'text_dim': '#94A3B8',     # Dimmed text
            'button_hover': '#2563EB'  # Bright blue hover
        }
        
        self.root.configure(bg=self.colors['background'])
        
        # Initialize the UI
        self.create_ui()
        
    def create_ui(self):
        """
        Create the user interface components.
        
        This method sets up the main layout with a title, navigation sidebar,
        and content area where different modules will be displayed.
        """
        # Title bar
        title_frame = tk.Frame(self.root, bg=self.colors['primary'], height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="⚡ Thunderz Assistant",
            font=("Arial", 24, "bold"),
            bg=self.colors['primary'],
            fg="white"
        )
        title_label.pack(pady=10)
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sidebar for navigation
        sidebar = tk.Frame(main_container, bg=self.colors['secondary'], width=200)
        sidebar.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 10))
        sidebar.pack_propagate(False)
        
        sidebar_title = tk.Label(
            sidebar,
            text="Tools",
            font=("Arial", 16, "bold"),
            bg=self.colors['secondary'],
            fg="white"
        )
        sidebar_title.pack(pady=20)
        
        # Dashboard button
        dashboard_btn = tk.Button(
            sidebar,
            text="📊  Dashboard",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_dashboard
        )
        dashboard_btn.pack(fill=tk.X, padx=10, pady=5)

        # News button
        news_btn = tk.Button(
            sidebar,
            text="📰  Breaking News",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_news
        )
        news_btn.pack(fill=tk.X, padx=10, pady=5)
                       
        # Weather button
        weather_btn = tk.Button(
            sidebar,
            text="🌤️  Weather",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_weather
        )
        weather_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # Pomodoro Timer button
        pomodoro_btn = tk.Button(
            sidebar,
            text="🍅  Pomodoro",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_pomodoro
        )
        pomodoro_btn.pack(fill=tk.X, padx=10, pady=5)
        
        # System Monitor button
        monitor_btn = tk.Button(
            sidebar,
            text="💻  System Monitor",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_system_monitor
        )
        monitor_btn.pack(fill=tk.X, padx=10, pady=5)

        # Stock Monitor button
        stock_monitor_btn = tk.Button(
            sidebar,
            text="📈  Stock Monitor",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_stock_monitor
        )
        stock_monitor_btn.pack(fill=tk.X, padx=10, pady=5)

        # File Organizer button
        file_organizer_btn = tk.Button(
            sidebar,
            text="📁  File Organizer",
            font=("Arial", 12),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_file_organizer
        )
        file_organizer_btn.pack(fill=tk.X, padx=10, pady=5)
                
        # Content area (where modules will be displayed)
        self.content_frame = tk.Frame(main_container, bg=self.colors['content_bg'], relief=tk.RAISED, borderwidth=2)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        
        # Show dashboard as the default home screen
        self.show_dashboard()
        
    def show_welcome(self):
        """
        Display the welcome screen in the content area.
        
        This is shown when the application first starts, before any module is selected.
        """
        self.clear_content()
        
        welcome_label = tk.Label(
            self.content_frame,
            text="Welcome to Thunderz Assistant!",
            font=("Arial", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        welcome_label.pack(pady=50)
        
        info_label = tk.Label(
            self.content_frame,
            text="Select a tool from the sidebar to get started.",
            font=("Arial", 12),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        info_label.pack()
        
    def show_dashboard(self):
        """
        Display the daily dashboard in the content area.
        
        This is the default home screen that shows on startup.
        """
        self.clear_content()
        DashboardModule(self.content_frame, self.colors)
    
    def show_weather(self):
        """
        Display the weather module in the content area.
        
        This method clears the current content and loads the weather checking module.
        """
        self.clear_content()
        
        # Create and display the weather module
        weather_module = WeatherModule(self.content_frame, self.colors)
    
    def show_news(self):
        """
        Display the news module in the content area.
        
        This method clears the current content and loads the breaking news module.
        """
        self.clear_content()
        
        # Check if API key is configured
        if not self.api_key:
            error_label = tk.Label(
                self.content_frame,
                text="📰 News Feature Not Available\n\n"
                     "To enable breaking news:\n"
                     "1. Get a free API key from:\n"
                     "   https://newsapi.org/register\n\n"
                     "2. Open config.py and add your key to:\n"
                     "   NEWS_API_KEY = 'your_key_here'\n\n"
                     "3. Restart the application",
                font=("Arial", 12),
                bg=self.colors['content_bg'],
                fg=self.colors['text_dim'],
                justify=tk.CENTER
            )
            error_label.pack(pady=50)
            return
        
        # Create and display the news module
        news_module = NewsModule(self.api_key, self.content_frame, self.colors)   
        news_module.display_news()
    
    def show_pomodoro(self):
        """
        Display the Pomodoro timer module in the content area.
        
        This method clears the current content and loads the Pomodoro timer.
        """
        self.clear_content()
        pomodoro_module = PomodoroModule(self.content_frame, self.colors)
    
    def show_system_monitor(self):
        """
        Display the system monitor module in the content area.
        
        This method clears the current content and loads the system resource monitor.
        """
        self.clear_content()
        monitor_module = SystemMonitorModule(self.content_frame, self.colors)
    
    def show_stock_monitor(self):
        """
        Display the stock monitor module in the content area.
        
        This method clears the current content and loads the stock monitoring module.
        """
        self.clear_content()
        stock_monitor_module = StockMonitorModule(self.content_frame, self.colors)
    
    def show_file_organizer(self):
        """
        Display the file organizer module in the content area.
        
        This method clears the current content and loads the file organization tool.
        """
        self.clear_content()
        file_organizer_module = FileOrganizerModule(self.content_frame, self.colors)


    def clear_content(self):
        """
        Clear all widgets from the content area.
        
        This is called before loading a new module to ensure a clean slate.
        """
        for widget in self.content_frame.winfo_children():
            widget.destroy()


def main():
    """
    Main function to start the application.
    
    This creates the main window and starts the tkinter event loop.
    """
    root = tk.Tk()
    app = ThunderzAssistant(root)
    root.mainloop()


# Only run if this file is executed directly (not imported)
if __name__ == "__main__":
    main()
