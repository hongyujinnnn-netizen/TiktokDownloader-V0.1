"""
Configuration settings for TikTok Downloader
"""

import os
from pathlib import Path

# Application Info
APP_NAME = "TikTok Downloader Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"

# Paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Files
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LOG_FILE = DATA_DIR / "app.log"

# Theme Colors
DARK_THEME = {
    "background": "#0F172A",      # Dark blue background
    "card": "#1E293B",            # Card background
    "button": "#22C55E",          # Green button
    "button_hover": "#16A34A",    # Darker green on hover
    "danger": "#EF4444",          # Red for delete/cancel
    "danger_hover": "#DC2626",    # Darker red on hover
    "text": "#E5E7EB",            # Light gray text
    "text_secondary": "#9CA3AF",  # Secondary text
    "accent": "#38BDF8",          # Blue accent
    "secondary": "#8B5CF6",       # Purple secondary
    "secondary_hover": "#7C3AED", # Darker purple on hover
    "button_contrast": "#F8FAFC", # Text on colored buttons
    "success": "#10B981",         # Success green
    "warning": "#F59E0B",         # Warning orange
    "border": "#334155",          # Border color
}

LIGHT_THEME = {
    "background": "#F8FAFC",      # Light gray background
    "card": "#FFFFFF",            # White card background
    "button": "#22C55E",          # Green button
    "button_hover": "#16A34A",    # Darker green on hover
    "danger": "#EF4444",          # Red for delete/cancel
    "danger_hover": "#DC2626",    # Darker red on hover
    "text": "#1E293B",            # Dark text
    "text_secondary": "#64748B",  # Secondary text
    "accent": "#0EA5E9",          # Blue accent
    "secondary": "#8B5CF6",       # Purple secondary
    "secondary_hover": "#7C3AED", # Darker purple on hover
    "button_contrast": "#FFFFFF", # Text on colored buttons
    "success": "#10B981",         # Success green
    "warning": "#F59E0B",         # Warning orange
    "border": "#E2E8F0",          # Border color
}

# Default to Light Theme
COLORS = LIGHT_THEME.copy()

def set_theme(theme_name):
    """Set the application theme"""
    global COLORS
    if theme_name == "light":
        COLORS.update(LIGHT_THEME)
    else:
        COLORS.update(DARK_THEME)

# Fonts
FONTS = {
    "family": "Segoe UI",
    "title": ("Segoe UI", 24, "bold"),
    "title_large": ("Segoe UI", 32, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 11),
    "button": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 9),
    "emoji": ("Segoe UI Emoji", 11),
    "emoji_large": ("Segoe UI Emoji", 20),
}

# Download Settings
DEFAULT_SETTINGS = {
    "language": "en",
    "download_path": str(DOWNLOADS_DIR),
    "auto_update_ytdlp": True,
    "video_quality": "best",
    "save_history": True,
    "theme": "light",
    "profile_video_limit": 10,  # Default limit for profile downloads
    "convert_to_mp3": False,  # Default MP3 conversion setting
    "create_profile_folders": True,
}

# yt-dlp Options
YTDLP_OPTIONS = {
    'format': 'best',
    'outtmpl': '%(title)s.%(ext)s',
    'quiet': False,
    'no_warnings': False,
    'extract_flat': False,
}

# Supported Languages
LANGUAGES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "km": "ភាសាខ្មែរ",
}
