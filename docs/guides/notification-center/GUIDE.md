# 🔔 Notification Center - Complete Guide

## Overview

The Notification Center is a centralized hub for all notifications from all modules in Thunderz Assistant. Every module can send notifications, and users can view, manage, and interact with them in one place.

---

## ✨ Features

### Core Features
- 📬 **Centralized Display** - All notifications in one place
- 🔔 **Badge Counter** - Shows unread count on sidebar
- ⏱️ **Timestamps** - Relative time ("5 minutes ago")
- 🎨 **Type Indicators** - Color-coded by type (info, success, warning, error)
- ✅ **Mark as Read** - Track which notifications you've seen
- ✕ **Dismiss** - Remove notifications you don't need
- 🎯 **Quick Actions** - Execute actions directly from notifications

### Advanced Features
- 🔕 **Do Not Disturb** - Silence all notifications (except errors)
- 📋 **Filter** - Show all or unread only
- 🔄 **Auto-Refresh** - Real-time updates when new notifications arrive
- 💾 **Persistent** - Notifications saved between sessions
- 🎵 **Sound** - Optional notification sounds
- 📊 **History** - Keep last 100 notifications

---

## 🎯 Notification Types

| Type | Icon | Color | Use Case |
|------|------|-------|----------|
| **Info** | 🔵 | Blue | General information |
| **Success** | 🟢 | Green | Completed tasks, achievements |
| **Warning** | 🟡 | Yellow | Important but non-critical |
| **Error** | 🔴 | Red | Critical issues, failures |

---

## 📱 User Interface

### Main View

```
┌──────────────────────────────────────────┐
│  🔔 Notification Center                  │
├──────────────────────────────────────────┤
│  📬 5 Unread  📋 Show All                │
│  [✓ Mark All Read] [🗑️ Clear] [🔔 DND]  │
├──────────────────────────────────────────┤
│  ┌────────────────────────────────────┐  │
│  │ 🟢 Pomodoro #5 Complete!          │  │
│  │ [Pomodoro] 2 minutes ago          │  │
│  │                                    │  │
│  │ Great work! 5 pomodoros today     │  │
│  │ (125 minutes). Time for a break!  │  │
│  │                                    │  │
│  │ [View Stats] [Start Break] [✕]    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 🟡 High CPU Usage (92%)            │  │
│  │ [System] 1 minute ago              │  │
│  │                                    │  │
│  │ CPU usage is above normal levels  │  │
│  │                                    │  │
│  │ [Check System] [✓ Mark Read] [✕]  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Sidebar Badge

```
🔔 Notifications  [5]  ← Red badge shows unread count
```

---

## 🚀 How to Use

### Viewing Notifications

1. Click **🔔 Notifications** in sidebar
2. See all notifications in chronological order (newest first)
3. Unread notifications have lighter background
4. Badge shows unread count

### Managing Notifications

**Mark as Read:**
- Click **✓ Mark Read** on individual notification
- Click **✓ Mark All Read** to mark all as read

**Dismiss:**
- Click **✕ Dismiss** to remove notification
- Click **🗑️ Clear All** to remove all notifications

**Filter:**
- Click **📋 Show All** to see all notifications
- Click **📬 Unread Only** to see unread only

**Do Not Disturb:**
- Click **🔔 DND Off** to enable DND mode
- Click **🔕 DND** to disable DND mode
- DND blocks all notifications except errors

### Using Actions

Many notifications have action buttons:
- Click action button to execute the action
- Notification auto-dismisses after action
- Examples: "View Stats", "Start Break", "Check System"

---

## 👨‍💻 For Developers: Sending Notifications

### Basic Notification

```python
from notification_manager import send_notification

send_notification(
    title="Task Complete",
    message="Your file has been organized successfully!",
    module="File Organizer",
    notification_type="success"
)
```

### Notification with Actions

```python
send_notification(
    title="Pomodoro Complete",
    message="Great work! Time for a break.",
    module="Pomodoro",
    notification_type="success",
    actions=[
        {
            "label": "View Stats",
            "callback": show_stats_function
        },
        {
            "label": "Start Break",
            "callback": start_break_function
        }
    ]
)
```

### Notification Types

```python
# Info (default)
send_notification(
    title="Weather Updated",
    message="Current temperature: 72°F",
    module="Weather",
    notification_type="info"
)

# Success
send_notification(
    title="Download Complete",
    message="File saved to Downloads",
    module="System",
    notification_type="success"
)

# Warning
send_notification(
    title="High CPU Usage",
    message="CPU at 92%, consider closing apps",
    module="System",
    notification_type="warning"
)

# Error
send_notification(
    title="Connection Failed",
    message="Could not connect to API",
    module="News",
    notification_type="error"
)
```

### Advanced Options

```python
send_notification(
    title="Custom Notification",
    message="With advanced options",
    module="MyModule",
    notification_type="info",
    actions=[{"label": "Action", "callback": func}],
    play_sound=True,         # Play notification sound
    auto_dismiss=30          # Auto-dismiss after 30 seconds
)
```

---

## 📚 API Reference

### Functions

**send_notification()**
```python
send_notification(
    title: str,                    # Notification title
    message: str,                  # Notification message
    module: str,                   # Module name
    notification_type: str,        # "info", "success", "warning", "error"
    actions: List[Dict],           # Optional action buttons
    play_sound: bool,              # Play sound (default: True)
    auto_dismiss: int              # Auto-dismiss seconds (default: None)
) -> str                           # Returns notification ID
```

**get_notifications()**
```python
get_notifications(
    unread_only: bool = False,     # Only unread notifications
    limit: int = None,             # Max number to return
    module: str = None             # Filter by module
) -> List[Dict]                    # Returns list of notifications
```

**get_unread_count()**
```python
get_unread_count(
    module: str = None             # Filter by module
) -> int                           # Returns count
```

**mark_as_read()**
```python
mark_as_read(notification_id: str)
```

**mark_all_as_read()**
```python
mark_all_as_read()
```

**dismiss_notification()**
```python
dismiss_notification(notification_id: str)
```

**clear_all_notifications()**
```python
clear_all_notifications()
```

**toggle_dnd()**
```python
toggle_dnd() -> bool               # Returns new DND state
```

---

## 🎨 Example Use Cases

### Pomodoro Timer Complete
```python
send_notification(
    title=f"🍅 Pomodoro #{count} Complete!",
    message=f"Great work! {total_today} pomodoros today.",
    module="Pomodoro",
    notification_type="success",
    actions=[
        {"label": "View Stats", "callback": show_stats},
        {"label": "Start Break", "callback": start_break}
    ]
)
```

### File Organization Complete
```python
send_notification(
    title="Files Organized",
    message=f"Sorted {file_count} files into {folder_count} folders",
    module="File Organizer",
    notification_type="success",
    actions=[
        {"label": "Open Folder", "callback": open_downloads}
    ]
)
```

### System Alert
```python
send_notification(
    title="High CPU Usage",
    message=f"CPU at {cpu_percent}%, may affect performance",
    module="System Monitor",
    notification_type="warning",
    actions=[
        {"label": "View Details", "callback": show_system_monitor}
    ]
)
```

### Stock Price Alert
```python
send_notification(
    title=f"{stock} Price Alert",
    message=f"{stock} reached ${price} ({change}%)",
    module="Stock Monitor",
    notification_type="info",
    actions=[
        {"label": "View Portfolio", "callback": show_portfolio}
    ]
)
```

---

## ⚙️ Technical Details

### Architecture

**NotificationManager (Singleton)**
- Backend notification system
- Manages storage, retrieval, actions
- Observer pattern for UI updates
- Thread-safe

**NotificationCenterModule**
- UI for viewing notifications
- Subscribes to NotificationManager
- Auto-refreshes on changes

### Data Storage

**File:** `notifications.json`
**Format:**
```json
[
  {
    "id": "notif_1707523456789_0",
    "timestamp": "2026-02-09T14:30:45",
    "type": "success",
    "title": "Pomodoro Complete",
    "message": "Great work! Time for a break.",
    "module": "Pomodoro",
    "read": false,
    "dismissed": false,
    "sound": true,
    "actions": [
      {"id": "notif_..._View Stats", "label": "View Stats"}
    ]
  }
]
```

### Observer Pattern

Modules register observers to be notified of changes:

```python
from notification_manager import register_observer

def on_notification_change():
    # Update UI
    pass

register_observer(on_notification_change)
```

---

## 🔒 Privacy & Data

**What's Stored:**
- Notification title, message, type
- Timestamp and module
- Read/dismissed status

**What's NOT Stored:**
- Action callbacks (functions)
- Sensitive user data
- API keys or credentials

**File Location:**
- `notifications.json` (gitignored)
- Automatically managed
- Safe to delete (will recreate)

---

## 🎯 Best Practices

### When to Send Notifications

**DO send notifications for:**
- ✅ Task completions
- ✅ Important status changes
- ✅ User-initiated actions finishing
- ✅ Alerts requiring attention
- ✅ Achievements/milestones

**DON'T send notifications for:**
- ❌ Every minor update
- ❌ Routine background tasks
- ❌ Expected/normal operations
- ❌ Errors already shown in UI
- ❌ Spam/excessive frequency

### Notification Quality

**Good Notification:**
- Clear, concise title
- Helpful message with context
- Relevant actions
- Appropriate type/urgency

**Example:**
```python
# GOOD ✅
send_notification(
    title="Pomodoro Complete",
    message="5 pomodoros done today (125 min). Take a 5-min break!",
    module="Pomodoro",
    notification_type="success",
    actions=[{"label": "Start Break", "callback": start_break}]
)

# BAD ❌
send_notification(
    title="Done",
    message="Task finished",
    module="App",
    notification_type="info"
)
```

---

## 🐛 Troubleshooting

### Notifications Not Appearing

**Check:**
1. Is DND mode enabled? (🔕 icon)
2. Is notification being sent? (check console for errors)
3. Are you filtering to "Unread Only"?
4. Is module sending notifications correctly?

### Badge Not Updating

**Solution:**
- Restart Thunderz Assistant
- Check observer registration
- Verify notification_manager import

### Sounds Not Playing

**Check:**
1. DND mode enabled?
2. `play_sound=True` in send_notification?
3. System sound settings

---

## 📊 Statistics

View notification statistics:
```python
from notification_manager import get_notifications

all_notifs = get_notifications()
unread = get_notifications(unread_only=True)
errors = [n for n in all_notifs if n['type'] == 'error']

print(f"Total: {len(all_notifs)}")
print(f"Unread: {len(unread)}")
print(f"Errors: {len(errors)}")
```

---

## 🚀 Future Enhancements

Planned features:
- 🔔 Push notifications to mobile
- 📧 Email digest
- 📊 Notification analytics dashboard
- ⏰ Scheduled notifications
- 🎨 Custom notification templates
- 🔊 Custom notification sounds
- 📱 Priority levels (urgent, normal, low)
- 🔗 Deep linking to modules

---

## 📝 Changelog

**v1.8.0** (February 2026)
- Initial release
- Core notification system
- Notification Center UI
- Pomodoro integration
- DND mode
- Action buttons
- Persistent storage

---

**Questions? Issues?**
- Check main README.md
- See module code: `modules/notification_center_module.py`
- See backend: `modules/notification_manager.py`

**Enjoy your centralized notifications!** 🎉
