#!/usr/bin/env python3
"""
Shared constants for film classification system

Single source of truth for format signals, release tags, and other constants.
DO NOT duplicate these lists in other modules - import from here instead.
"""

# Format/edition signals that indicate special curation
# These are METADATA about the edition, not tier classification
FORMAT_SIGNALS = [
    '35mm',
    '16mm',
    '2k',
    '4k',
    'uhd',
    'scan',  # Film scan metadata (e.g., "35mm Scan")
    'fullscreen',  # Aspect ratio variant
    'hybrid',  # Hybrid cut/version
    'open matte',
    'extended',
    'unrated',
    "director's cut",
    "directors cut",  # Alternative spelling
    "editor's cut",
    "editors cut",  # Alternative spelling
    'redux',
    'final cut',
    'theatrical',
    'criterion',
    'remux',
    'commentary',
    'special edition',
    'remastered',
    'restored',
    'anniversary',
    'hbo chronological cut',
    'ib tech'
]

# Release group tags to strip from titles
# These are encoding/release metadata, not film metadata
RELEASE_TAGS = [
    'bluray',
    'bdrip',
    'brrip',
    'web-dl',
    'webrip',
    'dvdrip',
    'hdrip',
    'x264',
    'x265',
    'h264',
    'h265',
    'hevc',
    'aac',
    'ac3',
    'dts',
    'dts-hd',
    'eac3',
    'flac',
    '1080p',
    '720p',
    '2160p',
    '4k',  # Also in FORMAT_SIGNALS - intentional overlap
    'uhd',  # Also in FORMAT_SIGNALS - intentional overlap
    'hd',
    'hdr',
    'scan',
    'fullscreen',
    'hybrid',
    'matte',  # Will also catch "open matte" via FORMAT_SIGNALS
    'preview',
    'yify',
    'rarbg',
    'vxt',
    'tigole',
    'sartre',
    'nikt0',
    'baggerinc',
    'gypsy',
    'amzn',
    'nf',
    'hulu',
    'remastered',  # Also in FORMAT_SIGNALS - intentional overlap
    'restored',  # Also in FORMAT_SIGNALS - intentional overlap
    'anniversary',  # Also in FORMAT_SIGNALS - intentional overlap
    'repack'
]

# =============================================================================
# LANGUAGE DETECTION PATTERNS (for v0.2 language/country extraction)
# =============================================================================

# Format: (regex_pattern, language_code, country_code)
# Pattern is matched case-insensitively against filename
LANGUAGE_PATTERNS = [
    # Portuguese/Brazilian
    (r'\b(portuguese|português|dublado|legendado pt)\b', 'pt', 'BR'),
    (r'\b(brazilian|brasil)\b', 'pt', 'BR'),
    # Italian
    (r'\b(italian|italiano|ita audio)\b', 'it', 'IT'),
    (r'\bdual\s+it\s+and\s+en\b', 'it', 'IT'),
    # French
    (r'\b(french|français|francais|fr audio)\b', 'fr', 'FR'),
    (r'\bin french\b', 'fr', 'FR'),
    (r'\bem\s+francês\b', 'fr', 'FR'),
    # Spanish
    (r'\b(spanish|español|espanol|es audio)\b', 'es', 'ES'),
    # German
    (r'\b(german|deutsch|de audio)\b', 'de', 'DE'),
    # Japanese
    (r'\b(japanese|日本語|jp audio)\b', 'ja', 'JP'),
    # Chinese (Cantonese/Mandarin → Hong Kong context)
    (r'\b(cantonese|mandarin|chinese|中文|chinese audio)\b', 'zh', 'HK'),
    # Korean
    (r'\b(korean|한국어|kr audio)\b', 'ko', 'KR'),
    # Indian languages
    (r'\b(hindi|malayalam|tamil|telugu|bengali)\b', 'hi', 'IN'),
    # Russian
    (r'\b(russian|русский|ru audio)\b', 'ru', 'RU'),
    # Polish
    (r'\b(polish|polski|pl audio)\b', 'pl', 'PL'),
    # Hungarian
    (r'\b(hungarian|magyar|hu audio)\b', 'hu', 'HU'),
]

# =============================================================================
# LANGUAGE TO COUNTRY MAPPING
# =============================================================================

LANGUAGE_TO_COUNTRY = {
    'pt': 'BR',  # Portuguese → Brazil (for this collection's context)
    'it': 'IT',  # Italian → Italy
    'fr': 'FR',  # French → France
    'es': 'ES',  # Spanish → Spain
    'de': 'DE',  # German → Germany
    'ja': 'JP',  # Japanese → Japan
    'zh': 'HK',  # Chinese → Hong Kong (for this collection's context)
    'ko': 'KR',  # Korean → South Korea
    'hi': 'IN',  # Hindi → India
    'ru': 'RU',  # Russian → Russia
    'pl': 'PL',  # Polish → Poland
    'hu': 'HU',  # Hungarian → Hungary
}

# =============================================================================
# COUNTRY TO SATELLITE WAVE MAPPING (decade + category routing)
# =============================================================================

# Structure: country_code → {decades: [list], category: str}
# Conservative routing: only films in specified decades will route to Satellite
COUNTRY_TO_WAVE = {
    'BR': {
        'decades': ['1970s', '1980s'],
        'category': 'Brazilian Exploitation',
    },
    'IT': {
        'decades': ['1960s', '1970s', '1980s'],
        'category': 'Giallo',
    },
    'JP': {
        'decades': ['1960s', '1970s', '1980s'],
        'category': 'Pinku Eiga',
    },
    'HK': {
        'decades': ['1970s', '1980s', '1990s'],
        'category': 'Hong Kong Action',
    },
}

# =============================================================================
# SATELLITE ROUTING RULES (unified country + director + decade validation)
# =============================================================================

# Title keyword gates for categories prone to false positives
# These are conservative and only used as fallback when director match is absent.
BLAXPLOITATION_TITLE_KEYWORDS = [
    'shaft', 'coffy', 'foxy brown', 'blacula', 'blackenstein',
    'hell up in harlem', 'super fly', 'superfly', 'black caesar',
    'truck turner', 'friday foster', 'cooley high', 'drop squad',
    'tales from the hood', 'dolemite', 'sweet sweetback'
]

AMERICAN_EXPLOITATION_TITLE_KEYWORDS = [
    'grindhouse', 'exploitation', 'troma', 'nudie', 'sleaze',
    'chainsaw', 'hookers', 'massacre', 'cannibal', 'nunsploitation',
    'rape revenge', 'rape-revenge', 'blood', 'gore', 'splatter'
]

# Shared exploitation keywords used to avoid misrouting obvious exploitation films
# into Popcorn in late-stage fallback.
EXPLOITATION_TITLE_KEYWORDS = sorted(
    set(BLAXPLOITATION_TITLE_KEYWORDS + AMERICAN_EXPLOITATION_TITLE_KEYWORDS)
)

# Popcorn heuristics
POPCORN_MAINSTREAM_GENRES = [
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
    'Family', 'Fantasy', 'Science Fiction', 'Thriller'
]

POPCORN_MAINSTREAM_COUNTRIES = ['US', 'GB', 'CA', 'AU']

POPCORN_STRONG_FORMAT_SIGNALS = [
    '35mm', 'open matte', 'criterion', 'remux', 'ib tech',
    '4k', 'uhd', 'commentary', 'special edition'
]

POPCORN_STAR_ACTORS = [
    'jackie chan', 'chris tucker', 'eddie murphy', 'robin williams',
    'jim carrey', 'tom cruise', 'bruce willis', 'arnold schwarzenegger',
    'sylvester stallone', 'harrison ford', 'keanu reeves', 'nicolas cage',
    'mel gibson', 'will smith', 'samuel l jackson', 'denzel washington',
    'tom hanks', 'michael j. fox', 'christopher lloyd', 'matt damon',
    'ben affleck', 'julia roberts', 'cameron diaz', 'meryl streep',
    'nicole kidman'
]

# Structure: category → {country_codes, decades, genres, directors}
# All director-based routing MUST respect decade bounds (Issue #6 fix)
# This replaces the hardcoded director_mappings in satellite.py with decade validation
SATELLITE_ROUTING_RULES = {
    'Brazilian Exploitation': {
        'country_codes': ['BR'],
        'decades': ['1970s', '1980s'],
        'genres': ['Drama', 'Crime', 'Thriller', 'Horror', 'Romance'],
        'directors': [],  # Country-driven, not director-driven
    },
    'Giallo': {
        'country_codes': ['IT'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Horror', 'Thriller', 'Mystery'],
        'directors': ['bava', 'argento', 'fulci', 'martino', 'soavi', 'lenzi'],
    },
    'Pinku Eiga': {
        'country_codes': ['JP'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Drama', 'Romance'],
        'directors': [
            'wakamatsu', 'kumashiro', 'tanaka',
            'masumura',  # NEW: Yasuzō Masumura (Issue #6)
        ],
    },
    'Japanese Exploitation': {  # NEW CATEGORY (Issue #6)
        'country_codes': ['JP'],
        'decades': ['1970s', '1980s'],
        'genres': ['Action', 'Crime', 'Thriller'],
        'directors': [
            'fukasaku',  # NEW: Kinji Fukasaku (Issue #6)
        ],
    },
    'Hong Kong Action': {
        'country_codes': ['HK', 'CN'],
        'decades': ['1970s', '1980s', '1990s'],
        'genres': ['Action', 'Crime', 'Thriller'],
        'directors': [
            'tsui hark', 'ringo lam', 'john woo',
            'lam nai-choi',  # NEW: Lam Nai-Choi (Issue #6)
        ],
    },
    'Blaxploitation': {  # MOVED BEFORE American Exploitation (Issue #6 - priority order)
        'country_codes': ['US'],
        'decades': ['1970s', '1990s'],  # Extended to include 1990s for Ernest Dickerson
        'genres': ['Action', 'Crime', 'Drama'],
        'directors': [
            'gordon parks', 'jack hill',
            'ernest dickerson', 'ernest r. dickerson',
        ],
    },
    'American Exploitation': {
        'country_codes': ['US'],
        'decades': ['1960s', '1970s', '1980s', '1990s', '2000s'],
        'genres': ['Horror', 'Thriller', 'Crime'],
        'directors': [
            'russ meyer', 'abel ferrara', 'larry cohen', 'herschell gordon lewis',
            'larry clark',  # NEW: Larry Clark (Issue #6)
        ],
    },
    'European Sexploitation': {
        'country_codes': ['FR', 'IT', 'DE', 'BE'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Drama', 'Romance'],
        'directors': [
            'borowczyk', 'metzger', 'brass',
            'vadim',  # NEW: Roger Vadim (Issue #6)
        ],
    },
    'Music Films': {
        'country_codes': None,  # Any country
        'decades': None,  # Any decade (no restriction)
        'genres': ['Music', 'Musical', 'Documentary'],
        'directors': [],
    },
}

# =============================================================================
# SUBTITLE KEYWORDS (for Parser Bug 2 detection)
# =============================================================================

# Used to detect "Title - Subtitle (Year)" patterns that should NOT extract director
SUBTITLE_KEYWORDS = [
    'theatrical cut',
    'theatrical',
    'directors cut',
    "director's cut",
    'extended cut',
    'extended',
    'unrated cut',
    'unrated',
    'special edition',
    'collectors edition',
    "collector's edition",
    'ultimate edition',
    'redux',
    'final cut',
    'restored',
    'remastered',
    'complete cut',
    'definitive edition',
    'international cut',
    'open matte',
    'widescreen',
    'fullscreen',
    'anniversary edition',
]

# =============================================================================
# REFERENCE CANON HARDCODED LOOKUP (50 films from REFERENCE_CANON_LIST.md)
# =============================================================================

# Format: (normalized_title, year) → 'Reference'
# Titles are normalized using normalize_for_lookup() for consistency
# This enables exact matching against parsed film metadata
REFERENCE_CANON = {
    # 1930s-1940s (Classical Hollywood Foundation)
    ('citizen kane', 1941): 'Reference',
    ('casablanca', 1942): 'Reference',
    ('it happened one night', 1934): 'Reference',
    ('the awful truth', 1937): 'Reference',
    ('duck soup', 1933): 'Reference',
    ('laura', 1944): 'Reference',
    ('double indemnity', 1944): 'Reference',
    ('the southerner', 1945): 'Reference',
    ('rome open city', 1945): 'Reference',
    ('fallen angel', 1945): 'Reference',

    # 1950s (Classical Studio Peak + Transitions)
    ('sunset boulevard', 1950): 'Reference',
    ('all about eve', 1950): 'Reference',
    ('singin in the rain', 1952): 'Reference',
    ('the searchers', 1956): 'Reference',
    ('sweet smell of success', 1957): 'Reference',
    ('vertigo', 1958): 'Reference',
    ('north by northwest', 1959): 'Reference',
    ('some like it hot', 1959): 'Reference',
    ('the apartment', 1960): 'Reference',
    ('psycho', 1960): 'Reference',
    ('rashomon', 1950): 'Reference',
    ('seven samurai', 1954): 'Reference',
    ('tokyo story', 1953): 'Reference',
    ('ugetsu', 1953): 'Reference',

    # 1960s (Canonical 60s - Not Core Auteurs)
    ('lawrence of arabia', 1962): 'Reference',
    ('the graduate', 1967): 'Reference',
    ('bonnie and clyde', 1967): 'Reference',
    ('the wild bunch', 1969): 'Reference',
    ('midnight cowboy', 1969): 'Reference',

    # 1970s (New Hollywood Canonical - Not Core)
    ('chinatown', 1974): 'Reference',
    ('one flew over the cuckoos nest', 1975): 'Reference',
    ('network', 1976): 'Reference',
    ('annie hall', 1977): 'Reference',
    ('star wars', 1977): 'Reference',
    ('close encounters of the third kind', 1977): 'Reference',
    ('alien', 1979): 'Reference',

    # 1980s-1990s (Modern Canonical Gaps)
    ('blade runner', 1982): 'Reference',
    ('et the extraterrestrial', 1982): 'Reference',
    ('e t the extraterrestrial', 1982): 'Reference',  # Alternative normalization
    ('the terminator', 1984): 'Reference',
    ('back to the future', 1985): 'Reference',
    ('aliens', 1986): 'Reference',
    ('die hard', 1988): 'Reference',
    ('pulp fiction', 1994): 'Reference',
    ('schindlers list', 1993): 'Reference',
    ('jurassic park', 1993): 'Reference',
    ('the matrix', 1999): 'Reference',
    ('saving private ryan', 1998): 'Reference',
    ('the silence of the lambs', 1991): 'Reference',
    ('unforgiven', 1992): 'Reference',
    ('the piano', 1993): 'Reference',
}
