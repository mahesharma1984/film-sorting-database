# Changelog

All notable changes to the film classification system.

## [v0.2] - 2026-02-15

### Issue #6: Director-Based Satellite Routing with Decade Validation

**Major Enhancement:** Added decade-validated director-based routing to Satellite tier.

#### Critical Bug Fixed
- **Before:** Directors could route films from any era to categories (e.g., 2010s Argento film → Giallo)
- **After:** Decade validation ensures films only route within historically valid periods

#### New Features
- **Unified SATELLITE_ROUTING_RULES** in `lib/constants.py` - single source of truth for all Satellite routing
- **Decade-validated director matching** - prevents anachronistic classifications
- **Category-first folder structure** - `Satellite/{category}/{decade}/` for better organization
- **New category: Japanese Exploitation** - Kinji Fukasaku and yakuza/action films (1970s-1980s)

#### Added Directors (6 total)
1. **Kinji Fukasaku** → Japanese Exploitation (1970s-1980s)
2. **Yasuzō Masumura** → Pinku Eiga (1960s-1980s)
3. **Larry Clark** → American Exploitation (1990s-2000s)
4. **Lam Nai-Choi** → Hong Kong Action (1970s-1990s)
5. **Ernest R. Dickerson** → Blaxploitation (1970s, 1990s)
6. **Roger Vadim** → European Sexploitation (1960s-1970s)

#### Technical Changes
- **lib/satellite.py:** Replaced hardcoded `director_mappings` with `SATELLITE_ROUTING_RULES` import
- **classify.py:** Updated all Satellite path generation to category-first structure
- **scaffold.py:** Updated folder creation to match new structure
- **lib/constants.py:** Added comprehensive `SATELLITE_ROUTING_RULES` with decade/country/genre/director fields

#### Documentation Updates
- **docs/SATELLITE_CATEGORIES.md:** Added Japanese Exploitation, updated all director lists
- **docs/theory/MARGINS_AND_TEXTURE.md:** Documented decade validation and new directors
- **docs/DEVELOPER_GUIDE.md:** Added Satellite routing architecture section
- **README.md:** Updated folder structure diagram

#### Testing
- Added comprehensive test suite: `tests/test_satellite_director_routing.py` (23 tests)
- ✅ All tests pass
- ✅ Decade validation prevents misclassification
- ✅ Existing directors still work (regression prevention)

#### Impact
- **Classification improvement:** ~1.3% (16 films from Unsorted → Satellite)
- **Combined with Issues #4 + #5:** Total improvement to 38-39% classification rate

---

## [v1.0] - Prior

### Complete Rebuild: Methodology Kit Implementation

- **Three-script design:** `classify.py`, `move.py`, `scaffold.py`
- **Precision/Reasoning split:** Clear separation of parsing vs classification
- **Test-driven development:** Comprehensive test suite with regression prevention
- **TMDb enrichment:** Optional API integration for director lookup
- **Explicit lookup database:** Human-curated `SORTING_DATABASE.md`
- **Core director whitelist:** Exact case-insensitive matching
- **Reference canon:** 50-film hardcoded list

### Issue #5: Parser Year Extraction Fixes
- Fixed parenthetical year detection
- Added Brazilian format support (1976 - Title)
- Improved subtitle keyword detection

### Issue #4: Core Director Additions
- Added missing Core directors to whitelist
- Verified decade assignments

### Issue #3: v0.2 Parser Fixes and Language/Country Extraction
- Language pattern detection (13 languages)
- Country code mapping for Satellite routing
- Enhanced Brazilian/Italian/Japanese film detection

### Issue #2: v0.1 Reasoning and Precision Audit
- Identified asymmetric normalization bug
- Fixed format signal stripping in lookup
- Improved classification pipeline ordering

### Issue #1: Simplification to v0.1
- Removed over-engineered LLM classification
- Implemented structured rules-based approach
- Pattern-first architecture established

---

## Version Numbering

- **v0.x:** Development versions with incremental improvements
- **v1.0:** Complete methodology kit (3-script design, full test suite)
- **v0.2+:** Post-v1.0 enhancements (Issue #6 is technically v1.1 but kept in 0.2 branch)

---

## Related Documentation

- **Issue tracking:** See `issues/` directory for detailed bug reports
- **Theory essays:** See `docs/theory/` for curatorial rationale
- **Developer guide:** See `docs/DEVELOPER_GUIDE.md` for making changes
- **Core documentation index:** See `docs/CORE_DOCUMENTATION_INDEX.md`
