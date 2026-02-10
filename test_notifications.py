"""
Test Notification System
Demonstrates how to send notifications from modules

Run this script to see example notifications in action!
"""

import sys
import os

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from notification_manager import send_notification, get_notifications, get_unread_count
import time


def test_basic_notifications():
    """Test basic notification sending"""
    print("🔔 Testing Basic Notifications...\n")
    
    # Info notification
    print("1. Sending INFO notification...")
    send_notification(
        title="Weather Updated",
        message="Current temperature: 72°F, Partly Cloudy",
        module="Weather",
        notification_type="info"
    )
    time.sleep(1)
    
    # Success notification
    print("2. Sending SUCCESS notification...")
    send_notification(
        title="Files Organized",
        message="Successfully sorted 47 files into 8 folders",
        module="File Organizer",
        notification_type="success"
    )
    time.sleep(1)
    
    # Warning notification
    print("3. Sending WARNING notification...")
    send_notification(
        title="High CPU Usage",
        message="CPU usage at 92%, consider closing applications",
        module="System Monitor",
        notification_type="warning"
    )
    time.sleep(1)
    
    # Error notification
    print("4. Sending ERROR notification...")
    send_notification(
        title="Connection Failed",
        message="Could not connect to News API. Check your internet connection.",
        module="News",
        notification_type="error"
    )
    time.sleep(1)


def test_notifications_with_actions():
    """Test notifications with action buttons"""
    print("\n🎯 Testing Notifications with Actions...\n")
    
    def action1():
        print("   → Action 1 executed!")
    
    def action2():
        print("   → Action 2 executed!")
    
    print("5. Sending notification with ACTION BUTTONS...")
    send_notification(
        title="Pomodoro #5 Complete!",
        message="Great work! You've completed 5 pomodoros today (125 minutes).\n\nTime for a Short Break (5 min)",
        module="Pomodoro",
        notification_type="success",
        actions=[
            {
                "label": "View Stats",
                "callback": action1
            },
            {
                "label": "Start Break",
                "callback": action2
            }
        ]
    )
    time.sleep(1)


def test_module_specific():
    """Test notifications from different modules"""
    print("\n📦 Testing Module-Specific Notifications...\n")
    
    modules = [
        ("Dashboard", "Daily Summary Ready", "Your daily overview is ready to view"),
        ("Stock Monitor", "AAPL Price Alert", "AAPL reached $185.50 (+2.3%)"),
        ("Discord", "Message Sent", "Successfully sent daily report to #productivity"),
        ("Glizzy", "Lucky Roll!", "You rolled a 🌭 GLIZZY! Congratulations!"),
    ]
    
    for i, (module, title, message) in enumerate(modules, 6):
        print(f"{i}. Sending from {module}...")
        send_notification(
            title=title,
            message=message,
            module=module,
            notification_type="info"
        )
        time.sleep(0.5)


def test_silent_notification():
    """Test notification without sound"""
    print("\n🔇 Testing Silent Notification...\n")
    
    print("10. Sending SILENT notification (no sound)...")
    send_notification(
        title="Background Task Complete",
        message="File sync completed in the background",
        module="System",
        notification_type="info",
        play_sound=False
    )
    time.sleep(1)


def show_notification_stats():
    """Show current notification statistics"""
    print("\n📊 Notification Statistics:")
    print("=" * 40)
    
    all_notifications = get_notifications()
    unread_count = get_unread_count()
    
    print(f"Total Notifications: {len(all_notifications)}")
    print(f"Unread: {unread_count}")
    
    # Count by type
    types = {"info": 0, "success": 0, "warning": 0, "error": 0}
    for notif in all_notifications:
        notif_type = notif.get("type", "info")
        types[notif_type] = types.get(notif_type, 0) + 1
    
    print(f"\nBy Type:")
    print(f"  Info: {types['info']}")
    print(f"  Success: {types['success']}")
    print(f"  Warning: {types['warning']}")
    print(f"  Error: {types['error']}")
    
    # Count by module
    modules = {}
    for notif in all_notifications:
        module = notif.get("module", "Unknown")
        modules[module] = modules.get(module, 0) + 1
    
    print(f"\nBy Module:")
    for module, count in sorted(modules.items(), key=lambda x: x[1], reverse=True):
        print(f"  {module}: {count}")
    
    print("=" * 40)


def main():
    """Run all tests"""
    print("\n" + "=" * 50)
    print("🔔 NOTIFICATION SYSTEM TEST")
    print("=" * 50)
    print()
    print("This script will send test notifications to demonstrate")
    print("the notification system. Open Thunderz Assistant and")
    print("navigate to the Notification Center to see them!")
    print()
    print("Press Enter to start...")
    input()
    
    # Run tests
    test_basic_notifications()
    test_notifications_with_actions()
    test_module_specific()
    test_silent_notification()
    
    # Show stats
    print()
    show_notification_stats()
    
    print("\n" + "=" * 50)
    print("✅ Test Complete!")
    print("=" * 50)
    print()
    print("Now open Thunderz Assistant and click:")
    print("  🔔 Notifications")
    print()
    print("You should see all 10 test notifications!")
    print()
    print("Try:")
    print("  • Click 'Mark All Read'")
    print("  • Click action buttons")
    print("  • Toggle 'Unread Only'")
    print("  • Enable/disable DND mode")
    print("  • Dismiss individual notifications")
    print()


if __name__ == "__main__":
    main()
