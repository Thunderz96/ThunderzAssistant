"""
Test if we can detect Microsoft Store Spotify using Windows Media Control
This uses Windows 10+ Media Session API
"""

import asyncio
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager

async def get_media_info():
    sessions = await MediaManager.request_async()
    
    current_session = sessions.get_current_session()
    if current_session:
        info = await current_session.try_get_media_properties_async()
        
        # Song information
        print("=" * 60)
        print("MEDIA SESSION DETECTED!")
        print("=" * 60)
        print(f"Title: {info.title}")
        print(f"Artist: {info.artist}")
        print(f"Album: {info.album_title}")
        print()
        
        # Playback info
        playback = current_session.get_playback_info()
        print(f"Status: {playback.playback_status}")
        print()
        
        return {
            'title': info.title,
            'artist': info.artist,
            'album': info.album_title,
            'status': playback.playback_status
        }
    else:
        print("No media session found.")
        print("Make sure Spotify is playing a song!")
        return None

if __name__ == "__main__":
    try:
        print("Checking for Windows Media Session...")
        print("(Works with Microsoft Store Spotify)")
        print()
        
        result = asyncio.run(get_media_info())
        
        if result:
            print("=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print("This method works for your Spotify!")
            print()
            print("We can use Windows Media Session API")
            print("to detect songs from Microsoft Store Spotify.")
        
    except ImportError as e:
        print("ERROR: winsdk not installed")
        print()
        print("Install with:")
        print("  pip install winsdk")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("This might not work on your Windows version.")
        print("Try Option 1 (Desktop Spotify) instead.")

    input("\nPress Enter to exit...")
