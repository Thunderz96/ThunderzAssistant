# 🚀 Planned Features - ThunderzAssistant

This document tracks features planned for future implementation in ThunderzAssistant. Features are organized by category and priority.

---

## 🎮 Gaming & Social Integration

### Discord Rich Presence
**Status:** Planned
**Priority:** High
**Description:**
Display what you're currently doing in ThunderzAssistant as your Discord status.

**Proposed Features:**
- 🎵 Show current Spotify track on Discord
- 🍅 Display Pomodoro session status ("Focusing - 15:30 remaining")
- 💻 Show system stats ("Monitoring - CPU: 45%")
- 📊 Display stock portfolio performance
- 🎯 Custom status messages per module
- ⚙️ Toggle on/off in settings
- 🎨 Custom Discord app ID for branding

**Technical Requirements:**
- `pypresence` library for Discord RPC
- Discord app registration for custom rich presence
- Background thread for status updates
- Privacy controls (user opt-in)

**Use Cases:**
- Let friends know when you're in a focus session
- Show off your productivity workflow
- Share what you're monitoring/tracking

---

### Video Game News Module
**Status:** Planned
**Priority:** Medium
**Description:**
Stay updated with the latest news from your favorite MMORPGs without leaving your productivity hub.

**Supported Games:**
- 🐉 **Final Fantasy XIV**
  - Patch notes and updates
  - Lodestone official news
  - Maintenance schedules
  - Event announcements
  - Hot fixes and known issues

- ⚔️ **World of Warcraft**
  - Patch notes
  - Hotfixes
  - Blue posts from forums
  - Expansion news
  - Server status and maintenance

**Proposed Features:**
- 📰 Game selector dropdown (FF14, WoW, or both)
- 🔔 Notification system for new posts
- 🔗 Direct links to official sources
- ⏰ Auto-refresh (configurable interval)
- 📅 Maintenance calendar integration
- 🎨 Game-themed card styling (blue for FF14, red/gold for WoW)
- 💾 Save favorite news articles

**Data Sources:**
- Lodestone RSS feed (FF14)
- Battle.net API (WoW)
- Wowhead news RSS (WoW)
- MMO-Champion API (fallback)

**Technical Requirements:**
- RSS feed parsing
- Web scraping (if needed)
- API key management for Battle.net
- Category filtering
- Caching for performance

---

## 💻 Technology & System News

### Tech News Hub
**Status:** Planned
**Priority:** High
**Description:**
Centralized feed for the latest technology news, with focus on computers, phones, and Windows updates.

**News Categories:**
- 🪟 **Windows Updates**
  - Security patches
  - Feature updates
  - Known issues and bugs
  - Windows Insider builds
  - Update deadlines

- 💾 **Computer Hardware**
  - CPU/GPU releases
  - Component reviews
  - Price drops and deals
  - Tech benchmarks
  - Industry news (Intel, AMD, NVIDIA)

- 📱 **Phone & Mobile**
  - iOS/Android updates
  - New device launches
  - App updates and features
  - Mobile security news

- 🐛 **Security & Bug Alerts**
  - CVE notifications
  - Zero-day exploits
  - Patch urgency indicators
  - Malware warnings
  - Best security practices

**Proposed Features:**
- 📑 Tabbed interface (Windows / Hardware / Mobile / Security)
- 🔍 Search/filter by keyword
- ⚠️ Priority indicators (critical/high/medium/low)
- 🔔 Alert system for critical Windows updates
- 📊 Update history tracker
- 🔗 Direct links to patch downloads
- 📅 Update calendar (upcoming releases)
- 💾 Bookmarking system

**Data Sources:**
- Microsoft Update Catalog API
- Windows Update RSS
- TechCrunch, The Verge, Ars Technica APIs
- Reddit API (r/Windows, r/hardware, r/technology)
- CVE database for security news
- Tom's Hardware RSS
- AnandTech RSS

**Technical Requirements:**
- Multiple RSS feed aggregation
- API integrations (Reddit, news sites)
- Severity classification algorithm
- Update checking against Windows Update API
- Caching with smart refresh
- Keyword filtering and tagging

---

## 🎵 Media & Entertainment

### Expanded Media Integration
**Status:** Planned (Enhancement of existing feature)
**Priority:** Low
**Description:**
Enhance the current Spotify integration with additional media players and features.

**Proposed Features:**
- 🎵 Support for additional players:
  - Apple Music (iTunes)
  - YouTube Music
  - VLC Media Player
  - Windows Media Player

- 📊 Listening statistics:
  - Top tracks of the day/week
  - Total listening time
  - Genre breakdown

- 🎮 Game soundtrack detection:
  - Auto-detect when playing games
  - Display game title instead of music
  - Integration with Discord presence

---

## 📊 Productivity Enhancements

### Enhanced Pomodoro Features
**Status:** Planned (Enhancement of existing feature)
**Priority:** Medium
**Description:**
Expand the existing Pomodoro timer with advanced features.

**Proposed Features:**
- ⏱️ Customizable durations (not just 25/5/15)
- 📝 Task labels per pomodoro session
- 📊 Weekly/monthly statistics
- 📈 Productivity graphs and charts
- 🔔 Custom notification sounds
- 🎯 Daily goals (target pomodoro count)
- 📅 Calendar integration
- 📁 Export stats to CSV/Excel
- 🏆 Achievement system

---

## 📈 System Monitoring Upgrades

### Advanced System Monitor
**Status:** Planned (Enhancement of existing feature)
**Priority:** Medium
**Description:**
Enhance the System Monitor with professional-grade features.

**Proposed Features:**
- 📊 Historical graphs (CPU/RAM/GPU over time)
- 🌡️ Temperature monitoring (CPU, GPU, motherboard)
- 🌐 Network usage statistics (upload/download)
- 💾 All storage drives (not just C:)
- 🔍 Detailed process viewer:
  - Kill processes from GUI
  - Process search/filter
  - CPU/RAM usage per process
  - Process tree view

- ⚠️ Alert system:
  - High temperature warnings
  - Low disk space alerts
  - High CPU/RAM usage notifications

- 📸 System snapshot export
- 🎮 Advanced GPU stats (clock speeds, VRAM)
- ⚡ Battery monitoring (for laptops)

---

## 🌐 New Module Ideas

### GitHub Activity Monitor
**Status:** Idea Stage
**Priority:** Low
**Description:**
Track your GitHub activity and repositories.

**Proposed Features:**
- 📊 Contribution graph
- ⭐ Starred repositories feed
- 🔔 Issue/PR notifications
- 📈 Repository statistics
- 👥 Follower updates

---

### Crypto Dashboard
**Status:** Idea Stage (Extension of Stock Monitor)
**Priority:** Low
**Description:**
Enhanced crypto tracking beyond basic stock monitor.

**Proposed Features:**
- 💰 Multiple exchange support
- 📊 Advanced charts with indicators
- 🔔 Price alerts with sound
- 💼 Portfolio with cost basis tracking
- 📈 Profit/loss calculations
- 🌐 Gas price monitor (Ethereum)

---

### Quick Notes Module
**Status:** Idea Stage
**Priority:** Low
**Description:**
Simple note-taking integrated into the dashboard.

**Proposed Features:**
- 📝 Markdown support
- 📁 Category organization
- 🔍 Search functionality
- 📌 Pin important notes
- 💾 Auto-save
- 📤 Export to files

---

## 🎯 Implementation Priority

### Phase 1 (High Priority)
1. ✨ **Discord Rich Presence** - Social integration
2. 💻 **Tech News Hub** - Windows Updates & Bug tracking
3. 🎮 **Video Game News** - FF14 & WoW tracking

### Phase 2 (Medium Priority)
4. 📊 **Enhanced Pomodoro Features**
5. 🖥️ **Advanced System Monitor**

### Phase 3 (Low Priority / Future)
6. 🎵 **Expanded Media Integration**
7. 🌐 **GitHub Activity Monitor**
8. 💰 **Crypto Dashboard Enhancement**
9. 📝 **Quick Notes Module**

---

## 📚 Technical Considerations

### New Dependencies (Estimated)
```txt
# Discord Integration
pypresence>=4.3.0

# Game News
beautifulsoup4>=4.12.0
feedparser>=6.0.10

# Tech News
praw>=7.7.0  # Reddit API
newspaper3k>=0.2.8  # News scraping
python-dateutil>=2.8.2

# Enhanced monitoring
py-cpuinfo>=9.0.0
GPUtil>=1.4.0
```

### API Keys Required
- 🔷 Discord Developer Portal (Rich Presence app ID)
- ⚔️ Battle.net API (World of Warcraft news)
- 🤖 Reddit API (Tech news aggregation)
- 📰 NewsAPI (General tech news)

### Module Architecture
All new modules will follow the established pattern:
- Inherit from base module template
- Respect dark theme colors
- Include error handling
- Support keyboard shortcuts
- Auto-refresh capabilities
- Thread-safe UI updates
- Data persistence when needed

---

## 💡 Feature Requests

**Have an idea?** Add it here!

### Template
```markdown
### Feature Name
**Status:** Proposed
**Priority:** TBD
**Description:**
[Describe your feature idea]

**Proposed Features:**
- [ ] Feature 1
- [ ] Feature 2

**Why it would be useful:**
[Explain the use case]
```

---

## 📝 Notes

- Features marked as **Planned** have been approved for development
- Features marked as **Idea Stage** are under consideration
- Priority levels: High (next release), Medium (future release), Low (nice to have)
- All features subject to technical feasibility review
- Module architecture must be maintained
- Dark theme compliance is mandatory
- Security best practices for all API integrations

---

## 🔗 Related Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Creating new modules
- [Current Features](../README.md) - What's already implemented
- [Version History](../CHANGELOG.md) - Past updates

---

**Last Updated:** 2026-02-09
**Document Version:** 1.0.0

---

*Have ideas? Fork the project and add your own modules! ThunderzAssistant is designed to be infinitely extensible.* ⚡
