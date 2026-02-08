#!/usr/bin/env python3
"""
Verify which films are in correct vs incorrect locations
"""
import csv
from pathlib import Path
from collections import defaultdict

# Read new manifest (correct classifications)
manifest = {}
with open('output/sorting_manifest_v01_fixed.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        manifest[row['original_filename']] = row

# Scan organized directory to find current locations
organized_base = Path("/Volumes/One Touch/movies/Organized")
current_locations = {}

print("Scanning drive for film locations...")
for file_path in organized_base.rglob("*"):
    if file_path.is_file() and file_path.suffix.lower() in ['.mkv', '.mp4', '.avi', '.mov', '.m4v']:
        # Get relative path from Organized base
        rel_path = file_path.relative_to(organized_base)
        filename = file_path.name
        current_locations[filename] = str(rel_path.parent) if rel_path.parent != Path('.') else ""

print(f"Found {len(current_locations)} video files on disk")
print(f"Manifest has {len(manifest)} entries\n")

# Compare current vs correct locations
correct = []
incorrect = []
missing = []

for filename, expected in manifest.items():
    expected_dest = expected['destination'].strip('/')

    if filename not in current_locations:
        missing.append({
            'filename': filename,
            'expected': expected_dest,
            'reason': 'File not found on disk'
        })
        continue

    current_loc = current_locations[filename]

    # Normalize paths for comparison
    # Current location might be like "Popcorn/1960s"
    # Expected might be "1960s/Core/Stanley Kubrick"
    if current_loc == expected_dest or current_loc.replace('/', '') == expected_dest.replace('/', ''):
        correct.append(filename)
    else:
        incorrect.append({
            'filename': filename,
            'current': current_loc,
            'expected': expected_dest,
            'tier': expected['tier'],
            'reason': expected['reason']
        })

# Report results
print("="*70)
print("LOCATION VERIFICATION RESULTS")
print("="*70)
print(f"\n✓ Correct location: {len(correct)} files")
print(f"✗ Wrong location:   {len(incorrect)} files")
if missing:
    print(f"⚠ Not found:        {len(missing)} files")

if incorrect:
    print("\n" + "="*70)
    print("FILES IN WRONG LOCATIONS (need to be moved)")
    print("="*70)

    # Group by type of move
    by_reason = defaultdict(list)
    for item in incorrect:
        by_reason[item['reason']].append(item)

    print(f"\nTotal files to move: {len(incorrect)}\n")

    # Show breakdown by classification reason
    for reason, items in sorted(by_reason.items()):
        print(f"{reason}: {len(items)} files")

    # Show sample of files that need moving
    print("\n" + "="*70)
    print("SAMPLE: First 20 files to move")
    print("="*70)

    for i, item in enumerate(incorrect[:20], 1):
        print(f"\n{i}. {item['filename'][:65]}")
        print(f"   Current:  {item['current']}")
        print(f"   Expected: {item['expected']}")
        print(f"   Tier: {item['tier']} ({item['reason']})")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
if len(incorrect) > 0:
    print(f"\n{len(incorrect)} files need to be reorganized.")
    print("\nOptions:")
    print("1. Generate a move script to reorganize these files")
    print("2. Review the list and move manually")
    print("3. Leave as-is (files work where they are, just not in 'correct' folders)")
else:
    print("\n✓ All files are in their correct locations!")
    print("No reorganization needed.")

# Save detailed report
with open('output/location_verification_report.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['filename', 'current', 'expected', 'tier', 'reason'])
    writer.writeheader()
    for item in incorrect:
        writer.writerow(item)

print(f"\nDetailed report saved to: output/location_verification_report.csv")
