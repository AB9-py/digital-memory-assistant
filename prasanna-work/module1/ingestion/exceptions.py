"""
exceptions.py

Custom exceptions for the ingestion module.

Why not just use built-in exceptions (ValueError, OSError, etc.) everywhere?
Because the calling code (and our tests) often need to react *differently*
depending on *why* validation failed. Custom exception classes let us do:

    try:
        validator.validate(path)
    except UnsupportedFileTypeError:
        ... handle this specific case ...
    except FileSizeLimitExceededError:
        ... handle this other case ...

instead of parsing error message strings, which is fragile and not
production-grade.

All our custom exceptions inherit from a single base class,
IngestionError, so callers who don't care about the specific reason
can catch just that one base class instead.
"""


class IngestionError(Exception):
    """Base class for all errors raised by the ingestion module."""


class FileNotFoundInIngestionError(IngestionError):
    """Raised when the given file path does not exist on disk."""


class EmptyFileError(IngestionError):
    """Raised when the file exists but contains zero bytes."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when the file extension is not in our supported list."""


class FileSizeLimitExceededError(IngestionError):
    """Raised when the file is larger than the configured maximum size."""


class CorruptedFileError(IngestionError):
    """
    Raised when the file's actual content does not match what its
    extension claims (e.g. a .pdf file that doesn't start with the
    PDF magic bytes, or a .txt file containing undecodable binary data).
    """
