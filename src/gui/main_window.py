"""
Main Application Window
Professional TikTok Downloader GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import re

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
from utils.translator import translate
import pyperclip
import threading


class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager()
        self.downloader = TikTokDownloader()
        self.profile_scraper = ProfileScraper()
        self.tr = translate
        
        # Download control flags
        self.is_paused = False
        self.should_stop = False
        self.is_downloading = False
        self.is_batch_downloading = False
        self.import_button = None
        self.pending_batch_links = []
        self.pending_batch_ignored = []
        
        # Configure window
        self.root.title(self.tr("app_title", APP_NAME))
        self.root.geometry("900x700")
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
            text=self.tr("app_title", "TikTok Downloader Pro"),
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
            text=self.tr("smart_download_heading", "Smart Download (Video or Profile)"),
            font=FONTS["heading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        single_label.pack(pady=(20, 10))
        
        # URL Entry
        url_label = tk.Label(
            main_card,
            text=self.tr("paste_url_any", "Paste Video or Profile URL:"),
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
            text=self.tr("paste_button", "\U0001F4CB Paste"),
            command=self.paste_url,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
            font=FONTS["emoji"]
        )
        paste_btn.pack(side="left", ipadx=10, ipady=8)

        self.import_button = create_styled_button(
            url_frame,
            text=self.tr("import_links_button", "📂 Import Links"),
            command=self.import_links_from_file,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
            font=FONTS["emoji"]
        )
        self.import_button.pack(side="left", padx=(10, 0), ipadx=10, ipady=8)
        
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
            text=self.tr("detecting_profile", "\U0001F501 Detecting profile..."),
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        # Don't pack yet, will show during loading
        
        # Download button (changes text based on URL type)
        self.download_btn = create_styled_button(
            main_card,
            text=self.tr("download_default", "\u2B07\uFE0F Download"),
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
            text=self.tr("pause_label", "\u23F8\uFE0F Pause"),
            command=self.toggle_pause,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
            font=FONTS["emoji"]
        )
        self.pause_btn.pack(side="left", padx=5, ipadx=15, ipady=6)
        
        self.stop_btn = create_styled_button(
            self.control_buttons_frame,
            text=self.tr("stop_label", "\u23F9\uFE0F Stop"),
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
            text=self.tr("history_button", "\U0001F4DC History"),
            command=self.open_history,
            bg=COLORS["card"],
            hover_bg=COLORS["border"],
            font=FONTS["emoji"]
        )
        history_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        settings_btn = create_styled_button(
            bottom_frame,
            text=self.tr("settings_button", "\u2699\uFE0F Settings"),
            command=self.open_settings,
            bg=COLORS["card"],
            hover_bg=COLORS["border"],
            font=FONTS["emoji"]
        )
        settings_btn.pack(side="left", padx=5, ipadx=10, ipady=5)
        
        folder_btn = create_styled_button(
            bottom_frame,
            text=self.tr("open_downloads_folder", "\U0001F4C1 Open Downloads Folder"),
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
            text=self.tr("footer_text", "Built with Ryu | v{version} | © 2026").format(version=APP_VERSION),
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
                    text=self.tr("paste_clipboard_failed", "\u274C Failed to paste from clipboard"),
                    fg=COLORS["danger"]
                )
    
    def import_links_from_file(self):
        """Import multiple TikTok links from a text file and download sequentially."""
        if self.is_batch_downloading or self.is_downloading:
            self.download_status.show_warning(
                self.tr("batch_busy_warning", "Please wait for the current download to finish."),
            )
            return

        file_path = filedialog.askopenfilename(
            title=self.tr("batch_file_dialog_title", "Select text file with TikTok links"),
            filetypes=[
                (self.tr("batch_file_dialog_filter", "Text Files (*.txt)"), "*.txt"),
                (self.tr("batch_file_dialog_filter_all", "All Files"), "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                lines = [line.strip() for line in file_handle if line.strip()]
        except Exception as exc:
            self.download_status.show_error(
                self.tr("batch_file_read_error", "Failed to read file: {error}").format(error=str(exc)[:80])
            )
            return

        valid_links = []
        ignored_links = []
        for line in lines:
            if is_valid_tiktok_url(line):
                valid_links.append(line)
            else:
                ignored_links.append(line)

        if not valid_links:
            self.download_status.show_error(
                self.tr("batch_no_valid_links", "No valid TikTok links found in the selected file."),
            )
            return

        self.pending_batch_links = valid_links
        self.pending_batch_ignored = ignored_links

        summary = self.tr(
            "batch_ready_message",
            "Loaded {count} links. Press Download to begin.",
        ).format(count=len(valid_links))

        if ignored_links:
            summary += " " + self.tr(
                "batch_ready_ignored",
                "Ignored {count} entries that were not valid TikTok URLs.",
            ).format(count=len(ignored_links))

        self.download_status.show_info(summary)

        if valid_links:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, valid_links[0])
            self.validate_url()

    def _batch_download_thread(self, links, ignored_links):
        """Perform sequential downloads for imported links."""
        convert_to_mp3 = self.config.get_setting("convert_to_mp3", False)
        success_count = 0
        failures = []

        total = len(links)
        try:
            for index, link in enumerate(links, start=1):
                progress_text = self.tr(
                    "batch_progress_message",
                    "Downloading {index}/{total}...",
                ).format(index=index, total=total)
                self.root.after(0, self.download_status.show_info, progress_text)

                result = self.downloader.download_video(
                    link,
                    convert_to_mp3=convert_to_mp3,
                    source="batch",
                )

                if result.get("success"):
                    success_count += 1
                else:
                    failures.append(
                        {
                            "url": link,
                            "error": result.get("error", "Unknown error"),
                        }
                    )
        except Exception as exc:  # Catch unexpected errors to restore UI properly
            failures.append({"url": "unexpected", "error": str(exc)})

        self.root.after(
            0,
            self._on_batch_download_complete,
            links,
            success_count,
            failures,
            ignored_links,
        )

    def _on_batch_download_complete(self, links, success_count, failures, ignored_links):
        """Handle UI updates after batch download finishes."""
        total = len(links)
        failed_count = len(failures)
        ignored_count = len(ignored_links)

        summary = self.tr(
            "batch_complete_summary",
            "Batch complete: {success}/{total} downloaded.",
        ).format(success=success_count, total=total)

        if failed_count:
            summary += " " + self.tr(
                "batch_complete_failed",
                "{failed} failed.",
            ).format(failed=failed_count)

        if ignored_count:
            summary += " " + self.tr(
                "batch_complete_invalid",
                "{invalid} ignored.",
            ).format(invalid=ignored_count)

        if success_count == total and failed_count == 0:
            self.download_status.show_success(summary)
        elif success_count > 0:
            detail = ""
            if failed_count:
                first_error = failures[0].get("error", "Unknown error")
                detail = " " + self.tr(
                    "batch_failure_example",
                    "Example error: {error}",
                ).format(error=str(first_error)[:80])
            self.download_status.show_warning(summary + detail)
        else:
            detail = ""
            if failed_count:
                first_error = failures[0].get("error", "Unknown error")
                detail = " " + self.tr(
                    "batch_failure_example",
                    "Example error: {error}",
                ).format(error=str(first_error)[:80])
            self.download_status.show_error(summary + detail)

        self.download_btn.config(state="normal")
        if hasattr(self, "import_button") and self.import_button:
            self.import_button.config(state="normal")

        self.is_batch_downloading = False
        self.url_entry.config(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_validation_label.config(text="")

    def _start_batch_download(self):
        """Initialize batch download after user confirmation."""
        if not self.pending_batch_links:
            return

        links = list(self.pending_batch_links)
        ignored = list(self.pending_batch_ignored)
        self.pending_batch_links = []
        self.pending_batch_ignored = []

        limit = self._safe_int(self.config.get_setting("profile_video_limit", 0))
        limit_notice = ""
        if limit > 0:
            links, skipped_due_to_limit = self._apply_profile_limit(links, limit)
            if skipped_due_to_limit:
                ignored.extend(skipped_due_to_limit)
                limit_notice = self.tr(
                    "batch_limit_notice",
                    "Respecting limit of {limit} per profile. Skipping {skipped} extra entries.",
                ).format(limit=limit, skipped=len(skipped_due_to_limit))

        if not links:
            ignored_count = len(ignored)
            if ignored_count:
                self.download_status.show_warning(
                    self.tr(
                        "batch_limit_all_skipped",
                        "All imported links exceeded the per-profile limit ({limit}). Nothing to download.",
                    ).format(limit=limit)
                )
            else:
                self.download_status.show_warning(
                    self.tr("batch_no_links_after_limit", "No links available after applying limits.")
                )
            return

        self.is_batch_downloading = True
        self.download_btn.config(state="disabled")
        if self.import_button:
            self.import_button.config(state="disabled")
        self.url_entry.config(state="disabled")

        start_message = self.tr(
            "batch_start_message",
            "Starting batch download ({count} links)...",
        ).format(count=len(links))
        if limit_notice:
            start_message += " " + limit_notice
        self.download_status.show_info(start_message)

        thread = threading.Thread(
            target=self._batch_download_thread,
            args=(links, ignored),
            daemon=True,
        )
        thread.start()

    def _safe_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _apply_profile_limit(self, links, limit):
        counts = {}
        kept = []
        skipped = []
        for link in links:
            profile = self._extract_profile_handle(link) or "__unknown__"
            current = counts.get(profile, 0)
            if current >= limit:
                skipped.append(link)
                continue
            counts[profile] = current + 1
            kept.append(link)
        return kept, skipped

    def _extract_profile_handle(self, url):
        if not url:
            return None
        match = re.search(r"@([A-Za-z0-9._-]+)", url)
        if not match:
            return None
        return match.group(1).lower()

    def validate_url(self, event=None):
        """Validate URL in real-time and detect type"""
        if event is not None and self.pending_batch_links:
            self.pending_batch_links = []
            self.pending_batch_ignored = []
            self.download_status.show_info(
                self.tr("batch_cancelled_message", "Batch import cleared. Ready for single download."),
            )

        url = self.url_entry.get().strip()
        
        if not url:
            self.url_validation_label.config(text="")
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_default", "\u2B07\uFE0F Download"))
            return
        
        # Check if it's a profile URL
        if is_valid_profile_url(url):
            self.url_validation_label.config(
                text=self.tr("profile_url_detected", "\u2705 Profile URL detected - Bulk download mode"),
                fg=COLORS["accent"]
            )
            self.profile_options_frame.pack(pady=10)
            self.download_btn.config(text=self.tr("download_profile", "\u2B07\uFE0F Start Profile Download"))
            # Try to get profile info
            threading.Thread(target=self.fetch_profile_info, args=(url,), daemon=True).start()
        # Check if it's a video URL
        elif is_valid_video_url(url):
            self.url_validation_label.config(
                text=self.tr("video_url_detected", "\u2705 Video URL detected - Single download mode"),
                fg=COLORS["success"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_video", "\u2B07\uFE0F Download Video"))
        # Valid TikTok URL but not sure which type
        elif is_valid_tiktok_url(url):
            self.url_validation_label.config(
                text=self.tr("valid_url_detected", "\u2705 Valid TikTok URL detected"),
                fg=COLORS["success"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_default", "\u2B07\uFE0F Download"))
        else:
            self.url_validation_label.config(
                text=self.tr("invalid_url_message", "\u274C Invalid TikTok URL"),
                fg=COLORS["danger"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_default", "\u2B07\uFE0F Download"))
    
    def smart_download(self):
        """Smart download - detects URL type and downloads accordingly"""
        if self.is_batch_downloading:
            self.download_status.show_warning(
                self.tr("batch_busy_warning", "Please wait for the current download to finish."),
            )
            return

        if self.pending_batch_links:
            self._start_batch_download()
            return

        url = self.url_entry.get().strip()
        
        if not url:
            self.download_status.show_error(self.tr("empty_url_error", "Please enter a URL"))
            return
        
        if not is_valid_tiktok_url(url):
            self.download_status.show_error(self.tr("invalid_url_error", "Invalid TikTok URL"))
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
            self.download_status.show_warning(self.tr("paste_video_prompt", "Please paste a TikTok video URL!"))
            return
        
        if not is_valid_tiktok_url(url):
            self.download_status.show_error(self.tr("invalid_url_error_strict", "Invalid TikTok URL!"))
            return
        
        try:
            # Show progress dialog
            progress = ProgressDialog(
                self.root,
                self.tr("progress_title_downloading", "Downloading Video"),
                mode="indeterminate",
            )
            progress.update_status(self.tr("progress_status_fetching", "Fetching video information..."))
            
            # Download video
            result = self.downloader.download_video(
                url,
                convert_to_mp3=self.config.get_setting("convert_to_mp3", False)
            )
            
            progress.close()
            
            if result["success"]:
                self.download_status.show_success(
                    self.tr("download_success_message", "Downloaded: {title}...").format(
                        title=result["title"][:50]
                    )
                )
                self.url_entry.delete(0, tk.END)
                self.url_validation_label.config(text="")
            else:
                self.download_status.show_error(
                    self.tr("download_failed_message", "Download failed: {error}").format(
                        error=result.get("error", "Unknown")[:50]
                    )
                )
                
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            self.download_status.show_error(
                self.tr("generic_error_message", "Error: {error}").format(error=str(e)[:50])
            )
    
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
            self.download_status.show_info(self.tr("profile_download_start", "Starting profile download..."))
            
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
            self.root.after(
                0,
                self.download_status.show_error,
                self.tr("generic_error_message", "Error: {error}").format(error=str(e)[:50]),
            )
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
        progress_text = self.tr(
            "profile_progress_text",
            "Downloading {current}/{total}: {video}...",
        ).format(current=current, total=total, video=video_name[:40])
        self.root.after(0, self.progress_label.config, {"text": progress_text})
    
    def _on_profile_download_complete(self, result):
        """Handle profile download completion"""
        if result["success"]:
            self.download_status.show_success(
                self.tr("profile_download_success", "Downloaded {done}/{total} videos").format(
                    done=result["downloaded"], total=result["total"]
                )
            )
            self.url_entry.delete(0, tk.END)
            self.url_validation_label.config(text="")
            self.profile_options_frame.pack_forget()
        else:
            self.download_status.show_error(
                self.tr("download_failed_message", "Download failed: {error}").format(
                    error=result.get("error", "Unknown error")[:50]
                )
            )
        
        self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI after download"""
        self.is_downloading = False
        self.control_buttons_frame.pack_forget()
        self.download_btn.config(state="normal")
        self.url_entry.config(state="normal")
        self.progress_label.config(text="")
        self.pause_btn.config(text=self.tr("pause_label", "\u23F8\uFE0F Pause"))
    
    def toggle_pause(self):
        """Toggle pause/resume"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text=self.tr("resume_label", "\u25B6 Resume"))
            self.download_status.show_info(self.tr("download_paused", "Download paused"))
        else:
            self.pause_btn.config(text=self.tr("pause_label", "\u23F8\uFE0F Pause"))
            self.download_status.show_info(self.tr("download_resumed", "Download resumed"))
    
    def stop_download(self):
        """Stop profile download"""
        self.should_stop = True
        self.is_paused = False
        self.download_status.show_warning(self.tr("stopping_download", "Stopping download..."))
    
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
                info_text = self.tr(
                    "profile_info_all",
                    "\U0001F464 @{username} - {count} videos available | Downloading ALL videos",
                ).format(username=username, count=video_count)
            else:
                download_count = min(limit, video_count)
                info_text = self.tr(
                    "profile_info_limited",
                    "\U0001F464 @{username} - {count} videos available | Downloading {limit} videos",
                ).format(username=username, count=video_count, limit=download_count)
            
            self.root.after(0, self.profile_loading_label.pack_forget)
            self.root.after(0, self.profile_info_label.config, {"text": info_text})
        except:
            self.root.after(0, self.profile_loading_label.pack_forget)
            self.root.after(0, self.profile_info_label.config, {
                "text": self.tr("profile_info_failed", "\u26A0\uFE0F Could not fetch profile info"),
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
