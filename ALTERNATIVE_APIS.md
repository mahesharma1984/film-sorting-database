# Alternative Film Metadata APIs - Analysis

**Context:** TMDb dependency causes 40-50% of Unsorted films (obscure/foreign films not in database or poor metadata). Can we use alternative/supplementary APIs?

**Status:** ✅ **OMDb integration implemented** (2026-02-16)
- OMDb fallback active in classify.py
- Expected impact: +10-15% classification rate
- See [lib/omdb.py](lib/omdb.py) for implementation

---

## Quick Comparison

| API | Free Tier | Coverage | Best For | Weaknesses |
|-----|-----------|----------|----------|------------|
| **TMDb** (current) | Yes (unlimited with key) | Good mainstream, OK foreign | English films, recent releases | Obscure/exploitation films missing |
| **OMDb** | 1,000 req/day | Excellent (IMDb data) | English titles, classic films | Foreign titles, daily limit |
| **IMDb datasets** | Free bulk download | Most comprehensive | Everything (200M+ records) | No API, requires local DB setup |
| **Wikidata** | Unlimited | Excellent foreign films | Non-English, art cinema | Complex queries, sparse genres |
| **Trakt.tv** | Paid only | Good | User-contributed data | No free tier |

---

## Option 1: OMDb API (Best Quick Win)

**Website:** https://www.omdbapi.com/

**What it is:**
- Unofficial IMDb API (scrapes IMDb data)
- Free tier: 1,000 requests/day
- Paid tier: $1/month (1,000 requests/day) or $10/month (100,000/day)

**Data provided:**
```json
{
  "Title": "The Bird with the Crystal Plumage",
  "Year": "1970",
  "Director": "Dario Argento",
  "Country": "Italy, West Germany",
  "Genre": "Horror, Mystery, Thriller",
  "imdbID": "tt0065143"
}
```

**Pros:**
- ✅ More comprehensive than TMDb (IMDb has more obscure films)
- ✅ Better director data (IMDb is authoritative)
- ✅ Simple REST API (easier than TMDb)
- ✅ Cheap ($1/month for 1,000/day is affordable)
- ✅ Better foreign film coverage

**Cons:**
- ⚠️ Daily rate limit (1,000 requests = problem for large batches)
- ⚠️ Genre data less structured than TMDb (text strings, not IDs)
- ⚠️ Unofficial API (could change/break)

**Implementation:**
```python
import requests

def omdb_search(title: str, year: Optional[int]) -> Optional[Dict]:
    """Query OMDb API for film metadata"""
    api_key = "YOUR_API_KEY"
    params = {
        "apikey": api_key,
        "t": title,  # Title search
        "type": "movie"
    }
    if year:
        params["y"] = str(year)
    
    response = requests.get("http://www.omdbapi.com/", params=params)
    data = response.json()
    
    if data.get("Response") == "True":
        return {
            "director": data.get("Director"),
            "countries": [c.strip() for c in data.get("Country", "").split(",")],
            "genres": [g.strip() for g in data.get("Genre", "").split(",")]
        }
    return None
```

**Use case:**
- **Fallback for TMDb failures** - Try TMDb first, if no results try OMDb
- **1,000/day is enough for incremental classification** (not full re-index)

**Impact estimate:** +10-15% classification rate (covers many obscure films TMDb misses)

---

## Option 2: IMDb Datasets (Best Long-term Solution)

**Website:** https://datasets.imdbws.com/

**What it is:**
- Official IMDb bulk data dumps (updated daily)
- Completely free, unlimited usage
- ~200 million titles, 10 million people

**Data files:**
- `title.basics.tsv.gz` - Title info (title, year, genres)
- `title.crew.tsv.gz` - Directors and writers
- `title.akas.tsv.gz` - Alternative titles (foreign language)

**Example data:**
```tsv
tconst    titleType  primaryTitle                          originalTitle                    isAdult  startYear  genres
tt0065143 movie      The Bird with the Crystal Plumage     L'uccello dalle piume di cristallo  0     1970       Horror,Mystery,Thriller
```

**Pros:**
- ✅ Most comprehensive (200M titles vs TMDb ~800K)
- ✅ Excellent foreign film coverage (original + translated titles)
- ✅ Free, unlimited
- ✅ Authoritative director data
- ✅ Updated daily

**Cons:**
- ❌ No API - must download ~2GB compressed files
- ❌ Requires local database setup (SQLite or PostgreSQL)
- ❌ More complex implementation (~1-2 days setup)
- ⚠️ Genre data less granular (no "Giallo", just "Horror,Thriller")

**Implementation:**
```python
import sqlite3
import gzip
import csv

# One-time setup: Download and import to SQLite
def build_imdb_database():
    """Download IMDb datasets and import to SQLite"""
    # Download files
    files = [
        "title.basics.tsv.gz",
        "title.crew.tsv.gz",
        "name.basics.tsv.gz"
    ]
    
    # Import to SQLite (simplified)
    conn = sqlite3.connect("imdb.db")
    # ... import logic ...

# Query function
def imdb_lookup(title: str, year: Optional[int]) -> Optional[Dict]:
    """Look up film in local IMDb database"""
    conn = sqlite3.connect("imdb.db")
    cursor = conn.cursor()
    
    query = """
        SELECT t.primaryTitle, t.startYear, t.genres, 
               GROUP_CONCAT(n.primaryName) as directors
        FROM title_basics t
        JOIN title_crew c ON t.tconst = c.tconst
        JOIN name_basics n ON c.directors LIKE '%' || n.nconst || '%'
        WHERE t.primaryTitle = ? AND t.startYear = ?
    """
    
    cursor.execute(query, (title, year))
    # ... process results ...
```

**Use case:**
- **Replace TMDb entirely** (no API limits, more comprehensive)
- **Offline classification** (no internet required)
- **Batch re-classification** of entire library

**Impact estimate:** +20-30% classification rate (best coverage, especially foreign films)

**Setup effort:** ~2 days (download, import, write query logic)

---

## Option 3: Wikidata SPARQL (Best for Foreign Films)

**Website:** https://query.wikidata.org/

**What it is:**
- Structured knowledge base (Wikipedia's data layer)
- Free, unlimited SPARQL queries
- Excellent multilingual support

**Example query:**
```sparql
SELECT ?film ?filmLabel ?director ?directorLabel ?country ?year
WHERE {
  ?film wdt:P31 wd:Q11424.        # Instance of: film
  ?film rdfs:label "Deep Red"@en. # Title
  ?film wdt:P577 ?date.           # Publication date
  ?film wdt:P57 ?director.        # Director
  ?film wdt:P495 ?country.        # Country of origin
  BIND(YEAR(?date) as ?year)
  FILTER(?year = 1975)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

**Pros:**
- ✅ Free, unlimited
- ✅ Excellent foreign film coverage (multilingual)
- ✅ Structured data (directors, countries, genres)
- ✅ Good for art cinema / festival films

**Cons:**
- ❌ Complex query language (SPARQL learning curve)
- ❌ Sparse genre data (not always tagged)
- ⚠️ Slower than REST APIs (~1-2 seconds per query)
- ⚠️ Some films missing directors/countries

**Implementation:**
```python
import requests

def wikidata_search(title: str, year: Optional[int]) -> Optional[Dict]:
    """Query Wikidata SPARQL endpoint"""
    query = f"""
        SELECT ?director ?directorLabel ?country ?countryLabel
        WHERE {{
          ?film wdt:P31 wd:Q11424.
          ?film rdfs:label "{title}"@en.
          ?film wdt:P577 ?date.
          ?film wdt:P57 ?director.
          ?film wdt:P495 ?country.
          FILTER(YEAR(?date) = {year})
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
    """
    
    url = "https://query.wikidata.org/sparql"
    response = requests.get(url, params={"query": query, "format": "json"})
    # ... parse SPARQL results ...
```

**Use case:**
- **Supplement for foreign films** - Try after TMDb/OMDb fail
- **Art cinema focus** - Wikidata strong for festival films

**Impact estimate:** +5-10% classification rate (fills gaps for foreign films)

---

## Option 4: Trakt.tv API (Not Recommended)

**Website:** https://trakt.tv/

**What it is:**
- User-contributed film/TV tracking
- API available but requires paid VIP subscription ($36/year)

**Pros:**
- ✅ Good coverage of recent films
- ✅ User-contributed metadata

**Cons:**
- ❌ No free tier (costs $36/year)
- ❌ Less comprehensive than IMDb/TMDb
- ❌ Not worth the cost vs free alternatives

**Recommendation:** Skip - OMDb or IMDb datasets are better free alternatives

---

## Recommended Strategy: Multi-Source Fallback Chain

**Best approach:** Use **multiple sources in priority order**

### Implementation: Cascading Enrichment

```python
class MultiSourceEnrichment:
    """Try multiple APIs in fallback order"""
    
    def __init__(self):
        self.tmdb = TMDbClient(api_key)
        self.omdb = OMDbClient(api_key)
        self.imdb = IMDbDatabase("imdb.db")  # Local SQLite
    
    def enrich_metadata(self, title: str, year: Optional[int]) -> Optional[Dict]:
        """Try sources in priority order"""
        
        # 1. Try TMDb first (current, works well for mainstream)
        tmdb_data = self.tmdb.search_film(title, year)
        if tmdb_data and tmdb_data.get('director'):
            return tmdb_data
        
        # 2. Fallback to OMDb (better obscure film coverage)
        omdb_data = self.omdb.search(title, year)
        if omdb_data and omdb_data.get('director'):
            return omdb_data
        
        # 3. Fallback to local IMDb database (most comprehensive)
        imdb_data = self.imdb.lookup(title, year)
        if imdb_data and imdb_data.get('director'):
            return imdb_data
        
        # 4. No results from any source
        return None
```

**Benefits:**
- ✅ Best of all worlds (TMDb speed + OMDb/IMDb coverage)
- ✅ Graceful degradation (if one API fails, try next)
- ✅ Maximize classification rate

**Costs:**
- TMDb: Free
- OMDb: $1-10/month (optional, for fallback)
- IMDb: Free (but 2GB disk space + setup time)

---

## Specific Recommendations

### Quick Win (1-2 hours implementation):

**Add OMDb as TMDb fallback**

```python
# In classify.py, after TMDb enrichment (line 214):
if not tmdb_data and self.omdb:
    omdb_data = self.omdb.search_film(clean_title.strip(), metadata.year)
    if omdb_data:
        if not metadata.director and omdb_data.get('director'):
            metadata.director = omdb_data['director']
        if not metadata.country and omdb_data.get('countries'):
            metadata.country = omdb_data['countries'][0]
```

**Impact:**
- +10-15% classification rate
- Minimal code changes
- Costs $1/month (or 1,000 free requests/day)

**Files to modify:**
- Create `lib/omdb.py` (similar to `lib/tmdb.py`)
- Update `classify.py` lines 200-222 (add fallback)
- Update `config.yaml` (add `omdb_api_key`)

---

### Best Long-term (1-2 days implementation):

**Replace TMDb with local IMDb database**

**Why:**
- Free, unlimited, most comprehensive
- Better for batch re-classification (no rate limits)
- Better foreign film coverage

**Setup:**
```bash
# Download IMDb datasets
wget https://datasets.imdbws.com/title.basics.tsv.gz
wget https://datasets.imdbws.com/title.crew.tsv.gz
wget https://datasets.imdbws.com/name.basics.tsv.gz

# Import to SQLite (create script)
python scripts/build_imdb_database.py

# Use in classification
python classify.py /path/to/films  # No API limits!
```

**Impact:**
- +20-30% classification rate
- Zero ongoing costs
- Offline classification (no internet needed)

---

## Impact Estimates

Current Unsorted rate: **25-30%**

| Enhancement | Implementation | Impact | New Unsorted Rate |
|-------------|---------------|--------|-------------------|
| **OMDb fallback** | 1-2 hours | +10-15% | ~15-20% |
| **IMDb local DB** | 1-2 days | +20-30% | ~5-10% |
| **Wikidata supplement** | 3-4 hours | +5-10% | ~10-15% |
| **All three combined** | 2-3 days | +30-40% | ~5-10% |

**Recommendation:** Start with **OMDb fallback** (quick win), then add **IMDb local DB** for long-term.

---

## Code Example: OMDb Integration

### 1. Create `lib/omdb.py`

```python
"""OMDb API client for film metadata enrichment"""
import requests
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class OMDbClient:
    """Client for OMDb API (IMDb data)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
    
    def search_film(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for film by title and optional year.
        
        Returns:
            {
                'director': str,
                'countries': List[str],
                'genres': List[str]
            }
        """
        params = {
            "apikey": self.api_key,
            "t": title,
            "type": "movie"
        }
        
        if year:
            params["y"] = str(year)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get("Response") == "True":
                logger.debug(f"OMDb hit: '{title}' ({year})")
                return {
                    "director": data.get("Director", "").split(",")[0].strip() if data.get("Director") != "N/A" else None,
                    "countries": [c.strip() for c in data.get("Country", "").split(",")] if data.get("Country") != "N/A" else [],
                    "genres": [g.strip() for g in data.get("Genre", "").split(",")] if data.get("Genre") != "N/A" else []
                }
            else:
                logger.debug(f"OMDb miss: '{title}' ({year})")
                return None
                
        except Exception as e:
            logger.warning(f"OMDb API error: {e}")
            return None
```

### 2. Update `config.yaml`

```yaml
# Add OMDb API key
omdb_api_key: "YOUR_API_KEY_HERE"  # Get from omdbapi.com
```

### 3. Update `classify.py`

```python
# In __init__ method (after TMDb setup, line 104):
omdb_key = self.config.get('omdb_api_key')
if omdb_key:
    from lib.omdb import OMDbClient
    self.omdb = OMDbClient(api_key=omdb_key)
    logger.info("OMDb API fallback enabled")
else:
    self.omdb = None

# In classify() method (after TMDb enrichment, line 222):
# Add OMDb fallback
if not tmdb_data and self.omdb and metadata.title and metadata.year:
    omdb_data = self.omdb.search_film(clean_title.strip(), metadata.year)
    if omdb_data:
        # Enrich metadata with OMDb director if we don't have one
        if not metadata.director and omdb_data.get('director'):
            metadata.director = omdb_data['director']
        # Enrich country if not detected from filename
        if not metadata.country and omdb_data.get('countries'):
            metadata.country = omdb_data['countries'][0] if omdb_data['countries'] else None
        
        # Use OMDb data for satellite classification
        tmdb_data = omdb_data  # Pass to satellite classifier
```

---

## Next Steps

1. **Immediate:** Get OMDb API key (free 1,000/day or $1/month)
2. **Week 1:** Implement OMDb fallback (~2 hours)
3. **Week 2:** Test on current Unsorted films (expect +10-15% classification)
4. **Week 3:** Evaluate IMDb local database (if needed for larger gains)

Want me to implement the OMDb integration now?
