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
from utils.translator import translate


class HistoryWindow:
    """Window for viewing download history"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.tr = translate
        self.window.title(self.tr("history_window_title", "Download History"))
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

    def _extract_profile_name(self, item):
        """Get the profile identifier for a history entry."""
        profile_name = item.get("profile_user")
        if profile_name:
            return profile_name

        url = item.get("url", "")
        if "@" in url:
            after_at = url.split("@", 1)[1]
            segment = after_at.split("/", 1)[0]
            if segment:
                return f"@{segment.rstrip()}"

        path = item.get("path", "")
        if "@" in path:
            after_at = path.split("@", 1)[1]
            segment = after_at.split(os.sep, 1)[0]
            if segment:
                return f"@{segment.rstrip()}"

        return self.tr("history_value_unknown", "Unknown")

    def _build_profile_summary(self, entries):
        """Aggregate profile entries for profile filter view."""
        summary = {}
        for item in entries:
            profile = self._extract_profile_name(item)
            if profile not in summary:
                summary[profile] = {
                    "source": "profile_summary",
                    "profile": profile,
                    "items": [],
                    "folder": None,
                    "latest_date": "",
                    "latest_url": "",
                }
            summary_entry = summary[profile]
            summary_entry["items"].append(item)

            path = item.get("path")
            if path and summary_entry["folder"] is None:
                summary_entry["folder"] = os.path.dirname(path)

            date_value = item.get("date", "")
            if date_value and date_value > summary_entry["latest_date"]:
                summary_entry["latest_date"] = date_value

            url_value = item.get("url", "")
            if url_value and not summary_entry["latest_url"]:
                summary_entry["latest_url"] = url_value

        summaries = list(summary.values())
        for entry in summaries:
            entry["count"] = len(entry["items"])
        summaries.sort(key=lambda e: e.get("latest_date", ""), reverse=True)
        return summaries
    
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
            text=self.tr("history_header_title", "📜 Download History"),
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
            text=self.tr("history_filter_label", "Filter:"),
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        ).pack(side="left", padx=(0, 10))
        
        self.filter_all_btn = create_styled_button(
            filter_frame,
            text=self.tr("history_filter_all", "📁 All"),
            command=lambda: self.apply_filter("all"),
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        self.filter_all_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_video_btn = create_styled_button(
            filter_frame,
            text=self.tr("history_filter_video", "🎬 Video"),
            command=lambda: self.apply_filter("video"),
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        self.filter_video_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_mp3_btn = create_styled_button(
            filter_frame,
            text=self.tr("history_filter_mp3", "🎵 MP3"),
            command=lambda: self.apply_filter("mp3"),
            bg=COLORS["border"],
            hover_bg=COLORS["background"]
        )
        self.filter_mp3_btn.pack(side="left", padx=2, ipadx=10, ipady=5)
        
        self.filter_profile_btn = create_styled_button(
            filter_frame,
            text=self.tr("history_filter_profile", "👤 Profile"),
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
            text=self.tr("history_search_label", "Search:"),
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
        self.context_menu.add_command(label=self.tr("history_context_open_file", "📂 Open File"), command=self.open_file)
        self.context_menu.add_command(label=self.tr("history_context_open_folder", "📁 Open Folder"), command=self.open_folder)
        self.context_menu.add_command(label=self.tr("history_context_copy_url", "🔗 Copy URL"), command=self.copy_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.tr("history_context_delete_entry", "🗑 Delete Entry"), command=self.delete_entry)
        
        # Buttons
        button_frame = tk.Frame(card, bg=COLORS["card"])
        button_frame.pack(pady=10, padx=20, fill="x")
        
        clear_btn = create_styled_button(
            button_frame,
            text=self.tr("history_button_clear", "🗑 Clear History"),
            command=self.clear_history,
            bg=COLORS["danger"],
            hover_bg=COLORS["danger_hover"]
        )
        clear_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        refresh_btn = create_styled_button(
            button_frame,
            text=self.tr("history_button_refresh", "🔄 Refresh"),
            command=self.load_history,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        refresh_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        close_btn = create_styled_button(
            button_frame,
            text=self.tr("history_button_close", "✖ Close"),
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
            if item.get("source") == "profile_summary":
                folder = item.get("folder")
                if folder and os.path.exists(folder):
                    os.startfile(folder)
                else:
                    self.history_status.show_error(self.tr("history_error_file_missing", "File not found"))
                return
            file_path = item.get('path', '')
            
            if os.path.exists(file_path):
                os.startfile(file_path)
            else:
                self.history_status.show_error(self.tr("history_error_file_missing", "File not found"))
    
    def open_folder(self):
        """Open folder containing file"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            if item.get("source") == "profile_summary":
                folder = item.get("folder")
                if folder and os.path.exists(folder):
                    os.startfile(folder)
                else:
                    self.history_status.show_error(self.tr("history_error_file_missing", "File not found"))
                return
            file_path = item.get('path', '')
            
            if os.path.exists(file_path):
                folder = os.path.dirname(file_path)
                os.startfile(folder)
            else:
                self.history_status.show_error(self.tr("history_error_file_missing", "File not found"))
    
    def copy_url(self):
        """Copy URL to clipboard"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            if item.get("source") == "profile_summary":
                urls = [entry.get("url", "") for entry in item.get("items", []) if entry.get("url")]
                if not urls:
                    self.history_status.show_error(
                        self.tr("history_profile_no_urls", "No URLs available for this profile")
                    )
                    return
                joined = "\n".join(urls)
                try:
                    import pyperclip
                    pyperclip.copy(joined)
                except:
                    self.window.clipboard_clear()
                    self.window.clipboard_append(joined)
                self.history_status.show_success(self.tr("history_status_url_copied", "URL copied to clipboard"))
                return
            url = item.get('url', '')
            
            try:
                import pyperclip
                pyperclip.copy(url)
                self.history_status.show_success(self.tr("history_status_url_copied", "URL copied to clipboard"))
            except:
                self.window.clipboard_clear()
                self.window.clipboard_append(url)
                self.history_status.show_success(self.tr("history_status_url_copied", "URL copied to clipboard"))
    
    def delete_entry(self):
        """Delete selected entry"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.filtered_history):
            item = self.filtered_history[index]
            if item.get("source") == "profile_summary":
                profile = item.get("profile", self.tr("history_value_unknown", "Unknown"))
                count = item.get("count", 0)
                confirm = messagebox.askyesno(
                    self.tr("history_confirm_delete_title", "Confirm"),
                    self.tr(
                        "history_confirm_delete_profile_message",
                        "Delete all history for {profile}? ({count} items)",
                    ).format(profile=profile, count=count),
                )
                if confirm:
                    for entry in item.get("items", []):
                        if entry in self.all_history:
                            self.all_history.remove(entry)
                    with open(self.config.history_file, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(self.all_history, f, indent=4)
                    self.load_history()
                    self.history_status.show_success(
                        self.tr("history_status_profile_deleted", "Profile history deleted")
                    )
                return
            
            confirm = messagebox.askyesno(
                self.tr("history_confirm_delete_title", "Confirm"),
                self.tr("history_confirm_delete_message", "Delete this entry?\n\n{title}").format(
                    title=item.get('title', self.tr("history_value_unknown", "Unknown"))
                )
            )
            
            if confirm:
                # Remove from all history
                self.all_history.remove(item)
                
                # Save updated history
                with open(self.config.history_file, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(self.all_history, f, indent=4)
                
                self.load_history()
                self.history_status.show_success(self.tr("history_status_entry_deleted", "Entry deleted"))
    
    def load_history(self):
        """Load download history with filters"""
        self.history_listbox.delete(0, tk.END)
        
        self.all_history = self.config.get_history()
        
        if not self.all_history:
            no_history_message = self.tr("history_status_no_history", "No download history yet.")
            self.history_listbox.insert(tk.END, no_history_message)
            self.history_status.show_info(no_history_message)
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
            filtered = [
                h for h in self.all_history
                if h.get('source') == 'profile' or h.get('profile_user')
            ]
        else:
            filtered = self.all_history
        
        search_text = self.search_entry.get().strip().lower()

        if self.filter_type == "profile":
            summaries = self._build_profile_summary(filtered)
            if search_text:
                summaries = [s for s in summaries if search_text in s["profile"].lower()]
            self.filtered_history = summaries
            for entry in self.filtered_history:
                count = entry.get("count", 0)
                if count == 1:
                    label = self.tr(
                        "history_profile_entry_single",
                        "👤 {profile} • {count} video",
                    ).format(profile=entry.get("profile", ""), count=count)
                else:
                    label = self.tr(
                        "history_profile_entry_plural",
                        "👤 {profile} • {count} videos",
                    ).format(profile=entry.get("profile", ""), count=count)
                self.history_listbox.insert(tk.END, label)

            count_profiles = len(self.filtered_history)
            if count_profiles == 0:
                message = self.tr("history_status_no_results", "No matching items")
                self.history_status.show_info(message)
                self.history_listbox.insert(tk.END, message)
            elif count_profiles == 1:
                self.history_status.show_info(
                    self.tr("history_status_profile_count_single", "Showing {count} profile").format(count=count_profiles)
                )
            else:
                self.history_status.show_info(
                    self.tr("history_status_profile_count_plural", "Showing {count} profiles").format(count=count_profiles)
                )
        else:
            if search_text:
                filtered = [h for h in filtered if search_text in h.get('title', '').lower()]

            self.filtered_history = list(reversed(filtered))
            for item in self.filtered_history:
                entry_text = (
                    f"[{item.get('date', self.tr('history_value_not_available', 'N/A'))}] "
                    f"{item.get('title', self.tr('history_value_unknown', 'Unknown'))} - "
                    f"{item.get('type', self.tr('history_value_not_available', 'N/A'))}"
                )
                self.history_listbox.insert(tk.END, entry_text)

            count = len(self.filtered_history)
            if count == 0:
                message = self.tr("history_status_no_results", "No matching items")
                self.history_status.show_info(message)
                self.history_listbox.insert(tk.END, message)
            elif count == 1:
                self.history_status.show_info(
                    self.tr("history_status_count_single", "Showing {count} item").format(count=count)
                )
            else:
                self.history_status.show_info(
                    self.tr("history_status_count_plural", "Showing {count} items").format(count=count)
                )
    
    def clear_history(self):
        """Clear all history"""
        if not self.all_history:
            self.history_status.show_info(self.tr("history_status_already_empty", "History is already empty"))
            return
        
        confirm = messagebox.askyesno(
            self.tr("history_confirm_clear_title", "Confirm"),
            self.tr("history_confirm_clear_message", "Are you sure you want to clear all download history?")
        )
        
        if confirm:
            self.config.clear_history()
            self.load_history()
            self.history_status.show_success(self.tr("history_status_cleared", "History cleared!"))
