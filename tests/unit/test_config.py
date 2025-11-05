"""
Tests for configuration file parsing and loading.

Critical Priority Tests (CRT-020 to CRT-027):
- Valid TOML config parsing
- Malformed TOML handling
- Missing config file (graceful degradation)
- Missing required fields
- Invalid source names
- Config file path resolution
- Default output path handling
- Metadata writing configuration
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Import tomli or tomllib depending on Python version
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

from grawlix.config import (
    Config,
    SourceConfig,
    load_config,
)


# ============================================================================
# CRT-020: Valid TOML Config Parsing
# ============================================================================

class TestValidConfigParsing:
    """Test parsing of valid TOML configuration files."""

    def test_load_config_with_all_sources(self, temp_config_dir, monkeypatch):
        """CRT-020: Parse config with multiple sources configured."""
        config_content = """
write_metadata_to_epub = true
output = "/tmp/books"

[sources.storytel]
username = "test@example.com"
password = "testpass123"

[sources.nextory]
username = "user@test.com"
password = "pass456"
library = "DK"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        # Mock user_config_dir to return our temp dir
        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert len(config.sources) == 2
        assert "storytel" in config.sources
        assert "nextory" in config.sources

        assert config.sources["storytel"].username == "test@example.com"
        assert config.sources["storytel"].password == "testpass123"
        assert config.sources["storytel"].library is None

        assert config.sources["nextory"].username == "user@test.com"
        assert config.sources["nextory"].password == "pass456"
        assert config.sources["nextory"].library == "DK"

        assert config.write_metadata_to_epub is True
        assert config.output == "/tmp/books"

    def test_load_config_minimal(self, temp_config_dir):
        """CRT-020: Parse minimal config with only one source."""
        config_content = """
[sources.storytel]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert len(config.sources) == 1
        assert config.write_metadata_to_epub is False  # Default
        assert config.output is None  # Default

    def test_load_config_with_special_characters(self, temp_config_dir):
        """CRT-020: Parse config with special characters in values."""
        config_content = """
[sources.test]
username = "user+tag@example.com"
password = "p@ss!w0rd#$%^&*()"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.sources["test"].username == "user+tag@example.com"
        assert config.sources["test"].password == "p@ss!w0rd#$%^&*()"

    def test_load_config_with_unicode(self, temp_config_dir):
        """CRT-020: Parse config with Unicode characters."""
        config_content = """
[sources.test]
username = "用户@example.com"
password = "пароль123"

output = "/home/user/Bücher"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content, encoding='utf-8')

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.sources["test"].username == "用户@example.com"
        assert config.sources["test"].password == "пароль123"
        assert config.output == "/home/user/Bücher"


# ============================================================================
# CRT-021: Malformed TOML Handling
# ============================================================================

class TestMalformedTOML:
    """Test handling of malformed TOML syntax."""

    def test_invalid_toml_syntax_raises_error(self, temp_config_dir):
        """CRT-021: Malformed TOML should raise TOMLDecodeError."""
        config_content = """
[sources.storytel
username = "test@example.com"  # Missing closing bracket
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            with pytest.raises(tomli.TOMLDecodeError):
                load_config()

    def test_invalid_boolean_format(self, temp_config_dir):
        """CRT-021: Invalid boolean should raise error."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

write_metadata_to_epub = True  # Should be lowercase 'true'
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            with pytest.raises(tomli.TOMLDecodeError):
                load_config()

    def test_unquoted_string_with_special_chars(self, temp_config_dir):
        """CRT-021: Unquoted strings with template variables should fail."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

output = {title}.{ext}  # Should be quoted
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            with pytest.raises(tomli.TOMLDecodeError):
                load_config()

    def test_invalid_utf8_encoding(self, temp_config_dir):
        """CRT-021: Invalid UTF-8 should cause error."""
        config_file = temp_config_dir / "grawlix.toml"
        # Write invalid UTF-8 bytes
        with open(config_file, 'wb') as f:
            f.write(b"[sources.test]\nusername = \"\xff\xfe\"\n")

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            with pytest.raises((UnicodeDecodeError, tomli.TOMLDecodeError)):
                load_config()

    def test_duplicate_keys(self, temp_config_dir):
        """CRT-021: Duplicate keys should raise error."""
        config_content = """
[sources.test]
username = "first@example.com"
username = "second@example.com"  # Duplicate key
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            with pytest.raises(tomli.TOMLDecodeError):
                load_config()


# ============================================================================
# CRT-022: Missing Config File Handling
# ============================================================================

class TestMissingConfigFile:
    """Test graceful handling when config file doesn't exist."""

    def test_missing_config_returns_empty_config(self, temp_config_dir):
        """CRT-022: Missing config should return empty Config (not crash)."""
        # Don't create any config file

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert isinstance(config, Config)
        assert len(config.sources) == 0
        assert config.write_metadata_to_epub is False
        assert config.output is None

    def test_empty_config_file(self, temp_config_dir):
        """CRT-022: Empty config file should return defaults."""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text("")  # Empty file

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert isinstance(config, Config)
        assert len(config.sources) == 0
        assert config.write_metadata_to_epub is False
        assert config.output is None

    def test_config_with_only_comments(self, temp_config_dir):
        """CRT-022: Config with only comments should return defaults."""
        config_content = """
# This is a comment
# Another comment
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert len(config.sources) == 0


# ============================================================================
# CRT-023: Missing Required Fields
# ============================================================================

class TestMissingFields:
    """Test handling of missing optional fields."""

    def test_source_without_password(self, temp_config_dir):
        """CRT-023: Source with only username (password optional)."""
        config_content = """
[sources.test]
username = "test@example.com"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.sources["test"].username == "test@example.com"
        assert config.sources["test"].password is None
        assert config.sources["test"].library is None

    def test_source_without_username(self, temp_config_dir):
        """CRT-023: Source with only password (username optional)."""
        config_content = """
[sources.test]
password = "testpass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.sources["test"].username is None
        assert config.sources["test"].password == "testpass"

    def test_source_with_only_library(self, temp_config_dir):
        """CRT-023: Source with only library field."""
        config_content = """
[sources.test]
library = "US"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.sources["test"].library == "US"
        assert config.sources["test"].username is None
        assert config.sources["test"].password is None

    def test_empty_source_section(self, temp_config_dir):
        """CRT-023: Empty source section should work."""
        config_content = """
[sources.test]
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert "test" in config.sources
        assert config.sources["test"].username is None
        assert config.sources["test"].password is None
        assert config.sources["test"].library is None


# ============================================================================
# CRT-024: Invalid Source Names
# ============================================================================

class TestSourceNames:
    """Test handling of various source names."""

    def test_unknown_source_name(self, temp_config_dir):
        """CRT-024: Unknown source names should still be loaded (for future sources)."""
        config_content = """
[sources.unknown_source]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        # Should still load, even if source doesn't exist yet
        assert "unknown_source" in config.sources
        assert config.sources["unknown_source"].username == "test@example.com"

    def test_source_name_with_underscores(self, temp_config_dir):
        """CRT-024: Source names with underscores."""
        config_content = """
[sources.my_custom_source]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert "my_custom_source" in config.sources

    def test_source_name_with_numbers(self, temp_config_dir):
        """CRT-024: Source names with numbers."""
        config_content = """
[sources.source123]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert "source123" in config.sources

    def test_multiple_unknown_sources(self, temp_config_dir):
        """CRT-024: Multiple unknown source names."""
        config_content = """
[sources.future_source_1]
username = "user1@example.com"
password = "pass1"

[sources.future_source_2]
username = "user2@example.com"
password = "pass2"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert len(config.sources) == 2
        assert "future_source_1" in config.sources
        assert "future_source_2" in config.sources


# ============================================================================
# CRT-025: Config File Path Resolution
# ============================================================================

class TestConfigPathResolution:
    """Test platform-specific config file path resolution."""

    def test_user_config_dir_called(self):
        """CRT-025: Should use platformdirs.user_config_dir."""
        with patch("grawlix.config.user_config_dir") as mock_config_dir:
            mock_config_dir.return_value = "/tmp/test_config"

            # Mock os.path.exists to return False (no config file)
            with patch("os.path.exists", return_value=False):
                config = load_config()

            # Should have called user_config_dir with correct args
            mock_config_dir.assert_called_once_with("grawlix", "jo1gi")

    def test_config_file_path_construction(self, temp_config_dir):
        """CRT-025: Config file should be at user_config_dir/grawlix.toml."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            # Mock open to track what file is opened
            original_open = open
            opened_files = []

            def tracking_open(*args, **kwargs):
                opened_files.append(args[0])
                return original_open(*args, **kwargs)

            with patch("builtins.open", tracking_open):
                config = load_config()

            # Should have opened the grawlix.toml file
            assert any("grawlix.toml" in str(f) for f in opened_files)

    @pytest.mark.skipif(os.name == 'nt', reason="Unix path test")
    def test_unix_config_path(self):
        """CRT-025: Unix systems use ~/.config/grawlix/grawlix.toml."""
        with patch("grawlix.config.user_config_dir") as mock_dir:
            mock_dir.return_value = os.path.expanduser("~/.config/grawlix")

            with patch("os.path.exists", return_value=False):
                config = load_config()

            # Should construct path correctly
            mock_dir.assert_called_once()


# ============================================================================
# CRT-026: Default Output Path Handling
# ============================================================================

class TestDefaultOutputPath:
    """Test default output path behavior."""

    def test_no_output_in_config_returns_none(self, temp_config_dir):
        """CRT-026: Missing output field should return None."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.output is None

    def test_output_path_with_template_variables(self, temp_config_dir):
        """CRT-026: Output path can contain template variables."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

output = "{title} - {authors}.{ext}"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.output == "{title} - {authors}.{ext}"

    def test_output_path_absolute(self, temp_config_dir):
        """CRT-026: Absolute output paths should be preserved."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

output = "/home/user/books/{title}.{ext}"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.output == "/home/user/books/{title}.{ext}"

    def test_output_path_relative(self, temp_config_dir):
        """CRT-026: Relative output paths should work."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

output = "books/{title}.{ext}"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.output == "books/{title}.{ext}"


# ============================================================================
# CRT-027: Metadata Writing Configuration
# ============================================================================

class TestMetadataWritingConfig:
    """Test write_metadata_to_epub configuration."""

    def test_metadata_writing_enabled(self, temp_config_dir):
        """CRT-027: write_metadata_to_epub = true should enable feature."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

write_metadata_to_epub = true
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.write_metadata_to_epub is True

    def test_metadata_writing_disabled(self, temp_config_dir):
        """CRT-027: write_metadata_to_epub = false should disable feature."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"

write_metadata_to_epub = false
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.write_metadata_to_epub is False

    def test_metadata_writing_default_false(self, temp_config_dir):
        """CRT-027: Default should be False when not specified."""
        config_content = """
[sources.test]
username = "test@example.com"
password = "pass"
"""
        config_file = temp_config_dir / "grawlix.toml"
        config_file.write_text(config_content)

        with patch("grawlix.config.user_config_dir", return_value=str(temp_config_dir)):
            config = load_config()

        assert config.write_metadata_to_epub is False


# ============================================================================
# Data Class Tests
# ============================================================================

class TestDataClasses:
    """Test Config and SourceConfig data classes."""

    def test_source_config_creation(self):
        """Test SourceConfig instantiation."""
        source = SourceConfig(
            username="test@example.com",
            password="testpass",
            library="US"
        )

        assert source.username == "test@example.com"
        assert source.password == "testpass"
        assert source.library == "US"

    def test_source_config_with_none_values(self):
        """Test SourceConfig with None values."""
        source = SourceConfig(
            username=None,
            password=None,
            library=None
        )

        assert source.username is None
        assert source.password is None
        assert source.library is None

    def test_config_creation(self):
        """Test Config instantiation."""
        sources = {
            "test": SourceConfig(
                username="test@example.com",
                password="pass",
                library=None
            )
        }

        config = Config(
            sources=sources,
            write_metadata_to_epub=True,
            output="/tmp/books"
        )

        assert len(config.sources) == 1
        assert config.write_metadata_to_epub is True
        assert config.output == "/tmp/books"

    def test_config_defaults(self):
        """Test Config with default values."""
        config = Config(sources={})

        assert len(config.sources) == 0
        assert config.write_metadata_to_epub is False
        assert config.output is None
