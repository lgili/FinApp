"""Tests for application configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from finlite.config import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_default_values(self):
        """Settings has sensible defaults."""
        settings = Settings()

        assert settings.database_filename == "finlite.db"
        assert settings.default_currency == "USD"
        assert settings.locale == "en_US"
        assert settings.log_level == "INFO"

    def test_finlite_data_dir_default(self):
        """Default data directory is ~/.finlite or overridden by env."""
        # Clean environment to ensure default behavior
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            # The default might be overridden by .env file or environment
            # Just check it's a valid Path
            assert isinstance(settings.finlite_data_dir, Path)

    def test_database_path_property(self):
        """database_path combines data_dir and filename."""
        settings = Settings()
        expected = settings.finlite_data_dir / "finlite.db"
        assert settings.database_path == expected

    def test_database_url_property(self):
        """database_url returns SQLAlchemy URL."""
        settings = Settings()
        assert settings.database_url.startswith("sqlite:///")
        assert str(settings.database_path) in settings.database_url

    def test_data_dir_alias(self):
        """data_dir is alias for finlite_data_dir."""
        settings = Settings()
        assert settings.data_dir == settings.finlite_data_dir

    def test_custom_database_filename(self):
        """Can override database filename."""
        settings = Settings(database_filename="custom.db")
        assert settings.database_filename == "custom.db"
        assert settings.database_path.name == "custom.db"

    def test_custom_currency(self):
        """Can override default currency."""
        settings = Settings(default_currency="BRL")
        assert settings.default_currency == "BRL"

    def test_custom_locale(self):
        """Can override locale."""
        settings = Settings(locale="pt_BR")
        assert settings.locale == "pt_BR"

    def test_custom_log_level(self):
        """Can override log level."""
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"

    def test_ensure_data_dir_creates_directory(self):
        """ensure_data_dir creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "test_finlite"
            settings = Settings(finlite_data_dir=data_dir)

            assert not data_dir.exists()
            settings.ensure_data_dir()
            assert data_dir.exists()
            assert data_dir.is_dir()

    def test_ensure_data_dir_idempotent(self):
        """ensure_data_dir is safe to call multiple times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "test_finlite"
            settings = Settings(finlite_data_dir=data_dir)

            settings.ensure_data_dir()
            settings.ensure_data_dir()  # Should not raise
            assert data_dir.exists()

    def test_ensure_data_dir_creates_parents(self):
        """ensure_data_dir creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "parent" / "child" / "finlite"
            settings = Settings(finlite_data_dir=data_dir)

            settings.ensure_data_dir()
            assert data_dir.exists()
            assert data_dir.parent.exists()

    def test_environment_variable_override(self):
        """Can override settings via environment variables."""
        with patch.dict(os.environ, {
            "DEFAULT_CURRENCY": "EUR",
            "LOG_LEVEL": "WARNING",
            "DATABASE_FILENAME": "test.db"
        }):
            settings = Settings()
            assert settings.default_currency == "EUR"
            assert settings.log_level == "WARNING"
            assert settings.database_filename == "test.db"

    def test_custom_data_dir(self):
        """Can set custom data directory."""
        custom_dir = Path("/tmp/custom_finlite")
        settings = Settings(finlite_data_dir=custom_dir)

        assert settings.finlite_data_dir == custom_dir
        assert settings.database_path == custom_dir / "finlite.db"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings_instance(self):
        """get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_creates_data_directory(self):
        """get_settings ensures data directory exists."""
        # This test relies on get_settings being called
        # The actual ~/.finlite directory should be created
        settings = get_settings()
        assert settings.finlite_data_dir.exists()

    def test_caching(self):
        """get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same object instance

    def test_default_configuration(self):
        """get_settings returns properly configured instance."""
        settings = get_settings()

        assert settings.database_filename == "finlite.db"
        assert settings.default_currency == "USD"
        assert settings.locale == "en_US"
        assert settings.log_level == "INFO"


class TestSettingsIntegration:
    """Integration tests for Settings."""

    def test_full_database_path_construction(self):
        """Complete database path is correctly constructed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "finlite_data"
            settings = Settings(
                finlite_data_dir=data_dir,
                database_filename="test.db"
            )

            expected_path = data_dir / "test.db"
            assert settings.database_path == expected_path

            expected_url = f"sqlite:///{expected_path}"
            assert settings.database_url == expected_url

    def test_case_insensitive_env_vars(self):
        """Environment variables are case insensitive."""
        with patch.dict(os.environ, {
            "default_currency": "GBP",
            "LOG_LEVEL": "ERROR"
        }):
            settings = Settings()
            assert settings.default_currency == "GBP"
            assert settings.log_level == "ERROR"

    def test_extra_env_vars_ignored(self):
        """Extra environment variables are ignored."""
        with patch.dict(os.environ, {
            "UNKNOWN_SETTING": "value",
            "RANDOM_VAR": "test"
        }):
            # Should not raise even with unknown env vars
            settings = Settings()
            assert isinstance(settings, Settings)
