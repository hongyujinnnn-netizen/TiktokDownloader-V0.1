"""
Settings Window
"""

import copy
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from config import (
    APP_NAME,
    APP_VERSION,
    COLORS,
    DEFAULT_SETTINGS,
    FONTS,
    LANGUAGES,
    set_theme,
)
from gui.styles import create_styled_button, create_styled_entry, create_styled_frame
from gui.progress_dialog import InlineStatus
from utils.config_manager import ConfigManager
from core.updater import YtdlpUpdater


class Tooltip:
    """Lightweight tooltip for Tk widgets."""

    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._tip = None

        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<ButtonPress>", self.hide)

    def _schedule(self, _event=None):
        self._unschedule()
        self._after_id = self.widget.after(self.delay, self.show)

    def _unschedule(self):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def show(self):
        if self._tip or not self.text:
            return

        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self._tip = tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")

        frame = tk.Frame(
            tip,
            bg=COLORS["card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
        )
        frame.pack()

        label = tk.Label(
            frame,
            text=self.text,
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            justify="left",
            wraplength=240,
            padx=10,
            pady=6,
        )
        label.pack()

    def hide(self, _event=None):
        self._unschedule()
        if self._tip:
            self._tip.destroy()
            self._tip = None


class ToggleSwitch(tk.Frame):
    """Toggle switch styled like a modern settings control."""

    def __init__(self, parent, text="", variable=None, command=None):
        super().__init__(parent, bg=parent.cget("bg"))
        self.variable = variable or tk.BooleanVar(value=False)
        self.command = command

        self.track = tk.Frame(
            self,
            width=40,
            height=20,
            bg=COLORS["border"],
            highlightthickness=0,
            bd=0,
        )
        self.track.pack(side="left", pady=2)
        self.track.pack_propagate(False)

        self.knob = tk.Frame(
            self.track,
            width=18,
            height=18,
            bg=COLORS["background"],
            highlightthickness=0,
            bd=0,
        )
        self.knob.place(x=1, y=1)

        self.label = tk.Label(
            self,
            text=text,
            font=FONTS["body"],
            bg=self.cget("bg"),
            fg=COLORS["text"],
            padx=8,
            justify="left",
        )
        self.label.pack(side="left", fill="x")

        for widget in (self, self.track, self.knob, self.label):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", self._toggle)

        self.variable.trace_add("write", lambda *_: self.refresh_theme())
        self.refresh_theme()

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def refresh_theme(self):
        background = self.master.cget("bg")
        self.configure(bg=background)
        self.label.configure(bg=background, fg=COLORS["text"])

        active = bool(self.variable.get())
        track_color = COLORS["accent"] if active else COLORS["border"]
        self.track.configure(bg=track_color)

        knob_x = 20 if active else 1
        self.knob.configure(bg=COLORS["background"])
        self.knob.place_configure(x=knob_x)

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(bool(value))
        self.refresh_theme()


class RadioCardGroup(tk.Frame):
    """Group of selectable cards that behave like radio buttons."""

    def __init__(self, parent, options, variable=None, command=None):
        super().__init__(parent, bg=parent.cget("bg"))
        self.variable = variable or tk.StringVar()
        self.command = command
        self.cards = {}

        for idx, option in enumerate(options):
            card = tk.Frame(
                self,
                bg=COLORS["background"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                bd=0,
                padx=12,
                pady=8,
            )
            card.grid(row=0, column=idx, padx=(0 if idx == 0 else 8), sticky="nsew")
            self.columnconfigure(idx, weight=1)

            title_text = f"{option.get('icon', '')} {option['label']}".strip()
            title_label = tk.Label(
                card,
                text=title_text,
                font=FONTS["body"],
                bg=card.cget("bg"),
                fg=COLORS["text"],
            )
            title_label.pack(anchor="w")
            title_label._is_primary = True

            description = option.get("description")
            if description:
                desc_label = tk.Label(
                    card,
                    text=description,
                    font=FONTS["small"],
                    bg=card.cget("bg"),
                    fg=COLORS["text_secondary"],
                    wraplength=180,
                    justify="left",
                )
                desc_label.pack(anchor="w", pady=(4, 0))
                desc_label._is_primary = False
            else:
                desc_label = None

            for widget in (card, title_label, desc_label):
                if widget is None:
                    continue
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", lambda _e, value=option["value"]: self.select(value))

            self.cards[option["value"]] = card

        self.variable.trace_add("write", lambda *_: self.refresh_theme())
        self.refresh_theme()

    def select(self, value):
        if self.variable.get() == value:
            if self.command:
                self.command(value)
            return
        self.variable.set(value)
        if self.command:
            self.command(value)
        self.refresh_theme()

    def refresh_theme(self):
        background = self.master.cget("bg")
        self.configure(bg=background)

        current = self.variable.get()
        for value, card in self.cards.items():
            selected = value == current
            card_bg = COLORS["accent"] if selected else COLORS["background"]
            border_color = COLORS["accent"] if selected else COLORS["border"]
            card.configure(bg=card_bg, highlightbackground=border_color)
            for child in card.winfo_children():
                child.configure(bg=card_bg)
                if getattr(child, "_is_primary", False):
                    child.configure(fg=COLORS["background"] if selected else COLORS["text"])
                else:
                    child.configure(fg=COLORS["background"] if selected else COLORS["text_secondary"])


class SettingsWindow:
    """Window for application settings."""

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("900x600")
        self.window.configure(bg=COLORS["background"])
        self.window.minsize(820, 560)

        self.window.transient(parent)
        self.window.grab_set()

        self.config = ConfigManager()
        self.updater = YtdlpUpdater()
        self.original_settings = copy.deepcopy(self.config.settings)
        self.original_theme = self.original_settings.get("theme", "light")
        self.preview_theme = self.original_theme
        self.dirty = False
        self.suppress_change = False
        self.themable = []
        self.theme_preview_widgets = []
        self.toggle_switches = []
        self.radio_groups = []
        self.update_thread = None
        self._mousewheel_bound = False

        self.create_widgets()
        self.load_settings()
        self.center_window()

        self.window.protocol("WM_DELETE_WINDOW", self.cancel_changes)
        self.window.bind("<Escape>", lambda _e: self.cancel_changes())
        self.window.bind("<Control-s>", lambda _e: self.save_settings())
        self.window.bind("<Destroy>", self._on_window_destroy)

        self.window.update_idletasks()

    def center_window(self):
        """Center window on screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def register_themable(self, widget, **mapping):
        """Register widget attributes for later theme refresh."""
        self.themable.append((widget, mapping))

    def refresh_theme_palette(self):
        """Apply current palette to registered widgets."""
        for widget, mapping in self.themable:
            config = {}
            for attr, color_key in mapping.items():
                config[attr] = COLORS.get(color_key, COLORS["background"])
            try:
                widget.configure(**config)
            except tk.TclError:
                continue

        for toggle in self.toggle_switches:
            toggle.refresh_theme()
        for group in self.radio_groups:
            group.refresh_theme()
        for updater in self.theme_preview_widgets:
            updater()

        if hasattr(self, "ttk_style"):
            self.ttk_style.configure("Custom.TNotebook", background=COLORS["card"])
            self.ttk_style.configure("Custom.TNotebook.Tab", background=COLORS["background"], foreground=COLORS["text"])
            self.ttk_style.map(
                "Custom.TNotebook.Tab",
                background=[("selected", COLORS["accent"])],
                foreground=[("selected", COLORS["background"])],
            )
            self.ttk_style.configure("Settings.TSeparator", background=COLORS["border"])

        if hasattr(self, "settings_status"):
            self.settings_status.label.config(bg=COLORS["card"], fg=COLORS["text_secondary"])

    def mark_dirty(self, _event=None):
        if self.suppress_change:
            return
        if not self.dirty:
            self.dirty = True
            self.update_save_state()

    def update_save_state(self):
        if hasattr(self, "save_button"):
            state = "normal" if self.dirty else "disabled"
            self.save_button.config(state=state)
        if hasattr(self, "reset_button"):
            self.reset_button.config(state="normal")

    def create_widgets(self):
        """Create UI widgets."""
        self.register_themable(self.window, bg="background")

        self.main_container = tk.Frame(self.window, bg=COLORS["background"])
        self.register_themable(self.main_container, bg="background")
        self.main_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_container, bg=COLORS["background"], highlightthickness=0)
        self.register_themable(self.canvas, bg="background")
        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["background"])
        self.register_themable(self.scrollable_frame, bg="background")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._mousewheel_bound = True

        header = tk.Frame(self.scrollable_frame, bg=COLORS["background"])
        self.register_themable(header, bg="background")
        header.pack(pady=(16, 8), padx=24, fill="x")

        title = tk.Label(
            header,
            text="⚙ Settings",
            font=FONTS["title"],
            bg=COLORS["background"],
            fg=COLORS["text"],
        )
        self.register_themable(title, bg="background", fg="text")
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Adjust the experience with instant theme previews and smarter controls.",
            font=FONTS["body"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"],
            wraplength=580,
            justify="left",
        )
        self.register_themable(subtitle, bg="background", fg="text_secondary")
        subtitle.pack(anchor="w", pady=(6, 0))

        separator = ttk.Separator(self.scrollable_frame, orient="horizontal", style="Settings.TSeparator")
        separator.pack(fill="x", padx=24, pady=(0, 12))

        self.card = create_styled_frame(self.scrollable_frame, COLORS["card"])
        self.register_themable(self.card, bg="card", highlightbackground="border")
        self.card.configure(highlightbackground=COLORS["border"], highlightthickness=1, bd=0)
        self.card.pack(pady=(0, 16), padx=24, fill="both", expand=True)
        self.card.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "Custom.TNotebook",
            background=COLORS["card"],
            borderwidth=0,
            padding=(0, 4, 0, 0),
        )
        style.configure(
            "Custom.TNotebook.Tab",
            background=COLORS["background"],
            foreground=COLORS["text"],
            padding=[16, 9],
            font=FONTS["body"],
        )
        style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["background"])],
            padding=[("selected", [16, 9])],
        )
        style.configure("Settings.TSeparator", background=COLORS["border"])
        self.ttk_style = style

        self.notebook = ttk.Notebook(self.card, style="Custom.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 10))
        self.card.rowconfigure(0, weight=1)

        self.create_general_tab()
        self.create_download_tab()
        self.create_advanced_tab()
        self.create_updates_tab()

        self.notebook.update_idletasks()

        self.settings_status = InlineStatus(self.card)
        self.settings_status.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 6))

        button_frame = tk.Frame(self.card, bg=COLORS["card"])
        self.register_themable(button_frame, bg="card")
        button_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(2, weight=1)

        self.save_button = create_styled_button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            bg=COLORS["accent"],
            hover_bg="#0D94D8",
        )
        self.save_button.grid(row=0, column=0, sticky="w", padx=(0, 8), ipadx=18, ipady=7)
        self.register_themable(self.save_button, bg="accent", fg="text", activebackground="accent", activeforeground="text")

        self.reset_button = tk.Button(
            button_frame,
            text="↩ Reset to Defaults",
            command=self.reset_to_defaults,
            font=FONTS["button"],
            bg=COLORS["card"],
            fg=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            cursor="hand2",
            bd=0,
            padx=18,
            pady=6,
            activebackground=COLORS["background"],
            activeforeground=COLORS["text"],
        )
        self.register_themable(self.reset_button, bg="card", fg="text", highlightbackground="border")
        self.reset_button.grid(row=0, column=1, padx=8)

        cancel_button = tk.Button(
            button_frame,
            text="✖ Cancel",
            command=self.cancel_changes,
            font=FONTS["button"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            cursor="hand2",
            bd=0,
            padx=18,
            pady=6,
            activebackground=COLORS["background"],
            activeforeground=COLORS["text"],
        )
        self.register_themable(cancel_button, bg="card", fg="text_secondary", highlightbackground="border")
        cancel_button.grid(row=0, column=2, sticky="e")

        self.update_save_state()

    def _on_mousewheel(self, event):
        if not getattr(self, "canvas", None):
            return
        if not self.canvas.winfo_exists():
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _unbind_mousewheel(self):
        if not getattr(self, "canvas", None):
            return
        if not self._mousewheel_bound:
            return
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        finally:
            self._mousewheel_bound = False

    def _on_window_destroy(self, event):
        if event.widget is self.window:
            self._unbind_mousewheel()

    def handle_path_change(self, _event=None):
        self.clear_path_error()
        self.mark_dirty()

    def clear_path_error(self):
        self.path_entry.configure(highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"])
        self.path_error.config(text="")

    def handle_profile_limit_change(self, _event=None):
        self.clear_profile_limit_error()
        self.mark_dirty()

    def clear_profile_limit_error(self):
        self.profile_limit_entry.configure(highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"])
        self.profile_limit_error.config(text="")

    def apply_theme_preview(self, theme_name):
        if theme_name == self.preview_theme and not self.suppress_change:
            return
        set_theme(theme_name)
        self.preview_theme = theme_name
        self.refresh_theme_palette()

    def on_theme_change(self, value):
        self.apply_theme_preview(value)
        self.mark_dirty()

    def on_language_change(self, _event=None):
        display = self.language_var.get() or ""
        self.app_info_label.config(text=f"{APP_NAME} v{APP_VERSION}\nLanguage: {display}")
        self.mark_dirty()

    def validate_settings(self):
        valid = True
        profile_limit_value = 0

        path = self.path_entry.get().strip()
        if not path:
            self.path_entry.configure(highlightbackground=COLORS["danger"], highlightcolor=COLORS["danger"])
            self.path_error.config(text="Download path is required.")
            valid = False
        else:
            self.clear_path_error()

        try:
            profile_limit_value = int(self.profile_limit_entry.get().strip() or 0)
            if profile_limit_value < 0:
                raise ValueError
            self.clear_profile_limit_error()
        except ValueError:
            self.profile_limit_entry.configure(highlightbackground=COLORS["danger"], highlightcolor=COLORS["danger"])
            self.profile_limit_error.config(text="Enter a whole number of videos (0 downloads all).")
            valid = False

        return valid, max(profile_limit_value, 0)

    def create_general_tab(self):
        """Create General settings tab."""
        general_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.register_themable(general_frame, bg="card")
        self.notebook.add(general_frame, text="⚙ General")
        general_frame.grid_columnconfigure(0, weight=1)

        info_section = self.create_setting_section(
            general_frame,
            title="Application Overview",
            icon="⚙",
            description="Review version details and language at a glance.",
        )

        self.app_info_label = tk.Label(
            info_section,
            text="",
            font=FONTS["body"],
            bg=info_section.cget("bg"),
            fg=COLORS["text_secondary"],
            justify="left",
        )
        self.register_themable(self.app_info_label, bg="background", fg="text_secondary")
        self.app_info_label.pack(anchor="w", pady=(0, 5))

        language_section = self.create_setting_section(
            general_frame,
            title="Language",
            icon="🗣",
            description="Choose the interface language.",
        )

        self.language_var = tk.StringVar()
        languages_sorted = sorted(LANGUAGES.items(), key=lambda item: item[1])
        self.language_options = {name: code for code, name in languages_sorted}
        self.language_menu = ttk.Combobox(
            language_section,
            textvariable=self.language_var,
            values=list(self.language_options.keys()),
            state="readonly",
            font=FONTS["body"],
            height=10,
        )
        self.language_menu.pack(fill="x", pady=4)
        self.language_menu.bind("<<ComboboxSelected>>", self.on_language_change)
        self.create_hint_label(language_section, "Restart the app to apply language changes.")

        theme_section = self.create_setting_section(
            general_frame,
            title="Appearance",
            icon="🎨",
            description="Preview light or dark mode instantly before committing.",
        )

        self.theme_var = tk.StringVar(value=self.original_theme)
        theme_cards = RadioCardGroup(
            theme_section,
            options=[
                {"value": "light", "label": "Light", "icon": "🌞", "description": "Balanced contrast for bright rooms."},
                {"value": "dark", "label": "Dark", "icon": "🌙", "description": "Dim palette for low-light sessions."},
            ],
            variable=self.theme_var,
            command=self.on_theme_change,
        )
        theme_cards.pack(fill="x", pady=(0, 8))
        self.radio_groups.append(theme_cards)

        preview_frame = self.create_theme_preview(theme_section)
        preview_frame.pack(fill="x")

    def create_theme_preview(self, parent):
        preview = tk.Frame(
            parent,
            bg=COLORS["background"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
            padx=12,
            pady=10,
        )
        self.register_themable(preview, bg="background", highlightbackground="border")

        title = tk.Label(
            preview,
            text="Theme preview",
            font=FONTS["subheading"],
            bg=COLORS["background"],
            fg=COLORS["text"],
        )
        self.register_themable(title, bg="background", fg="text")
        title.pack(anchor="w")

        subtitle = tk.Label(
            preview,
            text="Buttons, cards, and text adapt instantly to your selection.",
            font=FONTS["small"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"],
            wraplength=400,
            justify="left",
        )
        self.register_themable(subtitle, bg="background", fg="text_secondary")
        subtitle.pack(anchor="w", pady=(3, 10))

        primary = tk.Label(
            preview,
            text="Primary action",
            font=FONTS["button"],
            bg=COLORS["accent"],
            fg=COLORS["background"],
            padx=14,
            pady=6,
        )
        primary.pack(anchor="w")

        chip = tk.Label(
            preview,
            text="Secondary",
            font=FONTS["small"],
            bg=COLORS["card"],
            fg=COLORS["text_secondary"],
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            padx=8,
            pady=3,
        )
        chip.pack(anchor="w", pady=(12, 0))

        def update_preview():
            primary.config(bg=COLORS["accent"], fg=COLORS["background"])
            chip.config(bg=COLORS["card"], fg=COLORS["text_secondary"], highlightbackground=COLORS["border"])

        self.theme_preview_widgets.append(update_preview)
        return preview

    def create_download_tab(self):
        """Create Download settings tab."""
        download_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.register_themable(download_frame, bg="card")
        self.notebook.add(download_frame, text="📥 Download")
        download_frame.grid_columnconfigure(0, weight=1)

        path_section = self.create_setting_section(
            download_frame,
            title="Download Location",
            icon="📂",
            description="Decide where finished downloads are stored on your device.",
        )

        path_input_frame = tk.Frame(path_section, bg=path_section.cget("bg"))
        self.register_themable(path_input_frame, bg="background")
        path_input_frame.pack(fill="x", pady=4)

        self.path_entry = create_styled_entry(path_input_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, 10))
        self.path_entry.bind("<KeyRelease>", self.handle_path_change)

        browse_btn = create_styled_button(
            path_input_frame,
            text="📁 Browse",
            command=self.browse_folder,
            bg=COLORS["accent"],
            hover_bg="#0EA5E9",
        )
        browse_btn.pack(side="left", ipadx=10, ipady=5)
        self.register_themable(browse_btn, bg="accent", fg="text", activebackground="accent", activeforeground="text")

        self.path_error = tk.Label(
            path_section,
            text="",
            font=FONTS["small"],
            bg=path_section.cget("bg"),
            fg=COLORS["danger"],
            wraplength=540,
            justify="left",
        )
        self.register_themable(self.path_error, bg="background", fg="danger")
        self.path_error.pack(anchor="w")
        self.create_hint_label(path_section, "Tip: Point to a dedicated folder to keep downloads tidy.")

        quality_section = self.create_setting_section(
            download_frame,
            title="Video Quality",
            icon="🎞",
            description="Select your preferred quality. The best available option is used when possible.",
        )

        self.quality_var = tk.StringVar(value="best")
        quality_cards = RadioCardGroup(
            quality_section,
            options=[
                {"value": "best", "label": "Best", "icon": "⭐", "description": "Always grab the highest resolution."},
                {"value": "high", "label": "High", "icon": "📺", "description": "Great balance of size and quality."},
                {"value": "medium", "label": "Medium", "icon": "📱", "description": "Optimised for smaller devices."},
                {"value": "low", "label": "Low", "icon": "🚀", "description": "Fast downloads, smallest files."},
            ],
            variable=self.quality_var,
            command=lambda _value: self.mark_dirty(),
        )
        quality_cards.pack(fill="x", pady=4)
        self.radio_groups.append(quality_cards)
        self.create_hint_label(quality_section, "Higher quality files are larger and may take longer to download.")

        audio_section = self.create_setting_section(
            download_frame,
            title="Audio Conversion",
            icon="🎧",
            description="Automatically convert videos to MP3 after download.",
        )

        self.convert_mp3_var = tk.BooleanVar()
        mp3_toggle = ToggleSwitch(
            audio_section,
            text="Convert downloads to MP3",
            variable=self.convert_mp3_var,
            command=self.mark_dirty,
        )
        mp3_toggle.pack(anchor="w", pady=4)
        Tooltip(mp3_toggle, "Ideal for quickly building playlists without extra steps.")
        self.toggle_switches.append(mp3_toggle)

        profile_section = self.create_setting_section(
            download_frame,
            title="Profile Download Limit",
            icon="👤",
            description="Control how many videos are downloaded when grabbing an entire profile.",
        )

        limit_label = tk.Label(
            profile_section,
            text="Maximum videos per profile:",
            font=FONTS["body"],
            bg=profile_section.cget("bg"),
            fg=COLORS["text"],
        )
        self.register_themable(limit_label, bg="background", fg="text")
        limit_label.pack(anchor="w", pady=(0, 4))

        self.profile_limit_entry = create_styled_entry(profile_section, width=15)
        self.profile_limit_entry.pack(anchor="w", ipady=3)
        self.profile_limit_entry.bind("<KeyRelease>", self.handle_profile_limit_change)

        self.profile_limit_error = tk.Label(
            profile_section,
            text="",
            font=FONTS["small"],
            bg=profile_section.cget("bg"),
            fg=COLORS["danger"],
            wraplength=360,
            justify="left",
        )
        self.register_themable(self.profile_limit_error, bg="background", fg="danger")
        self.profile_limit_error.pack(anchor="w", pady=(3, 0))
        self.create_hint_label(profile_section, "Set to 0 to download everything. Large profiles may take longer.")

    def create_advanced_tab(self):
        """Create Advanced settings tab."""
        advanced_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.register_themable(advanced_frame, bg="card")
        self.notebook.add(advanced_frame, text="🔧 Advanced")
        advanced_frame.grid_columnconfigure(0, weight=1)

        options_section = self.create_setting_section(
            advanced_frame,
            title="Download Options",
            icon="🛠",
            description="Fine-tune how downloads are organised and logged.",
        )

        self.save_history_var = tk.BooleanVar()
        history_toggle = ToggleSwitch(
            options_section,
            text="Save download history",
            variable=self.save_history_var,
            command=self.mark_dirty,
        )
        history_toggle.pack(anchor="w", pady=4)
        Tooltip(history_toggle, "Stores the last 100 downloads so you can revisit them later.")
        self.toggle_switches.append(history_toggle)

        self.profile_folders_var = tk.BooleanVar()
        folder_toggle = ToggleSwitch(
            options_section,
            text="Create folders for profile downloads",
            variable=self.profile_folders_var,
            command=self.mark_dirty,
        )
        folder_toggle.pack(anchor="w", pady=4)
        Tooltip(folder_toggle, "Helpful when saving content from multiple creators at once.")
        self.toggle_switches.append(folder_toggle)
        self.create_hint_label(options_section, "Useful when downloading from multiple creators.")

    def create_updates_tab(self):
        """Create Updates tab."""
        updates_frame = tk.Frame(self.notebook, bg=COLORS["card"])
        self.register_themable(updates_frame, bg="card")
        self.notebook.add(updates_frame, text="🔄 Updates")
        updates_frame.grid_columnconfigure(0, weight=1)

        auto_section = self.create_setting_section(
            updates_frame,
            title="Automatic Updates",
            icon="⚡",
            description="Keep yt-dlp up to date automatically each time the app starts.",
        )

        self.auto_update_var = tk.BooleanVar()
        auto_toggle = ToggleSwitch(
            auto_section,
            text="Check for updates on launch",
            variable=self.auto_update_var,
            command=self.mark_dirty,
        )
        auto_toggle.pack(anchor="w", pady=4)
        Tooltip(auto_toggle, "Runs a quick update check every time you open the app.")
        self.toggle_switches.append(auto_toggle)

        manual_section = self.create_setting_section(
            updates_frame,
            title="Manual Update",
            icon="🔁",
            description="Update yt-dlp immediately when you need the latest fixes.",
        )

        self.current_version_var = tk.StringVar(value=f"Current yt-dlp version: {self.updater.get_version()}")
        current_version = tk.Label(
            manual_section,
            textvariable=self.current_version_var,
            font=FONTS["small"],
            bg=manual_section.cget("bg"),
            fg=COLORS["text_secondary"],
        )
        self.register_themable(current_version, bg="background", fg="text_secondary")
        current_version.pack(anchor="w", pady=(0, 8))

        self.update_button = create_styled_button(
            manual_section,
            text="🔄 Update yt-dlp",
            command=self.manual_update,
            bg=COLORS["success"],
            hover_bg="#059669",
        )
        self.update_button.pack(anchor="w", ipadx=14, ipady=6)
        self.register_themable(self.update_button, bg="success", fg="text", activebackground="success", activeforeground="text")

        self.update_progress = ttk.Progressbar(manual_section, mode="indeterminate", length=180)
        self.update_progress.pack(anchor="w", pady=(6, 0))
        self.update_progress.stop()

        self.update_status_label = tk.Label(
            manual_section,
            text="",
            font=FONTS["small"],
            bg=manual_section.cget("bg"),
            fg=COLORS["text_secondary"],
            wraplength=540,
            justify="left",
        )
        self.register_themable(self.update_status_label, bg="background", fg="text_secondary")
        self.update_status_label.pack(anchor="w", pady=(4, 0))
        self.create_hint_label(manual_section, "Requires an active internet connection.")

    def create_setting_section(self, parent, title, icon=None, description=None):
        """Create a styled section container with optional description."""
        wrapper = tk.Frame(parent, bg=COLORS["card"])
        self.register_themable(wrapper, bg="card")
        wrapper.pack(pady=8, padx=10, fill="x")

        section = tk.Frame(
            wrapper,
            bg=COLORS["background"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
        )
        self.register_themable(section, bg="background", highlightbackground="border")
        section.pack(fill="x")

        header = tk.Frame(section, bg=COLORS["background"])
        self.register_themable(header, bg="background")
        header.pack(fill="x", padx=14, pady=(14, 0))

        title_text = f"{icon} {title}".strip() if icon else title
        title_label = tk.Label(
            header,
            text=title_text,
            font=FONTS["subheading"],
            bg=COLORS["background"],
            fg=COLORS["text"],
        )
        self.register_themable(title_label, bg="background", fg="text")
        title_label.pack(anchor="w")

        if description:
            desc_label = tk.Label(
                section,
                text=description,
                font=FONTS["small"],
                bg=COLORS["background"],
                fg=COLORS["text_secondary"],
                wraplength=540,
                justify="left",
            )
            self.register_themable(desc_label, bg="background", fg="text_secondary")
            desc_label.pack(fill="x", padx=14, pady=(4, 10))
        else:
            spacer = tk.Frame(section, bg=COLORS["background"], height=12)
            self.register_themable(spacer, bg="background")
            spacer.pack(fill="x", padx=14)

        content_frame = tk.Frame(section, bg=COLORS["background"])
        self.register_themable(content_frame, bg="background")
        content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        return content_frame

    def create_hint_label(self, parent, text):
        hint = tk.Label(
            parent,
            text=text,
            font=FONTS["small"],
            bg=parent.cget("bg"),
            fg=COLORS["text_secondary"],
            wraplength=540,
            justify="left",
        )
        hint.pack(anchor="w", pady=(3, 0))
        self.register_themable(hint, bg="background", fg="text_secondary")
        return hint

    def load_settings(self):
        """Load current settings."""
        self.suppress_change = True

        download_path = self.config.get_setting("download_path", "")
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, download_path)
        self.clear_path_error()

        theme_value = self.config.get_setting("theme", "light")
        if theme_value not in {"light", "dark"}:
            theme_value = "light"
        self.theme_var.set(theme_value)
        self.apply_theme_preview(theme_value)

        quality_value = self.config.get_setting("video_quality", "best")
        if quality_value not in {"best", "high", "medium", "low"}:
            quality_value = "best"
        self.quality_var.set(quality_value)

        language_code = self.config.get_setting("language", "en")
        language_display = LANGUAGES.get(language_code, language_code.upper())
        if getattr(self, "language_options", None) and language_display in self.language_options:
            self.language_var.set(language_display)
        elif getattr(self, "language_options", None):
            first_language = next(iter(self.language_options.keys()))
            self.language_var.set(first_language)
            language_display = first_language
        self.app_info_label.config(text=f"{APP_NAME} v{APP_VERSION}\nLanguage: {language_display}")

        self.auto_update_var.set(self.config.get_setting("auto_update_ytdlp", True))
        self.save_history_var.set(self.config.get_setting("save_history", True))
        self.profile_folders_var.set(self.config.get_setting("create_profile_folders", True))
        self.convert_mp3_var.set(self.config.get_setting("convert_to_mp3", False))

        limit = self.config.get_setting("profile_video_limit", 10)
        self.profile_limit_entry.delete(0, tk.END)
        self.profile_limit_entry.insert(0, str(limit))
        self.clear_profile_limit_error()

        self.suppress_change = False
        self.dirty = False
        self.update_save_state()

    def browse_folder(self):
        """Browse for download folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
            self.handle_path_change()

    def reset_to_defaults(self):
        """Load default settings into the form without saving."""
        defaults = copy.deepcopy(DEFAULT_SETTINGS)
        self.suppress_change = True

        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, defaults.get("download_path", ""))
        self.clear_path_error()

        default_theme = defaults.get("theme", "light")
        self.theme_var.set(default_theme)
        self.apply_theme_preview(default_theme)

        default_quality = defaults.get("video_quality", "best")
        self.quality_var.set(default_quality)

        language_code = defaults.get("language", "en")
        language_display = LANGUAGES.get(language_code, language_code.upper())
        if getattr(self, "language_options", None) and language_display in self.language_options:
            self.language_var.set(language_display)
        else:
            self.language_var.set(language_display)

        self.app_info_label.config(text=f"{APP_NAME} v{APP_VERSION}\nLanguage: {language_display}")

        self.auto_update_var.set(defaults.get("auto_update_ytdlp", True))
        self.save_history_var.set(defaults.get("save_history", True))
        self.profile_folders_var.set(defaults.get("create_profile_folders", True))
        self.convert_mp3_var.set(defaults.get("convert_to_mp3", False))

        profile_limit = defaults.get("profile_video_limit", 10)
        self.profile_limit_entry.delete(0, tk.END)
        self.profile_limit_entry.insert(0, str(profile_limit))
        self.clear_profile_limit_error()

        self.suppress_change = False
        self.dirty = True
        self.update_save_state()
        self.settings_status.show_info("Defaults restored. Save to keep changes.")

    def cancel_changes(self):
        """Revert preview theme and close without saving."""
        self.apply_theme_preview(self.original_theme)
        self._unbind_mousewheel()
        self.window.destroy()

    def save_settings(self):
        """Save settings."""
        valid, profile_limit = self.validate_settings()
        if not valid:
            self.settings_status.show_error("Fix highlighted fields before saving.")
            return

        selected_language = self.language_var.get() if hasattr(self, "language_var") else ""
        if getattr(self, "language_options", None):
            language_code = self.language_options.get(selected_language)
            if not language_code:
                language_code = next(iter(self.language_options.values()))
        else:
            language_code = "en"

        theme_value = self.theme_var.get() or "light"
        quality_value = self.quality_var.get() or "best"

        settings = {
            "download_path": self.path_entry.get().strip(),
            "language": language_code,
            "theme": theme_value,
            "video_quality": quality_value,
            "auto_update_ytdlp": self.auto_update_var.get(),
            "save_history": self.save_history_var.get(),
            "create_profile_folders": self.profile_folders_var.get(),
            "profile_video_limit": profile_limit,
            "convert_to_mp3": self.convert_mp3_var.get(),
        }

        self.config.update_settings(settings)
        self.original_settings = copy.deepcopy(self.config.settings)
        self.original_theme = theme_value
        self.preview_theme = theme_value

        language_display = LANGUAGES.get(language_code, selected_language or language_code.upper())
        self.app_info_label.config(text=f"{APP_NAME} v{APP_VERSION}\nLanguage: {language_display}")

        self.dirty = False
        self.update_save_state()
        self.settings_status.show_success("Settings saved successfully!")

    def on_close(self):
        """Handle window close by saving settings."""
        self.save_settings()
        self._unbind_mousewheel()
        self.window.destroy()

    def manual_update(self):
        """Manually update yt-dlp asynchronously."""
        if self.update_thread and self.update_thread.is_alive():
            return

        self.update_status_label.config(text="Checking for updates...", fg=COLORS["text_secondary"])
        self.update_button.config(state="disabled")
        self.update_progress.start(10)
        self.settings_status.show_info("Updating yt-dlp...")

        def worker():
            try:
                result = self.updater.update()
            except Exception as exc:
                result = {"success": False, "message": f"Update error: {exc}"}
            self.window.after(0, lambda: self._finish_update(result))

        self.update_thread = threading.Thread(target=worker, daemon=True)
        self.update_thread.start()

    def _finish_update(self, result):
        self.update_progress.stop()
        self.update_button.config(state="normal")

        if result.get("success"):
            self.current_version_var.set(f"Current yt-dlp version: {self.updater.get_version()}")
            message = result.get("message", "yt-dlp updated successfully!")
            self.update_status_label.config(text=f"✅ {message}", fg=COLORS["success"])
            self.settings_status.show_success(message)
        else:
            message = result.get("message", "Update failed")
            trimmed = message[:120]
            self.update_status_label.config(text=f"❌ {trimmed}", fg=COLORS["danger"])
            self.settings_status.show_error(trimmed)
