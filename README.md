# Automated Film Library Sorting Script

Implements the tier-first cinema archive system by automatically parsing film metadata from filenames and moving files to the appropriate tier/decade folder structure based on comprehensive curatorial rules.

**v0.2+ uses tier-first organization**: Films are organized by tier (Core/Reference/Satellite/Popcorn) first, then by decade. This allows each tier to be a separate Plex library.

## Features

- **Automated Classification**: Sorts films into Core (auteur spine), Reference (canonical touchstones), Satellite (exploitation margins), and Popcorn (rewatchable entertainment) tiers
- **Expanded Core Coverage**: 105 directors across 8 decades (Welles, Godard, Chabrol, Bressane, Gallo, and more)
- **Tier-First Organization**: Primary organization by curatorial tier, secondary by decade
- **Intelligent Parsing**: Extracts title, year, director, and format signals from complex filename patterns including `(Director YYYY)` and bare years
- **Metadata Enrichment**: Optional TMDb API integration to fetch missing director and country information
- **Satellite Category Routing**: Decade-bounded classification for Giallo, Brazilian Exploitation, Pinku Eiga, etc.
- **Safety Features**: Dry-run mode, duplicate handling, comprehensive logging
- **Detailed Reporting**: Generates sorting manifest and staging reports

## Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure paths** in `config_external.yaml`
4. **Optional**: Get [TMDb API key](https://www.themoviedb.org/settings/api) for metadata enrichment

## Quick Start

```bash
# Classify films (never moves files, generates manifest)
python classify.py /path/to/unsorted/films

# Preview moves (dry-run, safe)
python move.py --dry-run

# Execute moves (requires explicit flag)
python move.py --execute

# Create folder structure on external drive
python scaffold.py --config config_external.yaml
```

## Configuration

Copy `config_external.yaml` and update these key settings:

```yaml
project_path: "/Users/mahesh/Downloads/film-sorting-database"  # This repo
library_path: "/Volumes/One Touch/Movies/Organized"            # External drive
source_path: "/Volumes/One Touch/Movies/unsorted"              # Unsorted films
tmdb_api_key: "your_api_key_here"                              # Optional
```

## Folder Structure Created (Tier-First)

```
/Library/
├── Core/                    # Auteur filmographies
│   ├── 1950s/
│   │   ├── Satyajit Ray/
│   │   └── Robert Bresson/
│   ├── 1960s/
│   │   ├── Jean-Luc Godard/
│   │   ├── Stanley Kubrick/
│   │   └── [38+ more directors]/
│   ├── 1970s/
│   └── [1980s-2020s]/
├── Reference/               # Canonical films (non-Core directors)
│   ├── 1950s/
│   ├── 1960s/
│   └── [1970s-2020s]/
├── Satellite/              # Margins & exploitation by category
│   ├── Giallo/
│   │   ├── 1960s/
│   │   ├── 1970s/
│   │   └── 1980s/
│   ├── Brazilian Exploitation/
│   │   ├── 1970s/
│   │   └── 1980s/
│   ├── Pinku Eiga/
│   │   ├── 1960s/
│   │   ├── 1970s/
│   │   └── 1980s/
│   └── [9+ more categories]/
├── Popcorn/                # Pleasure viewing
│   ├── 1960s/
│   ├── 1970s/
│   ├── 1980s/
│   │   ├── Back to the Future/
│   │   └── Batman/
│   └── [1990s-2020s]/
├── Unsorted/               # Needs classification
├── Staging/
│   ├── Borderline/
│   ├── Unknown/
│   ├── Unwatched/
│   └── Evaluate/
└── Out/
    └── Cut/
```

**Why tier-first?** Each tier can be added as a separate Plex library, making it easy to browse by curatorial intent (auteur study, canonical films, exploitation, pleasure).

## Sorting Logic (Priority Order)

The classifier implements this decision tree (first match wins):

1. **Explicit lookup** (`SORTING_DATABASE.md`) - Human-curated mappings (highest trust)
2. **Core director check** - Any film by Godard, Kubrick, Scorsese, etc. → `Core/[Decade]/[Director]/`
3. **Reference canon** - 50-film hardcoded list → `Reference/[Decade]/`
4. **User tag recovery** - Trust previous human classification from filename tags
5. **Satellite routing** - Country/language + decade rules → `Satellite/[Category]/[Decade]/`
6. **TMDb satellite** - Genre + country + decade from TMDb API → `Satellite/[Category]/[Decade]/`
7. **Default** → `Unsorted/` with reason code

**Important:** Core directors stay in Core even for canonical films. Kubrick's "2001" goes to `Core/1960s/Stanley Kubrick/`, not Reference. Reference is for canonical films by NON-Core directors.

### Core Directors (Auto-Classification)

Films by these directors automatically go to Core tier:
- **1960s**: Jean-Luc Godard, Stanley Kubrick, Federico Fellini, Pier Paolo Pasolini, Jacques Demy, Seijun Suzuki
- **1970s**: John Cassavetes, Martin Scorsese, Francis Ford Coppola, Rainer Werner Fassbinder, Terrence Malick
- **1980s**: David Lynch, Coen Brothers, Edward Yang, Jim Jarmusch, Brian De Palma
- **1990s**: Wong Kar-wai, Hou Hsiao-hsien, Edward Yang, Tsai Ming-liang
- **2000s**: Nicolas Winding Refn, Claire Denis, Paul Thomas Anderson
- **[Full list: 105 directors across 8 decades]**

### Satellite Categories (Decade-Bounded)

- **Giallo**: Italian horror-thrillers (1960s-1980s)
- **Brazilian Exploitation**: Portuguese titles (1970s-1980s)
- **Pinku Eiga**: Japanese pink films (1960s-1980s)
- **Hong Kong Action**: Martial arts, Category III (1970s-1990s)
- **Blaxploitation**: Black action cinema (1970s-1980s)
- **American Exploitation**: Grindhouse, cult (1960s-1980s)
- **European Sexploitation**: Euro softcore (1960s-1980s)
- **Music Films**: Concert films, rockumentaries (all decades, 20-film cap)
- **Cult Oddities**: Experimental, outsider (all decades, 20-film cap)

## Example Classifications (Tier-First)

```bash
# Core auteur film
Breathless (1960).mkv → Core/1960s/Jean-Luc Godard/

# Reference canon (non-Core director)
Psycho (1960).mkv → Reference/1960s/

# Core director's canonical film (stays in Core)
2001: A Space Odyssey (1968).mkv → Core/1960s/Stanley Kubrick/

# Brazilian exploitation (Portuguese + 1970s)
Escola Penal de Meninas Violentadas (1977).avi → Satellite/Brazilian Exploitation/1970s/

# Giallo (Italian + 1970s + horror/thriller)
Deep Red (1975).mkv → Satellite/Giallo/1970s/

# Popcorn franchise
Spider-Man (2002) 35mm Full Frame.mkv → Popcorn/2000s/Spider-Man/

# Unsorted (no year = cannot route to decade)
Random Film.mp4 → Unsorted/
```

## Filename Patterns Supported

```
Film Title (1985)
Film Title 1985
Director - Film Title (1985)
Director - Film Title 1985
Film Title (1985) [1980s-Core-Director]
Film Title (1985) [1980s-Satellite-Giallo]
```

## Reports Generated

### Sorting Manifest (`output/sorting_manifest.csv`)
Complete log of all classifications:
```csv
filename,title,year,director,tier,decade,subdirectory,destination,confidence,reason
Breathless (1960).mkv,Breathless,1960,Jean-Luc Godard,Core,1960s,Jean-Luc Godard,Core/1960s/Jean-Luc Godard/,1.0,core_director
```

### Staging Report (`output/staging_report.txt`)
Films requiring manual review:
```
FILMS REQUIRING MANUAL REVIEW
============================================================

File: Unknown Film.mkv
Title: Unknown Film
Year: UNKNOWN
Director: UNKNOWN
Reason: unsorted_no_year
```

### Classification Statistics
```
CLASSIFICATION STATISTICS (v1.0)
============================================================
Total films processed: 1090

BY TIER:
  Core           :   63 (  5.8%)
  Reference      :   19 (  1.7%)
  Satellite      :   76 (  7.0%)
  Popcorn        :   85 (  7.8%)
  Unsorted       :  847 ( 77.7%)

BY REASON:
  unsorted_no_match             :  405
  unsorted_no_year              :  270
  core_director                 :   49
  tmdb_satellite                :   39

Classification rate: 22.3% (243/1090)
```

## Command Line Options

### classify.py
```bash
python classify.py SOURCE_DIRECTORY [OPTIONS]

Arguments:
  SOURCE_DIRECTORY     Directory containing films to classify

Options:
  --output, -o        Output CSV path (default: output/sorting_manifest.csv)
  --config           Configuration file (default: config_external.yaml)
  --no-tmdb          Disable TMDb API enrichment (offline mode)
```

### move.py
```bash
python move.py [OPTIONS]

Options:
  --manifest, -m      Manifest CSV path (default: output/sorting_manifest.csv)
  --source, -s        Source directory (overrides config)
  --library, -l       Library base directory (overrides config)
  --config           Configuration file (default: config_external.yaml)
  --execute          Actually move files (default is dry-run)
  --dry-run          Preview moves without executing (default)
```

### scaffold.py
```bash
python scaffold.py [OPTIONS]

Options:
  --config           Configuration file (default: config_external.yaml)
```

## Safety Features

- **Dry-run mode**: Preview all moves before executing (`move.py` defaults to dry-run)
- **Tier-first migration**: Use `migrate_structure.py` to convert legacy decade-first to tier-first
- **Error recovery**: Graceful handling of parsing failures
- **Comprehensive logging**: Track all operations and errors
- **TMDb caching**: API responses cached locally to avoid repeat queries

## Migration from Decade-First to Tier-First

If you have an existing decade-first library structure:

```bash
# Preview migration
python migrate_structure.py "/Volumes/One Touch/Movies/Organized"

# Execute migration
python migrate_structure.py "/Volumes/One Touch/Movies/Organized" --execute
```

This will convert:
- `1960s/Core/Godard/` → `Core/1960s/Godard/`
- `1970s/Satellite/Giallo/` → `Satellite/Giallo/1970s/`
- etc.

## Plex Integration

Add each tier as a separate Plex movie library:

1. **Core Library**: `/Volumes/One Touch/Movies/Organized/Core/`
2. **Reference Library**: `/Volumes/One Touch/Movies/Organized/Reference/`
3. **Popcorn Library**: `/Volumes/One Touch/Movies/Organized/Popcorn/`
4. **Satellite Library**: `/Volumes/One Touch/Movies/Organized/Satellite/`

Plex will scan each tier independently, allowing you to browse by curatorial intent.

## Troubleshooting

### Common Issues

**Q: Script can't find project documents**
A: Update `project_path` in config_external.yaml to point to this repository

**Q: Many films go to Unsorted**
A: Most common reasons:
- No year in filename (hard gate - cannot route to decade)
- No director detected and not in explicit lookup database
- Enable TMDb API for better director detection

**Q: Core folders empty in Plex**
A: Make sure you're using tier-first structure. Run `migrate_structure.py` if needed.

**Q: Satellite films not classifying**
A: Satellite routing requires:
- Year in filename (to determine decade)
- Country/language match OR TMDb genre match
- Film within valid decade range for category

## Success Criteria

- ✅ 90%+ year extraction from filenames
- ✅ 100% accuracy on Core director films
- ✅ Decade-bounded Satellite routing (no 2010s Giallo)
- ✅ Tier-first structure for Plex integration
- ✅ Zero data loss with complete audit trail
- ✅ Dry-run mode for safety

## Dependencies

- Python 3.9+
- pyyaml (configuration)
- requests (TMDb API, optional)

## Project Structure

```
classify.py             # Main classifier (never moves files)
move.py                 # File mover (reads manifest)
scaffold.py             # Folder structure creator
migrate_structure.py    # Decade-first → tier-first migration
config_external.yaml    # Configuration template
requirements.txt        # Python dependencies
lib/                    # Core libraries
├── parser.py          # Filename parsing
├── tmdb.py            # TMDb API client
├── lookup.py          # SORTING_DATABASE.md lookup
├── core_directors.py  # Core director database
├── satellite.py       # Satellite classification
└── constants.py       # All constants (single source of truth)
docs/                   # Documentation
├── SORTING_DATABASE.md # Human-curated film mappings
└── theory/            # Curatorial philosophy
output/                # Generated reports
├── sorting_manifest.csv
├── staging_report.txt
└── tmdb_cache.json
```

## License

Part of the decade-wave cinema archive project. See `docs/theory/` for complete sorting methodology and curatorial philosophy.

---

**Important**: Always run `move.py` with default dry-run first to verify classifications before executing actual file moves. Use `classify.py` to generate the manifest, then review it before moving files.
