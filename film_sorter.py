#!/usr/bin/env python3
"""
Automated Film Library Sorting Script
=====================================

Implements the decade-wave cinema archive system by parsing film metadata
from filenames and moving files to appropriate decade/tier folder structure.

Based on the comprehensive sorting rules defined in the project documentation.
"""

import os
import sys
import re
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

import yaml
import requests
from fuzzywuzzy import fuzz
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FilmMetadata:
    """Container for film metadata extracted from filename or API"""
    filename: str
    title: str
    year: Optional[int] = None
    director: Optional[str] = None
    edition: Optional[str] = None  # 35mm, Open Matte, Extended, etc.
    format_signals: List[str] = None
    
    def __post_init__(self):
        if self.format_signals is None:
            self.format_signals = []


@dataclass
class SortingDecision:
    """Container for sorting decision and destination path"""
    tier: str  # Core, Reference, Satellite, Popcorn, Staging
    decade: Optional[str] = None
    subdirectory: Optional[str] = None  # Director for Core, Category for Satellite
    confidence: float = 1.0
    reason: str = ""


class FilenameParser:
    """Parse film metadata from various filename patterns"""

    # Common filename patterns - order matters!
    PATTERNS = [
        r'^(.+?)\s+-\s+(.+?)\s+\((\d{4})\)',        # Director - Film Title (Year)
        r'^(.+?)\s+-\s+(.+?)\s+(\d{4})',            # Director - Film Title Year
        r'^(.+?)\s*\((\d{4})\)',                    # Film Title (Year)
        r'^(.+?)\s*\[(\d{4})\]',                    # Film Title [Year]
        r'^(.+?)\s+(\d{4})(?!\d)',                  # Film Title Year (not followed by more digits)
    ]

    # Format/edition signals that indicate special curation
    FORMAT_SIGNALS = [
        '35mm', 'open matte', 'extended', 'director\'s cut', 'editor\'s cut',
        'unrated', 'redux', 'final cut', 'theatrical', 'criterion',
        '4k', 'uhd', 'remux', 'commentary', 'special edition'
    ]

    # Release group tags to strip from titles
    RELEASE_TAGS = [
        'bluray', 'bdrip', 'brrip', 'web-dl', 'webrip', 'dvdrip', 'hdrip',
        'x264', 'x265', 'h264', 'h265', 'hevc', 'aac', 'ac3', 'dts',
        '1080p', '720p', '2160p', '4k', 'uhd', 'hd',
        'yify', 'rarbg', 'vxt', 'tigole', 'amzn', 'nf', 'hulu'
    ]

    def _clean_title(self, title: str) -> str:
        """Clean and normalize title from various filename formats"""
        # Replace dots/underscores with spaces (scene release format)
        title = title.replace('.', ' ').replace('_', ' ')

        # Remove release group tags and quality indicators
        title_lower = title.lower()
        for tag in self.RELEASE_TAGS:
            # Find tag and remove everything after it
            idx = title_lower.find(tag)
            if idx != -1:
                title = title[:idx]
                title_lower = title_lower[:idx]

        # Clean up extra spaces
        title = ' '.join(title.split())

        # Basic title case (can be improved)
        title = title.strip()

        return title

    def _extract_year(self, name: str) -> Optional[Tuple[int, str]]:
        """Extract year from filename, returns (year, cleaned_name) or None"""
        # Try multiple year patterns in order of specificity
        year_patterns = [
            r'\((\d{4})\)',           # (1999)
            r'\[(\d{4})\]',           # [1969]
            r'[\.\s](\d{4})[\.\s]',   # .1984. or space-delimited
        ]

        for pattern in year_patterns:
            match = re.search(pattern, name)
            if match:
                year = int(match.group(1))
                # Validate year range (avoid matching resolutions like 1080, 2160)
                if 1920 <= year <= 2029:
                    # Remove the year from the name for cleaner title
                    cleaned = name[:match.start()] + name[match.end():]
                    return year, cleaned

        return None

    def parse(self, filename: str) -> FilmMetadata:
        """Extract metadata from filename"""
        # Remove file extension
        name = Path(filename).stem

        # Extract format signals
        format_signals = []
        name_lower = name.lower()
        for signal in self.FORMAT_SIGNALS:
            if signal in name_lower:
                format_signals.append(signal)

        # Try structured patterns first (with director)
        for i, pattern in enumerate(self.PATTERNS[:2]):  # First 2 are director patterns
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # (director, title, year)
                    director, title, year = groups
                    return FilmMetadata(
                        filename=filename,
                        title=self._clean_title(title),
                        year=int(year),
                        director=director.strip(),
                        format_signals=format_signals
                    )

        # Try title + year patterns
        for pattern in self.PATTERNS[2:]:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:  # (title, year)
                    title, year = groups
                    return FilmMetadata(
                        filename=filename,
                        title=self._clean_title(title),
                        year=int(year),
                        format_signals=format_signals
                    )

        # Fallback: try to extract year from anywhere in filename
        year_result = self._extract_year(name)
        if year_result:
            year, cleaned_name = year_result
            title = self._clean_title(cleaned_name)
            logger.info(f"Extracted year {year} from: {filename}")
            return FilmMetadata(
                filename=filename,
                title=title,
                year=year,
                format_signals=format_signals
            )

        # Last resort: just use filename as title
        logger.warning(f"Could not parse filename pattern: {filename}")
        return FilmMetadata(
            filename=filename,
            title=self._clean_title(name),
            format_signals=format_signals
        )


class CoreDirectorDatabase:
    """Load and query Core director whitelist"""
    
    def __init__(self, whitelist_file: Path):
        self.directors_by_decade = defaultdict(set)
        self.all_directors = set()
        self._load_whitelist(whitelist_file)
    
    def _load_whitelist(self, file_path: Path):
        """Parse the Core director whitelist markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_decade = None
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Detect decade headers
                if re.match(r'## \d{4}s CORE', line):
                    decade_match = re.search(r'(\d{4})s', line)
                    if decade_match:
                        current_decade = decade_match.group(1) + 's'
                        continue
                
                # Extract director names (bold text)
                director_match = re.match(r'\*\*([^*]+)\*\*', line)
                if director_match and current_decade:
                    director = director_match.group(1).strip()
                    self.directors_by_decade[current_decade].add(director)
                    self.all_directors.add(director)
            
            logger.info(f"Loaded {len(self.all_directors)} core directors across {len(self.directors_by_decade)} decades")
            
        except Exception as e:
            logger.error(f"Error loading core director whitelist: {e}")
    
    def is_core_director(self, director_name: str) -> bool:
        """Check if director is in Core whitelist (fuzzy matching)"""
        if not director_name:
            return False
        
        director_lower = director_name.lower().strip()
        
        # Exact match first
        for core_director in self.all_directors:
            if director_lower == core_director.lower():
                return True
        
        # Fuzzy matching for variations
        for core_director in self.all_directors:
            core_lower = core_director.lower()
            
            # High similarity match
            if fuzz.ratio(director_lower, core_lower) > 85:
                return True
            
            # Partial match for shortened names (e.g. "Godard" matches "Jean-Luc Godard")
            if len(director_lower) > 3 and director_lower in core_lower:
                return True
            
            # Check if last name matches
            core_parts = core_lower.split()
            director_parts = director_lower.split()
            
            if len(core_parts) > 1 and len(director_parts) > 0:
                if director_parts[-1] == core_parts[-1]:  # Last name match
                    return True
        
        return False
    
    def get_director_decades(self, director_name: str) -> List[str]:
        """Get decades where director appears in Core whitelist"""
        if not director_name:
            return []
        
        decades = []
        director_lower = director_name.lower().strip()
        
        for decade, directors in self.directors_by_decade.items():
            for core_director in directors:
                core_lower = core_director.lower()
                
                # Check multiple matching strategies
                if (director_lower == core_lower or 
                    fuzz.ratio(director_lower, core_lower) > 85 or
                    (len(director_lower) > 3 and director_lower in core_lower) or
                    (len(director_lower.split()) > 0 and len(core_lower.split()) > 1 and 
                     director_lower.split()[-1] == core_lower.split()[-1])):
                    decades.append(decade)
                    break
        
        return decades


class ReferenceCanonDatabase:
    """Load and query Reference canon films"""
    
    def __init__(self, canon_file: Path):
        self.reference_films = []
        self._load_canon(canon_file)
    
    def _load_canon(self, file_path: Path):
        """Parse Reference canon markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract numbered film entries
            pattern = r'\d+\.\s*\*\*([^*]+)\*\*\s*\((\d{4})\)'
            matches = re.findall(pattern, content)
            
            for title, year in matches:
                self.reference_films.append({
                    'title': title.strip(),
                    'year': int(year)
                })
            
            logger.info(f"Loaded {len(self.reference_films)} reference films")
            
        except Exception as e:
            logger.error(f"Error loading reference canon: {e}")
    
    def is_reference_film(self, title: str, year: int) -> bool:
        """Check if film is in Reference canon"""
        for ref_film in self.reference_films:
            title_match = fuzz.ratio(title.lower(), ref_film['title'].lower()) > 85
            year_match = year == ref_film['year']
            
            if title_match and year_match:
                return True
        
        return False


class SatelliteCategories:
    """Handle Satellite category classification"""
    
    def __init__(self, categories_file: Path):
        self.categories = {
            'Giallo': {
                'keywords': ['giallo', 'italian', 'horror', 'thriller'],
                'directors': ['bava', 'argento', 'fulci', 'martino'],
                'cap': 30
            },
            'Pinku Eiga': {
                'keywords': ['pinku', 'pink', 'roman porno'],
                'directors': ['wakamatsu'],
                'cap': 35
            },
            'Brazilian Exploitation': {
                'keywords': ['escola', 'amor', 'desejo', 'brasil', 'rio'],
                'directors': ['candeias', 'reichenbach'],
                'cap': 45,
                'language_pattern': r'[áàâãçéêíóôõú]'  # Portuguese characters
            },
            'Hong Kong Action': {
                'keywords': ['hong kong', 'martial arts', 'category iii'],
                'directors': ['tsui hark', 'ringo lam'],
                'cap': 65
            },
            'American Exploitation': {
                'keywords': ['exploitation', 'grindhouse', 'chainsaw', 'brain'],
                'directors': ['russ meyer', 'abel ferrara'],
                'cap': 80
            },
            'European Sexploitation': {
                'keywords': ['emanuelle', 'love', 'seduction'],
                'directors': ['borowczyk', 'metzger'],
                'cap': 25
            },
            'Blaxploitation': {
                'keywords': ['coffy', 'foxy', 'shaft', 'hell up in harlem'],
                'directors': ['gordon parks'],
                'cap': 20
            },
            'Music Films': {
                'keywords': ['concert', 'rock', 'roll', 'blues', 'motels'],
                'directors': ['zwigoff'],
                'cap': 20
            },
            'Cult Oddities': {
                'keywords': ['weird', 'bizarre', 'midnight', 'cult'],
                'directors': [],
                'cap': 50
            }
        }
    
    def classify_satellite(self, metadata: FilmMetadata) -> Optional[str]:
        """Attempt to classify film into Satellite category"""
        title_lower = metadata.title.lower()
        
        # Check for Brazilian films (Portuguese characters)
        if re.search(self.categories['Brazilian Exploitation']['language_pattern'], metadata.title):
            return 'Brazilian Exploitation'
        
        # Check each category
        for category_name, category_info in self.categories.items():
            # Check keywords in title
            for keyword in category_info['keywords']:
                if keyword in title_lower:
                    return category_name
            
            # Check directors if available
            if metadata.director:
                director_lower = metadata.director.lower()
                for director in category_info['directors']:
                    if director in director_lower:
                        return category_name
        
        return None


class TMDbAPI:
    """Interface to The Movie Database API for metadata enrichment"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
    
    def search_film(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Search for film and return metadata"""
        if not self.api_key:
            return None
        
        try:
            params = {
                'api_key': self.api_key,
                'query': title,
                'include_adult': True
            }
            
            if year:
                params['year'] = year
            
            response = requests.get(f"{self.base_url}/search/movie", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['results']:
                # Get director from credits
                film_id = data['results'][0]['id']
                credits_response = requests.get(
                    f"{self.base_url}/movie/{film_id}/credits",
                    params={'api_key': self.api_key}
                )
                credits_response.raise_for_status()
                
                credits_data = credits_response.json()
                director = None
                
                for crew_member in credits_data.get('crew', []):
                    if crew_member['job'] == 'Director':
                        director = crew_member['name']
                        break
                
                return {
                    'title': data['results'][0]['title'],
                    'year': int(data['results'][0]['release_date'][:4]) if data['results'][0]['release_date'] else None,
                    'director': director
                }
        
        except Exception as e:
            logger.debug(f"TMDb API error for '{title}': {e}")
        
        return None


class FilmSorter:
    """Main film sorting engine"""
    
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.setup_components()
        
        # Statistics
        self.stats = defaultdict(int)
        self.movements = []  # Track all file movements
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def setup_components(self):
        """Initialize all sorting components"""
        project_path = Path(self.config['project_path'])
        
        # Validate external drive availability
        self._validate_external_drive()
        
        self.parser = FilenameParser()
        self.core_db = CoreDirectorDatabase(project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md')
        self.reference_db = ReferenceCanonDatabase(project_path / 'REFERENCE_CANON_LIST.md')
        self.satellite_db = SatelliteCategories(project_path / 'SATELLITE_CATEGORIES.md')
        
        # Initialize TMDb API if key provided
        tmdb_key = self.config.get('tmdb_api_key')
        self.tmdb = TMDbAPI(tmdb_key) if tmdb_key else None

        if self.tmdb:
            logger.info("✓ TMDb API enrichment enabled")
        else:
            logger.warning("⚠ TMDb API enrichment disabled (no API key) - director lookup limited to filenames only")
            logger.warning("  Get a free API key at: https://www.themoviedb.org/settings/api")
    
    def _validate_external_drive(self):
        """Validate external drive is available and has sufficient space"""
        library_path = Path(self.config['library_path'])
        
        # Check if verify_available is enabled
        if self.config.get('external_drive', {}).get('verify_available', True):
            if not library_path.parent.exists():
                raise FileNotFoundError(
                    f"External drive not found: {library_path.parent}\n"
                    "Please ensure the external drive is connected and mounted."
                )
            
            logger.info(f"✓ External drive detected: {library_path.parent}")
            
            # Check available space (optional warning)
            try:
                import shutil
                total, used, free = shutil.disk_usage(library_path.parent)
                free_gb = free // (1024**3)
                logger.info(f"Available space: {free_gb} GB")
                
                if free_gb < 10:
                    logger.warning(f"Low disk space: {free_gb} GB remaining")
            except Exception as e:
                logger.debug(f"Could not check disk space: {e}")
    
    def get_decade(self, year: int) -> str:
        """Convert year to decade string"""
        decade = (year // 10) * 10
        return f"{decade}s"
    
    def detect_popcorn_signals(self, metadata: FilmMetadata) -> bool:
        """Detect if film has Popcorn format curation signals"""
        popcorn_signals = ['35mm', 'open matte', 'extended', 'director\'s cut', 'editor\'s cut']
        return any(signal in metadata.format_signals for signal in popcorn_signals)
    
    def enrich_metadata(self, metadata: FilmMetadata) -> FilmMetadata:
        """Enrich metadata using TMDb API if director missing"""
        if not metadata.director and self.tmdb and metadata.year:
            tmdb_data = self.tmdb.search_film(metadata.title, metadata.year)
            if tmdb_data and tmdb_data['director']:
                metadata.director = tmdb_data['director']
                logger.info(f"Enriched '{metadata.title}' with director: {metadata.director}")
        
        return metadata
    
    def classify_film(self, metadata: FilmMetadata) -> SortingDecision:
        """Main classification logic - implements the decision tree"""
        
        # Enrich metadata if needed
        metadata = self.enrich_metadata(metadata)
        
        # Must have year to determine decade
        if not metadata.year:
            return SortingDecision(
                tier='Staging',
                subdirectory='Unknown',
                confidence=0.0,
                reason='No year found in filename'
            )
        
        decade = self.get_decade(metadata.year)
        
        # 1. Check Core director whitelist (highest priority)
        if metadata.director and self.core_db.is_core_director(metadata.director):
            director_decades = self.core_db.get_director_decades(metadata.director)
            
            # Use film's decade if director appears in multiple decades
            if decade in director_decades:
                target_decade = decade
            else:
                # Use first decade where director appears
                target_decade = director_decades[0] if director_decades else decade
            
            return SortingDecision(
                tier='Core',
                decade=target_decade,
                subdirectory=metadata.director,
                confidence=1.0,
                reason=f'Director {metadata.director} on Core whitelist'
            )
        
        # 2. Check Reference canon
        if self.reference_db.is_reference_film(metadata.title, metadata.year):
            return SortingDecision(
                tier='Reference',
                decade=decade,
                confidence=1.0,
                reason='Film in Reference canon'
            )
        
        # 3. Check Satellite categories
        satellite_category = self.satellite_db.classify_satellite(metadata)
        if satellite_category:
            return SortingDecision(
                tier='Satellite',
                decade=decade,
                subdirectory=satellite_category,
                confidence=0.8,
                reason=f'Classified as {satellite_category}'
            )
        
        # 4. Check Popcorn signals
        if self.detect_popcorn_signals(metadata):
            return SortingDecision(
                tier='Popcorn',
                decade=decade,
                confidence=0.7,
                reason=f'Format signals: {", ".join(metadata.format_signals)}'
            )
        
        # 5. Everything else goes to Staging
        if not metadata.director:
            return SortingDecision(
                tier='Staging',
                subdirectory='Unknown',
                confidence=0.0,
                reason='No director information available'
            )
        else:
            return SortingDecision(
                tier='Staging',
                subdirectory='Borderline',
                confidence=0.0,
                reason='Could not classify automatically'
            )
    
    def create_folder_structure(self):
        """Create the complete decade/tier folder structure"""
        library_path = Path(self.config['library_path'])
        decades = ['1950s', '1960s', '1970s', '1980s', '1990s', '2000s', '2010s']
        tiers = ['Core', 'Reference', 'Satellite', 'Popcorn']
        
        # Create decade folders
        for decade in decades:
            decade_path = library_path / decade
            for tier in tiers:
                (decade_path / tier).mkdir(parents=True, exist_ok=True)
        
        # Create staging folders
        staging_path = library_path / 'Staging'
        for subdir in ['Borderline', 'Unwatched', 'Unknown', 'Evaluate']:
            (staging_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Create Out folder
        (library_path / 'Out' / 'Cut').mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created folder structure at {library_path}")
    
    def get_destination_path(self, decision: SortingDecision, metadata: FilmMetadata) -> Path:
        """Calculate destination path based on sorting decision"""
        library_path = Path(self.config['library_path'])
        
        if decision.tier == 'Staging':
            return library_path / 'Staging' / decision.subdirectory
        
        elif decision.tier in ['Core', 'Reference', 'Satellite', 'Popcorn']:
            decade_path = library_path / decision.decade / decision.tier
            
            if decision.subdirectory:
                return decade_path / decision.subdirectory
            else:
                return decade_path
        
        else:
            # Fallback
            return library_path / 'Staging' / 'Unknown'
    
    def move_file(self, source_file: Path, dest_path: Path, dry_run: bool = True):
        """Move file to destination (or simulate if dry_run)"""
        dest_file = dest_path / source_file.name
        
        # External drive safety checks
        if not dry_run:
            # Check source file still exists
            if not source_file.exists():
                logger.error(f"Source file disappeared: {source_file}")
                return False
            
            # Check if destination drive is still available
            if not dest_path.parent.exists():
                logger.error(f"Destination drive unavailable: {dest_path.parent}")
                return False
        
        # Ensure destination directory exists
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Handle duplicate filenames
        counter = 1
        original_dest = dest_file
        while dest_file.exists():
            stem = original_dest.stem
            suffix = original_dest.suffix
            dest_file = dest_path / f"{stem}_{counter}{suffix}"
            counter += 1
        
        if dry_run:
            logger.info(f"DRY RUN: Would move {source_file} -> {dest_file}")
        else:
            try:
                # External drive specific timeout
                move_timeout = self.config.get('performance', {}).get('move_timeout', 300)
                
                # For external drives, use copy + verify + delete instead of move for safety
                if self._is_external_drive_operation(source_file, dest_file):
                    logger.debug(f"External drive operation detected")
                    shutil.copy2(str(source_file), str(dest_file))
                    
                    # Verify copy succeeded
                    if dest_file.exists() and dest_file.stat().st_size == source_file.stat().st_size:
                        source_file.unlink()  # Delete original only after successful copy
                        logger.info(f"Safely moved {source_file} -> {dest_file}")
                    else:
                        logger.error(f"Copy verification failed: {dest_file}")
                        if dest_file.exists():
                            dest_file.unlink()  # Clean up failed copy
                        return False
                else:
                    # Standard move for same-drive operations
                    shutil.move(str(source_file), str(dest_file))
                    logger.info(f"Moved {source_file} -> {dest_file}")
                
                # Small delay for external drives
                batch_delay = self.config.get('performance', {}).get('batch_delay', 0.1)
                if batch_delay > 0:
                    import time
                    time.sleep(batch_delay)
                    
            except Exception as e:
                logger.error(f"Error moving {source_file}: {e}")
                return False
        
        # Track movement for manifest
        self.movements.append({
            'source': str(source_file),
            'destination': str(dest_file),
            'dry_run': dry_run
        })
        
        return True
    
    def _is_external_drive_operation(self, source: Path, dest: Path) -> bool:
        """Check if operation involves different filesystems/devices"""
        try:
            return source.stat().st_dev != dest.parent.stat().st_dev
        except Exception:
            # If we can't stat (e.g., dest parent missing), assume external for safety
            return True
    
    def process_directory(self, source_dir: Path, dry_run: bool = True):
        """Process all films in source directory"""

        logger.info(f"Processing directory: {source_dir}")
        logger.info(f"Dry run mode: {dry_run}")

        # Create folder structure
        self.create_folder_structure()

        # Get all video files
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg', '.mpeg'}
        video_files = []
        skipped_resource_forks = 0

        for file_path in source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                # Skip macOS resource fork files (._filename)
                if file_path.name.startswith('._'):
                    skipped_resource_forks += 1
                    continue
                video_files.append(file_path)

        if skipped_resource_forks > 0:
            logger.info(f"Skipped {skipped_resource_forks} macOS resource fork files")
        logger.info(f"Found {len(video_files)} video files")
        
        # Process each file
        results = []
        
        for source_file in video_files:
            try:
                # Parse metadata
                metadata = self.parser.parse(source_file.name)
                
                # Classify film
                decision = self.classify_film(metadata)
                
                # Calculate destination
                dest_path = self.get_destination_path(decision, metadata)
                
                # Move file
                success = self.move_file(source_file, dest_path, dry_run)
                
                # Track statistics
                self.stats[decision.tier] += 1
                
                # Store result
                results.append({
                    'filename': source_file.name,
                    'title': metadata.title,
                    'year': metadata.year,
                    'director': metadata.director,
                    'tier': decision.tier,
                    'decade': decision.decade,
                    'subdirectory': decision.subdirectory,
                    'confidence': decision.confidence,
                    'reason': decision.reason,
                    'destination': str(dest_path),
                    'success': success
                })
                
            except Exception as e:
                logger.error(f"Error processing {source_file}: {e}")
                self.stats['Error'] += 1
        
        return results
    
    def generate_reports(self, results: List[Dict], output_dir: Path):
        """Generate sorting manifest and staging report"""
        
        # Create manifest CSV
        df = pd.DataFrame(results)
        manifest_path = output_dir / 'sorting_manifest.csv'
        df.to_csv(manifest_path, index=False)
        logger.info(f"Generated manifest: {manifest_path}")
        
        # Create staging report
        staging_films = [r for r in results if r['tier'] == 'Staging']
        staging_path = output_dir / 'staging_report.txt'
        
        with open(staging_path, 'w', encoding='utf-8') as f:
            f.write("FILMS REQUIRING MANUAL REVIEW\n")
            f.write("=" * 40 + "\n\n")
            
            for film in staging_films:
                f.write(f"File: {film['filename']}\n")
                f.write(f"Title: {film['title']}\n")
                f.write(f"Year: {film['year']}\n")
                f.write(f"Director: {film['director']}\n")
                f.write(f"Reason: {film['reason']}\n")
                f.write(f"Destination: {film['destination']}\n")
                f.write("-" * 40 + "\n")
        
        logger.info(f"Generated staging report: {staging_path}")
        
        # Print statistics
        logger.info("\nSORTING STATISTICS:")
        logger.info("=" * 30)
        total_films = sum(self.stats.values())
        
        for tier, count in self.stats.items():
            percentage = (count / total_films * 100) if total_films > 0 else 0
            logger.info(f"{tier:15s}: {count:4d} ({percentage:5.1f}%)")
        
        logger.info(f"{'TOTAL':15s}: {total_films:4d}")
        
        staging_rate = (self.stats.get('Staging', 0) / total_films * 100) if total_films > 0 else 0
        logger.info(f"\nStaging rate: {staging_rate:.1f}% (target: <10%)")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Film Library Sorting')
    parser.add_argument('source', help='Source directory containing films')
    parser.add_argument('--config', default='config.yaml', help='Configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Preview moves without executing')
    parser.add_argument('--output', default='output', help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Check paths
    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        sys.exit(1)
    
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)
    
    # Initialize sorter
    try:
        sorter = FilmSorter(config_path)
    except Exception as e:
        logger.error(f"Failed to initialize sorter: {e}")
        sys.exit(1)
    
    # Process directory
    try:
        results = sorter.process_directory(source_path, dry_run=args.dry_run)
        sorter.generate_reports(results, output_path)
        
        logger.info("Sorting completed successfully!")
        
    except Exception as e:
        logger.error(f"Sorting failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
