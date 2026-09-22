"""
extraction.py

Extracts text from uploaded documents and splits into overlapping word-windowed
chunks that match the ChunkBase schema expected by ingest_memory_with_chunks.

Supported formats:
  PDF   — pypdf, one page per PageText
  TXT   — UTF-8 read, treated as a single page
  DOCX  — python-docx, paragraphs grouped into pseudo-pages (~20 per page)
  IMAGE — pytesseract OCR (PNG / JPG), treated as a single page

Chunking strategy: sliding word window, ~300 words (~400 tokens) per chunk
with ~38-word (~50-token) overlap so context isn't cut at hard boundaries.
"""

from pathlib import Path
from typing import NamedTuple

from backend.schemas.chunk import ChunkBase

_CHUNK_WORDS = 300
_OVERLAP_WORDS = 38
_DOCX_PARAS_PER_PAGE = 20


class _PageText(NamedTuple):
    page_number: int
    text: str


def _chunk_page(page: _PageText, start_index: int) -> list[ChunkBase]:
    words = page.text.split()
    if not words:
        return []
    stride = _CHUNK_WORDS - _OVERLAP_WORDS
    chunks: list[ChunkBase] = []
    i = 0
    while i < len(words):
        window = words[i : i + _CHUNK_WORDS]
        content = " ".join(window)
        chunks.append(
            ChunkBase(
                chunk_index=start_index + len(chunks),
                content=content,
                page_number=page.page_number,
                chunk_metadata={"word_count": len(window)},
            )
        )
        i += stride
    return chunks


def _pages_to_chunks(pages: list[_PageText]) -> list[ChunkBase]:
    result: list[ChunkBase] = []
    for page in pages:
        if page.text.strip():
            result.extend(_chunk_page(page, start_index=len(result)))
    return result


def _extract_pdf(path: Path) -> list[ChunkBase]:
    from pypdf import PdfReader  # type: ignore[import-untyped]

    reader = PdfReader(str(path))
    pages = [
        _PageText(page_number=i + 1, text=page.extract_text() or "")
        for i, page in enumerate(reader.pages)
    ]
    return _pages_to_chunks(pages)


def _extract_txt(path: Path) -> list[ChunkBase]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return _pages_to_chunks([_PageText(page_number=1, text=text)])


def _extract_docx(path: Path) -> list[ChunkBase]:
    from docx import Document  # type: ignore[import-untyped]

    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    pages: list[_PageText] = []
    for i in range(0, max(len(paragraphs), 1), _DOCX_PARAS_PER_PAGE):
        batch = paragraphs[i : i + _DOCX_PARAS_PER_PAGE]
        pages.append(_PageText(page_number=(i // _DOCX_PARAS_PER_PAGE) + 1, text="\n".join(batch)))
    return _pages_to_chunks(pages)


def _extract_image(path: Path) -> list[ChunkBase]:
    # pytesseract requires tesseract-ocr system binary; skip handwriting — unreliable.
    import pytesseract  # type: ignore[import-untyped]
    from PIL import Image  # type: ignore[import-untyped]

    img = Image.open(str(path))
    text = pytesseract.image_to_string(img)
    return _pages_to_chunks([_PageText(page_number=1, text=text)])


def extract_chunks(path: Path, file_type: str) -> list[ChunkBase]:
    """
    Dispatch to the correct extractor.
    file_type values: "PDF", "TEXT", "DOCX", "IMAGE"
    """
    ext = path.suffix.lower()
    if ext == ".docx":
        return _extract_docx(path)
    if file_type == "PDF" or ext == ".pdf":
        return _extract_pdf(path)
    if file_type == "IMAGE" or ext in (".png", ".jpg", ".jpeg"):
        return _extract_image(path)
    return _extract_txt(path)
