#!/usr/bin/env python3
"""
RAG-Enhanced Classification Assistant

Suggests classifications for films using RAG semantic search over the knowledge base.
Use this during manual curation of Unsorted films.

Usage:
    python classify_assistant.py "Film Title (Year)" "Director" "Country/Genre"
    python classify_assistant.py "Deep Red (1975)" "Dario Argento" "Italian horror"
    python classify_assistant.py "Black Orpheus" "1959" "Brazil"

Examples:
    python classify_assistant.py "The Bird with the Crystal Plumage (1970)" "Dario Argento" "Italian giallo"
    python classify_assistant.py "Antonio das Mortes (1969)" "" "Brazilian cinema"
    python classify_assistant.py "Thriller: A Cruel Picture (1974)" "" "Swedish exploitation"
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add lib/ to path for RAG imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.rag.query import query_docs


def parse_title_year(title_input: str) -> Tuple[str, Optional[int]]:
    """
    Extract title and year from input like "Film Title (Year)" or just "Film Title".

    Returns:
        (title, year) - year is None if not found
    """
    # Try to extract year in parentheses
    match = re.search(r'\((\d{4})\)', title_input)
    if match:
        year = int(match.group(1))
        title = re.sub(r'\s*\(\d{4}\)', '', title_input).strip()
        return title, year

    return title_input.strip(), None


def extract_decade(year: Optional[int]) -> Optional[str]:
    """Get decade string from year (e.g., 1975 → '1970s')."""
    if year is None:
        return None
    decade_start = (year // 10) * 10
    return f"{decade_start}s"


def format_query(title: str, year: Optional[int], director: str, context: str) -> str:
    """Build RAG query from film details."""
    parts = []

    if title:
        parts.append(title)
    if year:
        parts.append(f"from {year}")
    if director:
        parts.append(f"by {director}")
    if context:
        parts.append(context)

    return " ".join(parts)


def query_similar_films(title: str, director: str, year: Optional[int]) -> List[Dict]:
    """Query RAG for similar films in database."""
    if director:
        query = f"Films by {director}"
    elif year:
        decade = extract_decade(year)
        query = f"Films from {decade}"
    else:
        query = f"{title} similar films"

    # query_docs returns list of dicts with 'chunk', 'final_score', etc.
    results = query_docs(query, top_k=5)

    # Adapt to expected format
    adapted = []
    for r in results:
        chunk = r['chunk']
        adapted.append({
            'content': chunk.get('content', ''),
            'heading': chunk.get('heading', ''),
            'source': chunk.get('source_file', ''),
            'score': r['final_score'],
            'metadata': chunk.get('metadata', {})
        })
    return adapted


def query_category_match(context: str, year: Optional[int]) -> List[Dict]:
    """Query RAG for matching satellite categories."""
    decade = extract_decade(year) if year else ""
    query = f"{context} {decade} satellite category classification"

    # query_docs returns list of dicts with 'chunk', 'final_score', etc.
    results = query_docs(query, top_k=5)

    # Adapt to expected format
    adapted = []
    for r in results:
        chunk = r['chunk']
        adapted.append({
            'content': chunk.get('content', ''),
            'heading': chunk.get('heading', ''),
            'source': chunk.get('source_file', ''),
            'score': r['final_score'],
            'metadata': chunk.get('metadata', {})
        })
    return adapted


def extract_category_info(results: List[Dict]) -> List[Dict]:
    """Extract category information from RAG results."""
    categories = []

    for result in results:
        content = result.get('content', '')
        metadata = result.get('metadata', {})

        # Look for category definitions
        if 'category' in content.lower() or metadata.get('type') == 'category':
            category_info = {
                'name': None,
                'decades': None,
                'cap': None,
                'score': result.get('score', 0.0),
                'source': result.get('source', '')
            }

            # Extract category name from heading or content
            heading = result.get('heading', '')
            if heading:
                # Format: "1. GIALLO / ITALIAN HORROR-THRILLER"
                match = re.search(r'\d+\.\s+([A-Z][A-Z\s/\-]+)', heading)
                if match:
                    category_info['name'] = match.group(1).strip()

            # Extract decade boundaries
            decade_match = re.search(r'(\d{4}s)\s*[-–]\s*(\d{4}s)', content)
            if decade_match:
                category_info['decades'] = f"{decade_match.group(1)}-{decade_match.group(2)}"

            # Extract cap
            cap_match = re.search(r'[Cc]ap:\s*(\d+)', content)
            if cap_match:
                category_info['cap'] = int(cap_match.group(1))

            if category_info['name']:
                categories.append(category_info)

    return categories


def format_suggestions(
    title: str,
    year: Optional[int],
    director: str,
    similar_films: List[Dict],
    categories: List[Dict]
) -> str:
    """Format RAG suggestions as human-readable output."""
    output = []
    output.append("=" * 70)
    output.append("RAG CLASSIFICATION ASSISTANT")
    output.append("=" * 70)
    output.append("")

    # Film details
    output.append("Film Details:")
    output.append(f"  Title: {title}")
    if year:
        decade = extract_decade(year)
        output.append(f"  Year: {year} (Decade: {decade})")
    if director:
        output.append(f"  Director: {director}")
    output.append("")

    # Similar films in database
    if similar_films:
        output.append("Similar Films in Database:")
        film_entries = [r for r in similar_films if r.get('metadata', {}).get('type') == 'film_entry']

        if film_entries:
            for i, result in enumerate(film_entries[:5], 1):
                metadata = result.get('metadata', {})
                film_title = metadata.get('title', 'Unknown')
                film_year = metadata.get('year', '????')
                subdirectory = metadata.get('subdirectory', '')
                destination = metadata.get('destination', '')
                score = result.get('score', 0.0)

                output.append(f"  {i}. {film_title} ({film_year}) [Score: {score:.2f}]")
                output.append(f"     → {destination}")
                if subdirectory and subdirectory != film_title:
                    output.append(f"     Director/Category: {subdirectory}")
        else:
            output.append("  (No similar films found in database)")
        output.append("")

    # Category matches
    if categories:
        output.append("Matching Satellite Categories:")
        for i, cat in enumerate(categories[:3], 1):
            output.append(f"  {i}. {cat['name']} [Score: {cat['score']:.2f}]")
            if cat['decades']:
                # Check if year is within bounds
                if year:
                    valid = check_decade_bounds(year, cat['decades'])
                    status = "✓ Valid" if valid else "✗ Out of bounds"
                    output.append(f"     Decades: {cat['decades']} {status}")
                else:
                    output.append(f"     Decades: {cat['decades']}")
            if cat['cap']:
                output.append(f"     Cap: {cat['cap']} films")
            output.append(f"     Source: {cat['source']}")
        output.append("")
    else:
        output.append("Matching Satellite Categories:")
        output.append("  (No category matches found)")
        output.append("")

    # Suggested classification
    output.append("Suggested Classification:")
    suggestion = build_suggestion(title, year, director, similar_films, categories)
    if suggestion:
        output.append(f"  → {suggestion['path']}")
        output.append(f"  Confidence: {suggestion['confidence']}")
        output.append(f"  Reasoning: {suggestion['reason']}")
    else:
        output.append("  → Unsorted/ (insufficient context)")
        output.append("  Reasoning: Could not determine classification from RAG results")
    output.append("")

    output.append("=" * 70)
    output.append("Next Steps:")
    output.append("  1. Review RAG suggestions above")
    output.append("  2. Verify category boundaries and caps")
    output.append("  3. Update SORTING_DATABASE.md with classification")
    output.append("  4. Run: python classify.py <source_dir>")
    output.append("=" * 70)

    return "\n".join(output)


def check_decade_bounds(year: int, decade_range: str) -> bool:
    """Check if year falls within decade boundaries (e.g., '1960s-1980s')."""
    match = re.search(r'(\d{4})s\s*[-–]\s*(\d{4})s', decade_range)
    if not match:
        return False

    start_decade = int(match.group(1))
    end_decade = int(match.group(2))

    return start_decade <= year < end_decade + 10


def build_suggestion(
    title: str,
    year: Optional[int],
    director: str,
    similar_films: List[Dict],
    categories: List[Dict]
) -> Optional[Dict]:
    """Build classification suggestion from RAG results."""

    # Strategy 1: If director matches Core/Reference, use that
    film_entries = [r for r in similar_films if r.get('metadata', {}).get('type') == 'film_entry']
    if film_entries and director:
        for result in film_entries:
            metadata = result.get('metadata', {})
            subdirectory = metadata.get('subdirectory', '')
            destination = metadata.get('destination', '')

            # Check if director name appears in destination
            if director.lower() in subdirectory.lower():
                # Extract tier from destination
                if '/Core/' in destination:
                    decade = extract_decade(year) if year else '????s'
                    return {
                        'path': f"Core/{decade}/{director}/",
                        'confidence': 'High',
                        'reason': f'Director {director} found in Core tier'
                    }
                elif '/Reference/' in destination:
                    decade = extract_decade(year) if year else '????s'
                    return {
                        'path': f"Reference/{decade}/",
                        'confidence': 'High',
                        'reason': f'Similar films by {director} in Reference tier'
                    }

    # Strategy 2: If category match with valid decade, use that
    if categories and year:
        top_category = categories[0]
        if top_category['decades']:
            if check_decade_bounds(year, top_category['decades']):
                decade = extract_decade(year)
                category_name = top_category['name'].title().replace(' ', '_')
                return {
                    'path': f"Satellite/{category_name}/{decade}/",
                    'confidence': 'Medium-High',
                    'reason': f"Matches {top_category['name']} category (decades: {top_category['decades']})"
                }

    # Strategy 3: If similar films exist, suggest similar path
    if film_entries:
        top_result = film_entries[0]
        metadata = top_result.get('metadata', {})
        destination = metadata.get('destination', '')

        if destination:
            return {
                'path': destination,
                'confidence': 'Medium',
                'reason': f"Similar to {metadata.get('title', 'unknown film')}"
            }

    return None


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Parse arguments
    title_input = sys.argv[1] if len(sys.argv) > 1 else ""
    director = sys.argv[2] if len(sys.argv) > 2 else ""
    context = sys.argv[3] if len(sys.argv) > 3 else ""

    # Extract title and year
    title, year = parse_title_year(title_input)

    # If director is a year (e.g., "1959"), swap with year
    if director.isdigit() and len(director) == 4:
        year = int(director)
        director = ""

    if not title:
        print("Error: Film title required")
        print(__doc__)
        sys.exit(1)

    # Query RAG for suggestions
    print("Querying RAG knowledge base...")
    print("")

    similar_films = query_similar_films(title, director, year)
    category_results = query_category_match(context, year) if context else []
    categories = extract_category_info(category_results)

    # Format and display suggestions
    output = format_suggestions(title, year, director, similar_films, categories)
    print(output)


if __name__ == "__main__":
    main()
