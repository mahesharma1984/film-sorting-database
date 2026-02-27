#!/usr/bin/env python3
"""
scripts/rank_category_tentpoles.py — Satellite category tentpole ranking (Issue #30)

Scores every film in each Satellite category 0–13 across 7 dimensions and outputs
a ranked markdown report with Category Core / Reference / Texture tiers.

NEVER moves files. Read-only tool.

Usage:
    python scripts/rank_category_tentpoles.py Giallo
    python scripts/rank_category_tentpoles.py --all
    python scripts/rank_category_tentpoles.py --all --output output/tentpole_rankings.md
    python scripts/rank_category_tentpoles.py Giallo --wikipedia
"""

import sys
import csv
import json
import re
import argparse
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import FilenameParser
from lib.core_directors import CoreDirectorDatabase
from lib.normalization import normalize_for_lookup, strip_release_tags
from lib.constants import SATELLITE_ROUTING_RULES, SATELLITE_TENTPOLES
from lib.corpus import CorpusLookup

# ---------------------------------------------------------------------------
# Sight & Sound 2022 — films plausibly in Satellite categories
# Full 250-film list not needed; these are the Satellite-relevant entries.
# Format: frozenset of (normalized_title, year) tuples
# ---------------------------------------------------------------------------
SIGHT_AND_SOUND_2022 = frozenset([
    # Japanese New Wave
    ('in the realm of the senses', 1976),
    # Giallo / Italian Horror
    ('suspiria', 1977),
    # French New Wave
    ('breathless', 1960), ('a bout de souffle', 1960),
    ('the 400 blows', 1959), ('les quatre cents coups', 1959),
    ('vivre sa vie', 1962), ('cleo from 5 to 7', 1962),
    ('hiroshima mon amour', 1959),
    ('last year at marienbad', 1961),
    ('the soft skin', 1964),
    # Hong Kong Action
    ('chungking express', 1994),
    # Classic Hollywood
    ('citizen kane', 1941),
    ('vertigo', 1958),
    ('sunset blvd', 1950), ('sunset boulevard', 1950),
    ('the searchers', 1956),
    ('singin in the rain', 1952),
    ('some like it hot', 1959),
    ('all about eve', 1950),
    ('the best years of our lives', 1946),
    ('double indemnity', 1944),
    ('rear window', 1954),
    ('the wizard of oz', 1939),
    ('gone with the wind', 1939),
    ('casablanca', 1942),
    ('stagecoach', 1939),
    ('the lady eve', 1941),
    ('how green was my valley', 1941),
    ('the philadelphia story', 1940),
    # American New Hollywood
    ('nashville', 1975),
    ('mccabe and mrs miller', 1971),
    ('chinatown', 1974),
    ('the godfather', 1972),
    ('apocalypse now', 1979),
    ('dog day afternoon', 1975),
    ('the conversation', 1974),
    # Blaxploitation
    ('shaft', 1971),
    # Indie Cinema
    ('do the right thing', 1989),
    ('blue velvet', 1986),
    ('mulholland drive', 2001),
    ('lost highway', 1997),
    ('stranger than paradise', 1984),
    ('the piano', 1993),
    ('happy together', 1997),
    ('in the mood for love', 2000),
    ('yi yi', 2000),
    ('close-up', 1990),
    ('a separation', 2011),
    ('4 months 3 weeks and 2 days', 2007),
    ('the death of mr lazarescu', 2005),
    ('caché', 2005), ('cache', 2005), ('hidden', 2005),
    ('the white ribbon', 2009),
    ('uncle boonmee who can recall his past lives', 2010),
    ('tree of life', 2011),
    ('boyhood', 2014),
    # Music Films
    # (few S&S entries here)
])

# ---------------------------------------------------------------------------
# Peak decades per category (defines decade_match=2 vs =1)
# ---------------------------------------------------------------------------
PEAK_DECADES: Dict[str, Optional[List[str]]] = {
    'Giallo': ['1970s'],
    'Pinku Eiga': ['1970s'],
    'Japanese Exploitation': ['1970s'],
    'Brazilian Exploitation': ['1970s', '1980s'],
    'Hong Kong New Wave': ['1980s', '1990s'],
    'Hong Kong Category III': ['1990s'],
    'Hong Kong Action': ['1980s'],
    'American Exploitation': ['1970s'],
    'American New Hollywood': ['1970s'],
    'European Sexploitation': ['1970s'],
    'Blaxploitation': ['1970s'],
    'French New Wave': ['1960s'],
    'Japanese New Wave': ['1960s', '1970s'],
    'Classic Hollywood': ['1940s', '1950s'],
    'Music Films': None,    # No peak — any decade scores 2
    'Indie Cinema': None,   # No peak — any decade scores 2
}

# Satellite category caps (from satellite.py + SATELLITE_CATEGORIES.md)
CATEGORY_CAPS = {
    'Giallo': 30,
    'Pinku Eiga': 35,
    'Japanese Exploitation': 25,
    'Brazilian Exploitation': 45,
    'Hong Kong New Wave': 15,
    'Hong Kong Category III': 10,
    'Hong Kong Action': 65,
    'American Exploitation': 80,
    'European Sexploitation': 25,
    'Blaxploitation': 20,
    'Music Films': 20,
    'French New Wave': 30,
    'Japanese New Wave': 15,
    'Indie Cinema': 40,
    'Classic Hollywood': 25,
    'American New Hollywood': 25,
}

# ---------------------------------------------------------------------------
# Ranking-specific keyword sets — broader than routing tmdb_tags.
# Routing tags are high-precision (avoid false positives across all countries/decades).
# Ranking tags are used WITHIN a category, so false positives don't matter —
# we're scoring films already confirmed in the category.
# ---------------------------------------------------------------------------
RANKING_TAGS: Dict[str, List[str]] = {
    'Giallo': [
        'giallo', 'italian horror', 'psychosexual thriller', 'black-gloved killer',
        # Broader genre vocabulary that actually appears in TMDb keywords:
        'slasher', 'gore', 'murder', 'murder mystery', 'whodunit', 'mystery',
        'serial killer', 'axe murder', 'video nasty', 'italian thriller',
        'black gloves', 'proto-slasher', 'suspense', 'voyeurism', 'fetishism',
    ],
    'French New Wave': [
        'nouvelle vague', 'french new wave', 'new wave', 'cinéma vérité', 'cinema verite',
        'existentialism', 'alienation', 'paris', 'france', 'counter-culture',
        'improvisation', 'jump cut', 'handheld camera', 'social commentary',
        'rebellion', 'youth culture', 'romance', 'philosophical',
    ],
    'American New Hollywood': [
        'new hollywood', 'american new wave', 'counterculture', 'post-code',
        'vietnam war', 'anti-hero', 'corruption', 'disillusionment', 'cynicism',
        'revisionist', 'independent spirit', 'road movie', 'drug use',
        'political film', 'social critique', 'crime', 'heist',
    ],
    'Blaxploitation': [
        'blaxploitation', 'african american', 'inner city', 'black power',
        'ghetto', 'pimp', 'drug dealer', 'soul music', 'funk', 'vigilante',
        'racial politics', 'urban', 'exploitation',
    ],
    'Hong Kong New Wave': [
        'hong kong new wave', 'new wave', 'pre-handover', 'hong kong cinema',
        'social realism', 'melodrama', 'romance', 'urban life', 'nostalgia',
        'cantonese', 'colonial hong kong', 'art film', 'drama',
    ],
    'Hong Kong Category III': [
        'category iii', 'category 3', 'hong kong category iii', 'erotic horror',
        'supernatural', 'erotic', 'ghost', 'exploitation', 'adult',
    ],
    'Hong Kong Action': [
        'martial arts', 'wuxia', 'kung fu', 'triad', 'heroic bloodshed',
        'shaw brothers', 'hong kong action', 'sword fight', 'action',
        'gun fu', 'gangster', 'brotherhood', 'honour',
    ],
    'Pinku Eiga': [
        'pink film', 'pinku', 'japanese erotica', 'roman porno', 'exploitation',
        'erotic', 'sexuality', 'taboo', 'censored', 'nikkatsu', 'rape',
    ],
    'Japanese Exploitation': [
        'yakuza', 'japanese exploitation', 'toei', 'chambara', 'sword',
        'samurai', 'gangster', 'crime', 'violence', 'japanese crime',
    ],
    'Brazilian Exploitation': [
        'pornochanchada', 'brazilian exploitation', 'chanchada', 'erotic comedy',
        'sexuality', 'censorship', 'brazil', 'embrafilme', 'exploitation',
    ],
    'European Sexploitation': [
        'sexploitation', 'european erotica', 'soft core', 'softcore',
        'erotic', 'nudity', 'sexuality', 'europe', 'adult film',
    ],
    'American Exploitation': [
        'american exploitation', 'drive-in', 'grindhouse', 'b-movie',
        'violence', 'gore', 'exploitation', 'low budget', 'cult film',
        'roughie', 'women in prison', 'biker film',
    ],
    'Classic Hollywood': [
        'classic hollywood', 'golden age', 'studio system', 'film noir',
        'screwball comedy', 'musical', 'western', 'melodrama', 'noir',
        'black and white', 'hays code', 'pre-code', '1940s', '1950s',
    ],
    'Music Films': [
        'concert film', 'documentary', 'music', 'rock', 'jazz', 'blues',
        'musician', 'band', 'performance', 'live music', 'backstage',
    ],
    'Japanese New Wave': [
        'japanese new wave', 'nuberu bagu', 'political cinema', 'underground film',
        'avant-garde', 'new wave', 'rebellion', 'social critique', 'nikkatsu',
        'shochiku', 'counter-culture', 'student protest', 'protest film',
        'experimental', 'political film', 'anti-war',
    ],
    'Indie Cinema': [
        'independent film', 'art house', 'arthouse', 'festival film',
        'low budget', 'auteur', 'social realism', 'drama', 'character study',
    ],
}


# ---------------------------------------------------------------------------
# Cache loader
# ---------------------------------------------------------------------------

def load_json_cache(path: Path) -> Dict:
    if path.exists():
        try:
            return json.load(open(path, 'r', encoding='utf-8'))
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# Title cleaning (mirrors classify.py._clean_title_for_api)
# ---------------------------------------------------------------------------

_RESIDUAL_PATTERNS = [
    re.compile(r'\b(metro|pc|sr|moc|kl|doc|vo)\b', re.IGNORECASE),
    re.compile(r'\b\d{3,4}p\b', re.IGNORECASE),
    re.compile(r'\b(spanish|french|italian|german|japanese|chinese|vostfr)\b', re.IGNORECASE),
    re.compile(r'\b(itunes|upscale|uncensored|satrip|vhsrip|xvid|mp3|2audio)\b', re.IGNORECASE),
]


def clean_title_for_cache(title: str) -> str:
    """Strip release tags to build the same cache key as classify.py._clean_title_for_api."""
    clean = title
    # Strip user tag brackets [...] and {imdb-tt...} markers
    clean = re.sub(r'\s*\[.+?\]\s*', ' ', clean)
    clean = re.sub(r'\s*\{[^}]+\}\s*', ' ', clean)
    clean = strip_release_tags(clean)
    for pat in _RESIDUAL_PATTERNS:
        clean = pat.sub('', clean)
    clean = re.sub(r'\s*\(\s*\)', '', clean)
    return ' '.join(clean.split()).strip()


def make_cache_key(title: str, year: Optional[int]) -> str:
    return f"{clean_title_for_cache(title)}|{year if year else 'None'}"


# ---------------------------------------------------------------------------
# Director matching helpers
# ---------------------------------------------------------------------------

def _director_name_matches(director: Optional[str], pattern: str) -> bool:
    """Case-insensitive substring match: pattern 'bava' matches 'Mario Bava'."""
    if not director:
        return False
    return pattern.lower() in director.lower()


def _tentpole_directors(category: str) -> List[str]:
    """Return lowercase director name fragments from SATELLITE_TENTPOLES for this category."""
    tentpoles = SATELLITE_TENTPOLES.get(category, [])
    # Each entry is (title, year, director) — extract last-name fragment
    result = []
    for _, _, director in tentpoles:
        # Use full name lowercased for matching
        result.append(director.lower())
    return result


def score_director_tier(director: Optional[str], category: str,
                        core_db: CoreDirectorDatabase) -> int:
    """Score 0–3 for director_tier dimension."""
    if not director:
        return 0

    # Score 3: director in SATELLITE_TENTPOLES for this category
    tentpole_directors = _tentpole_directors(category)
    dir_lower = director.lower()
    for td in tentpole_directors:
        # Match if any word from tentpole director name appears in the film's director
        # or the film's director appears in the tentpole director name
        td_parts = td.split()
        if any(part in dir_lower for part in td_parts if len(part) > 3):
            return 3

    # Score 2: director in SATELLITE_ROUTING_RULES[category]['directors']
    routing_directors = SATELLITE_ROUTING_RULES.get(category, {}).get('directors', [])
    for rd in routing_directors:
        if rd.lower() in dir_lower or dir_lower in rd.lower():
            return 2

    # Score 1: director in Core whitelist
    if core_db.is_core_director(director):
        return 1

    return 0


# ---------------------------------------------------------------------------
# Scoring dimensions
# ---------------------------------------------------------------------------

def score_decade_match(decade: Optional[str], category: str) -> int:
    if not decade:
        return 0
    peak = PEAK_DECADES.get(category)
    if peak is None:
        return 2  # No peak defined — all valid decades score 2
    if decade in peak:
        return 2
    valid_decades = SATELLITE_ROUTING_RULES.get(category, {}).get('decades') or []
    if decade in valid_decades:
        return 1
    return 0


def score_keyword_alignment(tmdb_data: Optional[Dict], category: str) -> int:
    if not tmdb_data:
        return 0
    film_keywords = set(k.lower() for k in tmdb_data.get('keywords', []))
    if not film_keywords:
        return 0
    # Use RANKING_TAGS (broader) when available, fall back to routing tmdb_tags.
    # RANKING_TAGS are safe here because we're scoring films already IN the category.
    ranking_tags = RANKING_TAGS.get(category)
    if ranking_tags:
        category_tags = set(t.lower() for t in ranking_tags)
    else:
        category_tags = set(
            t.lower() for t in
            SATELLITE_ROUTING_RULES.get(category, {}).get('keyword_signals', {}).get('tmdb_tags', [])
        )
    hits = len(film_keywords & category_tags)
    return 2 if hits >= 3 else (1 if hits >= 1 else 0)


def score_canonical_recognition(tmdb_data: Optional[Dict], omdb_data: Optional[Dict]) -> int:
    vote_count = None
    if tmdb_data:
        vote_count = tmdb_data.get('vote_count')
    if vote_count is None and omdb_data:
        vote_count = omdb_data.get('vote_count')
    if vote_count and int(vote_count) >= 1000:
        return 1
    return 0


def score_text_signal(tmdb_data: Optional[Dict], omdb_data: Optional[Dict],
                      category: str) -> int:
    text_blob = ''
    if tmdb_data:
        text_blob += ' ' + (tmdb_data.get('overview') or '')
        text_blob += ' ' + (tmdb_data.get('tagline') or '')
    if omdb_data:
        text_blob += ' ' + (omdb_data.get('plot') or '')
    text_blob = text_blob.lower()
    if not text_blob.strip():
        return 0

    text_terms = SATELLITE_ROUTING_RULES.get(category, {}).get('keyword_signals', {}).get('text_terms', [])
    hits = sum(1 for term in text_terms if term.lower() in text_blob)
    return 1 if hits >= 2 else 0


def score_external_canonical(title: Optional[str], year: Optional[int],
                              filename: str, wikipedia_films: Optional[List[str]] = None) -> int:
    score = 0

    # Sight & Sound 2022: +2
    if title and year:
        norm = normalize_for_lookup(title, strip_format_signals=True).lower()
        if (norm, year) in SIGHT_AND_SOUND_2022 or (title.lower(), year) in SIGHT_AND_SOUND_2022:
            score += 2

    # Criterion: +1 (check original filename before normalization)
    if 'criterion' in filename.lower():
        score += 1

    # Wikipedia genre list: +1 (optional)
    if wikipedia_films and title:
        title_lower = title.lower()
        for wf in wikipedia_films:
            if title_lower in wf.lower() or wf.lower() in title_lower:
                score += 1
                break

    return min(score, 3)


def score_corpus_tier(title: Optional[str], year: Optional[int],
                      imdb_id: Optional[str], corpus_lookup: Optional[CorpusLookup]) -> int:
    """
    Score based on canonical tier in ground truth corpus (Issue #38).
    tier 1 (core canon)       → 3 points
    tier 2 (important ref)    → 2 points
    tier 3 (genre texture)    → 1 point
    not in corpus             → 0 points
    """
    if not corpus_lookup or not title or not year:
        return 0
    hit = corpus_lookup.lookup(title, year, imdb_id=imdb_id)
    if not hit:
        return 0
    return {1: 3, 2: 2, 3: 1}.get(hit['canonical_tier'], 0)


# ---------------------------------------------------------------------------
# Wikipedia fetch (optional --wikipedia flag)
# ---------------------------------------------------------------------------

WIKIPEDIA_CATEGORY_URLS = {
    'Giallo': 'https://en.wikipedia.org/wiki/Giallo',
    'French New Wave': 'https://en.wikipedia.org/wiki/French_New_Wave',
    'American New Hollywood': 'https://en.wikipedia.org/wiki/New_Hollywood',
    'Blaxploitation': 'https://en.wikipedia.org/wiki/Blaxploitation',
    'Hong Kong New Wave': 'https://en.wikipedia.org/wiki/Hong_Kong_New_Wave',
    'Hong Kong Category III': 'https://en.wikipedia.org/wiki/Category_III_film',
    'Hong Kong Action': 'https://en.wikipedia.org/wiki/Hong_Kong_action_cinema',
    'Pinku Eiga': 'https://en.wikipedia.org/wiki/Pink_film',
    'Brazilian Exploitation': 'https://en.wikipedia.org/wiki/Pornochanchada',
    'European Sexploitation': 'https://en.wikipedia.org/wiki/Sexploitation_film',
    'Classic Hollywood': 'https://en.wikipedia.org/wiki/Classical_Hollywood_cinema',
    'American Exploitation': 'https://en.wikipedia.org/wiki/Exploitation_film',
    'Indie Cinema': 'https://en.wikipedia.org/wiki/Independent_film',
    'Music Films': 'https://en.wikipedia.org/wiki/Concert_film',
    'Japanese Exploitation': 'https://en.wikipedia.org/wiki/Yakuza_film',
    'Japanese New Wave': 'https://en.wikipedia.org/wiki/Japanese_New_Wave',
}

# Regex to extract film titles from Wikipedia text (italic titles in year lists)
_WIKI_TITLE_RE = re.compile(r"'''(.+?)'''|''(.+?)''|\*\s*(.+?)\s*[\(\[](\d{4})")


def fetch_wikipedia_films(category: str) -> List[str]:
    """Fetch Wikipedia genre article and extract film title mentions."""
    url = WIKIPEDIA_CATEGORY_URLS.get(category)
    if not url:
        return []
    try:
        import urllib.request
        # Use Wikipedia's plain-text API
        api_url = url.replace('en.wikipedia.org/wiki/', 'en.wikipedia.org/w/api.php?action=query&titles=') + '&prop=extracts&explaintext=1&format=json'
        req = urllib.request.Request(api_url, headers={'User-Agent': 'film-sorting-database/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get('query', {}).get('pages', {})
        text = next(iter(pages.values()), {}).get('extract', '')
        # Extract any title-like strings near years
        titles = []
        for m in re.finditer(r'([A-Z][^.!?\n]{3,50})\s*\((\d{4})\)', text):
            titles.append(m.group(1).strip())
        return titles[:200]
    except Exception as e:
        print(f"  Wikipedia fetch failed for {category}: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Per-film scoring
# ---------------------------------------------------------------------------

def score_film(filename: str, title: Optional[str], year: Optional[int],
               director: Optional[str], decade: Optional[str], category: str,
               tmdb_cache: Dict, omdb_cache: Dict,
               core_db: CoreDirectorDatabase,
               wikipedia_films: Optional[List[str]] = None,
               corpus_lookup: Optional[CorpusLookup] = None) -> Optional[Dict]:
    """
    Score a single film. Returns None if no title/year (unscoreable).
    Returns dict with score breakdown.
    """
    if not title or not year:
        return None

    cache_key = make_cache_key(title, year)
    tmdb_data = tmdb_cache.get(cache_key)
    omdb_data = omdb_cache.get(cache_key)

    # Try alternate key with cleaned title if no hit
    if tmdb_data is None and omdb_data is None:
        # Also try year=None key
        alt_key = make_cache_key(title, None)
        tmdb_data = tmdb_cache.get(alt_key)
        omdb_data = omdb_cache.get(alt_key)

    has_api_data = (tmdb_data is not None) or (omdb_data is not None)

    # Get director from API if not from filename
    api_director = director
    if not api_director:
        if omdb_data and omdb_data.get('director'):
            api_director = omdb_data['director']
        elif tmdb_data and tmdb_data.get('director'):
            api_director = tmdb_data['director']

    dt = score_director_tier(api_director, category, core_db)
    dm = score_decade_match(decade, category)
    ka = score_keyword_alignment(tmdb_data, category)
    cr = score_canonical_recognition(tmdb_data, omdb_data)
    ts = score_text_signal(tmdb_data, omdb_data, category)
    ec = score_external_canonical(title, year, filename, wikipedia_films)
    # Corpus tier score (Issue #38) — 0 if corpus not loaded
    imdb_id = omdb_data.get('imdb_id') if omdb_data else None
    ct = score_corpus_tier(title, year, imdb_id, corpus_lookup)

    total = dt + dm + ka + cr + ts + ec + ct

    # Keyword hits for annotation — use RANKING_TAGS (broader set)
    film_keywords = set(k.lower() for k in (tmdb_data or {}).get('keywords', []))
    ranking_tags = RANKING_TAGS.get(category)
    if ranking_tags:
        cat_tags = set(t.lower() for t in ranking_tags)
    else:
        cat_tags = set(t.lower() for t in SATELLITE_ROUTING_RULES.get(category, {}).get('keyword_signals', {}).get('tmdb_tags', []))
    matched_keywords = sorted(film_keywords & cat_tags)

    # Use clean title for display (strips quality/language tags from dot-separated filenames)
    display_title = clean_title_for_cache(title)

    return {
        'filename': filename,
        'title': display_title,
        'year': year,
        'director': api_director or '',
        'decade': decade or '',
        'score': total,
        'director_tier': dt,
        'decade_match': dm,
        'keyword_alignment': ka,
        'canonical_recognition': cr,
        'text_signal': ts,
        'external_canonical': ec,
        'corpus_tier': ct,
        'matched_keywords': matched_keywords,
        'has_api_data': has_api_data,
        'criterion': 'criterion' in filename.lower(),
        'sight_and_sound': ec >= 2,
    }


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def tier_label(score: int) -> str:
    if score >= 8:
        return 'Category Core'
    if score >= 5:
        return 'Category Reference'
    return 'Texture'


def format_film_entry(rank: int, film: Dict) -> str:
    badges = []
    if film['sight_and_sound']:
        badges.append('★ Sight & Sound 2022')
    if film['criterion']:
        badges.append('◆ Criterion')

    director_str = f" — {film['director']}" if film['director'] else ''
    badge_str = '  ' + '  '.join(badges) if badges else ''
    keyword_str = ''
    if film['matched_keywords']:
        keyword_str = f"\n   Keywords: {', '.join(film['matched_keywords'])}"

    corpus_str = f" corpus:{film['corpus_tier']}" if film.get('corpus_tier', 0) > 0 else ''
    breakdown = (f"director:{film['director_tier']} decade:{film['decade_match']} "
                 f"keywords:{film['keyword_alignment']} canonical:{film['canonical_recognition']} "
                 f"text:{film['text_signal']} external:{film['external_canonical']}{corpus_str}")

    lines = [
        f"{rank}. **{film['title']} ({film['year']})**{director_str} — **{film['score']}/10**{badge_str}",
        f"   `{breakdown}`{keyword_str}",
    ]
    return '\n'.join(lines)


def generate_category_report(category: str, scored: List[Dict],
                              no_data: List[str], cap: int) -> str:
    today = datetime.date.today().strftime('%Y-%m')
    total = len(scored) + len(no_data)
    lines = [
        f"## {category} — Tentpole Ranking ({today})",
        f"*{total} films in collection | Cap: {cap} | {len(no_data)} films lack API data*",
        '',
    ]

    # Group by tier
    core_films = [f for f in scored if f['score'] >= 8]
    ref_films = [f for f in scored if 5 <= f['score'] < 8]
    texture_films = [f for f in scored if f['score'] < 5]

    if core_films:
        lines.append('### Category Core — keep last (score 8–10)')
        lines.append('*These films define what the category means. Keep even if nothing else remains.*')
        lines.append('')
        for i, film in enumerate(core_films, 1):
            lines.append(format_film_entry(i, film))
            lines.append('')

    if ref_films:
        lines.append('### Category Reference — keep if cap allows (score 5–7)')
        lines.append('*Essential range; films by secondary directors.*')
        lines.append('')
        offset = len(core_films) + 1
        for i, film in enumerate(ref_films, offset):
            lines.append(format_film_entry(i, film))
            lines.append('')

    if texture_films:
        lines.append('### Texture — cut first when over cap (score 0–4)')
        lines.append('*Review when over cap. Cut these before Core or Reference.*')
        lines.append('')
        offset = len(core_films) + len(ref_films) + 1
        for i, film in enumerate(texture_films, offset):
            lines.append(format_film_entry(i, film))
            lines.append('')

    if no_data:
        lines.append('### No API data — manual review required')
        lines.append('')
        for fname in sorted(no_data):
            lines.append(f'- {fname}')
        lines.append('')

    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main ranking logic
# ---------------------------------------------------------------------------

def load_category_films(audit_path: Path, category: str) -> List[Dict]:
    """Load films for a specific Satellite category from library_audit.csv."""
    rows = []
    with open(audit_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('tier') == 'Satellite' and row.get('subdirectory') == category:
                rows.append(row)
    return rows


def rank_category(category: str, audit_path: Path,
                  tmdb_cache: Dict, omdb_cache: Dict,
                  core_db: CoreDirectorDatabase,
                  wikipedia_films: Optional[List[str]] = None,
                  corpus_lookup: Optional[CorpusLookup] = None) -> str:
    """Rank all films in a Satellite category. Returns markdown string."""
    parser = FilenameParser()
    rows = load_category_films(audit_path, category)

    if not rows:
        return f"## {category}\n\n*No films found in library_audit.csv for this category.*\n\n---\n\n"

    scored = []
    no_data = []

    for row in rows:
        filename = row['filename']
        decade = row.get('decade') or None

        try:
            metadata = parser.parse(filename)
        except Exception:
            no_data.append(filename)
            continue

        result = score_film(
            filename=filename,
            title=metadata.title,
            year=metadata.year,
            director=metadata.director,
            decade=decade,
            category=category,
            tmdb_cache=tmdb_cache,
            omdb_cache=omdb_cache,
            core_db=core_db,
            wikipedia_films=wikipedia_films,
            corpus_lookup=corpus_lookup,
        )

        if result is None:
            no_data.append(filename)
        else:
            scored.append(result)

    # Sort by score descending, then by title
    scored.sort(key=lambda f: (-f['score'], f['title'].lower()))

    cap = CATEGORY_CAPS.get(category, '?')
    return generate_category_report(category, scored, no_data, cap)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Rank films in Satellite categories by tentpole score (Issue #30)'
    )
    parser.add_argument('category', nargs='?', help='Category name (e.g. "Giallo")')
    parser.add_argument('--all', action='store_true', help='Rank all categories')
    parser.add_argument('--output', help='Write output to file (default: stdout)')
    parser.add_argument('--wikipedia', action='store_true',
                        help='Fetch Wikipedia genre articles for external_canonical scoring')
    parser.add_argument('--audit', default='output/library_audit.csv',
                        help='Path to library_audit.csv')
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args()

    if not args.category and not args.all:
        parser.error('Specify a category name or --all')

    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"Error: {audit_path} not found — run audit.py first", file=sys.stderr)
        sys.exit(1)

    # Load caches
    tmdb_cache = load_json_cache(Path('output/tmdb_cache.json'))
    omdb_cache = load_json_cache(Path('output/omdb_cache.json'))
    print(f"Loaded TMDb cache ({len(tmdb_cache)} entries), OMDb cache ({len(omdb_cache)} entries)",
          file=sys.stderr)

    # Load Core director DB
    config_path = Path(args.config)
    if not config_path.exists():
        config_path = Path('config_external.yaml')
    import yaml
    config = yaml.safe_load(open(config_path))
    project_path = Path(config['project_path'])
    core_db = CoreDirectorDatabase(project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md')

    # Determine categories to rank
    if args.all:
        categories = list(SATELLITE_ROUTING_RULES.keys())
    else:
        categories = [args.category]

    # Validate category names
    for cat in categories:
        if cat not in SATELLITE_ROUTING_RULES:
            close = [k for k in SATELLITE_ROUTING_RULES if args.category.lower() in k.lower()]
            suggestion = f" Did you mean: {close[0]!r}?" if close else ''
            print(f"Error: Unknown category {cat!r}.{suggestion}", file=sys.stderr)
            print(f"Available: {', '.join(SATELLITE_ROUTING_RULES.keys())}", file=sys.stderr)
            sys.exit(1)

    # Build output
    output_parts = [
        '# Satellite Category Tentpole Rankings',
        f'*Generated {datetime.date.today()} by scripts/rank_category_tentpoles.py*',
        '',
        '**Score interpretation:** 8–10 = Category Core (keep last) | 5–7 = Category Reference | 0–4 = Texture (cut first)',
        '',
        '---',
        '',
    ]

    # Load ground truth corpus for canonical_tier scoring (Issue #38)
    corpora_dir = Path(__file__).parent.parent / 'data' / 'corpora'
    corpus_lookup = CorpusLookup(corpora_dir) if corpora_dir.exists() else None
    if corpus_lookup:
        stats = corpus_lookup.get_stats()
        if stats['total_entries'] > 0:
            print(f"Corpus loaded: {stats['total_entries']} films across {len(stats['categories'])} categories",
                  file=sys.stderr)

    for cat in categories:
        print(f"Ranking: {cat}...", file=sys.stderr)
        wikipedia_films = fetch_wikipedia_films(cat) if args.wikipedia else None
        if args.wikipedia and wikipedia_films:
            print(f"  Wikipedia: {len(wikipedia_films)} film mentions", file=sys.stderr)
        output_parts.append(rank_category(cat, audit_path, tmdb_cache, omdb_cache,
                                          core_db, wikipedia_films, corpus_lookup))

    output = '\n'.join(output_parts)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding='utf-8')
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
