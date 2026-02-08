#!/bin/bash
# Film Sorting System - Three-Script Workflow
# ===========================================
#
# This script orchestrates the three-phase sorting process:
# 1. scaffold.py  - Create folder structure (PRECISION)
# 2. classify.py  - Classify films → manifest (NEVER moves files)
# 3. move.py      - Execute moves from manifest (NEVER classifies)
#
# The manifest is the contract between classification and moving.

set -e  # Exit on error

# Configuration
CONFIG="config_external.yaml"
SOURCE_DIR="/Volumes/One Touch/movies/unsorted"
OUTPUT_DIR="output"

echo "========================================"
echo "FILM SORTING SYSTEM - Refactored"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Check config file
if [ ! -f "$CONFIG" ]; then
    echo "Error: Config file not found: $CONFIG"
    exit 1
fi

# Check source directory
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found: $SOURCE_DIR"
    echo "Update SOURCE_DIR in this script or run commands manually"
    exit 1
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "Configuration:"
echo "  Config: $CONFIG"
echo "  Source: $SOURCE_DIR"
echo "  Output: $OUTPUT_DIR"
echo

# ========================================
# PHASE 1: Scaffold
# ========================================
echo "========================================"
echo "PHASE 1: CREATE FOLDER STRUCTURE"
echo "========================================"
echo
echo "This will create the complete folder structure"
echo "at the library path defined in $CONFIG"
echo

read -p "Continue with scaffold? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Scaffold skipped."
else
    python3 scaffold.py --config "$CONFIG"
    echo
fi

# ========================================
# PHASE 2: Classify
# ========================================
echo "========================================"
echo "PHASE 2: CLASSIFY FILMS"
echo "========================================"
echo
echo "This will classify all films and generate:"
echo "  - $OUTPUT_DIR/sorting_manifest.csv"
echo "  - $OUTPUT_DIR/staging_report.txt"
echo "  - $OUTPUT_DIR/tmdb_cache.json"
echo
echo "IMPORTANT: This does NOT move any files."
echo

read -p "Continue with classification? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Classification skipped."
    echo
    echo "To run manually:"
    echo "  python3 classify.py \"$SOURCE_DIR\" --config \"$CONFIG\""
    exit 0
fi

python3 classify.py "$SOURCE_DIR" --config "$CONFIG" --output "$OUTPUT_DIR"
echo

# ========================================
# PHASE 3: Review (manual)
# ========================================
echo "========================================"
echo "PHASE 3: REVIEW MANIFEST"
echo "========================================"
echo
echo "Review the generated manifest:"
echo "  $OUTPUT_DIR/sorting_manifest.csv"
echo
echo "Review films needing manual classification:"
echo "  $OUTPUT_DIR/staging_report.txt"
echo
echo "You can edit the manifest CSV by hand if needed."
echo "The manifest is properly quoted to handle commas in filenames."
echo

read -p "Open manifest in default editor? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "$OUTPUT_DIR/sorting_manifest.csv" ]; then
        open "$OUTPUT_DIR/sorting_manifest.csv" || cat "$OUTPUT_DIR/sorting_manifest.csv" | head -20
    fi
fi

echo

# ========================================
# PHASE 4: Dry Run
# ========================================
echo "========================================"
echo "PHASE 4: DRY RUN MOVES"
echo "========================================"
echo
echo "This will preview what files will be moved."
echo "No files will actually be moved yet."
echo

read -p "Continue with dry run? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Dry run skipped."
    echo
    echo "To run manually:"
    echo "  python3 move.py \"$OUTPUT_DIR/sorting_manifest.csv\" \"$SOURCE_DIR\" --dry-run"
    exit 0
fi

python3 move.py "$OUTPUT_DIR/sorting_manifest.csv" "$SOURCE_DIR" --dry-run
echo

# ========================================
# PHASE 5: Execute
# ========================================
echo "========================================"
echo "PHASE 5: EXECUTE MOVES"
echo "========================================"
echo
echo "This will ACTUALLY MOVE FILES based on the manifest."
echo
echo "Performance:"
echo "  - Same filesystem: 2-5 minutes (os.rename)"
echo "  - Cross filesystem: 60-80 hours (byte copy)"
echo
echo "Safety:"
echo "  - Verifies copies before deleting source"
echo "  - Skips files already at destination (resumable)"
echo "  - Cleans up failed copies"
echo

read -p "EXECUTE MOVES NOW? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "Moves NOT executed."
    echo
    echo "To execute later:"
    echo "  python3 move.py \"$OUTPUT_DIR/sorting_manifest.csv\" \"$SOURCE_DIR\" --execute"
    exit 0
fi

python3 move.py "$OUTPUT_DIR/sorting_manifest.csv" "$SOURCE_DIR" --execute
echo

# ========================================
# Complete
# ========================================
echo "========================================"
echo "COMPLETE!"
echo "========================================"
echo
echo "All phases completed successfully."
echo
