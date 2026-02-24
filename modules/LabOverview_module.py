"""
Lab Overview Module — Thunderz Assistant
=========================================
At-a-glance homelab dashboard with:
  • Stat cards        — total hosts / online / offline / stacks deployed / runs 24h
  • Service health    — live dots + latency + 24h uptime % (via HealthService observer)
  • Docker stacks     — name + deployment status
  • Recent runs       — last 6 script executions with pass/fail indicator
"""

import tkinter as tk
from tkinter import ttk
import datetime
import sys
import os

import database_manager as db

try:
    from health_service import (
        get_health_status,
        trigger_health_poll,
        register_health_observer,
        unregister_health_observer,
    )
    _HEALTH_OK = True
except ImportError:
    _HEALTH_OK = False


class LabOverviewModule:
    ICON = "🏠"
    PRIORITY = 5   # After Dashboard (1), before other modules

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self._observer_registered = False
        self._destroyed = False

        self._build_ui()
        self._refresh_all()

        # Live updates from the background health service
        if _HEALTH_OK:
            register_health_observer(self._on_health_update)
            self._observer_registered = True

        # Unregister observer when this frame is torn down
        self.parent.bind("<Destroy>", self._on_destroy, add="+")

    # ─────────────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        C = self.colors

        # ── Header ─────────────────────────────────────────────────────────────
        hdr = tk.Frame(self.parent, bg=C['secondary'], pady=14, padx=20)
        hdr.pack(fill=tk.X)

        tk.Label(hdr, text="🏠  Lab Overview",
                 font=("Segoe UI", 18, "bold"),
                 bg=C['secondary'], fg=C['text']).pack(side=tk.LEFT)

        right_hdr = tk.Frame(hdr, bg=C['secondary'])
        right_hdr.pack(side=tk.RIGHT)

        self._lbl_updated = tk.Label(
            right_hdr, text="Not polled yet",
            font=("Segoe UI", 9),
            bg=C['secondary'], fg=C['text_dim'])
        self._lbl_updated.pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(right_hdr, text="⟳  Refresh Now",
                  command=self._on_refresh_click,
                  bg=C['accent'], fg=C['text'],
                  font=("Segoe UI", 9), relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2").pack(side=tk.LEFT)

        # ── Stat Cards Row ──────────────────────────────────────────────────────
        cards_wrap = tk.Frame(self.parent, bg=C['background'])
        cards_wrap.pack(fill=tk.X, padx=16, pady=(12, 6))

        stat_defs = [
            ("total",   "🖥️  Total Hosts", C['text']),
            ("online",  "✅  Online",       C['success']),
            ("offline", "❌  Offline",      C['danger']),
            ("stacks",  "🐳  Deployed",     C['accent']),
            ("scripts", "📜  Runs (24h)",   C['warning']),
        ]
        self._stat_vars: dict = {}
        for col, (key, label, val_color) in enumerate(stat_defs):
            cards_wrap.columnconfigure(col, weight=1)
            card = tk.Frame(cards_wrap, bg=C['card_bg'], padx=12, pady=10)
            card.grid(row=0, column=col, sticky="ew", padx=4)
            sv = tk.StringVar(value="—")
            self._stat_vars[key] = sv
            tk.Label(card, textvariable=sv,
                     font=("Segoe UI", 24, "bold"),
                     bg=C['card_bg'], fg=val_color).pack()
            tk.Label(card, text=label,
                     font=("Segoe UI", 9),
                     bg=C['card_bg'], fg=C['text_dim']).pack()

        # ── Main Body (two columns) ─────────────────────────────────────────────
        body = tk.Frame(self.parent, bg=C['background'])
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # ─── Left: Service Health ───────────────────────────────────────────────
        left_card = tk.Frame(body, bg=C['card_bg'])
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_card.rowconfigure(1, weight=1)
        left_card.columnconfigure(0, weight=1)

        lhdr = tk.Frame(left_card, bg=C['secondary'])
        lhdr.grid(row=0, column=0, sticky="ew")
        tk.Label(lhdr, text="🌐  Service Health",
                 font=("Segoe UI", 11, "bold"),
                 bg=C['secondary'], fg=C['text'],
                 pady=8, padx=12).pack(side=tk.LEFT)

        # Scrollable canvas for health rows
        health_wrap = tk.Frame(left_card, bg=C['card_bg'])
        health_wrap.grid(row=1, column=0, sticky="nsew")
        health_wrap.rowconfigure(0, weight=1)
        health_wrap.columnconfigure(0, weight=1)

        self._health_canvas = tk.Canvas(
            health_wrap, bg=C['card_bg'], highlightthickness=0)
        health_vsb = ttk.Scrollbar(
            health_wrap, orient="vertical",
            command=self._health_canvas.yview)
        self._health_canvas.configure(yscrollcommand=health_vsb.set)
        self._health_canvas.grid(row=0, column=0, sticky="nsew")
        health_vsb.grid(row=0, column=1, sticky="ns")

        self._health_inner = tk.Frame(self._health_canvas, bg=C['card_bg'])
        self._health_cw = self._health_canvas.create_window(
            (0, 0), window=self._health_inner, anchor="nw")

        self._health_inner.bind("<Configure>", self._on_health_inner_cfg)
        self._health_canvas.bind("<Configure>", self._on_health_canvas_cfg)

        # ─── Right: Stacks + Runs ───────────────────────────────────────────────
        right_col = tk.Frame(body, bg=C['background'])
        right_col.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_col.columnconfigure(0, weight=1)
        right_col.rowconfigure(0, weight=1)
        right_col.rowconfigure(1, weight=1)

        # Docker Stacks card
        stacks_card = tk.Frame(right_col, bg=C['card_bg'])
        stacks_card.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        stacks_card.columnconfigure(0, weight=1)
        stacks_card.rowconfigure(1, weight=1)

        shdr = tk.Frame(stacks_card, bg=C['secondary'])
        shdr.grid(row=0, column=0, sticky="ew")
        tk.Label(shdr, text="🐳  Docker Stacks",
                 font=("Segoe UI", 11, "bold"),
                 bg=C['secondary'], fg=C['text'],
                 pady=8, padx=12).pack(side=tk.LEFT)

        self._stacks_body = tk.Frame(stacks_card, bg=C['card_bg'])
        self._stacks_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)

        # Recent Runs card
        runs_card = tk.Frame(right_col, bg=C['card_bg'])
        runs_card.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        runs_card.columnconfigure(0, weight=1)
        runs_card.rowconfigure(1, weight=1)

        rhdr = tk.Frame(runs_card, bg=C['secondary'])
        rhdr.grid(row=0, column=0, sticky="ew")
        tk.Label(rhdr, text="📜  Recent Runs",
                 font=("Segoe UI", 11, "bold"),
                 bg=C['secondary'], fg=C['text'],
                 pady=8, padx=12).pack(side=tk.LEFT)

        self._runs_body = tk.Frame(runs_card, bg=C['card_bg'])
        self._runs_body.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)

    # ─────────────────────────────────────────────────────────────────────────
    # Canvas / scroll helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _on_health_inner_cfg(self, event=None):
        try:
            self._health_canvas.configure(
                scrollregion=self._health_canvas.bbox("all"))
        except Exception:
            pass

    def _on_health_canvas_cfg(self, event):
        try:
            self._health_canvas.itemconfig(self._health_cw, width=event.width)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Refresh entry points
    # ─────────────────────────────────────────────────────────────────────────

    def _on_refresh_click(self):
        if _HEALTH_OK:
            trigger_health_poll()   # observer will call _refresh_all when done
        else:
            self._refresh_all()

    def _on_health_update(self):
        """Called by HealthService on the main thread after each poll cycle."""
        if self._destroyed:
            return
        try:
            if not self.parent.winfo_exists():
                return
        except Exception:
            return
        self._refresh_all()

    def _refresh_all(self):
        self._refresh_stat_cards()
        self._refresh_health_panel()
        self._refresh_stacks_panel()
        self._refresh_runs_panel()

    # ─────────────────────────────────────────────────────────────────────────
    # Stat Cards
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_stat_cards(self):
        try:
            # Total hosts in IPAM
            rows = db.execute_query("SELECT COUNT(*) FROM ip_allocations") or [(0,)]
            self._stat_vars["total"].set(str(rows[0][0]))

            # Online / offline from live health snapshot
            if _HEALTH_OK:
                snap = get_health_status()
                self._stat_vars["online"].set(
                    str(sum(1 for s in snap.values() if s.online)))
                self._stat_vars["offline"].set(
                    str(sum(1 for s in snap.values() if not s.online)))
            else:
                self._stat_vars["online"].set("—")
                self._stat_vars["offline"].set("—")

            # Deployed stacks
            rows = db.execute_query(
                "SELECT COUNT(*) FROM docker_stacks "
                "WHERE status='Deployed'") or [(0,)]
            self._stat_vars["stacks"].set(str(rows[0][0]))

            # Script runs in last 24 h
            rows = db.execute_query(
                "SELECT COUNT(*) FROM script_execution_log "
                "WHERE started_at >= datetime('now','-1 day')") or [(0,)]
            self._stat_vars["scripts"].set(str(rows[0][0]))

            # Timestamp
            self._lbl_updated.config(
                text=f"Updated: {datetime.datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"[LabOverview] stat cards error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Service Health Panel
    # ─────────────────────────────────────────────────────────────────────────

    def _uptime_pct(self, ip: str, port: str):
        """Return (label, color) for 24-hour uptime percentage."""
        C = self.colors
        try:
            rows = db.execute_query(
                "SELECT online FROM service_health_log "
                "WHERE ip_address=? AND port=? "
                "AND checked_at >= datetime('now','-1 day')",
                (ip, port))
            if not rows:
                return "N/A", C['text_dim']
            pct = round(sum(r[0] for r in rows) / len(rows) * 100)
            color = (C['success'] if pct >= 90
                     else C['warning'] if pct >= 70
                     else C['danger'])
            return f"{pct}%", color
        except Exception:
            return "N/A", C['text_dim']

    def _refresh_health_panel(self):
        C = self.colors
        try:
            for w in self._health_inner.winfo_children():
                w.destroy()

            ipam = db.execute_query(
                "SELECT ip_address, hostname, port FROM ip_allocations "
                "ORDER BY ip_address, CAST(port AS INTEGER)") or []

            snap = get_health_status() if _HEALTH_OK else {}

            if not ipam:
                tk.Label(self._health_inner,
                         text="No hosts in IPAM yet.",
                         font=("Segoe UI", 10),
                         bg=C['card_bg'], fg=C['text_dim']).pack(pady=20)
                return

            # Column header
            col_hdr = tk.Frame(self._health_inner, bg=C['secondary'])
            col_hdr.pack(fill=tk.X)
            for txt, w in [("  ", 2), ("Service", 18), ("Address", 17),
                           ("Latency", 7), ("24h Up", 6)]:
                tk.Label(col_hdr, text=txt, width=w,
                         font=("Segoe UI", 8, "bold"),
                         bg=C['secondary'], fg=C['text_dim'],
                         anchor="w", padx=4).pack(side=tk.LEFT)

            # Data rows
            for ip, hostname, port in ipam:
                key = f"{ip}:{port}" if port else ip
                svc = snap.get(key)
                online = svc.online if svc else None
                latency = svc.latency_ms if svc else None

                dot_fg = (C['success'] if online is True
                          else C['danger'] if online is False
                          else C['text_dim'])

                row = tk.Frame(self._health_inner, bg=C['card_bg'])
                row.pack(fill=tk.X, pady=1, padx=2)

                tk.Label(row, text="●", font=("Segoe UI", 10),
                         bg=C['card_bg'], fg=dot_fg,
                         width=2).pack(side=tk.LEFT, padx=(6, 2))

                port_sfx = f":{port}" if port else ""
                name = hostname or ip
                name_str = f"{name}{port_sfx}"
                if len(name_str) > 18:
                    name_str = name_str[:17] + "…"
                tk.Label(row, text=name_str,
                         font=("Segoe UI", 9), bg=C['card_bg'],
                         fg=C['text'], anchor="w", width=18).pack(
                             side=tk.LEFT, padx=(2, 4))

                addr_str = f"{ip}{port_sfx}"
                tk.Label(row, text=addr_str,
                         font=("Segoe UI", 9), bg=C['card_bg'],
                         fg=C['text_dim'], anchor="w", width=17).pack(
                             side=tk.LEFT, padx=4)

                lat_str = f"{latency}ms" if latency is not None else "—"
                tk.Label(row, text=lat_str,
                         font=("Segoe UI", 9), bg=C['card_bg'],
                         fg=C['text_dim'], anchor="e", width=7).pack(
                             side=tk.LEFT, padx=4)

                up_txt, up_color = self._uptime_pct(ip, port or "")
                tk.Label(row, text=up_txt,
                         font=("Segoe UI", 9, "bold"),
                         bg=C['card_bg'], fg=up_color,
                         anchor="e", width=6).pack(side=tk.LEFT, padx=(4, 8))

        except Exception as e:
            print(f"[LabOverview] health panel error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Docker Stacks Panel
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_stacks_panel(self):
        C = self.colors
        try:
            for w in self._stacks_body.winfo_children():
                w.destroy()

            stacks = db.execute_query(
                "SELECT name, status FROM docker_stacks ORDER BY name") or []

            if not stacks:
                tk.Label(self._stacks_body, text="No stacks saved.",
                         font=("Segoe UI", 9),
                         bg=C['card_bg'], fg=C['text_dim']).pack()
                return

            for name, status in stacks[:10]:
                row = tk.Frame(self._stacks_body, bg=C['card_bg'])
                row.pack(fill=tk.X, pady=2)

                dot_fg = (C['success'] if status == "Deployed"
                          else C['warning'] if status == "Stopped"
                          else C['text_dim'])
                tk.Label(row, text="●", font=("Segoe UI", 9),
                         bg=C['card_bg'], fg=dot_fg).pack(side=tk.LEFT)

                n = name if len(name) <= 20 else name[:19] + "…"
                tk.Label(row, text=n,
                         font=("Segoe UI", 9), bg=C['card_bg'],
                         fg=C['text'], anchor="w").pack(
                             side=tk.LEFT, padx=(4, 0),
                             expand=True, fill=tk.X)

                tk.Label(row, text=status,
                         font=("Segoe UI", 8),
                         bg=C['card_bg'], fg=dot_fg).pack(side=tk.RIGHT)

        except Exception as e:
            print(f"[LabOverview] stacks panel error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Recent Script Runs Panel
    # ─────────────────────────────────────────────────────────────────────────

    def _refresh_runs_panel(self):
        C = self.colors
        try:
            for w in self._runs_body.winfo_children():
                w.destroy()

            runs = db.execute_query(
                "SELECT script_title, hostname, exit_code, started_at "
                "FROM script_execution_log "
                "ORDER BY started_at DESC LIMIT 6") or []

            if not runs:
                tk.Label(self._runs_body, text="No script runs yet.",
                         font=("Segoe UI", 9),
                         bg=C['card_bg'], fg=C['text_dim']).pack()
                return

            for title, host, exit_code, started_at in runs:
                row = tk.Frame(self._runs_body, bg=C['card_bg'])
                row.pack(fill=tk.X, pady=2)

                ok = (exit_code == 0)
                icon = "✅" if ok else "❌"
                tk.Label(row, text=icon,
                         font=("Segoe UI", 9),
                         bg=C['card_bg']).pack(side=tk.LEFT)

                t = (title or "—")
                if len(t) > 20:
                    t = t[:19] + "…"
                tk.Label(row, text=t,
                         font=("Segoe UI", 9), bg=C['card_bg'],
                         fg=C['text'], anchor="w").pack(
                             side=tk.LEFT, padx=(4, 0),
                             expand=True, fill=tk.X)

                # Show time portion of ISO timestamp
                ts = ""
                if started_at:
                    ts = started_at.replace("T", " ").split(" ")[-1][:8]
                tk.Label(row, text=ts,
                         font=("Segoe UI", 8),
                         bg=C['card_bg'], fg=C['text_dim']).pack(side=tk.RIGHT)

        except Exception as e:
            print(f"[LabOverview] runs panel error: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Cleanup
    # ─────────────────────────────────────────────────────────────────────────

    def _on_destroy(self, event=None):
        """Unregister health observer when this module's frame is destroyed."""
        if event and getattr(event, 'widget', None) is not self.parent:
            return
        self._destroyed = True
        if self._observer_registered and _HEALTH_OK:
            try:
                unregister_health_observer(self._on_health_update)
            except Exception:
                pass
            self._observer_registered = False
