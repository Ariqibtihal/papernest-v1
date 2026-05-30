# Journal Quality Data Setup

This document explains how to set up journal quality data for PaperLens.

## Overview

PaperLens uses Scimago Journal Rank (SJR) data to provide journal quality scoring based on Q1-Q4 quartile rankings. This enhances search results by ranking papers from high-quality journals higher.

## Data Sources

### Scimago Journal Rank (SJR)

**URL:** https://www.scimagojr.com/journalrank.php

**What it provides:**
- Journal quartile rankings (Q1-Q4) per subject area
- SJR (SCImago Journal Rank) scores
- H-index
- CiteScore
- Publication metrics

**How to download:**

1. Visit https://www.scimagojr.com/journalrank.php
2. Select your subject area (or "All subject areas" for complete data)
3. Click "Export" → "CSV"
4. Save the file as `data/scimago_journals.csv`

### File Format

The CSV file uses semicolons (`;`) as separators and includes these columns:

| Column | Description |
|--------|-------------|
| Rank | Journal ranking |
| Sourceid | Scimago source ID |
| Title | Journal title |
| Type | Publication type (Journal, Book Series, etc.) |
| Issn | ISSN(s) in format "1234-5678; 1234-5679" |
| Publisher | Publisher name |
| Country | Country of publication |
| Categories | Subject area categories |
| SJR | SCImago Journal Rank score |
| H index | H-index |
| CiteScore | CiteScore metric |
| Q1 | 1 if journal is in Q1 quartile |
| Q2 | 1 if journal is in Q2 quartile |
| Q3 | 1 if journal is in Q3 quartile |
| Q4 | 1 if journal is in Q4 quartile |

### Example CSV Row

```
1;12345;Nature;Journal;0028-0836;Springer Nature;United Kingdom;Multidisciplinary;14.148;844;66.2;1;0;0;0
```

## Setup Instructions

### 1. Download Scimago Data

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Download from Scimago (you'll need to do this manually from the website)
# The file should be saved as: data/scimago_journals.csv
```

### 2. Verify Data Loading

Start PaperLens and check the logs:

```bash
# Start the application
uvicorn app.main:app --reload

# Check logs for journal quality loading
# You should see something like:
# Journal quality data loaded: 45000+ journals (Q1=..., Q2=..., Q3=..., Q4=...)
```

### 3. Test Journal Quality

```bash
# Run the journal quality tests
pytest tests/test_journal_quality.py -v
```

## API Response

When journal quality data is loaded, search results include:

```json
{
  "results": [
    {
      "title": "Paper Title",
      "venue": "Nature",
      "venue_issn": "00280836",
      "journal_quality_score": 0.95,
      "is_predatory": false,
      "final_score": 0.87
    }
  ]
}
```

### New Fields

| Field | Type | Description |
|-------|------|-------------|
| `journal_quality_score` | float | Quality score (0.0-1.0) based on quartile, SJR, H-index |
| `is_predatory` | bool | Whether journal matches predatory journal criteria |

## Scoring Algorithm

Journal quality is calculated using weighted metrics:

```
Quality Score = 0.50 × Quartile Score + 0.25 × SJR Score + 0.25 × H-Index Score
```

### Quartile Scores

| Quartile | Score |
|----------|-------|
| Q1 | 1.00 |
| Q2 | 0.75 |
| Q3 | 0.50 |
| Q4 | 0.25 |
| Unknown | 0.30 |

### Metric Normalization

SJR and H-index are normalized using log-scale to handle the wide range of values:

- **SJR:** `min(1.0, log1p(sjr) / log1p(30))` (typical range: 0-30)
- **H-index:** `min(1.0, log1p(h_index) / log1p(150))` (typical range: 0-150)

## Predatory Journal Detection

PaperLens includes heuristic detection based on [Beall's List criteria](https://beallslist.net/standards/).

### Red Flags

**Suspicious Name Patterns:**
- "International Journal of Advances in..."
- "Global Journal of..."
- "Journal of Emerging Technologies..."
- "World Journal of..."

**Suspicious Publishers:**
- "Academic Emporium"
- "Open Access Publishing"
- "Science Publishing Group"

**Suspicious Domains:**
- `-journal.com`
- `-research.org`
- `-publishing.com`

### Scoring

- 3+ red flags = **Likely Predatory**
- Papers from predatory journals receive a 30% score penalty

## Limitations

1. **Data Freshness:** Scimago data is updated annually. Download new data each year.
2. **Coverage:** Not all journals are indexed by Scimago.
3. **Subject Differences:** Quartiles are relative within subject areas (a Q2 in Physics may have higher metrics than a Q1 in some humanities journals).
4. **Predatory Detection:** Heuristic-based, not definitive. Always verify with additional sources.

## Recommendations

1. **Update Annually:** Download fresh Scimago data each year (typically available in February/March).
2. **Supplement with DOAJ:** For open access validation, consider integrating DOAJ API.
3. **Manual Verification:** For critical use cases, manually verify journal quality using multiple sources:
   - Scimago: https://www.scimagojr.com
   - Web of Science: https://mjl.clarivate.com
   - DOAJ: https://doaj.org
   - Beall's List: https://beallslist.net
