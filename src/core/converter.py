"""
Audio Converter
Convert videos to MP3
"""

import os
from pathlib import Path
from pydub import AudioSegment
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class AudioConverter:
    """Handle audio conversion"""
    
    @staticmethod
    def video_to_mp3(video_path, output_path=None, bitrate="192k"):
        """
        Convert video to MP3
        
        Args:
            video_path: Path to video file
            output_path: Output MP3 path (optional)
            bitrate: Audio bitrate
        
        Returns:
            dict: Conversion result
        """
        try:
            video_path = Path(video_path)
            
            if not video_path.exists():
                return {
                    "success": False,
                    "error": "Video file not found"
                }
            
            # Prepare output path
            if not output_path:
                output_path = video_path.with_suffix('.mp3')
            else:
                output_path = Path(output_path)
            
            # Convert using pydub
            audio = AudioSegment.from_file(str(video_path))
            audio.export(
                str(output_path),
                format="mp3",
                bitrate=bitrate
            )
            
            return {
                "success": True,
                "path": str(output_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def batch_convert(video_paths, output_dir=None, bitrate="192k"):
        """
        Convert multiple videos to MP3
        
        Args:
            video_paths: List of video file paths
            output_dir: Output directory
            bitrate: Audio bitrate
        
        Returns:
            dict: Batch conversion results
        """
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for video_path in video_paths:
            if output_dir:
                output_path = Path(output_dir) / (Path(video_path).stem + '.mp3')
            else:
                output_path = None
            
            result = AudioConverter.video_to_mp3(video_path, output_path, bitrate)
            
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "file": video_path,
                    "error": result["error"]
                })
        
        return results
