# Film Sorting Performance Issue Report

## Issue Summary
File sorting is taking **60-80 hours** instead of **minutes** due to unnecessary byte-level copying on the same filesystem.

---

## Root Cause Analysis

### The Problem
The `sort_from_manifest.py` script uses `shutil.copy2()` which performs **byte-by-byte copying** of files, even when source and destination are on the **same filesystem**.

### Evidence
```bash
# Both paths are on the SAME USB drive:
Source:      /Volumes/One Touch/movies/unsorted         (/dev/disk4s2)
Destination: /Volumes/One Touch/movies/Organized        (/dev/disk4s2)

# Current behavior:
- Copying 7.6GB file: ~7 minutes per file
- Total: 1,201 files
- Estimated time: 60-80 hours
```

### What SHOULD Happen
When moving files **within the same filesystem**, the OS should:
1. Update directory entries (instant)
2. No data copying needed
3. Entire operation: **seconds**, not hours

---

## Code Issue

### Current Code (sort_from_manifest.py:54-55)
```python
# PROBLEM: Always copies bytes, even on same filesystem
shutil.copy2(str(source_file), str(dest_file))
```

### What It Should Be
```python
# SOLUTION: Use move() which detects same filesystem
shutil.move(str(source_file), str(dest_file))
# OR
os.rename(str(source_file), str(dest_file))  # For same filesystem only
```

---

## Performance Comparison

| Method | Same Filesystem | Different Filesystem | Current Time | Fixed Time |
|--------|-----------------|---------------------|--------------|------------|
| `shutil.copy2()` | Copies bytes (SLOW) | Copies bytes | **60-80 hrs** | N/A |
| `shutil.move()` | Renames (INSTANT) | Copies then deletes | N/A | **~5 mins** |
| `os.rename()` | Renames (INSTANT) | Fails | N/A | **~2 mins** |

---

## Current Progress
- **Started:** 13:51 PM
- **Files moved:** 4 of 1,201
- **Time elapsed:** 13 minutes
- **Current operation:** Copying 7.6GB file (43% done after 4 minutes)

---

## Impact

### Storage
- USB drive is **100% full** (3.1GB free / 4.5TB total)
- Copying creates duplicates temporarily
- May run out of space mid-operation

### Time
- At current rate: **2-3 days** to complete
- With proper move: **2-5 minutes** to complete
- **Efficiency loss: 99.8%**

---

## Recommended Fix

### Option 1: Stop and Use Optimized Script (RECOMMENDED)
1. Kill current process
2. Fix `sort_from_manifest.py` to use `shutil.move()`
3. Re-run (will complete in minutes)

### Option 2: Use rsync with --remove-source-files
```bash
# Read manifest and generate rsync commands
while IFS=, read -r filename dest; do
  rsync -av --remove-source-files \
    "/Volumes/One Touch/movies/unsorted/$filename" \
    "$dest/$filename"
done < manifest.csv
```

### Option 3: Direct Shell Script
```bash
# Fastest: Direct moves via shell
while IFS=, read -r filename dest; do
  mkdir -p "$dest"
  mv "/Volumes/One Touch/movies/unsorted/$filename" "$dest/$filename"
done < manifest.csv
```

---

## Why This Happened

### Design Flaw in sort_from_manifest.py
The script was designed for "safety" on external drives with this logic:
```python
# Copy file
shutil.copy2(source, dest)
# Verify copy
if dest.exists() and sizes_match:
    source.unlink()  # Delete original
```

**Intention:** Ensure file integrity on unreliable external USB drives

**Reality:** When source and destination are on **same drive**, this creates unnecessary work:
1. Read 7GB from USB → RAM → Write 7GB back to same USB
2. Verify file sizes match
3. Delete original

**Should have checked filesystem first:**
```python
if source.stat().st_dev == dest.parent.stat().st_dev:
    # Same filesystem - just rename (instant)
    os.rename(source, dest)
else:
    # Different filesystem - safe copy/verify/delete
    shutil.copy2(source, dest)
    verify_and_delete(source, dest)
```

---

## Immediate Action Required

**STOP current process** and use fixed approach:
```bash
# Kill slow process
kill 69466

# Use fast approach (move within same filesystem)
# Will complete in 2-5 minutes instead of 2-3 days
```

---

## Lessons Learned

1. **Always check filesystem** before choosing copy vs. move strategy
2. **Test with large files** to catch performance issues early
3. **Monitor initial operations** to detect problems quickly (we caught this after 4 files)
4. **Same-drive operations** should be nearly instant (just metadata updates)
5. **External drives** don't mean "different filesystem" - source/dest can be on same external drive

---

## Verification Commands

```bash
# Check if paths are on same filesystem:
df "/path1" "/path2" | tail -2

# If same device (disk4s2), use move not copy:
# /dev/disk4s2 = SAME FILESYSTEM = USE MOVE

# Monitor current slow operation:
lsof -p 69466 | grep "\.mkv\|\.mp4"
# Shows it's reading AND writing same drive (wasteful)
```

---

## Status: WAITING FOR USER DECISION

Should we:
1. ✅ **STOP and FIX** (2-5 minutes to complete)
2. ❌ **CONTINUE** (2-3 days to complete)

**Recommendation:** Stop and fix immediately.
