# File Organizer Module - User Guide

## 📁 What It Does

The File Organizer automatically sorts messy folders by file type, creating organized category folders.

---

## 🎯 How to Use

### **Step 1: Select Folder**
- Default: Downloads folder
- Click **"Browse"** to choose a different folder

### **Step 2: Scan**
- Click **"🔍 Scan"** button
- See file type breakdown:
  - 📷 Images (jpg, png, gif, etc.)
  - 📄 Documents (pdf, docx, txt, etc.)
  - 🎥 Videos (mp4, avi, mkv, etc.)
  - 🎵 Audio (mp3, wav, flac, etc.)
  - 📦 Archives (zip, rar, 7z, etc.)
  - 💻 Code (py, js, html, etc.)
  - ⚙️ Executables (exe, msi, bat, etc.)
  - 📁 Other (everything else)

### **Step 3: Organize**
- Click **"✨ Organize Files"** button
- Confirm the action
- Files are moved into category folders

### **Step 4: Undo (Optional)**
- Click **"↩️ Undo Last Organization"** if needed
- All files moved back to original location

---

## 📋 Example

**Before:**
```
Downloads/
├── photo.jpg
├── report.pdf
├── song.mp3
├── video.mp4
├── code.py
└── archive.zip
```

**After organizing:**
```
Downloads/
├── Images/
│   └── photo.jpg
├── Documents/
│   └── report.pdf
├── Audio/
│   └── song.mp3
├── Videos/
│   └── video.mp4
├── Code/
│   └── code.py
└── Archives/
    └── archive.zip
```

---

## ⚡ Features

### ✅ **Safe Mode**
- Handles duplicate filenames automatically
- Adds numbers to duplicates (file_1.txt, file_2.txt)
- Never overwrites existing files

### ✅ **Undo Functionality**
- Tracks all file moves
- One-click undo to restore original structure
- Works even after closing the app

### ✅ **Smart Categorization**
- 70+ file extensions recognized
- "Other" category for unknown types
- Easy to customize categories in code

---

## 🎓 Learning Notes (For Developers)

### **Key Concepts Used:**
1. **File Operations** - `os`, `shutil`, `pathlib`
2. **JSON Storage** - Track moves for undo
3. **GUI Layouts** - Scrollable canvas, card layouts
4. **Error Handling** - Try/except for safe operations
5. **User Confirmations** - messagebox for important actions

### **Code Structure:**
```python
# Main methods:
browse_folder()      # Select folder
scan_folder()        # Count files by category
organize_files()     # Move files to folders
undo_organization()  # Restore original structure
```

### **Extension:**
Want to add your own category?
```python
self.categories['MyCategory'] = ['.ext1', '.ext2', '.ext3']
```

---

## 🚀 Tips

### **Best Practices:**
1. **Test on Downloads first** - Safe to organize
2. **Don't organize system folders** - Stay away from C:\Windows, Program Files, etc.
3. **Backup important files** - Before organizing critical folders
4. **Use undo if unsure** - You can always reverse it

### **When to Use:**
- ✅ Downloads folder (perfect use case!)
- ✅ Desktop cleanup
- ✅ Project folders with mixed files
- ✅ USB drive organization
- ❌ System folders
- ❌ Folders you don't understand

---

## 🎯 Future Enhancements (Ideas)

- [ ] Custom category creation (user-defined)
- [ ] Schedule auto-organization (daily/weekly)
- [ ] Preview mode (see moves before confirming)
- [ ] Exclude certain files or folders
- [ ] Integration with cloud storage
- [ ] Statistics (files organized, space saved)

---

## 🐛 Troubleshooting

**Problem:** "Folder does not exist"
- **Solution:** Make sure the folder path is correct

**Problem:** "Permission denied"
- **Solution:** Run app as administrator or choose a folder you own

**Problem:** Duplicate filenames
- **Solution:** Automatically handled! Numbers added (file_1.txt)

**Problem:** Lost files after organizing
- **Solution:** Click "Undo" button or check category folders

---

## 📝 Technical Details

**Module:** `file_organizer_module.py`
**Version:** 1.0.0
**Dependencies:** tkinter, os, shutil, json, pathlib
**Platform:** Windows, macOS, Linux

**File Categories:**
- Images: 9 extensions
- Documents: 10 extensions
- Videos: 8 extensions
- Audio: 7 extensions
- Archives: 6 extensions
- Code: 10 extensions
- Executables: 7 extensions
- Other: Everything else

---

**Enjoy your organized folders!** 🎉
