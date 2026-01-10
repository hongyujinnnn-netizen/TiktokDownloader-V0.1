"""
Styling utilities for the application
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import COLORS, FONTS


def apply_styles(root):
    """Apply global styles to the application"""
    style = ttk.Style(root)
    style.theme_use('clam')
    
    # Configure ttk widgets
    style.configure(
        "TButton",
        background=COLORS["button"],
        foreground=COLORS["text"],
        borderwidth=0,
        focuscolor='none',
        padding=10,
        font=FONTS["button"]
    )
    
    style.map(
        "TButton",
        background=[('active', COLORS["button_hover"])]
    )
    
    style.configure(
        "TEntry",
        fieldbackground=COLORS["background"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"]
    )
    
    style.configure(
        "TFrame",
        background=COLORS["card"]
    )


def create_styled_button(parent, text, command, bg=None, hover_bg=None, font=None, **kwargs):
    """Create a styled button with hover effect"""
    bg_color = bg or COLORS["button"]
    hover_color = hover_bg or COLORS["button_hover"]
    button_font = font or FONTS["button"]
    
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=button_font,
        bg=bg_color,
        fg=COLORS["text"],
        activebackground=hover_color,
        activeforeground=COLORS["text"],
        relief="flat",
        cursor="hand2",
        borderwidth=0,
        **kwargs
    )
    
    # Hover effect
    def on_enter(e):
        button.config(bg=hover_color)
    
    def on_leave(e):
        button.config(bg=bg_color)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    
    return button


def create_styled_entry(parent, width=40, **kwargs):
    """Create a styled entry widget"""
    entry = tk.Entry(
        parent,
        font=FONTS["body"],
        bg=COLORS["background"],
        fg=COLORS["text"],
        insertbackground=COLORS["accent"],
        relief="flat",
        borderwidth=2,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["accent"],
        width=width,
        **kwargs
    )
    return entry


def create_styled_frame(parent, bg_color=None, **kwargs):
    """Create a styled frame"""
    frame = tk.Frame(
        parent,
        bg=bg_color or COLORS["card"],
        **kwargs
    )
    return frame


def create_styled_label(parent, text, font_type="body", **kwargs):
    """Create a styled label"""
    label = tk.Label(
        parent,
        text=text,
        font=FONTS.get(font_type, FONTS["body"]),
        bg=COLORS["card"],
        fg=COLORS["text"],
        **kwargs
    )
    return label


def create_progress_bar(parent, **kwargs):
    """Create a styled progress bar"""
    progress = ttk.Progressbar(
        parent,
        style="TProgressbar",
        mode='indeterminate',
        **kwargs
    )
    return progress
