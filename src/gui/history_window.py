"""
Download History Window
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import COLORS, FONTS
from gui.styles import create_styled_button, create_styled_frame, create_styled_entry
from gui.progress_dialog import InlineStatus
from utils.config_manager import ConfigManager


class HistoryWindow:
    """Window for viewing download history"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Download History")
        self.window.geometry("900x600")
        self.window.configure(bg=COLORS["background"])
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.config = ConfigManager()
        self.all_history = []
        self.filtered_history = []
        self.filter_type = "all"  # all, video, mp3, profile
        
        self.create_widgets()
        self.load_history()
        self.center_window()
    
    def center_window(self):
        """Center window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create UI widgets"""
        # Header
        header = create_styled_frame(self.window, COLORS["background"])
        header.pack(pady=20, padx=30, fill="x")
        
        title = tk.Label(
            header,
            text="📜 Download History",
            font=FONTS["title"],
            bg=COLORS["background"],
            fg=COLORS["text"]
        )
        title.pack()
        
        # Main card
        card = create_styled_frame(self.window, COLORS["card"])
        card.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Filter and search bar
        filter_frame = tk.Frame(card, bg=COLORS["card"])
        filter_frame.pack(pady=(20, 10), padx=20, fill="x")
        
        # Filter buttons
        tk.Label(
            filter_frame,
            text="Filter:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        ).pack(side="left", padx=(0, 10))
        
        self.filter_all_btn = create_styled_button(
            filter_frame,
            text="📁 All",
            command=lambda: self.apply_filter("all"),
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        self.filter_all_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_video_btn = create_styled_button(
            filter_frame,
            text="🎬 Video",
            command=lambda: self.apply_filter("video"),
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        self.filter_video_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_mp3_btn = create_styled_button(
            filter_frame,
            text="🎵 MP3",
            command=lambda: self.apply_filter("mp3"),
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        self.filter_mp3_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_profile_btn = create_styled_button(
            filter_frame,
            text="👤 Profile",
            command=lambda: self.apply_filter("profile"),
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        self.filter_profile_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        # Search bar
        search_frame = tk.Frame(card, bg=COLORS["card"])
        search_frame.pack(pady=(0, 10), padx=20, fill="x")
        
        tk.Label(
            search_frame,
            text="Search:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        ).pack(side="left", padx=(0, 10))
        
        self.search_entry = create_styled_entry(search_frame, width=40)
        self.search_entry.pack(side="left", ipady=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.apply_search())
        
        # Status
        self.history_status = InlineStatus(card)
        self.history_status.pack(pady=5)
        
        # History list
        list_frame = tk.Frame(card, bg=COLORS["card"])
        list_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        self.history_listbox = tk.Listbox(
            list_frame,
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["text"],
            yscrollcommand=scrollbar.set,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"]
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Double-click and right-click bindings
        self.history_listbox.bind('<Double-Button-1>', self.open_file)
        self.history_listbox.bind('<Button-3>', self.show_context_menu)
        
        # Context menu
        self.context_menu = tk.Menu(self.window, tearoff=0, bg=COLORS["card"], fg=COLORS["text"])
        self.context_menu.add_command(label="📂 Open File", command=self.open_file)
        self.context_menu.add_command(label="📁 Open Folder", command=self.open_folder)
        self.context_menu.add_command(label="🔗 Copy URL", command=self.copy_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑 Delete Entry", command=self.delete_entry)
        
        # Buttons
        button_frame = tk.Frame(card, bg=COLORS["card"])
        button_frame.pack(pady=10, padx=20, fill="x")
        
        clear_btn = create_styled_button(
            button_frame,
            text="🗑 Clear History",
            command=self.clear_history,
            bg=COLORS["danger"],
            hover_bg=COLORS["danger_hover"]
        )
        clear_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        refresh_btn = create_styled_button(
            button_frame,
            text="🔄 Refresh",
            command=self.load_history,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        refresh_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        close_btn = create_styled_button(
            button_frame,
            text="✖ Close",
            command=self.window.destroy,
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        close_btn.pack(side="right", padx=5, ipadx=10, ipady=5)
    
    def apply_filter(self, filter_type):
        """Apply filter to history"""
        self.filter_type = filter_type
        
        # Update button colors
        self.filter_profile_btn.config(
            bg=COLORS["accent"] if filter_type == "profile" else COLORS["border"]
        )
        self.filter_all_btn.config(
            bg=COLORS["accent"] if filter_type == "all" else COLORS["border"]
        )
        self.filter_video_btn.config(
            bg=COLORS["accent"] if filter_type == "video" else COLORS["border"]
        )
        self.filter_mp3_btn.config(
            bg=COLORS["accent"] if filter_type == "mp3" else COLORS["border"]
        )
        
        self.load_history()
    
    def apply_search(self):
        """Apply search filter"""
        self.load_history()
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select item under cursor
        index = self.history_listbox.nearest(event.y)
        self.history_listbox.selection_clear(0, tk.END)
        self.history_listbox.selection_set(index)
        
        # Show menu
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def open_file(self, event=None):
        """Open selected file"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            file_path = item.get('path', '')
            
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                self.history_status.show_error("File not found")
    
    def open_folder(self):
        """Open folder containing file"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            file_path = item.get('path', '')
            
            if os.path.exists(file_path):
                folder = os.path.dirname(file_path)
                os.startfile(folder)
            else:
                self.history_status.show_error("File not found")
    
    def copy_url(self):
        """Copy URL to clipboard"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            url = item.get('url', '')
            
            try:
                import pyperclip
                pyperclip.copy(url)
                self.history_status.show_success("URL copied to clipboard")
            except:
                self.window.clipboard_clear()
                self.window.clipboard_append(url)
                self.history_status.show_success("URL copied to clipboard")
    
    def delete_entry(self):
        """Delete selected entry"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            
            confirm = messagebox.askyesno(
                "Confirm",
                f"Delete this entry?\n\n{item.get('title', 'Unknown')}"
            )
            
            if confirm:
                # Remove from all history
                self.all_history.remove(item)
                
                # Save updated history
                with open(self.config.history_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(self.all_history, f, indent=4)
                
                self.load_history()
                self.history_status.show_success("Entry deleted")
    
    def load_history(self):
        """Load download history with filters"""
        self.history_listbox.delete(0, tk.END)
        
        self.all_history = self.config.get_history()
        
        if not self.all_history:
            self.history_listbox.insert(tk.END, "No download history yet.")
            self.filtered_history = []
            return
        
        # Apply type filter
        if self.filter_type == "all":
            filtered = self.all_history
        elif self.filter_type == "video":
            filtered = [h for h in self.all_history if h.get('type', '').lower() == 'video' and h.get('source') != 'profile']
        elif self.filter_type == "mp3":
            filtered = [h for h in self.all_history if h.get('type', '').lower() == 'mp3' and h.get('source') != 'profile']
        elif self.filter_type == "profile":
            filtered = [h for h in self.all_history if h.get('source') == 'profile']
        else:
            filtered = self.all_history
        
        # Apply search filter
        search_text = self.search_entry.get().strip().lower()
        if search_text:
            filtered = [h for h in filtered if search_text in h.get('title', '').lower()]
        
        self.filtered_history = list(reversed(filtered))  # Show newest first
        
        # Populate listbox
        for item in self.filtered_history:
            entry = f"[{item.get('date', 'N/A')}] {item.get('title', 'Unknown')} - {item.get('type', 'N/A')}"
            self.history_listbox.insert(tk.END, entry)
        
        # Show count
        count = len(self.filtered_history)
        self.history_status.show_info(f"Showing {count} item{'s' if count != 1 else ''}")
    
    def clear_history(self):
        """Clear all history"""
        if not self.all_history:
            self.history_status.show_info("History is already empty")
            return
        
        confirm = messagebox.askyesno(
            "Confirm",
            "Are you sure you want to clear all download history?"
        )
        
        if confirm:
            self.config.clear_history()
            self.load_history()
            self.history_status.show_success("History cleared!")
