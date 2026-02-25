#!/usr/bin/env python3
"""
classify.py - Film Classification Pipeline (v1.0)

NEVER moves files. Only reads filenames and writes CSV.

Classification priority order:
1. [PRECISION] Parse filename → FilmMetadata
2. [PRECISION] API Enrichment → TMDb + OMDb parallel query with smart merge
   - Director: OMDb > TMDb (OMDb = IMDb = authoritative)
   - Country: OMDb > TMDb (critical for Satellite routing)
   - Genres: TMDb > OMDb (TMDb has richer structured data)
3. [PRECISION] Explicit lookup → SORTING_DATABASE.md (human-curated, highest trust)
4. [REASONING] Core director check → whitelist exact match
5. [REASONING] Reference canon check → 50-film hardcoded list in constants.py
6. [PRECISION] User tag recovery → trust previous human classification
7. [REASONING] Popcorn classification → mainstream/curation signals (Issue #14: moved before Satellite)
8. [REASONING] Language/country → Satellite routing (decade-bounded)
9. [REASONING] Satellite classification → merged API data (country + genre + decade)
10. [PRECISION] Default → Unsorted with detailed reason code
"""

import sys
import csv
import json
import re
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

import yaml

from lib.parser import FilenameParser, FilmMetadata
from lib.tmdb import TMDbClient
from lib.omdb import OMDbClient
from lib.lookup import SortingDatabaseLookup
from lib.core_directors import CoreDirectorDatabase
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier
from lib.normalization import normalize_for_lookup
from lib.constants import (
    REFERENCE_CANON, COUNTRY_TO_WAVE,
    CATEGORY_CERTAINTY_TIERS, TIER_CONFIDENCE, REVIEW_CONFIDENCE_THRESHOLD,
)
from lib.enrichment import ManualEnrichmentSource
from lib.normalizer import FilenameNormalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of classifying one film"""
    filename: str
    title: str
    year: Optional[int]
    director: Optional[str]
    language: Optional[str]
    country: Optional[str]
    user_tag: Optional[str]
    tier: str
    decade: Optional[str]
    subdirectory: Optional[str]
    destination: str
    confidence: float
    reason: str
    # Audit trail: which TMDb film was used for enrichment (Issue #21)
    tmdb_id: Optional[int] = None
    tmdb_title: Optional[str] = None
    # Data readiness level at time of classification (Issue #30)
    # R0=no year, R1=no director+country, R2=partial data, R3=full data
    data_readiness: str = 'R3'
    # Issue #35: per-film evidence trail (shadow pass — purely additive, never alters verdict)
    evidence_trail: Optional[dict] = None


def get_decade(year: int) -> str:
    """Convert year to decade string"""
    return f"{(year // 10) * 10}s"


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class FilmClassifier:
    """Main film classification engine — v1.0"""

    def __init__(self, config_path: Path, no_tmdb: bool = False):
        self.config = load_config(config_path)
        self.stats = defaultdict(int)
        self.no_tmdb = no_tmdb
        self._setup_components()

    def _setup_components(self):
        """Initialize all classification components"""
        project_path = Path(self.config['project_path'])

        self.parser = FilenameParser()
        self.normalizer = FilenameNormalizer()

        # TMDb client with caching (optional — graceful degradation)
        tmdb_key = self.config.get('tmdb_api_key')
        if tmdb_key and not self.no_tmdb:
            self.tmdb = TMDbClient(
                api_key=tmdb_key,
                cache_path=Path('output/tmdb_cache.json')
            )
            logger.info("TMDb API enrichment enabled (with caching)")
        else:
            self.tmdb = None
            if self.no_tmdb:
                logger.info("API enrichment disabled (--no-api/--no-tmdb): TMDb and OMDb both offline")
            else:
                logger.warning("TMDb API enrichment disabled (no API key in config)")

        # OMDb client with caching (fallback for obscure films)
        omdb_key = self.config.get('omdb_api_key')
        if omdb_key and not self.no_tmdb:
            self.omdb = OMDbClient(
                api_key=omdb_key,
                cache_path=Path('output/omdb_cache.json')
            )
            logger.info("OMDb API fallback enabled (with caching)")
        else:
            self.omdb = None
            if not omdb_key:
                logger.info("OMDb API fallback disabled (no API key in config)")

        # Explicit lookup database — checked BEFORE all heuristics
        self.lookup_db = SortingDatabaseLookup(
            project_path / 'SORTING_DATABASE.md'
        )
        lookup_stats = self.lookup_db.get_stats()
        logger.info(f"Loaded explicit lookup table: {lookup_stats['total_entries']} films")

        # Core director database — exact match only
        self.core_db = CoreDirectorDatabase(
            project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        )

        # Satellite classifier (TMDb-based rules)
        # Issue #16: pass core_db for defensive Core director check
        self.satellite_classifier = SatelliteClassifier(core_db=self.core_db)
        self.popcorn_classifier = PopcornClassifier()  # Issue #25 D8: lookup_db removed (dead code)

        # Manual enrichment source — curator-supplied metadata for API-dark films (Issue #30)
        enrichment_path = Path('output/manual_enrichment.csv')
        self.enrichment = ManualEnrichmentSource(enrichment_path)
        if len(self.enrichment) > 0:
            logger.info(f"Loaded manual enrichment: {len(self.enrichment)} entries")

    def _build_destination(self, tier: str, decade: Optional[str], subdirectory: Optional[str]) -> str:
        """Build destination path string from classification components (tier-first)"""
        if tier == 'Unsorted':
            return 'Unsorted/'
        elif tier == 'Core' and decade and subdirectory:
            return f'Core/{decade}/{subdirectory}/'
        elif tier == 'Reference' and decade:
            return f'Reference/{decade}/'
        elif tier == 'Satellite' and decade and subdirectory:
            return f'Satellite/{subdirectory}/{decade}/'  # Category-first structure (Issue #6)
        elif tier == 'Popcorn' and decade:
            return f'Popcorn/{decade}/'
        else:
            return 'Unsorted/'

    def _assess_readiness(self, metadata: 'FilmMetadata', tmdb_data: Optional[Dict]) -> str:
        """
        Assess data readiness level after API enrichment (Issue #30).

        R0: no year → hard gate already handles this, but reported for completeness
        R1: year present but no director AND no country → skip heuristic routing
        R2: partial (director OR country, not both) → route but cap confidence at 0.6
        R3: full (director AND country AND genres) → full pipeline, no cap
        """
        if not metadata.year:
            return 'R0'
        has_director = bool(
            metadata.director or (tmdb_data and tmdb_data.get('director'))
        )
        has_country = bool(
            metadata.country or (tmdb_data and tmdb_data.get('countries'))
        )
        has_genres = bool(tmdb_data and tmdb_data.get('genres'))
        if not has_director and not has_country:
            return 'R1'
        if has_director and has_country and has_genres:
            return 'R3'
        return 'R2'

    def _parse_destination_path(self, path: str) -> dict:
        """Parse a destination path from SORTING_DATABASE.md into components (supports both formats)"""
        parts = path.strip('/').split('/')
        result = {'tier': 'Unknown', 'decade': None, 'subdirectory': None}

        if not parts:
            return result

        first = parts[0]

        # Tier-first format (PREFERRED): "Core/1960s/Director", "Reference/1960s", "Satellite/Category/1970s"
        if first in ('Core', 'Reference', 'Satellite', 'Popcorn', 'Staging', 'Unsorted'):
            result['tier'] = first
            if len(parts) > 1 and re.match(r'\d{4}s$', parts[1]):
                result['decade'] = parts[1]
                if len(parts) > 2:
                    result['subdirectory'] = '/'.join(parts[2:])
            elif len(parts) > 1:
                # Check if last part is a decade (Satellite/Category/1970s format — Issue #33)
                # e.g. "Satellite/Japanese New Wave/1970s" → subdirectory=Japanese New Wave, decade=1970s
                if len(parts) > 2 and re.match(r'\d{4}s$', parts[-1]):
                    result['decade'] = parts[-1]
                    result['subdirectory'] = '/'.join(parts[1:-1])
                else:
                    result['subdirectory'] = '/'.join(parts[1:])
        # Legacy decade-first format (for backward compatibility): "1960s/Core/Director"
        elif re.match(r'\d{4}s$', first):
            result['decade'] = first
            if len(parts) > 1:
                result['tier'] = parts[1]
            if len(parts) > 2:
                result['subdirectory'] = '/'.join(parts[2:])

        return result

    def _parse_user_tag(self, tag: str) -> dict:
        """Parse user tag like 'Popcorn-1970s' or 'Core-1960s-Jacques Demy' into components"""
        parts = tag.split('-')
        result = {}

        remaining_parts = []
        for part in parts:
            if re.match(r'(19|20)\d{2}s', part):
                result['decade'] = part
            elif part in ('Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted'):
                result['tier'] = part
            else:
                remaining_parts.append(part)

        if remaining_parts:
            result['extra'] = ' '.join(remaining_parts)

        return result

    def _clean_title_for_api(self, title: str) -> str:
        """
        ENHANCED (Issue #16): Aggressive cleaning for API queries

        Removes RELEASE_TAGS tokens that survive parser._clean_title()
        This fixes Layer 1 of the classification regression where tokens like
        "Metro", "576p", "PC" survive into API queries and cause null results.

        Removes:
        - User tag brackets [...]
        - Format signals (35mm, Criterion, etc.)
        - RELEASE_TAGS that survived parser (second-pass truncation)
        - Residual tokens not in RELEASE_TAGS (Metro, PC, SR, language tags)
        - Empty parentheses artifacts
        - Extra whitespace

        Preserves:
        - Punctuation (for proper title matching)
        - Capitalization
        - Special characters (é, ñ, etc.)

        Returns:
            Cleaned title string ready for API query
        """
        from lib.normalization import _strip_format_signals, strip_release_tags

        # Remove user tag brackets
        clean_title = re.sub(r'\s*\[.+?\]\s*', ' ', title)

        # Strip format signals (35mm, Criterion, etc.)
        clean_title = _strip_format_signals(clean_title)

        # NEW (Issue #16): Second-pass RELEASE_TAGS truncation
        # Parser's _clean_title() stops at FIRST tag, this catches survivors.
        # Uses token-boundary matching so short tags like "hd"/"nf" do not
        # truncate normal words (e.g. "Shadow", "Conformist").
        clean_title = strip_release_tags(clean_title)

        # NEW (Issue #16): Strip common residual tokens not in RELEASE_TAGS
        # These are tokens that appear mid-title after incomplete parser truncation
        residual_patterns = [
            r'\b(metro|pc|sr|moc|kl|doc|vo)\b',  # Source tags
            r'\b\d{3,4}p\b',  # Resolution: 576p, 1080p
            r'\b(spanish|french|italian|german|japanese|chinese|vostfr)\b',  # Language tags
            r'\b(itunes|upscale|uncensored|satrip|vhsrip|xvid|mp3|2audio)\b',  # Format/codec
        ]

        for pattern in residual_patterns:
            clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)

        # Remove empty parentheses artifacts
        clean_title = re.sub(r'\s*\(\s*\)', '', clean_title)

        # Collapse multiple spaces
        clean_title = ' '.join(clean_title.split())

        return clean_title.strip()

    def _query_apis(self, metadata: FilmMetadata) -> Dict[str, Optional[Dict]]:
        """
        Query TMDb and OMDb in parallel (both attempted, not fallback)

        Soft gate: API failures return None but don't stop pipeline

        Args:
            metadata: FilmMetadata with title and year

        Returns:
            Dict with keys 'tmdb' and 'omdb', values are API result dicts or None
        """
        results = {'tmdb': None, 'omdb': None}

        if not metadata.title or not metadata.year:
            return results

        clean_title = self._clean_title_for_api(metadata.title)

        # Query TMDb (if available)
        if self.tmdb:
            tmdb_data = self.tmdb.search_film(clean_title, metadata.year)
            if tmdb_data:
                results['tmdb'] = tmdb_data
                self.stats['tmdb_success'] += 1

        # Query OMDb (if available) — NOT a fallback, always attempt
        if self.omdb:
            omdb_data = self.omdb.search_film(clean_title, metadata.year)
            if omdb_data:
                results['omdb'] = omdb_data
                self.stats['omdb_success'] += 1

        # Track when both succeeded
        if results['tmdb'] and results['omdb']:
            self.stats['both_apis_success'] += 1

        return results

    def _merge_api_results(self, tmdb_data: Optional[Dict], omdb_data: Optional[Dict],
                           metadata: FilmMetadata) -> Optional[Dict]:
        """
        Merge TMDb and OMDb results with field-specific priority

        Priority rules:
        - Director: OMDb > TMDb (OMDb = IMDb = most authoritative)
        - Country: OMDb > TMDb (OMDb country data superior)
        - Genres: TMDb > OMDb (TMDb has richer genre data)
        - Cast/popularity: TMDb > OMDb (TMDb has richer popularity metadata)
        - Year: filename > OMDb > TMDb (trust human-curated filenames)
        - Title: TMDb > OMDb > filename (canonical names)

        Updates metadata.director and metadata.country as side effect

        Args:
            tmdb_data: TMDb API result or None
            omdb_data: OMDb API result or None
            metadata: FilmMetadata to enrich (mutated)

        Returns:
            Merged dict for downstream satellite classification, or None if no data
        """
        if not tmdb_data and not omdb_data:
            return None

        merged = {}

        # Director: OMDb > TMDb
        if omdb_data and omdb_data.get('director'):
            merged['director'] = omdb_data['director']
            self.stats['director_from_omdb'] += 1
            if not metadata.director:
                metadata.director = omdb_data['director']
        elif tmdb_data and tmdb_data.get('director'):
            merged['director'] = tmdb_data['director']
            self.stats['director_from_tmdb'] += 1
            if not metadata.director:
                metadata.director = tmdb_data['director']
        elif metadata.director:
            merged['director'] = metadata.director

        # Country: OMDb > TMDb (critical fix for Satellite routing)
        if omdb_data and omdb_data.get('countries'):
            merged['countries'] = omdb_data['countries']
            self.stats['country_from_omdb'] += 1
            if not metadata.country:
                metadata.country = omdb_data['countries'][0]
        elif tmdb_data and tmdb_data.get('countries'):
            merged['countries'] = tmdb_data['countries']
            self.stats['country_from_tmdb'] += 1
            if not metadata.country:
                metadata.country = tmdb_data['countries'][0]
        elif metadata.country:
            merged['countries'] = [metadata.country]
        else:
            merged['countries'] = []

        # Genres: TMDb > OMDb (TMDb has richer structured data)
        if tmdb_data and tmdb_data.get('genres'):
            merged['genres'] = tmdb_data['genres']
            self.stats['genres_from_tmdb'] += 1
        elif omdb_data and omdb_data.get('genres'):
            merged['genres'] = omdb_data['genres']
        else:
            merged['genres'] = []

        # Cast: TMDb > OMDb (used by Popcorn differentiator)
        if tmdb_data and tmdb_data.get('cast'):
            merged['cast'] = tmdb_data['cast']
        elif omdb_data and omdb_data.get('cast'):
            merged['cast'] = omdb_data['cast']
        else:
            merged['cast'] = []

        # Popularity/votes: TMDb preferred, OMDb vote count as fallback
        if tmdb_data and tmdb_data.get('popularity') is not None:
            merged['popularity'] = tmdb_data['popularity']
        if tmdb_data and tmdb_data.get('vote_count') is not None:
            merged['vote_count'] = tmdb_data['vote_count']
        elif omdb_data and omdb_data.get('vote_count') is not None:
            merged['vote_count'] = omdb_data['vote_count']

        # Year: filename > OMDb > TMDb
        if metadata.year:
            merged['year'] = metadata.year
        elif omdb_data and omdb_data.get('year'):
            merged['year'] = omdb_data['year']
        elif tmdb_data and tmdb_data.get('year'):
            merged['year'] = tmdb_data['year']

        # Title: TMDb > OMDb > filename (canonical names)
        if tmdb_data and tmdb_data.get('title'):
            merged['title'] = tmdb_data['title']
        elif omdb_data and omdb_data.get('title'):
            merged['title'] = omdb_data['title']
        else:
            merged['title'] = metadata.title

        # Original language (only TMDb provides this)
        if tmdb_data and tmdb_data.get('original_language'):
            merged['original_language'] = tmdb_data['original_language']

        # TMDb audit trail: pass through film ID and canonical title (Issue #21)
        if tmdb_data and tmdb_data.get('tmdb_id'):
            merged['tmdb_id'] = tmdb_data['tmdb_id']
            merged['tmdb_title'] = tmdb_data.get('tmdb_title')

        # Keywords: TMDb only (Issue #29)
        merged['keywords'] = tmdb_data.get('keywords', []) if tmdb_data else []

        # Text fields: longer source wins — encyclopedic preferred (Issue #29)
        tmdb_overview = (tmdb_data.get('overview', '') or '') if tmdb_data else ''
        tmdb_tagline = (tmdb_data.get('tagline', '') or '') if tmdb_data else ''
        omdb_plot = (omdb_data.get('plot', '') or '') if omdb_data else ''
        merged['overview'] = tmdb_overview
        merged['tagline'] = tmdb_tagline
        # plot: longer of OMDb plot vs TMDb overview (encyclopedic preferred)
        merged['plot'] = omdb_plot if len(omdb_plot) >= len(tmdb_overview) else tmdb_overview

        return merged

    def classify(self, metadata: FilmMetadata) -> ClassificationResult:
        """
        Main classification pipeline — priority-ordered checks.

        Priority order (Issue #14 - Popcorn/Indie before Satellite):
        1. Explicit lookup (SORTING_DATABASE.md)
        2. Core director check
        3. Reference canon check
        4. User tag recovery
        5. Popcorn check (MOVED UP - prevents mainstream films from Satellite)
        6. Country/decade satellite routing
        7. TMDb satellite classification
        8. Unsorted (default)

        Each check is a soft gate (no match → continue) except:
        - No year: hard gate (cannot route to decade → Unsorted)
        """

        # === Pre-Stage: Non-film detection (Issue #33) ===
        # Supplements, trailers, and TV episodes are identified by filename pattern.
        # These skip all routing stages and are excluded from the classification rate.
        _stem = Path(metadata.filename).stem
        _nonfim = self.normalizer._detect_nonfim(_stem)
        if _nonfim:
            self.stats['non_film_supplement'] += 1
            return ClassificationResult(
                filename=metadata.filename, title=metadata.filename,
                year=None, director=None, language=None, country=None,
                user_tag=None, tier='Non-Film', decade=None, subdirectory=None,
                destination='Non-Film/',
                confidence=0.0, reason='non_film_supplement',
                data_readiness='R0',
            )

        # === Manual enrichment: fill empty metadata fields before API query (Issue #30) ===
        # Enrichment fills gaps; API data takes priority (metadata fields only update if None).
        _enrichment = self.enrichment.get(metadata.filename)
        if _enrichment:
            if _enrichment.get('director') and not metadata.director:
                metadata.director = _enrichment['director']
            if _enrichment.get('country') and not metadata.country:
                metadata.country = _enrichment['country']

        # === Stage 1: API Enrichment (TMDb + OMDb parallel query with smart merge) ===
        api_results = self._query_apis(metadata)
        tmdb_data = self._merge_api_results(
            api_results['tmdb'],
            api_results['omdb'],
            metadata
        )
        # Note: metadata.director and metadata.country updated as side effect

        # Inject enrichment genres if API returned none (Issue #30)
        if _enrichment and _enrichment.get('genres'):
            if tmdb_data is None:
                tmdb_data = {'genres': _enrichment['genres'], 'countries': [], 'keywords': []}
            elif not tmdb_data.get('genres'):
                tmdb_data['genres'] = _enrichment['genres']

        # === Data readiness assessment (Issue #30) ===
        # Assessed after API enrichment so enriched director/country are considered.
        _readiness = self._assess_readiness(metadata, tmdb_data)

        # Audit trail: capture which TMDb film was used (Issue #21)
        _tmdb_id = tmdb_data.get('tmdb_id') if tmdb_data else None
        _tmdb_title = tmdb_data.get('tmdb_title') if tmdb_data else None

        # === Stage 2: Explicit lookup (highest trust — human-curated) ===
        if metadata.title:
            dest = self.lookup_db.lookup(metadata.title, metadata.year)
            if dest:
                self.stats['explicit_lookup'] += 1
                parsed = self._parse_destination_path(dest)

                if parsed['tier'] == 'Unknown':
                    self.stats['lookup_invalid_destination'] += 1
                    logger.warning(
                        "Skipping invalid explicit lookup destination '%s' for '%s'",
                        dest, metadata.title
                    )
                else:
                    # Track satellite counts for cap enforcement
                    if parsed['tier'] == 'Satellite' and parsed.get('subdirectory'):
                        self.satellite_classifier.increment_count(parsed['subdirectory'])

                    _result = ClassificationResult(
                        filename=metadata.filename, title=metadata.title,
                        year=metadata.year, director=metadata.director,
                        language=metadata.language, country=metadata.country,
                        user_tag=metadata.user_tag,
                        tier=parsed['tier'], decade=parsed['decade'],
                        subdirectory=parsed.get('subdirectory'),
                        destination=dest,
                        confidence=1.0, reason='explicit_lookup',
                        tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                        data_readiness=_readiness,
                    )
                    _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
                    return _result

        # === Hard gate: no year = cannot route to decade ===
        if not metadata.year:
            self.stats['unsorted_no_year'] += 1
            _result = ClassificationResult(
                filename=metadata.filename, title=metadata.title,
                year=None, director=metadata.director,
                language=metadata.language, country=metadata.country,
                user_tag=metadata.user_tag,
                tier='Unsorted', decade=None, subdirectory=None,
                destination='Unsorted/',
                confidence=0.0, reason='unsorted_no_year',
                tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                data_readiness='R0',
            )
            _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, 'R0')
            return _result

        decade = get_decade(metadata.year)

        # === Stage 3: Reference canon check (constants.py hardcoded list) ===
        normalized_title = normalize_for_lookup(metadata.title, strip_format_signals=True)
        ref_key = (normalized_title, metadata.year)
        if ref_key in REFERENCE_CANON:
            self.stats['reference_canon'] += 1
            dest = f'Reference/{decade}/'
            _result = ClassificationResult(
                filename=metadata.filename, title=metadata.title,
                year=metadata.year, director=metadata.director,
                language=metadata.language, country=metadata.country,
                user_tag=metadata.user_tag,
                tier='Reference', decade=decade, subdirectory=None,
                destination=dest,
                confidence=1.0, reason='reference_canon',
                tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                data_readiness=_readiness,
            )
            _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
            return _result

        # === Stage 4: Language/country → Satellite routing (from filename) ===
        # Skipped for R1 films (no director AND no country — routing would be meaningless)
        # Issue #25: Satellite fires before Core. Movement character takes priority over
        # director identity. Core directors' movement-period films route here.
        if _readiness != 'R1' and metadata.country and metadata.country in COUNTRY_TO_WAVE:
            wave_config = COUNTRY_TO_WAVE[metadata.country]
            if decade in wave_config['decades']:
                category = wave_config['category']
                self.stats['country_satellite'] += 1
                dest = f'Satellite/{category}/{decade}/'  # Category-first (Issue #6)
                _tier_num = CATEGORY_CERTAINTY_TIERS.get(category, 2)
                _confidence = TIER_CONFIDENCE[_tier_num]
                if _readiness == 'R2':
                    _confidence = min(_confidence, 0.6)
                _result = ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Satellite', decade=decade, subdirectory=category,
                    destination=dest,
                    confidence=_confidence, reason='country_satellite',
                    tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                    data_readiness=_readiness,
                )
                _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
                return _result

        # === Stage 5: TMDb-based satellite classification ===
        # Skipped for R1 films (no director AND no country — no basis for satellite routing).
        # Also fires when tmdb_data is None but metadata.director is set (from filename).
        # satellite.py constructs a minimal director-only dict in that case, enabling
        # director-list routing rules (FNW, Indie Cinema directors) to fire without API data.
        # Issue #25: Satellite fires before Core — Core directors in movement director lists
        # (e.g. Godard in FNW, Scorsese in AmNH) route to Satellite for their movement period.
        if _readiness != 'R1' and (tmdb_data or metadata.director):
            satellite_cat = self.satellite_classifier.classify(metadata, tmdb_data)
            if satellite_cat:
                self.stats['tmdb_satellite'] += 1
                dest = f'Satellite/{satellite_cat}/{decade}/'  # Category-first (Issue #6)
                _tier_num = CATEGORY_CERTAINTY_TIERS.get(satellite_cat, 2)
                _confidence = TIER_CONFIDENCE[_tier_num]
                if _readiness == 'R2':
                    _confidence = min(_confidence, 0.6)
                _result = ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Satellite', decade=decade, subdirectory=satellite_cat,
                    destination=dest,
                    confidence=_confidence, reason='tmdb_satellite',
                    tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                    data_readiness=_readiness,
                )
                _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
                return _result

        # === Stage 6: User tag recovery ===
        # Fires AFTER Satellite (Issue #25) so movement routing takes priority over stale
        # [Core] user tags. A film previously tagged [Core] that now matches a movement
        # is correctly routed to Satellite; the Core tag only applies when no movement
        # match is found.
        if metadata.user_tag:
            parsed_tag = self._parse_user_tag(metadata.user_tag)
            if 'tier' in parsed_tag and 'decade' in parsed_tag:
                tier = parsed_tag['tier']
                tag_decade = parsed_tag['decade']
                extra = parsed_tag.get('extra', '')
                dest = None  # Only set for valid, complete tags (Issue #23)

                if tier == 'Core' and extra:
                    # Cross-check against Core whitelist before trusting the tag (Issue #23 Bug 2)
                    if self.core_db.is_core_director(extra):
                        dest = f'Core/{tag_decade}/{extra}/'
                    else:
                        logger.warning(
                            "User tag '[Core-%s-%s]' — '%s' not in Core whitelist. "
                            "Falling through to heuristics. File: %s",
                            tag_decade, extra, extra, metadata.filename
                        )
                elif tier == 'Satellite':
                    if extra:
                        dest = f'Satellite/{extra}/{tag_decade}/'  # Category-first (Issue #6)
                    else:
                        # Bare [Satellite-1970s] tag has no category — cannot build valid path (Issue #23 Bug 1)
                        logger.warning(
                            "User tag '[Satellite-%s]' has no category subdirectory — "
                            "falling through to heuristics. File: %s",
                            tag_decade, metadata.filename
                        )
                elif tier in ('Reference', 'Popcorn'):
                    dest = f'{tier}/{tag_decade}/'
                else:
                    dest = f'{tier}/'

                if dest is not None:
                    self.stats['user_tag_recovery'] += 1
                    _result = ClassificationResult(
                        filename=metadata.filename, title=metadata.title,
                        year=metadata.year, director=metadata.director,
                        language=metadata.language, country=metadata.country,
                        user_tag=metadata.user_tag,
                        tier=tier, decade=tag_decade, subdirectory=extra or None,
                        destination=dest,
                        confidence=0.8, reason='user_tag_recovery',
                        tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                        data_readiness=_readiness,
                    )
                    _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
                    return _result
                # dest is None — fall through to Stage 7 (Core director check)

        # === Stage 7: Core director check (Issue #25: moved after Satellite) ===
        # Skipped for R1 films (no director — cannot match whitelist).
        # Fallback for prestige non-movement work. Movement-period films by Core directors
        # are caught by Stages 4-5 (Satellite); this stage handles work outside movement
        # decade bounds and any director not listed in a movement's director list.
        if _readiness != 'R1' and metadata.director and self.core_db.is_core_director(metadata.director):
            canonical = self.core_db.get_canonical_name(metadata.director)
            director_decade = self.core_db.get_director_decade(metadata.director, metadata.year)

            if canonical and director_decade:
                self.stats['core_director'] += 1
                dest = f'Core/{director_decade}/{canonical}/'
                _result = ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=canonical,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Core', decade=director_decade, subdirectory=canonical,
                    destination=dest,
                    confidence=1.0, reason='core_director',
                    tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                    data_readiness=_readiness,
                )
                _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
                return _result

        # === Stage 8: Popcorn check (skipped for R1 — no popularity/API data) ===
        popcorn_reason = None if _readiness == 'R1' else self.popcorn_classifier.classify_reason(metadata, tmdb_data)
        if popcorn_reason:
            self.stats['popcorn_auto'] += 1
            self.stats[popcorn_reason] += 1
            dest = f'Popcorn/{decade}/'
            _result = ClassificationResult(
                filename=metadata.filename, title=metadata.title,
                year=metadata.year, director=metadata.director,
                language=metadata.language, country=metadata.country,
                user_tag=metadata.user_tag,
                tier='Popcorn', decade=decade, subdirectory=None,
                destination=dest,
                confidence=0.65, reason=popcorn_reason,
                tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
                data_readiness=_readiness,
            )
            _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
            return _result

        # === Stage 9: Unsorted (default) ===
        # R1: insufficient data (no director AND no country) — distinct from taxonomy gap
        if _readiness == 'R1':
            reason = 'unsorted_insufficient_data'
            self.stats['unsorted_insufficient_data'] += 1
        else:
            reason_parts = []
            if not metadata.director:
                reason_parts.append('no_director')
            if metadata.director:
                reason_parts.append('no_match')
            reason = f"unsorted_{'_'.join(reason_parts)}" if reason_parts else 'unsorted_unknown'
            self.stats[reason] += 1
        _result = ClassificationResult(
            filename=metadata.filename, title=metadata.title,
            year=metadata.year, director=metadata.director,
            language=metadata.language, country=metadata.country,
            user_tag=metadata.user_tag,
            tier='Unsorted', decade=decade, subdirectory=None,
            destination='Unsorted/',
            confidence=0.0, reason=reason,
            tmdb_id=_tmdb_id, tmdb_title=_tmdb_title,
            data_readiness=_readiness,
        )
        _result.evidence_trail = self._gather_evidence(metadata, tmdb_data, _readiness)
        return _result

    def process_directory(self, source_dir: Path) -> List[ClassificationResult]:
        """Process all video files in directory"""
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg',
                          '.mpeg', '.wmv', '.ts', '.m2ts'}
        video_files = []

        for file_path in source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                if not file_path.name.startswith('._'):
                    video_files.append(file_path)

        logger.info(f"Found {len(video_files)} video files")

        results = []
        for i, file_path in enumerate(video_files, 1):
            if i % 100 == 0:
                logger.info(f"Processing {i}/{len(video_files)}...")

            try:
                metadata = self.parser.parse(file_path.name)
                # Store relative path so move.py can find files in subdirectories
                metadata.filename = str(file_path.relative_to(source_dir))
                result = self.classify(metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                self.stats['errors'] += 1

        return results

    def write_manifest(self, results: List[ClassificationResult], output_path: Path):
        """Write classification results to properly-quoted CSV manifest"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'filename', 'title', 'year', 'director',
                'language', 'country', 'user_tag',
                'tier', 'decade', 'subdirectory',
                'destination', 'confidence', 'reason',
                'tmdb_id', 'tmdb_title', 'data_readiness',
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for result in results:
                writer.writerow({
                    'filename': result.filename,
                    'title': result.title,
                    'year': result.year or '',
                    'director': result.director or '',
                    'language': result.language or '',
                    'country': result.country or '',
                    'user_tag': result.user_tag or '',
                    'tier': result.tier,
                    'decade': result.decade or '',
                    'subdirectory': result.subdirectory or '',
                    'destination': result.destination,
                    'confidence': result.confidence,
                    'reason': result.reason,
                    'tmdb_id': result.tmdb_id or '',
                    'tmdb_title': result.tmdb_title or '',
                    'data_readiness': result.data_readiness,
                })

        logger.info(f"Wrote manifest to {output_path}")

    def write_staging_report(self, results: List[ClassificationResult], output_path: Path):
        """Write staging report for films needing manual review"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging = [r for r in results if r.tier == 'Unsorted']

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("FILMS REQUIRING MANUAL REVIEW\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total: {len(staging)} films\n\n")

            for film in staging:
                f.write(f"File: {film.filename}\n")
                f.write(f"Title: {film.title}\n")
                f.write(f"Year: {film.year or 'UNKNOWN'}\n")
                f.write(f"Director: {film.director or 'UNKNOWN'}\n")
                f.write(f"Reason: {film.reason}\n")
                f.write("-" * 60 + "\n")

        logger.info(f"Wrote staging report to {output_path}")

    def write_review_queue(self, results: List[ClassificationResult], output_path: Path):
        """
        Write films that need curator review (Issue #30).

        Two populations:
        1. Classified films with confidence < REVIEW_CONFIDENCE_THRESHOLD (Tier 3-4 auto-classifications)
        2. Unsorted R2/R3 films that have data but no rule matched (taxonomy gaps)
        """
        review = []
        for r in results:
            if r.tier != 'Unsorted' and r.confidence < REVIEW_CONFIDENCE_THRESHOLD:
                review.append((r, 'low_confidence'))
            elif (r.tier == 'Unsorted'
                  and r.data_readiness in ('R2', 'R3')
                  and r.reason in ('unsorted_no_match', 'unsorted_no_director')):
                review.append((r, 'enriched_unsorted'))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            'filename', 'title', 'year', 'director', 'country',
            'tier', 'decade', 'subdirectory', 'destination',
            'confidence', 'reason', 'data_readiness', 'review_reason',
        ]
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for result, review_reason in review:
                writer.writerow({
                    'filename': result.filename,
                    'title': result.title,
                    'year': result.year or '',
                    'director': result.director or '',
                    'country': result.country or '',
                    'tier': result.tier,
                    'decade': result.decade or '',
                    'subdirectory': result.subdirectory or '',
                    'destination': result.destination,
                    'confidence': result.confidence,
                    'reason': result.reason,
                    'data_readiness': result.data_readiness,
                    'review_reason': review_reason,
                })

        logger.info(f"Wrote review queue ({len(review)} films) to {output_path}")

    # ------------------------------------------------------------------
    # Issue #35: Shadow pass — evidence accumulation (read-only)
    # ------------------------------------------------------------------

    def _gather_evidence(
        self,
        metadata,
        tmdb_data: Optional[dict],
        readiness: str,
    ) -> dict:
        """Collect per-stage evidence for one film WITHOUT modifying any state.

        Runs all stage logic in read-only mode (no stats writes, no cap increments).
        Returns a nested dict that is attached to ClassificationResult.evidence_trail.

        INVARIANT: This method must never write to self.stats, self.satellite_classifier.counts,
        or any other shared mutable state.
        """
        # --- Data readiness fields ---
        fields_present = ['title', 'year'] if metadata.title and metadata.year else (
            ['title'] if metadata.title else (['year'] if metadata.year else [])
        )
        if metadata.director:
            fields_present.append('director')
        if metadata.country:
            fields_present.append('country')

        fields_absent = []
        genres = (tmdb_data or {}).get('genres', [])
        countries = (tmdb_data or {}).get('countries', [])
        if not metadata.director and not (tmdb_data or {}).get('director'):
            fields_absent.append('director')
        if not metadata.country and not countries:
            fields_absent.append('country')
        if not genres:
            fields_absent.append('genres')

        # --- Lookup stage ---
        lookup_ev: dict = {'checked': False, 'matched': False}
        if metadata.title:
            lookup_ev['checked'] = True
            dest = self.lookup_db.lookup(metadata.title, metadata.year)
            if dest:
                lookup_ev['matched'] = True
                lookup_ev['dest'] = dest

        # --- Reference canon stage ---
        reference_ev: dict = {'checked': False, 'matched': False}
        if metadata.title and metadata.year:
            reference_ev['checked'] = True
            normalized_title = normalize_for_lookup(metadata.title, strip_format_signals=True)
            if (normalized_title, metadata.year) in REFERENCE_CANON:
                reference_ev['matched'] = True

        # Compute decade from metadata (same logic as classify())
        _year = metadata.year or (tmdb_data or {}).get('year')
        decade = f"{(_year // 10) * 10}s" if _year else None

        # --- Country-to-wave satellite (Stage 4) ---
        country_wave_ev: dict = {'checked': False, 'matched': False}
        if readiness != 'R1' and metadata.country and decade:
            country_wave_ev['checked'] = True
            if metadata.country in COUNTRY_TO_WAVE:
                wave_config = COUNTRY_TO_WAVE[metadata.country]
                if decade in wave_config['decades']:
                    country_wave_ev['matched'] = True
                    country_wave_ev['category'] = wave_config['category']

        # --- Satellite evidence (Stage 5) — evidence_classify() is read-only ---
        sat_ev_obj = self.satellite_classifier.evidence_classify(metadata, tmdb_data)

        # Compute nearest-miss from per_category evidence
        nearest_miss = None
        gates_missing_for_nearest: list = []
        best_pass_count = 0
        # Priority order from SATELLITE_ROUTING_RULES iteration order (matches classify())
        for cat_name, cat_ev in sat_ev_obj.per_category.items():
            if cat_ev.matched:
                continue  # skip actual winner for near-miss calculation
            gates = [
                cat_ev.decade_gate,
                cat_ev.director_gate,
                cat_ev.country_gate,
                cat_ev.genre_gate,
                cat_ev.keyword_gate,
                cat_ev.title_kw_gate,
            ]
            pass_count = sum(1 for g in gates if g.status == 'pass')
            blocking = [
                name for name, g in [
                    ('decade_gate', cat_ev.decade_gate),
                    ('director_gate', cat_ev.director_gate),
                    ('country_gate', cat_ev.country_gate),
                    ('genre_gate', cat_ev.genre_gate),
                    ('keyword_gate', cat_ev.keyword_gate),
                    ('title_kw_gate', cat_ev.title_kw_gate),
                ]
                if g.status in ('fail', 'untestable')
                and g.status != 'not_applicable'
            ]
            if pass_count > best_pass_count:
                best_pass_count = pass_count
                nearest_miss = cat_name
                gates_missing_for_nearest = blocking

        # Serialize SatelliteEvidence.per_category to a JSON-safe dict
        def _gate_dict(g) -> dict:
            return {'status': g.status, 'value': g.value, 'reason': g.reason}

        sat_serialized: dict = {
            'matched_category': sat_ev_obj.matched_category,
            'per_category': {
                cat_name: {
                    'decade_gate':   _gate_dict(cat_ev.decade_gate),
                    'director_gate': _gate_dict(cat_ev.director_gate),
                    'country_gate':  _gate_dict(cat_ev.country_gate),
                    'genre_gate':    _gate_dict(cat_ev.genre_gate),
                    'keyword_gate':  _gate_dict(cat_ev.keyword_gate),
                    'title_kw_gate': _gate_dict(cat_ev.title_kw_gate),
                    'matched':       cat_ev.matched,
                }
                for cat_name, cat_ev in sat_ev_obj.per_category.items()
            },
        }

        # --- User tag stage ---
        user_tag_ev: dict = {'has_tag': bool(metadata.user_tag)}
        if metadata.user_tag:
            parsed_tag = self._parse_user_tag(metadata.user_tag)
            user_tag_ev['parsed'] = parsed_tag

        # --- Core director stage ---
        core_ev: dict = {'checked': False, 'matched': False}
        if readiness != 'R1' and metadata.director:
            core_ev['checked'] = True
            if self.core_db.is_core_director(metadata.director):
                core_ev['matched'] = True
                core_ev['canonical'] = self.core_db.get_canonical_name(metadata.director)

        # --- Popcorn stage ---
        popcorn_ev: dict = {'checked': False, 'matched': False, 'reason': None}
        if readiness != 'R1':
            popcorn_ev['checked'] = True
            popcorn_reason = self.popcorn_classifier.classify_reason(metadata, tmdb_data)
            if popcorn_reason:
                popcorn_ev['matched'] = True
                popcorn_ev['reason'] = popcorn_reason

        return {
            'data_readiness': readiness,
            'fields_present': fields_present,
            'fields_absent': fields_absent,
            'lookup': lookup_ev,
            'reference': reference_ev,
            'country_wave': country_wave_ev,
            'satellite': sat_serialized,
            'user_tag': user_tag_ev,
            'core': core_ev,
            'popcorn': popcorn_ev,
            'nearest_miss': nearest_miss,
            'gates_missing_for_nearest': gates_missing_for_nearest,
        }

    def write_evidence_trails(self, results: List[ClassificationResult], output_path: Path):
        """Write per-film evidence trails to a flat CSV (Issue #35).

        One row per film. Satellite per-category gates are flattened to individual
        columns (Option A — flat) so a curator can filter directly in a spreadsheet:
          Filter indie_cinema_country=pass AND indie_cinema_genre=untestable
          → the 44 R2b films from Issue #34.

        Films with no evidence_trail (Non-Film supplements) are skipped.
        """
        from lib.constants import SATELLITE_ROUTING_RULES

        # Build ordered list of categories for consistent column ordering
        categories = list(SATELLITE_ROUTING_RULES.keys())
        gate_names = ['decade', 'director', 'country', 'genre', 'keyword', 'title_kw']
        # Map gate_names → CategoryEvidence attribute names
        gate_attr_map = {
            'decade': 'decade_gate', 'director': 'director_gate',
            'country': 'country_gate', 'genre': 'genre_gate',
            'keyword': 'keyword_gate', 'title_kw': 'title_kw_gate',
        }

        # Base columns
        base_cols = [
            'filename', 'title', 'year', 'director', 'country',
            'data_readiness', 'tier', 'reason',
            'lookup_matched', 'reference_matched',
            'country_wave_matched', 'country_wave_category',
            'satellite_matched_category',
            'nearest_miss', 'gates_missing_for_nearest',
            'fields_absent',
        ]
        # Per-category gate columns: {cat_slug}_{gate}
        def _slug(name: str) -> str:
            return name.lower().replace(' ', '_').replace('/', '_')

        cat_cols = [
            f'{_slug(cat)}_{gate}'
            for cat in categories
            for gate in gate_names
        ]

        fieldnames = base_cols + cat_cols
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL,
                                    extrasaction='ignore')
            writer.writeheader()

            for result in results:
                if result.evidence_trail is None:
                    continue  # Non-Film supplements — no evidence collected

                ev = result.evidence_trail
                sat = ev.get('satellite', {})
                per_cat = sat.get('per_category', {})

                row: dict = {
                    'filename': result.filename,
                    'title': result.title,
                    'year': result.year or '',
                    'director': result.director or '',
                    'country': result.country or '',
                    'data_readiness': result.data_readiness,
                    'tier': result.tier,
                    'reason': result.reason,
                    'lookup_matched': ev.get('lookup', {}).get('matched', False),
                    'reference_matched': ev.get('reference', {}).get('matched', False),
                    'country_wave_matched': ev.get('country_wave', {}).get('matched', False),
                    'country_wave_category': ev.get('country_wave', {}).get('category', ''),
                    'satellite_matched_category': sat.get('matched_category', ''),
                    'nearest_miss': ev.get('nearest_miss', ''),
                    'gates_missing_for_nearest': ','.join(ev.get('gates_missing_for_nearest', [])),
                    'fields_absent': ','.join(ev.get('fields_absent', [])),
                }

                # Flatten per-category gate statuses
                for cat in categories:
                    cat_ev = per_cat.get(cat, {})
                    slug = _slug(cat)
                    for gate in gate_names:
                        gate_key = gate_attr_map[gate] if gate != 'title_kw' else 'title_kw_gate'
                        gate_data = cat_ev.get(gate_key, {})
                        if not gate_data:
                            gate_data = cat_ev.get(f'{gate}_gate', {})
                        row[f'{slug}_{gate}'] = gate_data.get('status', 'not_applicable')

                writer.writerow(row)

        logger.info(f"Wrote evidence trails ({sum(1 for r in results if r.evidence_trail)} films) to {output_path}")

    def print_stats(self, results: List[ClassificationResult]):
        """Print classification statistics"""
        tier_counts = defaultdict(int)
        for r in results:
            tier_counts[r.tier] += 1

        total = len(results)
        non_film = tier_counts.get('Non-Film', 0)
        film_total = total - non_film  # Films only (excludes supplements)
        classified = film_total - tier_counts.get('Unsorted', 0)

        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS (v1.0)")
        print("=" * 60)
        print(f"Total files processed: {total}")
        if non_film:
            print(f"  Non-film supplements filtered: {non_film}")
            print(f"  Films (excl. supplements):     {film_total}\n")
        else:
            print()

        print("BY TIER:")
        for tier in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted']:
            count = tier_counts.get(tier, 0)
            pct = (count / film_total * 100) if film_total > 0 else 0
            print(f"  {tier:15s}: {count:4d} ({pct:5.1f}%)")
        if non_film:
            print(f"  {'Non-Film':15s}: {non_film:4d} (excluded from rate)")

        print(f"\nBY REASON:")
        for reason, count in sorted(self.stats.items(), key=lambda x: -x[1]):
            if reason != 'errors':
                print(f"  {reason:30s}: {count:4d}")

        classification_rate = (classified / film_total * 100) if film_total > 0 else 0
        rate_label = f"{classified}/{film_total}"
        if non_film:
            rate_label += f" films (excl. {non_film} supplements)"
        print(f"\nClassification rate: {classification_rate:.1f}% ({rate_label})")

        if self.stats.get('errors'):
            print(f"Errors: {self.stats['errors']}")

        if self.tmdb:
            cache_stats = self.tmdb.get_cache_stats()
            print(f"\nTMDb: {cache_stats['misses']} API queries, "
                  f"{cache_stats['hits']} cache hits "
                  f"({cache_stats['hit_rate']:.0f}% hit rate)")

        # OMDb cache statistics
        if self.omdb:
            cache_stats = self.omdb.get_cache_stats()
            print(f"OMDb: {cache_stats['misses']} API queries, "
                  f"{cache_stats['hits']} cache hits "
                  f"({cache_stats['hit_rate']:.0f}% hit rate)")

        # API source attribution statistics
        api_stats = {k: v for k, v in self.stats.items()
                     if 'api' in k or 'from_' in k or k in ['tmdb_success', 'omdb_success']}
        if api_stats:
            print(f"\nAPI Data Sources:")
            for stat, count in sorted(api_stats.items()):
                print(f"  {stat:30s}: {count:4d}")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Classify films and generate sorting manifest (v1.0)',
        epilog="""
NEVER moves files. Only reads filenames and writes CSV.

Examples:
  python classify.py /path/to/films
  python classify.py /path/to/films --no-api
  python classify.py /path/to/films --no-tmdb   (legacy alias for --no-api)
  python classify.py /path/to/films --output output/my_manifest.csv
        """
    )
    parser.add_argument('source_dir', type=Path,
                       help='Directory containing film files')
    parser.add_argument('--output', '-o', type=Path,
                       default=Path('output/sorting_manifest.csv'),
                       help='Output CSV manifest path (default: output/sorting_manifest.csv)')
    parser.add_argument('--config', type=Path, default=Path('config_external.yaml'),
                       help='Configuration file (default: config_external.yaml)')
    parser.add_argument('--no-tmdb', '--no-api', action='store_true',
                       dest='no_tmdb',
                       help='Disable TMDb and OMDb API enrichment (offline classification)')

    args = parser.parse_args()

    if not args.source_dir.exists():
        logger.error(f"Source directory does not exist: {args.source_dir}")
        sys.exit(1)

    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    # Initialize classifier
    classifier = FilmClassifier(args.config, no_tmdb=args.no_tmdb)

    # Process
    logger.info(f"Scanning: {args.source_dir}")
    results = classifier.process_directory(args.source_dir)

    # Write outputs
    classifier.write_manifest(results, args.output)

    staging_path = args.output.parent / 'staging_report.txt'
    classifier.write_staging_report(results, staging_path)

    review_path = args.output.parent / 'review_queue.csv'
    classifier.write_review_queue(results, review_path)

    # Issue #35: Write per-film evidence trails
    evidence_path = args.output.parent / 'evidence_trails.csv'
    classifier.write_evidence_trails(results, evidence_path)

    # Print stats
    classifier.print_stats(results)

    return 0


if __name__ == '__main__':
    sys.exit(main())
