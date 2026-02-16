"""CLI and programmatic query interface."""
import argparse
import json
import sys
from typing import List, Dict, Any, Optional

from . import config
from .retriever import RAGRetriever


def query_docs(
    query_text: str,
    top_k: int = config.DEFAULT_TOP_K,
    filter_status: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Programmatic query interface.

    Usage:
        from lib.rag.query import query_docs
        results = query_docs("How does authentication work?", top_k=3)
        for result in results:
            print(result["section_reference"])

    Args:
        query_text: Natural language query
        top_k: Number of results to return
        filter_status: Optional status filter (e.g., ["AUTHORITATIVE"])

    Returns:
        List of result dicts with chunks and scores
    """
    retriever = RAGRetriever()
    return retriever.query(query_text, top_k, filter_status)


def print_results_table(results: List[Dict[str, Any]]):
    """Print results in human-readable format."""
    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results, start=1):
        chunk = result["chunk"]
        score = result["final_score"]
        ref = result["section_reference"]
        status = chunk["metadata"].get("status", "unmarked")
        source = chunk["source_file"]
        line_range = chunk["line_range"]

        status_str = f"({status})" if status != "unmarked" else ""

        print(f"\n{i}. [{score:.2f}] {ref} {status_str}")
        print(f"   {source}:{line_range[0]}-{line_range[1]}")

        sem_score = result["semantic_score"]
        kw_score = result["keyword_score"]
        auth_score = result["authority_score"]
        print(f"   semantic={sem_score:.2f}, keyword={kw_score:.2f}, authority={auth_score:.2f}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Query RAG documentation index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m lib.rag.query "How does authentication work?"
  python -m lib.rag.query "deployment procedure" --top 10
  python -m lib.rag.query "API contracts" --filter AUTHORITATIVE
  python -m lib.rag.query "error handling" --json
        """
    )
    parser.add_argument(
        "query",
        help="Natural language query"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=config.DEFAULT_TOP_K,
        help=f"Number of results to return (default: {config.DEFAULT_TOP_K})"
    )
    parser.add_argument(
        "--filter",
        choices=["AUTHORITATIVE", "STABLE", "unmarked", "ARCHIVED"],
        nargs="+",
        help="Filter by document status"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if not config.INDEX_FILE.exists():
        print("Error: RAG index not found")
        print("Build index with: python -m lib.rag.indexer")
        sys.exit(1)

    try:
        results = query_docs(
            args.query,
            top_k=args.top,
            filter_status=args.filter
        )
    except Exception as e:
        print(f"Error during query: {e}")
        sys.exit(1)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nQuery: \"{args.query}\"")
        print(f"Top {args.top} results:\n")
        print_results_table(results)


if __name__ == "__main__":
    main()
