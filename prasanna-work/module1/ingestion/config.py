"""
config.py

Central place for all tunable settings used by the ingestion module.

Why this file exists:
Hardcoding a number like `10_000_000` (max file size) inside validator.py
means that changing it later requires hunting through the codebase.
Keeping it here means one change, one place -- and it's easy to point to
in a review when someone asks "how would you make this configurable?".
"""

from pathlib import Path

# --- File size limit ---
# Expressed in MB for human readability, converted to bytes for actual use.
MAX_FILE_SIZE_MB: int = 20
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Supported file types ---
# Maps a file extension (lowercase, with dot) to a human-readable
# "detected_file_type" label used in our metadata output.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".png": "IMAGE",
    ".jpg": "IMAGE",
    ".jpeg": "IMAGE",
    ".txt": "TEXT",
}

# Maps our internal type label to the MIME types we consider valid for it.
# Used as a secondary check alongside the extension.
SUPPORTED_MIME_TYPES: dict[str, list[str]] = {
    "PDF": ["application/pdf"],
    "IMAGE": ["image/png", "image/jpeg"],
    "TEXT": ["text/plain"],
}

# --- Storage location placeholder ---
# Not used for saving files yet (that's the next module), but declared
# here so config stays the single source of truth for paths going forward.
UPLOAD_STAGING_DIR = Path("uploads_staging")
