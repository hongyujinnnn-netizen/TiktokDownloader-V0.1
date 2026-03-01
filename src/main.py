"""
Main application entry point
"""

import sys
import tkinter as tk
from tkinter import messagebox
import os

# Import configuration
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import APP_NAME, COLORS, set_theme
from src.utils.translator import set_language

# Import GUI
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logger


def main():
    """Initialize and run the application"""
    try:
        # Setup logger
        logger = setup_logger()
        logger.info(f"Starting {APP_NAME}")
        
        # Initialize configuration
        config = ConfigManager()
        
        # Apply language and theme from settings
        language = config.get_setting("language", "en") or "en"
        set_language(language)

        theme = config.get_setting("theme", "light")
        set_theme(theme)
        logger.info(f"Applied {theme} theme | language={language}")
        
        # Create main window (prefer DnD-capable root when available)
        try:
            from tkinterdnd2 import TkinterDnD
            root = TkinterDnD.Tk()
            logger.info("Drag-and-drop support enabled")
        except Exception:
            root = tk.Tk()
            logger.info("Drag-and-drop support unavailable; running without DnD")
        app = MainWindow(root)
        
        # Run application
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application:\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
