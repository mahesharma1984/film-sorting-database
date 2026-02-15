#!/usr/bin/env python3
"""
scaffold.py - Create film library folder structure

Pure PRECISION operation. Reads documentation, creates folders.
Never moves files, never classifies anything.

Folder structure (Issue #6 update):
- Core/{decade}/{director}/              (tier-first)
- Reference/{decade}/                     (tier-first)
- Popcorn/{decade}/                       (tier-first)
- Satellite/{category}/{decade}/          (category-first, Issue #6)
- Staging/{Borderline|Unknown|Unwatched|Evaluate}/
- Out/Cut/
"""

import sys
import logging
import argparse
from pathlib import Path

import yaml

from lib.core_directors import CoreDirectorDatabase
from lib.constants import SATELLITE_ROUTING_RULES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_folder_structure(config_path: Path):
    """Create complete film library folder structure"""

    config = load_config(config_path)
    library_path = Path(config['library_path'])
    project_path = Path(config['project_path'])

    logger.info(f"Creating folder structure at {library_path}")

    # Decades to create
    decades = ['1940s', '1950s', '1960s', '1970s', '1980s',
               '1990s', '2000s', '2010s', '2020s']

    # Satellite categories (imported from SATELLITE_ROUTING_RULES - Issue #6)
    # Use the routing rules to ensure consistency between classification and scaffold
    satellite_categories_with_decades = SATELLITE_ROUTING_RULES

    # 1. Create tier-first structure for Core, Reference, Popcorn
    logger.info("Creating Core, Reference, Popcorn directories...")

    for tier in ['Core', 'Reference', 'Popcorn']:
        for decade in decades:
            tier_decade_path = library_path / tier / decade
            tier_decade_path.mkdir(parents=True, exist_ok=True)

    # 2. Create Core director subdirectories
    logger.info("Creating Core director subdirectories...")

    core_db = CoreDirectorDatabase(project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md')

    for decade in decades:
        directors = core_db.directors_by_decade.get(decade, set())
        for director in directors:
            director_path = library_path / 'Core' / decade / director
            director_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Created {len(core_db.director_lookup)} Core director folders")

    # 3. Create category-first Satellite structure (Issue #6)
    logger.info("Creating Satellite category directories...")

    satellite_count = 0
    for category, rules in satellite_categories_with_decades.items():
        # Get decades for this category (None means all decades)
        category_decades = rules['decades'] if rules['decades'] else decades

        for decade in category_decades:
            satellite_path = library_path / 'Satellite' / category / decade
            satellite_path.mkdir(parents=True, exist_ok=True)
            satellite_count += 1

    logger.info(f"Created {satellite_count} Satellite category/decade folders")

    # 4. Create Staging subdirectories
    logger.info("Creating Staging directories...")

    staging_subdirs = ['Borderline', 'Unknown', 'Unwatched', 'Evaluate']
    for subdir in staging_subdirs:
        staging_path = library_path / 'Staging' / subdir
        staging_path.mkdir(parents=True, exist_ok=True)

    # 5. Create Out folder
    out_path = library_path / 'Out' / 'Cut'
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info("Folder structure creation complete!")
    logger.info(f"Root: {library_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("FOLDER STRUCTURE CREATED")
    print("=" * 60)
    print(f"\nLocation: {library_path}")
    print(f"\nStructure:")
    print(f"  Core/{len(decades)} decades × {len(core_db.director_lookup)} directors")
    print(f"  Reference/{len(decades)} decades")
    print(f"  Popcorn/{len(decades)} decades")
    print(f"  Satellite/{len(satellite_categories_with_decades)} categories × decades (category-first)")
    print(f"  Staging/{len(staging_subdirs)} subdirectories")
    print(f"  Out/Cut/")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Create film library folder structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python scaffold.py --config config_external.yaml

This will create the complete folder structure for the film library
based on the configuration and documentation files.
        """
    )
    parser.add_argument('--config', default='config_external.yaml',
                        help='Configuration file (default: config_external.yaml)')

    args = parser.parse_args()

    # Check config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    # Create folder structure
    try:
        create_folder_structure(config_path)
        logger.info("Success!")
    except Exception as e:
        logger.error(f"Failed to create folder structure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
