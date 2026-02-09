#!/usr/bin/env python3
"""
Quick validation script for v0.2 parser fixes
Tests the three critical parser bugs to ensure they're fixed
"""

from lib.parser import FilenameParser

def test_bug1_empty_title():
    """Bug 1: Title (Year) - Resolution → should parse title correctly"""
    parser = FilenameParser()

    test_cases = [
        ("Casablanca (1942) - 4K.mkv", "Casablanca", 1942, None),
        ("The Apartment (1960) - 1080p.mkv", "The Apartment", 1960, None),
        ("Chinatown (1974) - 4K.mkv", "Chinatown", 1974, None),
        ("Pulp Fiction (1994) - 1080p.mkv", "Pulp Fiction", 1994, None),
    ]

    print("=" * 60)
    print("Testing Bug 1: Title (Year) - Resolution")
    print("=" * 60)

    passed = 0
    failed = 0

    for filename, expected_title, expected_year, expected_director in test_cases:
        metadata = parser.parse(filename)

        title_match = metadata.title == expected_title
        year_match = metadata.year == expected_year
        director_match = metadata.director == expected_director

        if title_match and year_match and director_match:
            print(f"✓ PASS: {filename}")
            print(f"   title={metadata.title}, year={metadata.year}, director={metadata.director}")
            passed += 1
        else:
            print(f"✗ FAIL: {filename}")
            print(f"   Expected: title='{expected_title}', year={expected_year}, director={expected_director}")
            print(f"   Got:      title='{metadata.title}', year={metadata.year}, director={metadata.director}")
            failed += 1

    print(f"\nBug 1 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_bug2_subtitle_swap():
    """Bug 2: Series - Subtitle (Year) → should NOT extract director"""
    parser = FilenameParser()

    test_cases = [
        ("Cinema Paradiso - Theatrical Cut (1988).mkv", "Cinema Paradiso", 1988, None),
        ("Blade Runner - The Final Cut (2007).mkv", "Blade Runner", 2007, None),
        ("Leon the Professional - Extended (1994).mkv", "Leon the Professional", 1994, None),
    ]

    print("=" * 60)
    print("Testing Bug 2: Title - Subtitle (Year)")
    print("=" * 60)

    passed = 0
    failed = 0

    for filename, expected_title, expected_year, expected_director in test_cases:
        metadata = parser.parse(filename)

        title_match = expected_title.lower() in metadata.title.lower()  # Flexible match
        year_match = metadata.year == expected_year
        director_match = metadata.director == expected_director

        if title_match and year_match and director_match:
            print(f"✓ PASS: {filename}")
            print(f"   title={metadata.title}, year={metadata.year}, director={metadata.director}")
            passed += 1
        else:
            print(f"✗ FAIL: {filename}")
            print(f"   Expected: title contains '{expected_title}', year={expected_year}, director={expected_director}")
            print(f"   Got:      title='{metadata.title}', year={metadata.year}, director={metadata.director}")
            failed += 1

    print(f"\nBug 2 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_bug3_director_year():
    """Bug 3: (Director, Year) Pattern → should extract both director and year"""
    parser = FilenameParser()

    test_cases = [
        ("A Bay of Blood (Mario Bava, 1971).mkv", "A Bay of Blood", "Mario Bava", 1971),
        ("Danger Diabolik (Mario Bava, 1968).mkv", "Danger Diabolik", "Mario Bava", 1968),
    ]

    print("=" * 60)
    print("Testing Bug 3: Title (Director, Year)")
    print("=" * 60)

    passed = 0
    failed = 0

    for filename, expected_title, expected_director, expected_year in test_cases:
        metadata = parser.parse(filename)

        title_match = metadata.title == expected_title
        year_match = metadata.year == expected_year
        director_match = metadata.director == expected_director

        if title_match and year_match and director_match:
            print(f"✓ PASS: {filename}")
            print(f"   title={metadata.title}, director={metadata.director}, year={metadata.year}")
            passed += 1
        else:
            print(f"✗ FAIL: {filename}")
            print(f"   Expected: title='{expected_title}', director='{expected_director}', year={expected_year}")
            print(f"   Got:      title='{metadata.title}', director='{metadata.director}', year={metadata.year}")
            failed += 1

    print(f"\nBug 3 Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_language_extraction():
    """Test language/country extraction"""
    parser = FilenameParser()

    test_cases = [
        # Language extraction requires explicit markers in filename
        ("Film (1976) Portuguese.avi", "pt", "BR"),
        ("Peking Opera Blues 1986 CHINESE 1080p.mkv", "zh", "HK"),
        ("Mississippi Mermaid (1969) In French.mkv", "fr", "FR"),
    ]

    print("=" * 60)
    print("Testing Language/Country Extraction")
    print("=" * 60)

    passed = 0
    failed = 0

    for filename, expected_lang, expected_country in test_cases:
        metadata = parser.parse(filename)

        lang_match = metadata.language == expected_lang
        country_match = metadata.country == expected_country

        if lang_match and country_match:
            print(f"✓ PASS: {filename}")
            print(f"   language={metadata.language}, country={metadata.country}")
            passed += 1
        else:
            print(f"✗ FAIL: {filename}")
            print(f"   Expected: language='{expected_lang}', country='{expected_country}'")
            print(f"   Got:      language='{metadata.language}', country='{metadata.country}'")
            failed += 1

    print(f"\nLanguage Extraction Results: {passed} passed, {failed} failed\n")
    return failed == 0


def test_user_tag_extraction():
    """Test user tag extraction"""
    parser = FilenameParser()

    test_cases = [
        ("Detour.1945.Criterion...[Popcorn-1940s].mkv", "Popcorn-1940s"),
        ("Dog Day Afternoon (1975)...[1970s-Reference].mkv", "1970s-Reference"),
        ("Regular Film (2000).mkv", None),
    ]

    print("=" * 60)
    print("Testing User Tag Extraction")
    print("=" * 60)

    passed = 0
    failed = 0

    for filename, expected_tag in test_cases:
        metadata = parser.parse(filename)

        tag_match = metadata.user_tag == expected_tag

        if tag_match:
            print(f"✓ PASS: {filename}")
            print(f"   user_tag={metadata.user_tag}")
            passed += 1
        else:
            print(f"✗ FAIL: {filename}")
            print(f"   Expected: user_tag='{expected_tag}'")
            print(f"   Got:      user_tag='{metadata.user_tag}'")
            failed += 1

    print(f"\nUser Tag Extraction Results: {passed} passed, {failed} failed\n")
    return failed == 0


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("V0.2 PARSER FIXES VALIDATION")
    print("=" * 60 + "\n")

    results = []
    results.append(("Bug 1 (Empty Title)", test_bug1_empty_title()))
    results.append(("Bug 2 (Subtitle Swap)", test_bug2_subtitle_swap()))
    results.append(("Bug 3 (Director, Year)", test_bug3_director_year()))
    results.append(("Language Extraction", test_language_extraction()))
    results.append(("User Tag Extraction", test_user_tag_extraction()))

    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! v0.2 parser fixes are working correctly.\n")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Review the output above.\n")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
