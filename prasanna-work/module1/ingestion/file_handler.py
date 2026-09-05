"""
file_handler.py

Contains FileHandler: the orchestrator that ties together
FileValidator + FileMetadata into a single entry point,
`ingest_file()`, that the rest of the app (or main.py) calls.

Separation of concerns:
  - validator.py knows HOW to check things and raises exceptions.
  - file_handler.py knows WHAT to do with the outcome: build metadata,
    set the correct ProcessingStatus, log the result, and package it
    all into an IngestionResult so the caller never has to deal with
    a raw exception directly.
"""

import logging
import uuid
from pathlib import Path

from ingestion.exceptions import IngestionError
from ingestion.models import FileMetadata, IngestionResult, ProcessingStatus
from ingestion.validator import FileValidator

logger = logging.getLogger(__name__)


class FileHandler:
    """Coordinates validation and metadata creation for a single uploaded file."""

    def __init__(self, validator: FileValidator | None = None) -> None:
        # Accepting the validator as a parameter (instead of creating it
        # internally) is called "dependency injection". It means tests
        # can pass in a fake/mock validator if needed, without changing
        # this class. For now we just default to a real FileValidator.
        self.validator = validator or FileValidator()

    def ingest_file(self, file_path: str) -> IngestionResult:
        """
        Runs the full ingestion + validation flow for one file path.
        Always returns an IngestionResult -- never raises. This makes it
        safe to call from a CLI, a future API endpoint, or a batch script
        without needing a try/except at every call site.
        """
        path = Path(file_path)
        file_id = str(uuid.uuid4())
        original_filename = path.name
        extension = path.suffix.lower()

        logger.info("Starting ingestion for '%s' (assigned file_id=%s)", original_filename, file_id)

        # Build a baseline metadata object with UPLOADED status first.
        # If something fails early (e.g. file doesn't exist), we still
        # have a well-formed metadata object to report back, just with
        # size_bytes = 0 and detected_file_type = None.
        metadata = FileMetadata(
            file_id=file_id,
            original_filename=original_filename,
            extension=extension,
            detected_file_type=None,
            file_size_bytes=0,
            upload_timestamp=FileMetadata.now_timestamp(),
            processing_status=ProcessingStatus.UPLOADED,
        )

        try:
            detected_type, size_bytes = self.validator.validate(path)

            metadata.detected_file_type = detected_type
            metadata.file_size_bytes = size_bytes
            metadata.processing_status = ProcessingStatus.VALIDATED

            logger.info("File '%s' validated successfully as %s.", original_filename, detected_type)
            return IngestionResult(success=True, metadata=metadata, error_message=None)

        except IngestionError as exc:
            # Any of our custom validation failures land here.
            # This is a "rejection", not a system failure -- the file
            # was properly examined, it just doesn't qualify.
            metadata.processing_status = ProcessingStatus.REJECTED
            logger.warning("File '%s' rejected: %s", original_filename, exc)
            return IngestionResult(success=False, metadata=metadata, error_message=str(exc))

        except Exception as exc:
            # Anything NOT anticipated (e.g. a permissions error, disk
            # I/O failure) is a genuine system failure, distinct from a
            # normal rejection. We log it with full traceback info and
            # still return a structured result instead of crashing.
            metadata.processing_status = ProcessingStatus.FAILED
            logger.exception("Unexpected error while ingesting '%s'", original_filename)
            return IngestionResult(success=False, metadata=metadata, error_message=str(exc))
