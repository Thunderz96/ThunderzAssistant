"""
System Tray Manager for Thunderz Assistant
Provides system tray icon with menu and notifications

Features:
- Always-on tray icon
- Right-click menu
- Minimize to tray
- Restore from tray
- Notification badge
- Quick actions
"""

import sys
import os
from PIL import Image
from PIL import ImageDraw
import pystray
from pystray import MenuItem as item
import threading


class TrayManager:
    """
    Manages system tray icon for Thunderz Assistant.
    
    Modern app behavior:
    - Window "X" button minimizes to tray (doesn't exit)
    - Tray icon always visible
    - Right-click for menu
    - Left-click to show/hide window
    - Badge shows unread notifications
    """
    
    def __init__(self, main_window, app_name="Thunderz Assistant"):
        """
        Initialize tray manager.
        
        Args:
            main_window: The main tkinter window
            app_name: Application name for tray tooltip
        """
        self.main_window = main_window
        self.app_name = app_name
        self.icon = None
        self.is_visible = True
        
        # Icon image
        self.icon_image = self.create_icon_image()
        
        # Start tray icon in background thread
        self.start_tray()
    
    def create_icon_image(self):
        """Create the tray icon image"""
        # Try to load custom icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'thunderz_icon.png')
        
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except:
                pass
        
        # Fallback: Create simple icon
        return self.create_default_icon()
    
    def create_default_icon(self):
        """Create a simple default icon if custom icon not found"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Dark blue circle
        draw.ellipse([2, 2, size-2, size-2], fill='#1E293B', outline='#3B82F6', width=3)
        
        # Lightning bolt (simple)
        bolt = [
            (32, 10),
            (25, 32),
            (35, 32),
            (22, 54),
            (28, 35),
            (20, 35),
        ]
        draw.polygon(bolt, fill='#F59E0B')
        
        return image
    
    def create_menu(self):
        """Create the tray menu"""
        from notification_manager import get_unread_count
        
        # Get unread notification count
        unread = get_unread_count()
        notif_text = f"🔔 Notifications ({unread} unread)" if unread > 0 else "🔔 Notifications"
        
        return pystray.Menu(
            item(
                '📊 Show Thunderz Assistant',
                self.show_window,
                default=True  # Bold, runs on left-click
            ),
            item(
                notif_text,
                self.open_notifications
            ),
            pystray.Menu.SEPARATOR,
            item(
                '⏸️ Pause Pomodoro',
                self.toggle_pomodoro,
                enabled=self.is_pomodoro_running
            ),
            item(
                '📈 Open Stock Monitor',
                self.open_stock_monitor
            ),
            item(
                '🍅 Open Pomodoro',
                self.open_pomodoro
            ),
            pystray.Menu.SEPARATOR,
            item(
                '❌ Exit',
                self.quit_app
            )
        )
    
    def start_tray(self):
        """Start the system tray icon"""
        def run_tray():
            self.icon = pystray.Icon(
                self.app_name,
                self.icon_image,
                self.app_name,
                menu=self.create_menu()
            )
            self.icon.run()
        
        # Run in background thread
        tray_thread = threading.Thread(target=run_tray, daemon=True)
        tray_thread.start()
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.main_window.after(0, self._show_window_safe)
    
    def _show_window_safe(self):
        """Safely show window on main thread"""
        self.main_window.deiconify()  # Restore from minimized
        self.main_window.lift()       # Bring to front
        self.main_window.focus_force()  # Give focus
        self.is_visible = True
    
    def hide_window(self):
        """Hide window to tray"""
        self.main_window.withdraw()  # Hide window
        self.is_visible = False
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()
    
    def open_notifications(self, icon=None, item=None):
        """Open notification center"""
        self.main_window.after(0, lambda: self._open_module("Notifications"))
    
    def open_stock_monitor(self, icon=None, item=None):
        """Open stock monitor"""
        self.main_window.after(0, lambda: self._open_module("Stocks"))
    
    def open_pomodoro(self, icon=None, item=None):
        """Open pomodoro"""
        self.main_window.after(0, lambda: self._open_module("Pomodoro"))
    
    def _open_module(self, module_name):
        """Open a specific module"""
        self.show_window()
        # Simulate button click
        if hasattr(self.main_window, 'module_buttons'):
            if module_name in self.main_window.module_buttons:
                self.main_window.module_buttons[module_name].invoke()
    
    def is_pomodoro_running(self, item=None):
        """Check if pomodoro is running (for menu enable/disable)"""
        # TODO: Integrate with pomodoro module
        return True  # Always enabled for now
    
    def toggle_pomodoro(self, icon=None, item=None):
        """Toggle pomodoro timer"""
        # TODO: Integrate with pomodoro module
        self.open_pomodoro()
    
    def quit_app(self, icon=None, item=None):
        """Completely quit the application"""
        if self.icon:
            self.icon.stop()
        self.main_window.quit()
        sys.exit(0)
    
    def update_badge(self, count):
        """Update notification badge on icon"""
        # Create new icon with badge
        if count > 0:
            # TODO: Draw badge number on icon
            pass
        
        # Update icon
        if self.icon:
            self.icon.icon = self.icon_image
            self.icon.menu = self.create_menu()
    
    def on_window_close(self):
        """
        Handle window close button (X).
        
        Modern behavior: Minimize to tray instead of exiting.
        """
        self.hide_window()
        return "break"  # Prevent default close behavior
