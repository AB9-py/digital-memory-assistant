"""
test_validator.py

Tests for FileValidator and FileHandler.

We use pytest's `tmp_path` fixture, which gives each test function a
fresh, automatically-cleaned-up temporary directory. This means our
tests don't depend on (or pollute) the real sample_files/ folder, and
each test is fully isolated from the others.

Run with:
    pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

# Allow tests to import the `ingestion` package from the project root
# when pytest is run from the project's top-level directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.config import MAX_FILE_SIZE_BYTES
from ingestion.exceptions import (
    FileNotFoundInIngestionError,
    UnsupportedFileTypeError,
    FileSizeLimitExceededError,
    CorruptedFileError,
    EmptyFileError,
)
from ingestion.file_handler import FileHandler
from ingestion.models import ProcessingStatus
from ingestion.validator import FileValidator, PDF_SIGNATURE, PNG_SIGNATURE, JPEG_SIGNATURE


# ---------------------------------------------------------------------
# Fixtures: build minimal-but-genuine files for each supported type.
# We only need correct MAGIC BYTES at the start of the file -- the
# validator only inspects the header, so these don't need to be fully
# "real" documents to exercise the code honestly.
# ---------------------------------------------------------------------

@pytest.fixture
def valid_pdf(tmp_path) -> Path:
    path = tmp_path / "notes.pdf"
    path.write_bytes(PDF_SIGNATURE + b"1.4\n%%EOF")
    return path


@pytest.fixture
def valid_png(tmp_path) -> Path:
    path = tmp_path / "screenshot.png"
    path.write_bytes(PNG_SIGNATURE + b"\x00" * 20)
    return path


@pytest.fixture
def valid_jpg(tmp_path) -> Path:
    path = tmp_path / "photo.jpg"
    path.write_bytes(JPEG_SIGNATURE + b"\x00" * 20)
    return path


@pytest.fixture
def valid_txt(tmp_path) -> Path:
    path = tmp_path / "notes.txt"
    path.write_text("These are my plain text notes.", encoding="utf-8")
    return path


# ---------------------------------------------------------------------
# 1. Valid PDF
# ---------------------------------------------------------------------
def test_valid_pdf_is_accepted(valid_pdf):
    handler = FileHandler()
    result = handler.ingest_file(str(valid_pdf))

    assert result.success is True
    assert result.metadata.detected_file_type == "PDF"
    assert result.metadata.processing_status == ProcessingStatus.VALIDATED
    assert result.metadata.file_size_bytes > 0
    # file_id should be a valid-looking UUID string (36 chars with dashes)
    assert len(result.metadata.file_id) == 36


# ---------------------------------------------------------------------
# 2. Valid PNG / JPG
# ---------------------------------------------------------------------
def test_valid_png_is_accepted(valid_png):
    handler = FileHandler()
    result = handler.ingest_file(str(valid_png))

    assert result.success is True
    assert result.metadata.detected_file_type == "IMAGE"
    assert result.metadata.processing_status == ProcessingStatus.VALIDATED


def test_valid_jpg_is_accepted(valid_jpg):
    handler = FileHandler()
    result = handler.ingest_file(str(valid_jpg))

    assert result.success is True
    assert result.metadata.detected_file_type == "IMAGE"
    assert result.metadata.processing_status == ProcessingStatus.VALIDATED


# ---------------------------------------------------------------------
# 3. Valid TXT
# ---------------------------------------------------------------------
def test_valid_txt_is_accepted(valid_txt):
    handler = FileHandler()
    result = handler.ingest_file(str(valid_txt))

    assert result.success is True
    assert result.metadata.detected_file_type == "TEXT"
    assert result.metadata.processing_status == ProcessingStatus.VALIDATED


# ---------------------------------------------------------------------
# 4. Unsupported extension
# ---------------------------------------------------------------------
def test_unsupported_extension_is_rejected(tmp_path):
    path = tmp_path / "archive.docx"
    path.write_bytes(b"irrelevant content")

    handler = FileHandler()
    result = handler.ingest_file(str(path))

    assert result.success is False
    assert result.metadata.processing_status == ProcessingStatus.REJECTED
    assert "Unsupported file extension" in result.error_message


def test_validator_raises_specific_exception_for_bad_extension(tmp_path):
    """Directly test the validator layer, not just the handler wrapper."""
    path = tmp_path / "archive.docx"
    path.write_bytes(b"irrelevant content")

    validator = FileValidator()
    with pytest.raises(UnsupportedFileTypeError):
        validator.validate(path)


# ---------------------------------------------------------------------
# 5. Missing file
# ---------------------------------------------------------------------
def test_missing_file_is_rejected(tmp_path):
    missing_path = tmp_path / "does_not_exist.pdf"

    handler = FileHandler()
    result = handler.ingest_file(str(missing_path))

    assert result.success is False
    assert result.metadata.processing_status == ProcessingStatus.REJECTED
    assert "No file found" in result.error_message


def test_validator_raises_specific_exception_for_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.pdf"

    validator = FileValidator()
    with pytest.raises(FileNotFoundInIngestionError):
        validator.validate(missing_path)


# ---------------------------------------------------------------------
# 6. File exceeding size limit
# ---------------------------------------------------------------------
def test_oversized_file_is_rejected(tmp_path):
    path = tmp_path / "huge_notes.txt"
    # Write one byte more than the configured maximum.
    oversized_content = b"a" * (MAX_FILE_SIZE_BYTES + 1)
    path.write_bytes(oversized_content)

    handler = FileHandler()
    result = handler.ingest_file(str(path))

    assert result.success is False
    assert result.metadata.processing_status == ProcessingStatus.REJECTED
    assert "exceeds" in result.error_message


def test_validator_raises_specific_exception_for_oversized_file(tmp_path):
    path = tmp_path / "huge_notes.txt"
    path.write_bytes(b"a" * (MAX_FILE_SIZE_BYTES + 1))

    validator = FileValidator()
    with pytest.raises(FileSizeLimitExceededError):
        validator.validate(path)


# ---------------------------------------------------------------------
# Bonus: corrupted / mismatched content detection
# ---------------------------------------------------------------------
def test_fake_pdf_with_wrong_content_is_rejected(tmp_path):
    """A file named .pdf but containing plain text should be caught."""
    path = tmp_path / "fake.pdf"
    path.write_bytes(b"This is not a real PDF file.")

    handler = FileHandler()
    result = handler.ingest_file(str(path))

    assert result.success is False
    assert result.metadata.processing_status == ProcessingStatus.REJECTED
    assert "PDF signature" in result.error_message


def test_validator_raises_specific_exception_for_corrupted_file(tmp_path):
    path = tmp_path / "fake.png"
    path.write_bytes(b"not actually a png")

    validator = FileValidator()
    with pytest.raises(CorruptedFileError):
        validator.validate(path)


# ---------------------------------------------------------------------
# Bonus: empty file
# ---------------------------------------------------------------------
def test_empty_file_is_rejected(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")

    validator = FileValidator()
    with pytest.raises(EmptyFileError):
        validator.validate(path)
