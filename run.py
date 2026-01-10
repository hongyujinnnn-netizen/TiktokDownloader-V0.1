"""
TikTok Downloader - Main Entry Point
Author: Your Name
Version: 1.0.0
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import main

if __name__ == "__main__":
    main()
