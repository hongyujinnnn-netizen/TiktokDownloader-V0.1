"""
Configuration Manager
Handle application settings and history
"""

import json
from datetime import datetime
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import SETTINGS_FILE, HISTORY_FILE, DEFAULT_SETTINGS


class ConfigManager:
    """Manage application configuration"""

    _settings_cache = None
    _settings_mtime = None
    _cache_lock = threading.RLock()

    def __init__(self):
        self.settings_file = SETTINGS_FILE
        self.history_file = HISTORY_FILE
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file and share cache across instances."""
        with ConfigManager._cache_lock:
            if ConfigManager._settings_cache is None:
                should_persist = False
                if self.settings_file.exists():
                    try:
                        with open(self.settings_file, 'r', encoding='utf-8') as f:
                            loaded = json.load(f)
                        if not isinstance(loaded, dict):
                            raise ValueError("Settings file root must be a JSON object")
                    except Exception:
                        loaded = DEFAULT_SETTINGS.copy()
                        should_persist = True
                else:
                    loaded = DEFAULT_SETTINGS.copy()
                    should_persist = True

                ConfigManager._settings_cache = loaded
                self.settings = ConfigManager._settings_cache

                if self.settings_file.exists():
                    try:
                        ConfigManager._settings_mtime = self.settings_file.stat().st_mtime
                    except OSError:
                        ConfigManager._settings_mtime = None
                else:
                    ConfigManager._settings_mtime = None

                if should_persist:
                    self._save_settings()
            else:
                latest_mtime = None
                if self.settings_file.exists():
                    try:
                        latest_mtime = self.settings_file.stat().st_mtime
                    except OSError:
                        latest_mtime = None

                if (
                    latest_mtime is not None
                    and (ConfigManager._settings_mtime is None or latest_mtime > ConfigManager._settings_mtime)
                ):
                    try:
                        with open(self.settings_file, 'r', encoding='utf-8') as f:
                            loaded = json.load(f)
                        if isinstance(loaded, dict):
                            ConfigManager._settings_cache.clear()
                            ConfigManager._settings_cache.update(loaded)
                            ConfigManager._settings_mtime = latest_mtime
                    except Exception:
                        pass

                self.settings = ConfigManager._settings_cache
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            try:
                ConfigManager._settings_mtime = self.settings_file.stat().st_mtime
            except OSError:
                ConfigManager._settings_mtime = None
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key, default=None):
        """
        Get a setting value
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
        
        Returns:
            Setting value
        """
        with ConfigManager._cache_lock:
            return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
        """
        with ConfigManager._cache_lock:
            self.settings[key] = value
            self._save_settings()
    
    def update_settings(self, settings_dict):
        """
        Update multiple settings
        
        Args:
            settings_dict: Dictionary of settings to update
        """
        with ConfigManager._cache_lock:
            self.settings.update(settings_dict)
            self._save_settings()
    
    def reset_settings(self):
        """Reset settings to default"""
        with ConfigManager._cache_lock:
            self.settings.clear()
            self.settings.update(DEFAULT_SETTINGS)
            self._save_settings()
    
    def add_to_history(self, item):
        """
        Add item to download history
        
        Args:
            item: History item dict with title, url, type, path
        """
        if not self.get_setting("save_history"):
            return
        
        history = self.get_history()
        
        # Add timestamp
        item['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        history.append(item)
        
        # Keep only last 100 items
        if len(history) > 100:
            history = history[-100:]
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_history(self):
        """
        Get download history
        
        Returns:
            list: History items
        """
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def clear_history(self):
        """Clear download history"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error clearing history: {e}")
    
    def export_settings(self, export_path):
        """
        Export settings to file
        
        Args:
            export_path: Path to export file
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except:
            return False
    
    def import_settings(self, import_path):
        """
        Import settings from file
        
        Args:
            import_path: Path to import file
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            if not isinstance(imported, dict):
                return False
            with ConfigManager._cache_lock:
                self.settings.update(imported)
                self._save_settings()
            return True
        except:
            return False
