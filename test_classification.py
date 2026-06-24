#!/usr/bin/env python3
"""
Test Suite for Author Classification Logic
Tests the classification rules against known test cases and edge cases.
"""

import sys
sys.path.insert(0, '.')

from classify_authors import (
    classify_author,
    is_acronym,
    contains_corporate_keyword,
    contains_known_brand,
    has_organizational_pattern,
    has_plural_indicator
)

# =============================================================================
# TEST DATA
# =============================================================================

TEST_CASES = {
    # CORPORATE - Known brands
    "CORPORATE - Known Brands": [
        ("Spotify", "CORPORATE"),
        ("Apple Podcasts", "CORPORATE"),
        ("NPR", "CORPORATE"),
        ("BBC", "CORPORATE"),
        ("Netflix", "CORPORATE"),
        ("iHeartMedia", "CORPORATE"),
    ],
    
    # CORPORATE - Legal entity types
    "CORPORATE - Legal Entities": [
        ("Acme Inc", "CORPORATE"),
        ("Smith LLC", "CORPORATE"),
        ("Tech Corp", "CORPORATE"),
        ("Global Ltd", "CORPORATE"),
        ("ABC Company", "CORPORATE"),
    ],
    
    # CORPORATE - Educational institutions
    "CORPORATE - Education": [
        ("Harvard University", "CORPORATE"),
        ("MIT Institute", "CORPORATE"),
        ("Stanford School", "CORPORATE"),
        ("Oxford College", "CORPORATE"),
    ],
    
    # CORPORATE - Organizations
    "CORPORATE - Organizations": [
        ("American Foundation", "CORPORATE"),
        ("Red Cross Society", "CORPORATE"),
        ("World Health Organization", "CORPORATE"),
        ("Tech Association", "CORPORATE"),
    ],
    
    # CORPORATE - Acronyms
    "CORPORATE - Acronyms": [
        ("FBI", "CORPORATE"),
        ("CIA", "CORPORATE"),
        ("NASA", "CORPORATE"),
        ("WHO", "CORPORATE"),
    ],
    
    # CORPORATE - Partnerships
    "CORPORATE - Partnerships": [
        ("Smith & Associates", "CORPORATE"),
        ("Johnson & Johnson", "CORPORATE"),
        ("Tom & Jerry Productions", "CORPORATE"),
        ("Simon + Schuster", "CORPORATE"),
    ],
    
    # CORPORATE - "The" organizations
    "CORPORATE - 'The' Pattern": [
        ("The New York Times", "CORPORATE"),
        ("The Washington Post", "CORPORATE"),
        ("The Beatles", "CORPORATE"),
        ("The Verge", "CORPORATE"),
    ],
    
    # CORPORATE - Plural indicators
    "CORPORATE - Plural Indicators": [
        ("Mary and Friends", "CORPORATE"),
        ("The Hosts", "CORPORATE"),
        ("Alex Presents", "CORPORATE"),
        ("Team Innovation", "CORPORATE"),
    ],
    
    # INDIVIDUAL - Common names
    "INDIVIDUAL - Common Names": [
        ("David Wilson", "INDIVIDUAL"),
        ("Sarah Jones", "INDIVIDUAL"),
        ("Michael Brown", "INDIVIDUAL"),
        ("Jessica Lee", "INDIVIDUAL"),
    ],
    
    # INDIVIDUAL - Single names
    "INDIVIDUAL - Single Names": [
        ("Madonna", "INDIVIDUAL"),
        ("Oprah", "INDIVIDUAL"),
        ("Beyonce", "INDIVIDUAL"),
        ("Prince", "INDIVIDUAL"),
    ],
    
    # INDIVIDUAL - First & Last name
    "INDIVIDUAL - Two-Part Names": [
        ("Joe Rogan", "INDIVIDUAL"),
        ("Marc Maron", "INDIVIDUAL"),
        ("Lex Fridman", "INDIVIDUAL"),
    ],
    
    # UNKNOWN - Edge cases
    "UNKNOWN - Edge Cases": [
        ("", "UNKNOWN"),
        (None, "UNKNOWN"),
        ("  ", "UNKNOWN"),
    ],
    
    # EDGE CASES - Tricky ones
    "EDGE CASES - Ambiguous": [
        ("MAX Media", "CORPORATE"),  # MAX is a keyword + Media
        ("Ray Dalio", "INDIVIDUAL"),  # Ray is a name, Dalio is surname
        ("BP Energy", "CORPORATE"),  # Company name
        ("Ed Sheeran", "INDIVIDUAL"),  # Personal name (ED not an acronym context)
    ],
}

# =============================================================================
# TEST EXECUTION
# =============================================================================

def run_tests():
    """Run all tests and report results."""
    print("=" * 80)
    print("AUTHOR CLASSIFICATION TEST SUITE")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_group, cases in TEST_CASES.items():
        print(f"\n{test_group}")
        print("-" * 80)
        
        for author, expected in cases:
            total_tests += 1
            result = classify_author(author)
            
            # Handle None/empty display
            display_author = repr(author) if author is None or author == "" else f"'{author}'"
            
            if result == expected:
                status = "✓ PASS"
                passed_tests += 1
            else:
                status = f"✗ FAIL (got {result}, expected {expected})"
                failed_tests += 1
            
            print(f"  {status:50} {display_author}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed_tests}/{total_tests} passed")
    print("=" * 80)
    
    if failed_tests > 0:
        print(f"\n❌ {failed_tests} test(s) failed")
        return 1
    else:
        print("\n✓ All tests passed!")
        return 0


def test_individual_functions():
    """Test individual classification helper functions."""
    print("\n" + "=" * 80)
    print("HELPER FUNCTION TESTS")
    print("=" * 80)
    
    print("\nis_acronym() tests:")
    print("-" * 80)
    acronym_tests = [
        ("FBI", True),
        ("NPR", True),
        ("John", False),
        ("ABC", True),
        ("TECH", True),  # 4-letter acronym
        ("J", False),
    ]
    for text, expected in acronym_tests:
        result = is_acronym(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} is_acronym('{text}') = {result} (expected {expected})")
    
    print("\ncontains_corporate_keyword() tests:")
    print("-" * 80)
    keyword_tests = [
        ("Acme Inc", True),
        ("John Smith", False),
        ("University of Tech", True),
        ("Sarah Jones", False),
    ]
    for text, expected in keyword_tests:
        result = contains_corporate_keyword(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} contains_corporate_keyword('{text}') = {result} (expected {expected})")
    
    print("\ncontains_known_brand() tests:")
    print("-" * 80)
    brand_tests = [
        ("Spotify", True),
        ("John Smith", False),
        ("NPR", True),
    ]
    for text, expected in brand_tests:
        result = contains_known_brand(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} contains_known_brand('{text}') = {result} (expected {expected})")
    
    print("\nhas_organizational_pattern() tests:")
    print("-" * 80)
    pattern_tests = [
        ("Smith & Associates", True),
        ("The Beatles", True),
        ("John Smith", False),
        ("Sarah Jones", False),
    ]
    for text, expected in pattern_tests:
        result = has_organizational_pattern(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} has_organizational_pattern('{text}') = {result} (expected {expected})")
    
    print("\nhas_plural_indicator() tests:")
    print("-" * 80)
    plural_tests = [
        ("Mary and Friends", True),
        ("John Smith", False),
        ("The Team", True),
    ]
    for text, expected in plural_tests:
        result = has_plural_indicator(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} has_plural_indicator('{text}') = {result} (expected {expected})")


if __name__ == '__main__':
    print()
    test_individual_functions()
    print()
    exit_code = run_tests()
    exit(exit_code)
