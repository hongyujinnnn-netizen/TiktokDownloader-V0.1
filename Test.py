import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import webbrowser
import re
import json
import time
from PIL import Image, ImageTk
import requests
from io import BytesIO
import tempfile
from urllib.parse import urlparse

# Global configuration and state
DOWNLOAD_FOLDER = os.path.expanduser("~")  # Default download folder
CONFIG_FILE = "tiktok_downloader_config.json"
HISTORY_FILE = "download_history.json"
PAUSED = False
STOP = False
TOTAL_COUNT = 0
SUCCESS_COUNT = 0
ERROR_COUNT = 0
DARK_MODE = False  # Fixed typo from DARK_MODE to DARK_MODE
MAX_RETRIES = 3

LIGHT_THEME = {
    "primary": "#4a6fa5",
    "secondary": "#6c8fc7",
    "accent": "#d65745",
    "bg": "#f5f5f5",
    "text": "#333333",
    "widget_bg": "#ffffff",
    "progress_trough": "#e0e0e0"
}

DARK_THEME = {
    "primary": "#3a4a6a",
    "secondary": "#4a5a7a",
    "accent": "#c54737",
    "bg": "#2d2d2d",
    "text": "#e0e0e0",
    "widget_bg": "#3d3d3d",
    "progress_trough": "#4d4d4d"
}

current_theme = LIGHT_THEME
running_processes = []

class ImageManager:
    """Class to manage image references and prevent garbage collection"""
    def __init__(self):
        self.images = []
        self.social_icons = {}
        self.thumbnail_cache = {}
        self.thumbnail_temp_dir = tempfile.mkdtemp(prefix="tiktok_thumbnails_")
    
    def add_image(self, image):
        """Add an image reference to prevent garbage collection"""
        self.images.append(image)
        return image
    
    def clear_temp_files(self):
        """Clean up temporary files and image references"""
        self.images.clear()
        self.social_icons.clear()
        
        # Clean up thumbnail cache directory
        for filename in os.listdir(self.thumbnail_temp_dir):
            file_path = os.path.join(self.thumbnail_temp_dir, filename)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting temp file {file_path}: {e}")
        try:
            os.rmdir(self.thumbnail_temp_dir)
        except Exception as e:
            print(f"Error removing temp dir: {e}")

def load_config():
    """Load configuration from file"""
    global DOWNLOAD_FOLDER, DARK_MODE
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                DOWNLOAD_FOLDER = config.get('download_folder', DOWNLOAD_FOLDER)
                DARK_MODE = config.get('dark_mode', DARK_MODE)
    except Exception as e:
        print(f"Error loading config: {e}")
        config = {
            'download_folder': DOWNLOAD_FOLDER,
            'dark_mode': DARK_MODE
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

def save_config():
    """Save configuration to file"""
    try:
        config = {
            'download_folder': DOWNLOAD_FOLDER,
            'dark_mode': DARK_MODE
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")

def load_history():
    """Load download history"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
    return []

def save_history(history):
    """Save download history"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def is_profile_url(url):
    """Check if URL is a TikTok profile"""
    patterns = [
        r'tiktok\.com\/@[^\/]+$',
        r'tiktok\.com\/@[^\/]+\/live',
        r'vm\.tiktok\.com\/[^\/]+',
        r'www\.tiktok\.com\/t\/[^\/]+'
    ]
    url = url.lower()
    return any(re.search(pattern, url) for pattern in patterns)

def extract_percentage(output_line):
    """Extract download percentage from yt-dlp output"""
    percentage_match = re.search(r'(\d+\.\d+)%', output_line)
    if percentage_match:
        return float(percentage_match.group(1))
    return None

def download_video(url, status_label, progress_var, progress_bar, quality, history_listbox=None):
    """Download a single URL with progress updates"""
    global SUCCESS_COUNT, ERROR_COUNT, TOTAL_COUNT, PAUSED, STOP

    retries = 0
    while retries < MAX_RETRIES:
        try:
            while PAUSED and not STOP:
                threading.Event().wait(0.5)
            
            if STOP:
                return

            TOTAL_COUNT += 1
            progress_var.set(0)
            progress_bar.update()
            
            yt_dlp_path = "yt-dlp"
            
            if is_profile_url(url):
                out_template = os.path.join(DOWNLOAD_FOLDER, "%(uploader)s", "%(title).80s.%(ext)s")
            else:
                out_template = os.path.join(DOWNLOAD_FOLDER, "%(title).80s.%(ext)s")
            
            cmd = [
                yt_dlp_path,
                "--no-warning",
                "--no-check-certificate",
                "--socket-timeout", "30",
                "-o", out_template
            ]
            
            if is_profile_url(url):
                cmd.append("--yes-playlist")
            
            if quality == "Best":
                cmd.extend(["--format", "best"])
            elif quality == "1080p":
                cmd.extend(["--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"])
            elif quality == "720p":
                cmd.extend(["--format", "bestvideo[height<=720]+bestaudio/best[height<=720]"])
            elif quality == "480p":
                cmd.extend(["--format", "bestvideo[height<=480]+bestaudio/best[height<=480]"])
            
            cmd.extend(["--user-agent", "Mozilla/5.0"])
            cmd.append(url)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            running_processes.append(process)

            while True:
                if STOP:
                    process.terminate()
                    break
                    
                output_line = process.stdout.readline()
                if output_line:
                    if '[download]' in output_line:
                        status_label.config(text=output_line.strip())
                        percentage = extract_percentage(output_line)
                        if percentage is not None:
                            progress_var.set(percentage)
                            progress_bar.update()
                
                if process.poll() is not None:
                    break
            
            stdout, stderr = process.communicate()
            
            if process in running_processes:
                running_processes.remove(process)
            
            if process.returncode == 0:
                SUCCESS_COUNT += 1
                status_text = "Download completed successfully!"
                progress_var.set(100)
                
                history_entry = {
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Success",
                    "quality": quality
                }
                history = load_history()
                history.append(history_entry)
                save_history(history)
                
                if history_listbox:
                    history_listbox.insert(0, f"{history_entry['date']} - {url} ({quality})")
                break
            else:
                ERROR_COUNT += 1
                status_text = f"Download failed: {stderr}"
                progress_var.set(0)
                retries += 1
                if retries < MAX_RETRIES:
                    status_label.config(text=f"Retrying ({retries}/{MAX_RETRIES})...")
                    time.sleep(2)
                else:
                    status_text = f"Failed after {MAX_RETRIES} attempts: {stderr}"

        except subprocess.CalledProcessError as e:
            ERROR_COUNT += 1
            status_text = f"Download failed: {e.stderr}"
            retries += 1
            if retries >= MAX_RETRIES:
                status_text = f"Failed after {MAX_RETRIES} attempts: {e.stderr}"
            else:
                status_label.config(text=f"Retrying ({retries}/{MAX_RETRIES})...")
                time.sleep(2)
        except Exception as e:
            ERROR_COUNT += 1
            status_text = f"Error: {str(e)}"
            progress_var.set(0)
            retries += 1
            if retries >= MAX_RETRIES:
                status_text = f"Failed after {MAX_RETRIES} attempts: {str(e)}"
            else:
                status_label.config(text=f"Retrying ({retries}/{MAX_RETRIES})...")
                time.sleep(2)

    final_status = f"Total: {TOTAL_COUNT} | Success: {SUCCESS_COUNT} | Error: {ERROR_COUNT}"
    status_label.after(0, lambda: status_label.config(text=final_status))

    if TOTAL_COUNT == (SUCCESS_COUNT + ERROR_COUNT):
        messagebox.showinfo("Download Complete", "All downloads finished!")
        try:
            os.startfile(DOWNLOAD_FOLDER)
        except:
            pass

class ModernButton(tk.Button):
    """Custom styled button with hover effects"""
    def __init__(self, master, text, command=None, custom_bg=None, is_action_button=True):
        bg_color = custom_bg if custom_bg else current_theme["primary"]
        text_color = "white"
        hover_color = current_theme["secondary"] if is_action_button else current_theme["accent"]
        
        super().__init__(
            master,
            text=text,
            command=command,
            font=("Arial", 10, "bold"),
            bg=bg_color,
            fg=text_color,
            activebackground=hover_color,
            activeforeground=text_color,
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.default_bg = bg_color
        self.hover_bg = hover_color
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=self.hover_bg)

    def on_leave(self, e):
        self.config(bg=self.default_bg)

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Downloader Pro V.1")
        self.image_manager = ImageManager()
        load_config()
        
        self.setup_ui()
        self.update_theme()
        self.update_datetime()

    def setup_ui(self):
        """Create all UI elements"""
        self.style = ttk.Style()
        self.setup_styles()
        
        self.main_frame = tk.Frame(self.root, bg=current_theme["bg"])
        self.main_frame.pack(fill="both", expand=True)
        
        self.setup_header()
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.setup_download_tab()
        self.setup_history_tab()
        self.setup_footer()

    def setup_styles(self):
        """Configure ttk styles"""
        self.style.configure(
            "Orange.Horizontal.TProgressbar",
            troughcolor=current_theme["progress_trough"],
            background=current_theme["accent"],
            thickness=20
        )
        self.style.configure(
            "TNotebook",
            background=current_theme["bg"]
        )
        self.style.configure(
            "TNotebook.Tab",
            background=current_theme["bg"],
            foreground=current_theme["text"],
            font=("Arial", 10, "bold")
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", current_theme["primary"])],
            foreground=[("selected", "white")]
        )

    def setup_header(self):
        """Create header with logo, title and theme toggle"""
        self.header = tk.Frame(self.main_frame, bg=current_theme["bg"])
        self.header.pack(fill="x", padx=10, pady=(10, 5))
        
        # Create container for logo and title
        logo_title_container = tk.Frame(self.header, bg=current_theme["bg"])
        logo_title_container.pack(side="left", fill="x", expand=True)
        
        # Add logo with proper reference keeping
        try:
            # Try to load logo from different possible locations
            logo_path = None
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "logo.png"),
                "logo.png",
                os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
                "assets/logo.png"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
                    
            if logo_path:
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((40, 40), Image.LANCZOS)
                self.logo_photo = self.image_manager.add_image(ImageTk.PhotoImage(logo_img))
                
                self.logo_label = tk.Label(
                    logo_title_container,
                    image=self.logo_photo,
                    bg=current_theme["bg"]
                )
                self.logo_label.pack(side="left", padx=(0, 10))
            else:
                raise FileNotFoundError("Logo image not found")
                
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback to text if logo can't be loaded
            self.logo_label = tk.Label(
                logo_title_container,
                text="TikTok",
                font=("Arial", 12, "bold"),
                bg=current_theme["bg"],
                fg=current_theme["text"]
            )
            self.logo_label.pack(side="left", padx=(0, 10))
        
        # Add title next to logo
        self.title_label = tk.Label(
            logo_title_container,
            text="TikTok Video Downloader Pro",
            font=("Arial", 20, "bold"),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        )
        self.title_label.pack(side="left")
        
        # Theme toggle button on the right
        self.theme_btn = ModernButton(
            self.header,
            text="☀️" if not DARK_MODE else "🌙",
            command=self.toggle_theme,
            custom_bg=current_theme["accent"],
            is_action_button=False
        )
        self.theme_btn.pack(side="right", padx=5)
        
        # Date label next to theme button
        self.date_label = tk.Label(
            self.header,
            font=("Arial", 11),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        )
        self.date_label.pack(side="right", padx=10)

    def setup_download_tab(self):
        """Create the download tab"""
        self.download_tab = tk.Frame(self.notebook, bg=current_theme["bg"])
        self.notebook.add(self.download_tab, text="Download")
        
        # URL input with thumbnail preview
        url_frame = tk.Frame(self.download_tab, bg=current_theme["bg"])
        url_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        url_container = tk.Frame(url_frame, bg=current_theme["bg"])
        url_container.pack(fill="both", expand=True)
        
        # URL text on left
        url_input_frame = tk.Frame(url_container, bg=current_theme["bg"])
        url_input_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(
            url_input_frame,
            text="TikTok Video/Profile URLs:",
            font=("Arial", 11, "bold"),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        ).pack(anchor="w")
        
        self.url_text = tk.Text(
            url_input_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            height=8,
            relief="flat",
            padx=10,
            pady=10,
            bg=current_theme["widget_bg"],
            fg=current_theme["text"],
            selectbackground=current_theme["primary"],
            selectforeground="white"
        )
        self.url_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # Thumbnail preview on right
        self.preview_frame = tk.Frame(
            url_container,
            bg=current_theme["bg"],
            width=200,
            height=200
        )
        self.preview_frame.pack(side="right", fill="y", padx=(10, 0))
        self.preview_frame.pack_propagate(False)
        
        self.thumbnail_label = tk.Label(
            self.preview_frame,
            bg=current_theme["widget_bg"],
            text="Thumbnail Preview",
            font=("Arial", 10),
            wraplength=180
        )
        self.thumbnail_label.pack(fill="both", expand=True)
        
        # Bind URL text changes to update preview
        self.url_text.bind("<KeyRelease>", self.update_thumbnail_preview)
        self.url_text.bind("<ButtonRelease>", self.update_thumbnail_preview)
        
        # Quality selection
        quality_frame = tk.Frame(self.download_tab, bg=current_theme["bg"])
        quality_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            quality_frame,
            text="Video Quality:",
            font=("Arial", 11, "bold"),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        ).pack(side="left")
        
        self.quality_var = tk.StringVar(value="Best")
        qualities = ["Best", "1080p", "720p", "480p"]
        for quality in qualities:
            rb = tk.Radiobutton(
                quality_frame,
                text=quality,
                variable=self.quality_var,
                value=quality,
                font=("Arial", 11),
                bg=current_theme["bg"],
                fg=current_theme["text"],
                selectcolor=current_theme["bg"],
                activebackground=current_theme["bg"],
                activeforeground=current_theme["text"]
            )
            rb.pack(side="left", padx=5)
        
        # Progress bar
        progress_frame = tk.Frame(self.download_tab, bg=current_theme["bg"])
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient="horizontal",
            length=100,
            mode="determinate",
            variable=self.progress_var,
            style="Orange.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", expand=True)
        
        # Status label
        self.status_label = tk.Label(
            self.download_tab,
            text="Ready",
            font=("Arial", 11),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        )
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # Folder selection
        folder_frame = tk.Frame(self.download_tab, bg=current_theme["bg"])
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        self.folder_label = tk.Label(
            folder_frame,
            text=f"Save Folder: {DOWNLOAD_FOLDER}",
            font=("Arial", 11),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        )
        self.folder_label.pack(side="left", fill="x", expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.download_tab, bg=current_theme["bg"])
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ModernButton(
            button_frame,
            text="Save To Folder",
            command=self.browse_folder
        ).pack(side="left", padx=5)
        
        ModernButton(
            button_frame,
            text="Import from File",
            command=self.import_urls
        ).pack(side="left", padx=5)
        
        ModernButton(
            button_frame,
            text="Download",
            command=self.start_downloads
        ).pack(side="left", padx=5)
        
        self.pause_btn = ModernButton(
            button_frame,
            text="Pause",
            command=self.toggle_pause,
            custom_bg=current_theme["secondary"]
        )
        self.pause_btn.pack(side="left", padx=5)
        
        ModernButton(
            button_frame,
            text="Stop",
            command=self.stop_downloads,
            custom_bg=current_theme["accent"],
            is_action_button=False
        ).pack(side="left", padx=5)

    def setup_history_tab(self):
        """Create the history tab"""
        self.history_tab = tk.Frame(self.notebook, bg=current_theme["bg"])
        self.notebook.add(self.history_tab, text="History")
        
        # History listbox with scrollbar
        history_frame = tk.Frame(self.history_tab, bg=current_theme["bg"])
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.history_listbox = tk.Listbox(
            history_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 11),
            bg=current_theme["widget_bg"],
            fg=current_theme["text"],
            selectbackground=current_theme["primary"],
            selectforeground="white",
            relief="flat",
            height=15
        )
        self.history_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Load history
        history = load_history()
        for entry in reversed(history):
            self.history_listbox.insert(0, f"{entry['date']} - {entry['url']} ({entry['quality']})")
        
        # History controls
        controls_frame = tk.Frame(self.history_tab, bg=current_theme["bg"])
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ModernButton(
            controls_frame,
            text="Clear History",
            command=self.clear_history,
            custom_bg=current_theme["accent"],
            is_action_button=False
        ).pack(side="left", padx=5)
        
        ModernButton(
            controls_frame,
            text="Copy URL",
            command=self.copy_history_url
        ).pack(side="left", padx=5)
        
        ModernButton(
            controls_frame,
            text="Redownload",
            command=self.redownload_from_history
        ).pack(side="left", padx=5)

    def setup_footer(self):
        """Create footer with creator info and social media"""
        self.footer = tk.Frame(self.main_frame, bg=current_theme["bg"])
        self.footer.pack(fill="x", padx=10, pady=(0, 10))
        
        # Creator info on left
        creator_frame = tk.Frame(self.footer, bg=current_theme["bg"])
        creator_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            creator_frame,
            text="Created by BunHong",
            font=("Arial", 9),
            bg=current_theme["bg"],
            fg=current_theme["text"]
        ).pack(side="left")
        
        # Social media buttons on right
        self.setup_social_media(self.footer)

    def setup_social_media(self, parent_frame):
        """Add social media buttons to the footer"""
        self.social_frame = tk.Frame(parent_frame, bg=current_theme["bg"])
        self.social_frame.pack(side="right", padx=10)
        
        # Social media platforms with their icons and URLs
        social_platforms = [
            ("facebook", "https://web.facebook.com/domma.vea"),
            ("telegram", "https://t.me/hongnacap"),
            ("instagram", "https://www.instagram.com/jacobson123_/"),
            ("youtube", "https://www.youtube.com/watch?v=m_XUClQCOUc")
        ]
        
        for platform, url in social_platforms:
            try:
                # Try to load theme-specific icon first
                theme_suffix = "_dark" if DARK_MODE else "_light"
                try:
                    img = Image.open(f"icons/{platform}{theme_suffix}.png")
                except FileNotFoundError:
                    # Fallback to default icon if theme-specific not available
                    img = Image.open(f"icons/{platform}.png")
                    
                img = img.resize((24, 24), Image.LANCZOS)
                photo = self.image_manager.add_image(ImageTk.PhotoImage(img))
                self.image_manager.social_icons[platform] = photo  # Store reference
                
                btn = tk.Button(
                    self.social_frame,
                    image=photo,
                    bg=current_theme["bg"],
                    activebackground=current_theme["bg"],
                    borderwidth=0,
                    cursor="hand2",
                    command=lambda u=url: webbrowser.open_new(u)
                )
                btn.pack(side="left", padx=5)
            except Exception as e:
                print(f"Error loading {platform} icon: {e}")
                # Fallback to text button if image fails
                btn = tk.Label(
                    self.social_frame,
                    text=platform.capitalize(),
                    font=("Arial", 9, "underline"),
                    bg=current_theme["bg"],
                    fg=current_theme["primary"],
                    cursor="hand2"
                )
                btn.pack(side="left", padx=2)
                btn.bind("<Button-1>", lambda e, u=url: webbrowser.open_new(u))

    def update_thumbnail_preview(self, event=None):
        """Update the thumbnail preview based on current URL selection"""
        try:
            # Get the URL at cursor position
            cursor_pos = self.url_text.index(tk.INSERT)
            line_num = int(cursor_pos.split('.')[0])
            line_text = self.url_text.get(f"{line_num}.0", f"{line_num}.end")
            
            # Extract URL from line
            url_match = re.search(r'https?://[^\s]+', line_text)
            if not url_match:
                self.thumbnail_label.config(
                    text="No URL selected",
                    image=''
                )
                return
                
            url = url_match.group(0)
            
            # Check cache first
            if url in self.image_manager.thumbnail_cache:
                img, _ = self.image_manager.thumbnail_cache[url]
                photo = self.image_manager.add_image(ImageTk.PhotoImage(img))
                self.thumbnail_label.config(image=photo, text='')
                return
                
            # Not in cache, fetch new thumbnail
            self.thumbnail_label.config(text="Fetching preview...")
            
            # Run in thread to prevent UI freeze
            threading.Thread(
                target=self._fetch_and_display_thumbnail,
                args=(url,),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Error updating thumbnail: {e}")
            self.thumbnail_label.config(text="Preview unavailable")

    def _fetch_and_display_thumbnail(self, url):
        """Background task to fetch and display thumbnail"""
        try:
            thumbnail_url = self.extract_thumbnail_url(url)
            if not thumbnail_url:
                self.root.after(0, lambda: self.thumbnail_label.config(
                    text="No preview available"
                ))
                return
                
            img = self.download_thumbnail(thumbnail_url)
            if img:
                # Add to cache
                self.image_manager.thumbnail_cache[url] = (img, time.time())
                self.cleanup_thumbnail_cache()
                
                # Update UI
                photo = self.image_manager.add_image(ImageTk.PhotoImage(img))
                self.root.after(0, lambda: self._display_thumbnail(photo))
        except Exception as e:
            print(f"Error in thumbnail thread: {e}")
            self.root.after(0, lambda: self.thumbnail_label.config(
                text="Preview error"
            ))

    def _display_thumbnail(self, photo_image):
        """Display the thumbnail image in the UI"""
        self.thumbnail_label.config(image=photo_image, text='')

    def extract_thumbnail_url(self, video_url):
        """Extract thumbnail URL from TikTok video URL"""
        try:
            cmd = [
                "yt-dlp",
                "--get-thumbnail",
                "--no-warning",
                video_url
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Error extracting thumbnail: {e}")
        return None

    def download_thumbnail(self, thumbnail_url):
        """Download and resize thumbnail"""
        try:
            response = requests.get(thumbnail_url, stream=True, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img.thumbnail((200, 200))  # Resize for preview
                return img
        except Exception as e:
            print(f"Error downloading thumbnail: {e}")
        return None

    def cleanup_thumbnail_cache(self):
        """Clean up old thumbnails from cache"""
        if len(self.image_manager.thumbnail_cache) > 50:  # Keep max 50 thumbnails in cache
            sorted_items = sorted(
                self.image_manager.thumbnail_cache.items(),
                key=lambda x: x[1][1]  # Sort by timestamp
            )
            for url, _ in sorted_items[:len(self.image_manager.thumbnail_cache) - 50]:
                del self.image_manager.thumbnail_cache[url]

    def update_theme(self):
        """Update all widgets to reflect current theme"""
        global current_theme
        current_theme = DARK_THEME if DARK_MODE else LIGHT_THEME
        
        # Update main window and widgets
        self.main_frame.config(bg=current_theme["bg"])
        
        for widget in self.main_frame.winfo_children():
            self.update_widget_colors(widget)
        
        # Update progress bar style
        self.style.configure(
            "Orange.Horizontal.TProgressbar",
            troughcolor=current_theme["progress_trough"],
            background=current_theme["accent"]
        )
        
        # Update notebook style
        self.style.configure(
            "TNotebook",
            background=current_theme["bg"]
        )
        self.style.configure(
            "TNotebook.Tab",
            background=current_theme["bg"],
            foreground=current_theme["text"]
        )
        
        # Update theme button
        self.theme_btn.config(
            text="☀️" if not DARK_MODE else "🌙",
            bg=current_theme["accent"]
        )

    def update_widget_colors(self, widget):
        """Recursively update widget colors"""
        try:
            # Skip image-based widgets
            if isinstance(widget, (tk.Label, tk.Button)) and hasattr(widget, 'image'):
                return
                
            if isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame):
                widget.config(bg=current_theme["bg"])
            elif isinstance(widget, tk.Label):
                widget.config(bg=current_theme["bg"], fg=current_theme["text"])
            elif isinstance(widget, tk.Text):
                widget.config(
                    bg=current_theme["widget_bg"],
                    fg=current_theme["text"],
                    selectbackground=current_theme["primary"],
                    selectforeground="white"
                )
            elif isinstance(widget, tk.Listbox):
                widget.config(
                    bg=current_theme["widget_bg"],
                    fg=current_theme["text"],
                    selectbackground=current_theme["primary"],
                    selectforeground="white"
                )
            elif isinstance(widget, tk.Button):
                if widget['text'] in ["Pause", "Resume"]:
                    widget.config(bg=current_theme["secondary"])
                elif widget['text'] in ["Stop", "Clear History"]:
                    widget.config(bg=current_theme["accent"])
                else:
                    widget.config(bg=current_theme["primary"])
            
            for child in widget.winfo_children():
                self.update_widget_colors(child)
        except Exception as e:
            print(f"Error updating widget colors: {e}")

    def update_datetime(self):
        """Update the date/time display"""
        now = datetime.now()
        formatted_time = now.strftime("%B %d, %Y %I:%M:%S %p")
        self.date_label.config(text=formatted_time)
        self.root.after(1000, self.update_datetime)

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        global DARK_MODE
        DARK_MODE = not DARK_MODE
        save_config()
        
        # Clear old image references and recreate social media buttons
        self.image_manager.clear_temp_files()
        if hasattr(self, 'social_frame'):
            self.social_frame.destroy()
            self.setup_social_media(self.footer)
        
        self.update_theme()

    def browse_folder(self):
        """Select download folder"""
        global DOWNLOAD_FOLDER
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            DOWNLOAD_FOLDER = folder_selected
            self.folder_label.config(text=f"Save Folder: {DOWNLOAD_FOLDER}")
            save_config()

    def import_urls(self):
        """Import URLs from a text file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    urls = f.read()
                    self.url_text.delete("1.0", tk.END)
                    self.url_text.insert("1.0", urls)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def start_downloads(self):
        """Start downloading all URLs"""
        urls = self.url_text.get("1.0", tk.END).splitlines()
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showwarning("Warning", "Please enter at least one URL")
            return

        global PAUSED, STOP, TOTAL_COUNT, SUCCESS_COUNT, ERROR_COUNT
        PAUSED = False
        STOP = False
        TOTAL_COUNT = SUCCESS_COUNT = ERROR_COUNT = 0
        
        quality = self.quality_var.get()
        
        for url in urls:
            t = threading.Thread(
                target=download_video, 
                args=(url, self.status_label, self.progress_var, self.progress_bar, quality, self.history_listbox),
                daemon=True
            )
            t.start()

    def toggle_pause(self):
        """Toggle pause/resume"""
        global PAUSED
        PAUSED = not PAUSED
        self.pause_btn.config(
            text="Resume" if PAUSED else "Pause",
            bg=current_theme["secondary"]
        )

    def stop_downloads(self):
        """Stop all downloads"""
        global STOP
        STOP = True
        for process in running_processes:
            try:
                process.terminate()
            except:
                pass
        self.status_label.config(text="Downloads stopped")
        self.progress_var.set(0)

    def clear_history(self):
        """Clear download history"""
        if messagebox.askyesno("Confirm", "Clear all download history?"):
            save_history([])
            self.history_listbox.delete(0, tk.END)

    def copy_history_url(self):
        """Copy selected history URL to clipboard"""
        selection = self.history_listbox.curselection()
        if selection:
            entry = self.history_listbox.get(selection[0])
            url = entry.split(" - ")[1].split(" (")[0]
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            messagebox.showinfo("Copied", "URL copied to clipboard")

    def redownload_from_history(self):
        """Redownload selected history item"""
        selection = self.history_listbox.curselection()
        if selection:
            entry = self.history_listbox.get(selection[0])
            url = entry.split(" - ")[1].split(" (")[0]
            quality = entry.split("(")[1].rstrip(")")
            
            self.url_text.delete("1.0", tk.END)
            self.url_text.insert("1.0", url)
            self.quality_var.set(quality)
            self.start_downloads()

def check_requirements():
    """Check if required tools are installed"""
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True)
        return True
    except:
        messagebox.showerror(
            "Error",
            "yt-dlp not found. Please install it with:\n\npip install yt-dlp"
        )
        return False

def main():
    root = tk.Tk()
    root.geometry("950x600")
    root.minsize(700, 500)
    
    # Set window icon with multiple fallbacks
    icon_paths = [
        os.path.join(os.path.dirname(__file__), "logo.ico"),
        "logo.ico",
        os.path.join(os.path.dirname(__file__), "logo.png"),
        "logo.png",
        os.path.join(os.path.dirname(__file__), "assets", "logo.ico"),
        "assets/logo.ico",
        os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
        "assets/logo.png"
    ]
    
    icon_set = False
    for path in icon_paths:
        try:
            if path.endswith('.ico'):
                root.iconbitmap(path)
                icon_set = True
                break
            elif path.endswith('.png'):
                img = Image.open(path)
                photo = ImageTk.PhotoImage(img)
                root.tk.call('wm', 'iconphoto', root._w, photo)
                icon_set = True
                break
        except Exception as e:
            continue
    
    if not icon_set:
        print("Warning: Could not load window icon from any path")
    
    if not check_requirements():
        return
    
    load_config()
    app = DownloaderApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [app.image_manager.clear_temp_files(), save_config(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()