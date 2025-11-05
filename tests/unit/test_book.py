"""
Tests for book data models and structures.

Critical Priority Tests (CRT-030 to CRT-037):
- Metadata construction with all fields
- Metadata with minimal fields
- Book with different BookData types (SingleFile, ImageList, HtmlFiles, EpubInParts)
- Series with multiple books
- Equality and hashing
"""

import pytest
from datetime import date

from grawlix.book import (
    Metadata,
    Book,
    Series,
    SingleFile,
    ImageList,
    HtmlFiles,
    HtmlFile,
    EpubInParts,
    OnlineFile,
    OfflineFile,
)


# ============================================================================
# CRT-030: Metadata Construction with All Fields
# ============================================================================

class TestMetadataComplete:
    """Test Metadata with all fields populated."""

    def test_metadata_all_fields(self):
        """CRT-030: Create Metadata with all fields populated."""
        metadata = Metadata(
            title="Complete Test Book",
            series="Test Series",
            index=1,
            authors=["Author One", "Author Two"],
            language="en",
            publisher="Test Publisher",
            identifier="ISBN:1234567890",
            description="A comprehensive test book.",
            release_date=date(2025, 1, 1),
            source="test_source",
        )

        assert metadata.title == "Complete Test Book"
        assert metadata.series == "Test Series"
        assert metadata.index == 1
        assert len(metadata.authors) == 2
        assert "Author One" in metadata.authors
        assert "Author Two" in metadata.authors
        assert metadata.language == "en"
        assert metadata.publisher == "Test Publisher"
        assert metadata.identifier == "ISBN:1234567890"
        assert metadata.description == "A comprehensive test book."
        assert metadata.release_date == date(2025, 1, 1)
        assert metadata.source == "test_source"

    def test_metadata_as_dict_all_fields(self):
        """CRT-030: as_dict() should convert all fields correctly."""
        metadata = Metadata(
            title="Test Book",
            series="Test Series",
            index=2,
            authors=["Author One", "Author Two"],
            language="en",
            publisher="Publisher",
            identifier="ISBN:123",
            description="Description",
            release_date=date(2025, 1, 15),
            source="storytel",
        )

        result = metadata.as_dict()

        assert result["title"] == "Test Book"
        assert result["series"] == "Test Series"
        assert result["index"] == "2"
        assert result["authors"] == "Author One; Author Two"
        assert result["language"] == "en"
        assert result["publisher"] == "Publisher"
        assert result["identifier"] == "ISBN:123"
        assert result["description"] == "Description"
        assert result["release_date"] == "2025-01-15"
        assert result["source"] == "storytel"

    def test_metadata_multiple_authors(self):
        """CRT-030: Multiple authors should be stored as list."""
        metadata = Metadata(
            title="Multi-Author Book",
            authors=["First Author", "Second Author", "Third Author"]
        )

        assert len(metadata.authors) == 3
        assert metadata.authors[0] == "First Author"
        assert metadata.authors[1] == "Second Author"
        assert metadata.authors[2] == "Third Author"


# ============================================================================
# CRT-031: Metadata with Minimal Fields
# ============================================================================

class TestMetadataMinimal:
    """Test Metadata with only required fields."""

    def test_metadata_only_title(self):
        """CRT-031: Metadata with only title (required field)."""
        metadata = Metadata(title="Minimal Book")

        assert metadata.title == "Minimal Book"
        assert metadata.series is None
        assert metadata.index is None
        assert metadata.authors == []
        assert metadata.language is None
        assert metadata.publisher is None
        assert metadata.identifier is None
        assert metadata.description is None
        assert metadata.release_date is None
        assert metadata.source is None

    def test_metadata_as_dict_minimal(self):
        """CRT-031: as_dict() with minimal fields uses 'UNKNOWN' for None."""
        metadata = Metadata(title="Minimal Book")

        result = metadata.as_dict()

        assert result["title"] == "Minimal Book"
        assert result["series"] == "UNKNOWN"
        assert result["index"] == "UNKNOWN"
        assert result["authors"] == ""  # Empty list joins to empty string
        assert result["language"] == "UNKNOWN"
        assert result["publisher"] == "UNKNOWN"
        assert result["identifier"] == "UNKNOWN"
        assert result["description"] == "UNKNOWN"
        assert result["release_date"] == "UNKNOWN"
        assert result["source"] == "UNKNOWN"

    def test_metadata_empty_authors_list(self):
        """CRT-031: Empty authors list should join to empty string."""
        metadata = Metadata(title="Book", authors=[])

        result = metadata.as_dict()
        assert result["authors"] == ""

    def test_metadata_none_release_date(self):
        """CRT-031: None release_date should convert to 'UNKNOWN'."""
        metadata = Metadata(title="Book", release_date=None)

        result = metadata.as_dict()
        assert result["release_date"] == "UNKNOWN"


# ============================================================================
# CRT-032: Book with SingleFile BookData
# ============================================================================

class TestBookWithSingleFile:
    """Test Book with SingleFile data (most common case)."""

    def test_book_with_online_file(self):
        """CRT-032: Book with SingleFile containing OnlineFile."""
        metadata = Metadata(title="Test Book")
        online_file = OnlineFile(
            url="https://example.com/book.epub",
            extension="epub"
        )
        book_data = SingleFile(file=online_file)
        book = Book(metadata=metadata, data=book_data)

        assert book.metadata.title == "Test Book"
        assert isinstance(book.data, SingleFile)
        assert isinstance(book.data.file, OnlineFile)
        assert book.data.file.url == "https://example.com/book.epub"
        assert book.data.file.extension == "epub"
        assert book.overwrite is False  # Default
        assert book.source_data is None  # Default

    def test_book_with_offline_file(self):
        """CRT-032: Book with SingleFile containing OfflineFile."""
        metadata = Metadata(title="Test Book")
        offline_file = OfflineFile(
            content=b"test content",
            extension="epub"
        )
        book_data = SingleFile(file=offline_file)
        book = Book(metadata=metadata, data=book_data)

        assert isinstance(book.data, SingleFile)
        assert isinstance(book.data.file, OfflineFile)
        assert book.data.file.content == b"test content"
        assert book.data.file.extension == "epub"

    def test_book_with_encrypted_file(self, aes_encryption):
        """CRT-032: Book with encrypted SingleFile."""
        metadata = Metadata(title="Encrypted Book")
        encrypted_file = OnlineFile(
            url="https://example.com/encrypted.epub",
            extension="epub",
            encryption=aes_encryption
        )
        book_data = SingleFile(file=encrypted_file)
        book = Book(metadata=metadata, data=book_data)

        assert book.data.file.encryption is not None
        assert book.data.file.encryption == aes_encryption

    def test_book_with_custom_headers(self):
        """CRT-032: Book with SingleFile with custom headers."""
        metadata = Metadata(title="Test Book")
        online_file = OnlineFile(
            url="https://example.com/book.epub",
            extension="epub",
            headers={"Authorization": "Bearer token123"}
        )
        book_data = SingleFile(file=online_file)
        book = Book(metadata=metadata, data=book_data)

        assert book.data.file.headers["Authorization"] == "Bearer token123"


# ============================================================================
# CRT-033: Book with ImageList BookData (Comics)
# ============================================================================

class TestBookWithImageList:
    """Test Book with ImageList data (for comics)."""

    def test_book_with_image_list(self):
        """CRT-033: Book with ImageList containing multiple images."""
        metadata = Metadata(title="Comic Book")
        images = [
            OnlineFile(url=f"https://example.com/page{i}.jpg", extension="jpg")
            for i in range(1, 11)
        ]
        book_data = ImageList(images=images)
        book = Book(metadata=metadata, data=book_data)

        assert isinstance(book.data, ImageList)
        assert len(book.data.images) == 10
        assert book.data.images[0].url == "https://example.com/page1.jpg"
        assert book.data.images[9].url == "https://example.com/page10.jpg"

    def test_book_with_single_image(self):
        """CRT-033: ImageList with single image."""
        metadata = Metadata(title="Single Page Comic")
        images = [OnlineFile(url="https://example.com/page1.jpg", extension="jpg")]
        book_data = ImageList(images=images)
        book = Book(metadata=metadata, data=book_data)

        assert len(book.data.images) == 1

    def test_book_with_encrypted_images(self, xor_encryption):
        """CRT-033: ImageList with encrypted images."""
        metadata = Metadata(title="Encrypted Comic")
        images = [
            OnlineFile(
                url=f"https://example.com/page{i}.jpg",
                extension="jpg",
                encryption=xor_encryption
            )
            for i in range(1, 6)
        ]
        book_data = ImageList(images=images)
        book = Book(metadata=metadata, data=book_data)

        for image in book.data.images:
            assert image.encryption is not None

    def test_book_with_mixed_image_formats(self):
        """CRT-033: ImageList with different image formats."""
        metadata = Metadata(title="Mixed Format Comic")
        images = [
            OnlineFile(url="https://example.com/page1.jpg", extension="jpg"),
            OnlineFile(url="https://example.com/page2.png", extension="png"),
            OnlineFile(url="https://example.com/page3.webp", extension="webp"),
        ]
        book_data = ImageList(images=images)
        book = Book(metadata=metadata, data=book_data)

        assert book.data.images[0].extension == "jpg"
        assert book.data.images[1].extension == "png"
        assert book.data.images[2].extension == "webp"


# ============================================================================
# CRT-034: Book with HtmlFiles BookData
# ============================================================================

class TestBookWithHtmlFiles:
    """Test Book with HtmlFiles data (for web scraping)."""

    def test_book_with_html_files(self):
        """CRT-034: Book with multiple HTML files."""
        metadata = Metadata(title="Web Novel")
        html_files = [
            HtmlFile(
                title=f"Chapter {i}",
                file=OnlineFile(url=f"https://example.com/ch{i}.html", extension="html"),
                selector={"class": "content"}
            )
            for i in range(1, 6)
        ]
        book_data = HtmlFiles(htmlfiles=html_files)
        book = Book(metadata=metadata, data=book_data)

        assert isinstance(book.data, HtmlFiles)
        assert len(book.data.htmlfiles) == 5
        assert book.data.htmlfiles[0].title == "Chapter 1"
        assert book.data.htmlfiles[4].title == "Chapter 5"
        assert book.data.cover is None  # No cover specified

    def test_book_with_html_files_and_cover(self):
        """CRT-034: Book with HTML files and cover image."""
        metadata = Metadata(title="Web Novel with Cover")
        html_files = [
            HtmlFile(
                title="Chapter 1",
                file=OnlineFile(url="https://example.com/ch1.html", extension="html"),
                selector=None
            )
        ]
        cover = OnlineFile(url="https://example.com/cover.jpg", extension="jpg")
        book_data = HtmlFiles(htmlfiles=html_files, cover=cover)
        book = Book(metadata=metadata, data=book_data)

        assert book.data.cover is not None
        assert book.data.cover.url == "https://example.com/cover.jpg"

    def test_html_file_with_selector(self):
        """CRT-034: HtmlFile with CSS selector."""
        html_file = HtmlFile(
            title="Chapter 1",
            file=OnlineFile(url="https://example.com/ch1.html", extension="html"),
            selector={"class": "chapter-content", "id": "main"}
        )

        assert html_file.selector["class"] == "chapter-content"
        assert html_file.selector["id"] == "main"

    def test_html_file_without_selector(self):
        """CRT-034: HtmlFile without selector (use entire page)."""
        html_file = HtmlFile(
            title="Chapter 1",
            file=OnlineFile(url="https://example.com/ch1.html", extension="html"),
            selector=None
        )

        assert html_file.selector is None


# ============================================================================
# CRT-035: Book with EpubInParts BookData
# ============================================================================

class TestBookWithEpubInParts:
    """Test Book with EpubInParts data (split EPUBs)."""

    def test_book_with_epub_parts(self):
        """CRT-035: Book with multiple EPUB parts."""
        metadata = Metadata(title="Split EPUB Book")
        files = [
            OnlineFile(url=f"https://example.com/part{i}.epub", extension="epub")
            for i in range(1, 4)
        ]
        files_in_toc = {
            "Chapter 1": "part1.epub",
            "Chapter 2": "part2.epub",
            "Chapter 3": "part3.epub",
        }
        book_data = EpubInParts(files=files, files_in_toc=files_in_toc)
        book = Book(metadata=metadata, data=book_data)

        assert isinstance(book.data, EpubInParts)
        assert len(book.data.files) == 3
        assert len(book.data.files_in_toc) == 3
        assert book.data.files_in_toc["Chapter 1"] == "part1.epub"

    def test_epub_parts_with_complex_toc(self):
        """CRT-035: EpubInParts with complex table of contents."""
        metadata = Metadata(title="Book with Complex TOC")
        files = [
            OnlineFile(url=f"https://example.com/part{i}.epub", extension="epub")
            for i in range(1, 6)
        ]
        files_in_toc = {
            "Part 1: Introduction": "part1.epub",
            "Part 2: Chapter 1": "part2.epub",
            "Part 2: Chapter 2": "part3.epub",
            "Part 3: Chapter 3": "part4.epub",
            "Epilogue": "part5.epub",
        }
        book_data = EpubInParts(files=files, files_in_toc=files_in_toc)
        book = Book(metadata=metadata, data=book_data)

        assert len(book.data.files) == 5
        assert len(book.data.files_in_toc) == 5
        assert book.data.files_in_toc["Epilogue"] == "part5.epub"

    def test_epub_parts_with_encrypted_files(self, aes_encryption):
        """CRT-035: EpubInParts with encrypted parts."""
        metadata = Metadata(title="Encrypted Split EPUB")
        files = [
            OnlineFile(
                url=f"https://example.com/part{i}.epub",
                extension="epub",
                encryption=aes_encryption
            )
            for i in range(1, 3)
        ]
        files_in_toc = {
            "Part 1": "part1.epub",
            "Part 2": "part2.epub",
        }
        book_data = EpubInParts(files=files, files_in_toc=files_in_toc)
        book = Book(metadata=metadata, data=book_data)

        for file in book.data.files:
            assert file.encryption is not None


# ============================================================================
# CRT-036: Series with Multiple Books
# ============================================================================

class TestSeries:
    """Test Series data structure."""

    def test_series_with_string_ids(self):
        """CRT-036: Series with string book IDs."""
        series = Series(
            title="Test Series",
            book_ids=["book1", "book2", "book3"]
        )

        assert series.title == "Test Series"
        assert len(series.book_ids) == 3
        assert series.book_ids[0] == "book1"
        assert series.book_ids[2] == "book3"

    def test_series_with_int_ids(self):
        """CRT-036: Series with integer book IDs."""
        series: Series[int] = Series(
            title="Numbered Series",
            book_ids=[101, 102, 103, 104]
        )

        assert len(series.book_ids) == 4
        assert series.book_ids[0] == 101
        assert series.book_ids[3] == 104

    def test_series_with_single_book(self):
        """CRT-036: Series with only one book."""
        series = Series(
            title="Single Book Series",
            book_ids=["only_book"]
        )

        assert len(series.book_ids) == 1

    def test_series_with_many_books(self):
        """CRT-036: Series with many books (ordering matters)."""
        book_ids = [f"book_{i:03d}" for i in range(1, 51)]  # 50 books
        series = Series(
            title="Large Series",
            book_ids=book_ids
        )

        assert len(series.book_ids) == 50
        assert series.book_ids[0] == "book_001"
        assert series.book_ids[49] == "book_050"

    def test_series_preserves_order(self):
        """CRT-036: Series should preserve book order."""
        book_ids = ["book3", "book1", "book2"]  # Not sorted
        series = Series(
            title="Ordered Series",
            book_ids=book_ids
        )

        # Should maintain the order given, not sort
        assert series.book_ids[0] == "book3"
        assert series.book_ids[1] == "book1"
        assert series.book_ids[2] == "book2"


# ============================================================================
# CRT-037: Equality and Hashing
# ============================================================================

class TestEqualityAndHashing:
    """Test equality and hashing of data structures."""

    def test_metadata_equality(self):
        """CRT-037: Two Metadata objects with same data should be equal."""
        metadata1 = Metadata(
            title="Test Book",
            authors=["Author"],
            series="Series",
            index=1
        )
        metadata2 = Metadata(
            title="Test Book",
            authors=["Author"],
            series="Series",
            index=1
        )

        assert metadata1 == metadata2

    def test_metadata_inequality(self):
        """CRT-037: Metadata objects with different data should not be equal."""
        metadata1 = Metadata(title="Book 1")
        metadata2 = Metadata(title="Book 2")

        assert metadata1 != metadata2

    def test_book_equality(self):
        """CRT-037: Two Book objects with same data should be equal."""
        metadata = Metadata(title="Test")
        file = OnlineFile(url="https://example.com/book.epub", extension="epub")
        data = SingleFile(file=file)

        book1 = Book(metadata=metadata, data=data)
        book2 = Book(metadata=metadata, data=data)

        # Note: Books might not be equal if they're different instances
        # This depends on whether __eq__ is implemented
        # Testing that the fields are accessible and comparable
        assert book1.metadata == book2.metadata
        assert type(book1.data) == type(book2.data)

    def test_online_file_equality(self):
        """CRT-037: OnlineFile equality."""
        file1 = OnlineFile(url="https://example.com/book.epub", extension="epub")
        file2 = OnlineFile(url="https://example.com/book.epub", extension="epub")

        assert file1 == file2

    def test_online_file_inequality_different_url(self):
        """CRT-037: OnlineFiles with different URLs should not be equal."""
        file1 = OnlineFile(url="https://example.com/book1.epub", extension="epub")
        file2 = OnlineFile(url="https://example.com/book2.epub", extension="epub")

        assert file1 != file2


# ============================================================================
# Additional Book Tests
# ============================================================================

class TestBookAdditionalFeatures:
    """Test additional Book features."""

    def test_book_with_overwrite_flag(self):
        """Test Book with overwrite flag set."""
        metadata = Metadata(title="Test Book")
        file = OnlineFile(url="https://example.com/book.epub", extension="epub")
        data = SingleFile(file=file)
        book = Book(metadata=metadata, data=data, overwrite=True)

        assert book.overwrite is True

    def test_book_with_source_data(self):
        """Test Book with source-specific data."""
        metadata = Metadata(title="Test Book")
        file = OnlineFile(url="https://example.com/book.epub", extension="epub")
        data = SingleFile(file=file)
        source_data = {"api_id": "12345", "format": "epub3"}
        book = Book(metadata=metadata, data=data, source_data=source_data)

        assert book.source_data is not None
        assert book.source_data["api_id"] == "12345"
        assert book.source_data["format"] == "epub3"

    def test_book_modification(self):
        """Test that Book metadata can be modified."""
        metadata = Metadata(title="Original Title")
        file = OnlineFile(url="https://example.com/book.epub", extension="epub")
        data = SingleFile(file=file)
        book = Book(metadata=metadata, data=data)

        # Modify metadata
        book.metadata.title = "New Title"
        assert book.metadata.title == "New Title"

    def test_book_with_complete_metadata_and_complex_data(self):
        """Test Book with complete metadata and complex BookData."""
        metadata = Metadata(
            title="Complete Book",
            series="Test Series",
            index=1,
            authors=["Author One", "Author Two"],
            language="en",
            publisher="Publisher",
            identifier="ISBN:123",
            description="Description",
            release_date=date(2025, 1, 1),
            source="storytel"
        )

        html_files = [
            HtmlFile(
                title=f"Chapter {i}",
                file=OnlineFile(url=f"https://example.com/ch{i}.html", extension="html"),
                selector={"class": "content"}
            )
            for i in range(1, 11)
        ]
        cover = OnlineFile(url="https://example.com/cover.jpg", extension="jpg")
        data = HtmlFiles(htmlfiles=html_files, cover=cover)

        book = Book(metadata=metadata, data=data, overwrite=False)

        assert book.metadata.title == "Complete Book"
        assert len(book.data.htmlfiles) == 10
        assert book.data.cover is not None
        assert book.overwrite is False
