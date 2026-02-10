# Discord Rich Presence - User Guide

## 🎮 What is Discord Rich Presence?

Discord Rich Presence lets you show what you're doing in Thunderz Assistant directly on your Discord profile! Your friends can see when you're:

- 🍅 In a Pomodoro focus session ("Focusing - 15:30 remaining")
- 🎵 Listening to Spotify ("Listening to Thunderstruck - AC/DC")
- 💻 Monitoring your system ("Monitoring System - CPU: 45%")
- 📊 Checking stocks ("Watching Stocks - Portfolio: +2.5%")
- 📁 Organizing files ("Organizing Files")
- And more!

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Library
```bash
.\install_discord_presence.bat
```

OR

```bash
pip install pypresence
```

### Step 2: Get Discord Application ID

1. Go to: https://discord.com/developers/applications
2. Click "New Application"
3. Name it "Thunderz Assistant"
4. Copy your "Application ID" (18-19 digit number)

### Step 3: Add to Config

1. Open `config.py`
2. Add this line:
```python
DISCORD_APP_ID = "1234567890123456789"  # Your actual ID
```

### Step 4: Launch & Connect

1. Open Thunderz Assistant
2. Click **🎮 Discord** in sidebar
3. Click **"Connect to Discord"**
4. Check your Discord profile - it's working! 🎉

---

## 🎯 How to Use

### Basic Usage:

1. **Start Discord** (make sure it's running)
2. **Open Thunderz Assistant**
3. **Go to Discord module**
4. **Click "Connect to Discord"**
5. **Use any module** - your status updates automatically!

### What Shows Up:

Your Discord profile will display:

```
Playing Thunderz Assistant
📍 Dashboard
Idle
```

When you switch modules:

```
Playing Thunderz Assistant
📍 Pomodoro
Focusing - 25:00 remaining
```

---

## ⚙️ Settings

### Show Elapsed Time
- ✅ **On**: Shows how long you've been using the app
- ❌ **Off**: No timestamp

### Auto-Connect on Startup
- ✅ **On**: Connects to Discord automatically when you open the app
- ❌ **Off**: You manually connect each time

---

## 🎨 Customization (Advanced)

### Upload Custom Images

1. Go to Discord Developer Portal
2. Select your application
3. Go to **Rich Presence** → **Art Assets**
4. Upload images:
   - `thunderz_logo` - Your app logo
   - `dashboard_icon` - Dashboard icon
   - `pomodoro_icon` - Pomodoro icon
   - etc.

Images should be 512x512 PNG files.

### Status Messages

The module automatically updates based on what you're doing:

| Module | Status Example |
|--------|----------------|
| Dashboard | "Viewing dashboard" |
| Pomodoro | "Focusing - 25:00 remaining" |
| Weather | "Checking weather" |
| News | "Reading news" |
| System Monitor | "Monitoring system" |
| Stocks | "Tracking portfolio" |
| File Organizer | "Organizing files" |
| Glizzy | "Rolling dice" |

---

## 🔒 Privacy & Control

### You Control Everything:

- ✅ Connect only when you want
- ✅ Disconnect anytime
- ✅ No data sent to Discord except your status
- ✅ Only shows when Discord is running
- ✅ Settings saved locally

### To Hide Your Status:

1. Click "Disconnect" in Discord module
2. Close Thunderz Assistant
3. Set Discord to "Invisible" mode

---

## 🐛 Troubleshooting

### "Connection Failed"

**Problem:** Can't connect to Discord

**Solutions:**
- Make sure Discord app is running
- Restart Discord
- Check you're not in "Invisible" mode
- Verify Application ID is correct in config.py

### "Discord Not Detected"

**Problem:** App says Discord isn't running

**Solutions:**
- Launch Discord desktop app
- Wait 10 seconds after opening Discord
- Restart Thunderz Assistant
- Check Discord is logged in

### "Status Not Showing"

**Problem:** Connected but status doesn't appear

**Solutions:**
- Close and reopen Discord
- Disconnect and reconnect in app
- Check Windows firewall settings
- Verify Application ID is valid

### "pypresence Not Found"

**Problem:** Module shows error about missing library

**Solutions:**
```bash
pip install pypresence
```

OR run:
```bash
.\install_discord_presence.bat
```

---

## 💡 Pro Tips

### Tip 1: Auto-Connect
Enable "Auto-connect on startup" to automatically show your status when you launch the app!

### Tip 2: Custom Status
Edit `discord_presence_module.py` to create your own custom status messages!

### Tip 3: Toggle Quickly
Use keyboard shortcuts to switch modules - your Discord status updates instantly!

### Tip 4: Focus Sessions
When you start a Pomodoro, your friends see "Focusing" - they know not to disturb you!

### Tip 5: Spotify Integration
If you're listening to Spotify while using the app, it can show your current track!

---

## 📊 What Your Friends See

### On Desktop:

```
┌─────────────────────────────────────┐
│  Your Name                          │
│  🟢 Online                          │
│                                     │
│  Playing Thunderz Assistant         │
│  📍 Pomodoro                        │
│  Focusing - 15:30 remaining         │
│                                     │
│  Elapsed: 01:34:22                  │
└─────────────────────────────────────┘
```

### On Mobile:

```
Your Name  🟢
Playing Thunderz Assistant
📍 Pomodoro
Focusing - 15:30 remaining
```

---

## 🎮 Example Scenarios

### Scenario 1: Work Focus
```
You: [Open Pomodoro module]
Your Status: "Focusing - 25:00 remaining"
Friend: *Sees you're busy, doesn't message*
```

### Scenario 2: Organizing Files
```
You: [Open File Organizer]
Your Status: "Organizing Downloads folder"
Friend: "Wow, that's productive!"
```

### Scenario 3: Monitoring System
```
You: [Open System Monitor]
Your Status: "Monitoring System - CPU: 45%"
Friend: "Is your PC okay?"
You: "Yeah, just checking!"
```

---

## 🔗 Related Features

- **Pomodoro Timer**: Syncs with Discord to show focus sessions
- **Spotify Detection**: Shows current track on Discord
- **Module Switching**: Auto-updates status on every module change

---

## 📚 Technical Details

### How It Works:

1. **pypresence library**: Connects to Discord via RPC
2. **Background thread**: Updates every 15 seconds
3. **Module hooks**: Each module can update status
4. **Local connection**: No data sent to external servers

### Requirements:

- Discord desktop app (running)
- pypresence library installed
- Discord Application ID configured
- Windows 10/11 (recommended)

### Performance:

- ⚡ Minimal CPU usage (<0.1%)
- 💾 Small memory footprint (~5MB)
- 🔋 No battery impact
- 🌐 No internet required (except initial Discord connection)

---

## ❓ FAQ

**Q: Does this work with Discord web browser?**
A: No, requires Discord desktop app.

**Q: Can I use this without Discord?**
A: Yes! The module is optional. Just don't enable it.

**Q: Will my friends see everything I do?**
A: Only what Discord Rich Presence shares (module name and activity).

**Q: Can I customize the messages?**
A: Yes! Edit `discord_presence_module.py` to customize.

**Q: Does this slow down my computer?**
A: No, it uses minimal resources.

**Q: Is my data safe?**
A: Yes, only sends status to Discord. No personal data.

---

## 🎉 Have Fun!

Discord Rich Presence makes your productivity visible and shareable!

Show off your focus sessions, impress friends with your organization skills, and let everyone know when you're in the zone! 🚀

---

**Questions? Check docs/DISCORD_SETUP.md for technical setup details!**
