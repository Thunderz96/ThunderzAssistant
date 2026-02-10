# 🎮 Discord Integration - Quick Start Card

## ⚡ 5-Minute Setup

### 1️⃣ Install (30 seconds)
```bash
.\install_discord_presence.bat
```

### 2️⃣ Rich Presence Setup (2 minutes)
1. Visit: https://discord.com/developers/applications
2. Create App → Copy Application ID
3. In `config.py`:
```python
DISCORD_APP_ID = "YOUR_APP_ID_HERE"
```

### 3️⃣ Webhook Setup (2 minutes)
1. Right-click Discord channel → Edit → Integrations → New Webhook
2. Copy Webhook URL
3. In `config.py`:
```python
DISCORD_WEBHOOK_URL = "YOUR_WEBHOOK_URL_HERE"
```

### 4️⃣ Use It! (30 seconds)
```bash
python main.py
```
- Click 🎮 Discord
- Tab 1: Connect Rich Presence
- Tab 2: Send a test message

---

## 🎯 What You Get

### Rich Presence (Tab 1)
```
Shows on your Discord profile:
Playing Thunderz Assistant
📍 Pomodoro
🍅 Focusing - 24:35 remaining
Pomodoro 5/8 today
```

### Webhooks (Tab 2)
```
Sends to Discord channel:
[Thunderz Assistant BOT]
🍅 Pomodoro Complete!
Completed 5 pomodoros today
Focus time: 125 minutes
```

---

## ✨ Key Features

✅ **Auto-Updates:** Switch modules → Discord updates instantly
✅ **Live Countdown:** Pomodoro timer shows on your profile
✅ **Quick Actions:** One-click notifications
✅ **Custom Messages:** Type and send anything
✅ **Team Collaboration:** Share progress with friends/team
✅ **Professional:** Rich embeds with colors and formatting

---

## 📚 Documentation

- `docs/DISCORD_SETUP.md` - Rich Presence setup
- `docs/DISCORD_USAGE_GUIDE.md` - How to use
- `docs/DISCORD_WEBHOOK_SETUP.md` - Webhook guide
- `DISCORD_VISUAL_GUIDE.md` - Visual overview
- `DISCORD_COMPLETE_INTEGRATION.md` - Full summary

---

## 🐛 Quick Troubleshooting

**Rich Presence not showing?**
→ Check Discord app is running + Application ID is correct

**Webhooks failing?**
→ Verify Webhook URL is correct + webhook exists

**Module not appearing?**
→ Restart Thunderz Assistant

---

## 💡 Pro Tip

**Use BOTH features together:**
- Rich Presence shows real-time status
- Webhooks send milestone notifications
- Perfect for productivity tracking!

---

**Ready? Run:** `python main.py` → Click 🎮 Discord! 🚀
