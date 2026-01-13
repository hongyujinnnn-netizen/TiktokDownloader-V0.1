# 🎵 TikTok Downloader Pro

A professional, feature-rich TikTok video downloader with a modern GUI built with Python and tkinter.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🎉 Latest Updates

**Enhanced Professional UX!** This version includes major user experience improvements:
- ✅ Real-time progress bars with percentage
- ✅ One-click paste button with URL validation
- ✅ Inline status messages (less popups!)
- ✅ Interactive history with filters and search
- ✅ Pause/Resume/Stop controls for bulk downloads
- ✅ Organized settings with tabs
- ✅ Keyboard shortcuts for power users

[See What's New →](WHATS_NEW.md) | [Full UX Improvements →](UX_IMPROVEMENTS.md)

## ✨ Features

### Core Features
- ✅ **Single Video Download** - Download any TikTok video by pasting the URL
- ✅ **Profile Bulk Download** - Download multiple videos from any TikTok profile
- ✅ **Selective Download** - Choose how many videos to download from a profile (e.g., 100 out of 1000)
- ✅ **Auto-create Folders** - Automatically creates download folders with profile names
- ✅ **Smart File Naming** - Intelligent file naming system
- ✅ **Error Handling** - Comprehensive error handling with user-friendly popups

### Advanced Features
- 🔥 **MP3 Conversion** - Convert videos to MP3 audio files
- 🔥 **Download History** - Track all your downloads
- 🔥 **Auto-update yt-dlp** - Keep the downloader up-to-date automatically
- 🔥 **Multi-language Support** - English and Bahasa Indonesia (easily expandable)
- 🔥 **Quality Selection** - Choose video quality (Best, High, Medium, Low)
- 🔥 **Skip Downloaded** - Skip already downloaded videos in bulk operations
- 🔥 **Progress Tracking** - Real-time progress updates for bulk downloads

### Professional Design
- 🎨 **Modern Dark Theme** with professional color scheme:
  - Background: `#0F172A` (dark blue)
  - Card: `#1E293B`
  - Button: `#22C55E` (green)
  - Text: `#E5E7EB`
  - Accent: `#38BDF8`
- 🖋 **Segoe UI Font** - Clean, professional typography
- 🎯 **Intuitive Interface** - User-friendly design

## 📋 Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Internet connection

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/hongyujinnnn-netizen/TiktokDownloader-V0.1.git
cd TiktokDownloader-V1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python run.py
```

## 📦 Dependencies

- **yt-dlp** - Core download functionality
- **tkinter** - GUI framework (usually comes with Python)
- **customtkinter** - Modern UI components
- **pillow** - Image processing
- **pydub** - Audio conversion
- **validators** - URL validation
- **requests** - HTTP requests

## 🎯 Usage

### Single Video Download
1. Launch the application
2. Paste a TikTok video URL in the input field
3. (Optional) Check "Convert to MP3" for audio-only
4. Click "Download Video"
5. Wait for the download to complete

### Profile Bulk Download
1. Click "Open Profile Downloader"
2. Paste a TikTok profile URL
3. Click "Check Profile" to see how many videos are available
4. Set the number of videos to download (0 = all)
5. Configure options:
   - Create separate folder for this profile
   - Convert to MP3
   - Skip already downloaded videos
6. Click "Start Bulk Download"
7. Monitor progress in the log window

### Settings Configuration
1. Click "Settings" button
2. Configure:
   - Download location
   - Language
   - Video quality
   - Auto-update options
   - History settings
3. Click "Save Settings"

## 📁 Project Structure

```
TiktokDownloader-V1/
├── src/
│   ├── gui/                    # GUI modules
│   │   ├── main_window.py      # Main application window
│   │   ├── profile_downloader.py  # Profile bulk downloader
│   │   ├── history_window.py   # Download history viewer
│   │   ├── settings_window.py  # Settings configuration
│   │   └── styles.py           # UI styling utilities
│   ├── core/                   # Core functionality
│   │   ├── downloader.py       # Single video downloader
│   │   ├── profile_scraper.py  # Profile video scraper
│   │   ├── converter.py        # Audio/video converter
│   │   └── updater.py          # yt-dlp updater
│   ├── utils/                  # Utility modules
│   │   ├── file_manager.py     # File operations
│   │   ├── logger.py           # Logging system
│   │   ├── validators.py       # Input validation
│   │   └── config_manager.py   # Configuration management
│   ├── locales/                # Language files
│   │   ├── en.py               # English
│   │   └── id.py               # Bahasa Indonesia
│   └── main.py                 # Application entry point
├── assets/                     # Assets and resources
│   ├── icons/                  # Application icons
│   └── images/                 # Images and logos
├── data/                       # Application data
│   ├── history.json            # Download history
│   └── settings.json           # User settings
├── downloads/                  # Default download folder
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── run.py                      # Application launcher
└── README.md                   # This file
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Colors
COLORS = {
    "background": "#0F172A",
    "card": "#1E293B",
    "button": "#22C55E",
    # ... more colors
}

# Fonts
FONTS = {
    "family": "Segoe UI",
    "title": ("Segoe UI", 24, "bold"),
    # ... more fonts
}

# Download Settings
DEFAULT_SETTINGS = {
    "language": "en",
    "download_path": "downloads",
    "auto_update_ytdlp": True,
    "video_quality": "best",
    "profile_video_limit": 100,
}
```

## 🌍 Adding Languages

To add a new language:

1. Create a new file in `src/locales/` (e.g., `es.py` for Spanish)
2. Copy the structure from `en.py`
3. Translate all strings
4. Add the language to `LANGUAGES` in `config.py`:

```python
LANGUAGES = {
    "en": "English",
    "id": "Bahasa Indonesia",
    "es": "Español",  # Add your language here
}
```

## 🐛 Troubleshooting

### yt-dlp Issues
If downloads fail, try updating yt-dlp:
- Click "Settings" → "Update yt-dlp Now"
- Or run: `pip install --upgrade yt-dlp`

### FFmpeg Not Found (for MP3 conversion)
Install FFmpeg:
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### Permission Errors
Run with administrator/sudo privileges if you encounter permission errors.

## 🔧 Development

### Running in Development Mode
```bash
python src/main.py
```

### Building Executable (Optional)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icons/app_icon.ico run.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect TikTok's Terms of Service and copyright laws. Only download content you have permission to download.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

For issues, questions, or suggestions, please open an issue on GitHub.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful download engine
- [tkinter](https://docs.python.org/3/library/tkinter.html) - Python's standard GUI package
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI components

---

Made with ❤️ by Ryu

**Star ⭐ this repository if you find it helpful!**
