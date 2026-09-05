"""
main.py

Command-line entry point for testing the ingestion module manually.

Usage:
    python main.py sample_files/notes.txt
"""

import logging
import sys

from ingestion.file_handler import FileHandler

# Basic logging setup. INFO level shows the flow of what happened;
# in a real deployment this might write to a file or a log aggregator
# instead of the console.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    handler = FileHandler()
    result = handler.ingest_file(file_path)
    metadata = result.metadata

    if result.success:
        print("File accepted")
    else:
        print("File rejected")

    print(f"File ID: {metadata.file_id}")
    print(f"Filename: {metadata.original_filename}")
    print(f"Type: {metadata.detected_file_type or 'UNKNOWN'}")
    print(f"Size: {metadata.file_size_bytes:,} bytes")
    print(f"Status: {metadata.processing_status.value}")

    if result.error_message:
        print(f"Reason: {result.error_message}")

    # Exit code 0 for success, 1 for failure -- useful if this is ever
    # called from a shell script or CI pipeline.
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
