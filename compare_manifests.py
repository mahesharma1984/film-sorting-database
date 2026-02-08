#!/usr/bin/env python3
"""
Compare old manifest (broken) vs new manifest (fixed) to show improvements
"""
import csv
from collections import defaultdict

# Read old manifest (broken classifier)
old_stats = defaultdict(int)
old_films = {}

try:
    with open('output/sorting_manifest_v01.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tier = row['tier']
            old_stats[tier] += 1
            old_films[row['original_filename']] = row
except FileNotFoundError:
    print("Old manifest not found at output/sorting_manifest_v01.csv")

# Read new manifest (fixed classifier)
new_stats = defaultdict(int)
new_films = {}

try:
    with open('output/sorting_manifest_v01_fixed.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tier = row['tier']
            new_stats[tier] += 1
            new_films[row['original_filename']] = row
except FileNotFoundError:
    print("New manifest not found. Please run:")
    print('  python classify_v01.py "/Volumes/One Touch/movies/Unsorted" --output output/sorting_manifest_v01_fixed.csv')
    exit(1)

# Compare
print("\n" + "="*70)
print("MANIFEST COMPARISON: OLD (BROKEN) vs NEW (FIXED)")
print("="*70)

print(f"\nOLD (Broken Classifier):")
for tier, count in sorted(old_stats.items()):
    print(f"  {tier:15s}: {count:4d}")
print(f"  {'TOTAL':15s}: {sum(old_stats.values()):4d}")

print(f"\nNEW (Fixed Classifier):")
for tier, count in sorted(new_stats.items()):
    print(f"  {tier:15s}: {count:4d}")
print(f"  {'TOTAL':15s}: {sum(new_stats.values()):4d}")

# Find changed classifications
changes = []
for filename in new_films:
    if filename in old_films:
        old_tier = old_films[filename]['tier']
        new_tier = new_films[filename]['tier']
        old_reason = old_films[filename]['reason']
        new_reason = new_films[filename]['reason']

        if old_tier != new_tier or old_reason != new_reason:
            changes.append({
                'filename': filename,
                'old_tier': old_tier,
                'new_tier': new_tier,
                'old_reason': old_reason,
                'new_reason': new_reason,
                'old_dest': old_films[filename]['destination'],
                'new_dest': new_films[filename]['destination']
            })

print(f"\n" + "="*70)
print(f"CHANGES: {len(changes)} films reclassified")
print("="*70)

if changes:
    # Group by type of change
    fixed_films = [c for c in changes if c['old_tier'] == 'Popcorn' and c['old_reason'] == 'format_signal']
    other_changes = [c for c in changes if c not in fixed_films]

    if fixed_films:
        print(f"\n✓ FIXED: {len(fixed_films)} films no longer misclassified as Popcorn")
        print("\nSample (first 10):")
        for change in fixed_films[:10]:
            print(f"  {change['filename'][:60]}")
            print(f"    OLD: {change['old_tier']} ({change['old_reason']})")
            print(f"    NEW: {change['new_tier']} ({change['new_reason']})")

    if other_changes:
        print(f"\nOther changes: {len(other_changes)}")

print("\n" + "="*70)
print("Next steps:")
print("="*70)
print("1. Review the changes above")
print("2. Preview file moves:")
print('   python sort_from_manifest.py output/sorting_manifest_v01_fixed.csv "/Volumes/One Touch/movies/Unsorted" --dry-run')
print("3. Execute moves:")
print('   python sort_from_manifest.py output/sorting_manifest_v01_fixed.csv "/Volumes/One Touch/movies/Unsorted"')
