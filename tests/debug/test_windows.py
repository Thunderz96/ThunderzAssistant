#"""
#Standalone test script to list all window titles containing 'spotify'.
#Run this with Spotify open and playing to see what titles are detected.
#"""

import ctypes
from ctypes import wintypes

# Set up Windows API calls
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    wintypes.HWND,
    wintypes.LPARAM
)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW

# List to store window titles
titles = []

# Callback function to collect titles
def foreach_window(hwnd, lParam):
    length = GetWindowTextLength(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    GetWindowText(hwnd, buffer, length)
    title = buffer.value
    if title:  # Only add non-empty titles
        titles.append(title)
    return True

# Enumerate all windows
EnumWindows(EnumWindowsProc(foreach_window), 0)

# Find and print Spotify-related titles
spotify_titles = [t for t in titles if 'spotify' in t.lower()]
print("Spotify-related window titles found:")
for t in spotify_titles:
    print(f" - '{t}'")

print(f"Total Spotify titles: {len(spotify_titles)}")
if not spotify_titles:
    print("No Spotify windows found. Make sure Spotify is open!")