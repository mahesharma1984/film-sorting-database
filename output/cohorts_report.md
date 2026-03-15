# Failure Cohort Analysis

Generated: 2026-03-04 | Films analyzed: 361 total, 350 unsorted | Actionable cohorts: 2

---

## Data Readiness Summary

| Level | Count | Notes |
|-------|-------|-------|
| R0 (no year) | 173 | Films with no year — supplements, interviews, non-film conte... |
| R1 (no API data) | 106 | Films with year but no API data (no director, no country). R... |
| R2/R3 (actionable) | 71 | Analyzed below |

---

## Cohort Summary

| # | Cohort | Type | Films | Confidence | Action |
|---|--------|------|-------|------------|--------|
| 1 | Missing country + genres → nearest: French New Wave (6 films) | data_gap | 6 | 🟡 MEDIUM | Enrich data |
| 2 | Joe Dante — Blaxploitation (2 films) | director_gap | 2 | 🟡 MEDIUM | Add director |
| 3 | Missing country + genres → nearest: Classic Hollywood (3 films) | data_gap | 3 | 🔴 LOW | Enrich data |
| 4 | Missing country + genres → nearest: Brazilian Exploitation (2 films) | data_gap | 2 | 🔴 LOW | Enrich data |

---

## [1] Missing country + genres → nearest: French New Wave (6 films)

**Type:** `data_gap` | **Confidence:** 🟡 **MEDIUM**

**Binding constraint:** API fields absent: country,genres

**Hypothesis:**
> These 6 films are blocked by missing country + genres data. Nearest match is French New Wave — enriching country + genres would likely resolve routing. Add known data to output/manual_enrichment.csv and re-run classify.

| Title | Year | Director | Country | Nearest miss |
|-------|------|----------|---------|--------------|
| Russ Meyer | 1970 | Cherry Harry e Raquel |  | French New Wave |
| L'astragale | 1968 | Guy Casaril |  | French New Wave |
| Kurotokage | 1962 | Umetsugu Inoue |  | French New Wave |
| Lilford Hall | 1969 | Peter Whitehead |  | French New Wave |
| Les amants de Montparnasse (Mo | 1958 | Jacques Becker |  | French New Wave |
| Ophelia—The Cat Lady | 1969 | Tom Chomont |  | French New Wave |

---

## [2] Joe Dante — Blaxploitation (2 films)

**Type:** `director_gap` | **Confidence:** 🟡 **MEDIUM**

**Binding constraint:** Director "Joe Dante" not in Blaxploitation directors list

**Hypothesis:**
> Add "dante" (or the full name "Joe Dante") to SATELLITE_ROUTING_RULES['Blaxploitation']['directors'] in lib/constants.py. This would immediately route 2 films to Blaxploitation. Verify director membership in the Blaxploitation movement before adding.

| Title | Year | Director | Country | Nearest miss |
|-------|------|----------|---------|--------------|
| Matinee | 1993 | Joe Dante | US | Blaxploitation |
| The Second Civil War | 1997 | Joe Dante | US | Blaxploitation |

---

## [3] Missing country + genres → nearest: Classic Hollywood (3 films)

**Type:** `data_gap` | **Confidence:** 🔴 **LOW**

**Binding constraint:** API fields absent: country,genres

**Hypothesis:**
> These 3 films are blocked by missing country + genres data. Nearest match is Classic Hollywood — enriching country + genres would likely resolve routing. Add known data to output/manual_enrichment.csv and re-run classify.

| Title | Year | Director | Country | Nearest miss |
|-------|------|----------|---------|--------------|
|  | 1944 | Roy William Neill |  | Classic Hollywood |
| Tavaszi zápor | 1932 | Fejős Pál |  | Classic Hollywood |
| Señor Droopy | 1949 | Tex Avery |  | Classic Hollywood |

---

## [4] Missing country + genres → nearest: Brazilian Exploitation (2 films)

**Type:** `data_gap` | **Confidence:** 🔴 **LOW**

**Binding constraint:** API fields absent: country,genres

**Hypothesis:**
> These 2 films are blocked by missing country + genres data. Nearest match is Brazilian Exploitation — enriching country + genres would likely resolve routing. Add known data to output/manual_enrichment.csv and re-run classify.

| Title | Year | Director | Country | Nearest miss |
|-------|------|----------|---------|--------------|
| Le livre de Marie | 1985 | Anne-Marie Miéville |  | Brazilian Exploitati |
| Clive Barker | 1995 | Lord of Illusions Unra |  | Brazilian Exploitati |

---

## No-API-Data Films (R1 — 106 films)

These films have a year but returned no director or country from TMDb/OMDb.
They are not analyzed as individual cohorts because the root cause is data absence,
not a routing rule gap.

**Remedy:** Add known director/country to `output/manual_enrichment.csv` for
individual films, or investigate title parsing if API lookups are failing.
