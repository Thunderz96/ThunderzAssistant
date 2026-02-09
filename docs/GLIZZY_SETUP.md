# Glizzy Module Setup Guide 🌭

## What Is This?

The Glizzy Module is a fun dice-rolling game that plays a video when you roll a 1!

---

## 🚀 Quick Setup

### Step 1: Install Required Packages

```powershell
pip install opencv-python Pillow
```

Or use the install script:
```powershell
.\install_glizzy.bat
```

---

### Step 2: Create Media Folder

Create a `media` folder in your ThunderzAssistant directory:

```
ThunderzAssistant/
├── main.py
├── modules/
├── media/          ← Create this folder
│   └── hot_dog_contest.mp4  ← Put your video here
```

**Windows Command:**
```powershell
mkdir media
```

---

### Step 3: Add Your Video

1. Find or download a hot dog eating contest video
2. Name it: `hot_dog_contest.mp4`
3. Place it in the `media` folder

**Recommended video format:** MP4 (H.264 codec)
**Recommended size:** Under 50MB for smooth playback

---

## 🎮 How to Use

1. Run the app: `python main.py`
2. Click **🌭 Glizzy Module** in the sidebar
3. Click **Roll For Glizzy** button
4. See what happens!

---

## 🎲 Roll Outcomes

| Roll | Result |
|------|--------|
| 1 | 🎬 Plays hot dog contest video IN the app! |
| 2-10 | 🌭 Glizzy to the face! |
| 11-19 | 🎉 Confetti celebration! |
| 20 | 🎊 Special message + confetti! |

---

## 🔧 Technical Details

### How Video Playback Works:

1. **OpenCV (cv2)** reads the video file frame-by-frame
2. **Threading** keeps the GUI responsive while playing
3. **Pillow (PIL)** converts frames for tkinter display
4. **ImageTk** displays frames in the Label widget

### Video Loop Process:
```python
1. Open video with cv2.VideoCapture()
2. Read frame-by-frame
3. Convert BGR → RGB
4. Resize to 640x480
5. Convert to PIL Image → ImageTk
6. Update Label with new frame
7. Wait for next frame (based on FPS)
8. Repeat until video ends
```

---

## 🐛 Troubleshooting

### Problem: "Video file not found"
**Solution:** 
- Make sure `media` folder exists
- Make sure video is named `hot_dog_contest.mp4`
- Check file location: `ThunderzAssistant/media/hot_dog_contest.mp4`

### Problem: "Failed to open video file"
**Solution:**
- Use MP4 format with H.264 codec
- Try converting video with VLC or ffmpeg:
  ```bash
  ffmpeg -i input.mp4 -c:v libx264 -c:a aac hot_dog_contest.mp4
  ```

### Problem: Video plays but is choppy
**Solution:**
- Reduce video resolution (720p max recommended)
- Reduce video file size
- Close other applications

### Problem: "ModuleNotFoundError: No module named 'cv2'"
**Solution:**
```powershell
pip install opencv-python
```

---

## 📁 Folder Structure

```
ThunderzAssistant/
├── main.py
├── modules/
│   ├── glizzy_module.py      ← The module code
│   └── ...
├── media/                      ← YOU CREATE THIS
│   └── hot_dog_contest.mp4    ← YOUR VIDEO HERE
├── requirements.txt
└── docs/
    └── GLIZZY_SETUP.md        ← This file
```

---

## 🎥 Video Requirements

**Format:** MP4
**Codec:** H.264 (most compatible)
**Resolution:** 720p or lower (1280x720 max)
**Size:** Under 50MB recommended
**FPS:** 30 fps recommended

---

## 🔄 Alternative Video Sources

If you don't have a video yet:

1. **YouTube Download** (with permission):
   - Use youtube-dl or similar
   - Convert to MP4 if needed

2. **Use a Sample Video**:
   - Download any MP4 video
   - Rename to `hot_dog_contest.mp4`
   - Test the module!

3. **Create Your Own**:
   - Record a funny video
   - Use any video editing software
   - Export as MP4

---

## 🎯 Testing

After setup:
1. Run: `python main.py`
2. Click **Glizzy Module**
3. Click **Roll For Glizzy**
4. Keep rolling until you get a 1!
5. Video should play in the app window

---

## 💡 Customization Ideas

### Change Video Size:
Edit `glizzy_module.py` line ~180:
```python
frame = cv2.resize(frame, (800, 600))  # Larger video
```

### Add More Videos:
```python
if roll == 1:
    videos = [
        "hot_dog_contest.mp4",
        "hot_dog_eating_2.mp4",
        "hot_dog_eating_3.mp4"
    ]
    video = random.choice(videos)
    video_path = os.path.join(..., "media", video)
```

### Loop Video:
Add a loop in `_video_loop()`:
```python
while self.video_playing:
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
    # ... play frames ...
```

---

## 🤓 Code Explanation (For Learning)

### Why OpenCV?
- ✅ Cross-platform (Windows, Mac, Linux)
- ✅ Handles many video formats
- ✅ Frame-by-frame control
- ✅ Well-documented
- ✅ Free and open source

### Why Threading?
- Video playback takes time
- Without threading → GUI freezes
- With threading → GUI stays responsive
- User can still interact with app

### Why Not Just Open External Player?
- We want video IN the app
- Better user experience
- More control over playback
- Looks more professional

---

## 📚 Dependencies

```
opencv-python>=4.8.0  # Video reading
Pillow>=10.0.0        # Image conversion
```

Both are automatically installed with:
```powershell
pip install -r requirements.txt
```

---

## 🎉 You're Ready!

Once you have:
- ✅ OpenCV and Pillow installed
- ✅ Media folder created
- ✅ Video file added

Just run the app and roll that glizzy! 🌭🎲

---

## 🆘 Still Having Issues?

1. Check Python version: `python --version` (need 3.7+)
2. Verify packages: `pip list | findstr opencv`
3. Test video separately:
   ```python
   import cv2
   cap = cv2.VideoCapture("media/hot_dog_contest.mp4")
   print(cap.isOpened())  # Should be True
   ```

---

**Happy Rolling!** 🎲🌭
