"""
Pomodoro Timer Module for Thunderz Assistant
Version: 2.0.0 - Enhanced Edition

Enhanced features:
- Customizable work/break durations
- Daily goal tracking with progress bar
- Task labels for each session
- Detailed session history
- Statistics visualization (matplotlib charts)
- CSV export
- Settings panel
- Discord integration with task labels
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import json
import os
from datetime import datetime, date
import threading
import csv


class PomodoroModule:
    """
    Enhanced Pomodoro Timer - Customizable productivity system with tracking.
    
    Features:
    - Customizable durations (work, short/long breaks)
    - Task labels for focus sessions
    - Daily goal tracking with visual progress
    - Session history with timestamps
    - Statistics charts (last 7/30 days)
    - CSV export
    - Settings panel
    """
    ICON = "🍅"
    PRIORITY = 8

    def __init__(self, parent_frame, colors):
        """
        Initialize the Enhanced Pomodoro timer module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
            colors: Dictionary containing the application's color scheme
        """      

        self.parent = parent_frame
        self.colors = colors
        
        # Load or create stats (with migration from v1)
        self.stats = self.load_stats()
        
        # Get settings (from stats > config > defaults)
        self.settings = self.get_settings(self.stats)
        
        # Timer settings (in seconds)
        self.WORK_TIME = self.settings['work_minutes'] * 60
        self.SHORT_BREAK = self.settings['short_break_minutes'] * 60
        self.LONG_BREAK = self.settings['long_break_minutes'] * 60
        self.DAILY_GOAL = self.settings['daily_goal']
        self.LONG_BREAK_INTERVAL = self.settings['long_break_interval']
        
        # Timer state
        self.time_left = self.WORK_TIME
        self.is_running = False
        self.is_work_session = True
        self.pomodoros_completed = 0
        self.total_today = self.get_today_count()
        self.current_task = ""
        
        # Session tracking
        self._session_start_time = None
        
        # Thread management
        self.timer_thread = None
        self._stop_timer = False
        self._destroyed = False
        
        # Settings panel state
        self.settings_visible = False
        
        # Create the UI
        self.create_ui()
        
        # Update progress indicator
        self.update_progress_indicator()
        
    def get_settings(self, stats=None):
        """Get settings from stats > config > defaults"""
        # Try stats file first (if provided)
        if stats and 'settings' in stats:
            return stats['settings']
        
        # Try config.py
        try:
            import config
            return {
                'work_minutes': getattr(config, 'POMODORO_WORK_MINUTES', 25),
                'short_break_minutes': getattr(config, 'POMODORO_SHORT_BREAK_MINUTES', 5),
                'long_break_minutes': getattr(config, 'POMODORO_LONG_BREAK_MINUTES', 15),
                'daily_goal': getattr(config, 'POMODORO_DAILY_GOAL', 8),
                'long_break_interval': getattr(config, 'POMODORO_LONG_BREAK_INTERVAL', 4)
            }
        except:
            pass
        
        # Defaults
        return {
            'work_minutes': 25,
            'short_break_minutes': 5,
            'long_break_minutes': 15,
            'daily_goal': 8,
            'long_break_interval': 4
        }
    
    def create_ui(self):
        """Create the enhanced user interface."""
        
        # Title with settings gear
        title_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        title_frame.pack(pady=20)
        
        tk.Label(
            title_frame,
            text="🍅 Pomodoro Timer",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        ).pack(side=tk.LEFT)
        
        # Settings gear button
        tk.Button(
            title_frame,
            text="⚙️",
            font=("Segoe UI", 14),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            cursor="hand2",
            command=self.toggle_settings,
            relief=tk.FLAT,
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=10)
        
        # Task label entry (what are you working on?)
        task_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        task_frame.pack(pady=10, padx=50, fill=tk.X)
        
        tk.Label(
            task_frame,
            text="What are you working on?",
            font=("Segoe UI", 10),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        ).pack(anchor=tk.W)
        
        self.task_entry = tk.Entry(
            task_frame,
            font=("Segoe UI", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief=tk.FLAT
        )
        self.task_entry.pack(fill=tk.X, pady=5, ipady=5)
        self.task_entry.insert(0, "Focus session")
        
        # Session type label
        self.session_label = tk.Label(
            self.parent,
            text="WORK SESSION",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['accent']
        )
        self.session_label.pack(pady=10)
        
        # Timer display
        self.timer_display = tk.Label(
            self.parent,
            text="25:00",
            font=("Segoe UI", 72, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        self.timer_display.pack(pady=30)
        
        # Progress indicator (●○○○)
        self.progress_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        self.progress_frame.pack(pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="○○○○",
            font=("Segoe UI", 20),
            bg=self.colors['content_bg'],
            fg=self.colors['accent']
        )
        self.progress_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['accent'],
            fg="white",
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_timer,
            padx=30,
            pady=10,
            width=12
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        reset_button = tk.Button(
            button_frame,
            text="⟲ Reset",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.reset_timer,
            padx=30,
            pady=10,
            width=12
        )
        reset_button.pack(side=tk.LEFT, padx=10)
        
        # Daily goal progress bar
        goal_frame = tk.Frame(
            self.parent,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=2
        )
        goal_frame.pack(pady=10, padx=50, fill=tk.X)
        
        tk.Label(
            goal_frame,
            text="📊 Daily Goal Progress",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).pack(pady=(10, 5))
        
        # Progress bar container
        progress_bar_frame = tk.Frame(goal_frame, bg=self.colors['card_bg'])
        progress_bar_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.progress_bar_canvas = tk.Canvas(
            progress_bar_frame,
            height=30,
            bg=self.colors['background'],
            highlightthickness=0
        )
        self.progress_bar_canvas.pack(fill=tk.X)
        
        self.goal_label = tk.Label(
            goal_frame,
            text=f"Completed: {self.total_today}/{self.DAILY_GOAL} | Focus time: {self.total_today * self.settings['work_minutes']} min",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        )
        self.goal_label.pack(pady=(5, 10))
        
        # Draw initial progress bar
        self.update_goal_progress()
        
        # Action buttons
        action_frame = tk.Frame(goal_frame, bg=self.colors['card_bg'])
        action_frame.pack(pady=10)
        
        tk.Button(
            action_frame,
            text="📈 View Stats",
            font=("Segoe UI", 10),
            bg=self.colors['accent'],
            fg="white",
            cursor="hand2",
            command=self.show_stats_window,
            relief=tk.FLAT,
            padx=15,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Settings Panel (collapsed by default)
        self.settings_frame = tk.LabelFrame(
            self.parent,
            text="⚙️ Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            relief=tk.RAISED,
            borderwidth=2
        )
        # Don't pack yet - will show/hide with toggle
        
        self.create_settings_panel()
        
        # Info tip
        tk.Label(
            self.parent,
            text="💡 Tip: Stay focused during work sessions, rest during breaks!",
            font=("Segoe UI", 9, "italic"),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        ).pack(pady=10)
    
    def create_settings_panel(self):
        """Create the collapsible settings panel."""
        settings_grid = tk.Frame(self.settings_frame, bg=self.colors['card_bg'])
        settings_grid.pack(pady=10, padx=20)
        
        # Work duration
        tk.Label(
            settings_grid,
            text="Work Duration (min):",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.work_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=60,
            font=("Segoe UI", 10),
            width=10
        )
        self.work_spin.delete(0, tk.END)
        self.work_spin.insert(0, str(self.settings['work_minutes']))
        self.work_spin.grid(row=0, column=1, pady=5)
        
        # Short break
        tk.Label(
            settings_grid,
            text="Short Break (min):",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.short_break_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=30,
            font=("Segoe UI", 10),
            width=10
        )
        self.short_break_spin.delete(0, tk.END)
        self.short_break_spin.insert(0, str(self.settings['short_break_minutes']))
        self.short_break_spin.grid(row=1, column=1, pady=5)
        
        # Long break
        tk.Label(
            settings_grid,
            text="Long Break (min):",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.long_break_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=60,
            font=("Segoe UI", 10),
            width=10
        )
        self.long_break_spin.delete(0, tk.END)
        self.long_break_spin.insert(0, str(self.settings['long_break_minutes']))
        self.long_break_spin.grid(row=2, column=1, pady=5)
        
        # Daily goal
        tk.Label(
            settings_grid,
            text="Daily Goal (pomodoros):",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.goal_spin = tk.Spinbox(
            settings_grid,
            from_=1,
            to=20,
            font=("Segoe UI", 10),
            width=10
        )
        self.goal_spin.delete(0, tk.END)
        self.goal_spin.insert(0, str(self.settings['daily_goal']))
        self.goal_spin.grid(row=3, column=1, pady=5)
        
        # Long break interval
        tk.Label(
            settings_grid,
            text="Long Break Interval:",
            font=("Segoe UI", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).grid(row=4, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        
        self.interval_spin = tk.Spinbox(
            settings_grid,
            from_=2,
            to=8,
            font=("Segoe UI", 10),
            width=10
        )
        self.interval_spin.delete(0, tk.END)
        self.interval_spin.insert(0, str(self.settings['long_break_interval']))
        self.interval_spin.grid(row=4, column=1, pady=5)
        
        # Save button
        tk.Button(
            self.settings_frame,
            text="💾 Save Settings",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['success'],
            fg="white",
            cursor="hand2",
            command=self.save_settings,
            relief=tk.FLAT,
            padx=20,
            pady=8
        ).pack(pady=(5, 15))
    
    def toggle_settings(self):
        """Show/hide settings panel."""
        if self.settings_visible:
            self.settings_frame.pack_forget()
            self.settings_visible = False
        else:
            self.settings_frame.pack(pady=10, padx=50, fill=tk.X, before=self.parent.winfo_children()[-1])
            self.settings_visible = True
    
    def save_settings(self):
        """Save settings to stats file."""
        try:
            # Get new values
            work_min = int(self.work_spin.get())
            short_min = int(self.short_break_spin.get())
            long_min = int(self.long_break_spin.get())
            goal = int(self.goal_spin.get())
            interval = int(self.interval_spin.get())
            
            # Update settings
            self.settings = {
                'work_minutes': work_min,
                'short_break_minutes': short_min,
                'long_break_minutes': long_min,
                'daily_goal': goal,
                'long_break_interval': interval
            }
            
            # Update timer values
            self.WORK_TIME = work_min * 60
            self.SHORT_BREAK = short_min * 60
            self.LONG_BREAK = long_min * 60
            self.DAILY_GOAL = goal
            self.LONG_BREAK_INTERVAL = interval
            
            # Reset timer if not running
            if not self.is_running:
                if self.is_work_session:
                    self.time_left = self.WORK_TIME
                else:
                    if self.pomodoros_completed % interval == 0:
                        self.time_left = self.LONG_BREAK
                    else:
                        self.time_left = self.SHORT_BREAK
                self.update_display()
            
            # Save to file
            self.stats['settings'] = self.settings
            self.save_stats()
            
            # Update UI
            self.update_goal_progress()
            
            messagebox.showinfo("Settings Saved", "Your Pomodoro settings have been updated!")
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for all settings.")
    
    def update_goal_progress(self):
        """Update the visual progress bar for daily goal."""
        if not hasattr(self, 'progress_bar_canvas'):
            return
            
        canvas = self.progress_bar_canvas
        canvas.delete("all")
        
        width = canvas.winfo_width()
        if width <= 1:
            width = 400  # Default width
        height = 30
        
        # Calculate progress
        progress = min(self.total_today / self.DAILY_GOAL, 1.0) if self.DAILY_GOAL > 0 else 0
        fill_width = int(width * progress)
        
        # Draw background
        canvas.create_rectangle(0, 0, width, height, fill=self.colors['background'], outline="")
        
        # Draw filled portion
        if fill_width > 0:
            color = self.colors['success'] if progress >= 1.0 else self.colors['accent']
            canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline="")
        
        # Draw text
        text = f"{self.total_today}/{self.DAILY_GOAL}"
        canvas.create_text(
            width // 2,
            height // 2,
            text=text,
            font=("Segoe UI", 11, "bold"),
            fill=self.colors['text']
        )
        
        # Update label
        focus_min = self.total_today * self.settings['work_minutes']
        self.goal_label.config(
            text=f"Completed: {self.total_today}/{self.DAILY_GOAL} | Focus time: {focus_min} min"
        )
    
    def toggle_timer(self):
        """Start or pause the timer."""
        if self.is_running:
            # Pause
            self.is_running = False
            self._stop_timer = True
            self.start_button.config(text="▶ Resume")
        else:
            # Start
            self.is_running = True
            self._stop_timer = False
            self.start_button.config(text="⏸ Pause")
            
            # Record session start time (for work sessions)
            if self.is_work_session and self._session_start_time is None:
                self._session_start_time = datetime.now()
                self.current_task = self.task_entry.get().strip() or "Focus session"
            
            # Start timer thread
            self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.timer_thread.start()
    
    def run_timer(self):
        """Run the countdown timer in a separate thread."""
        while self.is_running and self.time_left > 0:
            if self._stop_timer or self._destroyed:
                break
                
            time.sleep(1)
            self.time_left -= 1
            
            try:
                self.parent.after(0, self.update_display)
            except tk.TclError:
                self._destroyed = True
                break
        
        # Timer complete
        if self.time_left == 0 and self.is_running and not self._destroyed:
            try:
                self.parent.after(0, self.timer_complete)
            except tk.TclError:
                self._destroyed = True
    
    def update_display(self):
        """Update timer display."""
        if self._destroyed:
            return
        try:
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_display.config(text=time_str)
            
            # Update Discord presence
            if self.is_running:
                self.update_discord_status(time_str)
                
        except tk.TclError:
            self._destroyed = True
            self.is_running = False
    
    def update_discord_status(self, time_str):
        """Update Discord with current status and task label."""
        try:
            from discord_presence_module import set_presence
            
            if self.is_work_session:
                task = self.current_task or "Focus session"
                status = f"🍅 Focusing on: {task}"
                details = f"{time_str} remaining | {self.total_today}/{self.DAILY_GOAL} today"
            else:
                if self.pomodoros_completed % self.LONG_BREAK_INTERVAL == 0:
                    status = f"☕ Long break"
                else:
                    status = f"☕ Short break"
                details = f"{time_str} remaining"
            
            set_presence("Pomodoro", f"{status}\n{details}")
        except:
            pass
    
    def timer_complete(self):
        """Handle timer completion."""
        self.is_running = False
        self.start_button.config(text="▶ Start")
        
        # Play beep
        self.parent.bell()
        
        if self.is_work_session:
            # Work session completed
            self.pomodoros_completed += 1
            self.total_today += 1
            
            # Record session
            self.record_session()
            
            # Save stats
            self.save_stats()
            
            # Send notification
            self.send_pomodoro_notification()
            
            # Update UI
            self.update_progress_indicator()
            self.update_goal_progress()
            
            # Determine next session
            if self.pomodoros_completed % self.LONG_BREAK_INTERVAL == 0:
                self.time_left = self.LONG_BREAK
                self.is_work_session = False
                self.session_label.config(text="LONG BREAK", fg=self.colors['success'])
                messagebox.showinfo(
                    "Great Work! 🎉",
                    f"You completed {self.pomodoros_completed} pomodoros!\nTime for a {self.settings['long_break_minutes']}-minute break."
                )
            else:
                self.time_left = self.SHORT_BREAK
                self.is_work_session = False
                self.session_label.config(text="SHORT BREAK", fg=self.colors['success'])
                messagebox.showinfo(
                    "Work Complete! ✅",
                    f"Great job! Take a {self.settings['short_break_minutes']}-minute break."
                )
        else:
            # Break completed
            self.time_left = self.WORK_TIME
            self.is_work_session = True
            self.session_label.config(text="WORK SESSION", fg=self.colors['accent'])
            self._session_start_time = None  # Reset for next session
            messagebox.showinfo(
                "Break Over! 💪",
                "Ready to focus again? Let's start another pomodoro!"
            )
        
        self.update_display()
    
    def record_session(self):
        """Record completed work session details."""
        if self._session_start_time is None:
            return
        
        session = {
            "started_at": self._session_start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration_minutes": self.settings['work_minutes'],
            "task_label": self.current_task
        }
        
        # Add to today's sessions
        today = date.today().isoformat()
        if 'days' not in self.stats:
            self.stats['days'] = {}
        if today not in self.stats['days']:
            self.stats['days'][today] = {
                "count": 0,
                "goal": self.DAILY_GOAL,
                "sessions": []
            }
        
        self.stats['days'][today]['count'] = self.total_today
        self.stats['days'][today]['goal'] = self.DAILY_GOAL
        self.stats['days'][today]['sessions'].append(session)
        
        # Reset for next session
        self._session_start_time = None
        self.current_task = ""
    
    def reset_timer(self):
        """Reset timer to start of current session."""
        self.is_running = False
        self._stop_timer = True
        self._session_start_time = None
        self.start_button.config(text="▶ Start")
        
        if self.is_work_session:
            self.time_left = self.WORK_TIME
        else:
            if self.pomodoros_completed % self.LONG_BREAK_INTERVAL == 0:
                self.time_left = self.LONG_BREAK
            else:
                self.time_left = self.SHORT_BREAK
        
        self.update_display()
    
    def update_progress_indicator(self):
        """Update progress dots (●○○○)."""
        completed_in_set = self.pomodoros_completed % self.LONG_BREAK_INTERVAL
        remaining = self.LONG_BREAK_INTERVAL - completed_in_set
        indicator = "●" * completed_in_set + "○" * remaining
        self.progress_label.config(text=indicator)
    
    def send_pomodoro_notification(self):
        """Send notification on completion."""
        try:
            from notification_manager import send_notification
            
            focus_min = self.total_today * self.settings['work_minutes']
            
            # Next session type
            if self.pomodoros_completed % self.LONG_BREAK_INTERVAL == 0:
                next_session = f"Long Break ({self.settings['long_break_minutes']} min)"
            else:
                next_session = f"Short Break ({self.settings['short_break_minutes']} min)"
            
            send_notification(
                title=f"🍅 Pomodoro #{self.pomodoros_completed} Complete!",
                message=f"Task: {self.current_task}\n\nYou've completed {self.total_today}/{self.DAILY_GOAL} pomodoros today ({focus_min} minutes).\n\nTime for a {next_session}",
                module="Pomodoro",
                notification_type="success",
                actions=[
                    {"label": "View Stats", "callback": self.show_stats_window},
                    {"label": "Start Break", "callback": self.toggle_timer}
                ],
                play_sound=False
            )
        except Exception as e:
            print(f"Error sending notification: {e}")
    
    def show_stats_window(self):
        """Open statistics window with matplotlib chart."""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
        except ImportError:
            messagebox.showerror(
                "Matplotlib Required",
                "Please install matplotlib to view statistics:\npip install matplotlib"
            )
            return
        
        # Create stats window
        stats_window = tk.Toplevel(self.parent)
        stats_window.title("📊 Pomodoro Statistics")
        stats_window.geometry("800x600")
        stats_window.configure(bg=self.colors['content_bg'])
        
        # Title
        tk.Label(
            stats_window,
            text="📊 Pomodoro Statistics",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        ).pack(pady=20)
        
        # Period selector
        period_frame = tk.Frame(stats_window, bg=self.colors['content_bg'])
        period_frame.pack(pady=10)
        
        period_var = tk.StringVar(value="7")

        # matplotlib figure (shared between bar chart and heatmap)
        fig = Figure(figsize=(10, 5), facecolor=self.colors['content_bg'])
        ax = fig.add_subplot(111, facecolor=self.colors['card_bg'])
        canvas = FigureCanvasTkAgg(fig, master=stats_window)

        # heatmap tk canvas (shown instead of matplotlib for year view)
        heat_frame = tk.Frame(stats_window, bg=self.colors['content_bg'])

        def show_bar(days):
            heat_frame.pack_forget()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.update_stats_chart(fig, ax, canvas, days)

        def show_heatmap():
            canvas.get_tk_widget().pack_forget()
            heat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            self.draw_heatmap(heat_frame)

        tk.Radiobutton(
            period_frame,
            text="Last 7 Days",
            variable=period_var,
            value="7",
            font=("Segoe UI", 10),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['card_bg'],
            activebackground=self.colors['content_bg'],
            command=lambda: show_bar("7")
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            period_frame,
            text="Last 30 Days",
            variable=period_var,
            value="30",
            font=("Segoe UI", 10),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['card_bg'],
            activebackground=self.colors['content_bg'],
            command=lambda: show_bar("30")
        ).pack(side=tk.LEFT, padx=10)

        tk.Radiobutton(
            period_frame,
            text="📅 Year View",
            variable=period_var,
            value="year",
            font=("Segoe UI", 10),
            bg=self.colors['content_bg'],
            fg=self.colors['text'],
            selectcolor=self.colors['card_bg'],
            activebackground=self.colors['content_bg'],
            command=show_heatmap
        ).pack(side=tk.LEFT, padx=10)

        # Initial chart
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.update_stats_chart(fig, ax, canvas, "7")
        
        # Export button
        tk.Button(
            stats_window,
            text="📥 Export CSV",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['accent'],
            fg="white",
            cursor="hand2",
            command=self.export_csv,
            relief=tk.FLAT,
            padx=20,
            pady=10
        ).pack(pady=20)
    
    def update_stats_chart(self, fig, ax, canvas, days):
        """Update the statistics chart."""
        ax.clear()
        
        # Get data for period
        import datetime as dt
        period = int(days)
        today = date.today()
        dates = [(today - dt.timedelta(days=i)).isoformat() for i in range(period-1, -1, -1)]
        
        counts = []
        for d in dates:
            if 'days' in self.stats and d in self.stats['days']:
                counts.append(self.stats['days'][d]['count'])
            else:
                counts.append(0)
        
        # Create bar chart
        bars = ax.bar(range(len(dates)), counts, color=self.colors['accent'])
        
        # Highlight today
        if len(bars) > 0:
            bars[-1].set_color(self.colors['success'])
        
        # Styling
        ax.set_title(f"Pomodoros Completed - Last {days} Days", 
                    color=self.colors['text'], fontsize=14, fontweight='bold')
        ax.set_xlabel("Date", color=self.colors['text'], fontsize=11)
        ax.set_ylabel("Pomodoros", color=self.colors['text'], fontsize=11)
        ax.tick_params(colors=self.colors['text_dim'])
        ax.spines['bottom'].set_color(self.colors['text_dim'])
        ax.spines['left'].set_color(self.colors['text_dim'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # X-axis labels (show fewer for 30 days)
        if period == 7:
            labels = [dt.datetime.fromisoformat(d).strftime("%m/%d") for d in dates]
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(labels, rotation=45)
        else:
            # Show every 5th day for 30 days
            indices = list(range(0, len(dates), 5))
            labels = [dt.datetime.fromisoformat(dates[i]).strftime("%m/%d") for i in indices]
            ax.set_xticks(indices)
            ax.set_xticklabels(labels, rotation=45)
        
        fig.tight_layout()
        canvas.draw()
    
    def draw_heatmap(self, parent_frame):
        """Draw a GitHub-style contribution heatmap for the past 52 weeks."""
        import datetime as dt

        # Clear previous heatmap widgets
        for w in parent_frame.winfo_children():
            try: w.destroy()
            except: pass

        today = date.today()
        # Start from Monday 52 weeks ago
        start = today - dt.timedelta(weeks=52)
        # Walk back to the previous Monday
        start -= dt.timedelta(days=start.weekday())

        CELL = 12   # px per cell
        GAP = 2     # gap between cells
        COLS = 53   # weeks
        ROWS = 7    # days per week (Mon=0 … Sun=6)
        LEFT_PAD = 28
        TOP_PAD = 20
        MONTH_H = 16

        canvas_w = LEFT_PAD + COLS * (CELL + GAP) + 10
        canvas_h = MONTH_H + TOP_PAD + ROWS * (CELL + GAP) + 40

        cv = tk.Canvas(parent_frame, bg=self.colors['content_bg'],
                       highlightthickness=0, width=canvas_w, height=canvas_h)
        cv.pack(pady=8)

        # Title
        cv.create_text(canvas_w // 2, 10, text="Yearly Contribution Heatmap",
                       font=("Segoe UI", 11, "bold"), fill=self.colors['text'], anchor="n")

        # Day-of-week labels
        day_names = ["M", "", "W", "", "F", "", "S"]
        for r, name in enumerate(day_names):
            y = MONTH_H + TOP_PAD + r * (CELL + GAP) + CELL // 2
            cv.create_text(LEFT_PAD - 6, y, text=name,
                           font=("Segoe UI", 8), fill=self.colors['text_dim'], anchor="e")

        # Colour scale: 0 → background, 1 → dim accent, 2-3 → accent, 4+ → bright
        bg = self.colors['background']
        accent = self.colors['accent']
        bright = self.colors['success']
        dim = self.colors.get('card_bg', '#334155')

        def cell_color(count):
            if count == 0:   return dim
            if count == 1:   return accent + "88"   # semi-transparent via hex may not work in tk
            if count <= 3:   return accent
            return bright

        # Build data lookup
        day_data = self.stats.get('days', {})

        # Track months for labels
        last_month = None
        tooltip_items = []

        current = start
        for col in range(COLS):
            for row in range(ROWS):
                d = current + dt.timedelta(days=row)
                if d > today:
                    current += dt.timedelta(weeks=1)
                    break
                count = day_data.get(d.isoformat(), {}).get('count', 0)
                color = cell_color(count)

                x1 = LEFT_PAD + col * (CELL + GAP)
                y1 = MONTH_H + TOP_PAD + row * (CELL + GAP)
                x2, y2 = x1 + CELL, y1 + CELL

                rect_id = cv.create_rectangle(x1, y1, x2, y2, fill=color, outline="", tags="cell")

                # Tooltip on hover
                tip_text = f"{d.strftime('%a %b %d')} — {count} session{'s' if count != 1 else ''}"
                tooltip_items.append((rect_id, tip_text))

                # Month label at top of first row
                if row == 0 and d.month != last_month:
                    last_month = d.month
                    cv.create_text(x1, MONTH_H + TOP_PAD - 4,
                                   text=d.strftime("%b"), font=("Segoe UI", 8),
                                   fill=self.colors['text_dim'], anchor="sw")

            current += dt.timedelta(weeks=1)

        # Tooltip implementation
        tip_win = [None]

        def _show_tip(event, text):
            if tip_win[0]:
                try: tip_win[0].destroy()
                except: pass
            tw = tk.Toplevel(cv)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
            tk.Label(tw, text=text, font=("Segoe UI", 9),
                     bg="#1E293B", fg="#E2E8F0", padx=6, pady=3, relief="solid", bd=1).pack()
            tip_win[0] = tw

        def _hide_tip(event):
            if tip_win[0]:
                try: tip_win[0].destroy()
                except: pass
            tip_win[0] = None

        for rect_id, tip_text in tooltip_items:
            cv.tag_bind(rect_id, "<Enter>", lambda e, t=tip_text: _show_tip(e, t))
            cv.tag_bind(rect_id, "<Leave>", _hide_tip)

        # Legend
        legend_y = MONTH_H + TOP_PAD + ROWS * (CELL + GAP) + 8
        cv.create_text(LEFT_PAD, legend_y, text="Less", font=("Segoe UI", 8),
                       fill=self.colors['text_dim'], anchor="w")
        for i, col in enumerate([dim, accent, bright]):
            lx = LEFT_PAD + 32 + i * (CELL + GAP)
            cv.create_rectangle(lx, legend_y - 1, lx + CELL, legend_y + CELL - 1,
                                fill=col, outline="")
        cv.create_text(LEFT_PAD + 32 + 3 * (CELL + GAP) + 4, legend_y, text="More",
                       font=("Segoe UI", 8), fill=self.colors['text_dim'], anchor="w")

    def export_csv(self):
        """Export session history to CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"pomodoro_stats_{date.today().isoformat()}.csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Start Time', 'End Time', 'Duration (min)', 'Task'])
                
                # Export all sessions
                if 'days' in self.stats:
                    for day in sorted(self.stats['days'].keys()):
                        day_data = self.stats['days'][day]
                        for session in day_data.get('sessions', []):
                            writer.writerow([
                                day,
                                session['started_at'],
                                session['completed_at'],
                                session['duration_minutes'],
                                session.get('task_label', 'Focus session')
                            ])
            
            messagebox.showinfo("Export Complete", f"Statistics exported to:\n{filename}")
        
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting CSV:\n{str(e)}")
    
    def get_today_count(self):
        """Get today's pomodoro count."""
        today = date.today().isoformat()
        if 'days' in self.stats and today in self.stats['days']:
            return self.stats['days'][today]['count']
        return 0
    
    def load_stats(self):
        """Load stats with backward-compatible migration from v1."""
        stats_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "pomodoro_stats.json"
        )
        
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                
                # Check for v2 format
                if 'version' in stats:
                    return stats
                
                # Migrate v1 format: {"2026-02-10": 3}
                new_stats = {
                    "version": 2,
                    "settings": self.get_settings(None),  # Pass None since no stats yet
                    "days": {}
                }
                
                for day, count in stats.items():
                    if day.count('-') == 2:  # Valid date format
                        new_stats['days'][day] = {
                            "count": count,
                            "goal": 8,  # Default goal
                            "sessions": []
                        }
                
                # Save migrated version
                with open(stats_file, 'w') as f:
                    json.dump(new_stats, f, indent=2)
                
                print("✅ Migrated pomodoro stats from v1 to v2")
                return new_stats
        
        except (json.JSONDecodeError, IOError):
            pass
        
        # Return new v2 structure
        return {
            "version": 2,
            "settings": self.get_settings(None),  # Pass None since no stats yet
            "days": {}
        }
    
    def save_stats(self):
        """Save stats to file."""
        stats_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "pomodoro_stats.json"
        )
        
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(stats_file), exist_ok=True)
            
            # Save
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        
        except IOError as e:
            print(f"Error saving pomodoro stats: {e}")
