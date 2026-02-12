"""
System Monitor Module for Thunderz Assistant
Version: 2.1.0 - Fixed Edition

This module provides comprehensive real-time system resource monitoring.
- CPU usage percentage with per-core breakdown
- RAM usage (used/total)
- ALL disk drives (not just C:)
- Top 5 CPU-consuming processes
- Top 5 RAM-consuming processes
- GPU monitoring (NVIDIA cards) - now using official NVIDIA library!
- Updates every 2 seconds
- Fixed: Scroll position no longer jumps!

Requires: psutil, pynvml (pip install psutil pynvml)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time


class SystemMonitorModule:
    """
    Enhanced System Monitor - comprehensive computer resource monitoring.
    
    Shows:
    - CPU usage with per-core breakdown
    - RAM usage with progress bar
    - All connected storage drives
    - Top 5 processes by CPU usage
    - Top 5 processes by RAM usage  
    - GPU stats (if NVIDIA GPU present)
    - Auto-refreshes every 2 seconds
    """
    ICON = "💻"
    PRIORITY = 9
    
    def __init__(self, parent_frame, colors):
        """
        Initialize the enhanced system monitor module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
            colors: Dictionary containing the application's color scheme
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Monitoring state
        self.is_monitoring = True
        self.update_interval = 2  # seconds between updates
        self._destroyed = False
        
        # Check for GPU support
        self.gpu_handle = None
        self.gpu_available = self.check_gpu_support()
        
        # Track disk progress bars for updates (to avoid recreating them)
        self.disk_widgets = {}
        
        # Create the UI
        self.create_ui()
        
        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def check_gpu_support(self):
        """Check if pynvml is available and initialize NVIDIA GPU monitoring."""
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                # Get handle for first GPU
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                return True
        except Exception as e:
            # GPU monitoring not available
            self.gpu_handle = None
            return False
        return False
    
    def create_ui(self):
        """Create the enhanced user interface with scrolling support."""
        
        # Title
        title_label = tk.Label(
            self.parent,
            text="💻 System Monitor - Enhanced",
            font=("Arial", 18, "bold"),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=20)
        
        # Create scrollable canvas
        canvas = tk.Canvas(self.parent, bg=self.colors['content_bg'], highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=canvas.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Store canvas for scroll position preservation
        self.canvas = canvas
        
        # Main stats frame inside canvas
        stats_frame = tk.Frame(canvas, bg=self.colors['content_bg'])
        self.canvas_window = canvas.create_window((0, 0), window=stats_frame, anchor="nw")
        stats_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Configure canvas width
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(
            self.canvas_window, width=e.width
        ))
        
        # === CPU USAGE ===
        cpu_card = self.create_stat_card(stats_frame, "🔥 CPU Usage")
        cpu_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.cpu_label = tk.Label(
            cpu_card,
            text="0.0%",
            font=("Arial", 32, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['accent']
        )
        self.cpu_label.pack(pady=10)
        
        # CPU progress bar
        self.cpu_progress = ttk.Progressbar(
            cpu_card,
            length=500,
            mode='determinate',
            maximum=100
        )
        self.cpu_progress.pack(pady=10, padx=20)
        
        # Per-core CPU usage
        self.cpu_cores_label = tk.Label(
            cpu_card,
            text="Per-core: Loading...",
            font=("Arial", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim'],
            justify=tk.LEFT
        )
        self.cpu_cores_label.pack(pady=(0, 10))
        
        # === RAM USAGE ===
        ram_card = self.create_stat_card(stats_frame, "🧠 Memory (RAM)")
        ram_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.ram_label = tk.Label(
            ram_card,
            text="0 GB / 0 GB",
            font=("Arial", 18, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        self.ram_label.pack(pady=10)
        
        self.ram_percent_label = tk.Label(
            ram_card,
            text="0.0%",
            font=("Arial", 14),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        )
        self.ram_percent_label.pack()
        
        # RAM progress bar
        self.ram_progress = ttk.Progressbar(
            ram_card,
            length=500,
            mode='determinate',
            maximum=100
        )
        self.ram_progress.pack(pady=10, padx=20)
        
        # === ALL DISK DRIVES ===
        disk_card = self.create_stat_card(stats_frame, "💾 Storage Drives")
        disk_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.disks_frame = tk.Frame(disk_card, bg=self.colors['card_bg'])
        self.disks_frame.pack(pady=10, padx=10, fill=tk.BOTH)
        
        # === GPU MONITORING ===
        if self.gpu_available:
            gpu_card = self.create_stat_card(stats_frame, "🎮 GPU (Graphics Card)")
            gpu_card.pack(fill=tk.X, pady=10, padx=20)
            
            self.gpu_name_label = tk.Label(
                gpu_card,
                text="Loading...",
                font=("Arial", 12, "bold"),
                bg=self.colors['card_bg'],
                fg=self.colors['accent']
            )
            self.gpu_name_label.pack(pady=(10, 5))
            
            self.gpu_stats_label = tk.Label(
                gpu_card,
                text="",
                font=("Arial", 11),
                bg=self.colors['card_bg'],
                fg=self.colors['text'],
                justify=tk.LEFT
            )
            self.gpu_stats_label.pack(pady=(5, 15), padx=10)
        else:
            # Show why GPU monitoring is unavailable
            gpu_card = self.create_stat_card(stats_frame, "🎮 GPU Monitoring")
            gpu_card.pack(fill=tk.X, pady=10, padx=20)
            
            gpu_unavailable_label = tk.Label(
                gpu_card,
                text="⚠️ GPU monitoring unavailable\n\n"
                     "Requirements:\n"
                     "• NVIDIA GPU (GTX/RTX series)\n"
                     "• NVIDIA drivers installed\n"
                     "• Run: pip install pynvml",
                font=("Arial", 10),
                bg=self.colors['card_bg'],
                fg=self.colors['text_dim'],
                justify=tk.LEFT
            )
            gpu_unavailable_label.pack(pady=15, padx=10)
        
        # === TOP CPU PROCESSES ===
        cpu_proc_card = self.create_stat_card(stats_frame, "⚡ Top CPU Processes")
        cpu_proc_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.cpu_proc_label = tk.Label(
            cpu_proc_card,
            text="Loading...",
            font=("Courier", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        self.cpu_proc_label.pack(pady=10, padx=10)
        
        # === TOP RAM PROCESSES ===
        ram_proc_card = self.create_stat_card(stats_frame, "🧠 Top RAM Processes")
        ram_proc_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.ram_proc_label = tk.Label(
            ram_proc_card,
            text="Loading...",
            font=("Courier", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        self.ram_proc_label.pack(pady=10, padx=10)
        
        # === PROCESS COUNT ===
        process_card = self.create_stat_card(stats_frame, "⚙️ System Info")
        process_card.pack(fill=tk.X, pady=10, padx=20)
        
        self.process_label = tk.Label(
            process_card,
            text="0 processes",
            font=("Arial", 14),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        self.process_label.pack(pady=10)
        
        self.system_info_label = tk.Label(
            process_card,
            text="Loading system info...",
            font=("Arial", 10),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dim']
        )
        self.system_info_label.pack(pady=(0, 10))
        
        # Configure progress bar style for dark theme
        self.configure_progress_style()
    
    def create_stat_card(self, parent, title):
        """Create a card container for a stat section."""
        card = tk.Frame(
            parent,
            bg=self.colors['card_bg'],
            relief=tk.RAISED,
            borderwidth=2
        )
        
        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        title_label.pack(pady=(15, 5))
        
        return card
    
    def configure_progress_style(self):
        """Configure the progress bar style to match dark theme."""
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.colors['secondary'],
            background=self.colors['accent'],
            bordercolor=self.colors['card_bg'],
            lightcolor=self.colors['accent'],
            darkcolor=self.colors['accent']
        )
        
        # Apply custom style
        self.cpu_progress.config(style="Custom.Horizontal.TProgressbar")
        self.ram_progress.config(style="Custom.Horizontal.TProgressbar")
    
    def monitor_loop(self):
        """Background monitoring loop - continuously fetches and updates system stats."""
        while self.is_monitoring and not self._destroyed:
            try:
                # Get system stats
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
                ram = psutil.virtual_memory()
                disks = self.get_all_disks()
                process_count = len(psutil.pids())
                top_cpu_procs = self.get_top_processes_by_cpu()
                top_ram_procs = self.get_top_processes_by_ram()
                gpu_stats = self.get_gpu_stats() if self.gpu_available else None
                
                # Schedule UI update on main thread
                try:
                    self.parent.after(0, lambda: self.update_display(
                        cpu_percent, cpu_per_core, ram, disks, process_count,
                        top_cpu_procs, top_ram_procs, gpu_stats
                    ))
                except tk.TclError:
                    self._destroyed = True
                    break
                
                # Wait before next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                # If monitoring fails, show error and stop
                try:
                    self.parent.after(0, lambda: self.show_error(str(e)))
                except tk.TclError:
                    pass
                break
    
    def get_all_disks(self):
        """Get all mounted disk partitions."""
        disks = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'usage': usage
                })
            except (PermissionError, OSError):
                # Skip inaccessible drives
                continue
        return disks
    
    def get_top_processes_by_cpu(self, count=5):
        """Get top N processes by CPU usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 0:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU and return top N
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:count]
    
    def get_top_processes_by_ram(self, count=5):
        """Get top N processes by RAM usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                info = proc.info
                if info['memory_percent'] > 0:
                    processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by RAM and return top N
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        return processes[:count]
    
    def get_gpu_stats(self):
        """Get GPU statistics using NVIDIA's official library."""
        if not self.gpu_handle:
            return None
            
        try:
            import pynvml
            
            # Get GPU name
            name = pynvml.nvmlDeviceGetName(self.gpu_handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            
            # Get utilization rates
            util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            
            # Get memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            memory_used_mb = mem_info.used / (1024 ** 2)
            memory_total_mb = mem_info.total / (1024 ** 2)
            memory_percent = (mem_info.used / mem_info.total) * 100
            
            # Get temperature
            temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            
            return {
                'name': name,
                'load': util.gpu,  # Already a percentage
                'memory_used': memory_used_mb,
                'memory_total': memory_total_mb,
                'memory_percent': memory_percent,
                'temperature': temp
            }
        except Exception as e:
            return None
    
    def update_display(self, cpu_percent, cpu_per_core, ram, disks, process_count,
                      top_cpu_procs, top_ram_procs, gpu_stats):
        """Update all display elements with new system stats - preserves scroll position!"""
        if self._destroyed:
            return
        
        # CRITICAL: Save scroll position before updating
        try:
            scroll_pos = self.canvas.yview()[0]  # Get current scroll position
        except:
            scroll_pos = 0.0
            
        try:
            # Update CPU
            self.cpu_label.config(text=f"{cpu_percent:.1f}%")
            self.cpu_progress['value'] = cpu_percent
            
            # Change color based on CPU usage
            if cpu_percent > 80:
                self.cpu_label.config(fg="#EF4444")  # Red
            elif cpu_percent > 50:
                self.cpu_label.config(fg="#F59E0B")  # Orange
            else:
                self.cpu_label.config(fg=self.colors['accent'])  # Blue
            
            # Per-core CPU
            cores_text = "Per-core: " + " | ".join([f"Core {i+1}: {core:.1f}%" 
                                                     for i, core in enumerate(cpu_per_core)])
            self.cpu_cores_label.config(text=cores_text)
            
            # Update RAM
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            self.ram_label.config(text=f"{ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB")
            self.ram_percent_label.config(text=f"{ram.percent:.1f}% used")
            self.ram_progress['value'] = ram.percent
            
            # Update Disks (smart update - only recreate if drives changed)
            self.update_disks_display(disks)
            
            # Update GPU
            if self.gpu_available and gpu_stats:
                self.gpu_name_label.config(text=f"🎮 {gpu_stats['name']}")
                gpu_text = (
                    f"GPU Load: {gpu_stats['load']:.1f}%\n"
                    f"VRAM: {gpu_stats['memory_used']:.0f} MB / {gpu_stats['memory_total']:.0f} MB "
                    f"({gpu_stats['memory_percent']:.1f}%)\n"
                    f"Temperature: {gpu_stats['temperature']}°C"
                )
                self.gpu_stats_label.config(text=gpu_text)
            
            # Update top CPU processes
            cpu_proc_text = self.format_process_list(top_cpu_procs, 'cpu')
            self.cpu_proc_label.config(text=cpu_proc_text)
            
            # Update top RAM processes
            ram_proc_text = self.format_process_list(top_ram_procs, 'ram')
            self.ram_proc_label.config(text=ram_proc_text)
            
            # Update Process count and system info
            self.process_label.config(text=f"{process_count} running processes")
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            self.system_info_label.config(
                text=f"System Uptime: {uptime_hours:.1f} hours"
            )
            
            # CRITICAL: Restore scroll position after updates
            self.canvas.yview_moveto(scroll_pos)
            
        except tk.TclError:
            # Widget was destroyed, stop monitoring
            self._destroyed = True
            self.is_monitoring = False
    
    def update_disks_display(self, disks):
        """Update the disk drives display - smart update to preserve widgets."""
        if not disks:
            # Clear and show no drives message
            for widget in self.disks_frame.winfo_children():
                widget.destroy()
            self.disk_widgets = {}
            
            tk.Label(
                self.disks_frame,
                text="No accessible drives found",
                font=("Arial", 11),
                bg=self.colors['card_bg'],
                fg=self.colors['text_dim']
            ).pack()
            return
        
        # Get current disk list
        current_disks = {d['device']: d for d in disks}
        
        # Check if disk list changed
        if set(current_disks.keys()) != set(self.disk_widgets.keys()):
            # Disks changed, rebuild everything
            for widget in self.disks_frame.winfo_children():
                widget.destroy()
            self.disk_widgets = {}
            
            # Create widgets for each disk
            for disk in disks:
                disk_frame = tk.Frame(self.disks_frame, bg=self.colors['card_bg'])
                disk_frame.pack(fill=tk.X, pady=5)
                
                # Disk header
                header_text = f"{disk['device']} ({disk['fstype']})"
                header_label = tk.Label(
                    disk_frame,
                    text=header_text,
                    font=("Arial", 11, "bold"),
                    bg=self.colors['card_bg'],
                    fg=self.colors['text']
                )
                header_label.pack(anchor='w')
                
                # Usage label
                usage_label = tk.Label(
                    disk_frame,
                    text="",
                    font=("Arial", 10),
                    bg=self.colors['card_bg'],
                    fg=self.colors['text_dim']
                )
                usage_label.pack(anchor='w')
                
                # Progress bar for this disk
                disk_progress = ttk.Progressbar(
                    disk_frame,
                    length=450,
                    mode='determinate',
                    maximum=100,
                    style="Custom.Horizontal.TProgressbar"
                )
                disk_progress.pack(pady=5)
                
                # Store widgets for updates
                self.disk_widgets[disk['device']] = {
                    'usage_label': usage_label,
                    'progress': disk_progress
                }
        
        # Update existing widgets
        for device, disk in current_disks.items():
            if device in self.disk_widgets:
                widgets = self.disk_widgets[device]
                
                used_gb = disk['usage'].used / (1024 ** 3)
                total_gb = disk['usage'].total / (1024 ** 3)
                percent = disk['usage'].percent
                
                usage_text = f"{used_gb:.1f} GB / {total_gb:.1f} GB ({percent:.1f}%)"
                usage_color = "#EF4444" if percent > 90 else self.colors['text_dim']
                
                widgets['usage_label'].config(text=usage_text, fg=usage_color)
                widgets['progress']['value'] = percent
    
    def format_process_list(self, processes, metric_type):
        """Format the process list for display."""
        if not processes:
            return "No active processes"
        
        lines = []
        for i, proc in enumerate(processes, 1):
            name = proc['name'][:25]  # Truncate long names
            if metric_type == 'cpu':
                value = proc['cpu_percent']
                lines.append(f"{i}. {name:<25} {value:>6.1f}%")
            else:  # ram
                value = proc['memory_percent']
                lines.append(f"{i}. {name:<25} {value:>6.1f}%")
        
        return "\n".join(lines)
    
    def show_error(self, error_msg):
        """Display an error message if monitoring fails."""
        if self._destroyed:
            return
        try:
            error_label = tk.Label(
                self.parent,
                text=f"Error monitoring system:\n{error_msg}",
                font=("Arial", 12),
                bg=self.colors['content_bg'],
                fg="#EF4444",
                justify=tk.CENTER
            )
            error_label.pack(pady=20)
        except tk.TclError:
            pass
