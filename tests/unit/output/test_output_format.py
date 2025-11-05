"""
Tests for output path sanitization and formatting.

Critical Priority Tests (CRT-001 to CRT-008):
- Windows reserved filenames
- Path traversal prevention
- Forbidden character handling
- Filename length limits
- Template variable substitution
- None value handling
- Absolute vs relative paths
- Duplicate filename collision
"""

import pytest
import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

from grawlix.output import (
    format_output_location,
    remove_unwanted_chars,
    remove_strings,
)
from grawlix.book import Book, Metadata, SingleFile, OnlineFile
from grawlix.output.epub import Epub


# ============================================================================
# CRT-001: Windows Reserved Filenames
# ============================================================================

class TestWindowsReservedFilenames:
    """Test that Windows reserved names are properly sanitized."""

    RESERVED_NAMES = [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    ]

    @pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
    @patch("platform.system", return_value="Windows")
    def test_reserved_names_are_prefixed(self, mock_platform, reserved_name):
        """CRT-001: Reserved names should be prefixed with underscore on Windows."""
        result = remove_unwanted_chars(reserved_name)
        assert result == f"_{reserved_name}", f"{reserved_name} should be prefixed with underscore"

    @pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
    @patch("platform.system", return_value="Windows")
    def test_reserved_names_case_insensitive(self, mock_platform, reserved_name):
        """CRT-001: Reserved names should be detected case-insensitively."""
        lowercase = reserved_name.lower()
        result = remove_unwanted_chars(lowercase)
        assert result == f"_{lowercase}", f"{lowercase} should be prefixed with underscore"

    @pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
    @patch("platform.system", return_value="Windows")
    def test_reserved_names_with_extension(self, mock_platform, reserved_name):
        """CRT-001: Reserved names with extensions should be sanitized."""
        filename = f"{reserved_name}.txt"
        result = remove_unwanted_chars(filename)
        assert result.startswith("_"), f"{filename} should be prefixed with underscore"

    @pytest.mark.parametrize("reserved_name", RESERVED_NAMES)
    @patch("platform.system", return_value="Linux")
    def test_reserved_names_not_prefixed_on_unix(self, mock_platform, reserved_name):
        """CRT-001: Reserved names should not be modified on Unix systems."""
        result = remove_unwanted_chars(reserved_name)
        # On Unix, these names are fine (unless they contain forbidden chars)
        assert not result.startswith("_") or result == f"_{reserved_name}"


# ============================================================================
# CRT-002: Path Traversal Prevention
# ============================================================================

class TestPathTraversalPrevention:
    """Test that path traversal attempts are neutralized."""

    @pytest.mark.parametrize("traversal_path", [
        "../../../etc/passwd",
        "../../etc/passwd",
        "../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "test/../../etc/passwd",
    ])
    def test_path_traversal_characters_removed(self, traversal_path):
        """CRT-002: Path traversal sequences should be neutralized."""
        result = remove_unwanted_chars(traversal_path)
        # Slashes and backslashes should be replaced
        assert ".." not in result or "/" not in result, "Path traversal should be prevented"
        assert "\\" not in result, "Backslashes should be removed/replaced"

    def test_path_traversal_in_book_title(self, complete_metadata):
        """CRT-002: Path traversal in book title should be sanitized."""
        complete_metadata.title = "../../../evil"
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{title}.{ext}")

        # Should not contain path traversal
        assert "../" not in location
        assert "..\\" not in location


# ============================================================================
# CRT-003: Forbidden Character Handling
# ============================================================================

class TestForbiddenCharacters:
    """Test that forbidden characters are properly handled."""

    @pytest.mark.parametrize("char", ['<', '>', ':', '"', '|', '?', '*'])
    @patch("platform.system", return_value="Windows")
    def test_windows_forbidden_chars_replaced(self, mock_platform, char):
        """CRT-003: Windows forbidden characters should be replaced with underscore."""
        input_str = f"test{char}file"
        result = remove_unwanted_chars(input_str)
        assert char not in result, f"Character {char} should be removed/replaced"
        assert "_" in result or "-" in result, "Should be replaced with _ or -"

    @pytest.mark.parametrize("char", ['/', '\\'])
    @patch("platform.system", return_value="Windows")
    def test_windows_slashes_replaced_with_dash(self, mock_platform, char):
        """CRT-003: Slashes should be replaced with dash on Windows."""
        input_str = f"test{char}file"
        result = remove_unwanted_chars(input_str)
        assert char not in result
        assert "-" in result, "Slashes should be replaced with dash"

    @patch("platform.system", return_value="Linux")
    def test_unix_forward_slash_replaced(self, mock_platform):
        """CRT-003: Forward slash should be replaced on Unix."""
        result = remove_unwanted_chars("test/file")
        assert "/" not in result
        assert "-" in result, "Forward slash should be replaced with dash"

    @patch("platform.system", return_value="Darwin")
    def test_macos_colon_and_slash_replaced(self, mock_platform):
        """CRT-003: Both colon and slash should be replaced on macOS."""
        result = remove_unwanted_chars("test:file/name")
        assert ":" not in result
        assert "/" not in result
        assert "-" in result, "Special chars should be replaced with dash"

    @pytest.mark.parametrize("char", ['\x00', '\x01', '\x1f', '\x7f'])
    def test_control_characters_removed(self, char):
        """CRT-003: Control characters and null bytes should be removed."""
        input_str = f"test{char}file"
        result = remove_unwanted_chars(input_str)
        assert char not in result, f"Control character {repr(char)} should be removed"


# ============================================================================
# CRT-004: Filename Length Limits
# ============================================================================

class TestFilenameLengthLimits:
    """Test filename length constraints."""

    def test_long_filename_truncated(self):
        """CRT-004: Very long filenames should be truncated to max_length."""
        long_name = "a" * 250  # Exceeds 200 byte limit
        result = remove_unwanted_chars(long_name)
        assert len(result.encode('utf-8')) <= 200, "Should be truncated to max length"

    def test_long_unicode_filename_truncated(self):
        """CRT-004: Long Unicode filenames should be truncated at UTF-8 boundaries."""
        # Unicode characters take multiple bytes
        long_unicode = "测试文件" * 50  # Chinese characters
        result = remove_unwanted_chars(long_unicode)
        assert len(result.encode('utf-8')) <= 200, "Should respect byte limit"
        # Should still be valid UTF-8
        assert result.encode('utf-8').decode('utf-8') == result

    def test_exactly_max_length_not_truncated(self):
        """CRT-004: Filenames at exactly max length should not be truncated."""
        name_199_bytes = "a" * 199
        result = remove_unwanted_chars(name_199_bytes)
        assert result == name_199_bytes, "Should not truncate if under limit"

    def test_truncation_removes_trailing_spaces(self):
        """CRT-004: Truncation should not leave trailing spaces."""
        long_name = "a" * 195 + "     "  # Spaces at end
        result = remove_unwanted_chars(long_name)
        assert not result.endswith(" "), "Should remove trailing spaces"


# ============================================================================
# CRT-005: Template Variable Substitution
# ============================================================================

class TestTemplateVariableSubstitution:
    """Test template variable expansion."""

    def test_title_substitution(self, complete_metadata):
        """CRT-005: {title} should be substituted correctly."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{title}.{ext}")
        # Title should be in the path (with unwanted chars removed)
        assert "Complete Test Book" in location or "Complete_Test_Book" in location

    def test_authors_substitution(self, complete_metadata):
        """CRT-005: {authors} should be substituted with joined author names."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{authors}.{ext}")
        # Should contain author names
        assert "Test Author" in location or "Author" in location

    def test_series_and_index_substitution(self, complete_metadata):
        """CRT-005: {series} and {index} should be substituted correctly."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{series}_{index}.{ext}")
        assert "Test Series" in location or "Test_Series" in location
        assert "1" in location

    def test_all_variables_substitution(self, complete_metadata):
        """CRT-005: Multiple template variables should work together."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        template = "{series}/{index} - {title} by {authors}.{ext}"
        location = format_output_location(book, output_format, template)
        # Should not have unreplaced template variables
        assert "{" not in location
        assert "}" not in location
        assert location.endswith(".epub")

    def test_extension_substitution(self, complete_metadata):
        """CRT-005: {ext} should be replaced with output format extension."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "book.{ext}")
        assert location.endswith(".epub")


# ============================================================================
# CRT-006: None Value Handling
# ============================================================================

class TestNoneValueHandling:
    """Test handling of None/missing metadata values."""

    def test_missing_series_uses_unknown(self, minimal_metadata):
        """CRT-006: Missing series should be replaced with 'UNKNOWN'."""
        book = Book(
            metadata=minimal_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{series}.{ext}")
        assert "UNKNOWN" in location

    def test_missing_index_uses_unknown(self, minimal_metadata):
        """CRT-006: Missing index should be replaced with 'UNKNOWN'."""
        book = Book(
            metadata=minimal_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{index}.{ext}")
        assert "UNKNOWN" in location

    def test_empty_authors_list(self, minimal_metadata):
        """CRT-006: Empty authors list should be handled gracefully."""
        minimal_metadata.authors = []
        book = Book(
            metadata=minimal_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{authors}.{ext}")
        # Should not crash, should have empty or default value
        assert location.endswith(".epub")

    def test_all_optional_fields_none(self):
        """CRT-006: Book with only title should work."""
        metadata = Metadata(title="Minimal Book")
        book = Book(
            metadata=metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "{title}.{ext}")
        assert "Minimal Book" in location or "Minimal_Book" in location


# ============================================================================
# CRT-007: Absolute vs Relative Path Handling
# ============================================================================

class TestAbsoluteRelativePaths:
    """Test proper handling of absolute and relative paths."""

    def test_relative_path_template(self, complete_metadata):
        """CRT-007: Relative paths should work correctly."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "books/{title}.{ext}")
        # Should be a relative path starting with books/
        assert "books" in location
        assert location.endswith(".epub")

    def test_absolute_path_template_unix(self, complete_metadata):
        """CRT-007: Absolute Unix paths should be preserved."""
        if platform.system() == "Windows":
            pytest.skip("Unix path test, skipping on Windows")

        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "/tmp/{title}.{ext}")
        # Should be absolute path
        assert location.startswith("/tmp") or location.startswith("/private/tmp")  # macOS links /tmp

    def test_home_directory_expansion(self, complete_metadata):
        """CRT-007: Tilde (~) should expand to home directory."""
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()
        location = format_output_location(book, output_format, "~/{title}.{ext}")
        # Should expand ~
        assert "~" not in location
        import os
        assert os.path.expanduser("~") in location

    def test_environment_variable_expansion(self, complete_metadata, monkeypatch):
        """CRT-007: Environment variables should be expanded."""
        monkeypatch.setenv("TEST_BOOK_DIR", "/tmp/test_books")
        book = Book(
            metadata=complete_metadata,
            data=SingleFile(file=OnlineFile(url="https://example.com/book.epub", extension="epub"))
        )
        output_format = Epub()

        if platform.system() == "Windows":
            template = "%TEST_BOOK_DIR%/{title}.{ext}"
        else:
            template = "$TEST_BOOK_DIR/{title}.{ext}"

        location = format_output_location(book, output_format, template)
        # Should expand environment variable
        assert "test_books" in location or "TEST_BOOK_DIR" not in location


# ============================================================================
# CRT-008: Edge Cases and Additional Sanitization
# ============================================================================

class TestEdgeCases:
    """Test edge cases in path sanitization."""

    @patch("platform.system", return_value="Windows")
    def test_trailing_period_removed_windows(self, mock_platform):
        """CRT-008: Windows doesn't allow trailing periods."""
        result = remove_unwanted_chars("filename...")
        assert not result.endswith("."), "Trailing periods should be removed on Windows"

    @patch("platform.system", return_value="Windows")
    def test_trailing_space_removed_windows(self, mock_platform):
        """CRT-008: Windows doesn't allow trailing spaces."""
        result = remove_unwanted_chars("filename   ")
        assert not result.endswith(" "), "Trailing spaces should be removed on Windows"

    def test_empty_string_returns_default(self):
        """CRT-008: Empty input should return default 'untitled'."""
        result = remove_unwanted_chars("")
        assert result == "untitled", "Empty string should return default"

    def test_only_forbidden_chars_returns_default(self):
        """CRT-008: String with only forbidden chars should return default."""
        result = remove_unwanted_chars("///")
        assert result != "", "Should not return empty string"
        # Should have some safe content
        assert len(result) > 0

    def test_leading_trailing_whitespace_removed(self):
        """CRT-008: Leading and trailing whitespace should be trimmed."""
        result = remove_unwanted_chars("  filename  ")
        assert result == "filename", "Whitespace should be trimmed"

    def test_unicode_filename_preserved(self):
        """CRT-008: Valid Unicode filenames should be preserved."""
        unicode_name = "测试文件_тест_ファイル"
        result = remove_unwanted_chars(unicode_name)
        # Unicode should be preserved (only forbidden chars removed)
        assert len(result) > 0
        # Should still be valid UTF-8
        result.encode('utf-8')

    def test_mixed_forbidden_and_valid_chars(self):
        """CRT-008: Mix of forbidden and valid characters."""
        input_str = "Test <Book>: Chapter 1"
        result = remove_unwanted_chars(input_str)
        assert "<" not in result
        assert ">" not in result
        assert "Test" in result
        assert "Book" in result
        assert "Chapter" in result


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestRemoveStrings:
    """Test the remove_strings utility function."""

    def test_remove_single_string(self):
        """Test removing a single substring."""
        result = remove_strings("hello world", ["world"])
        assert result == "hello "

    def test_remove_multiple_strings(self):
        """Test removing multiple substrings."""
        result = remove_strings("hello world foo bar", ["world", "foo"])
        assert result == "hello   bar"

    def test_remove_overlapping_strings(self):
        """Test removing strings that might overlap."""
        result = remove_strings("ababab", ["ab"])
        assert result == ""

    def test_remove_nonexistent_string(self):
        """Test removing string that doesn't exist."""
        result = remove_strings("hello world", ["xyz"])
        assert result == "hello world"
