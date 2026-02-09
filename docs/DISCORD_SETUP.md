# Discord Rich Presence Setup Guide

## 🎮 Getting Your Discord Application ID

### Step 1: Go to Discord Developer Portal
1. Visit: https://discord.com/developers/applications
2. Log in with your Discord account

### Step 2: Create New Application
1. Click **"New Application"** (top right)
2. Name it: **"Thunderz Assistant"**
3. Click **"Create"**

### Step 3: Get Your Application ID
1. You'll see your app dashboard
2. Look for **"APPLICATION ID"** near the top
3. Click **"Copy"** to copy the ID
4. It looks like: `1234567890123456789` (18-19 digits)

### Step 4: Add to Config
1. Open `config.py`
2. Add this line:
```python
# Discord Rich Presence
DISCORD_APP_ID = "YOUR_APPLICATION_ID_HERE"  # Paste your ID here
```

### Step 5: Optional - Add Rich Presence Images
1. In Discord Developer Portal, go to **"Rich Presence"** → **"Art Assets"**
2. Upload images:
   - **thunderz_logo** - Your app logo (512x512 recommended)
   - **dashboard_icon** - Dashboard module icon
   - **pomodoro_icon** - Pomodoro module icon
   - **weather_icon** - Weather module icon
   - etc.

3. Image names should be lowercase with underscores

---

## 📦 Installation

### Install Required Library
```bash
pip install pypresence
```

That's it! The library is simple and lightweight.

---

## ✅ Quick Test

After setup, your Discord profile will show:
```
Playing Thunderz Assistant
Using Dashboard Module
```

---

## 🎨 Customization

### Custom Status Messages
Edit the module to show:
- 🎵 Currently playing song
- 🍅 Pomodoro timer countdown
- 💻 System stats
- 📊 Whatever you want!

### Privacy Controls
You can:
- Toggle presence on/off in settings
- Choose which modules show status
- Disable entirely

---

## 🐛 Troubleshooting

### "Discord not detected"
- Make sure Discord app is running
- Try restarting Discord
- Check Discord is not in "invisible" mode

### "Connection failed"
- Verify your Application ID is correct
- Make sure you copied the full ID
- Check Discord Developer Portal is accessible

### "Status not updating"
- Close and reopen Discord
- Restart Thunderz Assistant
- Check Windows firewall settings

---

## 🔗 Useful Links

- [Discord Developer Portal](https://discord.com/developers/applications)
- [pypresence Documentation](https://qwertyquerty.github.io/pypresence/html/index.html)
- [Discord Rich Presence Guide](https://discord.com/developers/docs/rich-presence/how-to)

---

**Ready?** Once you have your Application ID, add it to config.py and we're good to go! 🚀
