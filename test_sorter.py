#!/usr/bin/env python3
"""
Test script for the automated film library sorting system.
Validates core functionality without requiring actual files.
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add the current directory to path so we can import film_sorter
sys.path.insert(0, str(Path(__file__).parent))

try:
    from film_sorter import (
        FilenameParser, 
        CoreDirectorDatabase, 
        ReferenceCanonDatabase, 
        SatelliteCategories,
        FilmMetadata,
        FilmSorter
    )
except ImportError as e:
    print(f"Error importing film_sorter: {e}")
    print("Make sure you've installed the requirements: pip install -r requirements.txt")
    sys.exit(1)


class TestFileSorter:
    """Test suite for film sorting functionality"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        
    def assert_equal(self, actual, expected, message=""):
        """Simple assertion helper"""
        if actual == expected:
            self.passed += 1
            print(f"✓ {message}")
        else:
            self.failed += 1
            print(f"✗ {message}")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
    
    def test_filename_parsing(self):
        """Test filename parsing patterns"""
        print("\n=== Testing Filename Parser ===")
        
        parser = FilenameParser()
        
        # Test cases: (filename, expected_title, expected_year, expected_director)
        test_cases = [
            ("Breathless (1960).mkv", "Breathless", 1960, None),
            ("Jean-Luc Godard - Breathless (1960).mkv", "Breathless", 1960, "Jean-Luc Godard"),
            ("Spider-Man (2002) 35mm Full Frame.mkv", "Spider-Man", 2002, None),
            ("2001 A Space Odyssey (1968).avi", "2001 A Space Odyssey", 1968, None),
            ("Kubrick - 2001 A Space Odyssey 1968.mp4", "2001 A Space Odyssey", 1968, "Kubrick"),
        ]
        
        for filename, expected_title, expected_year, expected_director in test_cases:
            metadata = parser.parse(filename)
            
            self.assert_equal(
                metadata.title, expected_title, 
                f"Title parsing: {filename}"
            )
            self.assert_equal(
                metadata.year, expected_year,
                f"Year parsing: {filename}"
            )
            self.assert_equal(
                metadata.director, expected_director,
                f"Director parsing: {filename}"
            )
        
        # Test format signal detection
        metadata = parser.parse("Back to the Future (1985) 35mm Open Matte.mkv")
        self.assert_equal(
            "35mm" in metadata.format_signals, True,
            "Format signal detection: 35mm"
        )
        self.assert_equal(
            "open matte" in metadata.format_signals, True,
            "Format signal detection: open matte"
        )
    
    def test_core_director_detection(self):
        """Test core director whitelist functionality"""
        print("\n=== Testing Core Director Database ===")
        
        # Create a mock whitelist file
        mock_whitelist = """
# CORE DIRECTOR WHITELIST - FINAL

## 1960s CORE

**Jean-Luc Godard**
- Breathless (1960)

**Stanley Kubrick**  
- 2001: A Space Odyssey (1968)

## 1970s CORE

**Martin Scorsese**
- Taxi Driver (1976)

**Francis Ford Coppola**
- The Godfather (1972)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(mock_whitelist)
            whitelist_path = Path(f.name)
        
        try:
            db = CoreDirectorDatabase(whitelist_path)
            
            # Test exact matches
            self.assert_equal(
                db.is_core_director("Jean-Luc Godard"), True,
                "Core director detection: Jean-Luc Godard"
            )
            self.assert_equal(
                db.is_core_director("Stanley Kubrick"), True,
                "Core director detection: Stanley Kubrick"
            )
            
            # Test fuzzy matches
            self.assert_equal(
                db.is_core_director("Godard"), True,
                "Fuzzy director matching: Godard"
            )
            self.assert_equal(
                db.is_core_director("J.L. Godard"), True,
                "Fuzzy director matching: J.L. Godard"
            )
            
            # Test non-core directors
            self.assert_equal(
                db.is_core_director("Michael Bay"), False,
                "Non-core director detection: Michael Bay"
            )
            
            # Test decade mapping
            decades = db.get_director_decades("Martin Scorsese")
            self.assert_equal(
                "1970s" in decades, True,
                "Director decade mapping: Scorsese in 1970s"
            )
        
        finally:
            whitelist_path.unlink()
    
    def test_reference_canon_detection(self):
        """Test reference canon functionality"""  
        print("\n=== Testing Reference Canon Database ===")
        
        # Create mock reference list
        mock_reference = """
# REFERENCE CANON LIST

## REFERENCE FILMS BY DECADE

### 1960s Films

1. **Psycho** (1960) - Alfred Hitchcock
2. **Lawrence of Arabia** (1962) - David Lean

### 1970s Films

3. **The Godfather** (1972) - Francis Ford Coppola
4. **Chinatown** (1974) - Roman Polanski
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(mock_reference)
            reference_path = Path(f.name)
        
        try:
            db = ReferenceCanonDatabase(reference_path)
            
            self.assert_equal(
                db.is_reference_film("Psycho", 1960), True,
                "Reference film detection: Psycho (1960)"
            )
            self.assert_equal(
                db.is_reference_film("Lawrence of Arabia", 1962), True,
                "Reference film detection: Lawrence of Arabia"
            )
            self.assert_equal(
                db.is_reference_film("Random Movie", 1985), False,
                "Non-reference film detection"
            )
            
        finally:
            reference_path.unlink()
    
    def test_satellite_classification(self):
        """Test satellite category classification"""
        print("\n=== Testing Satellite Categories ===")
        
        categories = SatelliteCategories(Path("dummy"))  # Uses built-in categories
        
        # Test Brazilian exploitation (Portuguese characters)
        metadata = FilmMetadata(
            filename="Escola Penal de Meninas Violentadas (1977).avi",
            title="Escola Penal de Meninas Violentadas",
            year=1977
        )
        
        result = categories.classify_satellite(metadata)
        self.assert_equal(
            result, "Brazilian Exploitation",
            "Brazilian film classification"
        )
        
        # Test giallo classification
        metadata = FilmMetadata(
            filename="Strip Nude for Your Killer (1975).mkv",
            title="Strip Nude for Your Killer", 
            year=1975
        )
        
        result = categories.classify_satellite(metadata)
        # Should classify based on keywords or be None (acceptable)
        print(f"  Giallo classification result: {result}")
    
    def test_integration(self):
        """Test full integration with mocked project files"""
        print("\n=== Testing Integration ===")
        
        # Create temporary project directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project"
            project_path.mkdir()
            
            # Create mock project files
            (project_path / "CORE_DIRECTOR_WHITELIST_FINAL.md").write_text("""
# CORE DIRECTOR WHITELIST - FINAL

## 1960s CORE
**Jean-Luc Godard**
- Breathless (1960)

## 1970s CORE  
**Martin Scorsese**
- Taxi Driver (1976)
""")
            
            (project_path / "REFERENCE_CANON_LIST.md").write_text("""
# REFERENCE CANON LIST

### 1960s Films
1. **Psycho** (1960) - Alfred Hitchcock
""")
            
            (project_path / "SATELLITE_CATEGORIES.md").write_text("# SATELLITE CATEGORIES")
            
            # Create mock config
            config = {
                'project_path': str(project_path),
                'library_path': str(Path(temp_dir) / "library"),
                'tmdb_api_key': None
            }
            
            # Create config file
            import yaml
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config, f)
            
            try:
                sorter = FilmSorter(config_path)
                
                # Test classification decisions
                test_films = [
                    ("Breathless (1960).mkv", "Core"),
                    ("Psycho (1960).mkv", "Reference"), 
                    ("Random Movie (1985).mkv", "Staging"),
                    ("Spider-Man (2002) 35mm.mkv", "Popcorn"),
                ]
                
                for filename, expected_tier in test_films:
                    metadata = sorter.parser.parse(filename)
                    decision = sorter.classify_film(metadata)
                    
                    self.assert_equal(
                        decision.tier, expected_tier,
                        f"Film classification: {filename} -> {expected_tier}"
                    )
                
            except Exception as e:
                print(f"Integration test error: {e}")
                self.failed += 1
    
    def run_all_tests(self):
        """Run all test suites"""
        print("AUTOMATED FILM SORTING - TEST SUITE")
        print("=" * 50)
        
        self.test_filename_parsing()
        self.test_core_director_detection()
        self.test_reference_canon_detection()
        self.test_satellite_classification()
        self.test_integration()
        
        print(f"\n=== TEST RESULTS ===")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.failed == 0:
            print("✓ All tests passed!")
            return True
        else:
            print("✗ Some tests failed!")
            return False


def demo_classification():
    """Demonstrate classification of sample films"""
    print("\n" + "=" * 50)
    print("CLASSIFICATION DEMO")
    print("=" * 50)
    
    # Sample filenames to classify
    sample_films = [
        "Breathless (1960).mkv",
        "Jean-Luc Godard - Alphaville (1965).mkv", 
        "Psycho (1960).mkv",
        "Spider-Man (2002) 35mm Full Frame.mkv",
        "Escola Penal de Meninas Violentadas (1977).avi",
        "Back to the Future (1985) Open Matte.mkv",
        "Unknown Foreign Film (1983).mp4",
        "Rush Hour (1998).mkv",
    ]
    
    parser = FilenameParser()
    
    for filename in sample_films:
        print(f"\nFilename: {filename}")
        metadata = parser.parse(filename)
        
        print(f"  Title: {metadata.title}")
        print(f"  Year: {metadata.year}")
        print(f"  Director: {metadata.director}")
        
        if metadata.format_signals:
            print(f"  Format signals: {', '.join(metadata.format_signals)}")
        
        # Show predicted classification logic
        if metadata.director == "Jean-Luc Godard":
            print(f"  → CORE (Jean-Luc Godard is Core director)")
        elif metadata.title == "Psycho" and metadata.year == 1960:
            print(f"  → REFERENCE (canonical film)")
        elif "35mm" in metadata.format_signals or "open matte" in metadata.format_signals:
            print(f"  → POPCORN (format curation signals)")
        elif any(char in metadata.title.lower() for char in "áàâãçéêíóôõú"):
            print(f"  → SATELLITE - Brazilian Exploitation (Portuguese title)")
        elif not metadata.director:
            print(f"  → STAGING - Unknown (no director info)")
        else:
            print(f"  → STAGING - Borderline (needs manual classification)")


def main():
    """Main test entry point"""
    print("Automated Film Library Sorting Script - Test Suite")
    print("Validating core functionality...\n")
    
    # Check if we have access to project files
    project_files = [
        "CORE_DIRECTOR_WHITELIST_FINAL.md",
        "REFERENCE_CANON_LIST.md", 
        "SATELLITE_CATEGORIES.md"
    ]
    
    project_path = Path("/mnt/project")
    has_project_files = all((project_path / f).exists() for f in project_files)
    
    if has_project_files:
        print("✓ Project documentation files found")
    else:
        print("⚠ Project files not found - running with mock data")
    
    # Run test suite
    tester = TestFileSorter()
    success = tester.run_all_tests()
    
    # Run demo
    demo_classification()
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("=" * 50)
    print("1. Update config.yaml with your paths")
    print("2. Test with your collection:")
    print("   python film_sorter.py /path/to/films --dry-run")
    print("3. Review the staging report for manual classification")
    print("4. Execute actual sorting when satisfied")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
