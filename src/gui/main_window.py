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
from src.controllers.app_controller import AppController
from src.gui.styles import apply_styles, create_styled_button, create_styled_entry, create_styled_frame
from src.gui.profile_downloader import ProfileDownloaderWindow
from src.gui.history_window import HistoryWindow
from src.gui.settings_window import SettingsWindow
from src.gui.progress_dialog import ProgressDialog, InlineStatus
from src.utils.validators import is_valid_tiktok_url
from src.utils.translator import translate
from src.utils.logger import get_logger
import threading


class MainWindow:
    """Main application window"""
    
    def __init__(self, root, controller=None):
        self.root = root
        self.controller = controller or AppController()
        self.config = self.controller.config
        self.downloader = self.controller.downloader
        self.profile_scraper = self.controller.profile_scraper
        self.tr = translate
        self.logger = get_logger("MainWindow")
        
        # Download control flags
        self.is_paused = False
        self.should_stop = False
        self.is_downloading = False
        self.is_batch_downloading = False
        
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
            text=self.tr("smart_download_heading", "Smart Download (Profile)"),
            font=FONTS["heading"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        single_label.pack(pady=(20, 10))
        
        # URL Entry
        url_label = tk.Label(
            main_card,
            text=self.tr("paste_url_any", "Paste Profile URL:"),
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
        self._setup_drop_target(self.url_entry)
        
        paste_btn = create_styled_button(
            url_frame,
            text=self.tr("paste_button", "\U0001F4CB Paste"),
            command=self.paste_url,
            bg="#FFFFFF",
            hover_bg="#E2E8F0",
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
            text=self.tr("footer_text", "Built with Ryu | v{version} | Â© 2026").format(version=APP_VERSION),
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

        self._import_links_from_path(file_path)

    def _import_links_from_path(self, file_path):
        """Load TikTok links from a text file into batch queue."""
        if not file_path:
            return

        try:
            batch_result = self.controller.load_batch_file(file_path)
        except Exception as exc:
            self.download_status.show_error(
                self.tr("batch_file_read_error", "Failed to read file: {error}").format(error=str(exc)[:80])
            )
            return

        if not batch_result.tasks and not batch_result.ignored_links and not batch_result.duplicate_links:
            self.download_status.show_warning(
                self.tr("batch_empty_file", "Selected file does not contain any links."),
            )
            return

        if not batch_result.tasks:
            self.download_status.show_error(
                self.tr("batch_no_valid_links", "No valid TikTok links found in the selected file."),
            )
            return

        self.controller.set_pending_batch(batch_result)

        summary = self.tr(
            "batch_ready_message",
            "Loaded {count} links. Press Download to begin.",
        ).format(count=len(batch_result.tasks))

        detail_parts = []
        if batch_result.video_count:
            detail_parts.append(
                self.tr("batch_ready_videos", "{count} videos").format(count=batch_result.video_count)
            )
        if batch_result.profile_count:
            detail_parts.append(
                self.tr("batch_ready_profiles", "{count} profiles").format(count=batch_result.profile_count)
            )
        if detail_parts:
            summary += " (" + ", ".join(detail_parts) + ")"

        if batch_result.duplicate_links:
            summary += " " + self.tr(
                "batch_ready_duplicates",
                "Skipped {count} duplicate entries.",
            ).format(count=len(batch_result.duplicate_links))

        if batch_result.ignored_links:
            summary += " " + self.tr(
                "batch_ready_ignored",
                "Ignored {count} entries that were not valid TikTok URLs.",
            ).format(count=len(batch_result.ignored_links))

        self.download_status.show_info(summary)

        first_url = batch_result.tasks[0].url if batch_result.tasks else ""
        self.url_entry.delete(0, tk.END)
        if first_url:
            self.url_entry.insert(0, first_url)
        self.validate_url()

    def _setup_drop_target(self, widget):
        """Enable dropping .txt files onto a widget when DnD is available."""
        if not hasattr(widget, "drop_target_register") or not hasattr(widget, "dnd_bind"):
            return
        try:
            widget.drop_target_register("DND_Files")
            widget.dnd_bind("<<Drop>>", self._on_drop_file)
        except Exception as exc:
            self.logger.warning(f"Failed to bind drag-and-drop: {exc}")

    def _on_drop_file(self, event):
        """Handle dropped file(s) and import first .txt file."""
        if self.is_batch_downloading or self.is_downloading:
            self.download_status.show_warning(
                self.tr("batch_busy_warning", "Please wait for the current download to finish."),
            )
            return "break"

        raw_data = getattr(event, "data", "") or ""
        try:
            dropped_paths = list(self.root.tk.splitlist(raw_data))
        except Exception:
            dropped_paths = [raw_data]

        normalized_paths = []
        for path in dropped_paths:
            cleaned = str(path).strip().strip("{}").strip('"')
            if cleaned:
                normalized_paths.append(cleaned)

        txt_files = [path for path in normalized_paths if path.lower().endswith(".txt")]
        if not txt_files:
            self.download_status.show_warning(
                self.tr("drop_txt_only", "Please drop a .txt file that contains TikTok links."),
            )
            return "break"

        if len(txt_files) > 1:
            self.download_status.show_info(
                self.tr(
                    "drop_multi_files",
                    "Multiple files dropped. Using the first .txt file: {name}",
                ).format(name=os.path.basename(txt_files[0])),
            )

        self._import_links_from_path(txt_files[0])
        return "break"

    def _batch_download_thread(self, tasks, ignored_links, duplicate_links):
        """Perform sequential downloads for imported links."""
        convert_to_mp3 = self.config.get_setting("convert_to_mp3", False)
        create_folders = self.config.get_setting("create_profile_folders", True)
        profile_limit = self.controller.safe_int(self.config.get_setting("profile_video_limit", 10))

        success_count = 0
        failures = []
        total = len(tasks)

        def report(status_method: str, message: str) -> None:
            self.root.after(0, getattr(self.download_status, status_method), message)

        try:
            for index, task in enumerate(tasks, start=1):
                url = task.url
                kind = task.task_type
                prefix = self.tr(
                    "batch_progress_prefix",
                    "[{index}/{total}]",
                ).format(index=index, total=total)

                progress_detail = self.tr(
                    "batch_progress_message",
                    "Downloading {index}/{total}...",
                ).format(index=index, total=total)
                report("show_info", f"{prefix} {progress_detail}")

                if kind == "profile":
                    try:
                        result = self.profile_scraper.download_from_profile(
                            profile_url=url,
                            limit=profile_limit,
                            create_folder=create_folders,
                            convert_to_mp3=convert_to_mp3,
                            skip_existing=True,
                            progress_callback=lambda idx=index, total_count=total, **payload: self._report_profile_batch_progress(idx, total_count, payload),
                            pause_check=lambda: False,
                            stop_check=lambda: False,
                        )
                        if result.get("success"):
                            success_count += 1
                            downloaded = result.get("downloaded", 0)
                            failed_items = result.get("failed", 0)
                            base_msg = self.tr(
                                "batch_profile_success",
                                "{prefix} Profile done: {downloaded} downloaded",
                            ).format(prefix=prefix, downloaded=downloaded)
                            if failed_items:
                                warn_msg = base_msg + " " + self.tr(
                                    "batch_profile_partial",
                                    "({failed} failed)",
                                ).format(failed=failed_items)
                                report("show_warning", warn_msg)
                            else:
                                report("show_success", base_msg)
                        else:
                            failures.append({"url": url, "error": result.get("error", "Unknown error")})
                            report("show_error", f"{prefix} {self.tr('batch_profile_failed', 'Profile download failed.')}")
                    except Exception as exc:  # capture scraper exceptions
                        failures.append({"url": url, "error": str(exc)})
                        report("show_error", f"{prefix} {self.tr('batch_profile_failed', 'Profile download failed.')}")
                else:
                    try:
                        result = self.downloader.download_video(
                            url,
                            convert_to_mp3=convert_to_mp3,
                            source="batch",
                        )
                        if result.get("success"):
                            success_count += 1
                            title = result.get("title", "")[:50]
                            report(
                                "show_success",
                                f"{prefix} "
                                + self.tr("batch_video_success", "Video downloaded: {title}").format(title=title),
                            )
                        else:
                            failures.append({"url": url, "error": result.get("error", "Unknown error")})
                            report(
                                "show_error",
                                f"{prefix} "
                                + self.tr("batch_video_failed", "Video failed: {error}").format(
                                    error=str(result.get("error", "Unknown error"))[:60]
                                ),
                            )
                    except Exception as exc:
                        failures.append({"url": url, "error": str(exc)})
                        report(
                            "show_error",
                            f"{prefix} "
                            + self.tr("batch_video_failed", "Video failed: {error}").format(error=str(exc)[:60]),
                        )
        except Exception as exc:  # Catch unexpected errors to restore UI properly
            failures.append({"url": "unexpected", "error": str(exc)})

        self.root.after(
            0,
            self._on_batch_download_complete,
            tasks,
            success_count,
            failures,
            ignored_links,
            duplicate_links,
        )

    def _report_profile_batch_progress(self, index, total, payload):
        """Route profile progress updates to the inline status widget."""
        message = payload.get("message")
        current = payload.get("current")
        total_videos = payload.get("total")
        video_name = payload.get("video_name") or ""
        status = payload.get("status")

        if not message and current and total_videos:
            message = self.tr(
                "batch_profile_video_progress",
                "Downloading {current}/{total}: {video}",
            ).format(current=current, total=total_videos, video=video_name[:40])

        if not message:
            message = self.tr("batch_profile_processing", "Processing profile downloads...")

        prefix = self.tr("batch_progress_prefix", "[{index}/{total}]").format(index=index, total=total)

        def update():
            text = f"{prefix} {message}"
            if status == "success":
                self.download_status.show_success(text)
            elif status in {"failed", "error"}:
                method = self.download_status.show_warning if status == "failed" else self.download_status.show_error
                method(text)
            else:
                self.download_status.show_info(text)

        self.root.after(0, update)

    def _on_batch_download_complete(self, tasks, success_count, failures, ignored_links, duplicate_links):
        """Handle UI updates after batch download finishes."""
        total = len(tasks)
        failed_count = len(failures)
        ignored_count = len(ignored_links)
        duplicate_count = len(duplicate_links)

        # Log detailed errors for debugging
        if failures:
            self.logger.info(f"Batch download completed with {failed_count} failures:")
            for idx, failure in enumerate(failures, 1):
                url = failure.get("url", "Unknown URL")
                error = failure.get("error", "Unknown error")
                self.logger.error(f"  Failure {idx}: {url} - {error}")

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

        if duplicate_count:
            summary += " " + self.tr(
                "batch_complete_duplicates",
                "{duplicates} duplicates skipped.",
            ).format(duplicates=duplicate_count)

        # Show short status without detailed error messages
        if success_count == total and failed_count == 0:
            self.download_status.show_success(summary)
        elif success_count > 0:
            self.download_status.show_warning(summary)
        else:
            self.download_status.show_error(summary)

        self.download_btn.config(state="normal")

        self.is_batch_downloading = False
        self.url_entry.config(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_validation_label.config(text="")
        self.controller.clear_pending_batch()

    def _start_batch_download(self):
        """Initialize batch download after user confirmation."""
        if not self.controller.has_pending_batch() or not self.controller.batch_user_requested:
            return

        limit = self.controller.safe_int(self.config.get_setting("profile_video_limit", 0))
        prepared_batch = self.controller.prepare_pending_batch(limit)
        tasks = list(prepared_batch.tasks)
        ignored = list(prepared_batch.ignored_links)
        duplicates = list(prepared_batch.duplicate_links)
        limit_notice = ""
        if prepared_batch.skipped_due_to_limit:
            ignored.extend(task.url for task in prepared_batch.skipped_due_to_limit)
            limit_notice = self.tr(
                "batch_limit_notice",
                "Respecting limit of {limit} per profile. Skipping {skipped} extra entries.",
            ).format(limit=limit, skipped=len(prepared_batch.skipped_due_to_limit))

        if not tasks:
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
        self.url_entry.config(state="disabled")

        start_message = self.tr(
            "batch_start_message",
            "Starting batch download ({count} links)...",
        ).format(count=len(tasks))
        if limit_notice:
            start_message += " " + limit_notice
        self.download_status.show_info(start_message)

        thread = threading.Thread(
            target=self._batch_download_thread,
            args=(tasks, ignored, duplicates),
            daemon=True,
        )
        thread.start()

    def validate_url(self, event=None):
        """Validate URL in real-time and detect type"""
        if event is not None and self.controller.has_pending_batch():
            self.controller.clear_pending_batch()
            self.download_status.show_info(
                self.tr("batch_cancelled_message", "Batch import cleared. Ready for single download."),
            )

        analysis = self.controller.analyze_url(self.url_entry.get())
        
        if not analysis.url:
            self.url_validation_label.config(text="")
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_default", "\u2B07\uFE0F Download"))
            return
        
        # Check if it's a profile URL
        if analysis.is_profile:
            self.url_validation_label.config(
                text=self.tr("profile_url_detected", "\u2705 Profile URL detected - Bulk download mode"),
                fg=COLORS["accent"]
            )
            self.profile_options_frame.pack(pady=10)
            self.download_btn.config(text=self.tr("download_profile", "\u2B07\uFE0F Start Profile Download"))
            # Try to get profile info
            threading.Thread(target=self.fetch_profile_info, args=(analysis.url,), daemon=True).start()
        # Check if it's a video URL
        elif analysis.is_video:
            self.url_validation_label.config(
                text=self.tr("video_url_detected", "\u2705 Video URL detected - Single download mode"),
                fg=COLORS["success"]
            )
            self.profile_options_frame.pack_forget()
            self.download_btn.config(text=self.tr("download_video", "\u2B07\uFE0F Download Video"))
        # Valid TikTok URL but not sure which type
        elif analysis.is_valid:
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

        if self.controller.has_pending_batch():
            self.controller.mark_batch_requested()
            self._start_batch_download()
            return

        analysis = self.controller.analyze_url(self.url_entry.get())
        url = analysis.url
        
        if not url:
            self.download_status.show_error(self.tr("empty_url_error", "Please enter a URL"))
            return
        
        if not analysis.is_valid:
            self.download_status.show_error(self.tr("invalid_url_error", "Invalid TikTok URL"))
            return
        
        # Detect URL type and download
        if analysis.is_profile:
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
    
    def download_progress_callback(self, *args, **kwargs):
        """Update progress for profile downloads from scraper callbacks."""
        if self.should_stop:
            return

        # Normalise values so both legacy positional calls and newer keyword calls work.
        message = kwargs.get("message")
        current = kwargs.get("current")
        total = kwargs.get("total")
        video_name = kwargs.get("video_name")

        if not kwargs:
            current = args[0] if len(args) > 0 else current
            total = args[1] if len(args) > 1 else total
            video_name = args[2] if len(args) > 2 else video_name

        if video_name is None:
            video_name = ""

        # Wait while paused, keeping UI responsive.
        while self.is_paused and not self.should_stop:
            self.root.update()
            self.root.after(100)

        if message:
            progress_text = message
        else:
            progress_text = self.tr(
                "profile_progress_text",
                "Downloading {current}/{total}: {video}...",
            ).format(current=current or 0, total=total or 0, video=video_name[:40])

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

