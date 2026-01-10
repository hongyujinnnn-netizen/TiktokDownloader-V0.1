# Quick Start Guide

## Installation

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (Required for MP3 conversion)
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add to system PATH

## Running the App

```bash
python run.py
```

## Basic Usage

### Download Single Video
1. Copy a TikTok video URL
2. Paste it in the input field
3. Click "Download Video"

### Download from Profile
1. Click "Open Profile Downloader"
2. Paste profile URL (e.g., https://www.tiktok.com/@username)
3. Click "Check Profile"
4. Set number of videos to download
5. Click "Start Bulk Download"

## Tips

- Use "Check Profile" before bulk downloading to see total videos
- Set download limit to 0 to download ALL videos from a profile
- Enable "Skip already downloaded videos" to resume interrupted downloads
- Check "Create separate folder" to organize downloads by profile
- Use MP3 conversion for music/audio content

## Keyboard Shortcuts

- `Ctrl+V` - Paste URL
- `Enter` - Start download (when URL field is focused)
- `Escape` - Close popup windows

## Common Issues

**Downloads are slow?**
- Check your internet connection
- TikTok may throttle download speeds

**"Invalid URL" error?**
- Make sure you copied the complete URL
- Try opening the video in a browser first

**MP3 conversion fails?**
- Install FFmpeg
- Restart the application after installing FFmpeg

## Support

For help, visit: https://github.com/yourusername/TiktokDownloader-V1/issues
