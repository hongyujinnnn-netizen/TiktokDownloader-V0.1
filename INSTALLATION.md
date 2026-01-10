# 🚀 Installation & Setup Guide

## Quick Setup (5 minutes)

### Step 1: Install Python
1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```bash
   python --version
   ```

### Step 2: Install Dependencies
```bash
cd d:\Developer-AI\TiktokDownloder-V1
pip install -r requirements.txt
```

**What gets installed:**
- yt-dlp - Core downloader
- pyperclip - Clipboard/paste button
- validators - URL validation
- tkinter - GUI (usually included with Python)
- pydub - MP3 conversion
- And more...

### Step 3: Install FFmpeg (for MP3)
**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Search "Environment Variables"
   - Edit "Path"
   - Add `C:\ffmpeg\bin`
4. Restart terminal

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Step 4: Run the App
```bash
python run.py
```

---

## Detailed Installation

### Windows Installation

#### 1. Python Setup
```powershell
# Check if Python installed
python --version

# If not installed:
# Download from python.org
# Install with "Add to PATH" checked
```

#### 2. Virtual Environment (Recommended)
```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\activate

# You should see (.venv) in prompt
```

#### 3. Install Dependencies
```powershell
# With venv activated
pip install -r requirements.txt

# Verify installation
pip list
```

#### 4. FFmpeg Setup
```powershell
# Download FFmpeg
# Extract to C:\ffmpeg
# Add C:\ffmpeg\bin to PATH

# Verify
ffmpeg -version
```

#### 5. Run
```powershell
python run.py
```

---

### macOS Installation

#### 1. Python Setup
```bash
# Check Python
python3 --version

# Install if needed (using Homebrew)
brew install python
```

#### 2. Virtual Environment
```bash
# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. FFmpeg
```bash
brew install ffmpeg
```

#### 5. Run
```bash
python3 run.py
```

---

### Linux Installation (Ubuntu/Debian)

#### 1. Python Setup
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install tkinter
sudo apt install python3-tk
```

#### 2. Virtual Environment
```bash
# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. FFmpeg
```bash
sudo apt install ffmpeg
```

#### 5. Run
```bash
python3 run.py
```

---

## Troubleshooting

### Common Issues

#### "python: command not found"
**Solution:**
- Reinstall Python with "Add to PATH" checked (Windows)
- Use `python3` instead of `python` (macOS/Linux)

#### "No module named 'tkinter'"
**Solution:**
```bash
# Windows: Reinstall Python, check "tcl/tk" option
# macOS: Already included
# Linux:
sudo apt install python3-tk
```

#### "pip install fails"
**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Try again
pip install -r requirements.txt
```

#### "ffmpeg not found"
**Solution:**
- Install FFmpeg (see Step 3 above)
- Restart terminal after installation
- Verify with `ffmpeg -version`

#### "Permission denied"
**Solution:**
```bash
# Linux/macOS: Use sudo
sudo pip install -r requirements.txt

# Windows: Run as Administrator
```

#### "pyperclip not working"
**Solution:**
```bash
# Reinstall
pip uninstall pyperclip
pip install pyperclip

# Linux: Install xclip
sudo apt install xclip
```

#### "Downloads fail"
**Solution:**
- Check internet connection
- Update yt-dlp:
  ```bash
  pip install --upgrade yt-dlp
  ```
- Or use app's Settings → Updates → Update Now

---

## Verification Checklist

After installation, verify:

- [ ] Python version 3.8+: `python --version`
- [ ] Pip working: `pip --version`
- [ ] Dependencies installed: `pip list | grep yt-dlp`
- [ ] FFmpeg installed: `ffmpeg -version`
- [ ] App launches: `python run.py`
- [ ] No errors in console
- [ ] GUI appears correctly

---

## First Run Setup

### 1. Launch App
```bash
python run.py
```

### 2. Configure Settings
1. Click **⚙ Settings**
2. Go to **📥 Download** tab
3. Set download location
4. Choose video quality
5. Click **💾 Save Settings**

### 3. Test Download
1. Copy a TikTok video URL
2. Click **📋 Paste** (or Ctrl+V)
3. Click **⬇ Download Video**
4. Check Downloads folder

### 4. Test Profile Download
1. Click **📂 Open Profile Downloader**
2. Paste a profile URL
3. Click **🔍 Check Profile**
4. Set limit to 3 (for testing)
5. Click **⬇ Start Bulk Download**
6. Test Pause/Stop buttons

---

## Optional: Create Desktop Shortcut

### Windows
1. Right-click on desktop
2. New → Shortcut
3. Location: `C:\Python39\pythonw.exe "D:\Developer-AI\TiktokDownloder-V1\run.py"`
4. Name: "TikTok Downloader Pro"
5. Change icon (optional)

### macOS
Create Automator app:
1. Open Automator
2. New → Application
3. Add "Run Shell Script"
4. Script: `cd /path/to/app && python3 run.py`
5. Save as "TikTok Downloader Pro.app"

### Linux
Create `.desktop` file:
```bash
nano ~/.local/share/applications/tiktok-downloader.desktop
```

Content:
```ini
[Desktop Entry]
Name=TikTok Downloader Pro
Exec=/path/to/.venv/bin/python /path/to/run.py
Icon=/path/to/icon.png
Type=Application
Categories=Network;
```

---

## Building Executable (Advanced)

### Using PyInstaller

#### 1. Install PyInstaller
```bash
pip install pyinstaller
```

#### 2. Create Executable
```bash
# Windows
pyinstaller --onefile --windowed --icon=assets/icons/app_icon.ico run.py

# macOS/Linux
pyinstaller --onefile --windowed run.py
```

#### 3. Find Executable
- Windows: `dist\run.exe`
- macOS: `dist/run.app`
- Linux: `dist/run`

#### 4. Test
Double-click the executable!

---

## Updating the App

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Update yt-dlp
```bash
# Via pip
pip install --upgrade yt-dlp

# Or in app
# Settings → Updates → Update yt-dlp Now
```

### Update App Code
```bash
git pull origin main
```

---

## Uninstallation

### Remove App
```bash
# Delete project folder
rm -rf TiktokDownloder-V1
```

### Remove Virtual Environment
```bash
# Already deleted with project folder
```

### Remove Python (Optional)
- Windows: Control Panel → Uninstall
- macOS: `brew uninstall python`
- Linux: `sudo apt remove python3`

---

## Development Setup

For developers who want to contribute:

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/TiktokDownloader-V1.git
cd TiktokDownloader-V1
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate   # Windows
```

### 3. Install Dev Dependencies
```bash
pip install -r requirements.txt
pip install pytest black pylint
```

### 4. Run Tests
```bash
pytest
```

### 5. Format Code
```bash
black src/
```

### 6. Run Linter
```bash
pylint src/
```

---

## System Requirements

### Minimum
- **OS:** Windows 10+, macOS 10.14+, Ubuntu 20.04+
- **Python:** 3.8+
- **RAM:** 2 GB
- **Storage:** 100 MB (app) + space for downloads
- **Internet:** Required for downloads

### Recommended
- **OS:** Windows 11, macOS 12+, Ubuntu 22.04+
- **Python:** 3.10+
- **RAM:** 4 GB
- **Storage:** 1 GB+ for downloads
- **Internet:** Broadband connection

---

## Getting Help

### Documentation
- [README.md](README.md) - Full documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [WHATS_NEW.md](WHATS_NEW.md) - New features
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference

### Support
- GitHub Issues: [Report bugs](https://github.com/yourusername/TiktokDownloader-V1/issues)
- Discussions: [Ask questions](https://github.com/yourusername/TiktokDownloader-V1/discussions)

---

## Success!

If everything works, you should see:
```
[TikTok Downloader Pro Window]
🎵 TikTok Downloader Pro
v1.0.0

Ready to download! ✅
```

**Enjoy your professional TikTok Downloader! 🎉**
