"""
Main Application Window
Professional TikTok Downloader GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import APP_NAME, COLORS, FONTS, APP_VERSION
from gui.styles import apply_styles, create_styled_button, create_styled_entry, create_styled_frame
from gui.profile_downloader import ProfileDownloaderWindow
from gui.history_window import HistoryWindow
from gui.settings_window import SettingsWindow
from gui.progress_dialog import ProgressDialog, InlineStatus
from core.downloader import TikTokDownloader
from core.profile_scraper import ProfileScraper
from utils.config_manager import ConfigManager
from utils.validators import is_valid_tiktok_url, is_valid_profile_url, is_valid_video_url
import pyperclip
import threading


class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager()
        self.downloader = TikTokDownloader()
        self.profile_scraper = ProfileScraper()
        
        # Download control flags
        self.is_paused = False
        self.should_stop = False
        self.is_downloading = False
        
        # Configure window
        self.root.title(APP_NAME)
        self.root.geometry("800x700")
        self.root.configure(bg=COLORS["background"])
        self.root.resizable(True, True)  # Allow resizing for fullscreen
        
        # Fullscreen state
        self.is_fullscreen = False
        
        # Apply styles
        apply_styles(self.root)
        
        # Create UI
        self.create_widgets()
        
        # Keyboard shortcuts
        self.setup_shortcuts()
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Header
        header_frame = create_styled_frame(self.root, COLORS["background"])
        header_frame.pack(pady=20, padx=30, fill="x")
        
        # Title with styled emoji
        title_container = tk.Frame(header_frame, bg=COLORS["background"])
        title_container.pack()
        
        emoji_label = tk.Label(
            title_container,
            text="🎵",
            font=FONTS["emoji_large"],
            bg=COLORS["background"],
            fg=COLORS["accent"]
        )
        emoji_label.pack(side="left", padx=(0, 10))
        
        title_label = tk.Label(
            title_container,
            text="TikTok Downloader Pro",
            font=FONTS["title_large"],
            bg=COLORS["background"],
            fg=COLORS["accent"]
        )
        title_label.pack(side="left")
        
        version_label = tk.Label(
            header_frame,
            text=f"v{APP_VERSION}",
            font=FONTS["small"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"]
        )
        version_label.pack(pady=(5, 0))
        
        # Main content card
        main_card = create_styled_frame(self.root, COLORS["card"])
        main_card.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Smart Download Section (2-in-1)
        single_label = tk.Label(
            main_card,
            text="Smart Download (Video or Profile)",
            font=FONTS["heading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        single_label.pack(pady=(20, 10))
        
        # URL Entry
        url_label = tk.Label(
            main_card,
            text="Paste Video or Profile URL:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        url_label.pack(pady=(10, 5))
        
        # URL entry frame with paste button
        url_frame = tk.Frame(main_card, bg=COLORS["card"])
        url_frame.pack(pady=5)
        
        self.url_entry = create_styled_entry(url_frame, width=50)
        self.url_entry.pack(side="left", ipady=8, padx=(0, 10))
        self.url_entry.bind('<KeyRelease>', self.validate_url)
        
        paste_btn = create_styled_button(
            url_frame,
            text="📋 Paste",
            command=self.paste_url,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
            font=FONTS["emoji"]
        )
        paste_btn.pack(side="left", ipadx=10, ipady=8)
        
        # URL validation feedback
        self.url_validation_label = tk.Label(
            main_card,
            text="",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            height=1
        )
        self.url_validation_label.pack()
        
        # Profile Options Frame (hidden by default)
        self.profile_options_frame = tk.Frame(main_card, bg=COLORS["card"])
        self.profile_options_frame.pack(pady=10)
        self.profile_options_frame.pack_forget()  # Hide initially
        
        # Profile info label
        self.profile_info_label = tk.Label(
            self.profile_options_frame,
            text="",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["accent"]
        )
        self.profile_info_label.pack(pady=5)
        
        # Loading indicator for profile detection
        self.profile_loading_label = tk.Label(
            self.profile_options_frame,
            text="🔄 Detecting profile...",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        # Don't pack yet, will show during loading
        
        # Download button (changes text based on URL type)
        self.download_btn = create_styled_button(
            main_card,
            text="⬇ Download",
            command=self.smart_download,
            bg=COLORS["button"],
            hover_bg=COLORS["button_hover"],
            font=FONTS["emoji"]
        )
        self.download_btn.pack(pady=15, ipadx=20, ipady=8)
        
        # Control buttons frame (for profile downloads)
        self.control_buttons_frame = tk.Frame(main_card, bg=COLORS["card"])
        self.control_buttons_frame.pack(pady=5)
        self.control_buttons_frame.pack_forget()  # Hide initially
        
        self.pause_btn = create_styled_button(
            self.control_buttons_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
            font=FONTS["emoji"]
        )
        self.pause_btn.pack(side="left", padx=5, ipadx=15, ipady=6)
        
        self.stop_btn = create_styled_button(
            self.control_buttons_frame,
            text="⏹ Stop",
            command=self.stop_download,
            bg=COLORS["danger"],
            hover_bg="#DC2626",
            font=FONTS["emoji"]
        )
        self.stop_btn.pack(side="left", padx=5, ipadx=15, ipady=6)
        
        # Progress label for profile downloads
        self.progress_label = tk.Label(
            main_card,
            text="",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        self.progress_label.pack(pady=5)
        
        # Inline status feedback
        self.download_status = InlineStatus(main_card)
        self.download_status.pack(pady=10)
        

        
        # Bottom buttons
        bottom_frame = tk.Frame(self.root, bg=COLORS["background"])
        bottom_frame.pack(pady=10, padx=30, fill="x")
        
        history_btn = create_styled_button(
            bottom_frame,
            text="📜 History",
            command=self.open_history,
            bg=COLORS["card"],
            hover_bg=COLORS["border"],
            font=FONTS["emoji"]
        )
        history_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        settings_btn = create_styled_button(
            bottom_frame,
            text="⚙ Settings",
            command=self.open_settings,
            bg=COLORS["card"],
            hover_bg=COLORS["border"],
            font=FONTS["emoji"]
        )
        settings_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        folder_btn = create_styled_button(
            bottom_frame,
            text="📁 Open Downloads Folder",
            command=self.open_downloads_folder,
            bg=COLORS["card"],
            hover_bg=COLORS["border"],
            font=FONTS["emoji"]
        )
        folder_btn.pack(side="right", padx=5, ipadx=10, ipady=5)
        
        # Footer branding
        footer = tk.Frame(self.root, bg=COLORS["background"])
        footer.pack(pady=5, fill="x")
        
        footer_text = tk.Label(
            footer,
            text=f"Built with Ryu | v{APP_VERSION} | © 2026",
            font=FONTS["small"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"]
        )
        footer_text.pack()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Control-v>', lambda e: self.paste_url())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.root.bind('<Escape>', lambda e: self.exit_fullscreen() if self.is_fullscreen else self.root.quit())
        self.url_entry.bind('<Return>', lambda e: self.smart_download())
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            import pyperclip
            clipboard_text = pyperclip.paste()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard_text)
            self.validate_url()
        except:
            # Fallback to tkinter clipboard
            try:
                clipboard_text = self.root.clipboard_get()
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, clipboard_text)
                self.validate_url()
            except:
                self.url_validation_label.config(
                    text="❌ Failed to paste from clipboard",
                    fg=COLORS["danger"]
                )
    
    def validate_url(self, event=None):
        """Validate URL in real-time and detect type"""
        url = self.url_entry.get().strip()
        
        if not url:
            self.url_validation_label.config(text="")
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text="⬇ Download")
            return
        
        # Check if it's a profile URL
        if is_valid_profile_url(url):
            self.url_validation_label.config(
                text="✅ Profile URL detected - Bulk download mode",
                fg=COLORS["accent"]
            )
            self.profile_options_frame.pack(pady=10)
            self.download_btn.config(text="⬇ Start Profile Download")
            # Try to get profile info
            threading.Thread(target=self.fetch_profile_info, args=(url,), daemon=True).start()
        # Check if it's a video URL
        elif is_valid_video_url(url):
            self.url_validation_label.config(
                text="✅ Video URL detected - Single download mode",
                fg=COLORS["success"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text="⬇ Download Video")
        # Valid TikTok URL but not sure which type
        elif is_valid_tiktok_url(url):
            self.url_validation_label.config(
                text="✅ Valid TikTok URL detected",
                fg=COLORS["success"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text="⬇ Download")
        else:
            self.url_validation_label.config(
                text="❌ Invalid TikTok URL",
                fg=COLORS["danger"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text="⬇ Download")
    
    def smart_download(self):
        """Smart download - detects URL type and downloads accordingly"""
        url = self.url_entry.get().strip()
        
        if not url:
            self.download_status.show_error("Please enter a URL")
            return
        
        if not is_valid_tiktok_url(url):
            self.download_status.show_error("Invalid TikTok URL")
            return
        
        # Detect URL type and download
        if is_valid_profile_url(url):
            self.download_profile()
        else:
            self.download_single_video()
    
    def download_single_video(self):
        """Download a single video"""
        url = self.url_entry.get().strip()
        
        if not url:
            self.download_status.show_warning("Please paste a TikTok video URL!")
            return
        
        if not is_valid_tiktok_url(url):
            self.download_status.show_error("Invalid TikTok URL!")
            return
        
        try:
            # Show progress dialog
            progress = ProgressDialog(self.root, "Downloading Video", mode="indeterminate")
            progress.update_status("Fetching video information...")
            
            # Download video
            result = self.downloader.download_video(
                url,
                convert_to_mp3=self.config.get_setting("convert_to_mp3", False)
            )
            
            progress.close()
            
            if result["success"]:
                self.download_status.show_success(
                    f"Downloaded: {result['title'][:50]}..."
                )
                self.url_entry.delete(0, tk.END)
                self.url_validation_label.config(text="")
            else:
                self.download_status.show_error(f"Download failed: {result['error'][:50]}")
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            self.download_status.show_error(f"Error: {str(e)[:50]}")
    
    def download_profile(self):
        """Download videos from a profile"""
        url = self.url_entry.get().strip()
        
        # Get limit from settings
        limit = self.config.get_setting("profile_video_limit", 10)
        
        # Reset control flags
        self.is_paused = False
        self.should_stop = False
        self.is_downloading = True
        
        # Show control buttons
        self.control_buttons_frame.pack(pady=5)
        self.download_btn.config(state="disabled")
        self.url_entry.config(state="disabled")
        
        # Start download in thread
        thread = threading.Thread(
            target=self._download_profile_thread,
            args=(url, limit),
            daemon=True
        )
        thread.start()
    
    def _download_profile_thread(self, url, limit):
        """Profile download thread"""
        try:
            self.download_status.show_info("Starting profile download...")
            
            result = self.profile_scraper.download_from_profile(
                profile_url=url,
                limit=limit,
                convert_to_mp3=self.config.get_setting("convert_to_mp3", False),
                progress_callback=self.download_progress_callback,
                pause_check=lambda: self.is_paused,
                stop_check=lambda: self.should_stop
            )
            
            # Update UI in main thread
            self.root.after(0, self._on_profile_download_complete, result)
            
        except Exception as e:
            self.root.after(0, self.download_status.show_error, f"Error: {str(e)[:50]}")
            self.root.after(0, self._reset_ui)
    
    def download_progress_callback(self, current, total, video_name):
        """Update progress for profile downloads"""
        if self.should_stop:
            return
        
        # Wait while paused
        while self.is_paused and not self.should_stop:
            self.root.update()
            self.root.after(100)
        
        # Update progress label
        progress_text = f"Downloading {current}/{total}: {video_name[:40]}..."
        self.root.after(0, self.progress_label.config, {"text": progress_text})
    
    def _on_profile_download_complete(self, result):
        """Handle profile download completion"""
        if result["success"]:
            self.download_status.show_success(
                f"Downloaded {result['downloaded']}/{result['total']} videos"
            )
            self.url_entry.delete(0, tk.END)
            self.url_validation_label.config(text="")
            self.profile_options_frame.pack_forget()
        else:
            self.download_status.show_error(f"Download failed: {result.get('error', 'Unknown error')[:50]}")
        
        self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI after download"""
        self.is_downloading = False
        self.control_buttons_frame.pack_forget()
        self.download_btn.config(state="normal")
        self.url_entry.config(state="normal")
        self.progress_label.config(text="")
        self.pause_btn.config(text="⏸ Pause")
    
    def toggle_pause(self):
        """Toggle pause/resume"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="▶ Resume")
            self.download_status.show_info("Download paused")
        else:
            self.pause_btn.config(text="⏸ Pause")
            self.download_status.show_info("Download resumed")
    
    def stop_download(self):
        """Stop profile download"""
        self.should_stop = True
        self.is_paused = False
        self.download_status.show_warning("Stopping download...")
    
    def fetch_profile_info(self, url):
        """Fetch profile information in background"""
        # Show loading indicator
        self.root.after(0, self.profile_loading_label.pack, {"pady": 5})
        self.root.after(0, self.profile_info_label.config, {"text": ""})
        
        try:
            video_count = self.profile_scraper.get_profile_video_count(url)
            username = self.profile_scraper.extract_username(url)
            limit = self.config.get_setting("profile_video_limit", 10)
            
            if limit == 0:
                info_text = f"👤 @{username} - {video_count} videos available | Downloading ALL videos"
            else:
                download_count = min(limit, video_count)
                info_text = f"👤 @{username} - {video_count} videos available | Downloading {download_count} videos"
            
            self.root.after(0, self.profile_loading_label.pack_forget)
            self.root.after(0, self.profile_info_label.config, {"text": info_text})
        except:
            self.root.after(0, self.profile_loading_label.pack_forget)
            self.root.after(0, self.profile_info_label.config, {
                "text": "⚠️ Could not fetch profile info",
                "fg": COLORS["warning"]
            })
    
    def open_profile_downloader(self):
        """Open profile bulk downloader window"""
        ProfileDownloaderWindow(self.root)
    
    def open_history(self):
        """Open download history window"""
        HistoryWindow(self.root)
    
    def open_settings(self):
        """Open settings window"""
        SettingsWindow(self.root)
    
    def open_downloads_folder(self):
        """Open downloads folder in file explorer"""
        download_path = self.config.get_setting("download_path")
        os.startfile(download_path)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode (F11)"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        return 'break'
    
    def exit_fullscreen(self):
        """Exit fullscreen mode (Escape)"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes('-fullscreen', False)
            return 'break'
        return None
