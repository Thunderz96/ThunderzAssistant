"""
Pomodoro Timer Module for Thunderz Assistant
Version: 1.0.0

This module provides a Pomodoro productivity timer.
- 25 minute work sessions
- 5 minute short breaks
- 15 minute long breaks (after 4 pomodoros)
- Track completed sessions today
- Desktop notifications

The Pomodoro Technique: Work in focused 25-minute intervals with short breaks.
After 4 work sessions, take a longer break.
"""

import tkinter as tk
from tkinter import messagebox
import time
import json
import os
from datetime import datetime, date
import threading


class PomodoroModule:
    """
    Pomodoro Timer - helps you focus with timed work/break intervals.
    
    Features:
    - 25 min work sessions (customizable)
    - 5 min short breaks
    - 15 min long breaks after 4 pomodoros
    - Visual countdown
    - Session tracking
    - Sound notification (system beep)
    """
    
    def __init__(self, parent_frame, colors):
        """
        Initialize the Pomodoro timer module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
            colors: Dictionary containing the application's color scheme
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Timer settings (in seconds for easy calculation)
        self.WORK_TIME = 25 * 60      # 25 minutes
        self.SHORT_BREAK = 5 * 60     # 5 minutes
        self.LONG_BREAK = 15 * 60     # 15 minutes
        
        # Timer state
        self.time_left = self.WORK_TIME
        self.is_running = False
        self.is_work_session = True
        self.pomodoros_completed = 0
        self.total_today = 0
        
        # Thread management
        self.timer_thread = None
        self._stop_timer = False
        self._destroyed = False  # Track if widgets are destroyed
        
        # Load today's stats
        self.load_stats()
        
        # Create the UI
        self.create_ui()
        
    def create_ui(self):
        """Create the user interface for the Pomodoro timer."""
        
        # Title
        title_label = tk.Label(
            self.parent,
            text="🍅 Pomodoro Timer",
            font=("Arial", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Session type label (Work/Break)
        self.session_label = tk.Label(
            self.parent,
            text="WORK SESSION",
            font=("Arial", 14, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['accent']
        )
        self.session_label.pack(pady=10)
        
        # Timer display (large countdown)
        self.timer_display = tk.Label(
            self.parent,
            text="25:00",
            font=("Arial", 72, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        self.timer_display.pack(pady=30)
        
        # Progress indicator
        self.progress_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        self.progress_frame.pack(pady=10)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="●○○○",  # Visual indicator of pomodoros (●=completed, ○=pending)
            font=("Arial", 20),
            bg=self.colors['content_bg'],
            fg=self.colors['accent']
        )
        self.progress_label.pack()
        
        # Control buttons frame
        button_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        button_frame.pack(pady=20)
        
        # Start/Pause button
        self.start_button = tk.Button(
            button_frame,
            text="▶ Start",
            font=("Arial", 14, "bold"),
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
        
        # Reset button
        reset_button = tk.Button(
            button_frame,
            text="⟲ Reset",
            font=("Arial", 14, "bold"),
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
        
        # Stats frame
        stats_frame = tk.Frame(
            self.parent,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=2
        )
        stats_frame.pack(pady=20, padx=50, fill=tk.X)
        
        tk.Label(
            stats_frame,
            text="📊 Today's Progress",
            font=("Arial", 12, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        ).pack(pady=10)
        
        self.stats_label = tk.Label(
            stats_frame,
            text=f"Completed: {self.total_today} pomodoros\nFocus time: {self.total_today * 25} minutes",
            font=("Arial", 11),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        )
        self.stats_label.pack(pady=10)
        
        # Info label
        info_label = tk.Label(
            self.parent,
            text="💡 Tip: Focus for 25 minutes, then take a 5-minute break!",
            font=("Arial", 9, "italic"),
            bg=self.colors['content_bg'],
            fg=self.colors['text_dim']
        )
        info_label.pack(pady=10)
        
    def toggle_timer(self):
        """Start or pause the timer."""
        if self.is_running:
            # Pause the timer
            self.is_running = False
            self._stop_timer = True
            self.start_button.config(text="▶ Resume")
        else:
            # Start the timer
            self.is_running = True
            self._stop_timer = False
            self.start_button.config(text="⏸ Pause")
            
            # Start timer in a separate thread so UI doesn't freeze
            self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
            self.timer_thread.start()
    
    def run_timer(self):
        """
        Run the countdown timer.
        
        This runs in a separate thread to keep the UI responsive.
        Updates the display every second.
        """
        while self.is_running and self.time_left > 0:
            if self._stop_timer or self._destroyed:
                break
                
            time.sleep(1)
            self.time_left -= 1
            
            # Update display on main thread (safely)
            try:
                self.parent.after(0, self.update_display)
            except tk.TclError:
                # Widget destroyed, stop timer
                self._destroyed = True
                break
        
        # Timer finished
        if self.time_left == 0 and self.is_running and not self._destroyed:
            try:
                self.parent.after(0, self.timer_complete)
            except tk.TclError:
                self._destroyed = True
    
    def update_display(self):
        """Update the timer display with remaining time."""
        if self._destroyed:
            return
        try:
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_display.config(text=time_str)
            
            # Update Discord presence if timer is running
            if self.is_running:
                self.update_discord_status(time_str)
                
        except tk.TclError:
            # Widget destroyed
            self._destroyed = True
            self.is_running = False
    
    def update_discord_status(self, time_str):
        """Update Discord with current Pomodoro status"""
        try:
            from discord_presence_module import set_presence
            
            if self.is_work_session:
                status = f"🍅 Focusing - {time_str} remaining"
                details = f"Pomodoro {self.pomodoros_completed + 1}/8 today"
            else:
                # Determine if long or short break
                if self.pomodoros_completed % 4 == 0:
                    status = f"☕ Long break - {time_str}"
                else:
                    status = f"☕ Short break - {time_str}"
                details = f"{self.pomodoros_completed} pomodoros completed"
            
            set_presence("Pomodoro", f"{status}\n{details}")
        except:
            pass  # Discord not connected, ignore
    
    def timer_complete(self):
        """
        Called when a timer session completes.
        
        Handles:
        - Playing notification sound
        - Updating pomodoro count
        - Switching between work/break sessions
        - Saving stats
        """
        self.is_running = False
        self.start_button.config(text="▶ Start")
        
        # Play system beep (notification sound)
        self.parent.bell()
        
        if self.is_work_session:
            # Work session completed!
            self.pomodoros_completed += 1
            self.total_today += 1
            self.save_stats()
            
            # Update progress indicator
            self.update_progress_indicator()
            
            # Determine next session (short break or long break)
            if self.pomodoros_completed % 4 == 0:
                # Long break after 4 pomodoros
                self.time_left = self.LONG_BREAK
                self.is_work_session = False
                self.session_label.config(text="LONG BREAK", fg="#10B981")  # Green
                messagebox.showinfo(
                    "Great Work! 🎉",
                    f"You completed {self.pomodoros_completed} pomodoros!\nTime for a 15-minute break."
                )
            else:
                # Short break
                self.time_left = self.SHORT_BREAK
                self.is_work_session = False
                self.session_label.config(text="SHORT BREAK", fg="#10B981")  # Green
                messagebox.showinfo(
                    "Work Complete! ✅",
                    "Great job! Take a 5-minute break."
                )
        else:
            # Break completed, back to work
            self.time_left = self.WORK_TIME
            self.is_work_session = True
            self.session_label.config(text="WORK SESSION", fg=self.colors['accent'])
            messagebox.showinfo(
                "Break Over! 💪",
                "Ready to focus again? Let's start another pomodoro!"
            )
        
        # Update stats display
        self.update_stats_display()
        self.update_display()
    
    def reset_timer(self):
        """Reset the timer to the start of current session type."""
        self.is_running = False
        self._stop_timer = True
        self.start_button.config(text="▶ Start")
        
        if self.is_work_session:
            self.time_left = self.WORK_TIME
        else:
            # Determine if it should be short or long break
            if self.pomodoros_completed % 4 == 0:
                self.time_left = self.LONG_BREAK
            else:
                self.time_left = self.SHORT_BREAK
        
        self.update_display()
    
    def update_progress_indicator(self):
        """
        Update the visual progress indicator.
        
        Shows filled circles (●) for completed pomodoros in the current set of 4,
        and empty circles (○) for remaining ones.
        """
        completed_in_set = self.pomodoros_completed % 4
        indicator = "●" * completed_in_set + "○" * (4 - completed_in_set)
        self.progress_label.config(text=indicator)
    
    def update_stats_display(self):
        """Update the statistics display with today's totals."""
        focus_minutes = self.total_today * 25
        self.stats_label.config(
            text=f"Completed: {self.total_today} pomodoros\nFocus time: {focus_minutes} minutes"
        )
    
    def load_stats(self):
        """
        Load today's pomodoro statistics from file.
        
        Stats are stored in JSON format with the date as the key.
        Only today's stats are loaded; old dates are ignored.
        """
        stats_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "pomodoro_stats.json"
        )
        
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                
                # Get today's date as string
                today = date.today().isoformat()
                
                # Load today's count
                self.total_today = stats.get(today, 0)
        except (json.JSONDecodeError, IOError):
            self.total_today = 0
    
    def save_stats(self):
        """
        Save today's pomodoro count to file.
        
        Keeps a running total for today, creating or updating the file.
        """
        stats_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "pomodoro_stats.json"
        )
        
        try:
            # Load existing stats
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = {}
            
            # Update today's count
            today = date.today().isoformat()
            stats[today] = self.total_today
            
            # Save back to file
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except IOError:
            pass  # Fail silently if we can't save
