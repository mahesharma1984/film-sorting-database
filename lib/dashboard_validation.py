"""
Dashboard validation helpers.

Provides validation functions for dashboard editing UI.
Reuses constants and logic from classify.py pipeline.
"""

from typing import Dict, List, Optional
import pandas as pd

try:
    from lib.constants import SATELLITE_ROUTING_RULES, REFERENCE_CANON
except ImportError:
    # Fallback for when lib is not available
    SATELLITE_ROUTING_RULES = {}
    REFERENCE_CANON = {}

try:
    from lib.core_directors import CoreDirectorDatabase
except ImportError:
    CoreDirectorDatabase = None


class DashboardValidator:
    """Validates film classification edits from dashboard."""

    def __init__(self, core_db_path: Optional[str] = None):
        """Initialize with optional Core director whitelist."""
        self.core_db = None
        if core_db_path and CoreDirectorDatabase is not None:
            try:
                self.core_db = CoreDirectorDatabase(core_db_path)
            except Exception:
                pass

    def validate_film(self, film: Dict) -> Dict:
        """
        Validate a single film classification.

        Returns dict with:
        - valid: bool
        - errors: list of error messages
        - warnings: list of warning messages
        """
        errors = []
        warnings = []

        tier = film.get('tier')
        decade = film.get('decade')
        subdirectory = film.get('subdirectory')
        year = film.get('year')

        # Hard gate: Year required for classified tiers
        if tier not in ['Unsorted', 'Staging'] and pd.isna(year):
            errors.append("Year is required for this tier")

        # Tier-specific validation
        if tier == 'Core':
            errors.extend(self._validate_core(film))
        elif tier == 'Reference':
            warnings.extend(self._validate_reference(film))
        elif tier == 'Satellite':
            errors.extend(self._validate_satellite(film))
        elif tier == 'Popcorn':
            warnings.extend(self._validate_popcorn(film))

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_core(self, film: Dict) -> List[str]:
        """Validate Core tier requirements."""
        errors = []

        if not film.get('subdirectory'):
            errors.append("Core tier requires director subdirectory")

        if not film.get('decade'):
            errors.append("Core tier requires decade")

        # Check against whitelist if available
        if self.core_db and film.get('director'):
            if not self.core_db.is_core_director(film['director']):
                errors.append(f"Director '{film['director']}' not in Core whitelist")

        return errors

    def _validate_reference(self, film: Dict) -> List[str]:
        """Validate Reference tier (warnings only)."""
        warnings = []

        if film.get('subdirectory'):
            warnings.append("Reference tier doesn't use subdirectory")

        return warnings

    def _validate_satellite(self, film: Dict) -> List[str]:
        """Validate Satellite tier requirements."""
        errors = []

        if not film.get('subdirectory'):
            errors.append("Satellite tier requires category subdirectory")
            return errors

        category = film['subdirectory']
        decade = film.get('decade')

        # Check valid category
        if category not in SATELLITE_ROUTING_RULES:
            errors.append(f"Invalid satellite category: '{category}'")
            valid_cats = ', '.join(sorted(SATELLITE_ROUTING_RULES.keys()))
            errors.append(f"Valid categories: {valid_cats}")
            return errors

        # Check decade bounds
        valid_decades = SATELLITE_ROUTING_RULES[category].get('decades')
        if valid_decades and decade and decade not in valid_decades:
            errors.append(f"{category} only valid in decades: {', '.join(valid_decades)}")

        return errors

    def _validate_popcorn(self, film: Dict) -> List[str]:
        """Validate Popcorn tier (warnings only)."""
        warnings = []

        if film.get('subdirectory'):
            warnings.append("Popcorn tier doesn't use subdirectory")

        return warnings

    def check_satellite_cap(self, category: str, current_count: int) -> Dict:
        """
        Check if satellite category is at/over cap.

        Returns dict with:
        - at_cap: bool
        - current: int
        - cap: int
        - percentage: float
        """
        if category not in SATELLITE_ROUTING_RULES:
            return {'at_cap': False, 'current': 0, 'cap': 0, 'percentage': 0}

        # Get cap from routing rules
        category_config = SATELLITE_ROUTING_RULES[category]
        cap = category_config.get('cap', 999)
        percentage = (current_count / cap * 100) if cap > 0 else 0

        return {
            'at_cap': current_count >= cap,
            'current': current_count,
            'cap': cap,
            'percentage': percentage
        }


def build_destination(tier: str, decade: str, subdirectory: str) -> str:
    """
    Rebuild destination path from tier/decade/subdirectory.
    Mirrors classify.py _build_destination() logic.

    Args:
        tier: One of Core, Reference, Satellite, Popcorn, Unsorted, Staging
        decade: Decade string like '1960s'
        subdirectory: Director name (Core) or category name (Satellite)

    Returns:
        Destination path string with trailing slash
    """
    if tier == 'Unsorted':
        return 'Unsorted/'
    elif tier == 'Core' and decade and subdirectory:
        return f'Core/{decade}/{subdirectory}/'
    elif tier == 'Reference' and decade:
        return f'Reference/{decade}/'
    elif tier == 'Satellite' and decade and subdirectory:
        # Category-first structure (Issue #6)
        return f'Satellite/{subdirectory}/{decade}/'
    elif tier == 'Popcorn' and decade:
        return f'Popcorn/{decade}/'
    elif tier == 'Staging':
        return f'Staging/{subdirectory or "Unknown"}/'
    else:
        return 'Unsorted/'
