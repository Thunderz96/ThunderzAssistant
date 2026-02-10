"""
Thunderz Assistant - Enhanced UI Version
Version: 1.6.0

This is a modernized version with:
- Menu bar (File, View, Help)
- Status bar at bottom
- Tooltips on all buttons
- Keyboard shortcuts
- Built-in help system
- Better visual design

To test: python main_enhanced.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu
import sys
import os
import webbrowser
import config

# Add modules directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import all modules
from weather_module import WeatherModule
from dashboard_module import DashboardModule
from news_module import NewsModule
from pomodoro_module import PomodoroModule
from system_monitor_module import SystemMonitorModule
from stock_monitor_module import StockMonitorModule
from file_organizer_module import FileOrganizerModule
from glizzy_module import GlizzyModule
from discord_integration_module import DiscordIntegrationModule
from discord_presence_module import set_instance
from notification_center_module import NotificationCenterModule
from notification_manager import get_unread_count, register_observer
from tray_manager import TrayManager


class ToolTip:
    """Tooltip class for showing help text on hover"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#1E293B", foreground="#E2E8F0",
                        relief='solid', borderwidth=1,
                        font=("Segoe UI", 9), padx=8, pady=4)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class ThunderzAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Thunderz Assistant v1.6.0")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # Set window icon (taskbar/title bar)
        icon_path = os.path.join(os.path.dirname(__file__), 'thunderz_icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass  # Fallback to default icon if error
        
        self.api_key = config.NEWS_API_KEY
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            self.api_key = None
        
        self.colors = {
            'primary': '#1E40AF', 'secondary': '#1E293B', 'accent': '#3B82F6',
            'background': '#0F172A', 'content_bg': '#1E293B', 'card_bg': '#334155',
            'text': '#E2E8F0', 'text_dim': '#94A3B8', 'button_hover': '#2563EB',
            'success': '#10B981', 'warning': '#F59E0B', 'danger': '#EF4444'
        }
        
        self.root.configure(bg=self.colors['background'])
        self.current_module = "Dashboard"
        
        # Initialize system tray (before UI so it can reference widgets)
        self.tray_manager = None
        
        self.create_menu_bar()
        self.create_ui()
        self.create_status_bar()
        self.show_dashboard()
        
        # Initialize system tray icon
        try:
            self.tray_manager = TrayManager(self.root)
            # Override window close behavior (minimize to tray instead of exit)
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        except Exception as e:
            print(f"System tray not available: {e}")
            # Fall back to normal close behavior
            self.root.protocol("WM_DELETE_WINDOW", self.root.quit)
    
    def on_window_close(self):
        """
        Handle window close button.
        Modern behavior: Minimize to tray instead of exiting.
        """
        if self.tray_manager:
            self.tray_manager.hide_window()
        else:
            self.root.quit()
    
    def create_menu_bar(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self.refresh_current_module, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Dashboard", command=self.show_dashboard, accelerator="Ctrl+1")
        view_menu.add_command(label="News", command=self.show_news, accelerator="Ctrl+2")
        view_menu.add_command(label="Weather", command=self.show_weather, accelerator="Ctrl+3")
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start Guide", command=self.show_quick_start)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="Documentation", command=self.open_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        self.root.bind("<F5>", lambda e: self.refresh_current_module())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-1>", lambda e: self.show_dashboard())
        self.root.bind("<Control-2>", lambda e: self.show_news())
        self.root.bind("<Control-3>", lambda e: self.show_weather())
    
    def create_ui(self):
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        sidebar = tk.Frame(main_container, bg=self.colors['secondary'], width=220)
        sidebar.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 10))
        sidebar.pack_propagate(False)
        
        sidebar_header = tk.Frame(sidebar, bg=self.colors['primary'])
        sidebar_header.pack(fill=tk.X)
        tk.Label(sidebar_header, text="⚡ Modules", font=("Segoe UI", 16, "bold"),
                bg=self.colors['primary'], fg="white", pady=15).pack()
        
        modules = [
            ("📊", "Dashboard", "Overview of your day", self.show_dashboard),
            ("🔔", "Notifications", "View all notifications", self.show_notifications),
            ("📰", "News", "Latest breaking news", self.show_news),
            ("🌤️", "Weather", "Current weather conditions", self.show_weather),
            ("🍅", "Pomodoro", "Focus timer for productivity", self.show_pomodoro),
            ("💻", "System", "Monitor system resources", self.show_system_monitor),
            ("📈", "Stocks", "Track stock market prices", self.show_stock_monitor),
            ("📁", "Organizer", "Clean up messy folders", self.show_file_organizer),
            ("🎮", "Discord", "Discord presence & messages", self.show_discord_integration),
            ("🌭", "Glizzy", "Roll the dice for fun!", self.show_glizzy_module),
        ]
        
        self.module_buttons = {}
        self.notification_badge = None
        for icon, name, tooltip, command in modules:
            # Create button frame to hold button + badge
            btn_container = tk.Frame(sidebar, bg=self.colors['secondary'])
            btn_container.pack(fill=tk.X, padx=10, pady=3)
            
            btn = tk.Button(btn_container, text=f"{icon}  {name}", font=("Segoe UI", 11),
                          bg=self.colors['card_bg'], fg=self.colors['text'],
                          activebackground=self.colors['button_hover'], activeforeground="white",
                          relief=tk.FLAT, cursor="hand2",
                          command=lambda n=name, c=command: self.switch_module(n, c),
                          anchor="w", padx=15, pady=10)
            btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            ToolTip(btn, tooltip)
            self.module_buttons[name] = btn
            
            # Add badge for Notifications module
            if name == "Notifications":
                unread = get_unread_count()
                if unread > 0:
                    self.notification_badge = tk.Label(
                        btn_container,
                        text=str(unread) if unread < 100 else "99+",
                        font=("Segoe UI", 9, "bold"),
                        bg=self.colors['danger'],
                        fg="white",
                        padx=6,
                        pady=2
                    )
                    self.notification_badge.pack(side=tk.RIGHT, padx=5)
        
        # Register observer for notification changes to update badge
        register_observer(self.update_notification_badge)
        
        help_frame = tk.Frame(sidebar, bg=self.colors['secondary'])
        help_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        help_btn = tk.Button(help_frame, text="❓ Help", font=("Segoe UI", 11, "bold"),
                           bg=self.colors['accent'], fg="white", relief=tk.FLAT,
                           cursor="hand2", command=self.show_quick_start, pady=8)
        help_btn.pack(fill=tk.X, padx=10)
        ToolTip(help_btn, "View quick start guide and tips")
        
        self.content_frame = tk.Frame(main_container, bg=self.colors['content_bg'],
                                     relief=tk.RAISED, borderwidth=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
    
    def create_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg=self.colors['secondary'], height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_module_label = tk.Label(self.status_bar, text=f"📍 {self.current_module}",
                                           font=("Segoe UI", 9), bg=self.colors['secondary'],
                                           fg=self.colors['text'], anchor="w", padx=10)
        self.status_module_label.pack(side=tk.LEFT)
        
        self.status_tip_label = tk.Label(self.status_bar, text="💡 Tip: Use Ctrl+1,2,3 for quick navigation",
                                        font=("Segoe UI", 9), bg=self.colors['secondary'],
                                        fg=self.colors['text_dim'])
        self.status_tip_label.pack(side=tk.LEFT, expand=True)
        
        tk.Label(self.status_bar, text="v1.6.0", font=("Segoe UI", 9),
                bg=self.colors['secondary'], fg=self.colors['text_dim'],
                anchor="e", padx=10).pack(side=tk.RIGHT)
    
    def update_status(self, module_name, tip=None):
        self.status_module_label.config(text=f"📍 {module_name}")
        if tip:
            self.status_tip_label.config(text=f"💡 {tip}")
    
    def switch_module(self, name, command):
        self.current_module = name
        for btn_name, btn in self.module_buttons.items():
            if btn_name == name:
                btn.config(bg=self.colors['accent'], fg="white")
            else:
                btn.config(bg=self.colors['card_bg'], fg=self.colors['text'])
        self.update_status(name)
        command()
        
        # Update Discord presence automatically
        self.update_discord_presence(name)
    
    def update_discord_presence(self, module_name):
        """Update Discord Rich Presence when switching modules"""
        from discord_presence_module import set_presence
        
        # Custom messages per module
        discord_messages = {
            "Dashboard": "Viewing dashboard",
            "Notifications": "Checking notifications",
            "News": "Reading breaking news",
            "Weather": "Checking weather forecast",
            "Pomodoro": "Using focus timer",
            "System": "Monitoring system resources",
            "Stocks": "Tracking stock portfolio",
            "Organizer": "Organizing files",
            "Discord": "Configuring Discord presence",
            "Glizzy": "Rolling for Glizzy 🌭"
        }
        
        message = discord_messages.get(module_name, f"Using {module_name}")
        set_presence(module_name, message)
    
    def refresh_current_module(self):
        modules = {"Dashboard": self.show_dashboard, "News": self.show_news,
                  "Weather": self.show_weather, "Pomodoro": self.show_pomodoro,
                  "System": self.show_system_monitor, "Stocks": self.show_stock_monitor,
                  "Organizer": self.show_file_organizer, "Discord": self.show_discord_integration,
                  "Notifications": self.show_notifications, "Glizzy": self.show_glizzy_module}
        if self.current_module in modules:
            modules[self.current_module]()
    
    def update_notification_badge(self):
        """Update notification badge count"""
        try:
            unread = get_unread_count()
            if self.notification_badge:
                if unread > 0:
                    self.notification_badge.config(
                        text=str(unread) if unread < 100 else "99+"
                    )
                    self.notification_badge.pack(side=tk.RIGHT, padx=5)
                else:
                    self.notification_badge.pack_forget()
        except:
            pass  # Widget might not exist yet
    
    def show_dashboard(self):
        self.clear_content()
        DashboardModule(self.content_frame, self.colors)
        self.update_status("Dashboard", "Your daily overview at a glance")
    
    def show_notifications(self):
        self.clear_content()
        NotificationCenterModule(self.content_frame, self.colors)
        self.update_status("Notifications", "View and manage all notifications")
    
    def show_weather(self):
        self.clear_content()
        WeatherModule(self.content_frame, self.colors)
        self.update_status("Weather", "Check weather for any city")
    
    def show_news(self):
        self.clear_content()
        if not self.api_key:
            self.show_api_key_help()
            return
        news_module = NewsModule(self.api_key, self.content_frame, self.colors)
        news_module.display_news()
        self.update_status("News", "Stay updated with breaking news")
    
    def show_pomodoro(self):
        self.clear_content()
        PomodoroModule(self.content_frame, self.colors)
        self.update_status("Pomodoro", "Focus with 25-minute work sessions")
    
    def show_system_monitor(self):
        self.clear_content()
        SystemMonitorModule(self.content_frame, self.colors)
        self.update_status("System", "Monitor CPU, RAM, and disk usage")
    
    def show_stock_monitor(self):
        self.clear_content()
        StockMonitorModule(self.content_frame, self.colors)
        self.update_status("Stocks", "Track your portfolio in real-time")
    
    def show_file_organizer(self):
        self.clear_content()
        FileOrganizerModule(self.content_frame, self.colors)
        self.update_status("Organizer", "Clean up Downloads folder automatically")
    
    def show_discord_integration(self):
        self.clear_content()
        DiscordIntegrationModule(self.content_frame, self.colors)
        self.update_status("Discord", "Discord presence & send messages")
    
    def show_glizzy_module(self):
        self.clear_content()
        GlizzyModule(self.content_frame, self.colors)
        self.update_status("Glizzy", "Roll the dice and see what happens!")
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_api_key_help(self):
        self.clear_content()
        help_container = tk.Frame(self.content_frame, bg=self.colors['content_bg'])
        help_container.pack(expand=True)
        tk.Label(help_container, text="📰 News API Setup Required",
                font=("Segoe UI", 20, "bold"), bg=self.colors['content_bg'],
                fg=self.colors['text']).pack(pady=20)
        instructions = """To enable the News feature:

1. Get a free API key from NewsAPI.org
2. Open config.py in the app folder
3. Replace 'YOUR_API_KEY_HERE' with your key
4. Restart the application

The News feature will then be available!"""
        tk.Label(help_container, text=instructions, font=("Segoe UI", 12),
                bg=self.colors['content_bg'], fg=self.colors['text'],
                justify=tk.LEFT).pack(pady=20)
        tk.Button(help_container, text="Open NewsAPI.org",
                 command=lambda: webbrowser.open("https://newsapi.org/register"),
                 font=("Segoe UI", 11), bg=self.colors['accent'], fg="white",
                 cursor="hand2", padx=20, pady=10).pack(pady=10)
    
    def show_quick_start(self):
        guide = """Thunderz Assistant - Quick Start Guide

🎯 Getting Started:
• Use the sidebar to navigate between modules
• Each module has its own unique functionality
• Hover over buttons for helpful tooltips

⌨️ Keyboard Shortcuts:
• Ctrl+1, 2, 3: Quick module navigation
• F5: Refresh current module
• Ctrl+Q: Quit application

📊 Popular Modules:
• Dashboard: Daily overview with time, tasks, and media
• Weather: Real-time weather for any location
• Pomodoro: Focus timer for productivity
• File Organizer: Auto-organize Downloads folder

💡 Pro Tips:
• Check the status bar for module-specific tips
• Use File menu to access settings
• Visit Help > Documentation for detailed guides

Need more help? Check Help > Documentation!"""
        messagebox.showinfo("Quick Start Guide", guide)
    
    def show_shortcuts(self):
        shortcuts = """Keyboard Shortcuts

Navigation:
• Ctrl+1: Dashboard
• Ctrl+2: News
• Ctrl+3: Weather

Actions:
• F5: Refresh current module
• Ctrl+Q: Quit application

Window:
• Alt+F4: Close window"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def open_documentation(self):
        docs_path = os.path.join(os.path.dirname(__file__), "docs")
        if os.path.exists(docs_path):
            os.startfile(docs_path)
        else:
            messagebox.showinfo("Documentation", "Documentation folder not found.\n\nCheck the GitHub repository for docs.")
    
    def show_about(self):
        about_text = """⚡ Thunderz Assistant v1.6.0

A modular productivity suite with:
• Dashboard & Task Management
• Weather & News Updates
• Pomodoro Timer
• System Monitoring
• Stock Tracking
• File Organization
• And more!

Created with ❤️ by Thunderz
Python + Tkinter"""
        messagebox.showinfo("About Thunderz Assistant", about_text)


def main():
    root = tk.Tk()
    app = ThunderzAssistant(root)
    root.mainloop()


if __name__ == "__main__":
    main()
