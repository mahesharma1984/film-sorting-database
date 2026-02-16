# Thread Discovery Guide

**Status:** AUTHORITATIVE
**Last Updated:** 2026-02-16
**Issue:** #12

## Overview

Thread discovery is a **read-only research layer** that uses TMDb keywords to find thematic connections between films. It never modifies classifications—it's purely for exploration and curation decisions.

### Key Concept: Tentpole Films

Each Satellite category is anchored by 3-5 "tentpole films"—canonical examples that define the category's thematic essence. Keywords from these tentpoles create a profile that can be matched against any film in your collection.

**Example:**
- **Giallo tentpoles:** Deep Red (1975), Suspiria (1977), Blood and Black Lace (1964)
- **Shared keywords:** murder, mystery, psycho-killer, italy, horror
- **Discovery:** Query any film's keywords → find Jaccard overlap → rank connections

---

## Quick Start

### 1. Build the Thread Index

First, build the keyword index from tentpole films:

```bash
python scripts/build_thread_index.py --summary
```

**What it does:**
- Queries TMDb for each tentpole film's keywords
- Aggregates keywords by category with frequency counts
- Outputs `output/thread_keywords.json`

**Requirements:**
- TMDb API key in `config.yaml`
- Internet connection for API queries
- Uses cache to minimize API calls

**Output:**
```
=== THREAD KEYWORD INDEX SUMMARY ===

Giallo:
  Tentpoles: 5
  Unique keywords: 47
  Query failures: 0
  Top keywords:
    - murder (count: 5)
    - mystery (count: 4)
    - psycho-killer (count: 3)
    ...
```

### 2. Discover Threads for a Film

Find which Satellite threads a film connects to:

```bash
python scripts/thread_query.py --discover "Deep Red (1975)"
```

**Output:**
```
Found 1 thread connection(s):

1. Giallo
   Jaccard score: 0.856
   Shared keywords (12): murder, mystery, investigation, italy, psycho-killer, ...
```

### 3. Explore Category Keywords

See what defines a Satellite category:

```bash
python scripts/thread_query.py --thread "Giallo" --top 30
```

**Output:**
```
Thread: Giallo
Top 30 keywords:

 1. murder                     (count: 5, in: Deep Red, Tenebrae, The Beyond)
 2. mystery                    (count: 4, in: Deep Red, Blood and Black Lace)
 3. psycho-killer              (count: 3, in: Deep Red, Tenebrae)
 ...
```

### 4. List All Categories

View all Satellite categories and their tentpoles:

```bash
python scripts/thread_query.py --list --verbose
```

---

## Thread Discovery Dashboard

View thread connections visually in the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

Navigate to **Thread Discovery** section:

**Panel 1: Discover Threads for a Film**
- Enter film title and optional year
- Adjust minimum overlap threshold (default: 0.15)
- View radar chart of Jaccard scores
- Expand to see shared keywords

**Panel 2: Category Keyword Profiles**
- Select a Satellite category
- View bar chart of keyword frequencies
- See which tentpole films contributed each keyword

**Panel 3: Thread Coverage in Collection**
- Unique keywords per category
- Tentpoles vs query failures
- Index statistics

---

## Understanding Jaccard Scores

Thread discovery uses **Jaccard similarity** to measure keyword overlap:

```
Jaccard = |intersection| / |union|
```

**Example:**
- **Giallo keywords:** {murder, mystery, psycho-killer}
- **Film keywords:** {murder, mystery, thriller, action}
- **Intersection:** {murder, mystery} = 2
- **Union:** {murder, mystery, psycho-killer, thriller, action} = 5
- **Jaccard score:** 2/5 = 0.40

### Score Interpretation

| Range | Meaning | Example |
|-------|---------|---------|
| 0.4+ | **Strong connection** | Film is likely in this category |
| 0.2-0.4 | **Moderate connection** | Film shares themes with category |
| 0.15-0.2 | **Weak connection** | Tangential thematic overlap |
| < 0.15 | **Noise** | Suppressed by default |

**Tuning the threshold:**
- Lower `--min-overlap` to see more connections (including weak ones)
- Raise it to see only strong matches
- Default 0.15 filters noise while allowing tangential discoveries

---

## CLI Reference

### `build_thread_index.py`

Build keyword index from tentpole films.

**Usage:**
```bash
python scripts/build_thread_index.py [--config CONFIG] [--summary]
```

**Options:**
- `--config PATH` — Path to config file (default: `config.yaml`)
- `--summary` — Print human-readable summary after building

**Output:** `output/thread_keywords.json`

**Example:**
```bash
# Build index with default config
python scripts/build_thread_index.py --summary

# Use custom config
python scripts/build_thread_index.py --config config_external.yaml
```

---

### `thread_query.py`

Query thread connections and category profiles.

**Usage:**
```bash
python scripts/thread_query.py [--discover FILM | --thread CATEGORY | --list]
```

**Commands:**

#### `--discover FILM`
Discover thread connections for a film.

**Options:**
- `--year YEAR` — Film year (if not in title)
- `--min-overlap FLOAT` — Minimum Jaccard threshold (default: 0.15)

**Examples:**
```bash
# Discover threads for Deep Red
python scripts/thread_query.py --discover "Deep Red (1975)"

# Query without year in title
python scripts/thread_query.py --discover "Faster Pussycat Kill Kill" --year 1965

# Lower threshold to see weak connections
python scripts/thread_query.py --discover "Blade Runner" --min-overlap 0.1
```

#### `--thread CATEGORY`
Query keyword profile for a Satellite category.

**Options:**
- `--top N` — Number of keywords to show (default: 20)

**Examples:**
```bash
# Show top 20 Giallo keywords
python scripts/thread_query.py --thread "Giallo"

# Show all keywords
python scripts/thread_query.py --thread "Pinku Eiga" --top 100
```

#### `--list`
List all Satellite categories with tentpole counts.

**Options:**
- `--verbose` / `-v` — Show tentpole films for each category

**Examples:**
```bash
# List categories
python scripts/thread_query.py --list

# List with tentpole details
python scripts/thread_query.py --list --verbose
```

---

## Programmatic API

Use thread discovery in Python scripts:

### Discover Threads

```python
from lib.rag.query import discover_threads

# Discover threads for a film
threads = discover_threads("Deep Red", 1975, min_overlap=0.15)

for thread in threads:
    print(f"{thread['category']}: {thread['jaccard_score']:.2f}")
    print(f"  Shared keywords: {', '.join(thread['shared_keywords'][:5])}")
```

### Query Category Profile

```python
from lib.rag.query import query_thread_category

# Get Giallo keyword profile
data = query_thread_category("Giallo", top_k=20)

print(f"Category: {data['category']}")
print(f"Keywords: {len(data['keywords'])}")

for kw in data['keywords'][:5]:
    print(f"  {kw['keyword']}: {kw['count']} occurrences")
```

### Direct ThreadDiscovery Class

```python
from pathlib import Path
from lib.rag.threads import ThreadDiscovery

# Load thread index
index_path = Path('output/thread_keywords.json')
discovery = ThreadDiscovery(index_path)

# Query specific category
film_keywords = ['murder', 'mystery', 'thriller']
result = discovery.query_thread('Giallo', film_keywords, min_overlap=0.2)

if result:
    print(f"Jaccard: {result['jaccard_score']:.3f}")
    print(f"Overlap: {result['overlap_count']} keywords")
```

---

## Use Cases

### 1. Curation Decisions

**Scenario:** You have an Italian thriller from the 1970s. Is it Giallo or just thriller?

```bash
python scripts/thread_query.py --discover "Your Vice Is a Locked Room (1972)"
```

If Jaccard > 0.3 for Giallo, strong evidence it belongs in that category.

### 2. Collection Pruning

**Scenario:** Which films connect to zero threads? (Deletion candidates)

Run discovery on all films, flag those with no connections above 0.15.

### 3. Finding Thematic Clusters

**Scenario:** What other films share themes with this one?

1. Discover threads for film A
2. Query all films in those thread categories
3. Rank by keyword overlap

### 4. Validating Tentpoles

**Scenario:** Are the tentpole films representative of the category?

```bash
python scripts/thread_query.py --thread "Giallo"
```

Check if top keywords align with your curatorial understanding of Giallo.

---

## How It Works

### Architecture

```
┌─────────────────────┐
│ SATELLITE_TENTPOLES │  (lib/constants.py)
│   33 films across   │
│   9 categories      │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│   TMDb Keywords     │  (lib/tmdb.py)
│   API fetch with    │
│   append_to_response│
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  build_thread_index │  (scripts/)
│  Aggregate keywords │
│  by frequency       │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ thread_keywords.json│  (output/)
│ {category: {        │
│   keywords: [...],  │
│   tentpoles: [...]} │
│ }                   │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│  ThreadDiscovery    │  (lib/rag/threads.py)
│  Jaccard similarity │
│  scoring            │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│   thread_query.py   │  (scripts/)
│   CLI interface     │
└─────────────────────┘
```

### R/P Split

Thread discovery follows the project's R/P (Reasoning/Precision) split:

**PRECISION tasks:**
- Keyword extraction from TMDb (deterministic API parse)
- Jaccard similarity calculation (mathematical formula)
- File I/O (reading thread index)

**REASONING tasks:**
- Selecting tentpole films (curatorial judgment)
- Tuning overlap thresholds (empirical testing)
- Interpreting thread connections (human analysis)

---

## Tentpole Film Selection Criteria

Tentpoles must meet these requirements:

1. **Decade bounds:** Must respect `SATELLITE_ROUTING_RULES` decades
   - Example: Giallo valid 1960s-1980s only

2. **Category representative:** Defines the thematic essence
   - Example: Deep Red is quintessential Giallo

3. **Count:** 3-5 films per category
   - Too few → narrow profile
   - Too many → diluted signal

4. **Core directors allowed:** If they define the category
   - Example: Ōshima in Pinku Eiga (curatorial, not classification)

5. **Availability:** Film must exist in TMDb
   - Query failures noted in index

**Current tentpoles:** 33 films across 9 categories
- Defined in `lib/constants.py` as `SATELLITE_TENTPOLES`
- View with `python scripts/thread_query.py --list --verbose`

---

## Troubleshooting

### "Thread index not found"

**Problem:** `output/thread_keywords.json` doesn't exist

**Solution:**
```bash
python scripts/build_thread_index.py --summary
```

Requires TMDb API key in `config.yaml`.

### "No threads found above threshold"

**Problem:** Film keywords don't overlap with any category

**Possible causes:**
1. Film is truly uncategorizable (correct result)
2. Threshold too high (try `--min-overlap 0.1`)
3. Film lacks TMDb keywords (obscure film)
4. Keywords don't match category profiles (genre mismatch)

### "TMDb API key required"

**Problem:** `config.yaml` missing `tmdb_api_key`

**Solution:**
```yaml
# config.yaml
tmdb_api_key: "your_api_key_here"
```

Get free key at: https://www.themoviedb.org/settings/api

### Query failures in index

**Problem:** Some tentpoles failed to query

**Check:**
```bash
python scripts/build_thread_index.py --summary
```

Look for "Query failures" in output. This usually means:
- Film not in TMDb database
- Title normalization mismatch
- API timeout

**Fix:** Edit `SATELLITE_TENTPOLES` in `lib/constants.py` to use alternative films.

---

## Extending Thread Discovery

### Adding New Categories

1. **Define routing rules** in `lib/constants.py`:
   ```python
   SATELLITE_ROUTING_RULES = {
       'New Category': {
           'country_codes': ['XX'],
           'decades': ['1970s', '1980s'],
           'genres': ['Genre1', 'Genre2'],
           'directors': [],
       }
   }
   ```

2. **Select tentpole films**:
   ```python
   SATELLITE_TENTPOLES = {
       'New Category': [
           ('Film 1', 1975, 'Director A'),
           ('Film 2', 1978, 'Director B'),
           ('Film 3', 1982, 'Director C'),
       ]
   }
   ```

3. **Rebuild index**:
   ```bash
   python scripts/build_thread_index.py --summary
   ```

### Changing Tentpoles

1. Edit `SATELLITE_TENTPOLES` in `lib/constants.py`
2. Rebuild index: `python scripts/build_thread_index.py --summary`
3. Verify: `python scripts/thread_query.py --thread "Your Category"`

### Custom Similarity Metrics

Currently uses Jaccard similarity. To use other metrics (Cosine, Overlap Coefficient):

1. Extend `ThreadDiscovery.query_thread()` in `lib/rag/threads.py`
2. Add parameter: `metric='jaccard'|'cosine'|'overlap'`
3. Implement metric calculation
4. Update CLI with `--metric` flag

---

## Design Principles

### Read-Only Discovery

Thread discovery **never modifies**:
- Film classifications
- Tier assignments
- Manifest entries
- `SORTING_DATABASE.md`

It's a **research tool**, not a classifier.

### Zero Additional API Calls

TMDb keywords are fetched via `append_to_response='credits,keywords'`.

**Before Issue #12:** 1 API call per film (credits only)
**After Issue #12:** 1 API call per film (credits + keywords)

No cost increase—keywords come free in same response.

### Backward Compatible

Old TMDb cache entries work seamlessly:
- Missing `keywords` field → defaults to empty list `[]`
- New queries automatically add keywords
- No cache invalidation required

### Curatorial Anchoring

Tentpole films are **human-curated**, not algorithmic:
- Reflects curatorial judgment
- Anchors category definitions
- Makes discovery explainable

---

## Related Documentation

- **[SATELLITE_CATEGORIES.md](SATELLITE_CATEGORIES.md)** - Category definitions with caps and examples
- **[TIER_ARCHITECTURE.md](theory/TIER_ARCHITECTURE.md)** - Why satellite categories exist
- **[MARGINS_AND_TEXTURE.md](theory/MARGINS_AND_TEXTURE.md)** - Philosophy of satellite tier
- **[RAG_QUERY_GUIDE.md](RAG_QUERY_GUIDE.md)** - RAG system (separate from thread discovery)

---

## Changelog

**2026-02-16 — Initial Implementation (Issue #12)**
- Add TMDb keywords extraction
- Define 33 tentpole films across 9 categories
- Implement Jaccard similarity scoring
- Create CLI tools and dashboard integration
- 16 unit tests (164 total passing)
