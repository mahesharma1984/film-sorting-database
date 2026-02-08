# External Drive Configuration Guide

Working with external drives requires special path considerations and performance optimization.

## Finding Your External Drive Path

### Windows
```cmd
# List all drives
wmic logicaldisk get size,freespace,caption

# Example paths:
E:\Movies\Unsorted
F:\Cinema Collection\Raw Files
G:\My Films\To Sort
```

### macOS
```bash
# List mounted drives
ls /Volumes/

# Example paths:
/Volumes/External Drive/Movies/Unsorted
/Volumes/Cinema Collection/Unsorted Films
/Volumes/My Passport/Movies/Raw
```

### Linux
```bash
# List mounted drives
ls /mnt/
# or
ls /media/

# Example paths:
/mnt/external/Movies/Unsorted
/media/username/External/Cinema/Unsorted
/media/username/My Passport/Films/Raw
```

## Sample config.yaml for External Drive

```yaml
# Example configuration for external drive setup
project_path: "C:/Users/YourName/Documents/cinema-project"
library_path: "E:/Movies/Organized"           # External drive destination
source_path: "E:/Movies/Unsorted"             # External drive source

# Alternative setup - project on internal, movies on external
project_path: "/Users/YourName/Documents/cinema-project"
library_path: "/Volumes/Cinema Drive/Organized Library"
source_path: "/Volumes/Cinema Drive/Unsorted Collection"
```

## Performance Considerations for External Drives

### USB 3.0+ Recommended
- USB 2.0: ~35 MB/s (slow for large files)
- USB 3.0: ~100+ MB/s (good)
- USB-C/Thunderbolt: ~500+ MB/s (excellent)

### Optimization Tips

1. **Run script on same drive as files**
   ```bash
   # Copy script to external drive first
   cp film_sorter.py /Volumes/External\ Drive/
   cd /Volumes/External\ Drive/
   python3 film_sorter.py ./Unsorted --dry-run
   ```

2. **Use local temp directory for processing**
   ```yaml
   # In config.yaml
   temp_directory: "C:/temp"  # Fast internal drive for temp files
   ```

3. **Process in batches for very large collections**
   ```bash
   # Process one decade at a time
   python3 film_sorter.py ./1970s-Films --dry-run
   python3 film_sorter.py ./1980s-Films --dry-run
   ```

## Drive Space Planning

### Before Sorting
Check available space:
```bash
# Windows
dir /-c E:\Movies

# macOS/Linux
df -h /Volumes/External\ Drive
```

### Folder Structure Size Estimates
```
External Drive (2TB example):
├── Organized Library/          # ~800-1200 GB (final sorted)
│   ├── 1950s/
│   ├── 1960s/
│   └── [other decades]
├── Staging/                    # ~100-200 GB (temporary)
├── Original Unsorted/          # ~800-1200 GB (source files)
└── Out/Cut/                    # ~50-100 GB (files to delete)
```

**Recommend 2-3x collection size for reorganization buffer**

## Handling Drive Connection Issues

### Drive Mounting Check
```python
# Add to config.yaml
drive_check: true  # Verify drive is mounted before running

# The script will check if paths exist before starting
```

### Disconnection Recovery
```bash
# If drive disconnects mid-process
python3 film_sorter.py --resume /path/to/last/manifest.csv
```

## Network Attached Storage (NAS)

### SMB/CIFS Shares
```yaml
# Mount network drive first, then use local path
library_path: "/mnt/nas/Movies/Organized"
source_path: "/mnt/nas/Movies/Unsorted"
```

### Performance Tips for NAS
- Use wired connection (not WiFi)
- Enable SMB3+ protocol
- Consider running script directly on NAS if possible

## File System Considerations

### NTFS (Windows/Cross-platform)
✅ Best compatibility
✅ Large file support
⚠️ May need permissions fix on macOS/Linux

### exFAT (Cross-platform)
✅ Works on all platforms
✅ Large file support
⚠️ Less robust than NTFS

### HFS+/APFS (macOS only)
✅ Optimal for Mac-only setups
❌ Limited Windows compatibility

### ext4 (Linux only)
✅ Optimal for Linux
❌ No Windows/Mac support

## Example Complete Setup

### 1. Find External Drive
```bash
# macOS
diskutil list
# Look for external drive, note mount point
```

### 2. Update config.yaml
```yaml
project_path: "/Users/YourName/Documents/cinema-project"
library_path: "/Volumes/Cinema Collection/Organized"
source_path: "/Volumes/Cinema Collection/Unsorted"
tmdb_api_key: "your_api_key_here"
```

### 3. Test Drive Performance
```bash
# Copy a large test file to check speed
cp "large_movie.mkv" "/Volumes/Cinema Collection/test.mkv"
# Should be 50+ MB/s for good experience
```

### 4. Run Sorting
```bash
# Always start with dry-run
python3 film_sorter.py "/Volumes/Cinema Collection/Unsorted" --dry-run

# Review staging report, then execute
python3 film_sorter.py "/Volumes/Cinema Collection/Unsorted"
```

## Troubleshooting External Drives

### "Permission Denied" Errors
```bash
# macOS - grant permission
sudo chmod -R 755 "/Volumes/External Drive"

# Linux - mount with proper permissions
sudo mount -o uid=$(id -u),gid=$(id -g) /dev/sdb1 /mnt/external
```

### "Path Not Found" Errors
- Drive may have disconnected
- Check exact path spelling (case-sensitive on macOS/Linux)
- Verify drive is mounted: `ls /Volumes/` or `ls /mnt/`

### Slow Performance
- Use USB 3.0+ port
- Close other applications accessing drive
- Consider smaller batch sizes
- Check drive health with disk utility

### Cross-Platform Path Issues
```python
# Script handles this automatically with pathlib
# But config paths should use forward slashes:
library_path: "E:/Movies"  # Good (works on all platforms)
library_path: "E:\\Movies" # Avoid (Windows-specific escaping)
```

## Drive Maintenance

### Before Large Operations
1. **Backup important files**
2. **Check drive health** (disk utility)
3. **Ensure stable connection** (no extension cords)
4. **Close other apps** using the drive

### After Sorting
1. **Verify file integrity** (spot-check some moved files)
2. **Review staging report** for manual classification
3. **Clean up /Out/Cut/** after 30-day safety period
4. **Update backup** of organized collection
