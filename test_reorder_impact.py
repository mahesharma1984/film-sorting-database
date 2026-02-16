#!/usr/bin/env python3
"""Show impact of priority reordering using actual manifest data"""

import csv
from collections import Counter

# Load manifest
with open('output/sorting_manifest.csv', 'r') as f:
    films = list(csv.DictReader(f))

print("=" * 100)
print("IMPACT ANALYSIS: Priority Reordering (Popcorn/Indie BEFORE Satellite)")
print("=" * 100)
print()

# Find films in American Exploitation from 1980+
am_exploit_1980_plus = [
    f for f in films 
    if 'American Exploitation' in f.get('destination', '') 
    and f.get('year', '').isdigit() 
    and int(f['year']) >= 1980
]

print(f"📊 Films in American Exploitation from 1980+: {len(am_exploit_1980_plus)}")
print()

# Group by decade
by_decade = Counter(f['decade'] for f in am_exploit_1980_plus)
print("By decade:")
for decade in sorted(by_decade.keys()):
    print(f"  {decade}: {by_decade[decade]} films")
print()

# Show sample films that would reclassify
print("=" * 100)
print("SAMPLE FILMS THAT WOULD RECLASSIFY")
print("=" * 100)
print()

samples = am_exploit_1980_plus[:10]
for f in samples:
    print(f"📽️  {f['title']} ({f['year']})")
    print(f"   Director: {f.get('director', 'Unknown')}")
    print(f"   Current: Satellite/American Exploitation/{f['decade']}/")
    print(f"   Proposed: Would check Popcorn/Indie FIRST")
    print()

print("=" * 100)
print("RECOMMENDATION")
print("=" * 100)
print()
print(f"With reordered priority, these {len(am_exploit_1980_plus)} films would be re-evaluated:")
print("  - Mainstream/rewatchable → Popcorn")
print("  - Arthouse/character-driven → Indie Cinema")
print("  - True exploitation → Stays in American Exploitation")
print()
print("This aligns with the principle: Popcorn/Indie (1980+) → Satellite (<1980)")
print()

