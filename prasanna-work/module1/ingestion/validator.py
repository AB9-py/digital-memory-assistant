"""
validator.py

Contains FileValidator: a class whose only job is to answer,
step by step, "is this file acceptable?" -- and raise a specific
exception the moment it isn't.

Each check is a small, separately-named method. This matters for two
reasons:
  1. You can unit test each check in isolation (see tests/test_validator.py).
  2. When someone in your review asks "how do you detect a corrupted file?"
     you can point to one specific method instead of a wall of logic.

The order of checks matters and is deliberate:
  existence -> not empty -> extension -> size -> content signature
We check cheap things (does it exist? is it empty?) before expensive or
more complex things (reading bytes to verify a signature).
"""

import logging
import mimetypes
from pathlib import Path

from ingestion.config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from ingestion.exceptions import (
    FileNotFoundInIngestionError,
    EmptyFileError,
    UnsupportedFileTypeError,
    FileSizeLimitExceededError,
    CorruptedFileError,
)

logger = logging.getLogger(__name__)

# --- Known file signatures ("magic bytes") ---
# These are the fixed byte sequences that real files of these types
# begin with, regardless of filename. Source: each format's public spec.
PDF_SIGNATURE = b"%PDF-"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"

# How many bytes we need to read from the start of the file to check
# every signature above. PNG's is the longest at 8 bytes; we read a
# small safety margin.
SIGNATURE_READ_SIZE = 16


class FileValidator:
    """Performs all validation checks on a single file path."""

    def validate_existence(self, path: Path) -> None:
        """Raises FileNotFoundInIngestionError if the path doesn't exist or isn't a file."""
        if not path.exists():
            raise FileNotFoundInIngestionError(f"No file found at path: {path}")
        if not path.is_file():
            raise FileNotFoundInIngestionError(f"Path exists but is not a file: {path}")

    def validate_not_empty(self, path: Path) -> int:
        """
        Raises EmptyFileError if the file has zero bytes.
        Returns the file size in bytes on success (so callers don't need
        a second disk call).
        """
        size_bytes = path.stat().st_size
        if size_bytes == 0:
            raise EmptyFileError(f"File is empty (0 bytes): {path.name}")
        return size_bytes

    def validate_extension(self, path: Path) -> str:
        """
        Raises UnsupportedFileTypeError if the extension isn't supported.
        Returns our internal type label (e.g. "PDF") on success.
        """
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{extension}'. "
                f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}"
            )
        return SUPPORTED_EXTENSIONS[extension]

    def validate_size(self, size_bytes: int) -> None:
        """Raises FileSizeLimitExceededError if size_bytes exceeds the configured max."""
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise FileSizeLimitExceededError(
                f"File size {size_bytes:,} bytes exceeds the "
                f"{MAX_FILE_SIZE_MB}MB limit ({MAX_FILE_SIZE_BYTES:,} bytes)."
            )

    def validate_content_signature(self, path: Path, expected_type: str) -> None:
        """
        Reads the first bytes of the file and checks them against known
        magic-byte signatures for the expected type. This is what catches
        a file that has a misleading extension (e.g. a .pdf that is
        actually a text file, or a truncated/corrupted image).

        Raises CorruptedFileError if the content does not match.
        """
        with path.open("rb") as f:
            header = f.read(SIGNATURE_READ_SIZE)

        if expected_type == "PDF":
            if not header.startswith(PDF_SIGNATURE):
                raise CorruptedFileError(
                    f"File '{path.name}' has a .pdf extension but its content "
                    f"does not start with the PDF signature ({PDF_SIGNATURE!r})."
                )

        elif expected_type == "IMAGE":
            if not (header.startswith(PNG_SIGNATURE) or header.startswith(JPEG_SIGNATURE)):
                raise CorruptedFileError(
                    f"File '{path.name}' has an image extension but its content "
                    f"does not match the PNG or JPEG signature."
                )

        elif expected_type == "TEXT":
            # Plain text has no magic bytes. Instead we confirm the file
            # can be decoded as UTF-8 text -- if it can't, it's likely
            # binary data wearing a .txt extension.
            try:
                with path.open("r", encoding="utf-8") as f:
                    f.read(SIGNATURE_READ_SIZE)
            except UnicodeDecodeError as exc:
                raise CorruptedFileError(
                    f"File '{path.name}' has a .txt extension but its content "
                    f"could not be decoded as UTF-8 text."
                ) from exc

    def get_mime_type(self, path: Path) -> str | None:
        """
        Best-effort MIME type guess based on extension, using the
        standard library's mimetypes module. This is informational --
        NOT used as proof of file validity (see module docstring notes
        on extension vs. content signature).
        """
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type

    def validate(self, path: Path) -> tuple[str, int]:
        """
        Runs all checks in order. Returns (detected_file_type, size_bytes)
        on success. Raises the first applicable IngestionError subclass
        on failure.
        """
        logger.info("Validating file: %s", path)

        self.validate_existence(path)
        size_bytes = self.validate_not_empty(path)
        detected_type = self.validate_extension(path)
        self.validate_size(size_bytes)
        self.validate_content_signature(path, detected_type)

        logger.info("File passed all validation checks: %s (%s)", path.name, detected_type)
        return detected_type, size_bytes
