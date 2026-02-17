"""
Thunderz Assistant - Enhanced UI Version (v1.12.4 Smart Loader)
---------------------------------------------------------------
• FIXED: News Module error (Auto-detects if module needs API Key).
• FIXED: "Invalid command name" spam (Improved widget cleanup).
• CORE: Dynamic Sidebar, Red Internal Modules, Global Error Handler.
• NEW: Ctrl+K Command Palette, Theming, Sidebar Search, Focus Mode.
"""

import tkinter as tk
from tkinter import ttk, messagebox, Menu
import sys
import os
import json
import webbrowser
import config
import importlib.util
import inspect
import traceback

APP_VERSION = "1.12.4"

# ── Built-in Themes ────────────────────────────────────────────────────────────
THEMES = {
    "Dark Blue": {
        'primary': '#1E40AF', 'secondary': '#1E293B', 'accent': '#3B82F6',
        'background': '#0F172A', 'content_bg': '#1E293B', 'card_bg': '#334155',
        'text': '#E2E8F0', 'text_dim': '#94A3B8', 'button_hover': '#2563EB',
        'success': '#10B981', 'warning': '#F59E0B', 'danger': '#EF4444',
        'internal': '#FF5252'
    },
    "OLED Black": {
        'primary': '#3730A3', 'secondary': '#0A0A0A', 'accent': '#6366F1',
        'background': '#000000', 'content_bg': '#0D0D0D', 'card_bg': '#1A1A1A',
        'text': '#F1F5F9', 'text_dim': '#64748B', 'button_hover': '#4F46E5',
        'success': '#10B981', 'warning': '#F59E0B', 'danger': '#EF4444',
        'internal': '#FF5252'
    },
    "Slate": {
        'primary': '#475569', 'secondary': '#1E293B', 'accent': '#A78BFA',
        'background': '#1C1C2E', 'content_bg': '#252540', 'card_bg': '#2E2E4E',
        'text': '#E2E8F0', 'text_dim': '#94A3B8', 'button_hover': '#8B5CF6',
        'success': '#34D399', 'warning': '#FCD34D', 'danger': '#F87171',
        'internal': '#FB7185'
    },
}

# Add modules directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Core Imports
from discord_presence_module import set_presence
from notification_manager import get_unread_count, register_observer
from tray_manager import TrayManager

class ToolTip:
    """Tooltip class for showing help text on hover"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#1E293B", foreground="#E2E8F0",
                        relief='solid', borderwidth=1,
                        font=("Segoe UI", 9), padx=8, pady=4)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class ThunderzAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title(f"⚡ Thunderz Assistant v{APP_VERSION}")

        # INCREASED SIZE
        self.root.geometry("1280x900")
        self.root.minsize(1100, 750)

        # 1. GLOBAL ERROR HANDLER
        self.root.report_callback_exception = self.handle_crash

        icon_path = os.path.join(os.path.dirname(__file__), 'thunderz_icon.ico')
        if os.path.exists(icon_path):
            try: self.root.iconbitmap(icon_path)
            except: pass

        self.api_key = config.NEWS_API_KEY if config.NEWS_API_KEY != "YOUR_API_KEY_HERE" else None
        self.settings_file = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')
        self._focus_mode = False
        self._sidebar_container = None  # set in create_ui, used by focus mode
        self._menu_bar_visible = True

        # Load persisted settings (theme, etc.)
        self._settings = self._load_settings()
        theme_name = self._settings.get('theme', 'Dark Blue')
        self.colors = dict(THEMES.get(theme_name, THEMES['Dark Blue']))

        self.root.configure(bg=self.colors['background'])
        self.current_module_data = None
        self.module_buttons = {}
        self._sidebar_btn_containers = {}  # name → btn_container, for sidebar search
        self.notification_badge = None

        # Load Modules ONCE
        self.loaded_modules_list = self.discover_modules()

        self.create_menu_bar()
        self.create_ui()
        self.create_status_bar()

        # New keybindings
        self.root.bind("<Control-k>", lambda e: self.open_command_palette())
        self.root.bind("<F11>", lambda e: self.toggle_focus_mode())

        # Default load
        if self.loaded_modules_list:
            default = next((m for m in self.loaded_modules_list if m['name'] == "Dashboard"), self.loaded_modules_list[0])
            self.switch_module(default)

        try:
            self.tray_manager = TrayManager(self.root)
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        except:
            self.root.protocol("WM_DELETE_WINDOW", self.root.quit)

    def handle_crash(self, exc, val, tb):
        """Global handler that ignores Zombie Widget errors"""
        error_text = str(val)
        
        # SILENCE ZOMBIE ERRORS
        if "invalid command name" in error_text: return 
        if "yview_scroll" in error_text: return 
            
        # For real errors, print to console and show popup
        err_msg = "".join(traceback.format_exception(exc, val, tb))
        print(err_msg)
        messagebox.showerror("Application Error", f"An error occurred:\n\n{val}")

    def discover_modules(self):
        """Scans folders and flags internal modules"""
        discovered = []
        module_dirs = [os.path.join(os.path.dirname(__file__), 'modules')]
        
        if any(flag in sys.argv for flag in ["--internal", "-i"]):
            module_dirs.append(os.path.join(os.path.dirname(__file__), 'internal_modules'))

        for m_dir in module_dirs:
            if not os.path.exists(m_dir): continue
            is_internal_folder = "internal_modules" in m_dir

            for filename in os.listdir(m_dir):
                # ── Standard .py module ──
                if filename.endswith(".py") and filename not in ["__init__.py", "template_module.py"]:
                    module_name = filename[:-3]
                    file_path = os.path.join(m_dir, filename)

                    try:
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        gen_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(gen_module)

                        for name, obj in inspect.getmembers(gen_module):
                            if inspect.isclass(obj) and name.endswith("Module"):
                                if hasattr(obj, "ICON"):
                                    discovered.append({
                                        "class": obj,
                                        "name": name.replace("Module", ""),
                                        "icon": obj.ICON,
                                        "priority": getattr(obj, "PRIORITY", 99),
                                        "is_internal": is_internal_folder
                                    })
                    except Exception as e:
                        print(f"⚠️ Could not load {filename}: {e}")

                # ── Sub-package directory (e.g. modules/ff14/) ──
                elif (
                    os.path.isdir(os.path.join(m_dir, filename))
                    and os.path.exists(os.path.join(m_dir, filename, "__init__.py"))
                ):
                    pkg_dir  = os.path.join(m_dir, filename)
                    pkg_name = filename
                    try:
                        spec = importlib.util.spec_from_file_location(
                            pkg_name,
                            os.path.join(pkg_dir, "__init__.py"),
                            submodule_search_locations=[pkg_dir],
                        )
                        gen_module = importlib.util.module_from_spec(spec)
                        sys.modules[pkg_name] = gen_module
                        spec.loader.exec_module(gen_module)

                        for name, obj in inspect.getmembers(gen_module):
                            if inspect.isclass(obj) and name.endswith("Module"):
                                if hasattr(obj, "ICON"):
                                    discovered.append({
                                        "class": obj,
                                        "name": name.replace("Module", ""),
                                        "icon": obj.ICON,
                                        "priority": getattr(obj, "PRIORITY", 99),
                                        "is_internal": is_internal_folder
                                    })
                    except Exception as e:
                        print(f"⚠️ Could not load package {pkg_name}: {e}")
        
        discovered.sort(key=lambda x: x['priority'])
        return discovered
    
    def on_window_close(self):
        if self.tray_manager: self.tray_manager.hide_window()
        else: self.root.quit()
    
    def create_menu_bar(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self.refresh_current_module, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        for idx, mod in enumerate(self.loaded_modules_list):
            accel = f"Ctrl+{idx+1}" if idx < 9 else None
            view_menu.add_command(
                label=mod['name'], 
                command=lambda m=mod: self.switch_module(m),
                accelerator=accel
            )
            if accel:
                self.root.bind(f"<Control-{idx+1}>", lambda e, m=mod: self.switch_module(m))

        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Start Guide", command=self.show_quick_start)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        self.root.bind("<F5>", lambda e: self.refresh_current_module())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
    
    def create_ui(self):
        self._main_container = tk.Frame(self.root, bg=self.colors['background'])
        self._main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Sidebar
        sidebar_container = tk.Frame(self._main_container, bg=self.colors['secondary'], width=240)
        sidebar_container.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 10))
        sidebar_container.pack_propagate(False)
        self._sidebar_container = sidebar_container  # store for focus mode

        sidebar_header = tk.Frame(sidebar_container, bg=self.colors['primary'])
        sidebar_header.pack(fill=tk.X)
        tk.Label(sidebar_header, text="⚡ Modules", font=("Segoe UI", 16, "bold"),
                 bg=self.colors['primary'], fg="white", pady=15).pack()

        # ── Sidebar search box ─────────────────────────────────────────────────
        search_frame = tk.Frame(sidebar_container, bg=self.colors['secondary'], pady=4)
        search_frame.pack(fill=tk.X, padx=8)
        self._sidebar_search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self._sidebar_search_var,
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT,
            bd=4
        )
        search_entry.pack(fill=tk.X)
        search_entry.insert(0, "🔍 Filter modules...")
        search_entry.bind("<FocusIn>",  lambda e: (search_entry.delete(0, tk.END) if search_entry.get() == "🔍 Filter modules..." else None))
        search_entry.bind("<FocusOut>", lambda e: (search_entry.insert(0, "🔍 Filter modules...") if not search_entry.get() else None))
        self._sidebar_search_var.trace_add("write", lambda *_: self._filter_sidebar())

        # Scrollable Area
        canvas = tk.Canvas(sidebar_container, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(sidebar_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['secondary'])

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=220)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _safe_scroll(event):
            try: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except: pass
        canvas.bind_all("<MouseWheel>", _safe_scroll)

        # Generate Buttons
        for mod_data in self.loaded_modules_list:
            name = mod_data["name"]
            icon = mod_data["icon"]
            is_internal = mod_data.get("is_internal", False)

            btn_container = tk.Frame(scrollable_frame, bg=self.colors['secondary'])
            btn_container.pack(fill=tk.X, padx=10, pady=3)
            self._sidebar_btn_containers[name] = btn_container  # for search filtering

            text_color = self.colors['internal'] if is_internal else self.colors['text']

            btn = tk.Button(
                btn_container,
                text=f"{icon}  {name}",
                font=("Segoe UI", 11),
                bg=self.colors['card_bg'],
                fg=text_color,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda m=mod_data: self.switch_module(m),
                anchor="w",
                padx=15,
                pady=10
            )
            btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.module_buttons[name] = btn

            if name == "Notifications":
                self.notification_badge_frame = btn_container
                self.update_notification_badge()

        register_observer(self.update_notification_badge)

        # ── Bottom help bar ────────────────────────────────────────────────────
        help_frame = tk.Frame(sidebar_container, bg=self.colors['secondary'])
        help_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=4)
        tk.Button(help_frame, text="🎨 Theme", command=self.open_theme_picker,
                  bg=self.colors['card_bg'], fg=self.colors['text'], relief=tk.FLAT).pack(fill=tk.X, padx=10, pady=(0, 3))
        tk.Button(help_frame, text="❓ Help", command=self.show_quick_start,
                  bg=self.colors['accent'], fg="white", relief=tk.FLAT).pack(fill=tk.X, padx=10)

        self.content_frame = tk.Frame(self._main_container, bg=self.colors['content_bg'], relief=tk.RAISED, borderwidth=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
    
    def create_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg=self.colors['secondary'], height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_module_label = tk.Label(self.status_bar, text="", font=("Segoe UI", 9), 
                                          bg=self.colors['secondary'], fg=self.colors['text'], anchor="w", padx=10)
        self.status_module_label.pack(side=tk.LEFT)
        tk.Label(self.status_bar, text="v1.12.4", font=("Segoe UI", 9), 
                bg=self.colors['secondary'], fg=self.colors['text_dim'], anchor="e", padx=10).pack(side=tk.RIGHT)
    
    def switch_module(self, module_data):
        """Universal switcher with Smart Dependency Injection"""
        name = module_data['name']
        module_class = module_data['class']
        self.current_module_data = module_data 
        
        # 1. Unbind global scroll
        try: self.root.unbind_all("<MouseWheel>")
        except: pass

        # Update Visuals
        for btn_name, btn in self.module_buttons.items():
            if btn_name == name:
                btn.config(bg=self.colors['accent'], fg="white")
            else:
                mod_info = next((m for m in self.loaded_modules_list if m['name'] == btn_name), None)
                color = self.colors['internal'] if mod_info and mod_info.get('is_internal') else self.colors['text']
                btn.config(bg=self.colors['card_bg'], fg=color)

        self.status_module_label.config(text=f"📍 {name}")
        
        # 2. Cleanup Old Module (Prevent Zombie Errors)
        for widget in self.content_frame.winfo_children(): 
            try: widget.destroy()
            except: pass
        
        try:
            # 3. SMART LOADER: Inspect __init__ to see if it needs api_key
            sig = inspect.signature(module_class.__init__)
            params = sig.parameters

            if 'api_key' in params:
                # Inject API key if requested
                module_class(self.api_key, self.content_frame, self.colors)
            else:
                # Standard Load
                module_class(self.content_frame, self.colors)

            # Discord Presence
            try: set_presence(name, f"Using {name}")
            except Exception: pass

        except Exception as e:
            # Show a friendly error card instead of a messagebox crash
            traceback.print_exc()
            err_frame = tk.Frame(self.content_frame, bg=self.colors['background'])
            err_frame.pack(fill=tk.BOTH, expand=True)
            tk.Label(
                err_frame,
                text=f"⚠️  {name} failed to load",
                font=("Segoe UI", 18, "bold"),
                bg=self.colors['background'],
                fg=self.colors['danger']
            ).pack(pady=(80, 10))
            tk.Label(
                err_frame,
                text=f"{type(e).__name__}: {str(e)[:120]}",
                font=("Segoe UI", 11),
                bg=self.colors['background'],
                fg=self.colors['text_dim'],
                wraplength=600
            ).pack(pady=(0, 6))
            tk.Label(
                err_frame,
                text="See the console / terminal for the full traceback.",
                font=("Segoe UI", 10),
                bg=self.colors['background'],
                fg=self.colors['text_dim']
            ).pack()
    
    def refresh_current_module(self):
        if self.current_module_data:
            self.switch_module(self.current_module_data)

    def update_notification_badge(self):
        try:
            unread = get_unread_count()
            if hasattr(self, 'notification_badge_frame'):
                for w in self.notification_badge_frame.winfo_children():
                    if isinstance(w, tk.Label) and w != self.module_buttons.get("Notifications"):
                        w.destroy()
                if unread > 0:
                    tk.Label(self.notification_badge_frame, text=str(unread) if unread < 100 else "99+",
                            font=("Segoe UI", 9, "bold"), bg=self.colors['danger'], fg="white", padx=6).pack(side=tk.RIGHT, padx=5)
        except: pass
    
    # ── Settings persistence ───────────────────────────────────────────────────
    def _load_settings(self) -> dict:
        path = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_settings(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    # ── Theming ────────────────────────────────────────────────────────────────
    def open_theme_picker(self):
        """Show a small theme-selector popup."""
        win = tk.Toplevel(self.root)
        win.title("Choose Theme")
        win.resizable(False, False)
        win.configure(bg=self.colors['background'])
        win.geometry("280x200")
        win.grab_set()

        tk.Label(win, text="🎨  Choose Theme", font=("Segoe UI", 13, "bold"),
                 bg=self.colors['background'], fg=self.colors['text']).pack(pady=(18, 10))

        current = self._settings.get('theme', 'Dark Blue')
        var = tk.StringVar(value=current)

        for name in THEMES:
            tk.Radiobutton(
                win, text=name, variable=var, value=name,
                font=("Segoe UI", 11),
                bg=self.colors['background'], fg=self.colors['text'],
                selectcolor=self.colors['card_bg'],
                activebackground=self.colors['background'],
                activeforeground=self.colors['accent']
            ).pack(anchor="w", padx=30)

        def apply():
            chosen = var.get()
            self._settings['theme'] = chosen
            self._save_settings()
            self.colors.update(THEMES[chosen])
            # Rebuild entire UI with new colors
            for widget in self.root.winfo_children():
                try: widget.destroy()
                except: pass
            self.module_buttons = {}
            self._sidebar_btn_containers = {}
            self.create_menu_bar()
            self.create_ui()
            self.create_status_bar()
            self.root.bind("<Control-k>", lambda e: self.open_command_palette())
            self.root.bind("<F11>", lambda e: self.toggle_focus_mode())
            if self.current_module_data:
                self.switch_module(self.current_module_data)
            win.destroy()

        tk.Button(win, text="Apply", command=apply,
                  bg=self.colors['accent'], fg="white",
                  font=("Segoe UI", 11, "bold"), relief=tk.FLAT).pack(pady=12)

    # ── Sidebar search ─────────────────────────────────────────────────────────
    def _filter_sidebar(self):
        query = self._sidebar_search_var.get().strip().lower()
        if query in ("", "🔍 filter modules..."):
            for container in self._sidebar_btn_containers.values():
                try: container.pack(fill=tk.X, padx=10, pady=3)
                except: pass
            return
        for name, container in self._sidebar_btn_containers.items():
            try:
                if query in name.lower():
                    container.pack(fill=tk.X, padx=10, pady=3)
                else:
                    container.pack_forget()
            except:
                pass

    # ── Ctrl+K Command Palette ─────────────────────────────────────────────────
    def open_command_palette(self):
        """Pop up the Ctrl+K command palette."""
        win = tk.Toplevel(self.root)
        win.title("")
        win.overrideredirect(True)
        win.configure(bg=self.colors['card_bg'])
        win.attributes("-topmost", True)

        # Centre over root
        w, h = 520, 380
        rx = self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2
        ry = self.root.winfo_rooty() + 120
        win.geometry(f"{w}x{h}+{rx}+{ry}")

        # Border effect
        outer = tk.Frame(win, bg=self.colors['accent'], bd=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Search bar
        entry_frame = tk.Frame(outer, bg=self.colors['card_bg'])
        entry_frame.pack(fill=tk.X, padx=12, pady=(12, 6))
        tk.Label(entry_frame, text="🔍", font=("Segoe UI", 14),
                 bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(side=tk.LEFT)
        search_var = tk.StringVar()
        entry = tk.Entry(entry_frame, textvariable=search_var,
                         font=("Segoe UI", 13), bg=self.colors['card_bg'],
                         fg=self.colors['text'], insertbackground=self.colors['text'],
                         relief=tk.FLAT, bd=6)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.focus_set()

        # Results list
        results_frame = tk.Frame(outer, bg=self.colors['background'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        result_buttons = []

        def clear_results():
            for w in results_frame.winfo_children():
                try: w.destroy()
                except: pass
            result_buttons.clear()

        def build_results(*_):
            clear_results()
            q = search_var.get().strip().lower()

            rows = []
            # Modules
            for mod in self.loaded_modules_list:
                if not q or q in mod['name'].lower():
                    rows.append(("⚡ Module", mod['name'], lambda m=mod: (self.switch_module(m), win.destroy())))
            # Notes
            try:
                notes_path = os.path.join(os.path.dirname(__file__), 'data', 'notes.json')
                if os.path.exists(notes_path):
                    with open(notes_path, 'r') as f:
                        notes_data = json.load(f)
                    for note in notes_data.get('notes', []):
                        title = note.get('title', 'Untitled')
                        content = note.get('content', '')
                        if not q or q in title.lower() or q in content.lower():
                            rows.append(("📝 Note", title, None))
                            if len(rows) >= 12:
                                break
            except Exception:
                pass
            # Stocks
            try:
                stocks_path = os.path.join(os.path.dirname(__file__), 'data', 'stock_watchlist.json')
                if os.path.exists(stocks_path):
                    with open(stocks_path, 'r') as f:
                        stock_data = json.load(f)
                    for ticker in stock_data:
                        if not q or q in ticker.lower():
                            price = stock_data[ticker].get('price')
                            label = f"{ticker}  ${price:.2f}" if price else ticker
                            rows.append(("📈 Stock", label, None))
            except Exception:
                pass

            if not rows:
                tk.Label(results_frame, text="No results found",
                         font=("Segoe UI", 11), bg=self.colors['background'],
                         fg=self.colors['text_dim']).pack(pady=20)
                return

            for kind, label, action in rows[:10]:
                row = tk.Frame(results_frame, bg=self.colors['background'], cursor="hand2")
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=kind, font=("Segoe UI", 9),
                         bg=self.colors['background'], fg=self.colors['text_dim'],
                         width=10, anchor="e").pack(side=tk.LEFT, padx=(6, 4))
                lbl = tk.Label(row, text=label, font=("Segoe UI", 11),
                               bg=self.colors['background'], fg=self.colors['text'], anchor="w")
                lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, pady=5)
                result_buttons.append(row)
                if action:
                    row.bind("<Button-1>", lambda e, a=action: a())
                    lbl.bind("<Button-1>", lambda e, a=action: a())
                    row.bind("<Enter>", lambda e, r=row: r.configure(bg=self.colors['card_bg']))
                    row.bind("<Leave>", lambda e, r=row: r.configure(bg=self.colors['background']))
                    lbl.bind("<Enter>", lambda e, r=row: r.configure(bg=self.colors['card_bg']))
                    lbl.bind("<Leave>", lambda e, r=row: r.configure(bg=self.colors['background']))

        search_var.trace_add("write", build_results)
        build_results()

        entry.bind("<Escape>", lambda e: win.destroy())
        win.bind("<FocusOut>", lambda e: win.destroy() if win.winfo_exists() else None)

    # ── Focus Mode ─────────────────────────────────────────────────────────────
    def toggle_focus_mode(self):
        """F11 — hide/show sidebar and menu bar for distraction-free view."""
        self._focus_mode = not self._focus_mode
        if self._focus_mode:
            try: self._sidebar_container.pack_forget()
            except: pass
            self.root.config(menu=Menu(self.root))  # hide menu bar (blank menu)
            # Show a small floating exit button
            self._focus_btn = tk.Button(
                self.root, text="✕ Exit Focus  F11",
                command=self.toggle_focus_mode,
                font=("Segoe UI", 9), bg=self.colors['accent'], fg="white",
                relief=tk.FLAT, cursor="hand2"
            )
            self._focus_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-8, y=8)
        else:
            try: self._sidebar_container.pack(fill=tk.Y, side=tk.LEFT, padx=(0, 10), before=self.content_frame)
            except: pass
            try: self._focus_btn.destroy()
            except: pass
            self.create_menu_bar()  # restore menu bar

    def show_quick_start(self):
        messagebox.showinfo("Guide", "Use the sidebar to navigate.\nInternal modules appear in RED.\nHotkeys: Ctrl+1-9, Ctrl+K (search), F11 (focus)")

    def show_shortcuts(self):
        msg = f"F5: Refresh\nCtrl+Q: Quit\nCtrl+K: Command palette\nF11: Focus mode\n\nDynamic Keys:\n"
        for i, m in enumerate(self.loaded_modules_list[:9]):
            msg += f"Ctrl+{i+1}: {m['name']}\n"
        messagebox.showinfo("Shortcuts", msg)

    def show_about(self):
        messagebox.showinfo("About", f"Thunderz Assistant v{APP_VERSION}")

def main():
    root = tk.Tk()
    app = ThunderzAssistant(root)
    root.mainloop()

if __name__ == "__main__":
    main()