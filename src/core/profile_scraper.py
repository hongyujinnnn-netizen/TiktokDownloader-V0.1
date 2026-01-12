"""
Profile Scraper
Download multiple videos from TikTok profiles
"""

import yt_dlp
import os
from pathlib import Path
import sys
import re
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import DOWNLOADS_DIR
from core.downloader import TikTokDownloader
from utils.validators import is_valid_tiktok_url
from utils.config_manager import ConfigManager
from utils.file_manager import FileManager


class ProfileScraper:
    """Handle bulk downloads from TikTok profiles"""
    
    def __init__(self):
        self.downloader = TikTokDownloader()
        self.config = ConfigManager()
        self.file_manager = FileManager()
    
    def get_profile_video_count(self, profile_url):
        """
        Get total number of videos in a profile
        
        Args:
            profile_url: TikTok profile URL
        
        Returns:
            int: Number of videos
        """
        try:
            ydl_opts: dict[str, Any] = {
                'quiet': True,
                'extract_flat': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                
                if 'entries' in info:
                    return len(list(info['entries']))
                
                return 0
                
        except Exception as e:
            raise Exception(f"Failed to fetch profile info: {str(e)}")
    
    def extract_username(self, profile_url):
        """
        Extract username from profile URL
        
        Args:
            profile_url: TikTok profile URL
        
        Returns:
            str: Username
        """
        # Extract username from URL
        match = re.search(r'@([a-zA-Z0-9._]+)', profile_url)
        if match:
            return match.group(1)
        return "tiktok_profile"
    
    def download_from_profile(self, profile_url, limit=0, create_folder=True,
                             convert_to_mp3=False, skip_existing=True,
                             progress_callback=None, pause_check=None, stop_check=None):
        """
        Download videos from a TikTok profile
        
        Args:
            profile_url: TikTok profile URL
            limit: Number of videos to download (0 = all)
            create_folder: Create separate folder for profile
            convert_to_mp3: Convert videos to MP3
            skip_existing: Skip already downloaded files
            progress_callback: Function to call with progress updates
            pause_check: Function that returns True if should pause
            stop_check: Function that returns True if should stop
        
        Returns:
            dict: Download results
        """
        try:
            # Extract username for folder name
            username = self.extract_username(profile_url)
            
            # Prepare output path
            download_path = self.config.get_setting("download_path") or DOWNLOADS_DIR
            output_path = Path(download_path)
            
            if create_folder:
                output_path = output_path / f"@{username}"
                output_path.mkdir(parents=True, exist_ok=True)
            
            # Get video list
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'skip_download': True,
            }
            
            video_urls = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                
                if 'entries' in info:
                    entries = list(info['entries'])
                    
                    # Apply limit
                    if limit > 0:
                        entries = entries[:limit]
                    
                    for entry in entries:
                        if entry and 'url' in entry:
                            video_urls.append(entry['url'])
                        elif entry and 'id' in entry:
                            # Construct URL from ID
                            video_urls.append(f"https://www.tiktok.com/@{username}/video/{entry['id']}")
            
            # Download videos
            downloaded = 0
            failed = 0
            skipped = 0
            
            for idx, video_url in enumerate(video_urls, 1):
                # Check if should stop
                if stop_check and stop_check():
                    break
                
                # Handle pause
                if pause_check:
                    while pause_check() and not (stop_check and stop_check()):
                        import time
                        time.sleep(0.1)
                
                try:
                    # Get video title for progress
                    video_title = f"Video {idx}"
                    
                    if progress_callback:
                        progress_callback(idx, len(video_urls), video_title)
                    
                    result = self.downloader.download_video(
                        url=video_url,
                        output_path=str(output_path),
                        convert_to_mp3=convert_to_mp3,
                        source="profile"
                    )
                    
                    if result["success"]:
                        downloaded += 1
                    else:
                        failed += 1
                
                except Exception as e:
                    failed += 1
            
            return {
                "success": True,
                "downloaded": downloaded,
                "failed": failed,
                "skipped": skipped,
                "total": len(video_urls),
                "output_path": str(output_path)
            }
            
        except Exception as e:
            raise Exception(f"Profile download failed: {str(e)}")
    
    def get_profile_info(self, profile_url):
        """
        Get profile information
        
        Args:
            profile_url: TikTok profile URL
        
        Returns:
            dict: Profile information
        """
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(profile_url, download=False)
                
                return {
                    "success": True,
                    "username": self.extract_username(profile_url),
                    "title": info.get('title', 'Unknown'),
                    "video_count": len(list(info.get('entries', []))),
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
