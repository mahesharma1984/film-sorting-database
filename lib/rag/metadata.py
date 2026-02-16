"""Parse CORE_DOCUMENTATION_INDEX.md for authority metadata.

The metadata parser extracts document status, verification dates, and
canonical source mappings from your CORE_DOCUMENTATION_INDEX.md file.

This works with the DMK template format (see templates/CORE_DOCS_INDEX.md).
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from . import config


def parse_core_doc_index(index_path: Path = config.CORE_DOC_INDEX) -> Dict[str, Dict[str, Any]]:
    """
    Extract file metadata from CORE_DOCUMENTATION_INDEX.md.

    Parses markdown tables to find document paths, status levels, and
    verification dates. Works with multiple table formats.

    Returns:
        {
            "docs/architecture/SYSTEM_ARCHITECTURE.md": {
                "status": "AUTHORITATIVE",
                "verified": "2026-02-06",
                "version": "1.0"
            },
            ...
        }
    """
    if not index_path.exists():
        print(f"Warning: {index_path} not found, using unmarked status for all files")
        return {}

    metadata = {}

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Pattern 1: Table rows with backtick-wrapped file paths and bold status
        # Format: | `docs/path/file.md` | Purpose | **STATUS** | Date |
        table_row_pattern = r'\|\s*`([^`]+\.md)`\s*\|([^|]+)\|([^|]+)\|([^|]+)\|'
        for match in re.finditer(table_row_pattern, content):
            file_path = match.group(1).strip()
            purpose = match.group(2).strip()
            status_field = match.group(3).strip()
            date_field = match.group(4).strip()

            status_match = re.search(r'\*\*([A-Z]+)\*\*', status_field)
            status = status_match.group(1) if status_match else _extract_status(status_field)

            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_field)
            verified_date = date_match.group(1) if date_match else "unknown"

            version_match = re.search(r'v(\d+\.\d+)', purpose)
            version = version_match.group(1) if version_match else None

            metadata[file_path] = {
                "status": status,
                "verified": verified_date,
                "version": version,
                "canonical": False
            }

        # Pattern 2: Simpler table format (3 columns)
        # Format: | `docs/path/file.md` | Purpose | STATUS |
        if not metadata:
            simple_pattern = r'\|\s*`([^`]+\.md)`\s*\|([^|]+)\|([^|]+)\|'
            for match in re.finditer(simple_pattern, content):
                file_path = match.group(1).strip()
                purpose = match.group(2).strip()
                status_field = match.group(3).strip()

                status = _extract_status(status_field)

                metadata[file_path] = {
                    "status": status,
                    "verified": "unknown",
                    "version": None,
                    "canonical": False
                }

        # Mark canonical sources
        canonical_pattern = r'\|\s*\*\*[^|]+\*\*\s*\|\s*`/?([^`]+\.md)`\s*\|'
        canonical_matches = re.findall(canonical_pattern, content)
        for canonical_path in canonical_matches:
            canonical_path = canonical_path.lstrip('/')
            if canonical_path in metadata:
                metadata[canonical_path]["canonical"] = True

    except Exception as e:
        print(f"Warning: Failed to parse {index_path}: {e}")
        return {}

    return metadata


def _extract_status(field: str) -> str:
    """Extract status from a table field, handling various formats."""
    field_upper = field.strip().upper()
    for known_status in ["AUTHORITATIVE", "STABLE", "ARCHIVED"]:
        if known_status in field_upper:
            return known_status
    return "unmarked"


def get_authority_boost(
    status: str,
    verified_date: str,
    reference_date: Optional[str] = None,
    canonical: bool = False
) -> float:
    """
    Calculate authority boost with freshness decay.

    Documents that are more authoritative and more recently verified
    get higher scores. This ensures that actively maintained docs
    rank above stale ones.

    Args:
        status: "AUTHORITATIVE", "STABLE", "ARCHIVED", or "unmarked"
        verified_date: "2026-02-06" format or "unknown"
        reference_date: Override current date (for testing)
        canonical: Whether this is a canonical source

    Returns:
        Float between 0.1-1.2
    """
    base_boost = config.AUTHORITY_BOOST.get(status, config.AUTHORITY_BOOST["unmarked"])

    if verified_date == "unknown":
        boost = base_boost
        if canonical:
            boost = min(config.MAX_AUTHORITY_SCORE, boost + config.CANONICAL_BOOST)
        return boost

    try:
        verified_dt = datetime.fromisoformat(verified_date)
        ref_dt = datetime.fromisoformat(reference_date) if reference_date else datetime.now()

        days_since = (ref_dt - verified_dt).days
        freshness = max(0.5, 1.0 - (days_since / config.VERIFIED_DATE_DECAY_DAYS))

        boost = base_boost * freshness
        if canonical:
            boost = min(config.MAX_AUTHORITY_SCORE, boost + config.CANONICAL_BOOST)
        return boost

    except (ValueError, TypeError):
        boost = base_boost
        if canonical:
            boost = min(config.MAX_AUTHORITY_SCORE, boost + config.CANONICAL_BOOST)
        return boost


def extract_file_metadata(md_file: Path) -> Dict[str, Any]:
    """
    Extract metadata from markdown file header (first 50 lines).

    Looks for common header patterns:
        **Version:** 1.0
        **Last Updated:** 2026-02-06
        **Purpose:** ...
        **Status:** AUTHORITATIVE

    Returns:
        {"version": "1.0", "last_updated": "2026-02-06", ...}
    """
    metadata = {}

    if not md_file.exists():
        return metadata

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = [next(f, None) for _ in range(50)]
            header = ''.join(line for line in lines if line is not None)

        version_match = re.search(r'\*\*Version:\*\*\s*(\d+\.\d+)', header)
        if version_match:
            metadata["version"] = version_match.group(1)

        date_match = re.search(r'\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})', header)
        if date_match:
            metadata["last_updated"] = date_match.group(1)

        status_match = re.search(r'\*\*Status:\*\*\s*([A-Z]+)', header)
        if status_match:
            metadata["status"] = status_match.group(1)

        purpose_match = re.search(r'\*\*Purpose:\*\*\s*(.+)', header)
        if purpose_match:
            metadata["purpose"] = purpose_match.group(1).strip()

    except Exception as e:
        print(f"Warning: Failed to extract metadata from {md_file}: {e}")

    return metadata


def parse_quick_reference_table(index_path: Path = config.CORE_DOC_INDEX) -> List[Tuple[str, str]]:
    """
    Parse Quick Reference table from CORE_DOCUMENTATION_INDEX.md.

    Extracts question-to-file mappings for structured lookup.

    Returns:
        List of tuples: [(question, file_path), ...]
        Example: [("How do I set up the project?", "docs/DEVELOPER_GUIDE.md"), ...]
    """
    if not index_path.exists():
        print(f"Warning: {index_path} not found, Quick Reference table unavailable")
        return []

    quick_ref_entries = []

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Quick Reference section
        quick_ref_match = re.search(
            r'## Quick Reference\s*\n\s*\|[^\n]+\|[^\n]+\|\s*\n\s*\|[-\s|]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)',
            content,
            re.MULTILINE
        )

        if not quick_ref_match:
            print(f"Warning: Could not find Quick Reference table in {index_path}")
            return []

        table_rows = quick_ref_match.group(1)

        # Parse each row: look for file paths in backticks
        row_pattern = r'\|\s*([^|]+?)\s*\|([^|]+)\|'

        for match in re.finditer(row_pattern, table_rows):
            question = match.group(1).strip()
            rest = match.group(2).strip()

            # Extract file path from anywhere in the row (backtick-wrapped)
            # Check full row text for file paths
            full_row = match.group(0)
            file_match = re.search(r'`([^`]+\.md|[^`]+\.py|[^`]+\.json)`', full_row)
            if not file_match:
                # Try in remaining columns
                file_match = re.search(r'`([^`]+\.md|[^`]+\.py|[^`]+\.json)`', rest)

            if file_match:
                file_path = file_match.group(1).strip().lstrip('/')
                quick_ref_entries.append((question, file_path))
            else:
                # Try without backticks
                file_match = re.search(r'/?([a-zA-Z_/]+\.md)', rest)
                if file_match:
                    file_path = file_match.group(1).lstrip('/')
                    quick_ref_entries.append((question, file_path))

    except Exception as e:
        print(f"Warning: Failed to parse Quick Reference table: {e}")
        return []

    return quick_ref_entries


def parse_canonical_sources_table(index_path: Path = config.CORE_DOC_INDEX) -> Dict[str, str]:
    """
    Parse Canonical Sources table from CORE_DOCUMENTATION_INDEX.md.

    Returns:
        Dict mapping concept keywords to canonical file paths
        Example: {"system architecture": "docs/architecture/SYSTEM_ARCHITECTURE.md"}
    """
    if not index_path.exists():
        print(f"Warning: {index_path} not found, Canonical Sources table unavailable")
        return {}

    canonical_sources = {}

    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Canonical Sources section
        canonical_match = re.search(
            r'## Canonical Sources[^\n]*\n.*?\|[^\n]*Concept[^\n]*\|[^\n]*\|\s*\n\s*\|[-\s|]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)',
            content,
            re.MULTILINE | re.DOTALL
        )

        if not canonical_match:
            print(f"Warning: Could not find Canonical Sources table in {index_path}")
            return {}

        table_rows = canonical_match.group(1)

        # Parse rows - handle both bold and non-bold concept names
        row_pattern = r'\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|\s*`?([^`|]+?)`?\s*\|'

        for match in re.finditer(row_pattern, table_rows):
            concept = match.group(1).strip()
            file_path = match.group(2).strip().lstrip('/')

            # Only include if it looks like a file path
            if '.' in file_path and '/' in file_path:
                canonical_sources[concept.lower()] = file_path

    except Exception as e:
        print(f"Warning: Failed to parse Canonical Sources table: {e}")
        return {}

    return canonical_sources
