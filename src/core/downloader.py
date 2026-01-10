"""
TikTok Video Downloader
Core functionality for downloading single videos
"""

import yt_dlp
import os
from pathlib import Path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import DOWNLOADS_DIR, YTDLP_OPTIONS
from utils.file_manager import FileManager
from utils.validators import is_valid_tiktok_url
from utils.config_manager import ConfigManager


class TikTokDownloader:
    """Handle TikTok video downloads"""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.config = ConfigManager()
    
    def download_video(self, url, output_path=None, convert_to_mp3=False, filename=None, source=None):
        """
        Download a single TikTok video
        
        Args:
            url: TikTok video URL
            output_path: Custom output directory
            convert_to_mp3: Convert video to MP3
            filename: Custom filename
            source: Source of download (e.g., 'profile' for profile downloads)
        
        Returns:
            dict: Download result with success status and path
        """
        try:
            # Validate URL
            if not is_valid_tiktok_url(url):
                return {
                    "success": False,
                    "error": "Invalid TikTok URL"
                }
            
            # Prepare output path
            if not output_path:
                output_path = self.config.get_setting("download_path")
            
            output_path = Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = YTDLP_OPTIONS.copy()
            
            if convert_to_mp3:
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                ydl_opts['outtmpl'] = str(output_path / '%(title)s.%(ext)s')
            else:
                quality = self.config.get_setting("video_quality", "best")
                if quality == "best":
                    ydl_opts['format'] = 'best'
                elif quality == "high":
                    ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best'
                elif quality == "medium":
                    ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
                else:
                    ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best'
                
                if filename:
                    ydl_opts['outtmpl'] = str(output_path / f"{filename}.%(ext)s")
                else:
                    ydl_opts['outtmpl'] = str(output_path / '%(title)s.%(ext)s')
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get downloaded file path
                if convert_to_mp3:
                    downloaded_file = output_path / f"{info['title']}.mp3"
                else:
                    ext = info.get('ext', 'mp4')
                    if filename:
                        downloaded_file = output_path / f"{filename}.{ext}"
                    else:
                        downloaded_file = output_path / f"{info['title']}.{ext}"
                
                # Save to history
                if self.config.get_setting("save_history"):
                    history_entry = {
                        "title": info.get('title', 'Unknown'),
                        "url": url,
                        "type": "MP3" if convert_to_mp3 else "Video",
                        "path": str(downloaded_file)
                    }
                    if source:
                        history_entry["source"] = source
                    self.config.add_to_history(history_entry)
                
                return {
                    "success": True,
                    "path": str(downloaded_file),
                    "title": info.get('title', 'Unknown')
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_video_info(self, url):
        """
        Get video information without downloading
        
        Args:
            url: TikTok video URL
        
        Returns:
            dict: Video information
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    "success": True,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', 'Unknown'),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
