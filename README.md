# ⚡ Thunderz Assistant

A modular, productivity-focused GUI application built with Python. Your Swiss Army knife for daily tasks, system monitoring, and workflow optimization!

---

## 🎯 Current Version: **1.6.0**

### 🎨 What's New in v1.6.0?
- **Menu Bar**: Professional menu system (File, View, Help)
- **Status Bar**: Module indicator, tips, and version display
- **Tooltips**: Helpful hints on hover for all buttons
- **Keyboard Shortcuts**: Ctrl+1,2,3 for quick navigation, F5 to refresh
- **Built-in Help**: Quick Start Guide, shortcuts reference, and documentation access
- **Active Highlighting**: Visual feedback showing current module
- **Looping Video**: Glizzy module video now loops continuously
- **Modern Design**: Segoe UI font, better spacing, professional appearance

---

## ⌨️ Keyboard Shortcuts

Make your workflow faster with these hotkeys:

| Shortcut | Action |
|----------|--------|
| **Ctrl+1** | Jump to Dashboard |
| **Ctrl+2** | Jump to News |
| **Ctrl+3** | Jump to Weather |
| **F5** | Refresh current module |
| **Ctrl+Q** | Quit application |

💡 **Tip:** Hover over any button for helpful tooltips!

---

## ✨ Features

### 📊 Dashboard (Home Screen)
Your daily command center:
- ⏰ **Live clock** with time-based greetings
- 📅 **Current date** display
- 🌤️ **Weather summary** with auto-location
- 🎵 **Now Playing** - Spotify status (Windows)
- 💡 **Daily motivational quote** (30+ quotes)
- ✅ **Quick Tasks** with persistence

### 🍅 Pomodoro Timer
Focus timer using the Pomodoro Technique:
- ⏱️ **25-minute work sessions**
- ☕ **5-minute short breaks**
- 🌴 **15-minute long breaks** (after 4 pomodoros)
- 📊 **Daily tracking** with statistics
- 🔔 **Sound notifications**

### 💻 System Monitor
Real-time computer stats:
- 🔥 **CPU usage** (total + per-core)
- 🧠 **RAM usage** with progress bars
- 💾 **All storage drives** (not just C:)
- ⚡ **Top 5 CPU processes**
- 🧠 **Top 5 RAM processes**
- 🎮 **GPU monitoring** (NVIDIA cards)
- ⏱️ **System uptime**

### 📈 Stock Monitor
Real-time stock market tracking:
- 📊 **Live stock prices** (stocks, ETFs, crypto)
- 📈 **Historical charts** (1D, 1W, 1M, 1Y, 5Y)
- 💼 **Portfolio tracking** with P&L
- 🔔 **Price alerts** (customizable thresholds)
- ⏱️ **Auto-refresh** every 60 seconds

### 📁 File Organizer
Automatically organize messy folders:
- 🔍 **Scan any folder** (default: Downloads)
- 📊 **File type breakdown** (70+ extensions)
- ✨ **One-click organization** into category folders
- ↩️ **Undo functionality** to restore structure
- 🛡️ **Safe mode** (handles duplicates automatically)
- 🚫 **System protection** (30+ forbidden folders blocked)
- ✅ **Safety indicator** (visual confirmation)
- 📂 **8 categories**: Images, Documents, Videos, Audio, Archives, Code, Executables, Other

### 🌤️ Weather Checker
Real-time weather for any city:
- 🌍 **Auto-location detection**
- 📍 **"My Location" button**
- 🌡️ **Temperature** (°C and °F)
- 💨 **Wind, humidity, UV index**

### 📰 Breaking News
Top headlines (requires free API key):
- 📱 **Top 5 news stories**
- 🔗 **Clickable article links**
- 🎨 **Card-style layout**

---

## 🚀 Quick Start

### 1. Install Python
Python 3.7+ required. [Download here](https://www.python.org/downloads/)

### 2. Install Dependencies
```bash
cd ThunderzAssistant
pip install -r requirements.txt
```

### 3. Configure API Keys (Optional)
```bash
# Copy the template
copy config.example.py config.py

# Edit config.py and add your News API key
# Get free key at: https://newsapi.org/register
```

**Important:** `config.py` is gitignored for security!

### 4. Run the App
```bash
python main.py
```

---

## 📚 Documentation

**All detailed docs are in the [`docs/`](docs/) folder:**

- **[📖 Documentation Index](docs/README.md)** - Start here!
- **[🚀 Quick Start Guide](docs/QUICKSTART.md)** - Detailed setup
- **[🔐 Security Guide](docs/SECURITY.md)** - Protect API keys
- **[👨‍💻 Developer Guide](docs/DEVELOPER_GUIDE.md)** - Create modules
- **[🐛 Bug Fixes Log](docs/)** - Version history details

**Quick Links:**
- [How to create a new module](docs/DEVELOPER_GUIDE.md)
- [How to customize colors](docs/DARK_THEME_UPDATE.md)
- [Understanding the Pomodoro Timer](docs/NEW_FEATURES_V1.3.md)
- [Enabling GPU monitoring](docs/FIXES_V1.3.2.md)

---

## 📁 Project Structure

```
ThunderzAssistant/
│
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── config.py                    # Your config (gitignored)
├── config.example.py            # Config template
├── .gitignore                   # Git exclusions
├── CHANGELOG.md                 # Version history
├── README.md                    # This file
│
├── docs/                        # 📚 All documentation
│   ├── README.md                # Documentation index
│   ├── QUICKSTART.md
│   ├── DEVELOPER_GUIDE.md
│   ├── SECURITY.md
│   └── ... (version docs)
│
├── modules/                     # 🔧 Feature modules
│   ├── dashboard_module.py      # Dashboard home screen
│   ├── weather_module.py        # Weather checker
│   ├── news_module.py           # Breaking news
│   ├── pomodoro_module.py       # Focus timer
│   ├── system_monitor_module.py # System stats
│   └── template_module.py       # Module template
│
└── scripts/                     # 🛠️ Utility scripts
    └── (helper scripts)
```

---

## 🎨 Dark Theme

The app features a sleek **dark blue theme**:
- 🌑 Very dark backgrounds (#0F172A, #1E293B)
- 💡 Light text (#E2E8F0)
- 💙 Blue accents (#3B82F6)
- ❌ **Zero white backgrounds!**

**Want to customize?** See [docs/DARK_THEME_UPDATE.md](docs/DARK_THEME_UPDATE.md)

---

## 🔧 Requirements

### Core Dependencies
- **Python 3.7+** (tested on 3.13)
- **requests** - HTTP requests
- **psutil** - System monitoring

### Optional (for specific features)
- **pynvml** - NVIDIA GPU stats
- **yfinance** - Stock market data
- **matplotlib** - Stock charts
- **pandas** - Data analysis
- **pywin32** - Windows media detection (Windows only)

**All dependencies:** See `requirements.txt`

---

## 💡 Usage Tips

### For Productivity
- 🍅 Use Pomodoro for focused work sessions
- ✅ Track daily tasks on Dashboard
- 📊 Monitor system when multitasking

### For Gaming
- 🎮 Watch GPU load and temp
- 💾 Check VRAM usage
- 🔥 Monitor CPU bottlenecks

### For Development
- 💻 Track system resources during builds
- 📈 Identify memory leaks
- 🔍 Find CPU-hogging processes

---

## 🆕 Recent Updates

### v1.5.0 (Latest)
- ✅ File Organizer module
- ✅ Auto-organize folders by file type
- ✅ 70+ file extensions supported
- ✅ Undo functionality

### v1.4.2
- ✅ Fixed Spotify detection
- ✅ Now works with minimized Spotify
- ✅ More reliable song tracking

### v1.4.1
- ✅ Media Card on Dashboard
- ✅ Spotify status tracking (Windows)
- ✅ Live "Now Playing" display

### v1.3.1
- ✅ All storage drives (not just C:)
- ✅ Top process lists
- ✅ GPU monitoring
- ✅ Per-core CPU stats

### v1.3.0
- ✅ Dark theme
- ✅ Pomodoro Timer
- ✅ System Monitor

**Full history:** See [CHANGELOG.md](CHANGELOG.md)

---

## 🛠️ Adding Your Own Modules

Want to add features? It's designed to be modular!

**Quick Guide:**
1. Create `modules/your_module.py`
2. Follow the template in `modules/template_module.py`
3. Import in `main.py`
4. Add sidebar button

**Detailed Guide:** See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

---

## 🐛 Troubleshooting

### App Won't Start
- ✅ Check Python version: `python --version` (need 3.7+)
- ✅ Install dependencies: `pip install -r requirements.txt`

### GPU Stats Not Showing
- ✅ Only works with NVIDIA GPUs
- ✅ Install drivers from nvidia.com
- ✅ Verify: `nvidia-smi` should work
- ✅ Install pynvml: `pip install pynvml`

### Weather Not Loading
- ✅ Check internet connection
- ✅ Uses wttr.in (no API key needed)
- ✅ VPN may affect location detection

**More help:** See [docs/](docs/) folder

---

## 🔐 Security Notes

- ⚠️ **Never commit `config.py`** (contains API keys)
- ✅ Always commit `config.example.py` (template)
- ✅ `config.py` is in `.gitignore`

**Setup guide:** [docs/SECURITY.md](docs/SECURITY.md)

---

## 🤝 Contributing

This is a personal learning project, but feel free to:
- Fork and customize
- Add your own modules
- Improve existing features

---

## 📄 License

Personal and educational use.

---

## 🙏 Credits

- **Weather:** [wttr.in](https://wttr.in)
- **Location:** [ipapi.co](https://ipapi.co)
- **News:** [NewsAPI.org](https://newsapi.org)
- **System Monitoring:** [psutil](https://github.com/giampaolo/psutil)
- **GPU Monitoring:** [pynvml](https://github.com/gpuopenanalytics/pynvml)
- **Built with:** Python + tkinter

---

## 📞 Need Help?

1. Check the [docs/](docs/) folder
2. Read [QUICKSTART.md](docs/QUICKSTART.md)
3. Review [CHANGELOG.md](CHANGELOG.md) for known issues

---

**Happy Thundering! ⚡**

*A productivity assistant that grows with your needs.*
