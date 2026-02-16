"""Module entry point for python -m lib.rag.indexer and python -m lib.rag.query."""
import sys

if len(sys.argv) > 1 and sys.argv[0].endswith("indexer"):
    from .indexer import main
    main()
elif len(sys.argv) > 1 and sys.argv[0].endswith("query"):
    from .query import main
    main()
else:
    print("Usage:")
    print("  python -m lib.rag.indexer [--force]")
    print("  python -m lib.rag.query '<query>' [--top N] [--json]")
    sys.exit(1)
