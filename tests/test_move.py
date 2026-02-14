#!/usr/bin/env python3
"""
Test suite for move.py — dry-run logic and same-FS detection
"""

import pytest
import sys
import os
import csv
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from move import same_filesystem, move_file, process_manifest


class TestSameFilesystem:
    """Test same-filesystem detection"""

    def test_same_directory(self):
        """Files in same directory are on same filesystem"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "a").touch()
            (p / "b").touch()
            assert same_filesystem(p / "a", p / "b")

    def test_tmpdir_is_same_fs(self):
        """Two temp dirs on same OS volume should be same FS"""
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            assert same_filesystem(Path(d1), Path(d2))

    def test_nonexistent_path_returns_false(self):
        """Non-existent paths should return False (not crash)"""
        assert same_filesystem(Path("/nonexistent/a"), Path("/nonexistent/b")) is False


class TestMoveFile:
    """Test file move mechanics"""

    def test_rename_move(self):
        """Same-FS move via os.rename"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            source = p / "source.txt"
            dest = p / "subdir" / "dest.txt"
            source.write_text("hello")

            result = move_file(source, dest, use_rename=True)

            assert result is True
            assert dest.exists()
            assert not source.exists()
            assert dest.read_text() == "hello"

    def test_copy_move(self):
        """Cross-FS move via copy+verify+delete"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            source = p / "source.txt"
            dest = p / "subdir" / "dest.txt"
            source.write_text("hello world")

            result = move_file(source, dest, use_rename=False)

            assert result is True
            assert dest.exists()
            assert not source.exists()
            assert dest.read_text() == "hello world"


class TestDryRun:
    """Test dry-run behavior"""

    def test_dry_run_does_not_move(self):
        """Dry run should not move any files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)

            # Create source file
            source_dir = p / "source"
            source_dir.mkdir()
            (source_dir / "film.mkv").write_text("video data")

            # Create library dir
            library_dir = p / "library"
            library_dir.mkdir()

            # Create manifest
            manifest_path = p / "manifest.csv"
            with open(manifest_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'filename', 'title', 'year', 'director',
                    'language', 'country', 'user_tag',
                    'tier', 'decade', 'subdirectory',
                    'destination', 'confidence', 'reason'
                ])
                writer.writeheader()
                writer.writerow({
                    'filename': 'film.mkv',
                    'title': 'Film',
                    'year': '1980',
                    'director': '',
                    'language': '',
                    'country': '',
                    'user_tag': '',
                    'tier': 'Popcorn',
                    'decade': '1980s',
                    'subdirectory': '',
                    'destination': '1980s/Popcorn/',
                    'confidence': '1.0',
                    'reason': 'explicit_lookup',
                })

            stats = process_manifest(manifest_path, source_dir, library_dir, dry_run=True)

            assert stats['moved'] == 1
            # Source file should still exist (dry run)
            assert (source_dir / "film.mkv").exists()

    def test_skips_unsorted(self):
        """Unsorted tier should be skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            source_dir = p / "source"
            source_dir.mkdir()
            library_dir = p / "library"
            library_dir.mkdir()

            manifest_path = p / "manifest.csv"
            with open(manifest_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'filename', 'title', 'year', 'director',
                    'language', 'country', 'user_tag',
                    'tier', 'decade', 'subdirectory',
                    'destination', 'confidence', 'reason'
                ])
                writer.writeheader()
                writer.writerow({
                    'filename': 'unknown.mkv',
                    'title': 'Unknown',
                    'year': '',
                    'director': '',
                    'language': '',
                    'country': '',
                    'user_tag': '',
                    'tier': 'Unsorted',
                    'decade': '',
                    'subdirectory': '',
                    'destination': 'Unsorted/',
                    'confidence': '0.0',
                    'reason': 'unsorted_no_year',
                })

            stats = process_manifest(manifest_path, source_dir, library_dir, dry_run=True)

            assert stats['skipped_unsorted'] == 1
            assert stats['moved'] == 0

    def test_skips_already_exists(self):
        """Files already at destination should be skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            source_dir = p / "source"
            source_dir.mkdir()
            (source_dir / "film.mkv").write_text("data")

            library_dir = p / "library"
            dest = library_dir / "1980s" / "Popcorn"
            dest.mkdir(parents=True)
            (dest / "film.mkv").write_text("data")

            manifest_path = p / "manifest.csv"
            with open(manifest_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'filename', 'title', 'year', 'director',
                    'language', 'country', 'user_tag',
                    'tier', 'decade', 'subdirectory',
                    'destination', 'confidence', 'reason'
                ])
                writer.writeheader()
                writer.writerow({
                    'filename': 'film.mkv',
                    'title': 'Film',
                    'year': '1980',
                    'director': '',
                    'language': '',
                    'country': '',
                    'user_tag': '',
                    'tier': 'Popcorn',
                    'decade': '1980s',
                    'subdirectory': '',
                    'destination': '1980s/Popcorn/',
                    'confidence': '1.0',
                    'reason': 'explicit_lookup',
                })

            stats = process_manifest(manifest_path, source_dir, library_dir, dry_run=False)

            assert stats['skipped_exists'] == 1
            assert stats['moved'] == 0
