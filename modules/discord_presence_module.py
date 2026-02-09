"""
Discord Rich Presence Module
Shows your current Thunderz Assistant activity on Discord

This module runs in the background and updates your Discord status
to show what you're currently doing in Thunderz Assistant.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

try:
    from pypresence import Presence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    import config
except ImportError:
    config = None


class DiscordPresenceModule:
    """
    Discord Rich Presence integration for Thunderz Assistant.
    
    Shows your current activity on Discord:
    - Current module (Dashboard, Weather, etc.)
    - Pomodoro timer status
    - Spotify playback
    - And more!
    """
    
    def __init__(self, parent, colors):
        """
        Initialize the Discord Presence module.
        
        Args:
            parent: Parent tkinter frame
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.colors = colors
        
        # Discord RPC state
        self.rpc = None
        self.connected = False
        self.enabled = False
        self.start_time = int(time.time())
        
        # Current status tracking
        self.current_module = "Dashboard"
        self.current_details = "Idle"
        
        # Update thread
        self.update_thread = None
        self.running = False
        
        # Check if pypresence is installed
        if not PYPRESENCE_AVAILABLE:
            self.show_install_warning()
            return
        
        # Check if Discord app ID is configured
        if not config or not hasattr(config, 'DISCORD_APP_ID'):
            self.show_config_warning()
            return
        
        self.app_id = config.DISCORD_APP_ID
        
        # Build UI
        self.create_ui()
    
    def create_ui(self):
        """Create the module user interface"""
        # Title
        title_label = tk.Label(
            self.parent,
            text="🎮 Discord Rich Presence",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(
            self.parent,
            text="Show your Thunderz Assistant activity on Discord",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        desc_label.pack(pady=5)
        
        # Status frame
        status_frame = tk.Frame(
            self.parent,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=2
        )
        status_frame.pack(pady=20, padx=40, fill=tk.X)
        
        # Connection status
        self.status_label = tk.Label(
            status_frame,
            text="⚪ Disconnected",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        )
        self.status_label.pack(pady=15)
        
        # Current activity
        self.activity_label = tk.Label(
            status_frame,
            text="No activity",
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        self.activity_label.pack(pady=5, padx=20)
        
        # Control buttons frame
        button_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        button_frame.pack(pady=20)
        
        # Connect button
        self.connect_button = tk.Button(
            button_frame,
            text="🔌 Connect to Discord",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['accent'],
            fg="white",
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            command=self.toggle_connection,
            cursor="hand2",
            padx=20,
            pady=10
        )
        self.connect_button.pack(side=tk.LEFT, padx=10)
        
        # Settings frame
        settings_frame = tk.LabelFrame(
            self.parent,
            text=" Settings ",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            relief=tk.RAISED,
            borderwidth=2
        )
        settings_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # Show elapsed time option
        self.show_elapsed_var = tk.BooleanVar(value=True)
        elapsed_check = tk.Checkbutton(
            settings_frame,
            text="Show elapsed time",
            variable=self.show_elapsed_var,
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['background'],
            activebackground=self.colors['card_bg'],
            activeforeground=self.colors['text']
        )
        elapsed_check.pack(anchor=tk.W, padx=20, pady=10)
        
        # Auto-connect on startup option
        self.auto_connect_var = tk.BooleanVar(value=False)
        auto_check = tk.Checkbutton(
            settings_frame,
            text="Auto-connect on startup",
            variable=self.auto_connect_var,
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['background'],
            activebackground=self.colors['card_bg'],
            activeforeground=self.colors['text']
        )
        auto_check.pack(anchor=tk.W, padx=20, pady=10)
        
        # Info section
        info_frame = tk.Frame(settings_frame, bg=self.colors['card_bg'])
        info_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        info_text = """ℹ️ What will be shown:
        
• Current module (Dashboard, Weather, etc.)
• Pomodoro timer countdown (if active)
• Spotify track (if playing)
• Time spent in app

Your Discord profile will show:
"Playing Thunderz Assistant"
"""
        
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim'],
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)
        
        # Help button
        help_button = tk.Button(
            self.parent,
            text="❓ Setup Help",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            command=self.show_help,
            cursor="hand2",
            padx=15,
            pady=5
        )
        help_button.pack(pady=10)
    
    def toggle_connection(self):
        """Connect or disconnect from Discord"""
        if self.connected:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connect to Discord"""
        if self.connected:
            return
        
        try:
            # Create RPC instance
            self.rpc = Presence(self.app_id)
            self.rpc.connect()
            
            # Update status
            self.connected = True
            self.enabled = True
            self.start_time = int(time.time())
            
            # Update UI
            self.status_label.config(
                text="🟢 Connected",
                fg=self.colors['success']
            )
            self.connect_button.config(
                text="🔌 Disconnect",
                bg=self.colors['danger']
            )
            
            # Start update thread
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            # Initial update
            self.update_presence("Dashboard", "Just started")
            
            messagebox.showinfo(
                "Connected!",
                "Discord Rich Presence is now active!\n\n"
                "Check your Discord profile to see it in action."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Connection Failed",
                f"Could not connect to Discord:\n\n{str(e)}\n\n"
                "Make sure Discord is running and you're logged in."
            )
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from Discord"""
        if not self.connected:
            return
        
        try:
            # Stop update thread
            self.running = False
            if self.update_thread:
                self.update_thread.join(timeout=1.0)
            
            # Clear presence and disconnect
            if self.rpc:
                self.rpc.clear()
                self.rpc.close()
            
            # Update state
            self.connected = False
            self.enabled = False
            self.rpc = None
            
            # Update UI
            self.status_label.config(
                text="⚪ Disconnected",
                fg=self.colors['text_dim']
            )
            self.connect_button.config(
                text="🔌 Connect to Discord",
                bg=self.colors['accent']
            )
            self.activity_label.config(text="No activity")
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    def update_presence(self, module, details):
        """
        Update Discord presence with new status.
        
        Args:
            module: Current module name (e.g., "Dashboard", "Pomodoro")
            details: Activity details (e.g., "Organizing files", "25:00 remaining")
        """
        if not self.connected or not self.rpc:
            return
        
        try:
            # Store current status
            self.current_module = module
            self.current_details = details
            
            # Build presence data
            presence_data = {
                'state': f"📍 {module}",
                'details': details,
                'large_image': 'thunderz_logo',
                'large_text': 'Thunderz Assistant',
            }
            
            # Add elapsed time if enabled
            if self.show_elapsed_var.get():
                presence_data['start'] = self.start_time
            
            # Update Discord
            self.rpc.update(**presence_data)
            
            # Update UI
            self.activity_label.config(
                text=f"{module}: {details}"
            )
            
        except Exception as e:
            print(f"Error updating presence: {e}")
            # Try to reconnect if connection was lost
            if "Connection" in str(e):
                self.disconnect()
    
    def _update_loop(self):
        """Background thread to keep presence alive"""
        while self.running:
            try:
                # Update every 15 seconds to keep connection alive
                if self.connected and self.rpc:
                    self.update_presence(self.current_module, self.current_details)
                time.sleep(15)
            except Exception as e:
                print(f"Update loop error: {e}")
                break
    
    def show_install_warning(self):
        """Show warning that pypresence is not installed"""
        warning_label = tk.Label(
            self.parent,
            text="⚠️ Discord Rich Presence Not Available",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['warning']
        )
        warning_label.pack(pady=40)
        
        message = """The pypresence library is not installed.

To use Discord Rich Presence:

1. Run: install_discord_presence.bat
   OR
2. Run: pip install pypresence

Then restart Thunderz Assistant."""
        
        message_label = tk.Label(
            self.parent,
            text=message,
            font=("Segoe UI", 12),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        message_label.pack(pady=20)
    
    def show_config_warning(self):
        """Show warning that Discord app ID is not configured"""
        warning_label = tk.Label(
            self.parent,
            text="⚠️ Discord App ID Not Configured",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['warning']
        )
        warning_label.pack(pady=40)
        
        message = """Discord Application ID is missing from config.py

To set up Discord Rich Presence:

1. Visit: https://discord.com/developers/applications
2. Create a new application
3. Copy your Application ID
4. Add to config.py:
   DISCORD_APP_ID = "YOUR_ID_HERE"

See docs/DISCORD_SETUP.md for detailed instructions."""
        
        message_label = tk.Label(
            self.parent,
            text=message,
            font=("Segoe UI", 12),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        message_label.pack(pady=20)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Discord Rich Presence Help

SETUP:
1. Get Application ID from Discord Developer Portal
2. Add to config.py: DISCORD_APP_ID = "YOUR_ID"
3. Click "Connect to Discord"

WHAT IT SHOWS:
• Current module you're using
• Activity details (Pomodoro timer, etc.)
• Time elapsed in app

PRIVACY:
• Only shows when connected
• You control when it's active
• Disconnect anytime

TROUBLESHOOTING:
• Make sure Discord app is running
• Check you're not in "invisible" mode
• Verify Application ID is correct

See docs/DISCORD_SETUP.md for full guide."""
        
        messagebox.showinfo("Discord Rich Presence Help", help_text)
    
    def __del__(self):
        """Cleanup when module is destroyed"""
        try:
            self.disconnect()
        except:
            pass


# Global instance for main.py to access
_discord_presence_instance = None

def set_presence(module, details):
    """
    Update Discord presence from other modules.
    
    Args:
        module: Module name (e.g., "Pomodoro")
        details: Activity details (e.g., "25:00 remaining")
    
    Usage in other modules:
        from discord_presence_module import set_presence
        set_presence("Pomodoro", "25:00 remaining")
    """
    global _discord_presence_instance
    if _discord_presence_instance and _discord_presence_instance.connected:
        _discord_presence_instance.update_presence(module, details)

def set_instance(instance):
    """Set the global Discord presence instance"""
    global _discord_presence_instance
    _discord_presence_instance = instance
