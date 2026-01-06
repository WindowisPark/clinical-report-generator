"""
Unit tests for config loader
Tests config loading from YAML file and environment variables
"""

import os
import pytest
from pathlib import Path
from config.config_loader import ConfigLoader, ConfigurationError, get_config


class TestConfigLoader:
    """Test suite for ConfigLoader"""

    def test_singleton_pattern(self):
        """ConfigLoader should be singleton"""
        config1 = ConfigLoader()
        config2 = ConfigLoader()
        assert config1 is config2

    def test_get_config_convenience_function(self):
        """get_config() should return singleton instance"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_config_file_exists(self):
        """config.yaml should exist"""
        config_path = Path("config.yaml")
        assert config_path.exists(), "config.yaml not found"

    def test_get_method_with_dot_notation(self):
        """get() should support dot notation for nested keys"""
        config = get_config()

        # Test accessing nested keys
        gemini_key = config.get('api_keys.gemini_api_key')
        assert gemini_key is not None or gemini_key == '', \
            "Should return value or empty string for api_keys.gemini_api_key"

    def test_get_method_with_default(self):
        """get() should return default for missing keys"""
        config = get_config()

        # Non-existent key should return default
        result = config.get('non.existent.key', 'default_value')
        assert result == 'default_value'

    def test_databricks_config_structure(self):
        """get_databricks_config() should return dict with required keys"""
        config = get_config()

        try:
            db_config = config.get_databricks_config()

            # Should have all required keys
            assert 'server_hostname' in db_config
            assert 'http_path' in db_config
            assert 'access_token' in db_config

            # All values should be non-empty strings
            assert isinstance(db_config['server_hostname'], str)
            assert isinstance(db_config['http_path'], str)
            assert isinstance(db_config['access_token'], str)

            assert db_config['server_hostname'].strip() != ''
            assert db_config['http_path'].strip() != ''
            assert db_config['access_token'].strip() != ''

        except ConfigurationError as e:
            # If config is not set, test should document this
            pytest.skip(f"Databricks config not set: {e}")

    def test_gemini_api_key_validation(self):
        """get_gemini_api_key() should not return placeholder value"""
        config = get_config()

        try:
            api_key = config.get_gemini_api_key()

            # Should not be the placeholder value
            assert api_key != "YOUR_GEMINI_API_KEY_HERE"
            assert api_key.strip() != ''

        except ConfigurationError as e:
            pytest.skip(f"Gemini API key not set: {e}")

    def test_config_data_property(self):
        """config_data property should return copy of config"""
        config = get_config()

        data1 = config.config_data
        data2 = config.config_data

        # Should be equal but not the same object (copy)
        assert data1 == data2
        assert data1 is not data2

    def test_environment_variable_priority(self, monkeypatch):
        """Environment variables should take priority over config.yaml"""
        config = get_config()

        # Set environment variable
        test_key = "TEST_GEMINI_KEY_123"
        monkeypatch.setenv('GEMINI_API_KEY', test_key)

        # Reload config to pick up env var
        config.reload()

        # Should use env var, not config.yaml
        api_key = config.get_gemini_api_key()
        assert api_key == test_key


class TestConfigLoaderErrorHandling:
    """Test error handling in ConfigLoader"""

    def test_missing_config_file_error(self, tmp_path, monkeypatch):
        """Should raise ConfigurationError if config.yaml doesn't exist"""
        # Change to temp directory without config.yaml
        monkeypatch.chdir(tmp_path)

        # Reset singleton
        ConfigLoader._instance = None
        ConfigLoader._initialized = False

        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            ConfigLoader("nonexistent.yaml")

    def test_databricks_config_missing_fields(self, monkeypatch):
        """Should raise ConfigurationError if Databricks config is incomplete"""
        config = get_config()

        # Clear environment variables
        monkeypatch.delenv('DATABRICKS_SERVER_HOSTNAME', raising=False)
        monkeypatch.delenv('DATABRICKS_HTTP_PATH', raising=False)
        monkeypatch.delenv('DATABRICKS_TOKEN', raising=False)

        # Reload config
        config.reload()

        # Mock empty databricks config in YAML
        original_config = config._config_data
        config._config_data = {'databricks': {}}

        try:
            with pytest.raises(ConfigurationError, match="server_hostname not found"):
                config.get_databricks_config()
        finally:
            # Restore original config
            config._config_data = original_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
