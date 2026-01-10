"""
Settings Window
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import COLORS, FONTS, LANGUAGES
from gui.styles import create_styled_button, create_styled_entry, create_styled_frame
from gui.progress_dialog import InlineStatus
from utils.config_manager import ConfigManager
from core.updater import YtdlpUpdater


class SettingsWindow:
    """Window for application settings"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("650x700")
        self.window.configure(bg=COLORS["background"])
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.config = ConfigManager()
        self.updater = YtdlpUpdater()
        
        self.create_widgets()
        self.load_settings()
        self.center_window()
        
        # Auto-save on close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Keyboard shortcuts
        self.window.bind('<Escape>', lambda e: self.on_close())
    
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
            text="⚙ Settings",
            font=FONTS["title"],
            bg=COLORS["background"],
            fg=COLORS["text"]
        )
        title.pack()
        
        # Main card
        card = create_styled_frame(self.window, COLORS["card"])
        card.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Create notebook for tabs
        style = ttk.Style()
        style.configure(
            "Custom.TNotebook",
            background=COLORS["card"],
            borderwidth=0
        )
        style.configure(
            "Custom.TNotebook.Tab",
            background=COLORS["background"],
            foreground=COLORS["text"],
            padding=[20, 10],
            font=FONTS["body"]
        )
        style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text"])]
        )
        
        self.notebook = ttk.Notebook(card, style="Custom.TNotebook")
        self.notebook.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create tabs
        self.create_general_tab()
        self.create_download_tab()
        self.create_advanced_tab()
        self.create_updates_tab()
        
        # Status
        self.settings_status = InlineStatus(card)
        self.settings_status.pack(pady=10)
        
        # Save buttons
        button_frame = tk.Frame(card, bg=COLORS["card"])
        button_frame.pack(pady=10, fill="x", padx=20)
        
        save_btn = create_styled_button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            bg=COLORS["button"],
            hover_bg=COLORS["button_hover"]
        )
        save_btn.pack(side="left", padx=5, ipadx=20, ipady=8)
        
        cancel_btn = create_styled_button(
            button_frame,
            text="✖ Cancel",
            command=self.window.destroy,
            bg=COLORS["danger"],
            hover_bg=COLORS["danger_hover"]
        )
        cancel_btn.pack(side="right", padx=5, ipadx=20, ipady=8)
    
    def create_general_tab(self):
        """Create General settings tab"""
        general_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.notebook.add(general_frame, text="⚙ General")
        
        # App Info
        info_section = self.create_setting_section(general_frame, "Application")
        
        info_text = tk.Label(
            info_section,
            text="TikTok Downloader Pro v1.0.0\nLanguage: English (default)",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            justify="left"
        )
        info_text.pack(anchor="w", pady=5)
        
        # Theme Selector
        theme_section = self.create_setting_section(general_frame, "Theme")
        
        self.theme_var = tk.StringVar()
        theme_menu = ttk.Combobox(
            theme_section,
            textvariable=self.theme_var,
            values=["Dark", "Light"],
            state="readonly",
            font=FONTS["body"]
        )
        theme_menu.pack(fill="x", pady=5)
        
        theme_hint = tk.Label(
            theme_section,
            text="⚠️ Theme will apply after restarting the app",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["warning"]
        )
        theme_hint.pack(anchor="w", pady=(5, 0))
    
    def create_download_tab(self):
        """Create Download settings tab"""
        download_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.notebook.add(download_frame, text="📥 Download")
        
        # Download Path
        path_frame = self.create_setting_section(download_frame, "Download Location")
        
        path_input_frame = tk.Frame(path_frame, bg=COLORS["card"])
        path_input_frame.pack(fill="x", pady=5)
        
        self.path_entry = create_styled_entry(path_input_frame, width=35)
        self.path_entry.pack(side="left", ipady=5, padx=(0, 10))
        
        browse_btn = create_styled_button(
            path_input_frame,
            text="📁 Browse",
            command=self.browse_folder,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        browse_btn.pack(side="left", ipadx=10, ipady=5)
        
        # Video Quality
        quality_frame = self.create_setting_section(download_frame, "Video Quality")
        
        self.quality_var = tk.StringVar()
        quality_menu = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=["Best", "High", "Medium", "Low"],
            state="readonly",
            font=FONTS["body"]
        )
        quality_menu.pack(fill="x", pady=5)
        
        # Audio Conversion
        audio_frame = self.create_setting_section(download_frame, "Audio Conversion")
        
        self.convert_mp3_var = tk.BooleanVar()
        mp3_check = tk.Checkbutton(
            audio_frame,
            text="Always convert to MP3",
            variable=self.convert_mp3_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        mp3_check.pack(anchor="w", pady=5)
        
        mp3_hint = tk.Label(
            audio_frame,
            text="Convert all downloads to MP3 format automatically",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        mp3_hint.pack(anchor="w", pady=(0, 5))
        
        # Profile Download Limit
        profile_frame = self.create_setting_section(download_frame, "Profile Download Limit")
        
        limit_label = tk.Label(
            profile_frame,
            text="Default video limit for profile downloads:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        limit_label.pack(anchor="w", pady=(5, 2))
        
        self.profile_limit_entry = create_styled_entry(profile_frame, width=15)
        self.profile_limit_entry.pack(anchor="w", ipady=5, pady=5)
        
        limit_hint = tk.Label(
            profile_frame,
            text="Set to 0 to download all videos from profile (use with caution)",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        limit_hint.pack(anchor="w", pady=(0, 5))
    
    def create_advanced_tab(self):
        """Create Advanced settings tab"""
        advanced_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.notebook.add(advanced_frame, text="🔧 Advanced")
        
        # Options
        options_frame = self.create_setting_section(advanced_frame, "Options")
        
        self.save_history_var = tk.BooleanVar()
        history_check = tk.Checkbutton(
            options_frame,
            text="Save download history",
            variable=self.save_history_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        history_check.pack(anchor="w", pady=5)
        
        self.profile_folders_var = tk.BooleanVar()
        folder_check = tk.Checkbutton(
            options_frame,
            text="Create folders for profile downloads",
            variable=self.profile_folders_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        folder_check.pack(anchor="w", pady=5)
    
    def create_updates_tab(self):
        """Create Updates tab"""
        updates_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.notebook.add(updates_frame, text="🔄 Updates")
        
        # Auto-update option
        auto_section = self.create_setting_section(updates_frame, "Automatic Updates")
        
        self.auto_update_var = tk.BooleanVar()
        auto_update_check = tk.Checkbutton(
            auto_section,
            text="Auto-update yt-dlp on startup",
            variable=self.auto_update_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        auto_update_check.pack(anchor="w", pady=5)
        
        # Manual Update
        manual_section = self.create_setting_section(updates_frame, "Manual Update")
        
        current_version = tk.Label(
            manual_section,
            text=f"Current yt-dlp version: {self.updater.get_version()}",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        current_version.pack(anchor="w", pady=5)
        
        update_btn = create_styled_button(
            manual_section,
            text="🔄 Update yt-dlp Now",
            command=self.manual_update,
            bg=COLORS["success"],
            hover_bg="#059669"
        )
        update_btn.pack(anchor="w", pady=10, ipadx=15, ipady=8)
        
        self.update_status_label = tk.Label(
            manual_section,
            text="",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        self.update_status_label.pack(anchor="w", pady=5)
    
    def create_setting_section(self, parent, title):
        """Create a setting section"""
        section = tk.Frame(parent, bg=COLORS["card"])
        section.pack(pady=10, padx=20, fill="x")
        
        label = tk.Label(
            section,
            text=title,
            font=FONTS["subheading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        label.pack(anchor="w", pady=(0, 5))
        
        return section
    
    def load_settings(self):
        """Load current settings"""
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.config.get_setting("download_path"))
        
        # Load theme
        theme = self.config.get_setting("theme", "dark")
        self.theme_var.set(theme.capitalize())
        
        quality = self.config.get_setting("video_quality")
        self.quality_var.set(quality.capitalize())
        
        self.auto_update_var.set(self.config.get_setting("auto_update_ytdlp"))
        self.save_history_var.set(self.config.get_setting("save_history"))
        self.profile_folders_var.set(self.config.get_setting("create_profile_folders"))
        
        # Convert to MP3
        self.convert_mp3_var.set(self.config.get_setting("convert_to_mp3", False))
        
        # Profile limit
        limit = self.config.get_setting("profile_video_limit", 10)
        self.profile_limit_entry.delete(0, tk.END)
        self.profile_limit_entry.insert(0, str(limit))
    
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def save_settings(self):
        """Save settings"""
        # Get profile limit
        try:
            profile_limit = int(self.profile_limit_entry.get())
        except:
            profile_limit = 10
        
        settings = {
            "download_path": self.path_entry.get(),
            "language": "en",  # Default to English
            "theme": self.theme_var.get().lower(),
            "video_quality": self.quality_var.get().lower(),
            "auto_update_ytdlp": self.auto_update_var.get(),
            "save_history": self.save_history_var.get(),
            "create_profile_folders": self.profile_folders_var.get(),
            "profile_video_limit": profile_limit,
            "convert_to_mp3": self.convert_mp3_var.get(),
        }
        
        self.config.update_settings(settings)
        self.settings_status.show_success("Settings saved successfully!")
    
    def on_close(self):
        """Handle window close - auto-save settings"""
        self.save_settings()
        self.window.destroy()
    
    def manual_update(self):
        """Manually update yt-dlp"""
        self.update_status_label.config(text="Updating...", fg=COLORS["text_secondary"])
        self.window.update()
        
        try:
            result = self.updater.update()
            if result["success"]:
                self.update_status_label.config(
                    text=f"✅ {result['message']}",
                    fg=COLORS["success"]
                )
                self.settings_status.show_success(result["message"])
            else:
                self.update_status_label.config(
                    text=f"❌ {result['message'][:50]}",
                    fg=COLORS["danger"]
                )
                self.settings_status.show_error(result["message"][:50])
        except Exception as e:
            error_msg = str(e)[:50]
            self.update_status_label.config(text=f"❌ Update failed", fg=COLORS["danger"])
            self.settings_status.show_error(f"Update failed: {error_msg}")
