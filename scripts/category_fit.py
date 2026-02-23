#!/usr/bin/env python3
"""
scripts/category_fit.py — Category fit detector (Issue #33)

Cross-scores low-fit Satellite films against all categories to detect:
  - CORE_CANDIDATE: director in Core whitelist → should exit Satellite entirely
  - REROUTE: better home exists in another category (score delta >= 2)
  - NO_FIT: no better home — potential missing category

Groups NO_FIT films by country/decade to surface missing-category clusters.

NEVER moves files. Read-only diagnostic tool.

Usage:
    python scripts/category_fit.py                          # all Satellite categories
    python scripts/category_fit.py --category "Pinku Eiga"
    python scripts/category_fit.py --threshold 3            # widen to score <= 3
    python scripts/category_fit.py --output output/category_fit_report.md
"""

import sys
import csv
import argparse
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))
# scripts/ dir on path for sibling import
sys.path.insert(0, str(Path(__file__).parent))

from lib.parser import FilenameParser
from lib.core_directors import CoreDirectorDatabase
from lib.constants import SATELLITE_ROUTING_RULES

# Import scoring infrastructure from rank_category_tentpoles — no duplication
from rank_category_tentpoles import score_film, make_cache_key, load_json_cache


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all_satellite_films(audit_path: Path) -> Dict[str, List[Dict]]:
    """Load all Satellite films from library_audit.csv, grouped by category."""
    by_category: Dict[str, List[Dict]] = defaultdict(list)
    with open(audit_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('tier') == 'Satellite' and row.get('subdirectory'):
                by_category[row['subdirectory']].append(row)
    return dict(by_category)


def get_country_from_cache(title: str, year: Optional[int],
                           omdb_cache: Dict) -> Optional[str]:
    """Get primary country code from OMDb cache for a film."""
    key = make_cache_key(title, year)
    omdb_data = omdb_cache.get(key)
    if omdb_data:
        countries = omdb_data.get('countries') or []
        if countries:
            return countries[0]
    return None


# ---------------------------------------------------------------------------
# Core analysis logic
# ---------------------------------------------------------------------------

def classify_outcome(current_score: int, best_alt_score: int,
                     is_core: bool) -> str:
    if is_core:
        return 'CORE_CANDIDATE'
    if best_alt_score >= current_score + 2:
        return 'REROUTE'
    return 'NO_FIT'


def analyze_category(category: str, films: List[Dict],
                     threshold: int,
                     tmdb_cache: Dict, omdb_cache: Dict,
                     core_db: CoreDirectorDatabase,
                     all_categories: List[str],
                     parser: FilenameParser) -> Dict:
    """Analyze films in one category. Returns structured results dict."""
    low_fit = []
    no_score = []

    for row in films:
        filename = row['filename']
        decade = row.get('decade') or None

        try:
            metadata = parser.parse(filename)
        except Exception:
            no_score.append(filename)
            continue

        if not metadata.title or not metadata.year:
            no_score.append(filename)
            continue

        current_result = score_film(
            filename=filename,
            title=metadata.title,
            year=metadata.year,
            director=metadata.director,
            decade=decade,
            category=category,
            tmdb_cache=tmdb_cache,
            omdb_cache=omdb_cache,
            core_db=core_db,
        )

        if current_result is None:
            no_score.append(filename)
            continue

        if current_result['score'] > threshold:
            continue  # Good fit — skip

        director = current_result['director']
        is_core = bool(director and core_db.is_core_director(director))

        # Cross-score against all other categories
        best_alt_cat = None
        best_alt_score = 0

        for other_cat in all_categories:
            if other_cat == category:
                continue
            alt_result = score_film(
                filename=filename,
                title=metadata.title,
                year=metadata.year,
                director=metadata.director,
                decade=decade,
                category=other_cat,
                tmdb_cache=tmdb_cache,
                omdb_cache=omdb_cache,
                core_db=core_db,
            )
            if alt_result and alt_result['score'] > best_alt_score:
                best_alt_score = alt_result['score']
                best_alt_cat = other_cat

        outcome = classify_outcome(current_result['score'], best_alt_score, is_core)

        # Country: OMDb cache > audit CSV
        country = get_country_from_cache(metadata.title, metadata.year, omdb_cache)
        if not country:
            country = row.get('country') or '?'

        low_fit.append({
            'filename': filename,
            'title': current_result['title'],
            'year': metadata.year,
            'director': director,
            'decade': decade or '?',
            'country': country,
            'current_score': current_result['score'],
            'best_alt_cat': best_alt_cat,
            'best_alt_score': best_alt_score,
            'outcome': outcome,
        })

    return {
        'category': category,
        'total': len(films),
        'low_fit': low_fit,
        'no_score': no_score,
    }


def group_no_fit_clusters(no_fits: List[Dict]) -> Dict[Tuple, List[Dict]]:
    """Group NO_FIT films by (country, decade) for missing-category detection."""
    clusters: Dict[Tuple, List[Dict]] = defaultdict(list)
    for film in no_fits:
        key = (film['country'], film['decade'])
        clusters[key].append(film)
    return dict(clusters)


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(results: List[Dict], threshold: int) -> str:
    lines = [
        '# Category Fit Report',
        f'*Generated {datetime.date.today()} | threshold: score ≤ {threshold}*',
        '',
        '**Outcome types:**',
        '- `CORE_CANDIDATE` — director in Core whitelist; should exit Satellite',
        '- `REROUTE` — better home in existing category (delta ≥ 2)',
        '- `NO_FIT` — no better home; cluster = missing category signal',
        '',
        '---',
        '',
    ]

    for result in results:
        category = result['category']
        low_fit = result['low_fit']
        total = result['total']

        if not low_fit:
            lines.append(f'## {category} — all {total} films fit (no score ≤ {threshold})')
            lines.append('')
            lines.append('---')
            lines.append('')
            continue

        lines.append(f'## {category} — {len(low_fit)} low-fit films (of {total} total)')
        lines.append('')

        core_candidates = [f for f in low_fit if f['outcome'] == 'CORE_CANDIDATE']
        reroutes = [f for f in low_fit if f['outcome'] == 'REROUTE']
        no_fits = [f for f in low_fit if f['outcome'] == 'NO_FIT']

        if core_candidates:
            lines.append(f'### CORE_CANDIDATE ({len(core_candidates)})')
            lines.append('')
            for film in sorted(core_candidates, key=lambda f: (f['year'] or 0)):
                lines.append(f'  **{film["title"]} ({film["year"]})** — {film["director"]}')
                lines.append(f'  → Core director. Move to Core/{film["decade"]}/{film["director"]}/')
                lines.append(f'  Score: {film["current_score"]}')
                lines.append('')

        if reroutes:
            lines.append(f'### REROUTE ({len(reroutes)})')
            lines.append('')
            for film in sorted(reroutes, key=lambda f: -(f['best_alt_score'] - f['current_score'])):
                delta = film['best_alt_score'] - film['current_score']
                lines.append(f'  **{film["title"]} ({film["year"]})** — {film["director"]}')
                lines.append(
                    f'  → {film["best_alt_cat"]} scores {film["best_alt_score"]} '
                    f'vs current {film["current_score"]}. Delta: +{delta}'
                )
                lines.append('')

        if no_fits:
            lines.append(f'### NO_FIT — potential missing category ({len(no_fits)})')
            lines.append('')
            for film in sorted(no_fits, key=lambda f: (f['country'], f['decade'], f['year'] or 0)):
                lines.append(
                    f'  {film["title"]} ({film["year"]}) — '
                    f'{film["director"] or "unknown director"} — '
                    f'{film["country"]} {film["decade"]} — score {film["current_score"]}'
                )
            lines.append('')

            clusters = group_no_fit_clusters(no_fits)
            if clusters:
                lines.append('  **Clusters by country/decade:**')
                for (country, decade), cluster_films in sorted(
                        clusters.items(), key=lambda x: -len(x[1])):
                    lines.append(f'  {country} / {decade} / {len(cluster_films)} films')
                    if len(cluster_films) >= 3:
                        lines.append(f'  → **Possible missing category**: {country} {decade} cinema')
                lines.append('')

        if result['no_score']:
            lines.append(
                f'*{len(result["no_score"])} film(s) could not be scored (no parseable title/year)*'
            )
            lines.append('')

        lines.append('---')
        lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    arg_parser = argparse.ArgumentParser(
        description='Cross-score low-fit Satellite films to detect misroutes and missing categories (Issue #33)'
    )
    arg_parser.add_argument('--category', help='Single category to analyze (default: all)')
    arg_parser.add_argument(
        '--threshold', type=int, default=2,
        help='Score threshold for "low-fit" films (default: 2, i.e. score ≤ 2)'
    )
    arg_parser.add_argument('--output', help='Write report to file (default: stdout)')
    arg_parser.add_argument('--audit', default='output/library_audit.csv',
                            help='Path to library_audit.csv')
    arg_parser.add_argument('--config', default='config.yaml')
    args = arg_parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"Error: {audit_path} not found — run audit.py first", file=sys.stderr)
        sys.exit(1)

    # Load caches ($0 — read-only, no network calls)
    tmdb_cache = load_json_cache(Path('output/tmdb_cache.json'))
    omdb_cache = load_json_cache(Path('output/omdb_cache.json'))
    print(
        f"Loaded TMDb cache ({len(tmdb_cache)} entries), OMDb cache ({len(omdb_cache)} entries)",
        file=sys.stderr
    )

    # Load Core director DB
    config_path = Path(args.config)
    if not config_path.exists():
        config_path = Path('config_external.yaml')
    import yaml
    config = yaml.safe_load(open(config_path))
    project_path = Path(config['project_path'])
    core_db = CoreDirectorDatabase(project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md')

    # Load all Satellite films from audit CSV
    all_satellite = load_all_satellite_films(audit_path)
    all_categories = list(SATELLITE_ROUTING_RULES.keys())

    # Determine which categories to analyze
    if args.category:
        if args.category not in all_satellite:
            avail = ', '.join(sorted(all_satellite.keys()))
            print(f"Error: '{args.category}' not found in audit CSV.", file=sys.stderr)
            print(f"Available Satellite categories: {avail}", file=sys.stderr)
            sys.exit(1)
        categories_to_analyze = [args.category]
    else:
        # Analyze all categories present in audit CSV (in SATELLITE_ROUTING_RULES order)
        categories_to_analyze = [c for c in all_categories if c in all_satellite]
        # Also pick up any Satellite films in categories not yet in SATELLITE_ROUTING_RULES
        extra = [c for c in all_satellite if c not in all_categories]
        categories_to_analyze += extra

    film_parser = FilenameParser()
    results = []

    for cat in categories_to_analyze:
        films = all_satellite.get(cat, [])
        print(f"Analyzing {cat} ({len(films)} films, threshold ≤ {args.threshold})...",
              file=sys.stderr)

        result = analyze_category(
            category=cat,
            films=films,
            threshold=args.threshold,
            tmdb_cache=tmdb_cache,
            omdb_cache=omdb_cache,
            core_db=core_db,
            all_categories=all_categories,
            parser=film_parser,
        )
        results.append(result)

        # Progress summary to stderr
        lf = result['low_fit']
        core_n = sum(1 for f in lf if f['outcome'] == 'CORE_CANDIDATE')
        reroute_n = sum(1 for f in lf if f['outcome'] == 'REROUTE')
        nofit_n = sum(1 for f in lf if f['outcome'] == 'NO_FIT')
        print(
            f"  {len(lf)} low-fit: {core_n} CORE_CANDIDATE, {reroute_n} REROUTE, {nofit_n} NO_FIT",
            file=sys.stderr
        )

    report = format_report(results, args.threshold)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding='utf-8')
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(report)


if __name__ == '__main__':
    main()
