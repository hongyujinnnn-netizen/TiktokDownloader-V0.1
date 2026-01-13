"""
Profile Bulk Downloader Window
Download multiple videos from a TikTok profile
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import COLORS, FONTS
from gui.styles import create_styled_button, create_styled_entry, create_styled_frame
from gui.progress_dialog import InlineStatus
from core.profile_scraper import ProfileScraper
from utils.config_manager import ConfigManager
from utils.validators import is_valid_profile_url
import pyperclip


class ProfileDownloaderWindow:
    """Window for downloading videos from TikTok profiles"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Profile Bulk Downloader")
        self.window.geometry("800x700")
        self.window.configure(bg=COLORS["background"])
        
        self.config = ConfigManager()
        self.scraper = ProfileScraper()
        self.is_downloading = False
        self.should_stop = False
        self.should_pause = False
        
        self.create_widgets()
        self.center_window()
        self.setup_shortcuts()
    
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
            text="👤 Download from Profile",
            font=FONTS["title"],
            bg=COLORS["background"],
            fg=COLORS["text"]
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text="Download multiple videos from a TikTok user profile",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"]
        )
        subtitle.pack()
        
        # Main card
        card = create_styled_frame(self.window, COLORS["card"])
        card.pack(pady=10, padx=30, fill="both", expand=True)
        
        # Profile URL
        url_label = tk.Label(
            card,
            text="TikTok Profile URL:",
            font=FONTS["subheading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        url_label.pack(pady=(20, 5), anchor="w", padx=20)
        
        # URL entry with paste button
        url_frame = tk.Frame(card, bg=COLORS["card"])
        url_frame.pack(pady=5, padx=20, fill="x")
        
        self.profile_url_entry = create_styled_entry(url_frame, width=60)
        self.profile_url_entry.pack(side="left", ipady=8, padx=(0, 10))
        self.profile_url_entry.bind('<KeyRelease>', self.validate_profile_url)
        
        paste_btn = create_styled_button(
            url_frame,
            text="📋 Paste",
            command=self.paste_url,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        paste_btn.pack(side="left", ipadx=10, ipady=8)
        
        # URL validation feedback
        self.url_validation = InlineStatus(card)
        self.url_validation.pack(pady=(5, 0))
        
        # Video limit section
        limit_frame = tk.Frame(card, bg=COLORS["card"])
        limit_frame.pack(pady=15, padx=20, fill="x")
        
        # Total videos info
        total_label = tk.Label(
            limit_frame,
            text="Profile has:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        total_label.pack(side="left", padx=(0, 5))
        
        self.total_videos_label = tk.Label(
            limit_frame,
            text="? videos",
            font=FONTS["subheading"],
            bg=COLORS["card"],
            fg=COLORS["accent"]
        )
        self.total_videos_label.pack(side="left", padx=5)
        
        # Fetch button
        fetch_btn = create_styled_button(
            limit_frame,
            text="🔍 Check Profile",
            command=self.fetch_profile_info,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9"
        )
        fetch_btn.pack(side="left", padx=20, ipadx=10, ipady=5)
        
        # Download limit
        limit_input_frame = tk.Frame(card, bg=COLORS["card"])
        limit_input_frame.pack(pady=10, padx=20, fill="x")
        
        limit_label = tk.Label(
            limit_input_frame,
            text="Number of videos to download:",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        limit_label.pack(side="left", padx=(0, 10))
        
        self.limit_entry = create_styled_entry(limit_input_frame, width=10)
        self.limit_entry.insert(0, str(self.config.get_setting("profile_video_limit")))
        self.limit_entry.pack(side="left", ipady=5)
        
        hint_label = tk.Label(
            limit_input_frame,
            text="(0 = download all)",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        hint_label.pack(side="left", padx=10)
        
        # Options
        options_frame = tk.Frame(card, bg=COLORS["card"])
        options_frame.pack(pady=15, padx=20, fill="x")
        
        self.create_folder_var = tk.BooleanVar(
            value=self.config.get_setting("create_profile_folders")
        )
        folder_check = tk.Checkbutton(
            options_frame,
            text="Create separate folder for this profile",
            variable=self.create_folder_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        folder_check.pack(anchor="w", pady=2)
        
        self.convert_mp3_var = tk.BooleanVar()
        mp3_check = tk.Checkbutton(
            options_frame,
            text="Convert to MP3",
            variable=self.convert_mp3_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        mp3_check.pack(anchor="w", pady=2)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        skip_check = tk.Checkbutton(
            options_frame,
            text="Skip already downloaded videos",
            variable=self.skip_existing_var,
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            selectcolor=COLORS["background"],
            activebackground=COLORS["card"]
        )
        skip_check.pack(anchor="w", pady=2)
        
        # Download controls frame
        controls_frame = tk.Frame(card, bg=COLORS["card"])
        controls_frame.pack(pady=15)
        
        # Download button
        self.download_btn = create_styled_button(
            controls_frame,
            text="⬇ Start Bulk Download",
            command=self.start_bulk_download,
            bg=COLORS["button"],
            hover_bg=COLORS["button_hover"]
        )
        self.download_btn.pack(side="left", padx=5, ipadx=30, ipady=10)
        
        # Pause button (hidden initially)
        self.pause_btn = create_styled_button(
            controls_frame,
            text="⏸ Pause",
            command=self.toggle_pause,
            bg=COLORS["warning"],
            hover_bg="#D97706"
        )
        self.pause_btn.pack(side="left", padx=5, ipadx=20, ipady=10)
        self.pause_btn.pack_forget()  # Hide initially
        
        # Stop button (hidden initially)
        self.stop_btn = create_styled_button(
            controls_frame,
            text="❌ Stop",
            command=self.stop_download,
            bg=COLORS["danger"],
            hover_bg=COLORS["danger_hover"]
        )
        self.stop_btn.pack(side="left", padx=5, ipadx=20, ipady=10)
        self.stop_btn.pack_forget()  # Hide initially
        
        # Current download status
        self.current_video_label = tk.Label(
            card,
            text="",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["accent"],
            height=2
        )
        self.current_video_label.pack(pady=5)
        
        # Progress section
        progress_label = tk.Label(
            card,
            text="Download Progress:",
            font=FONTS["subheading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        progress_label.pack(pady=(10, 5), anchor="w", padx=20)
        
        # Progress text
        self.progress_text = scrolledtext.ScrolledText(
            card,
            height=10,
            font=FONTS["small"],
            bg=COLORS["background"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"]
        )
        self.progress_text.pack(pady=5, padx=20, fill="both", expand=True)
        
        # Status label
        self.status_label = tk.Label(
            card,
            text="Ready",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        self.status_label.pack(pady=10)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.window.bind('<Control-v>', lambda e: self.paste_url())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
    
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            import pyperclip
            clipboard_text = pyperclip.paste()
            self.profile_url_entry.delete(0, tk.END)
            self.profile_url_entry.insert(0, clipboard_text)
            self.validate_profile_url()
        except:
            try:
                clipboard_text = self.window.clipboard_get()
                self.profile_url_entry.delete(0, tk.END)
                self.profile_url_entry.insert(0, clipboard_text)
                self.validate_profile_url()
            except:
                self.url_validation.show_error("Failed to paste from clipboard")
    
    def validate_profile_url(self, event=None):
        """Validate profile URL in real-time"""
        url = self.profile_url_entry.get().strip()
        
        if not url:
            self.url_validation.clear()
            return
        
        if is_valid_profile_url(url):
            self.url_validation.show_success("Valid profile URL")
        else:
            self.url_validation.show_error("Invalid profile URL")
    
    def toggle_inputs(self, enabled):
        """Enable/disable inputs during download"""
        state = "normal" if enabled else "disabled"
        self.profile_url_entry.config(state=state)
        self.limit_entry.config(state=state)
        
        if enabled:
            self.download_btn.pack(side="left", padx=5, ipadx=30, ipady=10)
            self.pause_btn.pack_forget()
            self.stop_btn.pack_forget()
        else:
            self.download_btn.pack_forget()
            self.pause_btn.pack(side="left", padx=5, ipadx=20, ipady=10)
            self.stop_btn.pack(side="left", padx=5, ipadx=20, ipady=10)
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.should_pause = not self.should_pause
        
        if self.should_pause:
            self.pause_btn.config(text="▶ Resume")
            self.log_progress("⏸ Download paused...")
        else:
            self.pause_btn.config(text="⏸ Pause")
            self.log_progress("▶ Download resumed...")
    
    def stop_download(self):
        """Stop the download"""
        self.should_stop = True
        self.log_progress("🛑 Stopping download...")
    
    def log_progress(self, message):
        """Log message to progress text"""
        self.progress_text.insert(tk.END, f"{message}\n")
        self.progress_text.see(tk.END)
        self.window.update()
    
    def fetch_profile_info(self):
        """Fetch profile information"""
        url = self.profile_url_entry.get().strip()
        
        if not url:
            self.url_validation.show_warning("Please enter a profile URL!")
            return
        
        if not is_valid_profile_url(url):
            self.url_validation.show_error("Invalid profile URL!")
            return
        
        self.log_progress("🔍 Fetching profile information...")
        self.status_label.config(text="Checking profile...")
        
        try:
            total_videos = self.scraper.get_profile_video_count(url)
            self.total_videos_label.config(text=f"{total_videos} videos")
            self.log_progress(f"✅ Found {total_videos} videos in profile")
            self.status_label.config(text="Ready")
            self.url_validation.show_success(f"Profile has {total_videos} videos")
        except Exception as e:
            self.log_progress(f"❌ Error: {str(e)}")
            self.url_validation.show_error(f"Failed: {str(e)[:50]}")
            self.status_label.config(text="Error")
    
    def start_bulk_download(self):
        """Start bulk download process"""
        if self.is_downloading:
            self.url_validation.show_info("Download already in progress!")
            return
        
        url = self.profile_url_entry.get().strip()
        
        if not url:
            self.url_validation.show_warning("Please enter a profile URL!")
            return
        
        if not is_valid_profile_url(url):
            self.url_validation.show_error("Invalid profile URL!")
            return
        
        try:
            limit = int(self.limit_entry.get())
        except ValueError:
            self.url_validation.show_error("Please enter a valid number for video limit!")
            return
        
        # Confirm for download all
        if limit == 0:
            confirm = messagebox.askyesno(
                "Confirm",
                "Are you sure you want to download ALL videos from this profile?"
            )
            if not confirm:
                return
        
        # Reset flags
        self.should_stop = False
        self.should_pause = False
        
        # Start download in thread
        thread = threading.Thread(
            target=self.bulk_download_thread,
            args=(url, limit),
            daemon=True
        )
        thread.start()
    
    def bulk_download_thread(self, url, limit):
        """Bulk download in separate thread"""
        self.is_downloading = True
        self.toggle_inputs(False)
        
        try:
            self.log_progress(f"\n{'='*60}")
            self.log_progress("🚀 Starting bulk download...")
            self.log_progress(f"Profile URL: {url}")
            self.log_progress(f"Video limit: {limit if limit > 0 else 'All'}")
            self.log_progress(f"{'='*60}\n")
            
            result = self.scraper.download_from_profile(
                profile_url=url,
                limit=limit,
                create_folder=self.create_folder_var.get(),
                convert_to_mp3=self.convert_mp3_var.get(),
                skip_existing=self.skip_existing_var.get(),
                progress_callback=self.download_progress_callback,
                pause_check=lambda: self.should_pause,
                stop_check=lambda: self.should_stop
            )
            
            self.log_progress(f"\n{'='*60}")
            
            if self.should_stop:
                self.log_progress(f"🛑 Download stopped by user!")
                self.log_progress(f"Downloaded: {result['downloaded']} videos")
            else:
                self.log_progress(f"✅ Bulk download completed!")
                self.log_progress(f"Total downloaded: {result['downloaded']}")
                self.log_progress(f"Failed: {result['failed']}")
                self.log_progress(f"Skipped: {result['skipped']}")
                
                messagebox.showinfo(
                    "Complete",
                    f"Bulk download completed!\n\n"
                    f"Downloaded: {result['downloaded']}\n"
                    f"Failed: {result['failed']}\n"
                    f"Skipped: {result['skipped']}"
                )
            
            self.log_progress(f"{'='*60}\n")
            
        except Exception as e:
            self.log_progress(f"\n❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Bulk download failed:\n{str(e)}")
        
        finally:
            self.is_downloading = False
            self.should_stop = False
            self.should_pause = False
            self.toggle_inputs(True)
            self.current_video_label.config(text="")
            self.status_label.config(text="Ready")
    
    def download_progress_callback(self, message, current=None, total=None, video_name=None, status=None):
        """Enhanced progress callback with current video info"""
        self.log_progress(message)
        
        # Update current video display
        if video_name:
            if current and total:
                self.current_video_label.config(
                    text=f"📹 [{current}/{total}] {video_name[:60]}..."
                )
            else:
                self.current_video_label.config(text=f"📹 {video_name[:60]}...")
        
        # Handle pause
        while self.should_pause and not self.should_stop:
            self.window.update()
            import time
            time.sleep(0.1)
        
        # Check if should stop
        if self.should_stop:
            raise Exception("Download stopped by user")
