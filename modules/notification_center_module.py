"""
Notification Center Module
UI for viewing and managing notifications

Displays all notifications from all modules in a centralized view.
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import threading
from notification_manager import (
    get_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    dismiss_notification,
    clear_all_notifications,
    execute_notification_action,
    toggle_dnd,
    is_dnd,
    register_observer,
    unregister_observer
)


class NotificationCenterModule:
    """
    Notification Center - view and manage all notifications.
    
    Features:
    - View all notifications
    - Mark as read/unread
    - Dismiss notifications
    - Execute notification actions
    - Do Not Disturb mode
    - Auto-refresh
    """
    
    def __init__(self, parent, colors):
        """
        Initialize Notification Center module.
        
        Args:
            parent: Parent tkinter frame
            colors: Color scheme dictionary
        """
        self.parent = parent
        self.colors = colors
        
        # State
        self.filter_unread_only = False
        self.auto_refresh = True
        
        # Register as observer for notification changes
        register_observer(self.on_notifications_changed)
        
        self.create_ui()
        
        # Initial load
        self.refresh_notifications()
    
    def create_ui(self):
        """Create the user interface"""
        # Title
        title_label = tk.Label(
            self.parent,
            text="🔔 Notification Center",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Controls frame
        controls_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        controls_frame.pack(pady=10, padx=40, fill=tk.X)
        
        # Left controls
        left_controls = tk.Frame(controls_frame, bg=self.colors['content_bg'])
        left_controls.pack(side=tk.LEFT)
        
        # Unread count badge
        unread_count = get_unread_count()
        self.unread_badge = tk.Label(
            left_controls,
            text=f"📬 {unread_count} Unread",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['accent'] if unread_count > 0 else self.colors['card_bg'],
            fg="white",
            padx=15,
            pady=5
        )
        self.unread_badge.pack(side=tk.LEFT, padx=5)
        
        # Filter toggle
        self.filter_button = tk.Button(
            left_controls,
            text="📋 Show All",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            command=self.toggle_filter,
            cursor="hand2",
            padx=15,
            pady=5
        )
        self.filter_button.pack(side=tk.LEFT, padx=5)
        
        # Right controls
        right_controls = tk.Frame(controls_frame, bg=self.colors['content_bg'])
        right_controls.pack(side=tk.RIGHT)
        
        # DND toggle
        dnd_active = is_dnd()
        self.dnd_button = tk.Button(
            right_controls,
            text="🔕 DND" if dnd_active else "🔔 DND Off",
            font=("Segoe UI", 10),
            bg=self.colors['warning'] if dnd_active else self.colors['card_bg'],
            fg="white" if dnd_active else self.colors['text'],
            command=self.toggle_dnd,
            cursor="hand2",
            padx=15,
            pady=5
        )
        self.dnd_button.pack(side=tk.RIGHT, padx=5)
        
        # Mark all read button
        tk.Button(
            right_controls,
            text="✓ Mark All Read",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            command=self.mark_all_read,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT, padx=5)
        
        # Clear all button
        tk.Button(
            right_controls,
            text="🗑️ Clear All",
            font=("Segoe UI", 10),
            bg=self.colors['danger'],
            fg="white",
            command=self.clear_all,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT, padx=5)
        
        # Notifications container (scrollable)
        self.notifications_frame = tk.Frame(
            self.parent,
            bg=self.colors['content_bg']
        )
        self.notifications_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self.notifications_frame,
            bg=self.colors['content_bg'],
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            self.notifications_frame,
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
        
        # Info label at bottom
        self.info_label = tk.Label(
            self.parent,
            text="",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        self.info_label.pack(pady=10)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def refresh_notifications(self):
        """Refresh the notification list"""
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get notifications
        notifications = get_notifications(unread_only=self.filter_unread_only)
        
        # Update unread badge
        unread_count = get_unread_count()
        self.unread_badge.config(
            text=f"📬 {unread_count} Unread",
            bg=self.colors['accent'] if unread_count > 0 else self.colors['card_bg']
        )
        
        # Display notifications
        if not notifications:
            # Empty state
            empty_label = tk.Label(
                self.scrollable_frame,
                text="📭 No notifications yet!\n\nNotifications from all modules will appear here.",
                font=("Segoe UI", 12),
                bg=self.colors['content_bg'],
                fg=self.colors['text_dim'],
                justify=tk.CENTER
            )
            empty_label.pack(pady=50)
            return
        
        # Display each notification
        for notif in notifications:
            self.create_notification_card(notif)
        
        # Update info label
        self.info_label.config(
            text=f"Showing {len(notifications)} notification{'s' if len(notifications) != 1 else ''}"
        )
    
    def create_notification_card(self, notif):
        """Create a notification card widget"""
        # Determine colors based on type and read status
        if notif.get("type") == "error":
            border_color = self.colors['danger']
            icon = "🔴"
        elif notif.get("type") == "warning":
            border_color = self.colors['warning']
            icon = "🟡"
        elif notif.get("type") == "success":
            border_color = self.colors['success']
            icon = "🟢"
        else:  # info
            border_color = self.colors['accent']
            icon = "🔵"
        
        # Background based on read status
        bg_color = self.colors['card_bg'] if notif.get("read") else self.colors['content_bg']
        
        # Card frame
        card = tk.Frame(
            self.scrollable_frame,
            bg=bg_color,
            relief=tk.RAISED,
            borderwidth=2,
            highlightbackground=border_color,
            highlightthickness=2
        )
        card.pack(fill=tk.X, padx=5, pady=5)
        
        # Header frame
        header = tk.Frame(card, bg=bg_color)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Icon + Title
        title_frame = tk.Frame(header, bg=bg_color)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            title_frame,
            text=f"{icon} {notif.get('title', 'Notification')}",
            font=("Segoe UI", 11, "bold"),
            bg=bg_color,
            fg=self.colors['text'],
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        # Module badge
        tk.Label(
            title_frame,
            text=f"  [{notif.get('module', 'System')}]",
            font=("Segoe UI", 9),
            bg=bg_color,
            fg=self.colors['text_dim']
        ).pack(side=tk.LEFT)
        
        # Timestamp
        timestamp = self.format_timestamp(notif.get('timestamp'))
        tk.Label(
            header,
            text=timestamp,
            font=("Segoe UI", 9),
            bg=bg_color,
            fg=self.colors['text_dim']
        ).pack(side=tk.RIGHT)
        
        # Message
        tk.Label(
            card,
            text=notif.get('message', ''),
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=self.colors['text'],
            wraplength=700,
            justify=tk.LEFT,
            anchor=tk.W
        ).pack(fill=tk.X, padx=10, pady=5)
        
        # Actions frame
        actions_frame = tk.Frame(card, bg=bg_color)
        actions_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # Action buttons
        if notif.get('actions'):
            for action in notif['actions']:
                tk.Button(
                    actions_frame,
                    text=action['label'],
                    font=("Segoe UI", 9),
                    bg=self.colors['accent'],
                    fg="white",
                    command=lambda nid=notif['id'], aid=action['id']: self.execute_action(nid, aid),
                    cursor="hand2",
                    padx=10,
                    pady=3
                ).pack(side=tk.LEFT, padx=2)
        
        # Mark as read button (if unread)
        if not notif.get('read'):
            tk.Button(
                actions_frame,
                text="✓ Mark Read",
                font=("Segoe UI", 9),
                bg=self.colors['card_bg'],
                fg=self.colors['text'],
                command=lambda nid=notif['id']: self.mark_read(nid),
                cursor="hand2",
                padx=10,
                pady=3
            ).pack(side=tk.LEFT, padx=2)
        
        # Dismiss button
        tk.Button(
            actions_frame,
            text="✕ Dismiss",
            font=("Segoe UI", 9),
            bg=self.colors['danger'],
            fg="white",
            command=lambda nid=notif['id']: self.dismiss(nid),
            cursor="hand2",
            padx=10,
            pady=3
        ).pack(side=tk.RIGHT)
    
    def format_timestamp(self, iso_timestamp):
        """Format timestamp as relative time"""
        try:
            notif_time = datetime.fromisoformat(iso_timestamp)
            now = datetime.now()
            diff = now - notif_time
            
            seconds = diff.total_seconds()
            
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                mins = int(seconds / 60)
                return f"{mins} minute{'s' if mins != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
        except:
            return "Recently"
    
    def toggle_filter(self):
        """Toggle between all notifications and unread only"""
        self.filter_unread_only = not self.filter_unread_only
        
        if self.filter_unread_only:
            self.filter_button.config(text="📬 Unread Only")
        else:
            self.filter_button.config(text="📋 Show All")
        
        self.refresh_notifications()
    
    def toggle_dnd(self):
        """Toggle Do Not Disturb mode"""
        dnd_active = toggle_dnd()
        
        if dnd_active:
            self.dnd_button.config(
                text="🔕 DND",
                bg=self.colors['warning'],
                fg="white"
            )
        else:
            self.dnd_button.config(
                text="🔔 DND Off",
                bg=self.colors['card_bg'],
                fg=self.colors['text']
            )
    
    def mark_read(self, notification_id):
        """Mark notification as read"""
        mark_as_read(notification_id)
        # Refresh will be triggered by observer
    
    def mark_all_read(self):
        """Mark all notifications as read"""
        mark_all_as_read()
        # Refresh will be triggered by observer
    
    def dismiss(self, notification_id):
        """Dismiss notification"""
        dismiss_notification(notification_id)
        # Refresh will be triggered by observer
    
    def clear_all(self):
        """Clear all notifications"""
        from tkinter import messagebox
        if messagebox.askyesno(
            "Clear All Notifications",
            "Are you sure you want to clear all notifications?\n\nThis cannot be undone."
        ):
            clear_all_notifications()
            # Refresh will be triggered by observer
    
    def execute_action(self, notification_id, action_id):
        """Execute a notification action"""
        execute_notification_action(notification_id, action_id)
        # Auto-dismiss after action
        self.dismiss(notification_id)
    
    def on_notifications_changed(self):
        """Called when notifications change (observer pattern)"""
        # Refresh on main thread
        try:
            self.parent.after(0, self.refresh_notifications)
        except:
            pass  # Widget might be destroyed
    
    def __del__(self):
        """Cleanup when module is destroyed"""
        try:
            unregister_observer(self.on_notifications_changed)
        except:
            pass
