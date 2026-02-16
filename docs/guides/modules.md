# Module Index

All public modules available in Thunderz Assistant v1.12.4.

---

## Public Modules

| # | Icon | Module | Priority | Shortcut | Description |
|---|------|--------|----------|----------|-------------|
| 1 | 📊 | **Dashboard** | 1 | Ctrl+1 | Customizable home screen with widgets: clock, weather, quotes, Spotify, notes, focus stats, quick tasks, and crypto prices. |
| 2 | 🗒️ | **Notes** | 7 | Ctrl+4 | Markdown-ready note-taking with categories, tags, pinning, search, and export to `.md` / `.txt` / `.zip`. |
| 3 | 🍅 | **Pomodoro** | 3 | Ctrl+3 | Focus timer with customizable durations, task labeling, bar charts, and yearly contribution heatmap. |
| 4 | 📈 | **Stock Monitor** | 4 | Ctrl+5 | Real-time stock/ETF/crypto watchlist with price charts, price alerts, and Notification Center integration. |
| 5 | 💻 | **System Monitor** | 5 | Ctrl+6 | Live CPU, RAM, storage, NVIDIA GPU, and top-process monitoring. |
| 6 | 🔔 | **Notifications** | 8 | Ctrl+7 | Centralized hub for all module alerts with history, DND mode, unread badge, and action buttons. |
| 7 | 📁 | **File Organizer** | 6 | Ctrl+8 | One-click folder cleanup — sorts 70+ extensions into 8 categories with dry-run preview and undo. |
| 8 | 🌤️ | **Weather** | 2 | Ctrl+2 | Auto-detected location weather with temperature, humidity, wind, and UV index (wttr.in, no API key). |
| 9 | 📰 | **News** | 9 | — | Top world headlines via NewsAPI.org (free API key required). |
| 10 | 🎮 | **Discord** | 10 | — | Discord Rich Presence (shows current module) and Webhook messaging to Discord channels. |
| 11 | 🎬 | **Glizzy** | 11 | — | Local video player with loop support. |
| 12 | 📥 | **YouTube Downloader** | 12 | — | Download videos and audio from YouTube via yt-dlp. |
| 13 | 📋 | **Clipboard** | 9 | — | Persistent 50-item clipboard history with search and click-to-copy. |

---

## Module Priority System

Modules are sorted by their `PRIORITY` class attribute (lower = higher in sidebar):

```
1  → Dashboard (always first)
2  → Weather
3  → Pomodoro
4  → Stock Monitor
5  → System Monitor
6  → File Organizer
7  → Notes
8  → Notifications
9  → News / Clipboard
10 → Discord
11 → Glizzy
12 → YouTube Downloader
99 → (default for new modules)
```

---

## Adding a New Module

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the full guide. The short version:

1. Create `modules/your_module.py`
2. Define a class ending in `Module` with `ICON` and `PRIORITY`
3. `__init__(self, parent_frame, colors)` — build your UI there
4. Launch the app — it auto-discovers your module ✨
