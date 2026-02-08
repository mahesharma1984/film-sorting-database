#!/bin/bash

# External Drive Setup Script
# Helps configure the film sorter for external drives

echo "🎬 Film Library External Drive Setup"
echo "===================================="
echo

# Detect platform
case "$OSTYPE" in
    darwin*) PLATFORM="macOS" ;;
    linux*) PLATFORM="Linux" ;;
    msys*|cygwin*) PLATFORM="Windows" ;;
    *) PLATFORM="Unknown" ;;
esac

echo "Platform detected: $PLATFORM"
echo

# Show mounted drives
echo "🔍 Detecting available drives..."
echo

case "$PLATFORM" in
    "macOS")
        echo "Mounted volumes:"
        ls -la /Volumes/ 2>/dev/null | grep -v "^total" | while read -r line; do
            echo "  $line"
        done
        echo
        echo "Example external drive paths:"
        echo "  /Volumes/External Drive/Movies"
        echo "  /Volumes/Cinema Collection/Films"
        echo "  /Volumes/My Passport/Library"
        ;;
    "Linux")
        echo "Mounted drives:"
        df -h | grep -E "^/dev/(sd|nvme)" | while read -r line; do
            echo "  $line"
        done
        echo
        echo "Common mount points:"
        ls -la /mnt/ 2>/dev/null | grep -v "^total"
        ls -la /media/ 2>/dev/null | grep -v "^total"
        echo
        echo "Example external drive paths:"
        echo "  /mnt/external/Movies"
        echo "  /media/username/External/Cinema"
        ;;
    "Windows")
        echo "Available drives:"
        wmic logicaldisk get size,freespace,caption 2>/dev/null || echo "  Use 'dir' to see drives"
        echo
        echo "Example external drive paths:"
        echo "  E:/Movies/Collection"
        echo "  F:/Cinema Library"
        ;;
esac

echo
echo "📝 Configuration Help"
echo "===================="
echo

# Ask for drive location
echo "Please enter your external drive path for movies:"
read -r DRIVE_PATH

if [[ -n "$DRIVE_PATH" && -d "$DRIVE_PATH" ]]; then
    echo "✓ Drive path exists: $DRIVE_PATH"
    
    # Check if it's writable
    TEST_FILE="$DRIVE_PATH/.write_test_$$"
    if touch "$TEST_FILE" 2>/dev/null; then
        rm -f "$TEST_FILE"
        echo "✓ Drive is writable"
        
        # Generate config
        echo
        echo "🛠️  Generating configuration..."
        echo
        
        # Find project documents path
        PROJECT_PATH=""
        if [[ -f "./CORE_DIRECTOR_WHITELIST_FINAL.md" ]]; then
            PROJECT_PATH="$(pwd)"
        elif [[ -f "../CORE_DIRECTOR_WHITELIST_FINAL.md" ]]; then
            PROJECT_PATH="$(dirname "$(pwd)")"
        else
            echo "Project documents not found. Please enter path to folder containing:"
            echo "  - CORE_DIRECTOR_WHITELIST_FINAL.md"
            echo "  - REFERENCE_CANON_LIST.md"
            echo "  - etc."
            read -r PROJECT_PATH
        fi
        
        # Create suggested folder structure
        ORGANIZED_PATH="$DRIVE_PATH/Organized"
        UNSORTED_PATH="$DRIVE_PATH/Unsorted"
        
        cat > config_external.yaml << EOF
# Film Library Sorting Configuration - External Drive Setup
# ========================================================

# Project documents (Core whitelist, Reference canon, etc.)
project_path: "$PROJECT_PATH"

# External drive paths
library_path: "$ORGANIZED_PATH"    # Where sorted films will go
source_path: "$UNSORTED_PATH"      # Where unsorted films are now

# External drive settings
external_drive:
  verify_available: true           # Check drive is mounted before starting
  
# API Configuration (optional - get key from https://themoviedb.org)
tmdb_api_key: ""

# Processing settings
fuzzy_matching:
  director_threshold: 85
  title_threshold: 85

# File extensions to process
video_extensions: ['.mkv', '.mp4', '.avi', '.mov', '.m4v', '.wmv']

# Format signals that indicate Popcorn tier curation
format_signals:
  - "35mm"
  - "open matte"
  - "extended"
  - "director's cut"
  - "editor's cut"
  - "criterion"

# Satellite category caps (films exceeding caps go to staging)
satellite_caps:
  giallo: 30
  pinku_eiga: 35
  brazilian_exploitation: 45
  hong_kong_action: 65
  american_exploitation: 80
  european_sexploitation: 25
  nunsploitation: 15
  blaxploitation: 20
  wip_rape_revenge: 15
  music_films: 20
  mondo: 10
  cult_oddities: 50
EOF
        
        echo "Configuration saved to: config_external.yaml"
        echo
        echo "📁 Suggested folder structure on your external drive:"
        echo
        echo "$DRIVE_PATH/"
        echo "├── Organized/          # Will be created by script"
        echo "│   ├── 1960s/"
        echo "│   ├── 1970s/"
        echo "│   └── [other decades]"
        echo "├── Unsorted/           # Put your current film collection here"
        echo "└── Staging/            # Temporary files needing manual review"
        echo
        
        # Offer to create directories
        echo "Create these directories now? [y/N]"
        read -r CREATE_DIRS
        
        if [[ "$CREATE_DIRS" =~ ^[Yy] ]]; then
            mkdir -p "$UNSORTED_PATH" "$ORGANIZED_PATH/Staging"
            echo "✓ Directories created"
        fi
        
        echo
        echo "🚀 Next steps:"
        echo "1. Move your film collection to: $UNSORTED_PATH"
        echo "2. Test configuration: python3 film_sorter.py '$UNSORTED_PATH' --dry-run --config config_external.yaml"
        echo "3. Review the output, then run actual sort"
        echo
        echo "💡 Tips for external drives:"
        echo "- Use USB 3.0+ for faster processing"
        echo "- Close other apps using the drive during sorting"
        echo "- Always start with --dry-run to preview changes"
        echo
        
    else
        echo "❌ Cannot write to drive: $DRIVE_PATH"
        echo "Check permissions or drive format"
    fi
else
    echo "❌ Drive path not found: $DRIVE_PATH"
    echo
    echo "Common issues:"
    echo "- Drive not mounted/connected"
    echo "- Incorrect path spelling"
    echo "- Permission issues"
    echo
    echo "See EXTERNAL_DRIVE_GUIDE.md for detailed troubleshooting"
fi
