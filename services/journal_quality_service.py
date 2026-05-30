"""
Journal Quality Service

Provides journal quality scoring based on:
- Scimago Journal Rank (SJR) data - Q1-Q4 quartiles
- Journal metrics (h-index, cite score, impact factor)
- Predatory journal detection (Beall's List criteria)

Data Loading:
- Scimago CSV: Download from https://www.scimagojr.com/journalrank.php
  - Select "All subject areas" -> CSV export
  - Place file as data/scimago_journals.csv

- DOAJ (optional): For open access validation
  - API: https://doaj.org/api/search/journals/

Usage:
    service = JournalQualityService()
    await service.load_data()  # Load from CSV files

    # Lookup by ISSN
    record = service.get_by_issn("1234-5678")

    # Score a paper
    score = service.score_journal("Journal of Machine Learning Research")

    # Check if predatory
    is_pred = service.is_predatory("International Journal of Advances in Computing")
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger

from data.journal_models import (
    JournalQuartile,
    JournalRecord,
    JournalType,
    JournalQualityStats,
    PredatoryJournalCriteria,
)


class JournalQualityService:
    """
    Service for journal quality lookup and scoring.

    Loads journal data from Scimago CSV files and provides:
    - ISSN-based lookup
    - Title-based lookup (fuzzy)
    - Quality scoring (quartile, metrics)
    - Predatory journal detection

    Singleton pattern - use JournalQualityService.instance()
    """

    _instance: JournalQualityService | None = None

    def __new__(cls) -> JournalQualityService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Storage: ISSN -> JournalRecord
        self._records_by_issn: dict[str, JournalRecord] = {}
        # Storage: normalized title -> ISSN (for title lookup)
        self._title_index: dict[str, str] = {}
        # Storage: publisher -> list of ISSNs (for publisher lookup)
        self._publisher_index: dict[str, list[str]] = {}

        # Predatory criteria
        self._predatory_criteria = PredatoryJournalCriteria()

        # Predatory threshold (number of red flags to flag as predatory)
        self._predatory_threshold = 2

        # Stats
        self._stats = JournalQualityStats()

        # Loaded flag
        self._loaded = False
        self._initialized = True

        logger.info("JournalQualityService initialized")

    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None

    @classmethod
    def instance(cls) -> JournalQualityService:
        """Get singleton instance."""
        return cls()

    async def load_data(
        self,
        scimago_csv_path: str | Path | None = None,
    ) -> JournalQualityStats:
        """
        Load journal data from Scimago CSV file.

        Expected CSV columns (Scimago format):
        - Rank
        - Sourceid
        - Title
        - Type
        - Issn
        - SJR
        - H index
        - Quartiles (Q1, Q2, Q3, Q4 columns per subject area)
        - Publisher
        - Country
        - etc.

        Args:
            scimago_csv_path: Path to Scimago CSV file.
                            If None, uses default path data/scimago_journals.csv

        Returns:
            JournalQualityStats with loaded data statistics
        """
        if scimago_csv_path is None:
            scimago_csv_path = Path(__file__).parent.parent / "data" / "scimago_journals.csv"

        path = Path(scimago_csv_path)

        if not path.exists():
            logger.warning(f"Scimago CSV not found at {path}. Using empty journal database.")
            logger.info("Download Scimago data from: https://www.scimagojr.com/journalrank.php")
            return self._stats

        try:
            count = await self._load_scimago_csv(path)
            self._loaded = True
            self._compute_stats()
            logger.info(f"Loaded {count} journals from Scimago CSV")
        except Exception as e:
            logger.exception(f"Failed to load Scimago CSV: {e}")

        return self._stats

    async def _load_scimago_csv(self, path: Path) -> int:
        """Load Scimago CSV file and populate indexes."""
        count = 0

        # Scimago CSV uses semicolon separator
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")

            for row in reader:
                try:
                    record = self._parse_scimago_row(row)
                    if record:
                        self._add_record(record)
                        count += 1
                except Exception as e:
                    logger.debug(f"Skipping row: {e}")
                    continue

        return count

    def _parse_scimago_row(self, row: dict[str, str]) -> JournalRecord | None:
        """Parse a single Scimago CSV row into JournalRecord."""

        # Extract ISSN (Scimago format: "1234-5678; 1234-5679")
        issn_field = row.get("Issn", "").strip()
        if not issn_field:
            return None

        # Parse multiple ISSNs
        issns = re.split(r"[;,]\s*", issn_field)
        issns = [i.strip() for i in issns if i.strip()]

        if not issns:
            return None

        # Normalize ISSNs (remove hyphens)
        primary_issn = self._normalize_issn(issns[0])
        issn_print = self._normalize_issn(issns[0]) if len(issns) > 0 else ""
        issn_electronic = self._normalize_issn(issns[1]) if len(issns) > 1 else ""

        if not primary_issn:
            return None

        # Extract title
        title = row.get("Title", "").strip()
        if not title:
            return None

        # Extract publisher
        publisher = row.get("Publisher", "").strip()

        # Extract country
        country = row.get("Country", "").strip()

        # Extract type
        type_str = row.get("Type", "").strip().lower()
        journal_type = JournalType.UNKNOWN
        if "journal" in type_str:
            journal_type = JournalType.JOURNAL
        elif "book" in type_str:
            journal_type = JournalType.BOOK_SERIES
        elif "trade" in type_str:
            journal_type = JournalType.TRADE_JOURNAL

        # Extract metrics
        sjr = self._parse_float(row.get("SJR", "0"))
        h_index = self._parse_int(row.get("H index", "0"))
        cite_score = self._parse_float(row.get("CiteScore", "0"))
        impact_factor = self._parse_float(row.get("Ref. Doc.", "0"))  # Scimago calls it Ref. Doc.

        # Extract quartiles. Two known Scimago formats:
        #  (a) Modern export: single "SJR Best Quartile" column with value Q1-Q4.
        #  (b) Legacy export: separate Q1/Q2/Q3/Q4 columns, each holding "1".
        quartile = JournalQuartile.UNKNOWN

        best_q = (row.get("SJR Best Quartile") or "").strip().upper()
        quartile_map = {
            "Q1": JournalQuartile.Q1,
            "Q2": JournalQuartile.Q2,
            "Q3": JournalQuartile.Q3,
            "Q4": JournalQuartile.Q4,
        }
        if best_q in quartile_map:
            quartile = quartile_map[best_q]
        else:
            # Fallback to legacy per-quartile columns.
            for col_name, col_value in row.items():
                if col_value.strip() != "1":
                    continue
                if "Q1" in col_name:
                    quartile = JournalQuartile.Q1
                    break
                elif "Q2" in col_name:
                    quartile = JournalQuartile.Q2
                    break
                elif "Q3" in col_name:
                    quartile = JournalQuartile.Q3
                    break
                elif "Q4" in col_name:
                    quartile = JournalQuartile.Q4
                    break

        # Extract subject area
        subject_area = row.get("Categories", "").strip()

        # Open access flag (modern Scimago export includes an "Open Access" column)
        is_open_access = (row.get("Open Access") or "").strip().lower() in {"yes", "true", "1"}

        return JournalRecord(
            issn=primary_issn,
            title=title,
            publisher=publisher,
            subject_area=subject_area,
            quartile=quartile,
            sjr=sjr,
            h_index=h_index,
            cite_score=cite_score,
            impact_factor=impact_factor,
            is_open_access=is_open_access,
            country=country,
            languages=(),  # Not in Scimago data
            website=row.get("Homepage", "").strip(),
            issn_print=issn_print,
            issn_electronic=issn_electronic,
            year=2024,  # Scimago data year (should be extracted from filename)
        )

    def _normalize_issn(self, issn: str) -> str:
        """Normalize ISSN to standard format (XXXXXXXX)."""
        if not issn:
            return ""
        # Remove hyphens and whitespace
        normalized = re.sub(r"[-\s]", "", issn.upper())
        # Validate format (8 digits or 7 digits + X)
        if re.match(r"^\d{7}[\dX]$", normalized):
            return normalized
        return ""

    def _parse_float(self, value: str) -> float:
        """Parse float from string, handling various formats."""
        if not value:
            return 0.0
        try:
            # Remove quotes and whitespace
            cleaned = value.strip().strip('"').strip()
            if not cleaned:
                return 0.0
            return float(cleaned.replace(",", "."))
        except (ValueError, TypeError):
            return 0.0

    def _parse_int(self, value: str) -> int:
        """Parse int from string."""
        if not value:
            return 0
        try:
            cleaned = value.strip().strip('"').strip()
            if not cleaned:
                return 0
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0

    def _add_record(self, record: JournalRecord):
        """Add a journal record to all indexes."""
        # ISSN index
        self._records_by_issn[record.issn] = record

        # Title index (normalized)
        normalized_title = self._normalize_title(record.title)
        if normalized_title:
            self._title_index[normalized_title] = record.issn

        # Publisher index
        if record.publisher:
            publisher_key = record.publisher.lower().strip()
            if publisher_key not in self._publisher_index:
                self._publisher_index[publisher_key] = []
            self._publisher_index[publisher_key].append(record.issn)

    def _normalize_title(self, title: str) -> str:
        """Normalize journal title for fuzzy matching."""
        if not title:
            return ""
        # Normalize unicode
        value = unicodedata.normalize("NFKD", title)
        value = value.encode("ascii", "ignore").decode("ascii")
        # Lowercase
        value = value.lower()
        # Remove special chars but keep spaces
        value = re.sub(r"[^a-z0-9\s]", " ", value)
        # Collapse whitespace
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _compute_stats(self):
        """Compute aggregate statistics."""
        self._stats = JournalQualityStats()
        self._stats.total_journals = len(self._records_by_issn)

        sjr_sum = 0.0
        h_index_sum = 0
        cite_score_sum = 0.0
        subject_areas = set()

        for record in self._records_by_issn.values():
            if record.quartile == JournalQuartile.Q1:
                self._stats.q1_count += 1
            elif record.quartile == JournalQuartile.Q2:
                self._stats.q2_count += 1
            elif record.quartile == JournalQuartile.Q3:
                self._stats.q3_count += 1
            elif record.quartile == JournalQuartile.Q4:
                self._stats.q4_count += 1
            else:
                self._stats.unknown_count += 1

            if record.is_open_access:
                self._stats.open_access_count += 1

            sjr_sum += record.sjr
            h_index_sum += record.h_index
            cite_score_sum += record.cite_score

            if record.subject_area:
                subject_areas.add(record.subject_area)

        if self._stats.total_journals > 0:
            self._stats.avg_sjr = sjr_sum / self._stats.total_journals
            self._stats.avg_h_index = h_index_sum / self._stats.total_journals
            self._stats.avg_cite_score = cite_score_sum / self._stats.total_journals

        self._stats.subject_areas = tuple(sorted(subject_areas))

    # ── Public API ─────────────────────────────────────────────────────────

    def get_by_issn(self, issn: str) -> JournalRecord | None:
        """Lookup journal by ISSN."""
        normalized = self._normalize_issn(issn)
        return self._records_by_issn.get(normalized)

    def get_by_title(self, title: str, threshold: float = 0.75) -> JournalRecord | None:
        """
        Lookup journal by title (fuzzy matching).

        Args:
            title: Journal title to search
            threshold: Minimum similarity ratio (0-1) for match

        Returns:
            Matching JournalRecord or None
        """
        if not title:
            return None

        normalized = self._normalize_title(title)
        if not normalized:
            return None

        # Exact match
        if normalized in self._title_index:
            issn = self._title_index[normalized]
            return self._records_by_issn.get(issn)

        # Fuzzy match using token_set_ratio for better partial matching
        from rapidfuzz import fuzz

        best_match = None
        best_score = 0.0

        for stored_title, issn in self._title_index.items():
            # Use token_set_ratio which handles word order differences
            score = fuzz.token_set_ratio(normalized, stored_title) / 100.0
            if score > best_score and score >= threshold:
                best_score = score
                best_match = self._records_by_issn.get(issn)

        return best_match

    def get_by_publisher(self, publisher: str) -> list[JournalRecord]:
        """Get all journals by a publisher."""
        if not publisher:
            return []

        publisher_key = publisher.lower().strip()
        issns = self._publisher_index.get(publisher_key, [])
        return [self._records_by_issn[i] for i in issns if i in self._records_by_issn]

    def get_record(
        self,
        journal_title: str | None = None,
        issn: str | None = None,
    ) -> JournalRecord | None:
        """
        Public lookup helper: by ISSN first, fallback to fuzzy title match.

        Returns the matched JournalRecord or None if not found.
        Use this when you need the full record (e.g. quartile) rather than
        just a numeric score.
        """
        if issn:
            record = self.get_by_issn(issn)
            if record is not None:
                return record
        if journal_title:
            return self.get_by_title(journal_title)
        return None

    def score_journal(
        self,
        journal_title: str | None = None,
        issn: str | None = None,
    ) -> float:
        """
        Score a journal based on quality metrics.

        Scoring breakdown:
        - Quartile (50% weight): Q1=1.0, Q2=0.75, Q3=0.5, Q4=0.25
        - SJR (25% weight): normalized to 0-1
        - H-index (25% weight): normalized to 0-1

        Args:
            journal_title: Journal title for lookup
            issn: ISSN for lookup

        Returns:
            Score between 0.0 and 1.0
        """
        record = None

        if issn:
            record = self.get_by_issn(issn)
        elif journal_title:
            record = self.get_by_title(journal_title)

        if record is None:
            # Unknown journal - return neutral score
            return 0.5

        return self._compute_score(record)

    def _compute_score(self, record: JournalRecord) -> float:
        """Compute quality score for a journal record."""
        # Quartile score (50% weight)
        quartile_scores = {
            JournalQuartile.Q1: 1.0,
            JournalQuartile.Q2: 0.75,
            JournalQuartile.Q3: 0.5,
            JournalQuartile.Q4: 0.25,
            JournalQuartile.UNKNOWN: 0.3,  # Unknown gets neutral-ish score
        }
        quartile_score = quartile_scores.get(record.quartile, 0.3)

        # SJR score (25% weight)
        # SJR range is typically 0-30+, normalize with log scale
        import math

        sjr_score = min(1.0, math.log1p(record.sjr) / math.log1p(30))

        # H-index score (25% weight)
        # H-index range varies by field, normalize with log scale
        h_index_score = min(1.0, math.log1p(record.h_index) / math.log1p(150))

        # Weighted average
        final_score = 0.50 * quartile_score + 0.25 * sjr_score + 0.25 * h_index_score

        return final_score

    def is_predatory(
        self,
        journal_title: str | None = None,
        publisher: str | None = None,
        issn: str | None = None,
        website: str | None = None,
    ) -> bool:
        """
        Check if a journal matches predatory journal criteria.

        Based on Beall's List criteria:
        https://beallslist.net/standards/

        WARNING: This is a heuristic check, not definitive.
        Use with caution and verify with additional sources.

        Args:
            journal_title: Journal title
            publisher: Publisher name
            issn: ISSN
            website: Journal website URL

        Returns:
            True if journal matches predatory criteria
        """
        score = self._predatory_score(journal_title, publisher, issn, website)
        # Threshold: 2 or more red flags = likely predatory
        return score >= self._predatory_threshold

    def _predatory_score(
        self,
        journal_title: str | None = None,
        publisher: str | None = None,
        issn: str | None = None,
        website: str | None = None,
    ) -> int:
        """
        Compute predatory journal risk score.

        Returns count of red flags (higher = more suspicious).
        """
        score = 0

        if journal_title:
            title_lower = journal_title.lower()
            for pattern in self._predatory_criteria.suspicious_name_patterns:
                if pattern in title_lower:
                    score += 1
                    break

        if publisher:
            publisher_lower = publisher.lower()
            for pattern in self._predatory_criteria.suspicious_publisher_patterns:
                if pattern in publisher_lower:
                    score += 1
                    break

        if website:
            website_lower = website.lower()
            for pattern in self._predatory_criteria.suspicious_domain_patterns:
                if pattern in website_lower:
                    score += 1
                    break

        # Check if journal exists in our database
        if issn:
            record = self.get_by_issn(issn)
            if record:
                # Has SJR data = likely legitimate
                if record.sjr > 0:
                    score -= 1  # Reduce score for known journals
            else:
                # Unknown ISSN = slight red flag
                score += 1

        return max(0, score)  # Never go negative

    def get_stats(self) -> JournalQualityStats:
        """Get loaded data statistics."""
        return self._stats

    @property
    def is_loaded(self) -> bool:
        """Check if data is loaded."""
        return self._loaded

    @property
    def journal_count(self) -> int:
        """Get total number of loaded journals."""
        return len(self._records_by_issn)


# Convenience function
def get_journal_quality_service() -> JournalQualityService:
    """Get the singleton JournalQualityService instance."""
    return JournalQualityService.instance()
