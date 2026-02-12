"""
Comprehensive Discord Integration Module
Combines Rich Presence + Webhooks in one module

Features:
- Tab 1: Rich Presence (show your activity)
- Tab 2: Send Messages (webhooks)
"""

import tkinter as tk
from tkinter import ttk
from discord_presence_module import DiscordPresenceModule
from discord_webhook_module import DiscordWebhookModule


class DiscordIntegrationModule:
    """
    Complete Discord integration with tabbed interface.
    
    Tab 1: Rich Presence - Show your activity on Discord profile
    Tab 2: Webhooks - Send messages to Discord channels
    """
    ICON = "🎮"
    PRIORITY = 5  # Show after Weather and Stock modules
    
    def __init__(self, parent, colors):
        """
        Initialize the comprehensive Discord module.
        
        Args:
            parent: Parent tkinter frame
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.colors = colors
        
        self.create_ui()
    
    def create_ui(self):
        """Create tabbed interface"""
        # Title
        title_label = tk.Label(
            self.parent,
            text="🎮 Discord Integration",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(
            self.parent,
            text="Show activity on Discord & send messages to channels",
            font=("Segoe UI", 11),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        desc_label.pack(pady=5)
        
        # Create notebook (tabs)
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure tab style
        style.configure('TNotebook', background=self.colors['content_bg'])
        style.configure('TNotebook.Tab', 
                       padding=[20, 10],
                       font=('Segoe UI', 11, 'bold'))
        
        notebook = ttk.Notebook(self.parent)
        notebook.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # Tab 1: Rich Presence
        presence_frame = tk.Frame(notebook, bg=self.colors['content_bg'])
        notebook.add(presence_frame, text="🎮 Rich Presence")
        
        # Create Rich Presence module in this frame
        DiscordPresenceModule(presence_frame, self.colors)
        
        # Tab 2: Webhooks (Messages)
        webhook_frame = tk.Frame(notebook, bg=self.colors['content_bg'])
        notebook.add(webhook_frame, text="💬 Send Messages")
        
        # Create Webhook module in this frame
        DiscordWebhookModule(webhook_frame, self.colors)
