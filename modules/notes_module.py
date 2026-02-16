import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import time
import uuid
import re
import zipfile
from datetime import datetime

class NotesModule:
    ICON = "🗒️"
    PRIORITY = 7

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        
        # Configuration
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.data_file = os.path.join(self.data_dir, 'notes.json')
        self.default_categories = ["general", "work", "personal", "ideas"]
        
        # State
        self.notes = []
        self.categories = []
        self.current_note_id = None
        self.search_timer = None
        
        # Initialize Data
        self.ensure_data_directory()
        self.load_data()
        
        # UI Setup
        self.create_ui()
        
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notes = data.get('notes', [])
                    self.categories = data.get('categories', self.default_categories)
            except Exception as e:
                print(f"Error loading notes: {e}")
                self.notes = []
                self.categories = self.default_categories
        else:
            self.notes = []
            self.categories = self.default_categories
            self.save_data()

    def save_data(self):
        data = {
            "notes": self.notes,
            "categories": self.categories
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def create_ui(self):
        # Main Layout: PanedWindow for resizable split view
        self.paned_window = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL, bg=self.colors['background'], sashwidth=4)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # --- LEFT PANEL: List & Filters ---
        self.left_panel = tk.Frame(self.paned_window, bg=self.colors['secondary'], width=250)
        self.paned_window.add(self.left_panel)
        
        # Header / Controls
        control_frame = tk.Frame(self.left_panel, bg=self.colors['secondary'], pady=5, padx=5)
        control_frame.pack(fill=tk.X)
        
        # New Note Button
        tk.Button(control_frame, text="+ New Note", bg=self.colors['accent'], fg="white",
                 font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                 command=self.create_new_note).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Search Box
        search_frame = tk.Frame(self.left_panel, bg=self.colors['secondary'], padx=5, pady=5)
        search_frame.pack(fill=tk.X)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                   bg=self.colors['card_bg'], fg=self.colors['text'],
                                   insertbackground=self.colors['text'], relief=tk.FLAT)
        self.search_entry.pack(fill=tk.X)
        # Placeholder text logic could go here, keeping it simple for now
        
        # Category Filter
        self.category_filter_var = tk.StringVar(value="All Categories")
        cat_options = ["All Categories"] + self.categories
        self.cat_filter = ttk.Combobox(search_frame, textvariable=self.category_filter_var, 
                                     values=cat_options, state="readonly")
        self.cat_filter.pack(fill=tk.X, pady=(5, 0))
        self.cat_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_note_list())

        # Note List (Canvas + Scrollbar)
        list_frame = tk.Frame(self.left_panel, bg=self.colors['secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(list_frame, bg=self.colors['secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['secondary'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=230) # width tweaks needed
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- RIGHT PANEL: Editor ---
        self.right_panel = tk.Frame(self.paned_window, bg=self.colors['content_bg'])
        self.paned_window.add(self.right_panel)
        
        # Editor Header
        self.editor_header = tk.Frame(self.right_panel, bg=self.colors['content_bg'], pady=10, padx=10)
        self.editor_header.pack(fill=tk.X)
        
        # Title Entry
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(self.editor_header, textvariable=self.title_var,
                                  font=("Segoe UI", 16, "bold"), bg=self.colors['content_bg'],
                                  fg=self.colors['text'], insertbackground=self.colors['text'],
                                  relief=tk.FLAT)
        self.title_entry.pack(fill=tk.X)
        
        # Metadata Row (Category, Pinned)
        meta_frame = tk.Frame(self.editor_header, bg=self.colors['content_bg'])
        meta_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(meta_frame, text="Category:", bg=self.colors['content_bg'], fg=self.colors['text_dim']).pack(side=tk.LEFT)
        self.editor_cat_var = tk.StringVar()
        self.editor_cat = ttk.Combobox(meta_frame, textvariable=self.editor_cat_var, values=self.categories, width=15)
        self.editor_cat.pack(side=tk.LEFT, padx=5)
        
        self.is_pinned_var = tk.BooleanVar()
        tk.Checkbutton(meta_frame, text="📌 Pin Note", variable=self.is_pinned_var,
                      bg=self.colors['content_bg'], fg=self.colors['text'],
                      selectcolor=self.colors['card_bg'], activebackground=self.colors['content_bg'],
                      activeforeground=self.colors['text']).pack(side=tk.LEFT, padx=10)

        # Action Buttons
        btn_frame = tk.Frame(self.editor_header, bg=self.colors['content_bg'])
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="🗑️", command=self.delete_current_note,
                 bg=self.colors['danger'], fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="💾 Save", command=self.save_current_note,
                 bg=self.colors['success'], fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="👁️ Preview", command=self.toggle_preview,
                 bg=self.colors['primary'], fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="📤 Export", command=self.open_export_menu,
                 bg=self.colors['card_bg'], fg=self.colors['text'], relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)

        # Editor Body (Text Area)
        self.text_frame = tk.Frame(self.right_panel, bg=self.colors['content_bg'], padx=10, pady=5)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_editor = tk.Text(self.text_frame, font=("Consolas", 11),
                                 bg=self.colors['card_bg'], fg=self.colors['text'],
                                 insertbackground=self.colors['text'], relief=tk.FLAT,
                                 padx=10, pady=10)
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        
        # Preview Widget (Hidden initially)
        self.preview_widget = tk.Text(self.text_frame, font=("Segoe UI", 11),
                                    bg=self.colors['content_bg'], fg=self.colors['text'],
                                    relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED)
        
        # Setup Markdown Tags
        self.setup_markdown_tags()

        # Initial Load
        self.refresh_note_list()
        
    def setup_markdown_tags(self):
        # Configure tags for the preview widget
        self.preview_widget.tag_configure("h1", font=("Segoe UI", 20, "bold"), foreground=self.colors['accent'])
        self.preview_widget.tag_configure("h2", font=("Segoe UI", 16, "bold"), foreground=self.colors['text'])
        self.preview_widget.tag_configure("h3", font=("Segoe UI", 13, "bold"), foreground=self.colors['text_dim'])
        self.preview_widget.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.preview_widget.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        self.preview_widget.tag_configure("code", font=("Consolas", 10), background=self.colors['card_bg'])
        self.preview_widget.tag_configure("bullet", lmargin1=20, lmargin2=30)
    
    # --- Logic ---

    def create_new_note(self):
        new_id = f"note_{int(time.time()*1000)}"
        new_note = {
            "id": new_id,
            "title": "Untitled Note",
            "content": "",
            "category": "general",
            "tags": [],
            "pinned": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.notes.insert(0, new_note) # Add to top
        self.save_data()
        self.refresh_note_list()
        self.load_note_to_editor(new_id)

    def on_search_change(self, *args):
        # Debounce logic
        if self.search_timer:
            self.parent.after_cancel(self.search_timer)
        self.search_timer = self.parent.after(300, self.refresh_note_list)

    def refresh_note_list(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        search_query = self.search_var.get().lower()
        cat_filter = self.category_filter_var.get()
        
        filtered_notes = []
        for note in self.notes:
            # Category Filter
            if cat_filter != "All Categories" and note.get('category') != cat_filter:
                continue
                
            # Search Filter
            if search_query:
                content_match = search_query in note.get('content', '').lower()
                title_match = search_query in note.get('title', '').lower()
                if not (content_match or title_match):
                    continue
            
            filtered_notes.append(note)
            
        # Sort: Pinned first, then by updated_at desc
        filtered_notes.sort(key=lambda x: (not x.get('pinned', False), x.get('updated_at', '')), reverse=True)
        
        for note in filtered_notes:
            self.create_note_card(note)

    def create_note_card(self, note):
        bg_color = self.colors['card_bg']
        if note['id'] == self.current_note_id:
            bg_color = self.colors['accent']
            
        card = tk.Frame(self.scrollable_frame, bg=bg_color, pady=5, padx=5)
        card.pack(fill=tk.X, pady=2)
        
        # Click event handler
        def on_click(e):
            self.load_note_to_editor(note['id'])
            
        card.bind("<Button-1>", on_click)
        
        # Title
        title_text = f"{'📌 ' if note.get('pinned') else ''}{note.get('title', 'Untitled')}"
        lbl_title = tk.Label(card, text=title_text, font=("Segoe UI", 10, "bold"),
                           bg=bg_color, fg="white" if bg_color == self.colors['accent'] else self.colors['text'],
                           anchor="w")
        lbl_title.pack(fill=tk.X)
        lbl_title.bind("<Button-1>", on_click)
        
        # Date / Category
        date_str = note.get('updated_at', '')[:10]
        sub_text = f"{date_str} • {note.get('category', 'general')}"
        lbl_sub = tk.Label(card, text=sub_text, font=("Segoe UI", 8),
                         bg=bg_color, fg="white" if bg_color == self.colors['accent'] else self.colors['text_dim'],
                         anchor="w")
        lbl_sub.pack(fill=tk.X)
        lbl_sub.bind("<Button-1>", on_click)

    def load_note_to_editor(self, note_id):
        # Save current if exists
        if self.current_note_id:
            self.save_current_note(refresh_list=False)
            
        self.current_note_id = note_id
        
        # Find note data
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if not note:
            return
            
        # Update UI Vars
        self.title_var.set(note.get('title', ''))
        self.editor_cat_var.set(note.get('category', 'general'))
        self.is_pinned_var.set(note.get('pinned', False))
        
        # Update Text Editor
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", note.get('content', ''))
        
        # Switch to edit mode if in preview
        if self.preview_widget.winfo_ismapped():
            self.toggle_preview()
            
        # Refresh list to highlight selection
        self.refresh_note_list()

    def save_current_note(self, refresh_list=True):
        if not self.current_note_id:
            return
            
        note = next((n for n in self.notes if n['id'] == self.current_note_id), None)
        if note:
            note['title'] = self.title_var.get()
            note['category'] = self.editor_cat_var.get()
            note['pinned'] = self.is_pinned_var.get()
            note['content'] = self.text_editor.get("1.0", tk.END).strip()
            note['updated_at'] = datetime.now().isoformat()
            
            # Auto-add new category if it doesn't exist
            if note['category'] not in self.categories:
                self.categories.append(note['category'])
                self.cat_filter['values'] = ["All Categories"] + self.categories
                self.editor_cat['values'] = self.categories
            
            self.save_data()
            if refresh_list:
                self.refresh_note_list()

    def delete_current_note(self):
        if not self.current_note_id:
            return
            
        if messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
            self.notes = [n for n in self.notes if n['id'] != self.current_note_id]
            self.save_data()
            self.current_note_id = None
            self.title_var.set("")
            self.text_editor.delete("1.0", tk.END)
            self.refresh_note_list()

    def toggle_preview(self):
        if self.preview_widget.winfo_ismapped():
            # Switch to Editor
            self.preview_widget.pack_forget()
            self.text_editor.pack(fill=tk.BOTH, expand=True)
        else:
            # Switch to Preview
            content = self.text_editor.get("1.0", tk.END)
            self.render_markdown(content)
            self.text_editor.pack_forget()
            self.preview_widget.pack(fill=tk.BOTH, expand=True)

    def render_markdown(self, text):
        self.preview_widget.config(state=tk.NORMAL)
        self.preview_widget.delete("1.0", tk.END)
        
        lines = text.split('\n')
        for line in lines:
            tags = []
            
            # Headers
            if line.startswith('# '):
                tags.append("h1")
                line = line[2:]
            elif line.startswith('## '):
                tags.append("h2")
                line = line[3:]
            elif line.startswith('### '):
                tags.append("h3")
                line = line[4:]
            # List items
            elif line.strip().startswith('- '):
                tags.append("bullet")
                # Don't strip the dash here, looks better with it or replace with dot
                
            self.preview_widget.insert(tk.END, line + "\n", tags)
            
            # Inline formatting (Bold) - Simple regex approach
            # Note: This is a simplified renderer. It applies to the last inserted line.
            # Real-time complex parsing requires a full parser, this is "good enough" for Phase 2.
            
            # Apply bold to **text**
            # (In a real implementation, we'd search ranges in the widget, 
            #  but for simplicity we just render plain text with block tags first)
            
        self.preview_widget.config(state=tk.DISABLED)

    # ── Export ────────────────────────────────────────────────────────────────

    def open_export_menu(self):
        """Show a small popup with export options."""
        menu = tk.Menu(self.parent, tearoff=0,
                       bg=self.colors['card_bg'], fg=self.colors['text'],
                       activebackground=self.colors['accent'], activeforeground="white")
        menu.add_command(label="📄  Export current note as Markdown (.md)", command=self.export_current_md)
        menu.add_command(label="📃  Export current note as Text (.txt)",    command=self.export_current_txt)
        menu.add_separator()
        menu.add_command(label="🗂️  Export ALL notes as ZIP (.zip of .md)", command=self.export_all_zip)
        try:
            x = self.parent.winfo_rootx() + 200
            y = self.parent.winfo_rooty() + 80
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _safe_filename(self, title: str) -> str:
        """Strip characters that are illegal in filenames."""
        return re.sub(r'[\\/:*?"<>|]', '_', title).strip() or "untitled"

    def _get_current_note(self):
        """Return the current note dict, or None."""
        if not self.current_note_id:
            messagebox.showwarning("No Note Selected", "Please open a note before exporting.")
            return None
        return next((n for n in self.notes if n['id'] == self.current_note_id), None)

    def export_current_md(self):
        note = self._get_current_note()
        if not note:
            return
        default_name = self._safe_filename(note.get('title', 'note')) + ".md"
        path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialfile=default_name,
            title="Export Note as Markdown"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"# {note.get('title', 'Untitled')}\n\n")
                f.write(note.get('content', ''))
            messagebox.showinfo("Exported", f"Note saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_current_txt(self):
        note = self._get_current_note()
        if not note:
            return
        default_name = self._safe_filename(note.get('title', 'note')) + ".txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
            title="Export Note as Text"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"{note.get('title', 'Untitled')}\n")
                f.write("=" * len(note.get('title', 'Untitled')) + "\n\n")
                f.write(note.get('content', ''))
            messagebox.showinfo("Exported", f"Note saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def export_all_zip(self):
        if not self.notes:
            messagebox.showinfo("No Notes", "There are no notes to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip"), ("All files", "*.*")],
            initialfile="notes_export.zip",
            title="Export All Notes as ZIP"
        )
        if not path:
            return
        try:
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                seen_names = {}
                for note in self.notes:
                    base = self._safe_filename(note.get('title', 'untitled'))
                    count = seen_names.get(base, 0)
                    fname = f"{base}.md" if count == 0 else f"{base}_{count}.md"
                    seen_names[base] = count + 1
                    content = f"# {note.get('title', 'Untitled')}\n\n{note.get('content', '')}"
                    zf.writestr(fname, content)
            messagebox.showinfo("Exported", f"All {len(self.notes)} notes saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))