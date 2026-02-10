"""
Notification Manager - Backend for Notification System
Handles storage, retrieval, and management of notifications

This is a singleton class that manages all notifications across modules.
Other modules can import and use: send_notification(), get_notifications(), etc.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
import threading


class NotificationManager:
    """
    Singleton notification manager for Thunderz Assistant.
    
    Manages notifications from all modules with persistence, actions, and DND mode.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.notifications = []
        self.max_notifications = 100  # Keep last 100 notifications
        self.dnd_mode = False
        self.callbacks = {}  # Store callbacks by notification ID
        self.observers = []  # UI observers to notify of changes
        
        # File path for persistence
        self.notifications_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "notifications.json"
        )
        
        # Load existing notifications
        self.load_notifications()
        
        self._initialized = True
    
    def send_notification(
        self,
        title: str,
        message: str,
        module: str,
        notification_type: str = "info",
        actions: Optional[List[Dict]] = None,
        play_sound: bool = True,
        auto_dismiss: Optional[int] = None
    ) -> str:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            module: Module sending notification (e.g., "Pomodoro")
            notification_type: Type - "info", "success", "warning", "error"
            actions: List of action dicts: [{"label": "View", "callback": callable}]
            play_sound: Whether to play notification sound
            auto_dismiss: Auto-dismiss after N seconds (None = manual dismiss)
        
        Returns:
            Notification ID
        
        Example:
            send_notification(
                "Pomodoro Complete",
                "Great work! Time for a break.",
                "Pomodoro",
                "success",
                actions=[
                    {"label": "View Stats", "callback": show_stats_func},
                    {"label": "Start Break", "callback": start_break_func}
                ]
            )
        """
        # Skip if DND mode (except errors)
        if self.dnd_mode and notification_type != "error":
            return None
        
        # Generate unique ID
        notif_id = f"notif_{int(time.time() * 1000)}_{len(self.notifications)}"
        
        # Create notification
        notification = {
            "id": notif_id,
            "timestamp": datetime.now().isoformat(),
            "type": notification_type,
            "title": title,
            "message": message,
            "module": module,
            "read": False,
            "dismissed": False,
            "sound": play_sound and not self.dnd_mode,
            "auto_dismiss": auto_dismiss
        }
        
        # Store action callbacks separately (can't serialize functions)
        if actions:
            self.callbacks[notif_id] = {}
            notification["actions"] = []
            
            for action in actions:
                action_id = f"{notif_id}_{action['label']}"
                notification["actions"].append({
                    "id": action_id,
                    "label": action["label"]
                })
                
                # Store callback
                if "callback" in action and callable(action["callback"]):
                    self.callbacks[notif_id][action_id] = action["callback"]
        
        # Add to list
        self.notifications.insert(0, notification)  # Newest first
        
        # Trim to max size
        if len(self.notifications) > self.max_notifications:
            # Remove oldest dismissed notifications
            self.notifications = [
                n for n in self.notifications
                if not n.get("dismissed", False)
            ][:self.max_notifications]
        
        # Save to disk
        self.save_notifications()
        
        # Notify observers (UI)
        self.notify_observers()
        
        # Play sound if requested
        if play_sound and not self.dnd_mode:
            self.play_notification_sound()
        
        return notif_id
    
    def get_notifications(
        self,
        unread_only: bool = False,
        limit: int = None,
        module: str = None
    ) -> List[Dict]:
        """
        Get notifications.
        
        Args:
            unread_only: Only return unread notifications
            limit: Maximum number to return
            module: Filter by module name
        
        Returns:
            List of notification dictionaries
        """
        notifications = self.notifications.copy()
        
        # Filter by read status
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        # Filter dismissed
        notifications = [n for n in notifications if not n.get("dismissed", False)]
        
        # Filter by module
        if module:
            notifications = [n for n in notifications if n.get("module") == module]
        
        # Limit results
        if limit:
            notifications = notifications[:limit]
        
        return notifications
    
    def get_unread_count(self, module: str = None) -> int:
        """Get count of unread notifications."""
        notifications = self.get_notifications(unread_only=True, module=module)
        return len(notifications)
    
    def mark_as_read(self, notification_id: str):
        """Mark notification as read."""
        for notif in self.notifications:
            if notif["id"] == notification_id:
                notif["read"] = True
                self.save_notifications()
                self.notify_observers()
                break
    
    def mark_all_as_read(self):
        """Mark all notifications as read."""
        for notif in self.notifications:
            notif["read"] = True
        self.save_notifications()
        self.notify_observers()
    
    def dismiss_notification(self, notification_id: str):
        """Dismiss (remove) a notification."""
        for notif in self.notifications:
            if notif["id"] == notification_id:
                notif["dismissed"] = True
                
                # Clean up callbacks
                if notification_id in self.callbacks:
                    del self.callbacks[notification_id]
                
                self.save_notifications()
                self.notify_observers()
                break
    
    def clear_all(self):
        """Clear all notifications."""
        self.notifications = []
        self.callbacks = {}
        self.save_notifications()
        self.notify_observers()
    
    def execute_action(self, notification_id: str, action_id: str):
        """Execute a notification action callback."""
        if notification_id in self.callbacks:
            if action_id in self.callbacks[notification_id]:
                callback = self.callbacks[notification_id][action_id]
                try:
                    callback()
                except Exception as e:
                    print(f"Error executing notification action: {e}")
    
    def toggle_dnd(self) -> bool:
        """Toggle Do Not Disturb mode. Returns new state."""
        self.dnd_mode = not self.dnd_mode
        return self.dnd_mode
    
    def set_dnd(self, enabled: bool):
        """Set Do Not Disturb mode."""
        self.dnd_mode = enabled
    
    def is_dnd(self) -> bool:
        """Check if Do Not Disturb is enabled."""
        return self.dnd_mode
    
    def register_observer(self, callback: Callable):
        """Register an observer to be notified of notification changes."""
        if callback not in self.observers:
            self.observers.append(callback)
    
    def unregister_observer(self, callback: Callable):
        """Unregister an observer."""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def notify_observers(self):
        """Notify all observers of changes."""
        for observer in self.observers:
            try:
                observer()
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    def play_notification_sound(self):
        """Play notification sound (system beep)."""
        try:
            # Use system beep
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except:
            # Fallback to print bell
            print("\a")
    
    def save_notifications(self):
        """Save notifications to disk."""
        try:
            # Only save non-dismissed notifications
            to_save = [
                n for n in self.notifications
                if not n.get("dismissed", False)
            ]
            
            with open(self.notifications_file, 'w') as f:
                json.dump(to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving notifications: {e}")
    
    def load_notifications(self):
        """Load notifications from disk."""
        try:
            if os.path.exists(self.notifications_file):
                with open(self.notifications_file, 'r') as f:
                    self.notifications = json.load(f)
        except Exception as e:
            print(f"Error loading notifications: {e}")
            self.notifications = []


# Global singleton instance
_notification_manager = NotificationManager()


# Convenience functions for other modules to use
def send_notification(
    title: str,
    message: str,
    module: str,
    notification_type: str = "info",
    actions: Optional[List[Dict]] = None,
    play_sound: bool = True,
    auto_dismiss: Optional[int] = None
) -> str:
    """
    Send a notification from any module.
    
    Usage:
        from notification_manager import send_notification
        
        send_notification(
            "Task Complete",
            "Your file has been organized!",
            "File Organizer",
            "success"
        )
    """
    return _notification_manager.send_notification(
        title, message, module, notification_type, actions, play_sound, auto_dismiss
    )


def get_notifications(unread_only: bool = False, limit: int = None, module: str = None) -> List[Dict]:
    """Get notifications."""
    return _notification_manager.get_notifications(unread_only, limit, module)


def get_unread_count(module: str = None) -> int:
    """Get count of unread notifications."""
    return _notification_manager.get_unread_count(module)


def mark_as_read(notification_id: str):
    """Mark notification as read."""
    _notification_manager.mark_as_read(notification_id)


def mark_all_as_read():
    """Mark all notifications as read."""
    _notification_manager.mark_all_as_read()


def dismiss_notification(notification_id: str):
    """Dismiss a notification."""
    _notification_manager.dismiss_notification(notification_id)


def clear_all_notifications():
    """Clear all notifications."""
    _notification_manager.clear_all()


def execute_notification_action(notification_id: str, action_id: str):
    """Execute a notification action."""
    _notification_manager.execute_action(notification_id, action_id)


def toggle_dnd() -> bool:
    """Toggle Do Not Disturb mode."""
    return _notification_manager.toggle_dnd()


def set_dnd(enabled: bool):
    """Set Do Not Disturb mode."""
    _notification_manager.set_dnd(enabled)


def is_dnd() -> bool:
    """Check if Do Not Disturb is enabled."""
    return _notification_manager.is_dnd()


def register_observer(callback: Callable):
    """Register observer for notification changes."""
    _notification_manager.register_observer(callback)


def unregister_observer(callback: Callable):
    """Unregister observer."""
    _notification_manager.unregister_observer(callback)


def get_manager() -> NotificationManager:
    """Get the notification manager singleton instance."""
    return _notification_manager
