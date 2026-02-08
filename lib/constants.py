#!/usr/bin/env python3
"""
Shared constants for film classification system

Single source of truth for format signals, release tags, and other constants.
DO NOT duplicate these lists in other modules - import from here instead.
"""

# Format/edition signals that indicate special curation
# These are METADATA about the edition, not tier classification
FORMAT_SIGNALS = [
    '35mm',
    '16mm',
    '2k',
    '4k',
    'uhd',
    'open matte',
    'extended',
    'unrated',
    "director's cut",
    "directors cut",  # Alternative spelling
    "editor's cut",
    "editors cut",  # Alternative spelling
    'redux',
    'final cut',
    'theatrical',
    'criterion',
    'remux',
    'commentary',
    'special edition',
    'remastered',
    'restored',
    'anniversary',
    'hbo chronological cut',
    'ib tech'
]

# Release group tags to strip from titles
# These are encoding/release metadata, not film metadata
RELEASE_TAGS = [
    'bluray',
    'bdrip',
    'brrip',
    'web-dl',
    'webrip',
    'dvdrip',
    'hdrip',
    'x264',
    'x265',
    'h264',
    'h265',
    'hevc',
    'aac',
    'ac3',
    'dts',
    'dts-hd',
    'eac3',
    'flac',
    '1080p',
    '720p',
    '2160p',
    '4k',  # Also in FORMAT_SIGNALS - intentional overlap
    'uhd',  # Also in FORMAT_SIGNALS - intentional overlap
    'hd',
    'hdr',
    'scan',
    'fullscreen',
    'hybrid',
    'matte',  # Will also catch "open matte" via FORMAT_SIGNALS
    'preview',
    'yify',
    'rarbg',
    'vxt',
    'tigole',
    'sartre',
    'nikt0',
    'baggerinc',
    'gypsy',
    'amzn',
    'nf',
    'hulu',
    'remastered',  # Also in FORMAT_SIGNALS - intentional overlap
    'restored',  # Also in FORMAT_SIGNALS - intentional overlap
    'anniversary',  # Also in FORMAT_SIGNALS - intentional overlap
    'repack'
]
