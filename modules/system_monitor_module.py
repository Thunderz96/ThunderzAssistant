"""
System Monitor Module for Thunderz Assistant
Version: 3.2.0 - CPU Detail & VRAM Fix

Updates:
- FIXED: "Error fetching procs" on GPU (Added safe-guard for protected processes).
- FEATURE: CPU Frequency (GHz) display.
- FEATURE: CPU Temperature (Attempts to read hardware sensors).
"""

import tkinter as tk
from tkinter import ttk
import psutil
import threading
import time

class ModernProgressBar(tk.Canvas):
    """Sleek progress bar drawn using Canvas."""
    def __init__(self, parent, width=300, height=12, bg_color="#1E293B", fill_color="#3B82F6"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.width = width
        self.height = height
        self.base_fill_color = fill_color
        self.create_rectangle(0, 0, width, height, fill=bg_color, width=0)
        self.fill_rect = self.create_rectangle(0, 0, 0, height, fill=fill_color, width=0)

    def set_value(self, percent):
        percent = max(0, min(100, percent))
        fill_width = (percent / 100) * self.width
        self.coords(self.fill_rect, 0, 0, fill_width, self.height)
        if percent > 85: color = "#EF4444"
        elif percent > 60: color = "#F59E0B"
        else: color = self.base_fill_color
        self.itemconfig(self.fill_rect, fill=color)

class MiniCoreBar(tk.Canvas):
    """Tiny vertical bar for individual CPU cores"""
    def __init__(self, parent, width=30, height=40, bg_color="#1E293B", fill_color="#3B82F6"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.h = height
        self.w = width
        self.create_rectangle(0, 0, width, height, fill=bg_color, width=0)
        self.bar = self.create_rectangle(0, height, width, height, fill=fill_color, width=0)

    def set_value(self, percent):
        fill_h = (percent / 100) * self.h
        self.coords(self.bar, 0, self.h - fill_h, self.w, self.h)
        if percent > 80: col = "#EF4444"
        elif percent > 50: col = "#F59E0B"
        else: col = "#3B82F6"
        self.itemconfig(self.bar, fill=col)

class SystemMonitorModule:
    ICON = "💻"
    PRIORITY = 9
    
    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self.is_monitoring = True
        self.update_interval = 2 
        self._destroyed = False
        
        self.gpu_handle = None
        self.gpu_available = self.check_gpu_support()
        
        self.disk_widgets = {}
        self.core_bars = [] 
        
        self.create_ui()
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def check_gpu_support(self):
        try:
            import pynvml
            pynvml.nvmlInit()
            if pynvml.nvmlDeviceGetCount() > 0:
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                return True
        except: pass
        return False
    
    def create_ui(self):
        self.main_container = tk.Frame(self.parent, bg=self.colors['background'])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(self.main_container, bg=self.colors['background'], pady=15, padx=20)
        header.pack(fill=tk.X)
        tk.Label(header, text="System Monitor", font=("Segoe UI", 24, "bold"),
                 bg=self.colors['background'], fg="white").pack(side=tk.LEFT)

        # Canvas
        canvas = tk.Canvas(self.main_container, bg=self.colors['background'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=self.colors['background'])
        
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas = canvas

        # Grid Layout
        self.scroll_frame.columnconfigure(0, weight=1)
        self.scroll_frame.columnconfigure(1, weight=1)
        
        left_col = tk.Frame(self.scroll_frame, bg=self.colors['background'])
        left_col.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        right_col = tk.Frame(self.scroll_frame, bg=self.colors['background'])
        right_col.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Widgets
        self.create_cpu_card(left_col)
        self.create_ram_card(left_col)
        self.create_gpu_card(left_col)
        self.create_disk_card(right_col)
        self.create_process_card(right_col)

    def create_modern_card(self, parent, title, icon="📊"):
        card = tk.Frame(parent, bg=self.colors['card_bg'])
        card.pack(fill=tk.X, pady=10)
        strip = tk.Frame(card, bg=self.colors['accent'], width=4)
        strip.pack(side=tk.LEFT, fill=tk.Y)
        content = tk.Frame(card, bg=self.colors['card_bg'], padx=15, pady=15)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        header = tk.Frame(content, bg=self.colors['card_bg'])
        header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header, text=f"{icon}  {title}", font=("Segoe UI", 12, "bold"),
                 bg=self.colors['card_bg'], fg="white").pack(side=tk.LEFT)
        return content

    def create_cpu_card(self, parent):
        card = self.create_modern_card(parent, "CPU Processor", "🔥")
        
        # Grid for Stats (Usage | Speed | Temp)
        stats_frame = tk.Frame(card, bg=self.colors['card_bg'])
        stats_frame.pack(fill=tk.X)
        
        # Usage (Big)
        self.cpu_label = tk.Label(stats_frame, text="0.0%", font=("Segoe UI", 28, "bold"),
                                  bg=self.colors['card_bg'], fg=self.colors['accent'])
        self.cpu_label.pack(side=tk.LEFT)
        
        # Speed & Temp (Small, Right aligned)
        details_frame = tk.Frame(stats_frame, bg=self.colors['card_bg'])
        details_frame.pack(side=tk.RIGHT, anchor="e")
        
        self.cpu_freq_lbl = tk.Label(details_frame, text="0.00 GHz", font=("Segoe UI", 11),
                                     bg=self.colors['card_bg'], fg="white")
        self.cpu_freq_lbl.pack(anchor="e")
        
        self.cpu_temp_lbl = tk.Label(details_frame, text="", font=("Segoe UI", 10),
                                     bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        self.cpu_temp_lbl.pack(anchor="e")

        self.cpu_bar = ModernProgressBar(card, height=12, bg_color=self.colors['secondary'], fill_color=self.colors['accent'])
        self.cpu_bar.pack(fill=tk.X, pady=(5, 10))
        
        # Mini Cores
        tk.Label(card, text="Core Load", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'], fg="white").pack(anchor="w")
        self.cores_frame = tk.Frame(card, bg=self.colors['card_bg'])
        self.cores_frame.pack(fill=tk.X, pady=5)

    def create_ram_card(self, parent):
        card = self.create_modern_card(parent, "Memory (RAM)", "🧠")
        info = tk.Frame(card, bg=self.colors['card_bg'])
        info.pack(fill=tk.X)
        self.ram_label = tk.Label(info, text="0/0 GB", font=("Segoe UI", 16, "bold"), bg=self.colors['card_bg'], fg="white")
        self.ram_label.pack(side=tk.LEFT)
        self.ram_percent_label = tk.Label(info, text="0%", font=("Segoe UI", 12), bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        self.ram_percent_label.pack(side=tk.RIGHT, anchor="s", pady=(0,4))
        self.ram_bar = ModernProgressBar(card, height=12, bg_color=self.colors['secondary'], fill_color="#10B981")
        self.ram_bar.pack(fill=tk.X, pady=(5, 0))

    def create_gpu_card(self, parent):
        card = self.create_modern_card(parent, "Graphics (GPU)", "🎮")
        
        if not self.gpu_available:
            tk.Label(card, text="No NVIDIA GPU Detected", font=("Segoe UI", 10, "italic"),
                     bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(anchor="w")
            return

        self.gpu_name_label = tk.Label(card, text="Loading...", font=("Segoe UI", 11, "bold"), bg=self.colors['card_bg'], fg="white")
        self.gpu_name_label.pack(anchor="w")
        
        stats_grid = tk.Frame(card, bg=self.colors['card_bg'])
        stats_grid.pack(fill=tk.X, pady=10)
        
        tk.Label(stats_grid, text="Load:", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dim']).grid(row=0, column=0, sticky="w")
        self.gpu_load_val = tk.Label(stats_grid, text="0%", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'], fg="white")
        self.gpu_load_val.grid(row=0, column=1, sticky="w", padx=10)
        
        tk.Label(stats_grid, text="Temp:", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dim']).grid(row=0, column=2, sticky="w", padx=(20,0))
        self.gpu_temp_val = tk.Label(stats_grid, text="0°C", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'], fg="white")
        self.gpu_temp_val.grid(row=0, column=3, sticky="w", padx=10)

        # VRAM
        tk.Label(card, text="VRAM Usage", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'], fg="white").pack(anchor="w", pady=(15,2))
        vram_info = tk.Frame(card, bg=self.colors['card_bg'])
        vram_info.pack(fill=tk.X)
        self.vram_text = tk.Label(vram_info, text="0 / 0 GB", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text'])
        self.vram_text.pack(side=tk.LEFT)
        self.gpu_vram_bar = ModernProgressBar(card, height=8, bg_color=self.colors['secondary'], fill_color="#8B5CF6")
        self.gpu_vram_bar.pack(fill=tk.X, pady=(2,10))

        # GPU Processes
        tk.Label(card, text="Top VRAM Consumers:", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dim']).pack(anchor="w")
        self.gpu_procs_lbl = tk.Label(card, text="-", font=("Consolas", 9), bg=self.colors['card_bg'], fg=self.colors['text'], justify=tk.LEFT)
        self.gpu_procs_lbl.pack(anchor="w", pady=(2,0))

    def create_disk_card(self, parent):
        self.disk_container = self.create_modern_card(parent, "Storage Drives", "💾")
        self.disks_inner_frame = tk.Frame(self.disk_container, bg=self.colors['card_bg'])
        self.disks_inner_frame.pack(fill=tk.BOTH, expand=True)

    def create_process_card(self, parent):
        card = self.create_modern_card(parent, "Top Processes", "⚡")
        tk.Label(card, text="By CPU Usage", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['accent']).pack(anchor="w")
        self.cpu_proc_label = tk.Label(card, text="Loading...", font=("Consolas", 9), bg=self.colors['card_bg'], fg=self.colors['text'], justify=tk.LEFT)
        self.cpu_proc_label.pack(anchor="w", pady=(0, 15))
        
        tk.Label(card, text="By RAM Usage", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg="#10B981").pack(anchor="w")
        self.ram_proc_label = tk.Label(card, text="Loading...", font=("Consolas", 9), bg=self.colors['card_bg'], fg=self.colors['text'], justify=tk.LEFT)
        self.ram_proc_label.pack(anchor="w")

        self.sys_uptime_lbl = tk.Label(card, text="", font=("Segoe UI", 9, "italic"), bg=self.colors['card_bg'], fg=self.colors['text_dim'])
        self.sys_uptime_lbl.pack(anchor="e", pady=(10,0))

    # --- MONITOR LOGIC ---
    def monitor_loop(self):
        while self.is_monitoring and not self._destroyed:
            try:
                cpu_p = psutil.cpu_percent(interval=1)
                cpu_cores = psutil.cpu_percent(interval=0.1, percpu=True)
                # Frequency
                try: cpu_freq = psutil.cpu_freq().current
                except: cpu_freq = 0
                
                # Temperature (Linux only usually, or requires OpenHardwareMonitor on Windows)
                cpu_temp = "N/A"
                if hasattr(psutil, "sensors_temperatures"):
                    try:
                        temps = psutil.sensors_temperatures()
                        if 'coretemp' in temps: cpu_temp = f"{temps['coretemp'][0].current}°C"
                        elif 'cpu' in temps: cpu_temp = f"{temps['cpu'][0].current}°C"
                    except: pass

                ram = psutil.virtual_memory()
                disks = self.get_all_disks()
                top_cpu = self.get_top_processes_by_cpu()
                top_ram = self.get_top_processes_by_ram()
                gpu = self.get_gpu_stats() if self.gpu_available else None
                
                if self._destroyed: break
                self.parent.after(0, lambda: self.update_display(
                    cpu_p, cpu_cores, cpu_freq, cpu_temp, ram, disks, top_cpu, top_ram, gpu
                ))
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Monitor: {e}")
                break

    def update_display(self, cpu_p, cpu_cores, cpu_freq, cpu_temp, ram, disks, top_cpu, top_ram, gpu):
        if self._destroyed: return
        try: scroll_pos = self.canvas.yview()[0]
        except: scroll_pos = 0.0

        try:
            # CPU
            self.cpu_label.config(text=f"{cpu_p:.1f}%")
            self.cpu_bar.set_value(cpu_p)
            self.cpu_freq_lbl.config(text=f"{cpu_freq/1000:.2f} GHz" if cpu_freq > 1000 else f"{cpu_freq:.0f} MHz")
            if cpu_temp != "N/A": self.cpu_temp_lbl.config(text=cpu_temp)
            
            # CPU Cores
            if not self.core_bars and self.cores_frame.winfo_exists():
                num_cores = len(cpu_cores)
                cols = 8 if num_cores >= 8 else num_cores
                for i in range(num_cores):
                    bar = MiniCoreBar(self.cores_frame, width=20, height=35, bg_color=self.colors['secondary'])
                    bar.grid(row=i//cols, column=i%cols, padx=2, pady=2)
                    self.core_bars.append(bar)
            for i, bar in enumerate(self.core_bars):
                if i < len(cpu_cores): bar.set_value(cpu_cores[i])

            # RAM
            used_gb = ram.used / (1024**3)
            total_gb = ram.total / (1024**3)
            self.ram_label.config(text=f"{used_gb:.1f} / {total_gb:.1f} GB")
            self.ram_percent_label.config(text=f"{ram.percent}%")
            self.ram_bar.set_value(ram.percent)

            # GPU
            if self.gpu_available and gpu:
                self.gpu_name_label.config(text=gpu['name'])
                self.gpu_load_val.config(text=f"{gpu['load']:.0f}%")
                self.gpu_temp_val.config(text=f"{gpu['temperature']}°C")
                self.vram_text.config(text=f"{gpu['memory_used']:.1f} / {gpu['memory_total']:.1f} GB")
                self.gpu_vram_bar.set_value(gpu['memory_percent'])
                self.gpu_procs_lbl.config(text=gpu['processes'])

            self.update_disks_display(disks)
            self.cpu_proc_label.config(text=self.format_process_list(top_cpu, 'cpu'))
            self.ram_proc_label.config(text=self.format_process_list(top_ram, 'ram'))
            
            uptime = time.time() - psutil.boot_time()
            self.sys_uptime_lbl.config(text=f"Uptime: {int(uptime/3600)}h {int((uptime%3600)/60)}m")
            self.canvas.yview_moveto(scroll_pos)

        except Exception: self._destroyed = True

    def update_disks_display(self, disks):
        current_ids = set(d['device'] for d in disks)
        existing_ids = set(self.disk_widgets.keys())
        
        if current_ids != existing_ids:
            for w in self.disks_inner_frame.winfo_children(): w.destroy()
            self.disk_widgets = {}
            for disk in disks:
                f = tk.Frame(self.disks_inner_frame, bg=self.colors['card_bg'])
                f.pack(fill=tk.X, pady=5)
                
                name = disk['device']
                mount = disk['mountpoint']
                # FIXED: Logic to remove redundant C:\ C:
                if name.rstrip(':\\') == mount.rstrip(':\\'): display_text = f"{name}"
                else: display_text = f"{name} ({mount})"

                tk.Label(f, text=display_text, font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg="white").pack(anchor="w")
                lbl = tk.Label(f, text="", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dim'])
                lbl.pack(anchor="w")
                bar = ModernProgressBar(f, height=8, bg_color=self.colors['secondary'], fill_color="#F59E0B")
                bar.pack(fill=tk.X, pady=(2,0))
                self.disk_widgets[disk['device']] = (lbl, bar)

        for disk in disks:
            if disk['device'] in self.disk_widgets:
                lbl, bar = self.disk_widgets[disk['device']]
                u = disk['usage']
                free_gb = u.free / (1024**3)
                lbl.config(text=f"{free_gb:.0f} GB free • {u.percent}% used")
                bar.set_value(u.percent)

    # --- HELPERS ---
    def get_all_disks(self):
        d = []
        for p in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(p.mountpoint)
                d.append({'device': p.device, 'mountpoint': p.mountpoint, 'usage': u})
            except: pass
        return d

    def get_top_processes_by_cpu(self):
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent']):
            try:
                if p.info['cpu_percent'] > 0: 
                    p.info['name'] = p.info['name'][:20]
                    procs.append(p.info)
            except: pass
        return sorted(procs, key=lambda x: x['cpu_percent'], reverse=True)[:5]

    def get_top_processes_by_ram(self):
        procs = []
        for p in psutil.process_iter(['name', 'memory_percent']):
            try:
                if p.info['memory_percent'] > 0: 
                    p.info['name'] = p.info['name'][:20]
                    procs.append(p.info)
            except: pass
        return sorted(procs, key=lambda x: x['memory_percent'], reverse=True)[:5]

    def get_gpu_stats(self):
        try:
            import pynvml
            h = self.gpu_handle
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            temp = pynvml.nvmlDeviceGetTemperature(h, 0)
            name = pynvml.nvmlDeviceGetName(h)
            if isinstance(name, bytes): name = name.decode('utf-8')
            
            # --- VRAM PROCESSES (Safe Mode) ---
            procs_list = []
            try:
                running_procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(h) or []
                compute_procs = pynvml.nvmlDeviceGetComputeRunningProcesses(h) or []
                all_gpu_procs = list(running_procs) + list(compute_procs)
                all_gpu_procs.sort(key=lambda p: p.usedGpuMemory, reverse=True)
                
                for p in all_gpu_procs[:5]:
                    try:
                        # SAFE GUARD: Wrap process name fetching
                        p_name = psutil.Process(p.pid).name()
                    except: 
                        p_name = f"PID {p.pid}"
                    
                    mem_usage = p.usedGpuMemory / (1024**2) # MB
                    procs_list.append(f"{p_name[:15]:<15} {mem_usage:.0f} MB")
            except Exception:
                procs_list = ["(Access Denied)"]

            return {
                'name': name,
                'load': util.gpu,
                'memory_used': mem.used / (1024**3),
                'memory_total': mem.total / (1024**3),
                'memory_percent': (mem.used / mem.total) * 100,
                'temperature': temp,
                'processes': "\n".join(procs_list) if procs_list else "No active GPU apps"
            }
        except: return None

    def format_process_list(self, procs, key):
        if not procs: return "-"
        lines = []
        for p in procs:
            val = p['cpu_percent'] if key == 'cpu' else p['memory_percent']
            lines.append(f"{p['name']:<20} {val:>5.1f}%")
        return "\n".join(lines)