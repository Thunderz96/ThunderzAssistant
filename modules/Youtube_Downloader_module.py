"""
Video Downloader Module for Thunderz Assistant (v1.10+)
-------------------------------------------------------
Downloads videos from YouTube, HypnoTube.com, and thousands of other sites supported by yt-dlp.
Supports saving as MP4 (video + audio) or MP3 (audio only).

Requirements:
- yt-dlp (install via: pip install yt-dlp)
- FFmpeg (download from https://ffmpeg.org and add to PATH)

Place this file in the 'modules/' folder and restart the app.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import subprocess

class VideoDownloaderModule:
    # --- DISCOVERY METADATA ---
    ICON = "⬇️"        # Download icon
    PRIORITY = 40      # Position in sidebar

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        
        # --- UNIFIED PATH LOGIC ---
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.download_dir = os.path.join(self.data_dir, 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        
        # UI components
        self.format_var = tk.StringVar(value="mp4")
        
        self.create_ui()
        
    def create_ui(self):
        # 1. Header Section
        header = tk.Frame(self.parent, bg=self.colors['secondary'], pady=20, padx=20)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="Video Downloader", font=("Segoe UI", 20, "bold"),
                bg=self.colors['secondary'], fg="white").pack(anchor="w")
        
        desc_text = ("Download videos from YouTube, HypnoTube.com and many other sites.\n"
                     "Choose MP4 for video+audio or MP3 for audio only.\n\n"
                     "Requirements: yt-dlp (pip install yt-dlp) and FFmpeg in PATH.")
        tk.Label(header, text=desc_text, font=("Segoe UI", 10),
                bg=self.colors['secondary'], fg=self.colors['text_dim'],
                justify="left", wraplength=600).pack(anchor="w", pady=(5,0))

        # 2. Content Area
        content = tk.Frame(self.parent, bg=self.colors['background'], padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Input Card
        input_card = tk.Frame(content, bg=self.colors['card_bg'], padx=20, pady=20)
        input_card.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(input_card, text="Enter video URL:", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w", pady=(0, 8))
        
        entry_frame = tk.Frame(input_card, bg=self.colors['card_bg'])
        entry_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.url_entry = tk.Entry(entry_frame, font=("Segoe UI", 11), relief=tk.SOLID, bd=1)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Format selection
        format_frame = tk.Frame(input_card, bg=self.colors['card_bg'])
        format_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(format_frame, text="Output format:", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w", pady=(0, 5))
        
        radio_frame = tk.Frame(format_frame, bg=self.colors['card_bg'])
        radio_frame.pack(anchor="w")
        
        tk.Radiobutton(radio_frame, text="MP4 (Video + Audio)", variable=self.format_var,
                      value="mp4", bg=self.colors['card_bg'], fg=self.colors['text'],
                      selectcolor=self.colors['secondary'], font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 30))
        
        tk.Radiobutton(radio_frame, text="MP3 (Audio only)", variable=self.format_var,
                      value="mp3", bg=self.colors['card_bg'], fg=self.colors['text'],
                      selectcolor=self.colors['secondary'], font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        # Download button
        btn = tk.Button(input_card, text="Start Download", command=self.start_download,
                       bg=self.colors['accent'], fg="white", font=("Segoe UI", 11, "bold"),
                       relief=tk.FLAT, padx=30, pady=10, cursor="hand2")
        btn.pack(side=tk.RIGHT)
        
        # Progress Card
        progress_card = tk.Frame(content, bg=self.colors['card_bg'], padx=20, pady=20)
        progress_card.pack(fill=tk.X, pady=10)
        
        tk.Label(progress_card, text="Progress", font=("Segoe UI", 12, "bold"),
                bg=self.colors['card_bg'], fg="white").pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(progress_card, orient="horizontal",
                                          length=500, mode="determinate", maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(8, 10))
        
        self.status_label = tk.Label(progress_card, text="Ready", font=("Segoe UI", 11),
                                   bg=self.colors['card_bg'], fg=self.colors['text'],
                                   anchor="w", justify="left", wraplength=700)
        self.status_label.pack(fill=tk.X)
        
        # Info and open folder
        info_frame = tk.Frame(content, bg=self.colors['background'])
        info_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(info_frame, text=f"Downloads saved to:\n{self.download_dir}",
                font=("Segoe UI", 10), bg=self.colors['background'],
                fg=self.colors['text_dim']).pack(anchor="w")
        
        open_btn = tk.Button(info_frame, text="Open Downloads Folder", command=self.open_folder,
                            bg=self.colors['accent'], fg="white", font=("Segoe UI", 10),
                            relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        open_btn.pack(pady=(10, 0))

    def start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Input Required", "Please enter a video URL.")
            return
        
        self.status_label.config(text="Preparing download...", fg=self.colors['text'])
        self.progress_bar['value'] = 0
        
        threading.Thread(target=self._worker, args=(url, self.format_var.get()), daemon=True).start()

    def my_progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                percent = float(d.get('_percent_str', '0').replace('%', '').strip())
            except:
                percent = 0
                
            self.parent.after(0, lambda p=percent: self.progress_bar.config(value=p))
            
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            text = f"Downloading... {d.get('_percent_str', '0%')} | Speed: {speed} | ETA: {eta}"
            self.parent.after(0, lambda t=text: self.status_label.config(text=t, fg=self.colors['text']))
            
        elif d['status'] == 'finished':
            self.parent.after(0, lambda: self.progress_bar.config(value=100))
            self.parent.after(0, lambda: self.status_label.config(text="Download finished - finalizing file...", fg=self.colors['success']))

    def _worker(self, url, format_type):
        try:
            import yt_dlp
        except ImportError:
            self._safe_update("Error: yt-dlp not installed. Run: pip install yt-dlp", fg="red")
            return

        ydl_opts = {
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.my_progress_hook],
            'noplaylist': True,
            'quiet': False,
        }

        if format_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:  # mp4
            ydl_opts.update({
                'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best',
                # Prefers H.264 + AAC (MP4-compatible), falls back to best available
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            self._safe_update("Download completed successfully!", fg=self.colors['success'])
            self.parent.after(0, lambda: self.progress_bar.config(value=0))
            
        except Exception as e:
            error_msg = str(e).split('\n')[0]  # First line usually most useful
            self._safe_update(f"Download failed: {error_msg}", fg="red")
            self.parent.after(0, lambda: self.progress_bar.config(value=0))

    def _safe_update(self, text, fg=None):
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.config(text=text)
            if fg:
                self.status_label.config(fg=fg)

    def open_folder(self):
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.download_dir)
            elif os.name == 'posix':
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', self.download_dir])
                else:  # Linux/other
                    subprocess.call(['xdg-open', self.download_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")