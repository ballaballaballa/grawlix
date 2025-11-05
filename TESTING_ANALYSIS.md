# Grawlix Testing Analysis and Test Case Recommendations

**Generated:** 2025-11-05
**Current Test Coverage:** None (0%)
**Total Lines of Code:** ~2,367 LOC

---

## Executive Summary

Grawlix is a CLI tool for downloading ebooks from 12 different online services with support for multiple output formats (EPUB, CBZ, ACSM). The codebase is well-structured with clear separation of concerns but currently has **no automated tests**.

This document provides a comprehensive testing strategy with **prioritized test cases** ranging from critical to low priority, organized by module and functionality.

---

## Table of Contents

1. [Current State](#current-state)
2. [Testing Infrastructure Recommendations](#testing-infrastructure-recommendations)
3. [Test Cases by Priority](#test-cases-by-priority)
   - [Critical Priority](#critical-priority)
   - [High Priority](#high-priority)
   - [Medium Priority](#medium-priority)
   - [Low Priority](#low-priority)
4. [Testing Strategy](#testing-strategy)
5. [Appendix: Test Coverage Goals](#appendix-test-coverage-goals)

---

## Current State

### What Exists
- Clean, modular architecture
- Type hints throughout codebase
- Async/await patterns for I/O operations
- Protocol-based design (encryption)
- Data classes for models

### What's Missing
- ❌ No test directory
- ❌ No test files
- ❌ No test framework configuration (pytest/unittest)
- ❌ No CI/CD pipeline
- ❌ No mocking infrastructure
- ❌ No test fixtures or sample data

### Risk Assessment
**HIGH RISK**: Without tests, the following scenarios are not validated:
- File path sanitization across Windows/macOS/Linux
- Encryption/decryption correctness
- Metadata preservation during EPUB generation
- Error handling for network failures
- Configuration parsing edge cases
- Source URL pattern matching

---

## Testing Infrastructure Recommendations

### Framework Setup
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock pytest-cov httpx-mock
```

### Recommended Project Structure
```
grawlix/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── test_book.py
│   │   ├── test_config.py
│   │   ├── test_encryption.py
│   │   ├── test_utils.py
│   │   ├── test_arguments.py
│   │   ├── output/
│   │   │   ├── test_output_format.py
│   │   │   ├── test_epub.py
│   │   │   ├── test_cbz.py
│   │   │   └── test_acsm.py
│   │   └── sources/
│   │       ├── test_source_base.py
│   │       ├── test_storytel.py
│   │       ├── test_nextory.py
│   │       └── ... (other sources)
│   ├── integration/
│   │   ├── test_download_workflow.py
│   │   ├── test_metadata_writing.py
│   │   └── test_series_download.py
│   └── fixtures/
│       ├── sample_epub/
│       ├── sample_api_responses/
│       └── test_configs/
└── pyproject.toml               # Add [tool.pytest.ini_options]
```

### Configuration
Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--cov=grawlix",
    "--cov-report=html",
    "--cov-report=term-missing",
]
```

---

## Test Cases by Priority

---

## CRITICAL PRIORITY

> **Definition**: Core functionality that could cause data loss, security issues, or complete application failure. Must be tested before any release.

### 1. Output Path Sanitization (Module: `output/output_format.py`)

**Risk**: Malicious or malformed metadata could create files outside intended directory, overwrite system files, or cause crashes on Windows/macOS/Linux.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-001** | Test Windows reserved filenames (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) are sanitized | Windows crashes if these are used as filenames |
| **CRT-002** | Test path traversal prevention (`../../../etc/passwd` in title) | Security: prevents writing outside output directory |
| **CRT-003** | Test forbidden characters in filenames (`< > : " / \ | ? *` on Windows, `/` on Unix) | OS compatibility: prevents file creation failures |
| **CRT-004** | Test filename length limits (255 bytes on most filesystems) | Prevents filesystem errors on long titles |
| **CRT-005** | Test template variable substitution (`{title}`, `{authors}`, `{series}`, `{index}`, `{isbn}`, `{language}`) | Core feature: incorrect paths = lost files |
| **CRT-006** | Test handling of `None` values in template variables | Prevents crashes when metadata is incomplete |
| **CRT-007** | Test absolute vs relative path handling in output location | Ensures files go to expected directory |
| **CRT-008** | Test duplicate filename collision handling | Prevents overwriting existing files unless `--overwrite` |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 1)
**Estimated Test Count**: 15-20 unit tests
**Code Location**: `grawlix/output/output_format.py:60-80` (`format_output_location()`)

---

### 2. Encryption/Decryption Correctness (Module: `encryption.py`)

**Risk**: Incorrect decryption corrupts ebook files, making them unreadable.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-010** | Test AES CBC decryption with known plaintext/ciphertext pairs | Validates core decryption algorithm |
| **CRT-011** | Test AES CTR decryption with nonce handling | CTR mode failures corrupt entire file |
| **CRT-012** | Test XOR decryption with various key lengths | Simple but critical for some sources |
| **CRT-013** | Test PKCS7 padding removal in AES CBC | Incorrect padding breaks file parsing |
| **CRT-014** | Test decryption of empty data / single block / multi-block | Edge cases in block cipher modes |
| **CRT-015** | Test decryption with incorrect key (should fail gracefully) | Error handling validation |
| **CRT-016** | Test type safety of `SupportsDecrypt` protocol | Ensures interface contracts |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 1)
**Estimated Test Count**: 12-15 unit tests
**Code Location**: `grawlix/encryption.py:1-57`

---

### 3. Configuration Parsing (Module: `config.py`)

**Risk**: Malformed config files could expose credentials, crash app, or cause authentication failures.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-020** | Test valid TOML config with all sources configured | Happy path validation |
| **CRT-021** | Test malformed TOML syntax (invalid UTF-8, syntax errors) | Prevents crashes on user config errors |
| **CRT-022** | Test missing config file (should return empty config) | Graceful degradation |
| **CRT-023** | Test config with missing required fields (e.g., source credentials) | Validates fallback to CLI/prompt |
| **CRT-024** | Test config with invalid source names | Error handling for typos |
| **CRT-025** | Test config file path resolution across platforms (Windows/Linux/macOS) | Uses `platformdirs` correctly |
| **CRT-026** | Test default output path handling when not specified | Prevents writing to CWD unexpectedly |
| **CRT-027** | Test metadata writing configuration (`write_metadata` flag) | Feature enablement |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 1)
**Estimated Test Count**: 10-12 unit tests
**Code Location**: `grawlix/config.py:1-60`

---

### 4. Book Data Model Validation (Module: `book.py`)

**Risk**: Invalid data models could propagate through pipeline causing failures in output generation.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-030** | Test `Metadata` construction with all fields populated | Validates data structure |
| **CRT-031** | Test `Metadata` with minimal fields (only title) | Ensures optional fields work |
| **CRT-032** | Test `Book` with `SingleFile` BookData type | Most common path |
| **CRT-033** | Test `Book` with `ImageList` BookData (for comics) | CBZ generation dependency |
| **CRT-034** | Test `Book` with `HtmlFiles` BookData (for web scraping) | EPUB from HTML dependency |
| **CRT-035** | Test `Book` with `EpubInParts` BookData (for split EPUBs) | EPUB merging dependency |
| **CRT-036** | Test `Series` with multiple books and correct ordering | Series download correctness |
| **CRT-037** | Test equality and hashing of `Metadata` objects | Deduplication logic |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 1)
**Estimated Test Count**: 10-12 unit tests
**Code Location**: `grawlix/book.py:1-116`

---

### 5. Source URL Pattern Matching (Module: `sources/source.py` + implementations)

**Risk**: Incorrect source selection downloads wrong content or fails silently.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-040** | Test URL pattern matching for all 12 sources | Core routing logic |
| **CRT-041** | Test `load_source()` returns correct Source subclass for each URL | Factory pattern validation |
| **CRT-042** | Test handling of invalid/unknown URLs | Error handling |
| **CRT-043** | Test URL parsing with query parameters and fragments | Real-world URL variations |
| **CRT-044** | Test URL normalization (http→https, trailing slashes) | Prevents duplicate source logic |
| **CRT-045** | Test source caching (same source not instantiated twice) | Performance optimization validation |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 2)
**Estimated Test Count**: 18-20 unit tests (12 sources + edge cases)
**Code Location**: `grawlix/__main__.py:67-79` + `grawlix/sources/*.py` (pattern class attributes)

---

### 6. EPUB Generation (Module: `output/epub.py`)

**Risk**: Corrupted EPUB files are unusable in e-readers.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-050** | Test EPUB from `SingleFile` (direct download) | Most common path |
| **CRT-051** | Test EPUB from `HtmlFiles` (EbookLib generation) | Web scraping path |
| **CRT-052** | Test EPUB from `EpubInParts` (merging multiple EPUBs) | Complex merge logic |
| **CRT-053** | Test EPUB validation with `epubcheck` (if available) | Standards compliance |
| **CRT-054** | Test EPUB with missing metadata fields | Graceful degradation |
| **CRT-055** | Test EPUB chapter ordering from HTML files | Content correctness |
| **CRT-056** | Test EPUB metadata preservation when merging parts | Metadata integrity |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 2)
**Estimated Test Count**: 12-15 integration tests
**Code Location**: `grawlix/output/epub.py:1-137`

---

### 7. File Download with Decryption (Module: `output/output_format.py`)

**Risk**: Failed downloads or decryption leave partial/corrupted files.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **CRT-060** | Test file download with valid URL | Happy path |
| **CRT-061** | Test file download with encryption (AES CBC) | Decryption integration |
| **CRT-062** | Test file download with encryption (AES CTR) | Decryption integration |
| **CRT-063** | Test file download network failure handling (timeout, 404, 500) | Error resilience |
| **CRT-064** | Test partial download resume (if supported) | Data loss prevention |
| **CRT-065** | Test concurrent file downloads (async behavior) | Performance and correctness |
| **CRT-066** | Test download progress tracking | User feedback validation |

**Implementation Priority**: 🔴 **IMMEDIATE** (Week 2)
**Estimated Test Count**: 10-12 integration tests (using httpx-mock)
**Code Location**: `grawlix/output/output_format.py:82-97`

---

## HIGH PRIORITY

> **Definition**: Important features frequently used by end-users. Bugs here significantly impact user experience but don't cause data loss.

### 8. CLI Argument Parsing (Module: `arguments.py`)

**Risk**: Incorrect argument handling prevents users from running the tool.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-001** | Test all CLI flags parse correctly (`--output`, `--format`, `--login`, etc.) | User interface validation |
| **HGH-002** | Test mutually exclusive arguments (if any) | UX: prevents invalid combinations |
| **HGH-003** | Test default values when arguments omitted | Expected behavior |
| **HGH-004** | Test URL parsing from stdin vs file vs arguments | Multiple input methods |
| **HGH-005** | Test `--overwrite` flag behavior | File handling control |
| **HGH-006** | Test `--write-metadata` flag | Feature toggle |
| **HGH-007** | Test invalid argument combinations | Error messaging |

**Implementation Priority**: 🟡 **HIGH** (Week 3)
**Estimated Test Count**: 12-15 unit tests
**Code Location**: `grawlix/arguments.py:1-75`

---

### 9. Metadata Transformation (Module: `epub_metadata_writers.py`)

**Risk**: Incorrect transformations lose author info, series data, or other important metadata.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-010** | Test Storytel API response → standardized metadata | Source-specific transformation |
| **HGH-011** | Test Nextory API response → standardized metadata | Source-specific transformation |
| **HGH-012** | Test handling of missing fields in API responses | Graceful degradation |
| **HGH-013** | Test multi-author parsing and joining | Common metadata case |
| **HGH-014** | Test series name and index extraction | Series organization |
| **HGH-015** | Test ISBN normalization (ISBN-10 vs ISBN-13) | Metadata standardization |
| **HGH-016** | Test category/genre mapping | Metadata enrichment |
| **HGH-017** | Test date parsing from various formats | API variation handling |

**Implementation Priority**: 🟡 **HIGH** (Week 3)
**Estimated Test Count**: 15-18 unit tests
**Code Location**: `grawlix/epub_metadata_writers.py:1-117`

---

### 10. EPUB Metadata Writing (Module: `epub_metadata.py`)

**Risk**: Metadata writes could corrupt existing EPUB files.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-020** | Test metadata write to valid EPUB (OPF modification) | Core feature |
| **HGH-021** | Test metadata write preserves existing content | Data preservation |
| **HGH-022** | Test metadata write with all fields populated | Full coverage |
| **HGH-023** | Test metadata write with minimal fields | Edge case |
| **HGH-024** | Test handling of malformed OPF XML | Error resilience |
| **HGH-025** | Test EPUB re-zipping after metadata write | File integrity |
| **HGH-026** | Test metadata write to EPUB with existing metadata | Merge vs overwrite logic |

**Implementation Priority**: 🟡 **HIGH** (Week 3)
**Estimated Test Count**: 10-12 integration tests
**Code Location**: `grawlix/epub_metadata.py:1-~200`

---

### 11. CBZ Generation (Module: `output/cbz.py`)

**Risk**: Comic downloads fail or have incorrect page ordering.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-030** | Test CBZ from `ImageList` with correct page ordering | Core feature |
| **HGH-031** | Test CBZ with ComicInfo.xml metadata generation | Comic reader compatibility |
| **HGH-032** | Test image download and inclusion in zip | Content integrity |
| **HGH-033** | Test handling of encrypted images | Decryption integration |
| **HGH-034** | Test CBZ with missing images (network failure) | Error handling |
| **HGH-035** | Test CBZ filename sanitization (same as EPUB) | Consistency |

**Implementation Priority**: 🟡 **HIGH** (Week 4)
**Estimated Test Count**: 8-10 integration tests
**Code Location**: `grawlix/output/cbz.py:1-35`

---

### 12. Utility Functions (Module: `utils/__init__.py`)

**Risk**: Utility bugs propagate to multiple modules.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-040** | Test Levenshtein distance calculation for known pairs | Algorithm correctness |
| **HGH-041** | Test Levenshtein distance edge cases (empty strings, identical strings) | Edge case handling |
| **HGH-042** | Test URL parsing and validation | Data validation |
| **HGH-043** | Test asset loading from package resources | Resource management |
| **HGH-044** | Test filename sanitization helper (if exists) | Cross-cutting concern |

**Implementation Priority**: 🟡 **HIGH** (Week 4)
**Estimated Test Count**: 8-10 unit tests
**Code Location**: `grawlix/utils/__init__.py:1-52`

---

### 13. Source Authentication (Module: `sources/source.py` + implementations)

**Risk**: Authentication failures prevent downloads entirely.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **HGH-050** | Test login flow with valid credentials (mocked) | Happy path |
| **HGH-051** | Test login flow with invalid credentials (should fail) | Error handling |
| **HGH-052** | Test cookie-based authentication | Alternative auth method |
| **HGH-053** | Test cookie loading from file | File I/O integration |
| **HGH-054** | Test missing cookies.txt file handling | Graceful degradation |
| **HGH-055** | Test authentication caching (not re-authenticating per download) | Performance |
| **HGH-056** | Test session persistence across requests | HTTP client state |

**Implementation Priority**: 🟡 **HIGH** (Week 4)
**Estimated Test Count**: 12-15 integration tests (using httpx-mock)
**Code Location**: `grawlix/sources/source.py:24-79`

---

## MEDIUM PRIORITY

> **Definition**: Supporting features, edge cases, and less frequently used code paths. Important for robustness but not blocking releases.

### 14. Series Download Workflow (Module: `__main__.py`)

**Risk**: Series downloads might download wrong books, skip books, or download duplicates.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-001** | Test series download with all books available | Happy path |
| **MED-002** | Test series download with partial failures (some books fail) | Resilience |
| **MED-003** | Test series download ordering (by index) | User expectation |
| **MED-004** | Test series download with duplicate book IDs | Deduplication |
| **MED-005** | Test series metadata propagation to individual books | Metadata consistency |

**Implementation Priority**: 🟢 **MEDIUM** (Week 5)
**Estimated Test Count**: 8-10 integration tests
**Code Location**: `grawlix/__main__.py:136-161`

---

### 15. Logging and Progress Tracking (Module: `logging.py`)

**Risk**: Poor logging hinders debugging; broken progress bars annoy users.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-010** | Test progress bar creation and updates | UX validation |
| **MED-011** | Test log level filtering (debug vs normal) | Feature validation |
| **MED-012** | Test Rich console output formatting | Visual regression |
| **MED-013** | Test logging to file (if supported) | Feature validation |
| **MED-014** | Test async task progress tracking | Concurrency correctness |

**Implementation Priority**: 🟢 **MEDIUM** (Week 5)
**Estimated Test Count**: 6-8 unit tests
**Code Location**: `grawlix/logging.py:1-82`

---

### 16. Individual Source Implementations (Module: `sources/*.py`)

**Risk**: Source-specific bugs prevent downloads from that service.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-020** | Test Storytel URL parsing and book ID extraction | Source-specific logic |
| **MED-021** | Test Nextory URL parsing and book ID extraction | Source-specific logic |
| **MED-022** | Test Marvel Unlimited URL patterns | Source-specific logic |
| **MED-023** | Test DC Universe Infinite URL patterns | Source-specific logic |
| **MED-024** | Test Internet Archive URL patterns | Source-specific logic |
| **MED-025** | Test Royal Road URL patterns | Source-specific logic |
| **MED-026** | Test FanFiction.net URL patterns | Source-specific logic |
| **MED-027** | Test Flipp URL patterns | Source-specific logic |
| **MED-028** | Test Saxo URL patterns | Source-specific logic |
| **MED-029** | Test eReolen URL patterns | Source-specific logic |
| **MED-030** | Test Webtoons URL patterns | Source-specific logic |
| **MED-031** | Test MangaPlus URL patterns | Source-specific logic |

**Implementation Priority**: 🟢 **MEDIUM** (Week 6-7)
**Estimated Test Count**: 50-60 unit tests (12 sources × 4-5 tests each)
**Code Location**: `grawlix/sources/*.py` (all 12 source files)

---

### 17. Error Handling and Custom Exceptions (Module: `exceptions.py`)

**Risk**: Poor error messages confuse users; unhandled exceptions crash the app.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-040** | Test custom exception messages are formatted correctly | UX validation |
| **MED-041** | Test exception context preservation (traceback) | Debugging aid |
| **MED-042** | Test error handling in main workflow (network, file I/O, parsing) | Integration testing |
| **MED-043** | Test graceful shutdown on KeyboardInterrupt | UX validation |

**Implementation Priority**: 🟢 **MEDIUM** (Week 7)
**Estimated Test Count**: 6-8 unit tests
**Code Location**: `grawlix/exceptions.py` + error handling throughout codebase

---

### 18. ACSM Passthrough (Module: `output/acsm.py`)

**Risk**: Low risk (simple passthrough) but worth validating.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-050** | Test ACSM file passthrough from `SingleFile` | Simplest output format |
| **MED-051** | Test ACSM filename sanitization | Consistency with other formats |
| **MED-052** | Test ACSM with missing file | Error handling |

**Implementation Priority**: 🟢 **MEDIUM** (Week 7)
**Estimated Test Count**: 3-5 unit tests
**Code Location**: `grawlix/output/acsm.py:1-23`

---

### 19. Configuration Override Precedence (Module: `config.py` + `arguments.py`)

**Risk**: Users confused about which settings take precedence.

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **MED-060** | Test CLI args override config file settings | Expected behavior |
| **MED-061** | Test config file overrides default values | Expected behavior |
| **MED-062** | Test interactive prompts when neither CLI nor config provided | UX validation |

**Implementation Priority**: 🟢 **MEDIUM** (Week 8)
**Estimated Test Count**: 5-6 integration tests
**Code Location**: `grawlix/__main__.py` + `grawlix/config.py` + `grawlix/arguments.py`

---

## LOW PRIORITY

> **Definition**: Nice-to-have tests for rare edge cases, performance validation, or non-critical features. Can be deferred to later releases.

### 20. Performance Testing

**Risk**: Low (functional correctness more important than performance for this tool).

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **LOW-001** | Test download speed benchmarks (baseline) | Performance regression detection |
| **LOW-002** | Test concurrent download limits (asyncio.Semaphore if used) | Resource management |
| **LOW-003** | Test memory usage with large EPUB files (100MB+) | Scalability validation |
| **LOW-004** | Test handling of thousands of images in CBZ | Scalability validation |

**Implementation Priority**: ⚪ **LOW** (Future)
**Estimated Test Count**: 4-6 benchmark tests
**Tools**: `pytest-benchmark`

---

### 21. Cross-Platform Compatibility

**Risk**: Medium (but can be tested manually initially).

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **LOW-010** | Test path handling on Windows (backslashes, drive letters) | Platform compatibility |
| **LOW-011** | Test path handling on macOS (HFS+ vs APFS) | Platform compatibility |
| **LOW-012** | Test path handling on Linux (case sensitivity) | Platform compatibility |
| **LOW-013** | Test Unicode filenames across platforms | I18n validation |

**Implementation Priority**: ⚪ **LOW** (Future)
**Estimated Test Count**: 8-10 integration tests
**Tools**: CI runners for Windows/macOS/Linux

---

### 22. Property-Based Testing

**Risk**: Low (comprehensive but time-consuming to implement).

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **LOW-020** | Property test: filename sanitization never produces invalid filenames | Exhaustive edge case testing |
| **LOW-021** | Property test: encryption/decryption round-trip is identity | Cryptographic correctness |
| **LOW-022** | Property test: path template expansion never produces absolute paths from relative templates | Security validation |

**Implementation Priority**: ⚪ **LOW** (Future)
**Estimated Test Count**: 5-8 property tests
**Tools**: `hypothesis`

---

### 23. Regression Tests for Past Bugs

**Risk**: Low (no known bugs to regress yet).

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **LOW-030** | Add regression test for each future bug fix | Prevent re-introduction |

**Implementation Priority**: ⚪ **LOW** (Ongoing)
**Estimated Test Count**: Variable (add as bugs are discovered)

---

### 24. Documentation Testing

**Risk**: Low (but improves maintainability).

| Test ID | Test Case | Rationale |
|---------|-----------|-----------|
| **LOW-040** | Test all README examples execute without errors | Documentation accuracy |
| **LOW-041** | Test CLI `--help` output contains all documented flags | Help text validation |

**Implementation Priority**: ⚪ **LOW** (Future)
**Estimated Test Count**: 3-5 integration tests

---

## Testing Strategy

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Test critical pure functions and data structures.

1. Set up pytest infrastructure (conftest.py, fixtures)
2. Implement **Critical Priority** tests (CRT-001 to CRT-067)
   - Focus: Path sanitization, encryption, config, data models, URL routing, EPUB/CBZ generation
3. Target: **40-50% code coverage**

**Deliverables**:
- ~100 unit tests
- CI pipeline (GitHub Actions)
- Test fixtures for sample books/EPUBs

---

### Phase 2: Integration (Weeks 3-4)
**Goal**: Test high-priority workflows and transformations.

1. Implement **High Priority** tests (HGH-001 to HGH-056)
   - Focus: CLI args, metadata transformations, authentication, CBZ generation
2. Set up httpx-mock for HTTP testing
3. Target: **60-70% code coverage**

**Deliverables**:
- ~120 additional tests
- Mocked HTTP fixtures for source APIs
- Integration test suite

---

### Phase 3: Source-Specific (Weeks 5-7)
**Goal**: Test individual source implementations.

1. Implement **Medium Priority** tests (MED-001 to MED-062)
   - Focus: Series downloads, logging, 12 source implementations, error handling
2. Target: **75-85% code coverage**

**Deliverables**:
- ~100 additional tests
- Source-specific test fixtures (mocked API responses)

---

### Phase 4: Polish (Week 8+)
**Goal**: Edge cases and optional enhancements.

1. Implement **Low Priority** tests (LOW-001 to LOW-041)
   - Focus: Performance, cross-platform, property-based testing
2. Target: **85-90% code coverage**

**Deliverables**:
- ~30 additional tests
- Performance benchmarks
- Cross-platform CI runners

---

## Appendix: Test Coverage Goals

### Minimum Viable Coverage (Phase 1)
```
Module                          Target Coverage
────────────────────────────────────────────────
grawlix/book.py                 100%  (critical)
grawlix/encryption.py           100%  (critical)
grawlix/config.py               90%   (critical)
grawlix/output/output_format.py 85%   (critical)
grawlix/output/epub.py          80%   (critical)
grawlix/sources/source.py       75%   (critical)
────────────────────────────────────────────────
Overall                         40-50%
```

### Full Coverage Goals (Phase 4)
```
Module                          Target Coverage
────────────────────────────────────────────────
grawlix/book.py                 100%
grawlix/encryption.py           100%
grawlix/utils/__init__.py       100%
grawlix/config.py               95%
grawlix/arguments.py            95%
grawlix/output/*.py             90%
grawlix/sources/*.py            85%  (excluding API mocks)
grawlix/__main__.py             80%  (excluding interactive prompts)
grawlix/logging.py              70%  (visual output hard to test)
────────────────────────────────────────────────
Overall                         85-90%
```

---

## Recommended Test Fixtures

### Minimal Set (Phase 1)
```
tests/fixtures/
├── sample_epub/
│   └── minimal_valid.epub         # Valid EPUB for metadata writing tests
├── sample_api_responses/
│   ├── storytel_book.json         # Sample Storytel API response
│   └── nextory_book.json          # Sample Nextory API response
├── test_configs/
│   ├── valid_config.toml          # Complete config
│   └── minimal_config.toml        # Empty config
└── test_images/
    ├── page1.jpg                   # For CBZ tests
    └── page2.jpg
```

### Full Set (Phase 3)
Add API response fixtures for all 12 sources, sample CBZ files, encrypted files, etc.

---

## Success Metrics

### Quantitative
- ✅ **350+ tests** implemented across all phases
- ✅ **85-90% code coverage** (excluding external API calls)
- ✅ **0 critical bugs** in path sanitization, encryption, or EPUB generation
- ✅ **CI passing** on Windows, macOS, Linux

### Qualitative
- ✅ Developers confident making changes without breaking existing functionality
- ✅ New contributors can understand expected behavior from tests
- ✅ Regression bugs caught before release
- ✅ Code refactoring enabled by safety net of tests

---

## Notes

1. **Mocking Strategy**: Use `httpx-mock` for HTTP requests to external APIs. Do NOT make real network calls in tests.

2. **Async Testing**: All async functions must use `pytest-asyncio` with `@pytest.mark.asyncio`.

3. **Fixtures**: Create reusable fixtures in `conftest.py` for:
   - Sample `Metadata` objects
   - Sample `Book` objects with different `BookData` types
   - Mocked `httpx.AsyncClient` instances
   - Temporary directories for file I/O tests

4. **Parameterized Tests**: Use `@pytest.mark.parametrize` for testing multiple inputs (e.g., all 12 sources, all forbidden characters).

5. **Snapshot Testing**: Consider `pytest-snapshot` for testing complex output like EPUB structure or ComicInfo.xml.

6. **Test Data**: Keep test EPUBs small (<10KB) and use public domain content to avoid licensing issues.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-05
**Maintainer**: Development Team
