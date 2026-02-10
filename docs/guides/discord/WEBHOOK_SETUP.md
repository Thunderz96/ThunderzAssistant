# Discord Webhook Setup Guide

## 💬 What are Discord Webhooks?

Webhooks let you **send messages** to Discord channels from Thunderz Assistant!

Unlike Rich Presence (which shows your status), webhooks let you:
- 📨 Send actual messages to channels
- 🎯 Post notifications ("Completed 4 pomodoros!")
- 📊 Send productivity reports
- 🚨 Post system alerts
- 💬 Share updates with friends/team

---

## 🚀 Quick Setup (2 Minutes)

### Step 1: Create Webhook in Discord

1. **Open Discord** desktop app or web
2. **Go to your server** (or create one if you don't have one)
3. **Pick a channel** where you want messages to appear
4. **Right-click the channel** → **Edit Channel**
5. Go to **Integrations** tab
6. Click **Webhooks** → **New Webhook**
7. **Name it**: "Thunderz Assistant" (or anything you want)
8. **Copy the Webhook URL** (looks like: `https://discord.com/api/webhooks/123456...`)

### Step 2: Add to Config

1. Open `config.py` in your Thunderz Assistant folder
2. Find the line: `DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"`
3. Replace with your actual webhook URL:
```python
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1234567890/ABCDEFG..."
```

### Step 3: Test It!

1. **Restart Thunderz Assistant**
2. Click **🎮 Discord** in sidebar
3. Go to **💬 Send Messages** tab
4. Type a message and click **📤 Send to Discord**
5. Check your Discord channel - message appears! 🎉

---

## 🎯 What You Can Do

### Quick Actions (One-Click):

1. **🎯 Pomodoro Complete** - Post completion notification
   ```
   🍅 Pomodoro Complete!
   
   Completed 5 pomodoros today
   Focus time: 125 minutes
   ```

2. **📊 Daily Report** - Send productivity summary
   ```
   📊 Daily Productivity Report
   Summary for February 09, 2026
   
   🍅 Pomodoros: 8
   ⏱️ Focus Time: 3h 20m
   📈 Status: Great job!
   ```

3. **💻 System Status** - Post system stats
   ```
   💻 System Status Update
   
   CPU Usage: 45%
   RAM Usage: 62%
   Status: 🟢 Normal
   ```

4. **📈 Stock Update** - Share portfolio status
   ```
   📈 Portfolio Status
   Current market status
   ```

### Custom Messages:

Type anything and send it:
- Share progress updates
- Post reminders
- Log achievements
- Notify team members
- Journal entries
- Quick notes

---

## 🎨 Example Messages

### Pomodoro Notification:
```
🍅 Pomodoro Complete!

Just completed a focus session!
Today's Progress: 3 pomodoros
Focus Time: 75 minutes
```

### Daily Report:
```
📊 Daily Productivity Report
February 09, 2026

🍅 Pomodoros Completed: 8
⏱️ Total Focus Time: 3h 20m
📈 Status: Great job!
```

### System Alert:
```
💻 System Status

CPU Usage: 45%
RAM Usage: 62%
Status: 🟢 Normal
```

### Custom Message:
```
Just finished organizing my Downloads folder!
Sorted 847 files into categories 📁✨
```

---

## 💡 Pro Tips

### Tip 1: Dedicated Channel
Create a dedicated channel like `#thunderz-notifications` for cleaner organization

### Tip 2: Auto-Post Achievements
Set up automatic notifications when you complete pomodoros or reach goals

### Tip 3: Team Accountability
Share your webhook with team members so everyone can see productivity updates

### Tip 4: Daily Standup
Send daily reports to your team channel for async standups

### Tip 5: Personal Journal
Use webhooks as a personal journal in a private Discord channel

---

## 🔒 Security & Privacy

### **IMPORTANT: Protect Your Webhook URL!**

**❌ DON'T:**
- Share webhook URL publicly
- Commit webhook URL to GitHub
- Post webhook URL in Discord
- Give webhook to untrusted people

**✅ DO:**
- Keep webhook URL in config.py (it's gitignored)
- Regenerate webhook if compromised
- Use separate webhooks for different purposes
- Delete unused webhooks

### **Why it matters:**
Anyone with your webhook URL can send messages to your channel!

### **If Compromised:**
1. Go to Discord → Channel → Edit → Integrations → Webhooks
2. Click on your webhook
3. Click "Delete Webhook"
4. Create a new one
5. Update config.py with new URL

---

## 🐛 Troubleshooting

### "Webhook URL Not Configured"

**Problem:** Module shows setup required message

**Solution:**
- Check config.py has `DISCORD_WEBHOOK_URL = "..."`
- Make sure URL starts with `https://discord.com/api/webhooks/`
- Restart Thunderz Assistant after adding URL

### "Failed to Send Message"

**Problem:** Message doesn't appear in Discord

**Solutions:**
- Check webhook URL is correct
- Verify webhook still exists in Discord
- Check internet connection
- Make sure webhook wasn't deleted
- Try regenerating webhook

### "Message Shows But Looks Weird"

**Problem:** Message appears but formatting is off

**Solution:**
- Discord embeds may not render properly in mobile
- Check on desktop Discord for full formatting
- Some rich embeds require desktop app

### "Rate Limited"

**Problem:** "Too many requests" error

**Solution:**
- Discord limits webhooks to 30 messages per minute
- Wait a minute and try again
- Don't spam the send button

---

## 📱 Mobile Support

### Discord Mobile App:
- ✅ Receives webhook messages
- ✅ Shows basic text
- ⚠️ Rich embeds may not display fully
- ✅ Notifications work normally

**Best Experience:** Desktop Discord app

---

## 🔗 Multiple Webhooks

You can create multiple webhooks for different purposes:

### **Example Setup:**

**config.py:**
```python
# Main notifications webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123..."

# Optional: Separate webhooks
DISCORD_POMODORO_WEBHOOK = "https://discord.com/api/webhooks/456..."
DISCORD_ALERTS_WEBHOOK = "https://discord.com/api/webhooks/789..."
```

Then modify the webhook module to use different URLs for different message types!

---

## 🎮 Combining with Rich Presence

**Use Both Features Together:**

1. **Rich Presence** - Shows what module you're viewing in real-time
2. **Webhooks** - Sends notifications/messages to channels

**Example Flow:**
```
You: [Start Pomodoro timer]
Rich Presence: Shows "🍅 Focusing - 25:00 remaining"
              (Friends see you're busy)

[Timer ends]
Rich Presence: Shows "☕ Short break"
Webhook: Posts "🍅 Pomodoro Complete! 3/8 today"
         (Message appears in your channel)
```

**Perfect Combo!**

---

## 📚 Technical Details

### Webhook Format:

**Simple Message:**
```json
{
  "content": "Your message here"
}
```

**Rich Embed:**
```json
{
  "content": "🎯 Notification",
  "embeds": [{
    "title": "Pomodoro Complete",
    "description": "Just finished a session!",
    "color": 3066993,
    "fields": [
      {
        "name": "Today's Progress",
        "value": "5 pomodoros",
        "inline": true
      }
    ],
    "timestamp": "2026-02-09T12:34:56Z"
  }]
}
```

### Color Codes:
- Green: `3066993`
- Blue: `3447003`
- Red: `15158332`
- Orange: `15105570`
- Purple: `10181046`
- Yellow: `16776960`

---

## 🔧 Advanced Usage

### Auto-Send from Other Modules:

```python
from discord_webhook_module import send_to_discord

# In pomodoro_module.py
def timer_complete(self):
    # ... timer logic ...
    
    # Auto-send to Discord
    send_to_discord("🍅 Pomodoro complete!")
```

### Custom Embeds:

```python
embeds = [{
    "title": "Custom Notification",
    "description": "Your description here",
    "color": 3066993,
    "fields": [
        {"name": "Field 1", "value": "Value 1"},
        {"name": "Field 2", "value": "Value 2"}
    ]
}]

send_to_discord("Message", embeds=embeds)
```

---

## ❓ FAQ

**Q: Can I send images?**
A: Yes! Use embeds with `"image": {"url": "https://..."}"`

**Q: Can I @mention people?**
A: Yes! Use `<@USER_ID>` in your message

**Q: How many messages can I send?**
A: Discord limits to 30 messages per minute per webhook

**Q: Can I delete messages I sent?**
A: No, webhooks can't delete messages (only send)

**Q: Do webhooks work with Rich Presence?**
A: Yes! They're separate features that work together

**Q: Can I use multiple webhooks?**
A: Yes! Create multiple webhooks for different channels

---

## 🎉 You're Ready!

**Webhook Setup Complete!** 

Now you can:
- ✅ Send messages to Discord channels
- ✅ Post productivity notifications
- ✅ Share updates with friends/team
- ✅ Log achievements automatically
- ✅ Create custom notifications

---

**Questions?**
- Check docs/DISCORD_USAGE_GUIDE.md for Rich Presence
- See DISCORD_IMPLEMENTATION.md for technical details
- Read main documentation in README.md

**Have fun sharing your productivity!** 🚀
