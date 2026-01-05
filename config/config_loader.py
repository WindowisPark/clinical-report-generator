"""
Centralized Configuration Loader
Provides unified access to application configuration with validation and error handling
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass


class ConfigLoader:
    """
    Singleton configuration loader for clinical report generator

    Loads configuration from:
    1. Environment variables (highest priority)
    2. config.yaml file (fallback)

    Usage:
        config = ConfigLoader()
        api_key = config.get_gemini_api_key()
    """

    _instance = None
    _config_data = None
    _initialized = False

    def __new__(cls, config_path: str = "config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config.yaml file (default: "config.yaml")
        """
        if self._initialized:
            return

        self.config_path = Path(config_path)
        self._load_config()
        self._initialized = True

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create config.yaml with the following structure:\n"
                "api_keys:\n"
                "  gemini_api_key: YOUR_API_KEY_HERE"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse config.yaml: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config.yaml: {e}")

        if not isinstance(self._config_data, dict):
            raise ConfigurationError("config.yaml must contain a valid YAML dictionary")

    def get_gemini_api_key(self) -> str:
        """
        Get Gemini API key from environment or config file

        Priority:
        1. GEMINI_API_KEY environment variable
        2. config.yaml -> api_keys.gemini_api_key

        Returns:
            Gemini API key string

        Raises:
            ConfigurationError: If API key is not found or invalid
        """
        # 1. Check environment variable
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            return api_key

        # 2. Check config.yaml
        if self._config_data:
            api_key = self._config_data.get('api_keys', {}).get('gemini_api_key')

            # Validate API key
            if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
                return api_key

        # API key not found
        raise ConfigurationError(
            "Gemini API key not found!\n"
            "Please set it via:\n"
            "1. Environment variable: export GEMINI_API_KEY='your_key_here'\n"
            "2. config.yaml: api_keys.gemini_api_key\n"
            "\nMake sure to replace 'YOUR_GEMINI_API_KEY_HERE' with your actual key."
        )

    def get_databricks_config(self) -> Dict[str, str]:
        """
        Get Databricks configuration from environment or config file

        Priority:
        1. Environment variables (DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN)
        2. config.yaml -> databricks section

        Returns:
            Dictionary with keys: server_hostname, http_path, access_token

        Raises:
            ConfigurationError: If required Databricks configuration is missing
        """
        config = {}

        # Try environment variables first
        server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        http_path = os.getenv('DATABRICKS_HTTP_PATH')
        access_token = os.getenv('DATABRICKS_TOKEN')

        # Fallback to config.yaml
        if not server_hostname and self._config_data:
            server_hostname = self._config_data.get('databricks', {}).get('server_hostname')
        if not http_path and self._config_data:
            http_path = self._config_data.get('databricks', {}).get('http_path')
        if not access_token and self._config_data:
            access_token = self._config_data.get('databricks', {}).get('access_token')

        # Validate all required fields are present and non-empty
        if not (server_hostname and server_hostname.strip()):
            raise ConfigurationError(
                "Databricks server_hostname not found!\n"
                "Please set via:\n"
                "1. Environment variable: DATABRICKS_SERVER_HOSTNAME\n"
                "2. config.yaml: databricks.server_hostname"
            )

        if not (http_path and http_path.strip()):
            raise ConfigurationError(
                "Databricks http_path not found!\n"
                "Please set via:\n"
                "1. Environment variable: DATABRICKS_HTTP_PATH\n"
                "2. config.yaml: databricks.http_path"
            )

        if not (access_token and access_token.strip()):
            raise ConfigurationError(
                "Databricks access_token not found!\n"
                "Please set via:\n"
                "1. Environment variable: DATABRICKS_TOKEN\n"
                "2. config.yaml: databricks.access_token"
            )

        return {
            'server_hostname': server_hostname.strip(),
            'http_path': http_path.strip(),
            'access_token': access_token.strip()
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated key path

        Examples:
            config.get('api_keys.gemini_api_key')
            config.get('database.host', 'localhost')

        Args:
            key_path: Dot-separated configuration key path
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if not self._config_data:
            return default

        keys = key_path.split('.')
        value = self._config_data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def reload(self) -> None:
        """Reload configuration from file"""
        self._load_config()

    @property
    def config_data(self) -> Dict[str, Any]:
        """Get raw configuration data (read-only)"""
        return self._config_data.copy() if self._config_data else {}


# Convenience function for direct imports
def get_config() -> ConfigLoader:
    """
    Get singleton ConfigLoader instance

    Returns:
        ConfigLoader instance
    """
    return ConfigLoader()
