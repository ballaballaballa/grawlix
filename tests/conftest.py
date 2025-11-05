"""
Shared pytest fixtures for Grawlix tests.

This module provides reusable fixtures for:
- Sample data models (Metadata, Book, Series)
- Temporary directories and files
- Mock HTTP clients
- Encryption objects
- Sample EPUB/CBZ files
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from grawlix.book import (
    Metadata,
    Book,
    Series,
    SingleFile,
    ImageList,
    EpubInParts,
    HtmlFiles,
    HtmlFile,
    OnlineFile,
    OfflineFile,
)
from grawlix.encryption import AESEncryption, AESCTREncryption, XOrEncryption


# ============================================================================
# Metadata Fixtures
# ============================================================================

@pytest.fixture
def minimal_metadata() -> Metadata:
    """Minimal valid metadata with only required fields."""
    return Metadata(title="Test Book")


@pytest.fixture
def complete_metadata() -> Metadata:
    """Complete metadata with all fields populated."""
    return Metadata(
        title="The Complete Test Book",
        series="Test Series",
        index=1,
        authors=["Test Author", "Co-Author"],
        language="en",
        publisher="Test Publisher",
        identifier="ISBN:1234567890",
        description="A comprehensive test book for testing purposes.",
        release_date=date(2025, 1, 1),
        source="test_source",
    )


@pytest.fixture
def metadata_no_series() -> Metadata:
    """Metadata without series information."""
    return Metadata(
        title="Standalone Book",
        authors=["Single Author"],
        language="en",
        publisher="Independent Press",
    )


# ============================================================================
# Encryption Fixtures
# ============================================================================

@pytest.fixture
def aes_encryption() -> AESEncryption:
    """Sample AES CBC encryption."""
    return AESEncryption(
        key=b"0123456789abcdef",  # 16 bytes
        iv=b"fedcba9876543210",  # 16 bytes
    )


@pytest.fixture
def aes_ctr_encryption() -> AESCTREncryption:
    """Sample AES CTR encryption."""
    return AESCTREncryption(
        key=b"0123456789abcdef",  # 16 bytes
        nonce=b"12345678",  # 8 bytes
        initial_value=b"87654321",  # 8 bytes
    )


@pytest.fixture
def xor_encryption() -> XOrEncryption:
    """Sample XOR encryption."""
    return XOrEncryption(key=b"testkey")


# ============================================================================
# File Fixtures
# ============================================================================

@pytest.fixture
def online_file() -> OnlineFile:
    """Sample online file."""
    return OnlineFile(
        url="https://example.com/book.epub",
        extension="epub",
        encryption=None,
        headers={"User-Agent": "Grawlix-Test"},
        cookies=None,
    )


@pytest.fixture
def encrypted_online_file(aes_encryption: AESEncryption) -> OnlineFile:
    """Sample encrypted online file."""
    return OnlineFile(
        url="https://example.com/encrypted.epub",
        extension="epub",
        encryption=aes_encryption,
    )


@pytest.fixture
def offline_file() -> OfflineFile:
    """Sample offline file with content."""
    return OfflineFile(
        content=b"This is test EPUB content",
        extension="epub",
        encryption=None,
    )


# ============================================================================
# BookData Fixtures
# ============================================================================

@pytest.fixture
def single_file_data(online_file: OnlineFile) -> SingleFile:
    """Sample SingleFile BookData."""
    return SingleFile(file=online_file)


@pytest.fixture
def image_list_data() -> ImageList:
    """Sample ImageList BookData (for comics)."""
    images = [
        OnlineFile(url=f"https://example.com/page{i}.jpg", extension="jpg")
        for i in range(1, 6)
    ]
    return ImageList(images=images)


@pytest.fixture
def epub_in_parts_data() -> EpubInParts:
    """Sample EpubInParts BookData."""
    files = [
        OnlineFile(url=f"https://example.com/part{i}.epub", extension="epub")
        for i in range(1, 4)
    ]
    return EpubInParts(
        files=files,
        files_in_toc={
            "Chapter 1": "part1.epub",
            "Chapter 2": "part2.epub",
            "Chapter 3": "part3.epub",
        },
    )


@pytest.fixture
def html_files_data() -> HtmlFiles:
    """Sample HtmlFiles BookData."""
    htmlfiles = [
        HtmlFile(
            title=f"Chapter {i}",
            file=OnlineFile(url=f"https://example.com/chapter{i}.html", extension="html"),
            selector={"class": "content"},
        )
        for i in range(1, 4)
    ]
    return HtmlFiles(
        htmlfiles=htmlfiles,
        cover=OnlineFile(url="https://example.com/cover.jpg", extension="jpg"),
    )


# ============================================================================
# Book Fixtures
# ============================================================================

@pytest.fixture
def simple_book(complete_metadata: Metadata, single_file_data: SingleFile) -> Book:
    """Simple book with SingleFile data."""
    return Book(
        metadata=complete_metadata,
        data=single_file_data,
        overwrite=False,
    )


@pytest.fixture
def comic_book(minimal_metadata: Metadata, image_list_data: ImageList) -> Book:
    """Comic book with ImageList data."""
    return Book(
        metadata=minimal_metadata,
        data=image_list_data,
        overwrite=False,
    )


@pytest.fixture
def epub_parts_book(complete_metadata: Metadata, epub_in_parts_data: EpubInParts) -> Book:
    """Book with split EPUB parts."""
    return Book(
        metadata=complete_metadata,
        data=epub_in_parts_data,
        overwrite=False,
    )


@pytest.fixture
def html_book(minimal_metadata: Metadata, html_files_data: HtmlFiles) -> Book:
    """Book from HTML files."""
    return Book(
        metadata=minimal_metadata,
        data=html_files_data,
        overwrite=False,
    )


# ============================================================================
# Series Fixtures
# ============================================================================

@pytest.fixture
def simple_series() -> Series[str]:
    """Sample book series."""
    return Series(
        title="Test Series",
        book_ids=["book1", "book2", "book3"],
    )


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory that is cleaned up after the test."""
    dirpath = Path(tempfile.mkdtemp())
    yield dirpath
    shutil.rmtree(dirpath, ignore_errors=True)


@pytest.fixture
def temp_output_dir(temp_dir: Path) -> Path:
    """Temporary output directory for downloads."""
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def temp_config_dir(temp_dir: Path) -> Path:
    """Temporary config directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


# ============================================================================
# Mock HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Mock httpx.AsyncClient for testing HTTP operations."""
    client = AsyncMock()

    # Default mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"test content"
    mock_response.text = "test content"
    mock_response.json.return_value = {"test": "data"}

    client.get.return_value = mock_response
    client.post.return_value = mock_response

    return client


# ============================================================================
# Sample File Content Fixtures
# ============================================================================

@pytest.fixture
def sample_epub_content() -> bytes:
    """Minimal valid EPUB file content (simplified for testing)."""
    # This is a very minimal EPUB structure
    # Real EPUBs are zip files with specific structure
    return b"PK\x03\x04" + b"\x00" * 100  # ZIP file signature + padding


@pytest.fixture
def sample_image_content() -> bytes:
    """Sample image content (minimal valid JPEG)."""
    # JPEG file signature
    return b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def sample_config_dict() -> dict[str, Any]:
    """Sample configuration dictionary."""
    return {
        "output_path": "/tmp/books",
        "write_metadata": True,
        "sources": {
            "storytel": {
                "username": "test@example.com",
                "password": "testpass",
            },
            "nextory": {
                "username": "user@test.com",
                "password": "pass123",
            },
        },
    }


@pytest.fixture
def sample_toml_config(temp_config_dir: Path, sample_config_dict: dict[str, Any]) -> Path:
    """Create a sample TOML config file."""
    import tomli_w  # We'll need to add this for writing TOML in tests

    config_path = temp_config_dir / "config.toml"

    # Simple TOML writing (or write manually)
    config_content = """
[sources.storytel]
username = "test@example.com"
password = "testpass"

[sources.nextory]
username = "user@test.com"
password = "pass123"

output_path = "/tmp/books"
write_metadata = true
"""

    config_path.write_text(config_content)
    return config_path


# ============================================================================
# Parametrization Helpers
# ============================================================================

# Windows reserved filenames for parametrized tests
WINDOWS_RESERVED_NAMES = [
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
]

# Forbidden filename characters
FORBIDDEN_CHARS_WINDOWS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
FORBIDDEN_CHARS_UNIX = ['/']

# Template variable test data
TEMPLATE_VARIABLES = {
    "title": "Test Book",
    "authors": "Author One; Author Two",
    "series": "Test Series",
    "index": "1",
    "isbn": "1234567890",
    "language": "en",
}
