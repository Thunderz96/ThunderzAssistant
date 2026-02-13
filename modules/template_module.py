"""
Template Module for Thunderz Assistant (v1.10+)
-----------------------------------------------
This template demonstrates how to create a "Drop-in" module that is 
automatically discovered by the main application.

STEPS TO CREATE A NEW MODULE:
1. Copy this file to the 'modules/' folder (or 'internal_modules/' for private).
2. Rename the class (e.g., class CryptoModule).
3. Set your ICON and PRIORITY.
4. Restart the app. It will appear automatically!
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os

class TemplateModule:
    # --- DISCOVERY METADATA ---
    # These two variables tell main.py to load this class.
    ICON = "🛠️"       # Emoji icon for the sidebar
    PRIORITY = 50     # Order in sidebar (1=Top, 100=Bottom)
    
    def __init__(self, parent_frame, colors):
        """
        Standard constructor required by the plugin system.
        """
        self.parent = parent_frame
        self.colors = colors
        
        # --- UNIFIED PATH LOGIC ---
        # Ensures your module can find its assets whether running as code or EXE
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.data_dir = os.path.join(self.base_dir, 'data')
        
        # Create the UI
        self.create_ui()
        
    def create_ui(self):
        """
        Builds the interface. 
        Uses the 'colors' dictionary to match the app theme.
        """
        # 1. Header Section
        header = tk.Frame(self.parent, bg=self.colors['secondary'], pady=20, padx=20)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="New Module Title", font=("Segoe UI", 20, "bold"),
                bg=self.colors['secondary'], fg="white").pack(anchor="w")
        
        tk.Label(header, text="Description of what this tool does.", font=("Segoe UI", 10),
                bg=self.colors['secondary'], fg=self.colors['text_dim']).pack(anchor="w")

        # 2. Content Area
        content = tk.Frame(self.parent, bg=self.colors['background'], padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Example: Input Card
        card = tk.Frame(content, bg=self.colors['card_bg'], padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)
        
        tk.Label(card, text="Input Section", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w", pady=(0, 10))
        
        self.entry = tk.Entry(card, font=("Segoe UI", 11), width=40)
        self.entry.pack(side=tk.LEFT, padx=(0, 10))
        
        btn = tk.Button(card, text="Run Action", command=self.run_background_task,
                       bg=self.colors['accent'], fg="white", font=("Segoe UI", 10),
                       relief=tk.FLAT, padx=15, cursor="hand2")
        btn.pack(side=tk.LEFT)
        
        # Example: Results Area
        self.lbl_result = tk.Label(content, text="Ready", font=("Segoe UI", 11),
                                  bg=self.colors['background'], fg=self.colors['text'])
        self.lbl_result.pack(pady=20)

    def run_background_task(self):
        """
        Example of how to run code without freezing the UI.
        """
        user_input = self.entry.get()
        if not user_input:
            messagebox.showwarning("Input", "Please enter something first.")
            return

        self.lbl_result.config(text="Processing...", fg=self.colors['warning'])
        
        # Launch thread
        threading.Thread(target=self._worker, args=(user_input,), daemon=True).start()

    def _worker(self, input_data):
        """
        Background worker. 
        CRITICAL: Never update UI directly here. Use _safe_update.
        """
        import time
        # Simulate work
        time.sleep(2)
        
        result_text = f"Processed: {input_data.upper()}"
        
        # Update UI safely on the main thread
        self.parent.after(0, lambda: self._safe_update(result_text))

    def _safe_update(self, text):
        """
        Updates UI elements ONLY if they still exist.
        Prevents crashes if user switches modules while task is running.
        """
        if hasattr(self, 'lbl_result') and self.lbl_result.winfo_exists():
            self.lbl_result.config(text=text, fg=self.colors['success'])