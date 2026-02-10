"""
Spotify Detection Debugger
Run this while Spotify is playing a song to see what windows exist
"""

import win32gui
import psutil

print("=" * 60)
print("SPOTIFY WINDOW DETECTION DEBUGGER")
print("=" * 60)
print()

# Step 1: Check if Spotify is running
print("Step 1: Checking if Spotify process is running...")
spotify_procs = [proc for proc in psutil.process_iter(['name', 'pid']) if 'spotify' in proc.info['name'].lower()]

if spotify_procs:
    print(f"[OK] Found {len(spotify_procs)} Spotify process(es):")
    for proc in spotify_procs:
        print(f"  - {proc.info['name']} (PID: {proc.info['pid']})")
else:
    print("[ERROR] Spotify is NOT running!")
    print("  Please start Spotify and play a song, then run this script again.")
    input("\nPress Enter to exit...")
    exit()

print()

# Step 2: Enumerate all windows and find Spotify ones
print("Step 2: Finding all Spotify-related windows...")
print()

windows = []

def enum_callback(hwnd, param):
    title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)
    is_visible = win32gui.IsWindowVisible(hwnd)
    
    # Store all windows (we'll filter later)
    windows.append({
        'hwnd': hwnd,
        'title': title,
        'class_name': class_name,
        'visible': is_visible
    })

# Enumerate all windows
win32gui.EnumWindows(enum_callback, None)

# Filter for Spotify windows
spotify_windows = [w for w in windows if 'spotify' in w['title'].lower() or 'spotify' in w['class_name'].lower()]

print(f"Found {len(spotify_windows)} Spotify-related window(s):")
print()

for i, win in enumerate(spotify_windows, 1):
    print(f"Window #{i}:")
    print(f"  HWND: {win['hwnd']}")
    print(f"  Title: '{win['title']}'")
    print(f"  Class: '{win['class_name']}'")
    print(f"  Visible: {win['visible']}")
    print()

# Step 3: Check specifically for Chrome_WidgetWin_0 windows
print("=" * 60)
print("Step 3: Looking for Chrome_WidgetWin_0 class (current detection method)...")
print()

chrome_widget_windows = [w for w in spotify_windows if w['class_name'] == "Chrome_WidgetWin_0"]

if chrome_widget_windows:
    print(f"[OK] Found {len(chrome_widget_windows)} Chrome_WidgetWin_0 window(s):")
    print()
    for i, win in enumerate(chrome_widget_windows, 1):
        print(f"Match #{i}:")
        print(f"  Title: '{win['title']}'")
        print(f"  Visible: {win['visible']}")
        
        # Try to parse as song
        title = win['title']
        if ' – ' in title or ' - ' in title:
            separator = ' – ' if ' – ' in title else ' - '
            parts = title.split(separator, 1)
            if len(parts) == 2:
                print(f"  -> Detected Artist: '{parts[0].strip()}'")
                print(f"  -> Detected Song: '{parts[1].strip()}'")
        print()
else:
    print("[ERROR] No Chrome_WidgetWin_0 windows found!")
    print()

# Step 4: Show ALL windows that might have song info
print("=" * 60)
print("Step 4: All Spotify windows with non-empty titles:")
print()

titled_windows = [w for w in spotify_windows if w['title'] and w['title'] != 'Spotify']

if titled_windows:
    for i, win in enumerate(titled_windows, 1):
        print(f"Option #{i}:")
        print(f"  Class: '{win['class_name']}'")
        print(f"  Title: '{win['title']}'")
        print(f"  Visible: {win['visible']}")
        print()
else:
    print("No titled Spotify windows found.")
    print()

print("=" * 60)
print("SUMMARY:")
print("=" * 60)

if chrome_widget_windows and any(' – ' in w['title'] or ' - ' in w['title'] for w in chrome_widget_windows):
    print("[OK] Song detection SHOULD be working!")
    print("  If dashboard still shows no song, check:")
    print("  1. Is the dashboard_module.py using the correct class name?")
    print("  2. Are there any errors in the app console?")
elif spotify_procs and not chrome_widget_windows:
    print("[WARNING] Spotify is running but no Chrome_WidgetWin_0 windows found!")
    print("  Possible fixes:")
    print("  1. Try a different window class (see options above)")
    print("  2. Update Spotify (window class might have changed)")
    print("  3. Check if using Spotify from Microsoft Store vs. Desktop app")
else:
    print("[WARNING] Couldn't detect song information")
    print("  Make sure:")
    print("  1. Spotify is running")
    print("  2. A song is actively playing (not paused)")
    print("  3. You're using Spotify desktop app (not web player)")

print()
input("Press Enter to exit...")
