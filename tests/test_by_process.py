"""
Spotify Detection - Find windows by PROCESS not by title
This is the correct way to detect Spotify windows!
"""

import win32gui
import win32process
import psutil

print("=" * 60)
print("SPOTIFY WINDOW DETECTION - BY PROCESS")
print("=" * 60)
print()
print("INSTRUCTIONS:")
print("1. Make sure a song is PLAYING in Spotify")
print("2. Keep Spotify window visible")
print("3. Press Enter to continue...")
input()
print()

# Step 1: Get all Spotify process IDs
spotify_pids = []
for proc in psutil.process_iter(['pid', 'name']):
    if 'spotify.exe' in proc.info['name'].lower():
        spotify_pids.append(proc.info['pid'])

print(f"[OK] Found {len(spotify_pids)} Spotify processes")
print(f"PIDs: {spotify_pids}")
print()

# Step 2: Find all windows
all_windows = []

def enum_callback(hwnd, param):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        
        # Get process ID for this window
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
        except:
            pid = None
        
        all_windows.append({
            'hwnd': hwnd,
            'title': title,
            'class_name': class_name,
            'pid': pid
        })

win32gui.EnumWindows(enum_callback, None)

# Step 3: Filter for windows belonging to Spotify processes
spotify_windows = [w for w in all_windows if w['pid'] in spotify_pids]

print(f"Found {len(spotify_windows)} window(s) belonging to Spotify process:")
print()

for i, win in enumerate(spotify_windows, 1):
    print(f"Spotify Window #{i}:")
    print(f"  PID: {win['pid']}")
    print(f"  Title: '{win['title']}'")
    print(f"  Class: '{win['class_name']}'")
    print()

# Step 4: Look for Chrome_WidgetWin windows (these usually have song info)
chrome_windows = [w for w in spotify_windows if 'Chrome_WidgetWin' in w['class_name']]

print("=" * 60)
print(f"Chrome_WidgetWin windows: {len(chrome_windows)}")
print("=" * 60)
print()

if chrome_windows:
    for i, win in enumerate(chrome_windows, 1):
        title = win['title']
        print(f"Window #{i}:")
        print(f"  Class: {win['class_name']}")
        print(f"  Title: '{title}'")
        
        # Try to parse song
        if title and title not in ['Spotify', 'Spotify Premium', 'Spotify Free', '']:
            print(f"  -> CONTAINS TEXT!")
            
            # Try different separators
            if ' - ' in title:
                parts = title.split(' - ')
                print(f"     Parts: {parts}")
                
                # Remove Spotify suffix
                if parts[-1].strip() in ['Spotify Premium', 'Spotify Free', 'Spotify']:
                    parts = parts[:-1]
                
                if len(parts) >= 2:
                    print(f"     Artist: '{parts[0]}'")
                    print(f"     Song: '{parts[1]}'")
                elif len(parts) == 1:
                    print(f"     Title: '{parts[0]}'")
            else:
                print(f"     (No separator found, raw title)")
        else:
            print(f"  -> Empty or just 'Spotify' (no song playing?)")
        
        print()
else:
    print("[WARNING] No Chrome_WidgetWin windows found!")
    print()
    print("All Spotify windows found:")
    for win in spotify_windows:
        print(f"  - Class: {win['class_name']}")
        print(f"    Title: '{win['title']}'")
    print()

print("=" * 60)
print("RECOMMENDATION:")
print("=" * 60)

if chrome_windows:
    # Check which class to use
    classes = set(w['class_name'] for w in chrome_windows)
    print(f"Use these window classes: {classes}")
    print()
    print("Your dashboard should check for windows with:")
    print(f"  - Process: Spotify.exe")
    print(f"  - Class: {' or '.join(classes)}")
else:
    print("No suitable windows found for song detection.")
    print()
    print("Possible issues:")
    print("1. Song is paused (not playing)")
    print("2. Using Microsoft Store Spotify (different detection needed)")
    print("3. Spotify version doesn't show song in window title")

print()
input("Press Enter to exit...")
