"""
Discord Webhook Module
Send messages and notifications to Discord channels

This module lets you send messages to Discord without needing a bot.
Perfect for notifications, alerts, and productivity updates!
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import json
from datetime import datetime
import threading


class DiscordWebhookModule:
    """
    Discord Webhook integration - send messages to Discord channels.
    
    Features:
    - Send custom messages
    - Post Pomodoro completions
    - Send system alerts
    - Daily productivity reports
    - Quick message templates
    """
    
    def __init__(self, parent, colors):
        """
        Initialize Discord Webhook module.
        
        Args:
            parent: Parent tkinter frame
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.colors = colors
        
        # Check if webhook URL is configured
        try:
            import config
            self.webhook_url = getattr(config, 'DISCORD_WEBHOOK_URL', None)
        except:
            self.webhook_url = None
        
        self.create_ui()
    
    def create_ui(self):
        """Create the user interface"""
        # Title
        title_label = tk.Label(
            self.parent,
            text="💬 Discord Messages",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(
            self.parent,
            text="Send messages and notifications to your Discord server",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        desc_label.pack(pady=5)
        
        if not self.webhook_url:
            self.show_setup_required()
            return
        
        # Main content frame
        content_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        content_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # Quick Actions frame
        quick_frame = tk.LabelFrame(
            content_frame,
            text=" Quick Actions ",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            relief=tk.RAISED,
            borderwidth=2
        )
        quick_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Quick action buttons
        quick_buttons_frame = tk.Frame(quick_frame, bg=self.colors['card_bg'])
        quick_buttons_frame.pack(pady=15, padx=20)
        
        tk.Button(
            quick_buttons_frame,
            text="🎯 Pomodoro Complete",
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg="white",
            command=self.send_pomodoro_complete,
            cursor="hand2",
            padx=15,
            pady=8
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        tk.Button(
            quick_buttons_frame,
            text="📊 Daily Report",
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg="white",
            command=self.send_daily_report,
            cursor="hand2",
            padx=15,
            pady=8
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        tk.Button(
            quick_buttons_frame,
            text="💻 System Status",
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg="white",
            command=self.send_system_status,
            cursor="hand2",
            padx=15,
            pady=8
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        tk.Button(
            quick_buttons_frame,
            text="📈 Stock Update",
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg="white",
            command=self.send_stock_update,
            cursor="hand2",
            padx=15,
            pady=8
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Custom Message frame
        message_frame = tk.LabelFrame(
            content_frame,
            text=" Custom Message ",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            relief=tk.RAISED,
            borderwidth=2
        )
        message_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Message input
        tk.Label(
            message_frame,
            text="Type your message:",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        self.message_text = scrolledtext.ScrolledText(
            message_frame,
            height=6,
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            bg="white",
            fg=self.colors['text']
        )
        self.message_text.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        
        # Send button
        send_frame = tk.Frame(message_frame, bg=self.colors['card_bg'])
        send_frame.pack(pady=15)
        
        tk.Button(
            send_frame,
            text="📤 Send to Discord",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['accent'],
            fg="white",
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            command=self.send_custom_message,
            cursor="hand2",
            padx=25,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            send_frame,
            text="🧹 Clear",
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            command=lambda: self.message_text.delete("1.0", tk.END),
            cursor="hand2",
            padx=25,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.parent,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        self.status_label.pack(pady=5)
        
        # Help button
        tk.Button(
            self.parent,
            text="❓ Setup Help",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            command=self.show_help,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(pady=10)
    
    def show_setup_required(self):
        """Show setup instructions when webhook URL is not configured"""
        warning_label = tk.Label(
            self.parent,
            text="⚠️ Discord Webhook Not Configured",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['warning']
        )
        warning_label.pack(pady=40)
        
        message = """To send messages to Discord:

1. Go to your Discord server
2. Right-click a channel → Edit Channel
3. Go to Integrations → Webhooks
4. Click "New Webhook"
5. Copy the Webhook URL
6. Add to config.py:
   DISCORD_WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"

Then restart Thunderz Assistant.

See docs/DISCORD_WEBHOOK_SETUP.md for detailed guide."""
        
        message_label = tk.Label(
            self.parent,
            text=message,
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        message_label.pack(pady=20, padx=40)
        
        tk.Button(
            self.parent,
            text="📚 View Setup Guide",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['accent'],
            fg="white",
            command=self.show_help,
            cursor="hand2",
            padx=20,
            pady=10
        ).pack(pady=20)
    
    def send_webhook(self, content, embeds=None):
        """
        Send message to Discord webhook.
        
        Args:
            content: Message text
            embeds: Optional list of embed objects
        """
        if not self.webhook_url:
            messagebox.showerror("Error", "Webhook URL not configured!")
            return False
        
        try:
            payload = {"content": content}
            if embeds:
                payload["embeds"] = embeds
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                return True
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to send message.\nStatus code: {response.status_code}"
                )
                return False
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to send message:\n{str(e)}"
            )
            return False
    
    def send_custom_message(self):
        """Send custom message from text box"""
        message = self.message_text.get("1.0", tk.END).strip()
        
        if not message:
            messagebox.showwarning("Empty Message", "Please enter a message first!")
            return
        
        self.status_label.config(text="📤 Sending...", fg=self.colors['accent'])
        self.parent.update()
        
        def _send():
            success = self.send_webhook(message)
            if success:
                self.parent.after(0, lambda: self.status_label.config(
                    text="✅ Message sent!",
                    fg=self.colors['success']
                ))
                self.parent.after(0, lambda: self.message_text.delete("1.0", tk.END))
            else:
                self.parent.after(0, lambda: self.status_label.config(
                    text="❌ Failed to send",
                    fg=self.colors['danger']
                ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_pomodoro_complete(self):
        """Send Pomodoro completion notification"""
        # Get pomodoro stats
        try:
            import json
            import os
            from datetime import date
            
            stats_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "pomodoro_stats.json"
            )
            
            total_today = 0
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    today = date.today().isoformat()
                    total_today = stats.get(today, 0)
            
            message = f"🍅 **Pomodoro Complete!**\n\nCompleted {total_today} pomodoros today\nFocus time: {total_today * 25} minutes"
            
            embeds = [{
                "title": "🎯 Productivity Update",
                "description": f"Just completed a Pomodoro session!",
                "color": 3066993,  # Green
                "fields": [
                    {
                        "name": "Today's Progress",
                        "value": f"{total_today} pomodoros",
                        "inline": True
                    },
                    {
                        "name": "Focus Time",
                        "value": f"{total_today * 25} minutes",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat()
            }]
            
        except:
            message = "🍅 **Pomodoro Complete!**\n\nJust finished a focus session!"
            embeds = None
        
        self.status_label.config(text="📤 Sending...", fg=self.colors['accent'])
        self.parent.update()
        
        def _send():
            success = self.send_webhook(message, embeds)
            if success:
                self.parent.after(0, lambda: self.status_label.config(
                    text="✅ Pomodoro notification sent!",
                    fg=self.colors['success']
                ))
            else:
                self.parent.after(0, lambda: self.status_label.config(
                    text="❌ Failed to send",
                    fg=self.colors['danger']
                ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_daily_report(self):
        """Send daily productivity report"""
        try:
            import json
            import os
            from datetime import date
            
            # Get pomodoro stats
            stats_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "pomodoro_stats.json"
            )
            
            total_today = 0
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    today = date.today().isoformat()
                    total_today = stats.get(today, 0)
            
            focus_time = total_today * 25
            hours = focus_time // 60
            minutes = focus_time % 60
            
            embeds = [{
                "title": "📊 Daily Productivity Report",
                "description": f"Summary for {date.today().strftime('%B %d, %Y')}",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "🍅 Pomodoros Completed",
                        "value": str(total_today),
                        "inline": True
                    },
                    {
                        "name": "⏱️ Total Focus Time",
                        "value": f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                        "inline": True
                    },
                    {
                        "name": "📈 Status",
                        "value": "Great job!" if total_today >= 8 else "Keep going!" if total_today >= 4 else "Get started!",
                        "inline": False
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Thunderz Assistant"
                }
            }]
            
            message = "📊 **Daily Report**"
            
        except:
            message = "📊 **Daily Productivity Report**\n\nCheck your stats in Thunderz Assistant!"
            embeds = None
        
        self.status_label.config(text="📤 Sending...", fg=self.colors['accent'])
        self.parent.update()
        
        def _send():
            success = self.send_webhook(message, embeds)
            if success:
                self.parent.after(0, lambda: self.status_label.config(
                    text="✅ Daily report sent!",
                    fg=self.colors['success']
                ))
            else:
                self.parent.after(0, lambda: self.status_label.config(
                    text="❌ Failed to send",
                    fg=self.colors['danger']
                ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_system_status(self):
        """Send system status update"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            embeds = [{
                "title": "💻 System Status",
                "color": 10181046,  # Purple
                "fields": [
                    {
                        "name": "CPU Usage",
                        "value": f"{cpu_percent}%",
                        "inline": True
                    },
                    {
                        "name": "RAM Usage",
                        "value": f"{ram_percent}%",
                        "inline": True
                    },
                    {
                        "name": "Status",
                        "value": "🟢 Normal" if cpu_percent < 80 and ram_percent < 80 else "🟡 High Usage",
                        "inline": False
                    }
                ],
                "timestamp": datetime.utcnow().isoformat()
            }]
            
            message = "💻 **System Status Update**"
            
        except:
            message = "💻 **System Status**\n\nSystem is running normally!"
            embeds = None
        
        self.status_label.config(text="📤 Sending...", fg=self.colors['accent'])
        self.parent.update()
        
        def _send():
            success = self.send_webhook(message, embeds)
            if success:
                self.parent.after(0, lambda: self.status_label.config(
                    text="✅ System status sent!",
                    fg=self.colors['success']
                ))
            else:
                self.parent.after(0, lambda: self.status_label.config(
                    text="❌ Failed to send",
                    fg=self.colors['danger']
                ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_stock_update(self):
        """Send stock portfolio update"""
        message = "📈 **Stock Portfolio Update**\n\nCheck your portfolio in Thunderz Assistant!"
        
        embeds = [{
            "title": "📈 Portfolio Status",
            "description": "Current market status",
            "color": 3066993,  # Green
            "timestamp": datetime.utcnow().isoformat()
        }]
        
        self.status_label.config(text="📤 Sending...", fg=self.colors['accent'])
        self.parent.update()
        
        def _send():
            success = self.send_webhook(message, embeds)
            if success:
                self.parent.after(0, lambda: self.status_label.config(
                    text="✅ Stock update sent!",
                    fg=self.colors['success']
                ))
            else:
                self.parent.after(0, lambda: self.status_label.config(
                    text="❌ Failed to send",
                    fg=self.colors['danger']
                ))
        
        threading.Thread(target=_send, daemon=True).start()
    
    def show_help(self):
        """Show help dialog"""
        help_text = """Discord Webhook Help

SETUP:
1. Go to your Discord server
2. Right-click a channel → Edit Channel
3. Integrations → Webhooks → New Webhook
4. Copy Webhook URL
5. Add to config.py: DISCORD_WEBHOOK_URL = "URL"

QUICK ACTIONS:
🎯 Pomodoro Complete - Post completion notification
📊 Daily Report - Send productivity summary
💻 System Status - Post system stats
📈 Stock Update - Share portfolio status

CUSTOM MESSAGES:
Type anything and send it to your Discord channel!

TIPS:
- Messages appear instantly in Discord
- Rich embeds show formatted data
- Great for logging and tracking
- Share progress with team/friends

See docs/DISCORD_WEBHOOK_SETUP.md for full guide."""
        
        messagebox.showinfo("Discord Webhook Help", help_text)


# Auto-send functions for other modules to use
def send_to_discord(message, embeds=None):
    """
    Send message to Discord webhook from any module.
    
    Args:
        message: Message text
        embeds: Optional list of embed objects
    
    Usage:
        from discord_webhook_module import send_to_discord
        send_to_discord("Pomodoro complete!")
    """
    try:
        import config
        webhook_url = getattr(config, 'DISCORD_WEBHOOK_URL', None)
        
        if not webhook_url:
            return False
        
        payload = {"content": message}
        if embeds:
            payload["embeds"] = embeds
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 204
        
    except:
        return False
