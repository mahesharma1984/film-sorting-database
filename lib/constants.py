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
    # NOTE: This mapping is a fallback used when OMDb/TMDb country data is unavailable.
    # Three entries have known failure modes — they are intentional defaults for THIS
    # collection's profile, but will misroute edge cases. OMDb country data (higher
    # priority in the merge) should correct these before this lookup is reached.
    'pt': 'BR',  # Portuguese → Brazil. FAILURE MODE: also catches Portuguese European
                 # films (country=PT). OMDb country data should override before this fires.
    'it': 'IT',  # Italian → Italy
    'fr': 'FR',  # French → France
    'es': 'ES',  # Spanish → Spain. FAILURE MODE: also catches Latin American films
                 # (MX, AR, CL, etc.) — but those countries lack COUNTRY_TO_WAVE entries
                 # so they fall to Unsorted, which is the correct behaviour.
    'de': 'DE',  # German → Germany
    'ja': 'JP',  # Japanese → Japan
    'zh': 'HK',  # Chinese → Hong Kong. FAILURE MODE: also catches mainland Chinese films
                 # (country=CN). OMDb country data should override before this fires.
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
#
# NOTE: France ('FR') is intentionally absent.
# French New Wave is director-only (see SATELLITE_ROUTING_RULES['French New Wave']).
# A French film with no matching director falls to European Sexploitation (FR + genre)
# or Unsorted — this is designed behaviour, not an omission.
# Adding 'FR' here would route every French film in the 1950s-1970s to French New Wave
# regardless of whether it has any connection to the Nouvelle Vague movement.
COUNTRY_TO_WAVE = {
    'BR': {
        'decades': ['1960s', '1970s', '1980s', '1990s'],  # widened (Issue #20)
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
    # PRIORITY ORDER: specific/director-driven categories first, catch-alls last
    # Rationale: first-match-wins; catch-alls (Indie Cinema, Classic Hollywood)
    # must come AFTER exploitation categories so director matches aren't overridden.

    # French New Wave: DIRECTOR-ONLY routing (Issue #14, audited Issue #22)
    # Must come first as decade-bounded director override (no country/genre fallback).
    #
    # Core directors (Godard, Varda, Chabrol, Demy, Duras) are caught at Stage 3
    # (Core check) and never reach this entry. Resnais, Rivette, and Rohmer are also
    # Core but appear here as a safety net — Core check fires first when core_db is
    # provided; these entries only activate when core_db=None.
    #
    # IMPORTANT: is_core_director() is decade-agnostic. If a director is Core in ANY
    # decade, ALL their films are intercepted by the Core guard in SatelliteClassifier.
    # Rohmer (Core 1990s) will have his 1960s FNW films routed to Core when core_db
    # is active. This is a known architectural quirk, not a bug to fix here.
    #
    # Issue #25: Core directors are now intentionally included in this list.
    # With Satellite routing before Core (Issue #25 pipeline reorder), these directors'
    # 1950s-1970s films route to Satellite/French New Wave. Their non-movement-period
    # work (1980s+) falls through to the Core director check as before.
    # Prestige films that should stay in Core are pinned via SORTING_DATABASE.md entries,
    # which fire before Satellite routing.
    #   Core directors added (Issue #25): Godard, Varda, Chabrol, Demy, Duras
    #   Non-Core directors (confirmed against whitelist, #22): Marker, Malle, Eustache, Truffaut, Robbe-Grillet
    #   Resnais and Rivette were already present (also Core directors — now correctly routed)
    'French New Wave': {
        'country_codes': [],  # Director-only (no country fallback)
        'decades': ['1950s', '1960s', '1970s'],  # 1958-1973 movement
        'genres': [],  # Director-only (no genre fallback)
        'directors': [
            'godard',         # Issue #25: Jean-Luc Godard — Core director, FNW period 1960s-1970s
            'varda',          # Issue #25: Agnès Varda — Core director, FNW period 1960s-1970s
            'chabrol',        # Issue #25: Claude Chabrol — Core director, FNW period 1960s-1970s
            'demy',           # Issue #25: Jacques Demy — Core director, FNW period 1960s-1970s
            'duras',          # Issue #25: Marguerite Duras — Core director, FNW period 1960s-1970s
            'marker', 'rohmer', 'resnais', 'rivette', 'malle', 'eustache',
            'truffaut',       # Issue #22: François Truffaut — confirmed not in Core whitelist
            'robbe-grillet',  # Issue #22: Alain Robbe-Grillet — confirmed not in Core whitelist
        ],
        'tier_b_eligible': True,  # Issue #29: TMDb tag alone can route without director match
        'keyword_signals': {
            'tmdb_tags': ['nouvelle vague', 'french new wave', 'new wave', 'cinéma vérité', 'cinema verite'],
            'text_terms': ['nouvelle vague', 'new wave', 'jump cut', 'cinéma vérité', 'left bank', 'french new wave'],
        },
    },

    # EXPLOITATION CATEGORIES (Issue #6, Issue #14)
    # These must come before catch-alls (Indie Cinema, Classic Hollywood)
    'Brazilian Exploitation': {
        'country_codes': ['BR'],
        'decades': ['1960s', '1970s', '1980s', '1990s'],  # widened (Issue #20): pornochanchada peak 1970-1989, broader tradition 1960s-1990s
        'genres': ['Drama', 'Crime', 'Thriller', 'Horror', 'Romance'],
        'directors': [],  # Country-driven, not director-driven
        'keyword_signals': {
            'tmdb_tags': ['pornochanchada', 'boca do lixo', 'brazilian exploitation'],
            'text_terms': ['pornochanchada', 'chanchada', 'boca do lixo', 'embrafilme', 'erotic comedy'],
        },
    },
    'Giallo': {
        'country_codes': ['IT'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Horror', 'Thriller', 'Mystery'],
        'directors': ['bava', 'argento', 'fulci', 'martino', 'soavi', 'lenzi'],
        'keyword_signals': {
            'tmdb_tags': ['giallo', 'italian horror', 'psychosexual thriller', 'black-gloved killer'],
            'text_terms': ['giallo', 'stylized violence', 'voyeurism', 'whodunit', 'fetishism',
                           'mystery thriller', 'slasher', 'italian genre'],
        },
    },
    'Pinku Eiga': {
        'country_codes': ['JP'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Drama', 'Romance'],
        'directors': [
            'wakamatsu', 'kumashiro', 'tanaka',
            'masumura',  # NEW: Yasuzō Masumura (Issue #6)
        ],
        'keyword_signals': {
            'tmdb_tags': ['pink film', 'roman porno', 'pinku eiga', 'nikkatsu', 'erotic drama'],
            'text_terms': ['pink film', 'roman porno', 'erotica', 'softcore', 'exploitation',
                           'pinku', 'nikkatsu'],
        },
    },
    'Japanese Exploitation': {  # NEW CATEGORY (Issue #6)
        'country_codes': ['JP'],
        'decades': ['1970s', '1980s'],
        'genres': ['Action', 'Crime', 'Thriller'],
        'directors': [
            'fukasaku',  # NEW: Kinji Fukasaku (Issue #6)
        ],
        'keyword_signals': {
            'tmdb_tags': ['yakuza', 'jidaigeki', 'toei', 'chambara', 'japanese crime film'],
            'text_terms': ['yakuza', 'gang war', 'crime syndicate', 'organized crime',
                           'samurai', 'yakuza film', 'toei'],
        },
    },
    'Hong Kong Action': {
        'country_codes': ['HK', 'CN'],
        'decades': ['1970s', '1980s', '1990s'],
        'genres': ['Action', 'Crime', 'Thriller'],
        'directors': [
            'tsui hark', 'ringo lam', 'john woo',
            'lam nai-choi',  # NEW: Lam Nai-Choi (Issue #6)
        ],
        'keyword_signals': {
            'tmdb_tags': ['martial arts', 'wuxia', 'kung fu', 'triad', 'heroic bloodshed',
                          'shaw brothers', 'hong kong action'],
            'text_terms': ['martial arts', 'kung fu', 'wuxia', 'swordplay', 'triad',
                           'heroic bloodshed', 'shaw brothers', 'golden harvest', 'category iii'],
        },
    },
    'Blaxploitation': {  # MOVED BEFORE American Exploitation (Issue #6 - priority order)
        'country_codes': ['US'],
        'decades': ['1970s', '1990s'],  # 1980s deliberately excluded: genre largely
                                         # collapsed after its commercial peak (1971-1975).
                                         # 1990s added for the resurgence (Boyz n the Hood,
                                         # Menace II Society, Ernest Dickerson, etc.).
        'genres': ['Action', 'Crime', 'Drama'],
        'directors': [
            'gordon parks', 'jack hill',
            'ernest dickerson', 'ernest r. dickerson',
        ],
        'keyword_signals': {
            'tmdb_tags': ['blaxploitation', 'african american', 'inner city', 'black power'],
            'text_terms': ['blaxploitation', 'soul', 'ghetto', 'black power',
                           'inner city', 'african american exploitation'],
        },
    },
    # Director-only routing — like French New Wave (no country gate).
    # Issue #27: Post-Production Code prestige studio cinema, c.1965–1985.
    # Must come BEFORE American Exploitation (both US 1960s-1980s; AmNH is more specific).
    # Coppola + Scorsese: minor/indie work routes here; prestige work → Core when whitelisted
    # (Core check fires first, so whitelisted directors never reach this entry).
    'American New Hollywood': {
        'country_codes': [],   # Director-only (adding US would auto-route all US films)
        'decades': ['1960s', '1970s', '1980s'],  # captures 1965-1985 span
        'genres': [],          # Director-only (no genre fallback)
        'directors': [
            'fosse',        # Bob Fosse — Category Core
            'ashby',        # Hal Ashby — Category Core
            'pakula',       # Alan J. Pakula — Category Core
            'pollack',      # Sydney Pollack — Category Reference
            'lumet',        # Sidney Lumet — Category Reference
            'bogdanovich',  # Peter Bogdanovich — Category Reference
            'altman',       # Robert Altman — Category Reference
            'coppola',      # Francis Ford Coppola — minor/indie work; prestige → Core when whitelisted
            'scorsese',     # Martin Scorsese — minor/indie work; prestige → Core when whitelisted
        ],
        'tier_b_eligible': True,  # Issue #29: TMDb tag alone can route without director match
        'keyword_signals': {
            'tmdb_tags': ['new hollywood', 'american new wave', 'counterculture', 'post-code'],
            'text_terms': ['new hollywood', 'new american cinema', 'post-production code',
                           'counterculture', 'auteur', 'vietnam era', 'anti-establishment'],
        },
    },
    'American Exploitation': {
        'country_codes': ['US'],
        'decades': ['1960s', '1970s', '1980s'],  # NARROWED (Issue #14): was 1960s-2000s
        'genres': ['Horror', 'Thriller', 'Crime'],
        'directors': [
            'russ meyer', 'abel ferrara', 'larry cohen', 'herschell gordon lewis',
            'larry clark',  # NEW: Larry Clark (Issue #6)
        ],
        'keyword_signals': {
            'tmdb_tags': ['grindhouse', 'exploitation film', 'b-movie', 'troma', 'slasher',
                          'drive-in movie'],
            'text_terms': ['grindhouse', 'drive-in', 'exploitation', 'splatter', 'gore',
                           'b-movie', 'troma', 'low budget horror', 'cult classic'],
        },
    },
    'European Sexploitation': {
        'country_codes': ['FR', 'IT', 'DE', 'BE'],
        'decades': ['1960s', '1970s', '1980s'],
        'genres': ['Romance', 'Drama'],  # Reordered to match Romance first
        'directors': [
            'borowczyk', 'metzger', 'brass', 'vadim',
            'jaeckin',  # NEW: Just Jaeckin (Emmanuelle) (Issue #14)
            'p\u00e9cas',  # Max Pécas (FR) — TMDb genres Crime/Thriller, director match needed
        ],
        'keyword_signals': {
            'tmdb_tags': ['erotic film', 'softcore', 'sexploitation', 'european erotica'],
            'text_terms': ['erotic film', 'softcore', 'erotica', 'sexploitation',
                           'adult film', 'european erotica'],
        },
    },
    'Music Films': {
        'country_codes': None,  # Any country
        'decades': None,  # Any decade (no restriction)
        'genres': ['Music', 'Musical', 'Documentary'],
        'directors': [],
        'keyword_signals': {
            'tmdb_tags': ['concert film', 'rockumentary', 'musical performance', 'rock documentary'],
            'text_terms': ['concert film', 'rockumentary', 'music documentary',
                           'concert', 'live performance'],
        },
    },

    # CATCH-ALL CATEGORIES (Issue #14, Issue #16)
    # These MUST come LAST — they are broad and will match many films.
    # Exploitation categories above must have priority.
    'Classic Hollywood': {
        'country_codes': ['US'],
        'decades': ['1930s', '1940s', '1950s'],
        'genres': None,  # Issue #16: genre gate removed - decade (1930s-1950s) + US is sufficient gate
        'directors': [],  # Country + decade driven, not director-specific
        'keyword_signals': {
            'tmdb_tags': ['film noir', 'pre-code', 'golden age of hollywood', 'screwball comedy',
                          'classical hollywood'],
            'text_terms': ['film noir', 'golden age', 'studio system', 'pre-code',
                           'screwball comedy', 'hays code', 'classical hollywood'],
        },
    },
    # Functional arthouse catch-all — NOT a historical wave category.
    # Catches non-exploitation, non-Popcorn, non-Core films from any major film nation.
    # Issue #16: moved to END so exploitation director films are caught first.
    # Issue #20: extended to 1960s-1970s + added CN, TW, KR, IR, JP, HU, IN, RO.
    # Note: unlike Giallo or Brazilian Exploitation (historical events with start/end
    # dates), Indie Cinema is defined negatively — by what it is NOT. JP in 1970s-1980s
    # still hits Pinku Eiga/Japanese Exploitation first; JP here only catches post-1980s
    # Japanese films that fall through those categories.
    #
    # US is intentionally NOT in country_codes. US already has Classic Hollywood
    # (1930s-1950s), American Exploitation (1960s-1980s), and Blaxploitation. US films
    # that don't match those categories should fall to Unsorted — not Indie Cinema.
    # US indie directors (Jarmusch, Hartley etc.) are covered by the directors list
    # below, which fires before the country+genre check.
    'Indie Cinema': {
        'country_codes': [
            # US intentionally excluded — US indie directors covered by directors list
            'GB', 'FR', 'DE', 'IT', 'ES', 'CA', 'AU', 'NL', 'BE',
            'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'PL', 'CZ', 'AR', 'MX', 'BR', 'CL',
            # Added (Issue #20): East/South Asian and underrepresented film nations
            'CN', 'TW', 'KR', 'IR', 'JP', 'HU', 'IN', 'RO',
            # Historical country codes: Czechoslovakia (pre-1993 split into CZ + SK)
            'CS', 'XC',
            # Additional European film nations
            'RU', 'GR', 'BG',
        ],
        'decades': ['1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'],  # extended back (Issue #20)
        'genres': ['Drama', 'Romance', 'Thriller', 'Science Fiction', 'Comedy',
                   'Fantasy', 'Mystery', 'History', 'War', 'Documentary', 'Music'],
                   # Comedy added: OMDb labels many arthouse films Comedy that TMDb would call Drama.
                   # Action/Crime/Horror intentionally excluded: block late-decade exploitation
                   # directors (Argento 2010s Horror, Fukasaku 2000s Crime) from landing here.
        'directors': [
            # US indie (director match fires regardless of country_codes exclusion)
            'jarmusch', 'hartley', 'linklater', 'reichardt', 'haynes', 'korine', 'araki', 'solondz',
            # Larry Clark: 1980s work is American Exploitation; 1990s+ (Kids, Bully, Ken Park) is indie
            'larry clark',
            # International indie (add more as needed)
            'denis', 'assayas', 'desplechin', 'haneke', 'trier', 'winterbottom', 'loach'
        ],
    },
}

# =============================================================================
# CERTAINTY TIERS (Issue #30 — confidence-gated routing)
# =============================================================================
# Maps each Satellite category to a certainty tier (1–4).
# Tier 1: 4+ corroborating signals (country + genre + decade + directors) → confidence 0.8
# Tier 2: 3 signals (director/country + decade + keywords) → confidence 0.7
# Tier 3: 2 weak signals (genre/country + decade, negative-space categories) → confidence 0.5
# Tier 4: manual only (auto-classification strongly discouraged) → confidence 0.3

CATEGORY_CERTAINTY_TIERS: dict = {
    # Tier 1 — high-certainty exploitation genres with distinctive genre+country+decade gates
    'Giallo': 1,
    'Brazilian Exploitation': 1,
    'Hong Kong Action': 1,
    'Pinku Eiga': 1,
    'American Exploitation': 1,
    'European Sexploitation': 1,
    'Blaxploitation': 1,
    # Tier 2 — named historical movements, director-anchored
    'Classic Hollywood': 2,
    'French New Wave': 2,
    'American New Hollywood': 2,
    # Tier 3 — negative-space / catch-all categories (weak gates)
    'Music Films': 3,
    'Indie Cinema': 3,
    # Tier 4 — manual curation only; auto-classification is strongly discouraged
    'Japanese Exploitation': 4,
    'Cult Oddities': 4,
}

# Confidence value assigned per certainty tier
TIER_CONFIDENCE: dict = {1: 0.8, 2: 0.7, 3: 0.5, 4: 0.3}

# Films classified below this confidence threshold go to the review queue (Issue #30)
REVIEW_CONFIDENCE_THRESHOLD: float = 0.5

# =============================================================================
# SATELLITE TENTPOLES (Thread Discovery Anchors - Issue #12)
# =============================================================================

# Tentpole films are canonical examples that define each Satellite category.
# Used for keyword-based thread discovery (read-only, never affects routing).
# Format: (title, year, director) - matches FilmMetadata structure
# IMPORTANT: All tentpoles must respect decade bounds from SATELLITE_ROUTING_RULES

SATELLITE_TENTPOLES = {
    'Giallo': [
        ('Blood and Black Lace', 1964, 'Mario Bava'),
        ('Deep Red', 1975, 'Dario Argento'),
        ('The Beyond', 1981, 'Lucio Fulci'),
        ('Tenebrae', 1982, 'Dario Argento'),
        ('A Bay of Blood', 1971, 'Mario Bava'),
    ],
    'Pinku Eiga': [
        ('Go Go Second Time Virgin', 1969, 'Kōji Wakamatsu'),
        ('Inflatable Sex Doll of the Wastelands', 1967, 'Kōji Wakamatsu'),
        ('Wife to Be Sacrificed', 1974, 'Masaru Konuma'),
        ('Violated Angels', 1967, 'Kōji Wakamatsu'),
    ],
    'Japanese Exploitation': [
        ('Battles Without Honor and Humanity', 1973, 'Kinji Fukasaku'),
        ('Street Mobster', 1972, 'Kinji Fukasaku'),
        ('Graveyard of Honor', 1975, 'Kinji Fukasaku'),
    ],
    'Brazilian Exploitation': [
        ('Escola Penal de Meninas Violentadas', 1977, 'Antonio Polo Galante'),
        ('A Super Fêmea', 1973, 'Aníbal Massaini Neto'),
        ('O Império do Desejo', 1981, 'Carlos Reichenbach'),
        ('Amadas e Violentadas', 1976, 'Jean Garrett'),
    ],
    'Hong Kong Action': [
        ('Drunken Master', 1978, 'Yuen Woo-ping'),
        ('The Killer', 1989, 'John Woo'),
        ('Peking Opera Blues', 1986, 'Tsui Hark'),
        ('City on Fire', 1987, 'Ringo Lam'),
    ],
    'American Exploitation': [
        ('Faster, Pussycat! Kill! Kill!', 1965, 'Russ Meyer'),
        ('Hollywood Chainsaw Hookers', 1988, 'Fred Olen Ray'),
        ('Ms. 45', 1981, 'Abel Ferrara'),
        ('Re-Animator', 1985, 'Stuart Gordon'),
    ],
    'European Sexploitation': [
        ('Emmanuelle', 1974, 'Just Jaeckin'),
        ('The Story of O', 1975, 'Just Jaeckin'),
        ('Immoral Tales', 1973, 'Walerian Borowczyk'),
    ],
    'Blaxploitation': [
        ('Shaft', 1971, 'Gordon Parks'),
        ('Coffy', 1973, 'Jack Hill'),
        ('Foxy Brown', 1974, 'Jack Hill'),
    ],
    'Music Films': [
        ('200 Motels', 1971, 'Frank Zappa'),
        ('Tommy', 1975, 'Ken Russell'),
        ('Louie Bluie', 1985, 'Terry Zwigoff'),
    ],
    # NEW CATEGORIES (Issue #14: Satellite Restructure v0.3)
    'French New Wave': [
        ('La jetée', 1962, 'Chris Marker'),
        ("My Night at Maud's", 1969, 'Eric Rohmer'),
        ('Last Year at Marienbad', 1961, 'Alain Resnais'),
        ('The 400 Blows', 1959, 'François Truffaut'),
    ],
    'Indie Cinema': [
        ('Stranger Than Paradise', 1984, 'Jim Jarmusch'),
        ('Slacker', 1990, 'Richard Linklater'),
        ('Trust', 1990, 'Hal Hartley'),
        ('Safe', 1995, 'Todd Haynes'),
    ],
    'Classic Hollywood': [
        ('Out of the Past', 1947, 'Jacques Tourneur'),
        ('The Big Sleep', 1946, 'Howard Hawks'),
        ('Gun Crazy', 1950, 'Joseph H. Lewis'),
        ('Kiss Me Deadly', 1955, 'Robert Aldrich'),
    ],
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
# NON-FILM CONTENT PREFIXES (for Parser inversion fix - Issue #20)
# =============================================================================

# Filenames starting with these tokens are supplementary content (interviews,
# trailers, shorts), not feature films. The parser checks potential_director
# against this list to avoid inverting "Interview - Director (Year)" into
# director="Interview", title="Director".
NON_FILM_PREFIXES = [
    'interview', 'interviews',
    'trailer', 'featurette',
    'short',
    'radio play',
    'video essay',
    'english version', 'french version', 'german version', 'italian version',
    'documentary',
    'behind the scenes',
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

# Enforce Reference canon cap — fires at import time (Issue #25 D6).
# ~50 films by design; cap is 55 to allow up to 5 alternate-normalization
# entries (e.g. the dual E.T. entry) without requiring cap adjustment.
# To add a film: remove a lower-priority entry first.
assert len(REFERENCE_CANON) <= 55, (
    f"REFERENCE_CANON has {len(REFERENCE_CANON)} entries (cap is 55). "
    "Remove entries before adding new ones."
)
