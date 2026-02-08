#!/usr/bin/env python3
"""
Simple validation script for v0.1 classification fixes (no pytest required)

Tests the 3 critical Kubrick cases from the effectiveness report
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classify_v01 import FilmClassifierV01
from lib.parser import FilenameParser
from lib.normalization import normalize_for_lookup
from lib.lookup import SortingDatabaseLookup


def test_kubrick_films():
    """Test the 3 Kubrick films from the effectiveness report"""
    print("\n" + "=" * 70)
    print("TESTING KUBRICK FILM CLASSIFICATION FIXES")
    print("=" * 70)

    project_path = Path(__file__).parent.parent
    classifier = FilmClassifierV01(project_path)

    test_cases = [
        {
            'name': 'Dr. Strangelove with Criterion',
            'filename': 'Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv',
            'expected_tier': 'Core',
            'expected_destination': '1960s/Core/Stanley Kubrick/',
            'expected_year': 1964,
            'expected_reason': 'explicit_lookup'
        },
        {
            'name': 'The Shining with 35mm',
            'filename': 'The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv',
            'expected_tier': 'Core',
            'expected_destination': '1980s/Core/Stanley Kubrick/',
            'expected_year': 1980,
            'expected_reason': 'explicit_lookup'
        },
        {
            'name': '2001 - A Space Odyssey (year parsing)',
            'filename': '2001 - A Space Odyssey (1968) - 4K.mkv',
            'expected_tier': 'Core',
            'expected_destination': '1960s/Core/Stanley Kubrick/',
            'expected_year': 1968,  # NOT 2001!
            'expected_reason': 'explicit_lookup'
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"  Filename: {test['filename']}")

        try:
            metadata = classifier.parser.parse(test['filename'])
            result = classifier.classify(metadata)

            # Check year
            if metadata.year != test['expected_year']:
                print(f"  ✗ FAIL: Year = {metadata.year}, expected {test['expected_year']}")
                failed += 1
                continue

            # Check tier
            if result.tier != test['expected_tier']:
                print(f"  ✗ FAIL: Tier = {result.tier}, expected {test['expected_tier']}")
                print(f"    Reason: {result.reason}")
                print(f"    Destination: {result.destination}")
                failed += 1
                continue

            # Check destination (allow for trailing slash differences)
            dest_normalized = result.destination.rstrip('/')
            expected_normalized = test['expected_destination'].rstrip('/')
            if dest_normalized != expected_normalized:
                print(f"  ✗ FAIL: Destination = {result.destination}")
                print(f"    Expected: {test['expected_destination']}")
                failed += 1
                continue

            # Check reason
            if result.reason != test['expected_reason']:
                print(f"  ⚠ WARNING: Reason = {result.reason}, expected {test['expected_reason']}")
                print(f"    (Still routed correctly, but via different path)")

            print(f"  ✓ PASS: year={metadata.year}, tier={result.tier}, destination={result.destination}")
            passed += 1

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)

    return failed == 0


def test_normalization():
    """Test symmetric normalization"""
    print("\n" + "=" * 70)
    print("TESTING SYMMETRIC NORMALIZATION")
    print("=" * 70)

    test_cases = [
        ("Dr Strangelove Criterion", "dr strangelove"),
        ("The Shining 35mm Scan", "the shining scan"),
        ("2001 A Space Odyssey 4K", "2001 a space odyssey"),
    ]

    passed = 0
    failed = 0

    for raw, expected in test_cases:
        normalized = normalize_for_lookup(raw, strip_format_signals=True)
        if normalized == expected:
            print(f"  ✓ '{raw}' → '{normalized}'")
            passed += 1
        else:
            print(f"  ✗ '{raw}' → '{normalized}' (expected '{expected}')")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_lookup_symmetry():
    """Test that lookup works with format signal contamination"""
    print("\n" + "=" * 70)
    print("TESTING LOOKUP SYMMETRY")
    print("=" * 70)

    project_path = Path(__file__).parent.parent
    lookup_db = SortingDatabaseLookup(project_path / 'docs' / 'SORTING_DATABASE.md')

    test_cases = [
        ("Dr Strangelove Criterion", 1964),
        ("The Shining 35mm Scan FullScreen HYBRID OPEN MATTE", 1980),
        ("2001 A Space Odyssey 4K", 1968),
    ]

    passed = 0
    failed = 0

    for title, year in test_cases:
        result = lookup_db.lookup(title, year)
        if result and 'Stanley Kubrick' in result:
            print(f"  ✓ '{title}' ({year}) → {result}")
            passed += 1
        else:
            print(f"  ✗ '{title}' ({year}) → {result} (expected Kubrick match)")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_year_parsing():
    """Test year parsing priority"""
    print("\n" + "=" * 70)
    print("TESTING YEAR PARSING PRIORITY")
    print("=" * 70)

    parser = FilenameParser()

    test_cases = [
        ("2001 - A Space Odyssey (1968) - 4K.mkv", 1968, "2001"),
        ("1984 (1956).mkv", 1956, "1984"),
        ("1976 - Amadas e Violentadas.avi", 1976, "Amadas"),
    ]

    passed = 0
    failed = 0

    for filename, expected_year, title_contains in test_cases:
        metadata = parser.parse(filename)

        year_ok = metadata.year == expected_year
        title_ok = title_contains.lower() in metadata.title.lower()

        if year_ok and title_ok:
            print(f"  ✓ '{filename}' → year={metadata.year}, title='{metadata.title}'")
            passed += 1
        else:
            print(f"  ✗ '{filename}' → year={metadata.year} (expected {expected_year}), title='{metadata.title}'")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print("FILM CLASSIFICATION SYSTEM - FIX VALIDATION")
    print("=" * 70)

    all_passed = True

    all_passed &= test_kubrick_films()
    all_passed &= test_normalization()
    all_passed &= test_lookup_symmetry()
    all_passed &= test_year_parsing()

    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
