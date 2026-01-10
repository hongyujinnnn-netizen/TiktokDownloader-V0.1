"""
File Manager
Handle file operations and management
"""

import os
import shutil
from pathlib import Path
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import DOWNLOADS_DIR


class FileManager:
    """Manage files and directories"""
    
    @staticmethod
    def create_directory(path):
        """
        Create directory if it doesn't exist
        
        Args:
            path: Directory path
        
        Returns:
            Path: Created directory path
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename for safe storage
        
        Args:
            filename: Original filename
        
        Returns:
            str: Sanitized filename
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim and limit length
        filename = filename.strip()[:200]
        
        return filename
    
    @staticmethod
    def get_unique_filename(directory, filename):
        """
        Get unique filename by adding number suffix if file exists
        
        Args:
            directory: Target directory
            filename: Desired filename
        
        Returns:
            str: Unique filename
        """
        directory = Path(directory)
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        
        counter = 1
        unique_filename = filename
        
        while (directory / unique_filename).exists():
            unique_filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return unique_filename
    
    @staticmethod
    def get_file_size(file_path):
        """
        Get file size in human-readable format
        
        Args:
            file_path: Path to file
        
        Returns:
            str: File size
        """
        try:
            size = os.path.getsize(file_path)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            
            return f"{size:.2f} TB"
            
        except:
            return "Unknown"
    
    @staticmethod
    def move_file(source, destination):
        """
        Move file from source to destination
        
        Args:
            source: Source file path
            destination: Destination path
        
        Returns:
            bool: Success status
        """
        try:
            shutil.move(str(source), str(destination))
            return True
        except:
            return False
    
    @staticmethod
    def delete_file(file_path):
        """
        Delete a file
        
        Args:
            file_path: Path to file
        
        Returns:
            bool: Success status
        """
        try:
            os.remove(file_path)
            return True
        except:
            return False
    
    @staticmethod
    def list_files(directory, extension=None):
        """
        List files in directory
        
        Args:
            directory: Directory path
            extension: Filter by extension (e.g., '.mp4')
        
        Returns:
            list: List of file paths
        """
        directory = Path(directory)
        
        if not directory.exists():
            return []
        
        if extension:
            files = list(directory.glob(f"*{extension}"))
        else:
            files = [f for f in directory.iterdir() if f.is_file()]
        
        return [str(f) for f in files]
    
    @staticmethod
    def ensure_downloads_folder():
        """Ensure downloads folder exists"""
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        return DOWNLOADS_DIR
