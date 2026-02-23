#!/usr/bin/env python3
"""
scripts/curate.py — Curation execution tool (Issue #30)

Reads output/curation_decisions.csv (the curator's triage of the review queue)
and executes accept/override/enrich/defer actions.

Always dry-run by default. Use --execute to apply.

Input file format (output/curation_decisions.csv):
  filename,action,destination,director,country,notes
  "Film.mkv",accept,"","","","Confirmed"
  "Other.mkv",override,"Satellite/Giallo/1970s/","","","Actually giallo"
  "Unknown.mkv",enrich,"","Mario Bava","IT","Found on IMDb"
  "Weird.mkv",defer,"","","","Need to research"

Actions:
  accept   — Mark as confirmed in output/confirmed_films.csv (available for move.py)
  override — Append SORTING_DATABASE.md-format entry to output/sorting_database_additions.txt
  enrich   — Append to output/manual_enrichment.csv
  defer    — Re-queue in review_queue.csv with deferred=true (no file change in dry-run)

NEVER writes to docs/SORTING_DATABASE.md (human-curated, code reads only).

Usage:
    python scripts/curate.py                          # dry-run (default)
    python scripts/curate.py --execute                # apply actions
    python scripts/curate.py --decisions PATH         # custom decisions file
    python scripts/curate.py --config PATH            # custom config
"""

import sys
import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VALID_ACTIONS = {'accept', 'override', 'enrich', 'defer'}

DEFAULT_DECISIONS = Path('output/curation_decisions.csv')
CONFIRMED_FILMS   = Path('output/confirmed_films.csv')
SORTING_DB_ADDITIONS = Path('output/sorting_database_additions.txt')
MANUAL_ENRICHMENT = Path('output/manual_enrichment.csv')
REVIEW_QUEUE      = Path('output/review_queue.csv')


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_decisions(path: Path) -> List[Dict]:
    """Load curation_decisions.csv."""
    if not path.exists():
        logger.error(f"Decisions file not found: {path}")
        sys.exit(1)

    rows = []
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            action = row.get('action', '').strip().lower()
            if not action:
                logger.warning(f"Row {i}: empty action — skipping")
                continue
            if action not in VALID_ACTIONS:
                logger.warning(f"Row {i}: unknown action '{action}' — skipping")
                continue
            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def _do_accept(rows: List[Dict], dry_run: bool) -> int:
    """Append accepted films to output/confirmed_films.csv."""
    accepted = [r for r in rows if r['action'].strip().lower() == 'accept']
    if not accepted:
        return 0

    if dry_run:
        for r in accepted:
            logger.info(f"[DRY-RUN] ACCEPT: {r['filename']!r}")
        return len(accepted)

    CONFIRMED_FILMS.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CONFIRMED_FILMS.exists()
    with open(CONFIRMED_FILMS, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['filename', 'notes'],
            quoting=csv.QUOTE_ALL,
        )
        if write_header:
            writer.writeheader()
        for r in accepted:
            writer.writerow({'filename': r['filename'], 'notes': r.get('notes', '')})
            logger.info(f"ACCEPT: {r['filename']!r}")

    return len(accepted)


def _do_override(rows: List[Dict], dry_run: bool) -> int:
    """Append SORTING_DATABASE.md-format entries to sorting_database_additions.txt."""
    overrides = [r for r in rows if r['action'].strip().lower() == 'override']
    if not overrides:
        return 0

    if dry_run:
        for r in overrides:
            dest = r.get('destination', '').strip()
            logger.info(f"[DRY-RUN] OVERRIDE: {r['filename']!r} → {dest!r}")
        return len(overrides)

    SORTING_DB_ADDITIONS.parent.mkdir(parents=True, exist_ok=True)
    with open(SORTING_DB_ADDITIONS, 'a', encoding='utf-8') as f:
        for r in overrides:
            filename = r['filename'].strip()
            dest = r.get('destination', '').strip()
            notes = r.get('notes', '').strip()
            # Extract title and year from filename for SORTING_DATABASE format
            # Best-effort: curator should verify before pasting into SORTING_DATABASE.md
            line = f"- {filename} → {dest}/"
            if notes:
                line += f"  # {notes}"
            f.write(line + "\n")
            logger.info(f"OVERRIDE: {filename!r} → {dest!r}")

    return len(overrides)


def _do_enrich(rows: List[Dict], dry_run: bool) -> int:
    """Append curator-provided metadata to output/manual_enrichment.csv."""
    enrichments = [r for r in rows if r['action'].strip().lower() == 'enrich']
    if not enrichments:
        return 0

    if dry_run:
        for r in enrichments:
            logger.info(
                f"[DRY-RUN] ENRICH: {r['filename']!r}"
                f" director={r.get('director', '')!r}"
                f" country={r.get('country', '')!r}"
            )
        return len(enrichments)

    MANUAL_ENRICHMENT.parent.mkdir(parents=True, exist_ok=True)
    write_header = not MANUAL_ENRICHMENT.exists()
    with open(MANUAL_ENRICHMENT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['filename', 'director', 'country', 'genres'],
            quoting=csv.QUOTE_ALL,
        )
        if write_header:
            writer.writeheader()
        for r in enrichments:
            writer.writerow({
                'filename': r['filename'],
                'director': r.get('director', ''),
                'country': r.get('country', ''),
                'genres': r.get('genres', ''),
            })
            logger.info(f"ENRICH: {r['filename']!r}")

    return len(enrichments)


def _do_defer(rows: List[Dict], dry_run: bool) -> int:
    """Log deferred films. They remain in the review queue for the next cycle."""
    deferred = [r for r in rows if r['action'].strip().lower() == 'defer']
    if not deferred:
        return 0

    for r in deferred:
        notes = r.get('notes', '').strip()
        msg = f"DEFER: {r['filename']!r}"
        if notes:
            msg += f" ({notes})"
        if dry_run:
            logger.info(f"[DRY-RUN] {msg}")
        else:
            logger.info(msg)

    return len(deferred)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(rows: List[Dict], dry_run: bool, counts: Dict[str, int]):
    label = "[DRY-RUN] " if dry_run else ""
    total = len(rows)
    print(f"\n{'=' * 60}")
    print(f"{label}CURATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total decisions: {total}")
    for action in ('accept', 'override', 'enrich', 'defer'):
        n = counts.get(action, 0)
        print(f"  {action:10s}: {n}")
    if dry_run:
        print("\n(No files were modified — re-run with --execute to apply)")
    else:
        print(f"\nOutputs written to:")
        if counts.get('accept'):
            print(f"  {CONFIRMED_FILMS}")
        if counts.get('override'):
            print(f"  {SORTING_DB_ADDITIONS}")
        if counts.get('enrich'):
            print(f"  {MANUAL_ENRICHMENT}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Curation execution tool — process review queue decisions (Issue #30)',
        epilog="""
NEVER modifies docs/SORTING_DATABASE.md directly.
Override entries are staged in output/sorting_database_additions.txt for manual review.

Always dry-run by default. Use --execute to apply.
        """
    )
    parser.add_argument(
        '--execute', action='store_true',
        help='Apply actions (default: dry-run only)',
    )
    parser.add_argument(
        '--decisions', type=Path, default=DEFAULT_DECISIONS,
        help=f'Path to curation decisions CSV (default: {DEFAULT_DECISIONS})',
    )
    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        logger.info("DRY-RUN mode — no files will be modified (use --execute to apply)")

    rows = load_decisions(args.decisions)
    if not rows:
        logger.warning("No valid decisions found.")
        return 0

    logger.info(f"Loaded {len(rows)} decisions from {args.decisions}")

    counts = {
        'accept':   _do_accept(rows, dry_run),
        'override': _do_override(rows, dry_run),
        'enrich':   _do_enrich(rows, dry_run),
        'defer':    _do_defer(rows, dry_run),
    }

    print_summary(rows, dry_run, counts)
    return 0


if __name__ == '__main__':
    sys.exit(main())
