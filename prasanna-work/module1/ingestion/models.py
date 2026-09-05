"""
models.py

Defines the data structures this module produces:
- ProcessingStatus: the allowed lifecycle states of a file
- FileMetadata: the structured record describing an ingested file
- IngestionResult: the final thing returned to whoever called this module

We use `dataclasses` (standard library) rather than plain dictionaries
because:
  1. Typos are caught. `metadata.file_id` fails loudly if mistyped;
     `metadata["fiel_id"]` on a dict silently returns a KeyError only
     at runtime, or worse, is a totally different bug if you used .get().
  2. Type hints make the shape of the data self-documenting.
  3. IDE autocomplete works properly.

We use `Enum` for processing_status instead of raw strings so that
invalid status values (e.g. a typo like "validatd") are impossible --
Python will not let you assign a value that isn't a defined enum member.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ProcessingStatus(str, Enum):
    """
    Lifecycle states for a file as it moves through ingestion.

    Inherits from `str` as well as `Enum` so that the value can be
    printed / JSON-serialized directly as a plain string (e.g. "validated")
    instead of the more awkward "ProcessingStatus.VALIDATED".
    """
    UPLOADED = "uploaded"      # file received, not yet checked
    VALIDATED = "validated"    # passed all checks, safe to proceed
    REJECTED = "rejected"      # failed a validation rule (e.g. bad type, too big)
    FAILED = "failed"          # an unexpected error occurred during processing


@dataclass
class FileMetadata:
    """Structured metadata describing a single ingested file."""
    file_id: str
    original_filename: str
    extension: str
    detected_file_type: Optional[str]   # "PDF", "IMAGE", "TEXT", or None if unknown
    file_size_bytes: int
    upload_timestamp: str                # ISO 8601 string, e.g. "2026-09-04T10:30:00+00:00"
    processing_status: ProcessingStatus

    @staticmethod
    def now_timestamp() -> str:
        """Returns the current UTC time as an ISO 8601 string."""
        return datetime.now(timezone.utc).isoformat()


@dataclass
class IngestionResult:
    """
    The final object returned by the ingestion module for a single file.

    `success` and `error_message` let the caller (e.g. main.py, or a
    future API layer) branch on the outcome without inspecting exceptions.
    """
    success: bool
    metadata: FileMetadata
    error_message: Optional[str] = None
