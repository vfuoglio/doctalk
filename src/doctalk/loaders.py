"""Read supported files into (page_label, text) sections."""
from __future__ import annotations

from pathlib import Path

SUPPORTED = {".pdf", ".md", ".txt"}


def load_file(path: Path) -> list[tuple[str, str]]:
    """Return a list of (location, text) sections for a file.

    PDFs yield one section per page ("p. 3"); text files yield one section.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [
            (f"p. {i}", page.extract_text() or "")
            for i, page in enumerate(reader.pages, start=1)
        ]
    if suffix in {".md", ".txt"}:
        return [("", path.read_text(encoding="utf-8", errors="replace"))]
    raise ValueError(f"Unsupported file type: {suffix}")


def find_files(root: Path) -> list[Path]:
    """Recursively collect supported files under root (or root itself)."""
    if root.is_file():
        return [root]
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in SUPPORTED)
