"""
Progress Dialog with Real Progress Bar
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import COLORS, FONTS


class ProgressDialog:
    """Enhanced progress dialog with real progress tracking"""
    
    def __init__(self, parent, title="Please Wait", mode="indeterminate"):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.configure(bg=COLORS["card"])
        self.window.resizable(False, False)
        
        # Center on parent
        self.window.transient(parent)
        self.window.grab_set()
        
        # Status label
        self.status_label = tk.Label(
            self.window,
            text="Processing...",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text"]
        )
        self.status_label.pack(pady=(20, 10))
        
        # Progress bar
        style = ttk.Style()
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=COLORS["accent"],
            troughcolor=COLORS["background"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"]
        )
        
        self.progress_bar = ttk.Progressbar(
            self.window,
            style="Custom.Horizontal.TProgressbar",
            length=350,
            mode=mode
        )
        self.progress_bar.pack(pady=10)
        
        # Details label
        self.details_label = tk.Label(
            self.window,
            text="",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"]
        )
        self.details_label.pack(pady=(5, 20))
        
        # Start animation for indeterminate mode
        if mode == "indeterminate":
            self.progress_bar.start(10)
        
        self.window.update()
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.window.update()
    
    def update_details(self, details):
        """Update details text"""
        self.details_label.config(text=details)
        self.window.update()
    
    def update_progress(self, current, total):
        """Update progress bar (switches to determinate mode)"""
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", maximum=total, value=current)
        
        # Update details with percentage
        percentage = int((current / total) * 100) if total > 0 else 0
        self.details_label.config(text=f"{current} / {total} ({percentage}%)")
        
        self.window.update()
    
    def close(self):
        """Close the dialog"""
        try:
            self.window.destroy()
        except:
            pass


class InlineStatus:
    """Inline status label for feedback without popups"""
    
    def __init__(self, parent):
        self.label = tk.Label(
            parent,
            text="",
            font=FONTS["body"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            height=2
        )
    
    def pack(self, **kwargs):
        self.label.pack(**kwargs)
    
    def show_success(self, message):
        """Show success message"""
        self.label.config(text=f"✅ {message}", fg=COLORS["success"])
        self.label.after(5000, self.clear)  # Auto-clear after 5s
    
    def show_error(self, message):
        """Show error message"""
        self.label.config(text=f"❌ {message}", fg=COLORS["danger"])
    
    def show_info(self, message):
        """Show info message"""
        self.label.config(text=f"ℹ️ {message}", fg=COLORS["accent"])
    
    def show_warning(self, message):
        """Show warning message"""
        self.label.config(text=f"⚠️ {message}", fg=COLORS["warning"])
    
    def clear(self):
        """Clear status"""
        self.label.config(text="")
