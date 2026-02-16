# classify_assistant.py Usage Examples

Quick reference for using the RAG-enhanced classification assistant.

## Basic Usage

```bash
python classify_assistant.py "Film Title (Year)" "Director" "Country/Genre"
```

## Examples

### Example 1: Core Director Film (Godard)
```bash
python classify_assistant.py "Alphaville (1965)" "Jean-Luc Godard" "French New Wave"
```

**Result:**
- Found 5 similar Godard films in database
- Suggested: `Core/1960s/Jean-Luc Godard/`
- Confidence: High

---

### Example 2: Unknown Director, Known Category
```bash
python classify_assistant.py "Deep Red (1975)" "Dario Argento" "Italian giallo"
```

**Result:**
- No Argento films in database yet
- Shows similar films from other directors
- Curator makes judgment based on context

---

### Example 3: Film Without Director Info
```bash
python classify_assistant.py "Black Orpheus (1959)" "" "Brazilian cinema"
```

**Result:**
- Searches by title and year
- Finds similar 1950s films
- Suggested: `Reference/1950s/` (based on similar films)

---

### Example 4: Compact Format (Year as Second Arg)
```bash
python classify_assistant.py "Black Orpheus" "1959" "Brazilian drama"
```

Same as Example 3 - script detects year and swaps arguments.

---

### Example 5: Just Title and Year
```bash
python classify_assistant.py "Suspiria (1977)" "" ""
```

Minimal info - RAG searches by title and year only.

---

## Tips

1. **Include as much context as possible** in the third argument
   - ✅ "Italian giallo horror thriller from 1970s"
   - ❌ "horror"

2. **Year in title or separate** - both work:
   - `"Film (1975)" "Director" "Context"`
   - `"Film" "1975" "Context"`

3. **Empty strings for unknown fields:**
   - `"Title (Year)" "" "Context"` (no director)
   - `"Title (Year)" "Director" ""` (no context)

4. **Use quotes for multi-word args:**
   - ✅ `"Dario Argento"`
   - ❌ `Dario Argento` (will treat as two separate args)

---

## Output Explained

The tool shows:

1. **Film Details** - Parsed from your input
2. **Similar Films in Database** - From RAG semantic search
   - Shows score (higher = more similar)
   - Shows destination path
   - Shows director/category
3. **Matching Satellite Categories** - Category definitions from docs
   - Shows decade boundaries
   - Shows capacity caps
   - Validates if year is within bounds
4. **Suggested Classification** - Based on RAG analysis
   - Path suggestion
   - Confidence level (High/Medium/Low)
   - Reasoning explanation

---

## When to Use This Tool

**Use during manual curation:**
- Reviewing Unsorted films after `classify.py` run
- Researching unfamiliar directors
- Checking satellite category boundaries
- Finding similar films for context

**Don't use for:**
- Batch classification (use `classify.py` instead)
- Core/Reference directors (already auto-classified)
- Films already in SORTING_DATABASE.md (already have destination)

---

## Next Steps After Getting Suggestions

1. **Review RAG suggestions** - Are they relevant?
2. **Check category boundaries** - Is the year within valid decades?
3. **Verify capacity** - Is the satellite category at cap?
4. **Update SORTING_DATABASE.md** - Add the film entry:
   ```
   - Film Title (Year) → Tier/Category/Decade/
   ```
5. **Re-run classify.py** - Film will now auto-classify

---

## Integration with classify.py Workflow

```bash
# 1. Run classification
python classify.py /path/to/unsorted --dry-run

# 2. Review staging_report.txt for Unsorted films
cat output/staging_report.txt

# 3. For each Unsorted film, query RAG
python classify_assistant.py "Film (Year)" "Director" "Context"

# 4. Update SORTING_DATABASE.md based on suggestions
# 5. Re-run classification
python classify.py /path/to/unsorted
```

---

## Future Improvements (Stage 2-4)

This tool will evolve:

- **Stage 2:** Access to decision history (past classifications)
- **Stage 3:** Integrated into classify.py (automatic suggestions)
- **Stage 4:** LLM reasoning (Claude API for complex cases)

See Issue #9 for roadmap.
