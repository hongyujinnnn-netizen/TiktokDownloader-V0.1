"""
yt-dlp Updater
Auto-update yt-dlp to latest version
"""

import subprocess
import sys
import os


class YtdlpUpdater:
    """Handle yt-dlp updates"""
    
    @staticmethod
    def update():
        """
        Update yt-dlp to latest version
        
        Returns:
            dict: Update result
        """
        try:
            # Update using pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "yt-dlp updated successfully!"
                }
            else:
                return {
                    "success": False,
                    "message": f"Update failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Update error: {str(e)}"
            }
    
    @staticmethod
    def get_version():
        """
        Get current yt-dlp version
        
        Returns:
            str: Version string
        """
        try:
            import yt_dlp
            return yt_dlp.version.__version__
        except:
            return "Unknown"
    
    @staticmethod
    def check_for_updates():
        """
        Check if updates are available
        
        Returns:
            dict: Update availability status
        """
        try:
            # Check using pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated"],
                capture_output=True,
                text=True
            )
            
            if "yt-dlp" in result.stdout:
                return {
                    "available": True,
                    "message": "Update available for yt-dlp"
                }
            else:
                return {
                    "available": False,
                    "message": "yt-dlp is up to date"
                }
                
        except Exception as e:
            return {
                "available": False,
                "message": f"Check failed: {str(e)}"
            }
