# Automated Film Library Sorting Script

Implements the decade-wave cinema archive system by automatically parsing film metadata from filenames and moving files to the appropriate decade/tier folder structure based on comprehensive curatorial rules.

## Features

- **Automated Classification**: Sorts ~850 films into Core (auteur spine), Reference (canonical touchstones), Satellite (exploitation margins), and Popcorn (rewatchable entertainment) tiers
- **Decade Organization**: Files organized by historical "waves" (1960s modernist rupture, 1970s political cinema, etc.)
- **Intelligent Parsing**: Extracts title, year, director, and format signals from common filename patterns
- **Metadata Enrichment**: Optional TMDb API integration to fetch missing director information
- **Format Curation Detection**: Identifies special editions (35mm, Open Matte, Extended Cut) for Popcorn classification
- **Fuzzy Matching**: Handles variations in director names and film titles
- **Safety Features**: Dry-run mode, duplicate handling, comprehensive logging
- **Detailed Reporting**: Generates sorting manifest and staging reports

## Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure paths** in `config.yaml`
4. **Optional**: Get [TMDb API key](https://www.themoviedb.org/settings/api) for metadata enrichment

## Quick Start

```bash
# Test with dry-run (recommended first time)
python film_sorter.py /path/to/unsorted/films --dry-run

# Execute actual sorting
python film_sorter.py /path/to/unsorted/films

# Custom configuration
python film_sorter.py /path/to/unsorted/films --config my_config.yaml
```

## External Drive Setup (Recommended)

Most users store large film collections on external drives. Use the automated setup:

```bash
./setup_external_drive.sh
```

This interactive script will:
- ✅ **Detect your external drive** (USB, Thunderbolt, etc.)
- ✅ **Auto-configure paths** for your platform (Windows/Mac/Linux) 
- ✅ **Test write permissions** and available space
- ✅ **Create folder structure** (Organized, Unsorted, Staging)
- ✅ **Generate optimized config** with external drive settings

### External Drive Tips
- **Use USB 3.0+** for faster file operations
- **Close other apps** accessing the drive during sorting
- **Ensure stable connection** (avoid extension cords)
- **Check available space** - need ~2x collection size for reorganization

See `EXTERNAL_DRIVE_GUIDE.md` for detailed troubleshooting.

## Configuration

Copy `config.yaml` and update these key settings:

```yaml
project_path: "/path/to/project/documents"  # Folder with CORE_DIRECTOR_WHITELIST_FINAL.md
library_path: "/path/to/organized/library"  # Destination for sorted films
tmdb_api_key: "your_api_key_here"          # Optional: for metadata enrichment
```

## Folder Structure Created

```
/Library/
├── 1950s/
│   ├── Core/
│   │   ├── Satyajit Ray/
│   │   └── Robert Bresson/
│   ├── Reference/
│   ├── Satellite/
│   └── Popcorn/
├── 1960s/
│   ├── Core/
│   │   ├── Jean-Luc Godard/
│   │   ├── Stanley Kubrick/
│   │   └── [38+ more directors]/
│   ├── Reference/
│   ├── Satellite/
│   │   ├── Giallo/
│   │   ├── Pinku Eiga/
│   │   └── [10+ more categories]/
│   └── Popcorn/
├── [1970s-2010s with same structure]/
├── Staging/
│   ├── Borderline/     # Needs manual classification
│   ├── Unknown/        # Missing metadata
│   ├── Unwatched/      # Need to watch first
│   └── Evaluate/       # Potential cuts
└── Out/
    └── Cut/            # Files marked for deletion
```

## Sorting Logic

The script implements this decision tree:

1. **Extract metadata** from filename (`Film Title (Year)`, `Director - Title`, etc.)
2. **Determine decade** from year (1960s, 1970s, etc.)
3. **Check Core directors** - Any film by Godard, Kubrick, Scorsese, etc. → `Core/[Director]/`
4. **Check Reference canon** - Citizen Kane, Psycho, The Matrix, etc. → `Reference/`
5. **Check Satellite categories** - Brazilian exploitation, Giallo, etc. → `Satellite/[Category]/`
6. **Check Popcorn signals** - 35mm, Open Matte, Extended Cut → `Popcorn/`
7. **Everything else** → `Staging/` for manual review

### Core Directors (Auto-Classification)

Films by these directors automatically go to Core tier:
- **1960s**: Jean-Luc Godard, Stanley Kubrick, Federico Fellini, Pier Paolo Pasolini
- **1970s**: John Cassavetes, Martin Scorsese, Francis Ford Coppola, Rainer Werner Fassbinder
- **1980s**: David Lynch, Coen Brothers, Edward Yang, Jim Jarmusch
- **1990s**: Wong Kar-wai, Hal Hartley, Hou Hsiao-hsien
- **[Full list: 38-43 directors across all decades]**

### Satellite Categories (Pattern Matching)

- **Brazilian Exploitation**: Portuguese titles, 1970s-80s production
- **Giallo**: Italian horror-thrillers (Bava, Argento, Fulci)
- **Hong Kong Action**: Martial arts, Category III films
- **Pinku Eiga**: Japanese pink films
- **American Exploitation**: Grindhouse, Russ Meyer, VHS cult
- **[7+ more categories with individual caps]**

### Popcorn Signals (Format Detection)

Files with these markers auto-classify as Popcorn:
- `35mm`, `Open Matte`, `Extended Cut`, `Director's Cut`
- `4K`, `UHD`, `Remux`, `Commentary`, `Special Edition`

## Filename Patterns Supported

```
Film Title (1985)
Film Title 1985
Director - Film Title (1985)
Director - Film Title 1985
Film Title (1985) 35mm Open Matte
Spider-Man 2.1 Extended Open Matte
```

## Example Classifications

```bash
# Core auteur film
Breathless (1960).mkv → 1960s/Core/Jean-Luc Godard/

# Reference canon
Psycho (1960).mkv → 1960s/Reference/

# Brazilian exploitation (Portuguese title)
Escola Penal de Meninas Violentadas (1977).avi → 1970s/Satellite/Brazilian Exploitation/

# Format-curated Popcorn
Spider-Man (2002) 35mm Full Frame.mkv → 2000s/Popcorn/Spider-Man/

# Staging (unknown director)
Random Film (1985).mp4 → Staging/Unknown/
```

## Reports Generated

### Sorting Manifest (`sorting_manifest.csv`)
Complete log of all file movements:
```csv
filename,title,year,director,tier,decade,subdirectory,confidence,reason,destination,success
Breathless (1960).mkv,Breathless,1960,Jean-Luc Godard,Core,1960s,Jean-Luc Godard,1.0,Director on Core whitelist,/Library/1960s/Core/Jean-Luc Godard,True
```

### Staging Report (`staging_report.txt`)
Films requiring manual review:
```
FILMS REQUIRING MANUAL REVIEW
========================================

File: Unknown Film (1985).mkv
Title: Unknown Film
Year: 1985
Director: None
Reason: No director information available
Destination: /Library/Staging/Unknown
```

### Statistics Output
```
SORTING STATISTICS:
==============================
Core           :   125 ( 25.0%)
Reference      :    35 (  7.0%)
Satellite      :   242 ( 48.4%)
Popcorn        :    91 ( 18.2%)
Staging        :     7 (  1.4%)
TOTAL          :   500

Staging rate: 1.4% (target: <10%)
```

## Command Line Options

```bash
python film_sorter.py SOURCE_DIRECTORY [OPTIONS]

Arguments:
  SOURCE_DIRECTORY     Directory containing unsorted films

Options:
  --config CONFIG      Configuration file (default: config.yaml)
  --dry-run           Preview moves without executing
  --output OUTPUT     Output directory for reports (default: output/)
  --help              Show this help message
```

## Safety Features

- **Dry-run mode**: Preview all moves before executing
- **Duplicate handling**: Automatic filename deduplication
- **Error recovery**: Graceful handling of parsing failures
- **Comprehensive logging**: Track all operations and errors
- **Backup recommendation**: Always backup your collection first

## Troubleshooting

### Common Issues

**Q: Script can't find project documents**
A: Update `project_path` in config.yaml to point to folder containing `CORE_DIRECTOR_WHITELIST_FINAL.md`

**Q: Many films go to Staging/Unknown**
A: Enable TMDb API by adding your API key to config.yaml for automatic director lookup

**Q: Foreign films not classified correctly**
A: Brazilian films auto-detect via Portuguese characters. Other foreign films may need manual classification.

**Q: Format signals not detected**
A: Ensure format indicators are in filename: `Film (Year) 35mm.mkv` not `Film (Year).mkv` in `35mm/` folder

### Performance Tips

- **Large collections (1000+ films)**: Use TMDb API to reduce staging rate
- **Network storage**: Run script locally then copy to avoid network timeouts
- **Progress tracking**: Uncomment `tqdm` in requirements.txt for progress bars

### Customization

**Add new Core director**:
1. Update `CORE_DIRECTOR_WHITELIST_FINAL.md` 
2. Restart script (directors are loaded on startup)

**Add new Satellite category**:
1. Modify `SatelliteCategories` class in `film_sorter.py`
2. Add pattern matching rules

**Adjust fuzzy matching**:
1. Change `fuzzy_thresholds` in config.yaml
2. Higher values = stricter matching

## Success Criteria

- ✅ 95%+ metadata extraction from filenames
- ✅ 100% accuracy on Core director films  
- ✅ 85%+ accuracy on Reference/Satellite classification
- ✅ <10% staging rate for manual review
- ✅ Zero data loss with complete audit trail
- ✅ Dry-run mode for safety

## Dependencies

- Python 3.9+
- pyyaml (configuration)
- requests (TMDb API)
- pandas (reporting)
- fuzzywuzzy (string matching)
- python-levenshtein (performance)

## Project Structure

```
film_sorter.py          # Main script
config.yaml             # Configuration template  
requirements.txt        # Python dependencies
README.md              # This documentation
output/                # Generated reports
├── sorting_manifest.csv
├── staging_report.txt
└── sorting.log
```

## License

Part of the decade-wave cinema archive project. See project documentation for complete sorting methodology and curatorial philosophy.

---

**Important**: Always run with `--dry-run` first to verify classifications before executing actual file moves. The script implements a sophisticated classification system but complex edge cases may require manual review.
