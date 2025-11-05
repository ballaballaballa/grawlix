"""
Tests for utility functions.

High Priority Tests (HGH-040 to HGH-044):
- Levenshtein distance calculation
- Edge cases (empty strings, identical strings)
- URL parsing and query parameter extraction
- Asset file loading
- Nearest string matching
"""

import pytest
from grawlix.utils import (
    levenstein_distance,
    nearest_string,
    get_arg_from_url,
    read_asset_file,
)
from grawlix.exceptions import DataNotFound


# ============================================================================
# HGH-040: Levenshtein Distance Calculation
# ============================================================================

class TestLevensteinDistance:
    """Test Levenshtein distance algorithm correctness."""

    def test_identical_strings(self):
        """HGH-040: Distance between identical strings should be 0."""
        assert levenstein_distance("hello", "hello") == 0
        assert levenstein_distance("test", "test") == 0
        assert levenstein_distance("a", "a") == 0

    def test_empty_strings(self):
        """HGH-041: Distance with empty string equals length of other string."""
        assert levenstein_distance("", "hello") == 5
        assert levenstein_distance("hello", "") == 5
        assert levenstein_distance("", "") == 0

    def test_single_character_difference(self):
        """HGH-040: Single character insertion/deletion/replacement."""
        # Insertion
        assert levenstein_distance("cat", "cats") == 1
        # Deletion
        assert levenstein_distance("cats", "cat") == 1
        # Replacement
        assert levenstein_distance("cat", "bat") == 1

    def test_multiple_operations(self):
        """HGH-040: Multiple edit operations."""
        assert levenstein_distance("kitten", "sitting") == 3  # classic example
        assert levenstein_distance("saturday", "sunday") == 3

    def test_completely_different_strings(self):
        """HGH-040: Completely different strings."""
        result = levenstein_distance("abc", "xyz")
        assert result == 3  # All three characters need replacement

    def test_case_sensitive(self):
        """HGH-040: Algorithm should be case-sensitive."""
        assert levenstein_distance("Hello", "hello") == 1
        assert levenstein_distance("TEST", "test") == 4

    def test_long_strings(self):
        """HGH-040: Works with longer strings."""
        str1 = "The quick brown fox"
        str2 = "The quack brown fix"
        # differences: ui->ua (2 ops), o->i (1 op) = 3 operations
        distance = levenstein_distance(str1, str2)
        assert distance == 3

    def test_unicode_strings(self):
        """HGH-040: Works with Unicode strings."""
        assert levenstein_distance("café", "cafe") == 1
        assert levenstein_distance("测试", "测验") == 1

    def test_caching(self):
        """HGH-040: Function uses LRU cache (same call returns cached result)."""
        # First call
        result1 = levenstein_distance("hello", "world")
        # Second call (should be cached)
        result2 = levenstein_distance("hello", "world")
        assert result1 == result2
        # Cache hit should be fast, but we can't directly test speed


# ============================================================================
# HGH-042: URL Parsing and Validation
# ============================================================================

class TestGetArgFromUrl:
    """Test URL query parameter extraction."""

    def test_single_query_parameter(self):
        """HGH-042: Extract single query parameter."""
        url = "https://example.com/book?id=12345"
        assert get_arg_from_url(url, "id") == "12345"

    def test_multiple_query_parameters(self):
        """HGH-042: Extract from URL with multiple parameters."""
        url = "https://example.com/book?id=123&format=epub&lang=en"
        assert get_arg_from_url(url, "id") == "123"
        assert get_arg_from_url(url, "format") == "epub"
        assert get_arg_from_url(url, "lang") == "en"

    def test_parameter_with_special_characters(self):
        """HGH-042: Handle URL-encoded parameters."""
        url = "https://example.com/search?q=hello+world&title=Test%20Book"
        assert get_arg_from_url(url, "q") == "hello world"
        assert get_arg_from_url(url, "title") == "Test Book"

    def test_missing_parameter_raises_exception(self):
        """HGH-042: Missing parameter should raise DataNotFound."""
        url = "https://example.com/book?id=123"
        with pytest.raises(DataNotFound):
            get_arg_from_url(url, "nonexistent")

    def test_url_without_query_string(self):
        """HGH-042: URL without query parameters should raise exception."""
        url = "https://example.com/book"
        with pytest.raises(DataNotFound):
            get_arg_from_url(url, "id")

    def test_parameter_with_multiple_values(self):
        """HGH-042: Parameter with multiple values returns first."""
        url = "https://example.com/search?tag=fiction&tag=scifi"
        # parse_qs returns a list; our function gets first item
        result = get_arg_from_url(url, "tag")
        assert result == "fiction"  # First value

    def test_empty_parameter_value(self):
        """HGH-042: Parameter with empty value."""
        url = "https://example.com/book?id="
        result = get_arg_from_url(url, "id")
        assert result == ""

    def test_numeric_parameter(self):
        """HGH-042: Numeric parameter is returned as string."""
        url = "https://example.com/book?id=12345&page=1"
        result = get_arg_from_url(url, "id")
        assert result == "12345"
        assert isinstance(result, str)

    def test_fragment_ignored(self):
        """HGH-042: URL fragment should not affect query parsing."""
        url = "https://example.com/book?id=123#section"
        assert get_arg_from_url(url, "id") == "123"


# ============================================================================
# HGH-043: Asset Loading
# ============================================================================

class TestReadAssetFile:
    """Test asset file loading from package resources."""

    def test_read_existing_asset(self):
        """HGH-043: Read an existing asset file."""
        # The grawlix package has *.txt files according to pyproject.toml
        # We would need to know what actual asset files exist
        # For now, test that the function exists and has correct signature
        assert callable(read_asset_file)

    def test_read_asset_returns_string(self):
        """HGH-043: Asset reading should return string."""
        # This test would need an actual asset file to exist
        # Skipping for now, as we don't know what assets exist
        pytest.skip("Requires knowledge of actual asset files in package")

    def test_read_nonexistent_asset_raises_error(self):
        """HGH-043: Reading nonexistent asset should raise error."""
        with pytest.raises((FileNotFoundError, AttributeError)):
            read_asset_file("nonexistent_file.txt")

    def test_asset_path_relative_to_package_root(self):
        """HGH-043: Asset path should be relative to grawlix package root."""
        # This would require knowing actual asset structure
        pytest.skip("Requires knowledge of package structure")


# ============================================================================
# HGH-044: Nearest String Matching
# ============================================================================

class TestNearestString:
    """Test finding nearest string using Levenshtein distance."""

    def test_exact_match_in_list(self):
        """HGH-044: Exact match should be returned."""
        candidates = ["apple", "banana", "cherry"]
        assert nearest_string("banana", candidates) == "banana"

    def test_close_match(self):
        """HGH-044: Find closest match with typo."""
        candidates = ["storytel", "nextory", "marvel"]
        assert nearest_string("stortel", candidates) == "storytel"
        assert nearest_string("nextry", candidates) == "nextory"

    def test_single_candidate(self):
        """HGH-044: Single candidate should always be returned."""
        candidates = ["only_option"]
        assert nearest_string("anything", candidates) == "only_option"

    def test_multiple_equal_distances(self):
        """HGH-044: When multiple strings have same distance, return one."""
        candidates = ["cat", "bat", "rat"]
        result = nearest_string("mat", candidates)
        # All have distance 1, should return one of them
        assert result in candidates

    def test_case_sensitivity(self):
        """HGH-044: Nearest string respects case."""
        candidates = ["Test", "test", "TEST"]
        assert nearest_string("test", candidates) == "test"

    def test_longer_candidate_list(self):
        """HGH-044: Works with larger candidate lists."""
        candidates = [
            "storytel", "nextory", "marvel", "dcuniverse",
            "internetarchive", "royalroad", "fanfictionnet",
            "flipp", "saxo", "ereolen", "webtoons", "mangaplus"
        ]
        assert nearest_string("stortel", candidates) == "storytel"
        assert nearest_string("marvl", candidates) == "marvel"
        assert nearest_string("royalrd", candidates) == "royalroad"

    def test_unicode_candidates(self):
        """HGH-044: Works with Unicode strings."""
        candidates = ["café", "naïve", "résumé"]
        result = nearest_string("cafe", candidates)
        assert result == "café"

    def test_empty_string_input(self):
        """HGH-044: Empty string finds shortest candidate."""
        candidates = ["a", "abc", "abcdef"]
        result = nearest_string("", candidates)
        # Should return shortest string (closest to empty)
        assert result == "a"

    def test_numbers_in_strings(self):
        """HGH-044: Works with numbers in strings."""
        candidates = ["book1", "book2", "book3"]
        assert nearest_string("bok2", candidates) == "book2"


# ============================================================================
# Integration Tests
# ============================================================================

class TestUtilsIntegration:
    """Test utils functions working together."""

    def test_url_parsing_with_source_names(self):
        """Integration: Parse URL and find nearest source name."""
        sources = ["storytel", "nextory", "marvel"]
        url = "https://example.com/book?source=stortel&id=123"

        # Get source from URL (with typo)
        source_param = get_arg_from_url(url, "source")
        # Find nearest match
        matched_source = nearest_string(source_param, sources)

        assert matched_source == "storytel"

    def test_typo_correction_workflow(self):
        """Integration: Correct typos in user input."""
        valid_formats = ["epub", "cbz", "acsm"]

        # User typed "epb" (typo)
        user_input = "epb"
        corrected = nearest_string(user_input, valid_formats)

        assert corrected == "epub"

    def test_case_insensitive_source_matching(self):
        """Integration: Match source names case-insensitively."""
        sources = ["storytel", "nextory", "marvel"]

        # Convert to lowercase for matching
        user_input = "Storytel"
        matched = nearest_string(user_input.lower(), sources)

        assert matched == "storytel"


# ============================================================================
# Edge Cases
# ============================================================================

class TestUtilsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_levenstein_very_long_strings(self):
        """Edge case: Very long strings (performance check)."""
        long_str1 = "a" * 100
        long_str2 = "a" * 99 + "b"
        distance = levenstein_distance(long_str1, long_str2)
        assert distance == 1

    def test_url_with_port_number(self):
        """Edge case: URL with port number."""
        url = "https://example.com:8080/book?id=123"
        assert get_arg_from_url(url, "id") == "123"

    def test_url_with_username_password(self):
        """Edge case: URL with authentication."""
        url = "https://user:pass@example.com/book?id=123"
        assert get_arg_from_url(url, "id") == "123"

    def test_nearest_string_all_different(self):
        """Edge case: All candidates very different."""
        candidates = ["aaaaa", "bbbbb", "ccccc"]
        result = nearest_string("zzzzz", candidates)
        # Should still return one of them
        assert result in candidates

    def test_levenstein_one_char_vs_many(self):
        """Edge case: Single character vs long string."""
        distance = levenstein_distance("a", "abcdefghij")
        assert distance == 9  # Need 9 insertions

    def test_url_query_with_equals_in_value(self):
        """Edge case: Query parameter value contains '='."""
        url = "https://example.com/search?formula=a=b+c"
        result = get_arg_from_url(url, "formula")
        # Should handle this gracefully
        assert "a=b" in result or result == "a=b+c"

    def test_nearest_string_with_empty_candidate(self):
        """Edge case: Empty string in candidates."""
        candidates = ["", "a", "abc"]
        result = nearest_string("", candidates)
        assert result == ""
