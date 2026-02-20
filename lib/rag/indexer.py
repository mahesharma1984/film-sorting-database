"""Build RAG index from scratch by reading, chunking, embedding, and storing."""
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from . import config
from .metadata import parse_core_doc_index, extract_file_metadata, parse_quick_reference_table
from .chunker import chunk_file, Chunk  # Use chunk_file dispatcher for film-specific routing

# Optional dependencies (graceful fallback)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    SentenceTransformer = None
    np = None

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = None


def build_index(
    docs_root: Path = config.DOCS_ROOT,
    force_rebuild: bool = False
) -> Dict[str, Any]:
    """
    Build RAG index from all markdown files in docs/.

    Process:
        1. Check if index exists (skip if force_rebuild=False)
        2. Load CORE_DOCUMENTATION_INDEX metadata
        3. Discover all .md files recursively
        4. For each file: chunk at heading boundaries, extract metadata, embed
        5. Write index.jsonl + embeddings.npy
        6. Build Quick Reference index
        7. Log build stats

    Returns:
        Build stats dict
    """
    if not HAS_EMBEDDINGS:
        print("Error: sentence-transformers required for indexing")
        print("Install with: pip install sentence-transformers numpy")
        sys.exit(1)

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if config.INDEX_FILE.exists() and not force_rebuild:
        print(f"Index already exists at {config.INDEX_FILE}")
        print("Use --force to rebuild")
        return {}

    print("Building RAG index...")
    start_time = time.time()

    # Load CORE_DOCUMENTATION_INDEX metadata
    print(f"Loading metadata from {config.CORE_DOC_INDEX}...")
    doc_metadata = parse_core_doc_index()
    print(f"  Loaded metadata for {len(doc_metadata)} files")

    # Discover all .md files from primary root + additional roots
    print(f"Discovering markdown files in {docs_root}...")
    all_md_files = list(docs_root.rglob("*.md"))
    for additional_root in getattr(config, 'ADDITIONAL_DOCS_ROOTS', []):
        if additional_root.exists():
            additional_files = list(additional_root.rglob("*.md"))
            print(f"  + {len(additional_files)} files from {additional_root}")
            all_md_files.extend(additional_files)

    # Filter out excluded paths
    repo_root = Path.cwd()
    md_files = []
    excluded_count = 0
    for f in all_md_files:
        try:
            rel_path = str(f.relative_to(repo_root))
        except ValueError:
            rel_path = str(f)

        if any(rel_path.startswith(excl) for excl in config.EXCLUDED_PATHS):
            excluded_count += 1
            continue

        md_files.append(f)

    print(f"  Found {len(md_files)} files ({excluded_count} excluded)")

    # Collect all chunks
    all_chunks = []
    files_processed = 0

    iterator = tqdm(md_files, desc="Chunking files") if HAS_TQDM else md_files

    for md_file in iterator:
        try:
            rel_path = str(md_file.relative_to(repo_root))
        except ValueError:
            rel_path = str(md_file)

        # Get metadata for this file
        file_meta = doc_metadata.get(rel_path, {})

        # If not in CORE_DOC_INDEX, try extracting from file header
        if not file_meta:
            file_meta = extract_file_metadata(md_file)
            if not file_meta.get("status"):
                file_meta["status"] = "unmarked"

        try:
            chunks = chunk_file(md_file, file_meta)  # Routes to film-specific chunkers
            all_chunks.extend(chunks)
            files_processed += 1

            if not HAS_TQDM and files_processed % 10 == 0:
                print(f"  Processed {files_processed}/{len(md_files)} files...")

        except Exception as e:
            print(f"Warning: Failed to chunk {md_file}: {e}")
            continue

    print(f"\nChunked {files_processed} files into {len(all_chunks)} chunks")

    # Embed all chunks
    print("Generating embeddings...")
    embeddings = embed_chunks(all_chunks, model_name=config.EMBEDDING_MODEL)
    print(f"  Generated {embeddings.shape[0]} embeddings ({embeddings.shape[1]}-dim)")

    # Write index and embeddings
    print(f"Writing index to {config.INDEX_FILE}...")
    write_index(all_chunks, embeddings)

    # Build Quick Reference index
    qr_count = build_quick_reference_index(model_name=config.EMBEDDING_MODEL)

    # Calculate stats
    build_time = time.time() - start_time
    total_lines = sum(c.line_range[1] - c.line_range[0] + 1 for c in all_chunks)
    avg_chunk_lines = total_lines / len(all_chunks) if all_chunks else 0

    stats = {
        "files_processed": files_processed,
        "chunks_created": len(all_chunks),
        "avg_chunk_lines": round(avg_chunk_lines, 1),
        "build_time_seconds": round(build_time, 1),
        "model": config.EMBEDDING_MODEL,
        "embedding_dim": config.EMBEDDING_DIM,
        "quick_reference_questions": qr_count
    }

    log_build_event(stats)

    print("\nIndex build complete!")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Chunks created: {stats['chunks_created']}")
    print(f"  Avg chunk size: {stats['avg_chunk_lines']} lines")
    print(f"  Build time: {stats['build_time_seconds']}s")

    return stats


def embed_chunks(
    chunks: List[Chunk],
    model_name: str = config.EMBEDDING_MODEL
):
    """
    Generate embeddings for chunks using sentence-transformers.

    Embeds heading_text + first 500 chars of content.
    Normalizes vectors (L2 norm) for cosine similarity.
    """
    print(f"Loading embedding model: {model_name}...")
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Error loading model: {e}")
        print("If model download failed, check internet connection")
        sys.exit(1)

    texts = []
    for chunk in chunks:
        content_preview = chunk.content[:500] if len(chunk.content) > 500 else chunk.content
        text = f"{chunk.heading_text}\n{content_preview}"
        texts.append(text)

    print("Encoding chunks...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=HAS_TQDM,
        normalize_embeddings=True
    )

    return embeddings


def write_index(chunks: List[Chunk], embeddings):
    """Write chunks and embeddings to index files."""
    with open(config.INDEX_FILE, 'w', encoding='utf-8') as f:
        for chunk, embedding in zip(chunks, embeddings):
            chunk_dict = chunk.to_dict()
            chunk_dict['embedding'] = embedding.tolist()
            f.write(json.dumps(chunk_dict, ensure_ascii=False) + '\n')

    np.save(config.EMBEDDINGS_FILE, embeddings)

    print(f"  Wrote {len(chunks)} chunks to {config.INDEX_FILE}")
    print(f"  Wrote embeddings to {config.EMBEDDINGS_FILE}")


def build_quick_reference_index(model_name: str = config.EMBEDDING_MODEL):
    """
    Build Quick Reference index by embedding questions from CORE_DOCUMENTATION_INDEX.

    Creates:
        - quick_reference_index.json: Question-to-file mappings
        - quick_reference_embeddings.npy: Embeddings for all questions
    """
    print("\nBuilding Quick Reference index...")

    qr_entries = parse_quick_reference_table()

    if not qr_entries:
        print("  No Quick Reference entries found, skipping")
        return 0

    print(f"  Found {len(qr_entries)} Quick Reference entries")

    print(f"  Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)

    questions = [q for q, _ in qr_entries]

    print("  Encoding questions...")
    embeddings = model.encode(
        questions,
        batch_size=32,
        show_progress_bar=HAS_TQDM,
        normalize_embeddings=True
    )

    quick_ref_index = []
    for idx, (question, file_path) in enumerate(qr_entries):
        quick_ref_index.append({
            "question": question,
            "file": file_path,
            "embedding_idx": idx
        })

    with open(config.QUICK_REFERENCE_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(quick_ref_index, f, ensure_ascii=False, indent=2)

    np.save(config.QUICK_REFERENCE_EMBEDDINGS_FILE, embeddings)

    print(f"  Wrote Quick Reference index ({len(qr_entries)} questions)")

    return len(qr_entries)


def log_build_event(stats: Dict[str, Any]):
    """Append build event to build_log.jsonl (append-only history)."""
    event = {
        "event": "build_complete",
        "timestamp": datetime.now().isoformat(),
        **stats
    }

    with open(config.BUILD_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Build RAG index from docs/")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if index exists"
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=config.DOCS_ROOT,
        help="Root directory for docs (default: docs/)"
    )

    args = parser.parse_args()

    build_index(docs_root=args.docs_root, force_rebuild=args.force)


if __name__ == "__main__":
    main()
