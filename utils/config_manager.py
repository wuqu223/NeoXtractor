import os
import json
from threading import Lock

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config_data = {}
        self.lock = Lock()  # Ensure thread safety
        self.load_config()

    def load_config(self):
        """Load configuration from a JSON file."""
        with self.lock:
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as file:
                        self.config_data = json.load(file)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading config file: {e}")
                    self.config_data = self.default_config()
            else:
                self.config_data = self.default_config()

    def save_config(self):
        """Save configuration to a JSON file."""
        if(os.path.dirname(self.config_file)):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)  # Ensure directory exists
        with self.lock:
            try:
                with open(self.config_file, 'w') as file:
                    json.dump(self.config_data, file, indent=4)
            except IOError as e:
                print(f"Error writing to config file: {e}")

    def get(self, key, default=None):
        """Get a configuration value."""
        with self.lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save it."""
        print(key)
        if key == "decryption_key":
            if not isinstance(value, int):
                raise ValueError("The decryption_key must be an integer.")
            value = int(value) # Ensure it is stored as int
        self.config_data[key] = value
        self.save_config()

    def default_config(self):
        """Return default configuration."""
        return {
            "output_folder": "",
            "decryption_key": 0
        }
