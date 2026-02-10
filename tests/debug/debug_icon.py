"""
Debug Icon Loading
This script checks if the icon is loading correctly
"""

import tkinter as tk
import os

def test_icon():
    print("=" * 50)
    print("ICON LOADING DEBUG")
    print("=" * 50)
    
    # Check if icon exists
    icon_path = 'thunderz_icon.ico'
    abs_path = os.path.abspath(icon_path)
    
    print(f"\n1. Icon File Check:")
    print(f"   Looking for: {icon_path}")
    print(f"   Absolute path: {abs_path}")
    print(f"   Exists: {os.path.exists(icon_path)}")
    
    if os.path.exists(icon_path):
        size = os.path.getsize(icon_path)
        print(f"   File size: {size} bytes")
    
    # Try to load icon
    print(f"\n2. Loading Icon:")
    root = tk.Tk()
    root.title("Icon Test")
    root.geometry("400x200")
    
    try:
        root.iconbitmap(icon_path)
        print(f"   ✅ SUCCESS! Icon loaded without errors")
        print(f"   The taskbar should show the lightning bolt icon")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print(f"   Icon could not be loaded")
    
    # Show message
    label = tk.Label(
        root,
        text="Check your taskbar!\n\nDo you see:\n🐍 Python icon (OLD)\nOR\n⚡ Lightning bolt (NEW)?",
        font=("Segoe UI", 12),
        pady=30
    )
    label.pack()
    
    print(f"\n3. Visual Check:")
    print(f"   Look at your taskbar RIGHT NOW")
    print(f"   This window should show a lightning bolt icon")
    print(f"   If you see the Python icon, there's a cache issue")
    
    print(f"\n" + "=" * 50)
    print(f"Press Ctrl+C or close window to exit")
    print("=" * 50)
    
    root.mainloop()

if __name__ == "__main__":
    test_icon()
