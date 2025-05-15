import os
import json
from threading import Lock
from typing import Any
from logger import logger


class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config_data = {}
        self.lock = Lock()  # Ensure thread safety
        self.load_config()

    def load_config(self):
        with self.lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as file:
                        self.config_data = json.load(file)
                    logger.info(f"Config loaded from {self.config_file}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Error reading config file: {e}")
                    self.config_data = self.default_config()

    def save_config(self):
        """Save configuration to a JSON file."""
        config_dir = os.path.dirname(self.config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)  # Ensure directory exists        with self.lock:
            try:
                with open(self.config_file, 'w') as file:
                    json.dump(self.config_data, file, indent=4)
            except IOError as e:
                print(f"Error writing to config file: {e}")
                logger.error(f"Error writing to config file: {e}")
                
    def get(self, key: str, default=None) -> Any:
        """Retrieve a value, supporting nested keys using dot notation."""
        with self.lock:
            keys = key.split(".")
            value = self.config_data
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, default)
                else:
                    return default
            return value
            
    def set(self, key: str, value):
        """Set a configuration value and save it, supporting nested keys using dot notation."""
        with self.lock:
            keys = key.split(".")
            if not keys:
                return value
            
            current = self.config_data
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            self.save_config()
            return value

    def default_config(self):
        """Return default configuration."""
        return {
            "work_folder": "",
            "output_folder": "",
            "decryption_key": 0,
            "npk_type": 0,
            "aes_key": 0,
            "index_size": 0,
        }
