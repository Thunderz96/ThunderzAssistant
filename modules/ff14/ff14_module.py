"""
FF14 Module — Hub for all Final Fantasy XIV sub-tools.

Tabs:
  ⚙️  Gear Sets     — XIVGear API viewer + local saved sets
  🎲  Loot Tracker  — Static raid loot distribution tracker
  🔨  Crafting      — TeamCraft integration + local lists
  💹  Market Board  — Universalis price lookup
"""

import tkinter as tk
from tkinter import ttk

from .gear_tab import GearTab
from .loot_tab import LootTab
from .crafting_tab import CraftingTab
from .marketboard_tab import MarketBoardTab
from .static_tab import StaticTab
from .settings_tab import SettingsTab


# FF14 brand colours used for the tab bar (override local theme slightly)
FF14_GOLD   = "#C8A84B"
FF14_DARK   = "#1A1209"


class FF14Module:
    ICON     = "⚔️"
    PRIORITY = 10

    TABS = [
        ("⚙️  Gear Sets",    GearTab),
        ("👥  Static",       StaticTab),
        ("🎲  Loot Tracker", LootTab),
        ("🔨  Crafting",     CraftingTab),
        ("💹  Market Board", MarketBoardTab),
        ("🛠️  Settings",     SettingsTab),
    ]

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors

        self._tab_frames: dict[str, tk.Frame] = {}
        self._tab_instances: dict[str, object] = {}
        self._active_tab: str | None = None
        self._tab_btns: dict[str, tk.Button] = {}

        self._build_ui()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Banner ──
        banner = tk.Frame(self.parent, bg=FF14_DARK, pady=10)
        banner.pack(fill=tk.X)
        tk.Label(
            banner,
            text="⚔️   Final Fantasy XIV",
            font=("Segoe UI", 18, "bold"),
            bg=FF14_DARK, fg=FF14_GOLD,
        ).pack(side=tk.LEFT, padx=20)
        tk.Label(
            banner,
            text="Gear · Static · Loot · Crafting · Market · Settings",
            font=("Segoe UI", 10),
            bg=FF14_DARK, fg="#8A7240",
        ).pack(side=tk.LEFT, padx=4)

        # ── Tab bar ──
        tab_bar = tk.Frame(self.parent, bg=self.colors["secondary"], pady=0)
        tab_bar.pack(fill=tk.X)

        for label, _ in self.TABS:
            btn = tk.Button(
                tab_bar,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg=self.colors["secondary"],
                fg=self.colors["text_dim"],
                relief=tk.FLAT,
                cursor="hand2",
                padx=18, pady=8,
                command=lambda l=label: self._switch_tab(l),
            )
            btn.pack(side=tk.LEFT)
            self._tab_btns[label] = btn

        # ── Content area ──
        self._content = tk.Frame(self.parent, bg=self.colors["background"])
        self._content.pack(fill=tk.BOTH, expand=True)

        # Pre-build all tab frames (lazy-init the tab classes)
        for label, TabClass in self.TABS:
            frame = tk.Frame(self._content, bg=self.colors["background"])
            self._tab_frames[label] = frame

        # Show first tab
        first_label = self.TABS[0][0]
        self._switch_tab(first_label)

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, label: str):
        # Hide all
        for frame in self._tab_frames.values():
            frame.pack_forget()

        # Style buttons
        for lbl, btn in self._tab_btns.items():
            if lbl == label:
                btn.config(
                    bg=self.colors["primary"],
                    fg="white",
                    relief=tk.FLAT,
                )
            else:
                btn.config(
                    bg=self.colors["secondary"],
                    fg=self.colors["text_dim"],
                    relief=tk.FLAT,
                )

        # Show selected tab frame
        frame = self._tab_frames[label]
        frame.pack(fill=tk.BOTH, expand=True)

        # Lazy-init the tab class on first visit
        if label not in self._tab_instances:
            TabClass = dict(self.TABS)[label]
            try:
                kwargs = {}
                if TabClass in (GearTab, StaticTab):
                    kwargs["on_crafting_saved"] = self._on_crafting_saved
                self._tab_instances[label] = TabClass(frame, self.colors, **kwargs)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                tk.Label(
                    frame,
                    text=f"⚠️  Failed to load {label}\n\n{exc}",
                    font=("Segoe UI", 11),
                    bg=self.colors["background"],
                    fg=self.colors["danger"],
                    justify=tk.CENTER,
                ).pack(expand=True)

        self._active_tab = label

    def _on_crafting_saved(self):
        """Called by GearTab after saving to the crafting data file — reload the CraftingTab."""
        crafting_label = "🔨  Crafting"
        instance = self._tab_instances.get(crafting_label)
        if instance and hasattr(instance, "reload"):
            instance.reload()
