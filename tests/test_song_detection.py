"""
Spotify Detection Debugger - Updated for Chrome_WidgetWin_1
"""

import win32gui
import psutil

print("=" * 60)
print("SPOTIFY SONG DETECTION TEST")
print("=" * 60)
print()
print("INSTRUCTIONS:")
print("1. Make sure a song is PLAYING (not paused)")
print("2. Keep Spotify window visible (not minimized)")
print("3. Then press Enter to continue...")
input()
print()

# Find Spotify windows
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

# Look for Chrome_WidgetWin_1 windows (Desktop Spotify uses this)
spotify_windows = [w for w in windows if 'Chrome_WidgetWin_1' in w['class_name'] and 'spotify' in w['title'].lower()]

print(f"Found {len(spotify_windows)} Spotify Chrome_WidgetWin_1 window(s):")
print()

song_found = False

for i, win in enumerate(spotify_windows, 1):
    print(f"Window #{i}:")
    print(f"  Title: '{win['title']}'")
    print(f"  Class: '{win['class_name']}'")
    print(f"  Visible: {win['visible']}")
    
    title = win['title']
    
    # Try different separators
    if ' - ' in title and title != 'Spotify Premium':
        # Format: "Artist - Song" or "Song - Spotify Premium"
        parts = title.split(' - ')
        print(f"  -> Parts found: {parts}")
        
        if len(parts) >= 2:
            # Check if last part is "Spotify Premium"
            if 'Spotify' in parts[-1]:
                # Format: Artist - Song - Spotify Premium
                if len(parts) >= 3:
                    artist = parts[0].strip()
                    song = ' - '.join(parts[1:-1]).strip()
                    print(f"  -> Artist: '{artist}'")
                    print(f"  -> Song: '{song}'")
                    song_found = True
                # Format: Song - Spotify Premium
                else:
                    song = parts[0].strip()
                    print(f"  -> Song: '{song}'")
                    print(f"  -> Artist: Unknown")
                    song_found = True
            else:
                # Format: Artist - Song (no Spotify suffix)
                artist = parts[0].strip()
                song = parts[1].strip()
                print(f"  -> Artist: '{artist}'")
                print(f"  -> Song: '{song}'")
                song_found = True
    
    print()

print("=" * 60)
if song_found:
    print("[SUCCESS] Song detection working!")
    print()
    print("Your dashboard should be able to show this song.")
    print("We'll update dashboard_module.py to use Chrome_WidgetWin_1")
else:
    print("[NO SONG FOUND]")
    print()
    print("Possible reasons:")
    print("1. Song is paused (not playing)")
    print("2. Spotify window is minimized")
    print("3. Song title doesn't appear in window title")
    print()
    print("Try:")
    print("- Click on Spotify window to focus it")
    print("- Make sure song is actively playing")
    print("- Try playing a different song")

print()
input("Press Enter to exit...")
