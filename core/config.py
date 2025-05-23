"""Provides game config utilities."""

from dataclasses import dataclass, field
import json
from typing import Any

@dataclass
class Config:
    """Represents a game config."""
    name = "Default"
    decryption_key: int | None = None

    entry_signature_name_map: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_dict(obj: dict[str, Any]) -> 'Config':
        """
        Creates a config from a `obj`.

        `obj` should contains the following keys:
        - `name`: `str`
        - `decryption_key`: `int`
        """
        cfg = Config()
        cfg.name = obj.get("name")
        if not isinstance(cfg.name, str):
            raise ValueError("Invalid dict: name must be a string.")
        cfg.decryption_key = obj.get("decryption_key")
        if cfg.decryption_key is not None and not isinstance(cfg.decryption_key, int):
            raise ValueError("Invalid dict: decryption_key must be an integer.")
        cfg.entry_signature_name_map = obj.get("entry_signature_name_map", {})
        if not isinstance(cfg.entry_signature_name_map, dict):
            raise ValueError("Invalid dict: entry_signature_name_map must be a dictionary.")
        return cfg

    @staticmethod
    def from_file(path: str) -> 'Config':
        """Creates a config from file."""
        with open(path, "r", encoding="utf-8") as config_file:
            data: dict[str, Any] = json.load(config_file)
            return Config.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the config to a dictionary.
        """
        return {
            "name": self.name,
            "decryption_key": self.decryption_key,
            "entry_signature_name_map": self.entry_signature_name_map,
        }
