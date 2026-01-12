"""
TikTok Video Downloader
Core functionality for downloading single videos
"""

import yt_dlp
import os
import shutil
from pathlib import Path
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import YTDLP_OPTIONS
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
            explicit_output_path = bool(output_path)
            base_output_path = Path(output_path) if output_path else Path(self.config.get_setting("download_path") or "downloads")
            base_output_path.mkdir(parents=True, exist_ok=True)

            create_folder = self.config.get_setting("create_profile_folders", True)
            profile_user = self._extract_profile_user(url) if create_folder else None

            if create_folder and not profile_user:
                profile_user = self._extract_profile_from_path(base_output_path)

            output_path = self._resolve_output_path(base_output_path, profile_user, explicit_output_path, create_folder)
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                info = ydl.extract_info(url, download=True)
                downloaded_file = Path(ydl.prepare_filename(info))

                if convert_to_mp3:
                    downloaded_file = downloaded_file.with_suffix('.mp3')

                if create_folder and not profile_user:
                    resolved_user = (
                        self._extract_profile_from_info(info)
                        or self._extract_profile_user(url)
                        or self._extract_profile_from_path(base_output_path)
                    )
                    if resolved_user:
                        profile_user = resolved_user
                        target_dir = self._resolve_output_path(
                            base_output_path,
                            profile_user,
                            explicit_output_path,
                            create_folder,
                        )
                        target_dir.mkdir(parents=True, exist_ok=True)
                    else:
                        target_dir = output_path
                else:
                    target_dir = output_path

                if target_dir != downloaded_file.parent:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    unique_name = self.file_manager.get_unique_filename(target_dir, downloaded_file.name)
                    final_path = target_dir / unique_name
                    try:
                        downloaded_file.rename(final_path)
                        downloaded_file = final_path
                    except OSError:
                        # Fallback to copy if rename fails across devices
                        shutil.copy2(downloaded_file, final_path)
                        downloaded_file.unlink(missing_ok=True)
                        downloaded_file = final_path
                
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
                    if profile_user:
                        history_entry["profile_user"] = f"@{profile_user}"
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

    def _extract_profile_user(self, url: str | None) -> str | None:
        if not url:
            return None
        match = re.search(r"@([a-zA-Z0-9._-]+)", url)
        if match:
            return match.group(1)
        return None

    def _extract_profile_from_path(self, path: Path) -> str | None:
        for part in reversed(path.parts):
            if part.startswith("@") and len(part) > 1:
                return part[1:]
        return None

    def _extract_profile_from_info(self, info) -> str | None:
        if not info:
            return None
        for key in ("uploader_id", "uploader", "channel", "creator"):
            value = info.get(key)
            if value:
                sanitized = re.sub(r"[^A-Za-z0-9._-]", "", str(value))
                if sanitized:
                    return sanitized
        return None

    def _resolve_output_path(
        self,
        base_output_path: Path,
        profile_user: str | None,
        explicit_output_path: bool,
        create_folder: bool,
    ) -> Path:
        if not create_folder or not profile_user:
            return base_output_path

        base_profile = self._extract_profile_from_path(base_output_path)
        if base_profile and base_profile.lower() == profile_user.lower():
            return base_output_path

        if explicit_output_path and base_profile:
            return base_output_path

        return base_output_path / f"@{profile_user}"
    
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
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
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
