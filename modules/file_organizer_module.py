"""
File Organizer Module for Thunderz Assistant
Version: 1.0.0

Automatically organize messy folders by file type!
Perfect for cleaning up Downloads folders.

Features:
- Scan any folder and see file type breakdown
- Automatically categorize files into folders
- Preview changes before organizing
- Undo last organization
- Safe mode: handles duplicates and conflicts
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class FileOrganizerModule:
    """
    File Organizer Module
    
    This module helps organize messy folders by automatically sorting files
    into category folders based on their file extensions.
    
    How it works:
    1. User selects a folder to organize
    2. Module scans and shows file type breakdown
    3. User clicks "Organize" to move files into category folders
    4. Module tracks moves so you can undo if needed
    """
    ICON = "📁"
    PRIORITY = 6

    def __init__(self, parent, colors):
        self.parent = parent
        
        # Map main.py colors to the keys we use
        # main.py uses: 'background', 'content_bg', 'card_bg', 'text', 'text_dim', 'accent'
        # We need: 'bg_dark', 'bg_medium', 'text', 'text_secondary', 'accent', 'success', 'warning'
        self.colors = {
            'bg_dark': colors.get('background', '#0F172A'),
            'bg_medium': colors.get('card_bg', '#334155'),
            'bg_light': colors.get('content_bg', "#F70606"),
            'text': colors.get('text', '#E2E8F0'),
            'text_secondary': colors.get('text_dim', '#94A3B8'),
            'accent': colors.get('accent', '#3B82F6'),
            'success': '#10B981',  # Green for success
            'warning': '#F59E0B',  # Orange for warning
        }
        
        self.name = "File Organizer"
        
        # FORBIDDEN FOLDERS - NEVER organize these!
        # These are critical system folders that should never be touched
        self.forbidden_folders = [
            # Windows system folders
            'C:\\Windows',
            'C:\\Windows\\System32',
            'C:\\Windows\\SysWOW64',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\ProgramData',
            'C:\\Users\\All Users',
            'C:\\$Recycle.Bin',
            
            # User system folders (we'll add username dynamically)
            os.path.join(str(Path.home()), 'AppData'),
            os.path.join(str(Path.home()), 'AppData', 'Local'),
            os.path.join(str(Path.home()), 'AppData', 'Roaming'),
            os.path.join(str(Path.home()), 'AppData', 'LocalLow'),
            
            # macOS system folders
            '/System',
            '/Library',
            '/Applications',
            '/usr',
            '/bin',
            '/sbin',
            '/var',
            '/private',
            
            # Linux system folders
            '/boot',
            '/dev',
            '/etc',
            '/lib',
            '/lib64',
            '/proc',
            '/root',
            '/sys',
            '/tmp',
        ]
        
        # Normalize all paths for comparison (lowercase, forward slashes)
        self.forbidden_folders = [os.path.normpath(f).lower() for f in self.forbidden_folders]
        
        # File type categories
        # Each category maps to a list of file extensions
        self.categories = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xlsx', '.xls', '.pptx', '.ppt'],
            'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go'],
            'Executables': ['.exe', '.msi', '.bat', '.sh', '.app', '.deb', '.rpm'],
            'Other': []  # Catch-all for unknown types
        }
        
        # Current state
        self.current_folder = str(Path.home() / "Downloads")  # Default to Downloads
        self.scan_results = {}  # Will store file counts by category
        self.last_organization = None  # For undo functionality
        
        # Create the UI
        self.create_ui()
        
    def create_ui(self):
        """Create the user interface"""
        # Main container with dark theme
        self.frame = tk.Frame(self.parent, bg=self.colors['bg_dark'])
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            self.frame,
            text="📁 File Organizer",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors['bg_dark'],
            fg=self.colors['text']
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = tk.Label(
            self.frame,
            text="Automatically organize messy folders by file type",
            font=("Segoe UI", 11),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary']
        )
        desc_label.pack(pady=(0, 20))
        
        # Folder selection section
        folder_frame = tk.Frame(self.frame, bg=self.colors['bg_medium'])
        folder_frame.pack(fill="x", pady=(0, 20))
        
        folder_label = tk.Label(
            folder_frame,
            text="📂 Folder to Organize:",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_light'],
            fg=self.colors['text']
        )
        folder_label.pack(side="left", padx=10, pady=10)
        
        # Current folder display
        self.folder_var = tk.StringVar(value=self.current_folder)
        self.folder_label = tk.Label(
            folder_frame,
            textvariable=self.folder_var,
            font=("Segoe UI", 10),
            bg=self.colors['bg_dark'],
            fg=self.colors['text'],
            anchor="w",  # Left-align text
            padx=10,
            pady=5,
            relief="sunken",  # Makes it look like an input field
            borderwidth=1
        )
        self.folder_label.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        # Safety indicator
        self.safety_label = tk.Label(
            folder_frame,
            text="✅ Safe",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['success'],
            fg="white",
            padx=8,
            pady=2
        )
        self.safety_label.pack(side="left", padx=(0, 10), pady=10)
        
        # Browse button
        browse_btn = tk.Button(
            folder_frame,
            text="Browse",
            command=self.browse_folder,
            bg=self.colors['accent'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5
        )
        browse_btn.pack(side="left", padx=10, pady=10)
        
        # Scan button
        scan_btn = tk.Button(
            folder_frame,
            text="🔍 Scan",
            command=self.scan_folder,
            bg=self.colors['success'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief="flat",
            padx=15,
            pady=5
        )
        scan_btn.pack(side="left", padx=(0, 10), pady=10)
        
        # Results area (scrollable)
        results_frame = tk.Frame(self.frame, bg=self.colors['bg_dark'])
        results_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Canvas for scrolling
        canvas = tk.Canvas(results_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        
        self.results_container = tk.Frame(canvas, bg=self.colors['bg_dark'])
        self.results_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.results_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.show_initial_message()
        
        # Action buttons
        button_frame = tk.Frame(self.frame, bg=self.colors['bg_dark'])
        button_frame.pack(fill="x")
        
        # Organize button (disabled until scan)
        self.organize_btn = tk.Button(
            button_frame,
            text="✨ Organize Files",
            command=self.organize_files,
            bg=self.colors['accent'],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            relief="flat",
            padx=30,
            pady=10,
            state="disabled"
        )
        self.organize_btn.pack(side="left", padx=(0, 10))
        
        # Undo button (disabled until organization)
        self.undo_btn = tk.Button(
            button_frame,
            text="↩️ Undo Last Organization",
            command=self.undo_organization,
            bg=self.colors['warning'],
            fg="white",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            relief="flat",
            padx=30,
            pady=10,
            state="disabled"
        )
        self.undo_btn.pack(side="left")
    
    def show_initial_message(self):
        """Show welcome message before first scan"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        message = tk.Label(
            self.results_container,
            text="👆 Select a folder and click 'Scan' to get started!",
            font=("Segoe UI", 14),
            bg=self.colors['bg_dark'],
            fg=self.colors['text_secondary'],
            pady=40
        )
        message.pack()
    
    def is_folder_safe(self, folder_path):
        r"""
        Check if a folder is safe to organize.
        
        Returns:
            tuple: (is_safe: bool, reason: str)
        
        Safety checks:
        1. Folder must exist
        2. Folder must not be in forbidden list
        3. Folder must not be a parent of forbidden folders
        4. Folder must not be root drive (C:\, D:\, etc.)
        """
        # Normalize path for comparison
        folder_path_normalized = os.path.normpath(folder_path).lower()
        
        # Check 1: Folder exists
        if not os.path.exists(folder_path):
            return False, "Folder does not exist"
        
        # Check 2: Not a root drive (C:\, D:\, /)
        if os.path.splitdrive(folder_path_normalized)[1] in ['\\', '/'] or folder_path_normalized in ['/', '\\']:
            return False, "Cannot organize root drive! This would affect your entire system."
        
        # Check 3: Not in forbidden list
        for forbidden in self.forbidden_folders:
            # Exact match
            if folder_path_normalized == forbidden:
                return False, f"🚫 FORBIDDEN: This is a critical system folder!\n\n{folder_path}\n\nOrganizing this folder could damage your system."
            
            # Check if trying to organize a subfolder of a forbidden folder
            if folder_path_normalized.startswith(forbidden + os.sep):
                return False, f"🚫 FORBIDDEN: This is inside a system folder!\n\n{folder_path}\n\nThis folder is protected for your safety."
        
        # Check 4: Not a parent of forbidden folders (e.g., C:\ contains C:\Windows)
        for forbidden in self.forbidden_folders:
            if forbidden.startswith(folder_path_normalized + os.sep):
                return False, f"🚫 FORBIDDEN: This folder contains system folders!\n\n{folder_path}\n\nOrganizing this would affect critical system directories."
        
        return True, "Folder is safe to organize"
    
    def browse_folder(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(
            title="Select Folder to Organize",
            initialdir=self.current_folder
        )
        
        if folder:
            # Safety check
            is_safe, reason = self.is_folder_safe(folder)
            
            if not is_safe:
                messagebox.showerror(
                    "Unsafe Folder",
                    reason + "\n\n" +
                    "Please choose a safe folder like:\n" +
                    "• Downloads\n" +
                    "• Desktop\n" +
                    "• Documents\n" +
                    "• A project folder you created"
                )
                return
            
            # Folder is safe - update UI
            self.current_folder = folder
            self.folder_var.set(folder)  # Label updates automatically - no state changes needed!
            
            # Update safety indicator
            self.safety_label.config(text="✅ Safe", bg=self.colors['success'])
            
            # Reset scan results
            self.scan_results = {}
            self.organize_btn.config(state="disabled")
    
    def scan_folder(self):
        """
        Scan the selected folder and count files by category
        
        This function:
        1. Checks if folder is safe to organize
        2. Lists all files in the folder (not subdirectories)
        3. Categorizes each file by extension
        4. Counts files in each category
        5. Displays the results
        """
        # Safety check first!
        is_safe, reason = self.is_folder_safe(self.current_folder)
        
        if not is_safe:
            messagebox.showerror(
                "Unsafe Folder",
                reason + "\n\n" +
                "Please choose a safe folder like:\n" +
                "• Downloads\n" +
                "• Desktop\n" +
                "• Documents\n" +
                "• A project folder you created"
            )
            return
        
        if not os.path.exists(self.current_folder):
            messagebox.showerror("Error", "Folder does not exist!")
            return
        
        # Clear previous results
        self.scan_results = {category: [] for category in self.categories.keys()}
        
        try:
            # Get all files (not directories) in the folder
            files = [f for f in os.listdir(self.current_folder) 
                    if os.path.isfile(os.path.join(self.current_folder, f))]
            
            if not files:
                messagebox.showinfo("No Files", "This folder is empty!")
                return
            
            # Categorize each file
            for filename in files:
                ext = Path(filename).suffix.lower()  # Get extension (.txt, .jpg, etc.)
                categorized = False
                
                # Check which category this extension belongs to
                for category, extensions in self.categories.items():
                    if ext in extensions:
                        self.scan_results[category].append(filename)
                        categorized = True
                        break
                
                # If no category matched, put in "Other"
                if not categorized:
                    self.scan_results['Other'].append(filename)
            
            # Display results
            self.display_scan_results()
            
            # Enable organize button
            self.organize_btn.config(state="normal")
            
        except Exception as e:
            messagebox.showerror("Scan Error", f"Failed to scan folder:\n{str(e)}")
    
    def display_scan_results(self):
        """Display a dry-run preview table with per-file checkboxes."""
        for widget in self.results_container.winfo_children():
            widget.destroy()

        total_files = sum(len(files) for files in self.scan_results.values())

        # Header row
        hdr_frame = tk.Frame(self.results_container, bg=self.colors['bg_dark'])
        hdr_frame.pack(fill="x", padx=10, pady=(10, 4))
        tk.Label(hdr_frame, text=f"Preview — {total_files} files to organise",
                 font=("Segoe UI", 13, "bold"),
                 bg=self.colors['bg_dark'], fg=self.colors['text']).pack(side="left")

        # Select-all / none
        self._select_all_var = tk.BooleanVar(value=True)
        def _toggle_all():
            v = self._select_all_var.get()
            for var in self._preview_check_vars.values():
                var.set(v)
            self._refresh_organise_btn()

        tk.Checkbutton(hdr_frame, text="Select all",
                       variable=self._select_all_var, command=_toggle_all,
                       bg=self.colors['bg_dark'], fg=self.colors['text'],
                       selectcolor=self.colors['bg_medium'],
                       activebackground=self.colors['bg_dark'],
                       font=("Segoe UI", 10)).pack(side="right")

        # Scrollable table
        outer = tk.Frame(self.results_container, bg=self.colors['bg_dark'])
        outer.pack(fill="both", expand=True, padx=10, pady=4)
        tbl_canvas = tk.Canvas(outer, bg=self.colors['bg_dark'], highlightthickness=0)
        tbl_sb = ttk.Scrollbar(outer, orient="vertical", command=tbl_canvas.yview)
        tbl_inner = tk.Frame(tbl_canvas, bg=self.colors['bg_dark'])
        tbl_inner.bind("<Configure>", lambda e: tbl_canvas.configure(scrollregion=tbl_canvas.bbox("all")))
        tbl_canvas.create_window((0, 0), window=tbl_inner, anchor="nw")
        tbl_canvas.configure(yscrollcommand=tbl_sb.set)
        tbl_canvas.pack(side="left", fill="both", expand=True)
        tbl_sb.pack(side="right", fill="y")

        # Column headers
        icons = {'Images': '📷', 'Documents': '📄', 'Videos': '🎥', 'Audio': '🎵',
                 'Archives': '📦', 'Code': '💻', 'Executables': '⚙️', 'Other': '📁'}

        tk.Label(tbl_inner, text="✓", width=3, font=("Segoe UI", 10, "bold"),
                 bg=self.colors['bg_medium'], fg=self.colors['text']).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        tk.Label(tbl_inner, text="File name", font=("Segoe UI", 10, "bold"), anchor="w",
                 bg=self.colors['bg_medium'], fg=self.colors['text']).grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        tk.Label(tbl_inner, text="→  Destination folder", font=("Segoe UI", 10, "bold"), anchor="w",
                 bg=self.colors['bg_medium'], fg=self.colors['text']).grid(row=0, column=2, sticky="nsew", padx=1, pady=1)
        tbl_inner.columnconfigure(1, weight=1)
        tbl_inner.columnconfigure(2, weight=1)

        self._preview_check_vars = {}  # "Category/filename" → BooleanVar
        row_idx = 1
        for category, files in self.scan_results.items():
            if not files:
                continue
            icon = icons.get(category, '📁')
            dest_folder = os.path.join(self.current_folder, category)
            for filename in files:
                key = f"{category}/{filename}"
                var = tk.BooleanVar(value=True)
                self._preview_check_vars[key] = var
                row_bg = self.colors['bg_dark'] if row_idx % 2 == 0 else self.colors['bg_medium']

                cb = tk.Checkbutton(tbl_inner, variable=var,
                                    bg=row_bg, activebackground=row_bg,
                                    selectcolor=self.colors['bg_dark'],
                                    command=self._refresh_organise_btn)
                cb.grid(row=row_idx, column=0, sticky="nsew", padx=1, pady=1)

                tk.Label(tbl_inner, text=filename, font=("Segoe UI", 9), anchor="w",
                         bg=row_bg, fg=self.colors['text']).grid(row=row_idx, column=1, sticky="nsew", padx=4, pady=1)
                tk.Label(tbl_inner, text=f"{icon} {category}{os.sep}", font=("Segoe UI", 9),
                         anchor="w", bg=row_bg, fg=self.colors['accent']).grid(row=row_idx, column=2, sticky="nsew", padx=4, pady=1)
                row_idx += 1

        self._refresh_organise_btn()

    def _refresh_organise_btn(self):
        """Update Organise button label with checked count."""
        if not hasattr(self, '_preview_check_vars'):
            return
        count = sum(1 for v in self._preview_check_vars.values() if v.get())
        self.organize_btn.config(
            text=f"✨ Organise Selected ({count} files)",
            state="normal" if count > 0 else "disabled"
        )
    
    def create_category_card(self, category, files):
        """Create a card showing category info"""
        card = tk.Frame(
            self.results_container,
            bg=self.colors['bg_medium'],
            relief="flat"
        )
        card.pack(fill="x", padx=10, pady=5)
        
        # Category emoji/icon
        icons = {
            'Images': '📷',
            'Documents': '📄',
            'Videos': '🎥',
            'Audio': '🎵',
            'Archives': '📦',
            'Code': '💻',
            'Executables': '⚙️',
            'Other': '📁'
        }
        
        icon = icons.get(category, '📁')
        
        # Category label
        label = tk.Label(
            card,
            text=f"{icon} {category}",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text']
        )
        label.pack(side="left", padx=15, pady=10)
        
        # File count
        count_label = tk.Label(
            card,
            text=f"{len(files)} files",
            font=("Segoe UI", 11),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent']
        )
        count_label.pack(side="left", padx=5, pady=10)
        
        # Example files (show first 3)
        if len(files) > 0:
            examples = ", ".join(files[:3])
            if len(files) > 3:
                examples += f" (+{len(files) - 3} more)"
            
            example_label = tk.Label(
                card,
                text=examples,
                font=("Segoe UI", 9),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary']
            )
            example_label.pack(side="left", padx=15, pady=10)
    
    def organize_files(self):
        """
        Organize files into category folders
        
        This function:
        1. Creates category folders if they don't exist
        2. Moves files into appropriate folders
        3. Handles duplicate filenames
        4. Tracks moves for undo functionality
        """
        # Build the selected-file set from checkboxes
        check_vars = getattr(self, '_preview_check_vars', {})
        selected_keys = {k for k, v in check_vars.items() if v.get()} if check_vars else None

        # Count selected files
        if selected_keys is not None:
            total_files = len(selected_keys)
        else:
            total_files = sum(len(files) for files in self.scan_results.values())

        if total_files == 0:
            messagebox.showinfo("Nothing Selected", "No files are selected to organise.")
            return

        response = messagebox.askyesno(
            "Confirm Organisation",
            f"This will move {total_files} files into category folders.\n\n"
            f"Category folders will be created in:\n{self.current_folder}\n\n"
            "You can undo this action if needed.\n\nContinue?"
        )

        if not response:
            return

        # Track all moves for undo
        moves = []

        try:
            # Process each category
            for category, files in self.scan_results.items():
                if len(files) == 0:
                    continue

                # Create category folder
                category_path = os.path.join(self.current_folder, category)

                # Move each file (only if selected)
                for filename in files:
                    key = f"{category}/{filename}"
                    if selected_keys is not None and key not in selected_keys:
                        continue  # user unchecked this file
                    os.makedirs(category_path, exist_ok=True)
                    source = os.path.join(self.current_folder, filename)
                    destination = os.path.join(category_path, filename)
                    
                    # Handle duplicate filenames
                    if os.path.exists(destination):
                        # Add number to filename
                        base, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(category_path, f"{base}_{counter}{ext}")):
                            counter += 1
                        destination = os.path.join(category_path, f"{base}_{counter}{ext}")
                    
                    # Move the file
                    shutil.move(source, destination)
                    
                    # Track this move
                    moves.append({
                        'source': source,
                        'destination': destination
                    })
            
            # Save undo information
            self.last_organization = {
                'timestamp': datetime.now().isoformat(),
                'folder': self.current_folder,
                'moves': moves
            }
            
            # Enable undo button
            self.undo_btn.config(state="normal")
            
            # Show success message
            messagebox.showinfo(
                "Success!",
                f"✅ Organized {len(moves)} files!\n\n"
                f"Files have been moved to category folders in:\n{self.current_folder}"
            )
            
            # Clear results and disable organize button
            self.scan_results = {}
            self.organize_btn.config(state="disabled")
            self.show_initial_message()
            
        except Exception as e:
            messagebox.showerror("Organization Error", f"Failed to organize files:\n{str(e)}")
    
    def undo_organization(self):
        """
        Undo the last organization
        
        Moves all files back to their original locations
        """
        if not self.last_organization:
            messagebox.showinfo("Nothing to Undo", "No recent organization to undo.")
            return
        
        response = messagebox.askyesno(
            "Confirm Undo",
            f"This will move {len(self.last_organization['moves'])} files back to:\n"
            f"{self.last_organization['folder']}\n\n"
            "Continue?"
        )
        
        if not response:
            return
        
        try:
            # Move files back
            for move in self.last_organization['moves']:
                # Move from destination back to source
                if os.path.exists(move['destination']):
                    shutil.move(move['destination'], move['source'])
            
            messagebox.showinfo(
                "Undo Complete",
                f"✅ Moved {len(self.last_organization['moves'])} files back to original location!"
            )
            
            # Clear undo data and disable button
            self.last_organization = None
            self.undo_btn.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo organization:\n{str(e)}")
    
    def _is_alive(self):
        """Check if widget still exists (for safe updates)"""
        try:
            self.frame.winfo_exists()
            return True
        except:
            return False
