"""Split markdown files at heading boundaries with intelligent merge rules."""
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from . import config

# Film-specific: Import normalization for symmetric SORTING_DATABASE matching
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.normalization import normalize_for_lookup
    HAS_NORMALIZATION = True
except ImportError:
    HAS_NORMALIZATION = False
    normalize_for_lookup = None


@dataclass
class Chunk:
    """A single documentation chunk."""
    chunk_id: str                    # "SYSTEM_ARCHITECTURE__api_contracts"
    source_file: str                 # "docs/architecture/SYSTEM_ARCHITECTURE.md"
    section_reference: str           # "SYSTEM_ARCHITECTURE.md \u00a7 API Contracts"
    heading_text: str                # "API Contracts"
    heading_level: int               # 2 or 3
    parent_sections: List[str]       # ["Architecture", "Detailed Specification"]
    content: str                     # Raw markdown (including heading)
    line_range: Tuple[int, int]      # (730, 827)
    metadata: Dict[str, Any]         # From metadata.py
    outgoing_references: List[str]   # Section refs found in content

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)


def chunk_sorting_database(
    file_path: Path,
    file_metadata: Dict[str, Any]
) -> List[Chunk]:
    """
    Film-specific chunking for SORTING_DATABASE.md.

    Each film entry becomes one chunk:
        "- Deep Red (1975) → Satellite/Giallo/1970s/"

    Metadata extracted:
        - title: "Deep Red"
        - normalized_title: "deep red" (using normalize_for_lookup)
        - year: 1975
        - tier: "Satellite"
        - subdirectory: "Giallo"
        - decade: "1970s"

    Critical: Uses lib/normalization.normalize_for_lookup() for symmetric
    matching with the existing lookup system (same bug fix as lib/lookup.py).
    """
    if not file_path.exists():
        print(f"Warning: {file_path} not found, skipping")
        return []

    if not HAS_NORMALIZATION:
        print("Warning: lib.normalization not available, falling back to generic chunking")
        return chunk_markdown_file(file_path, file_metadata)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return []

    chunks = []
    file_stem = file_path.stem
    try:
        rel_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(file_path)

    # Patterns for film entries (from lib/lookup.py)
    pattern_standard = r'^-\s+(.+?)\s+\((\d{4})\).*?→\s+(.+?)/?$'
    pattern_year_prefix = r'^-\s+(\d{4})\s+-\s+(.+?)\s+→\s+(.+?)/?$'
    pattern_no_year = r'^-\s+([^→]+?)\s+→\s+(.+?)/?$'

    current_decade = None
    current_tier = None
    chunk_counter = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Track context from headers
        if stripped.startswith('## ') and 'FILMS' in stripped.upper():
            # Extract decade: "## 1970s FILMS" -> "1970s"
            decade_match = re.search(r'(\d{4}s)', stripped)
            current_decade = decade_match.group(1) if decade_match else None
            continue

        if stripped.startswith('###'):
            # Extract tier: "### Satellite - Giallo" or "### Reference"
            tier_match = re.match(r'###\s+(\w+)', stripped)
            current_tier = tier_match.group(1) if tier_match else None
            continue

        # Skip non-entry lines
        if not stripped.startswith('-'):
            continue

        # Skip notes/comments
        if any(marker in line for marker in ['[NOTE', '[BORDER', '[Wrong', '[OR ']):
            continue

        # Try standard format: "Title (Year) → Destination"
        match = re.match(pattern_standard, line)
        if match:
            title_raw, year_str, dest = match.groups()
            title_normalized = normalize_for_lookup(title_raw, strip_format_signals=True)
            year = int(year_str)

            # Extract tier/decade/subdirectory from destination
            dest_parts = [p for p in dest.strip().split('/') if p]
            tier = dest_parts[0] if len(dest_parts) > 0 else current_tier
            decade = dest_parts[1] if len(dest_parts) > 1 and re.match(r'\d{4}s', dest_parts[1]) else current_decade
            subdirectory = dest_parts[2] if len(dest_parts) > 2 else None
            if not subdirectory and len(dest_parts) > 1 and not re.match(r'\d{4}s', dest_parts[1]):
                subdirectory = dest_parts[1]

            chunk_counter += 1
            chunk = Chunk(
                chunk_id=f"{file_stem}__film_{chunk_counter}",
                source_file=rel_path,
                section_reference=f"{file_path.name} § {title_raw} ({year})",
                heading_text=f"{title_raw} ({year})",
                heading_level=3,
                parent_sections=[decade, tier] if decade and tier else [],
                content=line.strip(),
                line_range=(i, i),
                metadata={
                    **file_metadata,
                    'type': 'film_entry',
                    'title': title_raw,
                    'normalized_title': title_normalized,
                    'year': year,
                    'tier': tier,
                    'decade': decade,
                    'subdirectory': subdirectory,
                    'destination': dest.strip()
                },
                outgoing_references=[]
            )
            chunks.append(chunk)
            continue

        # Try year-prefix format: "Year - Title → Destination"
        match = re.match(pattern_year_prefix, line)
        if match:
            year_str, title_raw, dest = match.groups()
            title_normalized = normalize_for_lookup(title_raw, strip_format_signals=True)
            year = int(year_str)

            dest_parts = [p for p in dest.strip().split('/') if p]
            tier = dest_parts[0] if len(dest_parts) > 0 else current_tier
            decade = dest_parts[1] if len(dest_parts) > 1 and re.match(r'\d{4}s', dest_parts[1]) else current_decade
            subdirectory = dest_parts[2] if len(dest_parts) > 2 else None

            chunk_counter += 1
            chunk = Chunk(
                chunk_id=f"{file_stem}__film_{chunk_counter}",
                source_file=rel_path,
                section_reference=f"{file_path.name} § {title_raw} ({year})",
                heading_text=f"{title_raw} ({year})",
                heading_level=3,
                parent_sections=[decade, tier] if decade and tier else [],
                content=line.strip(),
                line_range=(i, i),
                metadata={
                    **file_metadata,
                    'type': 'film_entry',
                    'title': title_raw,
                    'normalized_title': title_normalized,
                    'year': year,
                    'tier': tier,
                    'decade': decade,
                    'subdirectory': subdirectory,
                    'destination': dest.strip()
                },
                outgoing_references=[]
            )
            chunks.append(chunk)
            continue

    print(f"  SORTING_DATABASE: {len(chunks)} film entries")
    return chunks


def chunk_satellite_categories(
    file_path: Path,
    file_metadata: Dict[str, Any]
) -> List[Chunk]:
    """
    Film-specific chunking for SATELLITE_CATEGORIES.md.

    Each satellite category (### section) becomes one chunk with metadata:
        - category: "giallo"
        - category_full_name: "GIALLO / ITALIAN HORROR-THRILLER"
        - decades: "1960s-1980s"
        - cap: 30
        - directors: ["Mario Bava", "Dario Argento", ...]

    Uses DMK's generic markdown chunker but keeps all category sections atomic
    (PROTECTED_HEADING_KEYWORDS includes "satellite", "category", "giallo", etc.).
    """
    # Use generic markdown chunker (protected keywords prevent merging)
    chunks = chunk_markdown_file(file_path, file_metadata)

    # Enhance chunks with category-specific metadata
    for chunk in chunks:
        content_lower = chunk.content.lower()

        # Detect category chunks (containing "directors:" or "cap:")
        if 'directors:' in content_lower or 'cap:' in content_lower or 'category' in chunk.heading_text.lower():
            # Extract category name from heading
            category_match = re.search(r'###\s+\d+\.\s+([A-Z\s/]+)', chunk.content)
            if category_match:
                category_full_name = category_match.group(1).strip()
                category_normalized = category_full_name.split('/')[0].strip().lower().replace(' ', '_')

                # Extract decade boundaries: "1960s-1980s peak" -> "1960s-1980s"
                decades_match = re.search(r'(\d{4}s)[-–](\d{4}s)', chunk.content)
                decades = f"{decades_match.group(1)}-{decades_match.group(2)}" if decades_match else "All decades"

                # Extract cap: "Total cap: 30" -> 30
                cap_match = re.search(r'cap[:\s]+(\d+)', chunk.content, re.IGNORECASE)
                cap = int(cap_match.group(1)) if cap_match else None

                # Extract directors list
                directors = []
                director_match = re.search(r'Directors?:\s*([^\n]+)', chunk.content, re.IGNORECASE)
                if director_match:
                    director_text = director_match.group(1)
                    directors = [d.strip() for d in re.split(r'[,;]', director_text) if d.strip()]

                # Add metadata
                chunk.metadata.update({
                    'type': 'satellite_category',
                    'category': category_normalized,
                    'category_full_name': category_full_name,
                    'decades': decades,
                    'cap': cap,
                    'directors': directors
                })

    return chunks


def chunk_file(
    file_path: Path,
    file_metadata: Dict[str, Any]
) -> List[Chunk]:
    """
    Route to appropriate chunking strategy based on filename.

    Film-specific routing:
        - SORTING_DATABASE.md → chunk_sorting_database()
        - SATELLITE_CATEGORIES.md → chunk_satellite_categories()
        - All other .md files → chunk_markdown_file() (generic DMK chunker)
    """
    filename = file_path.name

    if filename == "SORTING_DATABASE.md":
        return chunk_sorting_database(file_path, file_metadata)
    elif filename == "SATELLITE_CATEGORIES.md":
        return chunk_satellite_categories(file_path, file_metadata)
    else:
        return chunk_markdown_file(file_path, file_metadata)


def chunk_markdown_file(
    file_path: Path,
    file_metadata: Dict[str, Any]
) -> List[Chunk]:
    """
    Chunk a single markdown file at heading boundaries (H2/H3).

    Process:
        1. Parse file line-by-line
        2. Detect H2/H3 headings (## and ###)
        3. Extract content until next heading
        4. Apply merge rules (small chunks -> parent)
        5. Build parent_sections hierarchy
        6. Extract section references from content

    Returns:
        List[Chunk] with metadata attached
    """
    if not file_path.exists():
        print(f"Warning: {file_path} not found, skipping")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return []

    chunks = []
    current_chunk_lines = []
    current_heading = None
    current_level = None
    current_line_start = 0
    in_code_block = False
    parent_h2 = None

    file_stem = file_path.stem
    try:
        rel_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(file_path)

    pre_heading_lines = []
    header_chunk_emitted = False

    for i, line in enumerate(lines, start=1):
        # Track code block state to avoid treating ## in code as headings
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        # Detect headings (H2 or H3 only, not in code blocks)
        if not in_code_block:
            heading_match = re.match(r'^(#{2,3})\s+(.+)$', line)
            if heading_match:
                level_markers = heading_match.group(1)
                heading_text = heading_match.group(2).strip()
                level = len(level_markers)

                if level in (2, 3):
                    # Emit header chunk (content before first H2/H3)
                    if not header_chunk_emitted and pre_heading_lines:
                        if any(l.strip() for l in pre_heading_lines):
                            header_chunk = Chunk(
                                chunk_id=f"{file_stem}__header",
                                source_file=rel_path,
                                section_reference=f"{file_path.name} \u00a7 Header",
                                heading_text="Header",
                                heading_level=1,
                                parent_sections=[],
                                content=''.join(pre_heading_lines),
                                line_range=(1, i - 1),
                                metadata=file_metadata,
                                outgoing_references=extract_section_references(''.join(pre_heading_lines))
                            )
                            chunks.append(header_chunk)
                        header_chunk_emitted = True

                    # Save previous chunk if exists
                    if current_heading and current_chunk_lines:
                        chunk_content = ''.join(current_chunk_lines)

                        parents = []
                        if current_level == 3 and parent_h2:
                            parents = [parent_h2]

                        chunk = Chunk(
                            chunk_id=generate_chunk_id(file_stem, current_heading),
                            source_file=rel_path,
                            section_reference=f"{file_path.name} \u00a7 {current_heading}",
                            heading_text=current_heading,
                            heading_level=current_level,
                            parent_sections=parents,
                            content=chunk_content,
                            line_range=(current_line_start, i - 1),
                            metadata=file_metadata,
                            outgoing_references=extract_section_references(chunk_content)
                        )
                        chunks.append(chunk)

                    # Start new chunk
                    current_heading = heading_text
                    current_level = level
                    current_line_start = i
                    current_chunk_lines = [line]

                    if level == 2:
                        parent_h2 = heading_text

                    continue

        if current_heading is None and not header_chunk_emitted:
            pre_heading_lines.append(line)

        if current_heading:
            current_chunk_lines.append(line)

    # Save last chunk
    if current_heading and current_chunk_lines:
        chunk_content = ''.join(current_chunk_lines)
        parents = []
        if current_level == 3 and parent_h2:
            parents = [parent_h2]

        chunk = Chunk(
            chunk_id=generate_chunk_id(file_stem, current_heading),
            source_file=rel_path,
            section_reference=f"{file_path.name} \u00a7 {current_heading}",
            heading_text=current_heading,
            heading_level=current_level,
            parent_sections=parents,
            content=chunk_content,
            line_range=(current_line_start, len(lines)),
            metadata=file_metadata,
            outgoing_references=extract_section_references(chunk_content)
        )
        chunks.append(chunk)

    # Handle files without H2/H3 headings (treat as single chunk)
    if not chunks and lines:
        title_match = re.search(r'^#\s+(.+)$', lines[0]) if lines else None
        heading = title_match.group(1) if title_match else file_stem.replace('_', ' ')

        chunk = Chunk(
            chunk_id=generate_chunk_id(file_stem, heading),
            source_file=rel_path,
            section_reference=f"{file_path.name}",
            heading_text=heading,
            heading_level=1,
            parent_sections=[],
            content=''.join(lines),
            line_range=(1, len(lines)),
            metadata=file_metadata,
            outgoing_references=extract_section_references(''.join(lines))
        )
        chunks.append(chunk)

    # Apply merge rules
    chunks = merge_small_chunks(chunks, min_lines=config.MIN_CHUNK_LINES)

    return chunks


def extract_section_references(content: str) -> List[str]:
    """
    Find all section references in content.

    Pattern: `FILENAME.md \u00a7 Section Heading`

    Returns:
        ["PATTERN_FIRST.md \u00a7 Principle 2", ...]
    """
    pattern = r'([A-Z_]+\.md)\s*\u00a7\s*([^`\n]+)'
    matches = re.findall(pattern, content)

    references = []
    for filename, section in matches:
        section_clean = section.strip().rstrip('.,;:')
        references.append(f"{filename} \u00a7 {section_clean}")

    return references


def merge_small_chunks(chunks: List[Chunk], min_lines: int = 20) -> List[Chunk]:
    """
    Merge chunks smaller than min_lines into their parent section.

    Rules:
        - Never merge header chunk (first chunk)
        - Never merge H2 sections (top-level)
        - Only merge small H3 into H2 parent
        - Never merge chunks with protected heading keywords (configurable)
    """
    if not chunks:
        return chunks

    protected_keywords = [kw.lower() for kw in config.PROTECTED_HEADING_KEYWORDS]
    merged = []

    for i, chunk in enumerate(chunks):
        line_count = chunk.line_range[1] - chunk.line_range[0] + 1

        # Never merge first chunk
        if i == 0:
            merged.append(chunk)
            continue

        # Never merge H2 sections (top-level)
        if chunk.heading_level == 2:
            merged.append(chunk)
            continue

        # Never merge protected headings (keep atomic even if small)
        heading_lower = chunk.heading_text.lower()
        if any(kw in heading_lower for kw in protected_keywords):
            merged.append(chunk)
            continue

        # Never merge if over threshold
        if line_count >= min_lines:
            merged.append(chunk)
            continue

        # Merge into previous chunk if it's the H2 parent
        if i > 0 and merged:
            prev_chunk = merged[-1]
            if prev_chunk.heading_level == 2:
                merged_content = prev_chunk.content + "\n" + chunk.content
                merged_chunk = Chunk(
                    chunk_id=prev_chunk.chunk_id,
                    source_file=prev_chunk.source_file,
                    section_reference=prev_chunk.section_reference,
                    heading_text=prev_chunk.heading_text,
                    heading_level=prev_chunk.heading_level,
                    parent_sections=prev_chunk.parent_sections,
                    content=merged_content,
                    line_range=(prev_chunk.line_range[0], chunk.line_range[1]),
                    metadata=prev_chunk.metadata,
                    outgoing_references=list(set(prev_chunk.outgoing_references + chunk.outgoing_references))
                )
                merged[-1] = merged_chunk
            else:
                merged.append(chunk)
        else:
            merged.append(chunk)

    return merged


def generate_chunk_id(file_stem: str, heading_text: str) -> str:
    """
    Generate stable chunk ID from file and heading.

    Example:
        file_stem="SYSTEM_ARCHITECTURE"
        heading_text="API Contracts (v2.0)"
        -> "SYSTEM_ARCHITECTURE__api_contracts"
    """
    # Remove version markers
    heading_clean = re.sub(r'\(v\d+\.\d+[^)]*\)', '', heading_text)
    heading_clean = re.sub(r'v\d+\.\d+', '', heading_clean)

    # Lowercase and replace non-alphanumeric with underscore
    heading_slug = re.sub(r'[^a-z0-9]+', '_', heading_clean.lower())
    heading_slug = heading_slug.strip('_')

    chunk_id = f"{file_stem}__{heading_slug}"

    if len(chunk_id) > 100:
        chunk_id = chunk_id[:100].rstrip('_')

    return chunk_id
