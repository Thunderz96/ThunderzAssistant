"""
Spotify Detection Debugger - Smarter version that filters out browsers
"""

import win32gui
import psutil

print("=" * 60)
print("SPOTIFY SONG DETECTION TEST - IMPROVED")
print("=" * 60)
print()
print("INSTRUCTIONS:")
print("1. Make sure a song is PLAYING in Spotify (not paused)")
print("2. Keep Spotify window visible (not minimized)")
print("3. Close any browser tabs about Spotify")
print("4. Then press Enter to continue...")
input()
print()

# Check if Spotify process is running
spotify_procs = [proc for proc in psutil.process_iter(['name', 'exe']) if 'spotify.exe' in proc.info['name'].lower()]

if not spotify_procs:
    print("[ERROR] Spotify is not running!")
    input("\nPress Enter to exit...")
    exit()

print(f"[OK] Spotify is running ({len(spotify_procs)} processes)")
print()

# Find all windows
windows = []

def enum_callback(hwnd, param):
    title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)
    is_visible = win32gui.IsWindowVisible(hwnd)
    windows.append({
        'hwnd': hwnd,
        'title': title,
        'class_name': class_name,
        'visible': is_visible
    })

win32gui.EnumWindows(enum_callback, None)

# Filter for Spotify windows (exclude browser tabs)
spotify_windows = []
for w in windows:
    title_lower = w['title'].lower()
    # Must contain 'spotify' but NOT 'chrome', 'edge', 'firefox', etc.
    if 'spotify' in title_lower:
        # Exclude browser windows
        if not any(browser in title_lower for browser in ['chrome', 'edge', 'firefox', 'safari', 'brave', 'opera']):
            # Only Chrome_WidgetWin_0 or Chrome_WidgetWin_1
            if 'Chrome_WidgetWin' in w['class_name']:
                spotify_windows.append(w)

print(f"Found {len(spotify_windows)} ACTUAL Spotify window(s) (excluding browsers):")
print()

if not spotify_windows:
    print("[ERROR] No Spotify windows found!")
    print()
    print("All windows with 'spotify' in title:")
    all_spotify = [w for w in windows if 'spotify' in w['title'].lower()]
    for w in all_spotify:
        print(f"  - {w['title']} ({w['class_name']})")
    print()
    input("\nPress Enter to exit...")
    exit()

song_found = False

for i, win in enumerate(spotify_windows, 1):
    print(f"Spotify Window #{i}:")
    print(f"  HWND: {win['hwnd']}")
    print(f"  Title: '{win['title']}'")
    print(f"  Class: '{win['class_name']}'")
    print(f"  Visible: {win['visible']}")
    print()
    
    title = win['title']
    
    # Skip if just "Spotify" or "Spotify Premium"
    if title in ['Spotify', 'Spotify Premium', 'Spotify Free']:
        print(f"  -> Just the app name, no song playing")
        print()
        continue
    
    # Try to parse song title
    # Common formats:
    # "Artist - Song"
    # "Song - Artist"  
    # "Artist - Song - Spotify Premium"
    
    if ' - ' in title:
        parts = title.split(' - ')
        print(f"  -> Found {len(parts)} parts: {parts}")
        
        # Remove "Spotify Premium", "Spotify Free", etc. from end
        if parts[-1].strip() in ['Spotify Premium', 'Spotify Free', 'Spotify']:
            parts = parts[:-1]
        
        if len(parts) >= 2:
            artist = parts[0].strip()
            song = parts[1].strip()
            print(f"  -> DETECTED!")
            print(f"     Artist: '{artist}'")
            print(f"     Song: '{song}'")
            song_found = True
        elif len(parts) == 1:
            print(f"  -> Only one part: '{parts[0]}'")
            print(f"     (Might be song title without artist)")
            song_found = True
    
    print()

print("=" * 60)
if song_found:
    print("[SUCCESS] Song information detected!")
    print()
    print("We can update your dashboard to use this detection method.")
else:
    print("[WARNING] No song title found in window title")
    print()
    print("This could mean:")
    print("1. Song is paused (not actively playing)")
    print("2. Spotify doesn't show song in window title when minimized")
    print("3. Need to focus/click on Spotify window first")
    print()
    print("Try this:")
    print("- Click on the Spotify window to bring it to front")
    print("- Make sure a song is actively playing (not paused)")
    print("- Run this test again")

print()
input("Press Enter to exit...")
